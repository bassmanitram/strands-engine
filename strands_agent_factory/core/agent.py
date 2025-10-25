import concurrent
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
import sys
import time
from typing import Optional, List, Any

from loguru import logger
from strands import Agent

from strands_agent_factory.adapters.base import FrameworkAdapter
from strands_agent_factory.messaging.generator import generate_llm_messages
from strands_agent_factory.core.types import EnhancedToolSpec

class AgentProxy:
    """Proxy for Agent that manages MCP client lifecycle and defers agent creation until context entry.
    
    This proxy ensures MCP servers are properly initialized before creating the underlying Agent,
    preventing premature agent creation and ensuring all tools are available.
    """
    
    def __init__(self, adapter: FrameworkAdapter, tool_specs: List[EnhancedToolSpec], **kwargs: Any) -> None:
        """Initialize the AgentProxy with configuration for later agent creation.
        
        Args:
            adapter: Framework adapter for message transformations
            tool_specs: List of enhanced tool specifications including MCP server clients
            **kwargs: Arguments to pass to Agent constructor during __enter__
        """
        if logger.level('TRACE').no >= logger._core.min_level:
            logger.trace("AgentProxy.__init__ called with {} tool specs", len(tool_specs))
        
        self._adapter = adapter
        self._agent_kwargs = kwargs
        self._agent: Optional[Agent] = None
        self._context_entered = False
    
        self._all_tool_specs = tool_specs
        # Separate MCP server specs from regular tools
        self._local_tool_specs = [obj for obj in tool_specs if not obj.get("client") and not obj.get("error")]
        self._mcp_client_specs = [obj for obj in tool_specs if obj.get("client") and not obj.get("error")]

        self._tools = []
        for spec in self._local_tool_specs:
            if spec.get("tools"):
                my_tools = spec["tools"]
                # Use robust name extraction that handles tools without .name attribute
                spec["tool_names"] = [getattr(tool, 'name', getattr(tool, '__name__', str(tool))) for tool in my_tools]
                self._tools.extend(my_tools)

        self._mcp_tools = []

        self._max_threads = 3
        self._exit_stack = None
        self._active_mcp_clients = []
        
        if logger.level('TRACE').no >= logger._core.min_level:
            logger.trace("AgentProxy.__init__ completed - {} MCP clients, {} regular tools", len(self._mcp_client_specs), len(self._tools))

    @property
    def tool_specs(self) -> List[EnhancedToolSpec]:
        """Get the enhanced tool specifications provided to the proxy.
        
        Returns:
            List[EnhancedToolSpec]: The list of enhanced tool specifications
        """
        return self._all_tool_specs
    
    def __enter__(self):
        """Initialize MCP servers and create the underlying Agent.
        
        Returns:
            self: The proxy instance for use in the context manager
        """
        if logger.level('TRACE').no >= logger._core.min_level:
            logger.trace("AgentProxy.__enter__ called with {} MCP server specs", len(self._mcp_client_specs))
        
        # Extract MCP clients from tool specs
        mcp_clients = [spec["client"] for spec in self._mcp_client_specs]

        # Initialize MCP servers concurrently
        futures_with_specs = []
        if self._mcp_client_specs:
            start_time = time.perf_counter()
            self._exit_stack = ExitStack()
            
            # Register ALL clients for cleanup before initialization
            for client in [spec["client"] for spec in self._mcp_client_specs]:
                try:
                    self._exit_stack.push(client.__exit__)
                except Exception as e:
                    logger.debug("Could not register cleanup for client {}: {}", getattr(client, 'server_id', 'unknown'), e)
            
            with ThreadPoolExecutor(max_workers=self._max_threads) as executor:
                for spec in self._mcp_client_specs:
                    client = spec["client"]
                    future = executor.submit(self._call_single_enter_safely, client)
                    futures_with_specs.append((future, spec))

                # Wait for all MCP server initializations to complete
                done, not_done = concurrent.futures.wait([item[0] for item in futures_with_specs], 
                                            return_when=concurrent.futures.ALL_COMPLETED)
                
                if not_done:
                    logger.warning("Some MCP server initializations were not done even though the 'wait for all' returned")

                # Process results and track only successful clients
                for future, spec in futures_with_specs:
                    client = spec["client"]
                    try:
                        _resource = future.result() # Will raise if there was an exception
                        tools = client.list_tools_sync()
                        # Use robust name extraction for MCP tools too
                        spec["tool_names"] = [getattr(tool, 'tool_name', getattr(tool, '__name__', str(tool))) for tool in tools]
                        self._mcp_tools.extend(tools)
                        self._active_mcp_clients.append(client)
                        logger.debug("Successfully initialized MCP client: {}", client.server_id)
                    except Exception as e:
                        logger.warning(f"MCP client initialization failed for {getattr(client, 'server_id', 'unknown')}: {e}")
                        spec["error"] = str(e)
                        # Cleanup already registered above

            init_time = time.perf_counter() - start_time
            logger.debug("MCP server initialization completed for {} servers in {:.2f}ms", 
                        len(self._active_mcp_clients), init_time * 1000)

        # Create the actual Agent with all tools available
        self._context_entered = True
        self._agent = Agent(tools=(self._tools + self._mcp_tools), **self._agent_kwargs)

        if logger.level('TRACE').no >= logger._core.min_level:
            logger.trace("AgentProxy.__enter__ completed with {} active MCP servers", len(self._active_mcp_clients))
        return self
    
    def _call_single_enter_safely(self, manager):
        """Initialize a single MCP server context manager in a worker thread.
        
        Args:
            manager: MCP client context manager to initialize
            
        Returns:
            Result from the manager's __enter__ method
        """
        logger.trace("_call_single_enter_safely called for manager type: {}", type(manager).__name__)
        
        result = manager.__enter__()
        
        logger.trace("_call_single_enter_safely completed")
        return result

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up MCP servers and agent resources.
        
        Args:
            exc_type: Exception type if exiting due to exception
            exc_val: Exception value if exiting due to exception  
            exc_tb: Exception traceback if exiting due to exception
            
        Returns:
            bool: False to propagate any exceptions
        """
        logger.trace("AgentProxy.__exit__ called with exc_type={}", exc_type)
        
        # Clean up agent first to prevent access during MCP cleanup
        self._context_entered = False
        self._agent = None
        
        if self._exit_stack:
            result = self._exit_stack.__exit__(exc_type, exc_val, exc_tb)
            self._active_mcp_clients = []
            self._mcp_tools = []
            logger.trace("AgentProxy.__exit__ completed with exit stack cleanup")
            return result
        
        self._active_mcp_clients = []
        self._mcp_tools = []
        logger.trace("AgentProxy.__exit__ completed (no exit stack)")
        return False
    
    async def _handle_agent_stream(self, message: str) -> bool:
        """Process a message through the agent with framework-specific transformations.
        
        Args:
            message: Message to process through the agent
            
        Returns:
            bool: True if message was processed successfully, False on error
        """
        logger.trace("_handle_agent_stream called with message type: {}", type(message))
        self._ensure_agent_available()
        
        if not message:
            logger.debug("_handle_agent_stream returning True (empty message)")
            return True

        try:
            # Transform the message using the framework adapter
            messages = generate_llm_messages(message)
            transformed_messages = self._adapter.adapt_content(messages)

            # Stream the response through the agent
            async for chunk in self.stream_async(transformed_messages):
                pass  # CallbackHandler processes all output

            logger.trace("_handle_agent_stream completed successfully")
            return True
        except Exception as e:
            logger.error(f"Unexpected error in agent stream: {e}")
            print(
                f"\nAn unexpected error occurred while generating the response: {e}",
                file=sys.stderr,
            )
            logger.trace("_handle_agent_stream completed with error")
            return False

    async def send_message_to_agent(self, message: str, show_user_input: bool = True) -> bool:
        """Send a message to the agent with optional input display.
        
        Args:
            message: Message to send to the agent
            show_user_input: Whether to display the user input before processing
            
        Returns:
            bool: True if message was processed successfully, False on error
        """
        logger.trace("send_message_to_agent called with message type: {}, show_user_input: {}", type(message), show_user_input)
        self._ensure_agent_available()
        
        if show_user_input:
            print(f"You: {message}")

        result = await self._handle_agent_stream(message)
        
        logger.debug("send_message_to_agent returning: {}", result)
        return result
    
    def _ensure_agent_available(self):
        """Validate that the agent is available for use.
        
        Raises:
            RuntimeError: If agent is accessed outside of context manager
        """
        logger.trace("_ensure_agent_available called")
        
        if not self._context_entered or self._agent is None:
            logger.debug("_ensure_agent_available failed - agent not available")
            raise RuntimeError(
                "Agent not available. Use AgentProxy within a context manager:\n"
                "with AgentProxy(...) as agent:\n"
                "    agent.do_something()"
            )
        
        logger.trace("_ensure_agent_available completed - agent available")
    
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the underlying agent.
        
        Args:
            name: Name of the attribute to access
            
        Returns:
            Any: The attribute value from the underlying agent
        """
        logger.trace("__getattr__ called for attribute: {}", name)
        self._ensure_agent_available()
        result = getattr(self._agent, name)
        logger.trace("__getattr__ completed for attribute: {}", name)
        return result
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Delegate attribute setting to the underlying agent or handle internal attributes.
        
        Args:
            name: Name of the attribute to set
            value: Value to set the attribute to
        """
        logger.trace("__setattr__ called for attribute: {}", name)
        
        if name.startswith('_'):  # Internal attributes
            object.__setattr__(self, name, value)
            logger.trace("__setattr__ completed for internal attribute: {}", name)
        else:
            self._ensure_agent_available()
            setattr(self._agent, name, value)
            logger.trace("__setattr__ completed for agent attribute: {}", name)
    
    def __call__(self, *args, **kwargs):
        """Make the proxy callable like the underlying agent.
        
        Args:
            *args: Positional arguments to pass to the agent
            **kwargs: Keyword arguments to pass to the agent
            
        Returns:
            Any: Result from calling the underlying agent
        """
        if logger.level('TRACE').no >= logger._core.min_level:
            logger.trace("__call__ called with {} args, {} kwargs", len(args), len(kwargs))
        self._ensure_agent_available()
        result = self._agent(*args, **kwargs)
        logger.trace("__call__ completed")
        return result
    
    # Other convenient things to do
    def clear_messages(self):
        self._ensure_agent_available()
        self._agent.messages.clear()