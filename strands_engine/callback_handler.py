"""
Callback handler implementation for strands_engine.

This module provides the EngineCallbackHandler class, which extends the
strands-agents PrintingCallbackHandler to provide customized output handling
for strands_engine applications. The handler manages agent output display
without requiring prompt_toolkit dependencies.

The callback handler provides:
- Clean agent response display with proper formatting
- Optional tool usage information display
- Event-driven output handling for streaming responses
- Graceful handling of reasoning text and tool execution feedback

The handler is designed to work seamlessly with strands_engine's streaming
capabilities while providing clear, formatted output for end users.
"""

from typing import Any, Optional
from loguru import logger
from strands.handlers.callback_handler import PrintingCallbackHandler


class EngineCallbackHandler(PrintingCallbackHandler):
    """
    Customized callback handler for strands_engine output management.
    
    EngineCallbackHandler extends the standard PrintingCallbackHandler to
    provide enhanced output formatting and optional tool usage display for
    strands_engine applications. It handles the complexity of streaming
    agent responses while maintaining clean, user-friendly output.
    
    The handler manages:
    - Message content display with proper formatting
    - Optional tool execution information display
    - Event-driven output handling for streaming responses
    - Reasoning text display for models that support it
    - Clean completion handling with appropriate line breaks
    
    Key features:
    - No prompt_toolkit dependencies (lightweight)
    - Configurable tool usage display
    - Event-based output state management  
    - Proper handling of streaming vs. complete responses
    - Integration with strands-agents callback system
    
    Attributes:
        show_tool_use: Whether to display tool usage information
        in_message: Current message display state
        in_tool_use: Current tool usage display state
        tool_count: Running count of tools used in conversation
        previous_tool_use: Most recent tool usage information
        
    Example:
        Basic usage::
        
            handler = EngineCallbackHandler(show_tool_use=True)
            agent = Agent(model=model, callback_handler=handler)
            
        With custom configuration::
        
            handler = EngineCallbackHandler(show_tool_use=False)
            # Handler will show responses but not tool usage details
    """

    def __init__(self, show_tool_use: Optional[bool] = False):
        """
        Initialize the callback handler with display options.
        
        Creates an EngineCallbackHandler with configurable output behavior.
        The handler extends PrintingCallbackHandler while adding tool usage
        display capabilities and enhanced state management.
        
        Args:
            show_tool_use: Whether to display detailed tool usage information.
                          When True, shows tool names and execution counts.
                          When False, only shows agent responses. (default: False)
        """
        super().__init__()
        self.show_tool_use = show_tool_use
        self.in_message = False
        self.in_tool_use = False
        self.tool_count = 0
        self.previous_tool_use = None

    def __call__(self, **kwargs: Any) -> None:
        """
        Handle agent output events and format display accordingly.
        
        This is the main callback method that processes events from the
        strands-agents streaming system. It handles different types of
        output events including message content, tool usage, reasoning
        text, and completion signals.
        
        The method processes several event types:
        - Message content: Regular agent response text
        - Tool usage: Information about tool calls and execution
        - Reasoning text: Model reasoning/thinking display
        - Completion events: End-of-message or end-of-response signals
        
        Args:
            **kwargs: Event data from strands-agents callback system
                     Common keys include:
                     - event: Event type information
                     - reasoningText: Model reasoning content
                     - data: Response content data
                     - complete: Whether response is complete
                     - current_tool_use: Current tool usage information
                     
        Note:
            This method is called automatically by the strands-agents
            streaming system. It should not be called directly by
            application code.
        """
        logger.trace("EngineCallbackHandler.__call__ arguments: {}", kwargs)

        event = kwargs.get("event", {})
        reasoningText = kwargs.get("reasoningText", False)
        data = kwargs.get("data", "")
        complete = kwargs.get("complete", False)
        current_tool_use = kwargs.get("current_tool_use", {})

        # Handle message completion
        if "messageStop" in event and self.in_message:
            self.in_message = False
            print(flush=True)

        # Display reasoning text (for models that support it)
        if reasoningText:
            print(reasoningText, end="")

        # Display response content
        if data:
            print(data, end="" if not complete else "\n")

        # Handle tool use display if enabled
        if self.show_tool_use:
            if current_tool_use:
                if not self.in_tool_use:
                    self.tool_count += 1
                    self.in_tool_use = True
                self.previous_tool_use = current_tool_use

            if "messageStop" in event and self.in_tool_use:
                if self.previous_tool_use:
                    print(f"\nTool #{self.tool_count}: {self.previous_tool_use.get('name', 'Unknown')}")
                    self.previous_tool_use = None
                self.in_tool_use = False

        # Handle completion formatting
        if complete and data:
            print("\n")