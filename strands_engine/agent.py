"""
Agent wrapper implementation for strands_engine.

This module provides the WrappedAgent class, which extends the strands-agents
Agent with framework-specific adaptations and enhanced message handling
capabilities. The wrapper maintains full compatibility with strands-agents
while adding features needed by strands_engine.

The WrappedAgent serves as a bridge between the strands_engine configuration
system and the strands-agents execution environment, handling message
transformation, streaming, and framework-specific adaptations.
"""

import sys
from typing import Union, List, Dict, Any

from loguru import logger
from strands import Agent

from strands_engine.framework.base_adapter import FrameworkAdapter


class WrappedAgent(Agent):
    """
    Enhanced Agent wrapper with framework adapter integration.
    
    WrappedAgent extends the strands-agents Agent class to provide framework-
    specific message transformation and enhanced streaming capabilities. It
    maintains full compatibility with the strands-agents interface while
    adding features required by strands_engine.
    
    Key features:
    - Framework-specific message transformation via adapters
    - Enhanced error handling and logging
    - Streaming response handling with callback integration
    - Transparent compatibility with strands-agents ecosystem
    
    The wrapper pattern allows strands_engine to enhance agent behavior
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
        # Store adapter before calling parent constructor
        self.adapter = adapter

        # Call parent constructor with all other arguments
        super().__init__(**kwargs)

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
        if not message:
            return True

        try:
            # Transform the message using the framework adapter
            transformed_message = self.adapter.transform_content(message)

            # Stream the response - the CustomCallbackHandler handles all output formatting
            async for _ in self.stream_async(transformed_message):
                pass

            return True
        except Exception as e:
            logger.error(f"Unexpected error in agent stream: {e}")
            print(
                f"\\nAn unexpected error occurred while generating the response: {e}",
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
        if show_user_input and isinstance(message, str):
            print(f"You: {message}")

        return await self.handle_agent_stream(message)