"""
Tool factory for strands_engine.

Provides a centralized factory for creating tools from different sources
using registered adapters. Tools are loaded for strands-agents to execute.
"""

from contextlib import ExitStack
from typing import Any, Dict, List

from loguru import logger

from ..ptypes import ToolCreationResult
from .base_adapter import ToolAdapter
from .python_adapter import PythonToolAdapter
from .mcp_adapters import MCPHTTPAdapter, MCPStdIOAdapter


class ToolFactory:
    """
    Factory that uses registered adapters to create tools.
    
    The factory loads and configures tools from different sources
    but does NOT execute them. Tool execution is handled by strands-agents.
    """

    def __init__(self, exit_stack: ExitStack):
        """
        Initialize the tool factory.
        
        Args:
            exit_stack: Context manager for resource cleanup
        """
        self._adapters: Dict[str, ToolAdapter] = {
            "python": PythonToolAdapter(exit_stack),
            "mcp-stdio": MCPStdIOAdapter(exit_stack),
            "mcp-http": MCPHTTPAdapter(exit_stack)
        }

    def create_tools(self, config: Dict[str, Any]) -> ToolCreationResult:
        """
        Create tools from a configuration dictionary.
        
        Args:
            config: Tool configuration dictionary
            
        Returns:
            ToolCreationResult with loaded tools and metadata
        """
        tool_type = config.get("type")

        # Special handling for MCP to distinguish between stdio and http
        if tool_type == "mcp":
            if "command" in config:
                tool_type = "mcp-stdio"
            elif "url" in config:
                tool_type = "mcp-http"
            else:
                logger.error(f"MCP config for '{config.get('id')}' is missing 'url' or 'command'. Cannot connect.")
                return ToolCreationResult(
                    tools=[],
                    requested_functions=config.get("functions", []),
                    found_functions=[],
                    missing_functions=config.get("functions", []),
                    error="MCP config missing 'url' or 'command'"
                )

        adapter = self._adapters.get(tool_type)
        if adapter:
            logger.debug(f"Creating tools using {tool_type} adapter for '{config.get('id')}'")
            return adapter.create(config)
        else:
            logger.warning(f"Tool '{config.get('id')}' has unknown type '{tool_type}'. Skipping.")
            return ToolCreationResult(
                tools=[],
                requested_functions=config.get("functions", []),
                found_functions=[],
                missing_functions=config.get("functions", []),
                error=f"Unknown tool type '{tool_type}'"
            )

    def register_adapter(self, tool_type: str, adapter: ToolAdapter) -> None:
        """
        Register a new tool adapter.
        
        Args:
            tool_type: Type identifier for the adapter
            adapter: Tool adapter instance
        """
        self._adapters[tool_type] = adapter
        logger.info(f"Registered tool adapter for type: {tool_type}")

    def get_supported_types(self) -> List[str]:
        """Get list of supported tool types."""
        return list(self._adapters.keys())