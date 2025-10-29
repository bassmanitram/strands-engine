"""
Custom callback handler for strands_agent_factory.

This module provides a configurable callback handler that controls output verbosity
and tool execution feedback for strands-agents Agent instances.

The callback handler serves as the interface between the agent's internal events
and user-visible output, providing fine-grained control over what information
is displayed during agent execution.
"""

import os
from typing import Any, Optional, Callable

from loguru import logger

from strands_agent_factory.core.utils import print_structured_data


class ConfigurableCallbackHandler:
    """
    Configurable callback handler for controlling agent output verbosity.

    This handler provides configurable control over tool execution feedback:
    - When show_tool_use=False (default): Suppresses verbose tool execution details
    - When show_tool_use=True: Shows full tool execution feedback with structured formatting
    
    The handler processes various agent events including message content, tool usage,
    and completion signals to provide appropriate user feedback. It maintains state
    to track message boundaries and tool execution phases.
    
    Also handles:
    - Response prefix printing in interactive mode
    - Final newline after responses
    - Tool input formatting with optional truncation
    - Environment-based configuration overrides
    - Custom output printer for formatted text (HTML/ANSI)
    
    Attributes:
        show_tool_use: Whether to display verbose tool execution details
        response_prefix: Optional prefix to print before agent responses
        max_line_length: Maximum line length for tool input display
        output_printer: Custom printer function for formatted output
        in_message: Internal state tracking for message boundaries
        in_tool_use: Internal state tracking for tool execution phases
        tool_count: Counter for numbering tool executions
        previous_tool_use: Cached tool information for delayed display
        disable_truncation: Environment override for tool input truncation
    """

    def __init__(self, 
                 show_tool_use: Optional[bool] = False,
                 response_prefix: Optional[str] = None,
                 max_line_length: Optional[int] = None,
                 output_printer: Optional[Callable] = None):
        """
        Initialize the callback handler with display preferences.

        Args:
            show_tool_use: Whether to show verbose tool execution feedback (default: False)
            response_prefix: Optional prefix to print before responses (default: None)
            max_line_length: Maximum line length for tool input display (default: None)
            output_printer: Optional custom printer function for formatted output (default: None)
                           If None, uses standard print(). Should have signature:
                           printer(text: str, **kwargs) -> None
        """
        logger.trace("ConfigurableCallbackHandler.__init__ called with show_tool_use={}, response_prefix='{}', max_line_length={}, output_printer={}", 
                    show_tool_use, response_prefix, max_line_length, output_printer is not None)
        
        super().__init__()
        self.show_tool_use = show_tool_use
        self.in_message = False
        self.in_tool_use = False
        self.max_line_length = max_line_length
        self.response_prefix = response_prefix
        self.output_printer = output_printer if output_printer is not None else print
        
        # Initialize tool tracking
        self.tool_count = 0
        self.previous_tool_use = None
        
        # Check env var once at startup for efficiency
        self.disable_truncation = os.environ.get('SHOW_FULL_TOOL_INPUT', 'false').lower() == 'true'
        
        logger.trace("ConfigurableCallbackHandler.__init__ completed")

    def _format_and_print_tool_input(self, tool_name: str, tool_input: Any):
        """
        Format and print tool input with structured formatting and optional truncation.
        
        Uses the structured data printer to display tool inputs in a readable format
        with hierarchical indentation. Respects truncation settings and environment
        overrides for controlling output verbosity.
        
        Args:
            tool_name: Name of the tool being called
            tool_input: Input parameters for the tool (any type)
        """
        logger.trace("_format_and_print_tool_input called with tool_name='{}', input_type={}", 
                    tool_name, type(tool_input).__name__)
        
        self.output_printer(f"\nTool #{self.tool_count}: {tool_name}")
        print_structured_data(
            tool_input, 
            1, 
            -1 if self.disable_truncation else self.max_line_length, 
            printer=self.output_printer
        )
        
        logger.trace("_format_and_print_tool_input completed")

    def __call__(self, **kwargs: Any) -> None:
        """
        Handle callback events from the agent to control terminal output.

        This is the main entry point for agent events. Processes various event types
        including message content, tool usage, reasoning text, and completion signals
        to provide appropriate user feedback based on configuration settings.
        
        The handler maintains internal state to track message boundaries and tool
        execution phases, ensuring proper formatting and timing of output elements.

        Args:
            **kwargs: Event data from the agent containing:
                - event: Dict with event type information
                - reasoningText: Optional reasoning text to display
                - data: Message content data
                - complete: Boolean indicating if message is complete
                - current_tool_use: Dict with current tool execution info
                
        Event Processing:
            - Message content: Displays agent responses with optional prefixes
            - Tool usage: Collects and displays tool information when enabled
            - Reasoning text: Shows agent's internal reasoning process
            - Completion: Handles final formatting and cleanup
        """
        if logger.level('TRACE').no >= logger._core.min_level:
            logger.trace("ConfigurableCallbackHandler.__call__ called with kwargs keys: {}", list(kwargs.keys()))

        event = kwargs.get("event", {})
        reasoningText = kwargs.get("reasoningText", False)
        data = kwargs.get("data", "")
        complete = kwargs.get("complete", False)
        current_tool_use = kwargs.get("current_tool_use", {})

        # Handle response prefix in interactive mode
        if data and not self.in_message:
            logger.trace("Starting new message, applying response prefix")
            self.in_message = True
            if self.response_prefix:
                self.output_printer(self.response_prefix, end="", flush=True)

        # Handle message completion
        if "messageStop" in event and self.in_message:
            logger.trace("Message completed, resetting state")
            self.in_message = False
            self.output_printer("", flush=True)  # Print the final newline

        # Print reasoning text
        if reasoningText:
            logger.trace("Printing reasoning text")
            self.output_printer(reasoningText, end="")

        # Print response data
        if data:
            logger.trace("Printing response data (complete={})", complete)
            self.output_printer(data, end="" if not complete else "\n")

        # Handle tool usage display based on configuration
        if self.show_tool_use:
            logger.trace("Processing tool usage display")
            if current_tool_use:
                if not self.in_tool_use:
                    self.tool_count += 1
                    self.in_tool_use = True
                    logger.trace("Started tool use #{}", self.tool_count)
                self.previous_tool_use = current_tool_use

            if "messageStop" in event and self.in_tool_use:
                logger.trace("Tool use completed, displaying tool information")
                if self.previous_tool_use:
                    self._format_and_print_tool_input(
                        tool_name=self.previous_tool_use.get("name", "Unknown tool"),
                        tool_input=self.previous_tool_use.get("input", {})
                    )
                    self.previous_tool_use = None
                self.in_tool_use = False

        # Handle completion
        if complete and data:
            logger.trace("Handling completion with data")
            self.output_printer("\n")
        
        logger.trace("ConfigurableCallbackHandler.__call__ completed")
