"""
Default framework adapter for strands_engine.

This is a generic adapter for frameworks that support standard system prompts and message formats.
It contains no framework-specific logic and serves as a base for other adapters.
"""

from typing import Any, Dict, List, Optional, Tuple
from loguru import logger

from .base_adapter import FrameworkAdapter
from ..ptypes import Tool, Message

from strands.models.anthropic import AnthropicModel

class DefaultAdapter(FrameworkAdapter):
    """
    Generic adapter for frameworks that support standard system prompts and message formats.
    
    This adapter provides basic functionality without any framework-specific modifications.
    Other adapters can inherit from this or implement their own specific logic.
    """

    @property
    def framework_name(self) -> str:
        """Get the framework name."""
        return "default"

    def adapt_tools(self, tools: List[Tool], model_string: str) -> List[Tool]:
        """
        Adapt tools for the framework.
        
        Default implementation passes tools through unchanged.
        Framework-specific adapters should override this method.

        Args:
            tools: List of tools to adapt
            model_string: Model string (unused in default implementation)

        Returns:
            List of tools (unchanged)
        """
        return tools
    
    def load_model(self, model_name, model_config = None):
        model_config = model_config or {}
        if model_name:
            model_config["model"] = model_name
        client_args = model_config.pop("client_args", None)
        return AnthropicModel(client_args=client_args,model_config=model_config)
