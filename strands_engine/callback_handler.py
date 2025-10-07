"""
Callback handler for strands_engine without prompt_toolkit dependencies.
"""

from typing import Any, Optional
from loguru import logger
from strands.handlers.callback_handler import PrintingCallbackHandler


class EngineCallbackHandler(PrintingCallbackHandler):
    """
    Callback handler for strands_engine output without prompt_toolkit dependencies.
    """

    def __init__(self, show_tool_use: Optional[bool] = False):
        """Initialize the callback handler."""
        super().__init__()
        self.show_tool_use = show_tool_use
        self.in_message = False
        self.in_tool_use = False
        self.tool_count = 0
        self.previous_tool_use = None

    def __call__(self, **kwargs: Any) -> None:
        """Handle agent output events."""
        logger.trace("EngineCallbackHandler.__call__ arguments: {}", kwargs)

        event = kwargs.get("event", {})
        reasoningText = kwargs.get("reasoningText", False)
        data = kwargs.get("data", "")
        complete = kwargs.get("complete", False)
        current_tool_use = kwargs.get("current_tool_use", {})

        if "messageStop" in event and self.in_message:
            self.in_message = False
            print(flush=True)

        if reasoningText:
            print(reasoningText, end="")

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

        if complete and data:
            print("\n")