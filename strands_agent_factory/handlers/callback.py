"""
Custom callback handler for strands_agent_factory.

This module provides a configurable callback handler that controls output verbosity
and tool execution feedback for strands-agents Agent instances.
"""

import os
from typing import Any, Optional

from loguru import logger

from strands_agent_factory.core.utils import print_structured_data


class ConfigurableCallbackHandler:
    """
    Configurable callback handler for controlling agent output verbosity.

    This handler provides configurable control over tool execution feedback:
    - When show_tool_use=False (default): Suppresses verbose tool execution details
    - When show_tool_use=True: Shows full tool execution feedback with structured formatting
    
    Also handles:
    - Response prefix printing in interactive mode
    - Final newline after responses
    - Tool input formatting with optional truncation
    """

    def __init__(self, 
                 show_tool_use: Optional[bool] = False,
                 response_prefix: Optional[str] = None,
                 max_line_length: Optional[int] = None):
        """
        Initialize the callback handler.

        Args:
            show_tool_use: Whether to show verbose tool execution feedback (default: False)
            response_prefix: Optional prefix to print before responses (default: None)
            max_line_length: Maximum line length for tool input display (default: None)
        """
        logger.trace("ConfigurableCallbackHandler.__init__ called with show_tool_use={}, response_prefix='{}', max_line_length={}", show_tool_use, response_prefix, max_line_length)
        
        super().__init__()
        self.show_tool_use = show_tool_use
        self.in_message = False
        self.in_tool_use = False
        self.max_line_length = max_line_length
        self.response_prefix = response_prefix
        
        # Initialize tool tracking
        self.tool_count = 0
        self.previous_tool_use = None
        
        # Check env var once at startup for efficiency
        self.disable_truncation = os.environ.get('SHOW_FULL_TOOL_INPUT', 'false').lower() == 'true'
        
        logger.trace("ConfigurableCallbackHandler.__init__ completed")

    def _format_and_print_tool_input(self, tool_name: str, tool_input: Any):
        """
        Format and print tool input with structured formatting.
        
        Args:
            tool_name: Name of the tool being called
            tool_input: Input parameters for the tool
        """
        logger.trace("_format_and_print_tool_input called with tool_name='{}', input_type={}", tool_name, type(tool_input).__name__)
        
        print(f"\nTool #{self.tool_count}: {tool_name}")
        print_structured_data(
            tool_input, 
            1, 
            -1 if self.disable_truncation else self.max_line_length, 
            printer=print
        )
        
        logger.trace("_format_and_print_tool_input completed")

    def __call__(self, **kwargs: Any) -> None:
        """
        Handle callback events from the agent to control terminal output.

        Processes various agent events including message content, tool usage,
        and completion signals to provide appropriate user feedback.

        Args:
            **kwargs: Event data from the agent containing event type, data, and metadata
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
            self.in_message = True
            if self.response_prefix:
                print(self.response_prefix, end="", flush=True)

        # Handle message completion
        if "messageStop" in event and self.in_message:
            self.in_message = False
            print(flush=True)  # Print the final newline

        # Print reasoning text
        if reasoningText:
            print(reasoningText, end="")

        # Print response data
        if data:
            print(data, end="" if not complete else "\n")

        # Handle tool usage display based on configuration
        if self.show_tool_use:
            if current_tool_use:
                if not self.in_tool_use:
                    self.tool_count += 1
                    self.in_tool_use = True
                self.previous_tool_use = current_tool_use

            if "messageStop" in event and self.in_tool_use:
                if self.previous_tool_use:
                    self._format_and_print_tool_input(
                        tool_name=self.previous_tool_use.get("name", "Unknown tool"),
                        tool_input=self.previous_tool_use.get("input", {})
                    )
                    self.previous_tool_use = None
                self.in_tool_use = False

        # Handle completion
        if complete and data:
            print("\n")
        
        logger.trace("ConfigurableCallbackHandler.__call__ completed")