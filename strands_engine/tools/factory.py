"""
Tool factory for strands_engine.

Provides a centralized factory for creating tools from different sources
using registered adapters. Tools are loaded for strands-agents to execute.
"""

from contextlib import ExitStack
from pathlib import Path
from typing import Any, Dict, List, Tuple

from loguru import logger

from strands_engine.utils import load_structured_file

from ..ptypes import PathLike, Tool, ToolConfig, ToolCreationResult, ToolDiscoveryResult
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

    def create_tools(self, tool_configs: List[ToolConfig]) -> List[ToolCreationResult]:

        creation_results = []

        for tool_config in tool_configs:
            # Skip disabled tools
            if tool_config.get('disabled', False):
                logger.info(f"Skipping disabled tool: {tool_config.get('id', 'unknown')}")
                continue
                
            logger.debug(f"Creating tools for config: {tool_config.get('id', 'unknown')}")
            
            try:
                result = self.create_tools_from_config(tool_config)
                creation_results.extend(result)

            except Exception as e:
                message = "Exception loading tools from '{tool_config.get('id', 'unknown')}': {e}"
                creation_results.extend(ToolCreationResult(
                    error=message
                ))
                logger.error(message)
        
        return creation_results

    def create_tools_from_config(self, config: Dict[str, Any]) -> ToolCreationResult:
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

    def load_tool_configs(self, file_paths: List[PathLike]) -> Tuple[List[ToolConfig], ToolDiscoveryResult]:
        """
        Load tool configurations from resolved file paths.
        Engine only validates the configuration structure, not tool functionality.

        Args:
            file_paths: Resolved file path(s) to .tools.json files, or None to disable discovery

        Returns:
            Tuple of (successful_configs, discovery_result)
        """
        path_list = file_paths or []

        successful_configs: List[ToolConfig] = []
        failed_configs: List[Dict[str, Any]] = []

        logger.debug(f"Loading {len(path_list)} tool configuration files...")

        for file_path in path_list:
            try:
                file_path = Path(file_path)
                config_data = load_structured_file(file_path)

                # Add source file reference for debugging
                config_data['source_file'] = str(file_path)

                # Enhanced validation with detailed error messages
                successful_configs.append(config_data)
                logger.info(f"Loaded tool config '{config_data.get('id', 'unknown')}' from {file_path}")

            except Exception as e:
                failed_configs.append({
                    'file_path': str(file_path),
                    'config_id': 'unknown',
                    'error': e,
                    'config_data': None
                })
                logger.error(f"Error loading tool config '{file_path}': {e}")

        discovery_result = ToolDiscoveryResult(
            successful_configs,
            failed_configs,
            len(path_list)
        )

        logger.info(f"Tool discovery complete: {len(successful_configs)} successful, {len(failed_configs)} failed from {len(path_list)} files")
        return successful_configs, discovery_result
