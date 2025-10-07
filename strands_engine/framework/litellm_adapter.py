"""
LiteLLM framework adapter for strands_engine.

This adapter handles LiteLLM-specific functionality, particularly tool schema cleaning
for compatibility with different underlying providers.
"""

from typing import List, Tuple
from loguru import logger
from strands.models.litellm import LiteLLMModel

from .base_adapter import FrameworkAdapter
from ..ptypes import Tool
from .._utils import recursively_remove


class LiteLLMAdapter(FrameworkAdapter):
    """
    Adapter for LiteLLM framework.
    
    LiteLLM provides a unified interface to multiple AI providers, but requires
    specific tool schema modifications for compatibility with certain providers.
    """

    @property
    def framework_name(self) -> str:
        """Get the framework name."""
        return "litellm"

    def load_model(self, model_name, model_config = None):
        model_config = model_config or {}
        if model_name:
            model_config["model_id"] = model_name
        client_args = model_config.pop("client_args", None)
        return LiteLLMModel(client_args=client_args,model_config=model_config)

    def adapt_tools(self, tools: List[Tool], model_string: str) -> List[Tool]:
        """
        Adapts tool schemas for LiteLLM compatibility.
        
        LiteLLM requires cleaning tool schemas to remove 'additionalProperties',
        which is not supported by some underlying APIs like Google VertexAI.

        Args:
            tools: List of tools to adapt
            model_string: Model string to determine adaptations needed

        Returns:
            List of adapted tools
        """
        # For LiteLLM, always clean additionalProperties regardless of underlying provider
        if tools:
            logger.debug("LiteLLM adapter: Cleaning tool schemas to remove 'additionalProperties'.")
            
            for tool in tools:
                if hasattr(tool, 'TOOL_SPEC'):
                    tool_name = getattr(tool, 'name', 'unnamed-tool')
                    logger.trace(f"Cleaning TOOL_SPEC for tool: {tool_name}")
                    recursively_remove(tool.TOOL_SPEC, "additionalProperties")
                elif hasattr(tool, '_tool_spec'):
                    tool_name = getattr(tool, 'name', 'unnamed-tool')
                    logger.trace(f"Cleaning _tool_spec for tool: {tool_name}")
                    recursively_remove(tool._tool_spec, "additionalProperties")
                else:
                    # Handle module-based tools
                    module_funcs = [name for name in dir(tool) if callable(getattr(tool, name))]
                    for func_name in module_funcs:
                        func = getattr(tool, func_name)
                        if hasattr(func, '_tool_spec'):
                            func_name_or_attr = getattr(func, 'name', func_name)
                            logger.trace(f"Cleaning _tool_spec for tool: {func_name_or_attr}")
                            recursively_remove(func._tool_spec, "additionalProperties")

        return tools