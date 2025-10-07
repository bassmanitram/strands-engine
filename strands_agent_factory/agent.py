"""
Agent wrapper implementation for strands_agent_factory.

This module provides the WrappedAgent class, which extends the strands-agents
Agent with framework-specific adaptations and enhanced message handling
capabilities. The wrapper maintains full compatibility with strands-agents
while adding features needed by strands_agent_factory.

The WrappedAgent serves as a bridge between the strands_agent_factory configuration
system and the strands-agents execution environment, handling message
transformation, streaming, and framework-specific adaptations.
"""

import sys
from typing import Union, List, Dict, Any

from loguru import logger
from strands import Agent

from strands_agent_factory.framework.base_adapter import FrameworkAdapter


class WrappedAgent(Agent):
    """
    Enhanced Agent wrapper with framework adapter integration.
    
    WrappedAgent extends the strands-agents Agent class to provide framework-
    specific message transformation and enhanced streaming capabilities. It
    maintains full compatibility with the strands-agents interface while
    adding features required by strands_agent_factory.
    
    Key features:
    - Framework-specific message transformation via adapters
    - Enhanced error handling and logging
    - Streaming response handling with callback integration
    - Transparent compatibility with strands-agents ecosystem
    
    The wrapper pattern allows strands_agent_factory to enhance agent behavior
    without modifying the core strands-agents implementation, ensuring
    compatibility and maintainability.
    
    Attributes:
        adapter: The FrameworkAdapter instance for message transformations
        
    Example:
        Creating a wrapped agent::
        
            adapter = OpenAIAdapter()
            agent = WrappedAgent(
                adapter=adapter,
                model=model,
                tools=tools,
                callback_handler=handler
            )
            
            success = await agent.send_message_to_agent("Hello!")
    """

    def __init__(self, adapter: FrameworkAdapter, **kwargs: Any) -> None:
        """
        Initialize the wrapped agent with framework adapter.
        
        Creates a WrappedAgent instance that extends strands-agents Agent
        functionality with framework-specific adaptations. The adapter
        is stored before calling the parent constructor to ensure it's
        available for all agent operations.
        
        Args:
            adapter: FrameworkAdapter instance for message transformations
            **kwargs: Additional arguments passed to the parent Agent constructor
            
        Note:
            All standard Agent constructor arguments (model, tools, callback_handler,
            etc.) are supported through **kwargs and passed directly to the
            parent class constructor.
        """
        logger.debug(f"WrappedAgent.__init__ called with adapter={type(adapter).__name__}, kwargs keys: {list(kwargs.keys())}")
        
        # Store adapter before calling parent constructor
        self.adapter = adapter

        # Call parent constructor with all other arguments
        logger.debug(f"Calling parent Agent.__init__ with kwargs: {kwargs}")
        super().__init__(**kwargs)
        logger.debug("WrappedAgent initialization completed")

    async def handle_agent_stream(self,
        message: Union[str, List[Dict[str, Any]]]) -> bool:
        """
        Handle streaming agent response with framework-specific transformations.
        
        Processes a message through the framework adapter and streams the
        agent's response. This method provides the core message handling
        logic with error handling and framework adaptation.
        
        The method:
        1. Validates the input message
        2. Applies framework-specific transformations via the adapter
        3. Streams the response through the agent's streaming interface
        4. Handles errors gracefully with appropriate logging and user feedback
        
        Args:
            message: Message to process - can be string or structured content
            
        Returns:
            bool: True if message was processed successfully, False on error
            
        Note:
            The CustomCallbackHandler (if configured) handles all output
            formatting during streaming. This method focuses on message
            processing and error handling.
        """
        logger.debug(f"handle_agent_stream called with message type: {type(message)}, content preview: {str(message)[:100] if message else 'None'}")
        
        if not message:
            logger.debug("Empty message, returning True")
            return True

        try:
            # Transform the message using the framework adapter
            logger.debug(f"Transforming message using adapter: {type(self.adapter).__name__}")
            transformed_message = self.adapter.transform_content(message)
            logger.debug(f"Message transformed, type: {type(transformed_message)}")

            # Stream the response - the CallbackHandler handles all output formatting
            logger.debug("Starting agent streaming...")
            async for chunk in self.stream_async(transformed_message):
                logger.trace(f"Received stream chunk: {chunk}")
                pass

            logger.debug("Agent streaming completed successfully")
            return True
        except Exception as e:
            logger.error(f"Unexpected error in agent stream: {e}", exc_info=True)
            print(
                f"\nAn unexpected error occurred while generating the response: {e}",
                file=sys.stderr,
            )
            return False

    async def send_message_to_agent(self,
        message: Union[str, List[Dict[str, Any]]],
        show_user_input: bool = True
    ) -> bool:
        """
        Send a message to the agent with optional input display.
        
        Higher-level interface for agent interaction that combines message
        display and processing. This method provides a clean API for
        applications that need both input echoing and response generation.
        
        The method optionally displays the user input (for conversational
        interfaces) and then processes the message through the streaming
        handler with all framework adaptations applied.
        
        Args:
            message: Message to send to the agent
            show_user_input: Whether to display the user input before processing
            
        Returns:
            bool: True if message was processed successfully, False on error
            
        Example:
            Basic usage::
            
                # With input display (conversational mode)
                success = await agent.send_message_to_agent("Hello!", show_user_input=True)
                
                # Without input display (programmatic mode)  
                success = await agent.send_message_to_agent(message, show_user_input=False)
                
        Note:
            Input display only occurs for string messages. Structured content
            (List[Dict]) is not displayed as it may contain complex formatting
            or binary data that's not suitable for text display.
        """
        logger.debug(f"send_message_to_agent called with message type: {type(message)}, show_user_input: {show_user_input}")
        
        if show_user_input and isinstance(message, str):
            print(f"You: {message}")

        return await self.handle_agent_stream(message)