import concurrent
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
import sys
from typing import Optional, List, Any

from loguru import logger
from strands import Agent

from strands_agent_factory.framework.base_adapter import FrameworkAdapter
from strands_agent_factory.messages import generate_llm_messages
from strands_agent_factory.ptypes import ToolSpec

class AgentProxy:
    """Proxy for Agent that manages MCP server lifecycle and defers agent creation until context entry.
    
    This proxy ensures MCP servers are properly initialized before creating the underlying Agent,
    preventing premature agent creation and ensuring all tools are available.
    """
    
    def __init__(self, adapter: FrameworkAdapter, tool_specs: List[ToolSpec], **kwargs: Any) -> None:
        """Initialize the AgentProxy with configuration for later agent creation.
        
        Args:
            adapter: Framework adapter for message transformations
            tool_specs: List of tool specifications including MCP server clients
            **kwargs: Arguments to pass to Agent constructor during __enter__
        """
        logger.trace(f"AgentProxy.__init__ called with {len(tool_specs)} tool specs")
        
        self._adapter = adapter
        self._tool_specs = tool_specs or []
        self._agent_kwargs = kwargs
        self._agent: Optional[Agent] = None
        self._context_entered = False
    
        # Separate MCP server specs from regular tools
        self._mcp_server_specs = [obj for obj in tool_specs if obj.get("client")]
        self._tools = []
        for spec in tool_specs:
            if spec.get("tools"):
                self._tools.extend(spec["tools"])

        self._mcp_tools = []
        self._max_threads = 3
        self._exit_stack = None
        self._active_mcp_servers = []
        
        logger.trace(f"AgentProxy.__init__ completed - {len(self._mcp_server_specs)} MCP servers, {len(self._tools)} regular tools")

    def __enter__(self):
        """Initialize MCP servers and create the underlying Agent.
        
        Returns:
            self: The proxy instance for use in the context manager
        """
        logger.trace(f"AgentProxy.__enter__ called with {len(self._mcp_server_specs)} MCP server specs")
        
        # Extract MCP clients from tool specs
        mcp_clients = [spec["client"] for spec in self._mcp_server_specs]

        # Initialize MCP servers concurrently
        futures_with_clients = []
        if mcp_clients:
            self._exit_stack = ExitStack()
            with ThreadPoolExecutor(max_workers=self._max_threads) as executor:
                for client in mcp_clients:
                    future = executor.submit(self._call_single_enter_safely, client)
                    futures_with_clients.append((future, client))

                # Wait for all MCP server initializations to complete
                done, not_done = concurrent.futures.wait([item[0] for item in futures_with_clients], 
                                            return_when=concurrent.futures.ALL_COMPLETED)
                
                if not_done:
                    logger.warning("Some MCP server initializations were not done even though the 'wait for all' returned")

                # Process results and register successful clients
                for future, client in futures_with_clients:
                    try:
                        _resource = future.result()
                        self._exit_stack.push(client.__exit__)
                        self._active_mcp_servers.append(client)
                        logger.debug(f"Successfully initialized MCP client: {client.server_id}")
                    except Exception as e:
                        logger.warn(f"MCP client initialization failed for {getattr(client, 'server_id', 'unknown')}: {e}")

            # Collect tools from all active MCP servers
            for client in self._active_mcp_servers:
                try:
                    self._mcp_tools.extend(client.list_tools_sync());
                except Exception as e:
                    logger.error(f"MCP client tools listing failed for {getattr(client, 'server_id', 'unknown')}: {e}")

        # Create the actual Agent with all tools available
        self._context_entered = True
        self._agent = Agent(tools=(self._tools + self._mcp_tools), **self._agent_kwargs)

        logger.trace(f"AgentProxy.__enter__ completed with {len(self._active_mcp_servers)} active MCP servers")
        return self
    
    def _call_single_enter_safely(self, manager):
        """Initialize a single MCP server context manager in a worker thread.
        
        Args:
            manager: MCP client context manager to initialize
            
        Returns:
            Result from the manager's __enter__ method
        """
        logger.trace(f"_call_single_enter_safely called for manager type: {type(manager).__name__}")
        
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
        logger.trace(f"AgentProxy.__exit__ called with exc_type={exc_type}")
        
        # Clean up agent first to prevent access during MCP cleanup
        self._context_entered = False
        self._agent = None
        
        if self._exit_stack:
            result = self._exit_stack.__exit__(exc_type, exc_val, exc_tb)
            self._active_mcp_servers = []
            self._mcp_tools = []
            logger.trace("AgentProxy.__exit__ completed with exit stack cleanup")
            return result
        
        self._active_mcp_servers = []
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
        logger.trace(f"_handle_agent_stream called with message type: {type(message)}")
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
        logger.trace(f"send_message_to_agent called with message type: {type(message)}, show_user_input: {show_user_input}")
        self._ensure_agent_available()
        
        if show_user_input:
            print(f"You: {message}")

        result = await self._handle_agent_stream(message)
        
        logger.debug(f"send_message_to_agent returning: {result}")
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
        logger.trace(f"__getattr__ called for attribute: {name}")
        self._ensure_agent_available()
        result = getattr(self._agent, name)
        logger.trace(f"__getattr__ completed for attribute: {name}")
        return result
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Delegate attribute setting to the underlying agent or handle internal attributes.
        
        Args:
            name: Name of the attribute to set
            value: Value to set the attribute to
        """
        logger.trace(f"__setattr__ called for attribute: {name}")
        
        if name.startswith('_'):  # Internal attributes
            object.__setattr__(self, name, value)
            logger.trace(f"__setattr__ completed for internal attribute: {name}")
        else:
            self._ensure_agent_available()
            setattr(self._agent, name, value)
            logger.trace(f"__setattr__ completed for agent attribute: {name}")
    
    def __call__(self, *args, **kwargs):
        """Make the proxy callable like the underlying agent.
        
        Args:
            *args: Positional arguments to pass to the agent
            **kwargs: Keyword arguments to pass to the agent
            
        Returns:
            Any: Result from calling the underlying agent
        """
        logger.trace(f"__call__ called with {len(args)} args, {len(kwargs)} kwargs")
        self._ensure_agent_available()
        result = self._agent(*args, **kwargs)
        logger.trace("__call__ completed")
        return result
    
    # Other convenient things to do
    def clear_messages(self):
        self._ensure_agent_available()
        self._agent.messages.clear()