"""
Consolidated tool factory for strands_agent_factory.

This module provides the complete tool management system in a single file,
eliminating base classes and adapter patterns in favor of direct dispatch.
Supports Python tools and MCP tools with auto-detection.
"""

import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from loguru import logger

from strands_agent_factory.messaging.content import load_structured_file
from strands_agent_factory.tools.python import import_python_item

from ..core.types import PathLike, ToolConfig, ToolDiscoveryResult, ToolSpec

# MCP imports with availability check
try:
    from strands.tools.mcp import MCPClient as StrandsMCPClient
    _STRANDS_MCP_AVAILABLE = True
except ImportError:
    _STRANDS_MCP_AVAILABLE = False
    StrandsMCPClient = object


class ToolSpecCreationResult:
    """
    Result of tool specification creation operations.
    
    Provides comprehensive information about tool spec creation success/failure
    including metadata for debugging and tracking.
    """
    
    def __init__(self, tool_spec: ToolSpec = None, requested_functions: list = None, error: str = None):
        self.tool_spec = tool_spec
        self.requested_functions = requested_functions or []
        self.error = error


class MCPClient(StrandsMCPClient):
    """Enhanced strands MCPClient with filtering and server identification."""
    
    def __init__(self, server_id: str, transport_callable: Callable, requested_functions: Optional[List[str]] = None):
        logger.trace("MCPClient.__init__ called with server_id='{}', requested_functions={}", server_id, requested_functions)
        
        if not _STRANDS_MCP_AVAILABLE:
            logger.error("MCP dependencies not installed")
            raise ImportError("MCP dependencies not installed")
            
        self.server_id = server_id
        self.requested_functions = requested_functions or []
        super().__init__(transport_callable)
        
        logger.trace("MCPClient.__init__ completed for server_id='{}'", server_id)
    
    def list_tools_sync(self, pagination_token: Optional[str] = None):
        """List tools with optional filtering by requested_functions."""
        logger.trace("list_tools_sync called with pagination_token={}, requested_functions={}", pagination_token, self.requested_functions)
        
        all_tools = super().list_tools_sync(pagination_token)
        
        if not self.requested_functions:
            logger.debug("list_tools_sync returning {} unfiltered tools", len(all_tools) if all_tools else 0)
            return all_tools
            
        # Filter tools by requested function names
        filtered_tools = []
        for requested_func in self.requested_functions:
            for tool in all_tools:
                if tool.tool_name == requested_func:
                    filtered_tools.append(tool)
                    break
            else:
                logger.warning(f"Function '{requested_func}' not found on MCP server '{self.server_id}'")
        
        logger.debug("list_tools_sync returning {} filtered tools", len(filtered_tools))
        return filtered_tools


class ToolFactory:
    """
    Centralized factory for tool discovery, loading, and specification creation.
    
    ToolFactory coordinates the complete tool specification management lifecycle for
    strands_agent_factory, from configuration file discovery through tool specification
    creation. Uses direct dispatch instead of adapter pattern for simplicity.
    
    The factory creates tool specifications that describe how to load and execute
    tools, but never executes tools directly.
    """

    def __init__(self, file_paths: List[PathLike]):
        """
        Initialize ToolFactory with configuration file paths.
        
        Args:
            file_paths: List of paths to tool configuration files
        """
        if logger.level('TRACE').no >= logger._core.min_level:
            logger.trace("ToolFactory.__init__ called with {} file paths", len(file_paths) if file_paths else 0)
        
        # Load configurations at construction time
        self._tool_configs, self._tool_discovery_results = self._load_tool_configs(file_paths) if file_paths else ([], None)
        
        if logger.level('TRACE').no >= logger._core.min_level:
            logger.trace("ToolFactory.__init__ completed with {} tool configs loaded", len(self._tool_configs))

    def create_tool_specs(self) -> Tuple[Optional[ToolDiscoveryResult], List[ToolSpecCreationResult]]:
        """
        Create tool specifications from loaded configurations.
        
        Returns:
            Tuple containing:
            - ToolDiscoveryResult: Discovery statistics (None if no configs)
            - List[ToolSpecCreationResult]: Results from each tool spec creation attempt
        """
        if logger.level('TRACE').no >= logger._core.min_level:
            logger.trace("create_tool_specs called with {} tool configs", len(self._tool_configs))
        
        if not self._tool_configs:
            logger.debug("create_tool_specs returning empty results (no configs)")
            return (None, [])
        
        creation_results = []

        for tool_config in self._tool_configs:
            # Skip disabled tools
            if tool_config.get('disabled', False):
                logger.info(f"Skipping disabled tool: {tool_config.get('id', 'unknown')}")
                continue
                
            logger.debug("Creating tool spec for config: {}", tool_config.get('id', 'unknown'))
            
            try:
                result = self.create_tool_spec_from_config(tool_config)
                creation_results.append(result)

            except Exception as e:
                message = f"Exception creating tool spec from '{tool_config.get('id', 'unknown')}': {e}"
                creation_results.append(ToolSpecCreationResult(
                    tool_spec=None,
                    requested_functions=tool_config.get("functions", []),
                    error=message
                ))
                logger.warning(message)
        
        logger.debug("create_tool_specs returning {} results", len(creation_results))
        return (self._tool_discovery_results, creation_results)

    def create_tool_spec_from_config(self, config: Dict[str, Any]) -> ToolSpecCreationResult:
        """
        Create tool specification from a single configuration dictionary.
        
        Uses direct dispatch based on tool type.
        
        Args:
            config: Tool configuration dictionary
                   
        Returns:
            ToolSpecCreationResult: Detailed result of the tool spec creation process
        """
        tool_type = config.get("type")
        tool_id = config.get("id", "unknown")
        
        logger.trace("create_tool_spec_from_config called for type='{}', id='{}'", tool_type, tool_id)

        # Direct dispatch to tool type handlers
        if tool_type == "python":
            result = self._create_python_tool_spec(config)
        elif tool_type in ("mcp", "mcp-stdio", "mcp-http"):
            result = self._create_mcp_tool_spec(config)
        else:
            logger.warning(f"Tool '{tool_id}' has unknown type '{tool_type}'. Skipping.")
            result = ToolSpecCreationResult(
                tool_spec=None,
                requested_functions=config.get("functions", []),
                error=f"Unknown tool type '{tool_type}'"
            )
        
        logger.debug("create_tool_spec_from_config returning result for '{}': error={}", tool_id, result.error)
        return result

    def _create_python_tool_spec(self, config: Dict[str, Any]) -> ToolSpecCreationResult:
        """Create Python tool specification directly."""
        tool_id = config.get("id", "unknown-python-tool")
        logger.trace("_create_python_tool_spec called for tool_id='{}'", tool_id)
        
        # Extract configuration
        module_path = config.get("module_path")
        func_names = config.get("functions", [])
        package_path = config.get("package_path")
        src_file = config.get("source_file")
        
        logger.debug("Python tool spec: id={}, module_path={}, functions={}", tool_id, module_path, func_names)
        
        # Validate required configuration
        if not all([tool_id, module_path, func_names, src_file]):
            error_msg = "Python tool configuration missing required fields"
            logger.error(f"Python tool '{tool_id}' missing required fields: {config}")
            return ToolSpecCreationResult(
                tool_spec=None,
                requested_functions=func_names,
                error=error_msg
            )
        
        # Resolve base path for package_path resolution
        base_path = None
        if package_path and src_file:
            base_path = Path(src_file).parent
            logger.debug("Using base path from source file: {}", base_path)
        
        loaded_tools = []
        
        try:
            loaded_tools = []
            found_functions = []
            missing_functions = []

            # Look for the specific function names requested in the config
            for func_spec in func_names:
                if not isinstance(func_spec, str):
                    logger.warning(f"Function spec '{func_spec}' is not a string in tool config '{tool_id}'. Skipping.")
                    missing_functions.append(str(func_spec))
                    continue

                try:
                    logger.debug("Attempting to load function '{}' from module '{}' (package_path '{}')", func_spec, module_path, package_path)
                    tool = import_python_item(module_path, func_spec, package_path, base_path)
                except (ImportError, AttributeError, FileNotFoundError) as e:
                    logger.warn(f"Error loading function '{func_spec}' from module '{module_path}' (package_path '{package_path}')): {e}")
                    missing_functions.append(func_spec)
                    continue

                # Clean up the tool name to remove path prefixes
                clean_function_name = func_spec.split('.')[-1]
                loaded_tools.append(tool)
                found_functions.append(clean_function_name)
                logger.debug("Successfully loaded callable '{}' as '{}' from module '{}'", func_spec, clean_function_name, module_path)

            logger.info(f"Successfully loaded {len(loaded_tools)} tools from Python module: {tool_id}")

            # Check if any tools were successfully loaded
            if not loaded_tools:
                error_msg = f"No tools could be loaded from Python module '{module_path}'"
                if func_names:
                    error_msg += f" for functions: {func_names}"
                logger.error(error_msg)
                return ToolSpecCreationResult(
                    tool_spec=None,
                    requested_functions=func_names,
                    error=error_msg
                )

            # Create ToolSpec with loaded tools
            tool_spec: ToolSpec = {
                "tools": loaded_tools,
                "client": None
            }

            logger.info(f"Successfully created tool spec for {len(loaded_tools)} tools from Python module: {tool_id}")
            result = ToolSpecCreationResult(
                tool_spec=tool_spec,
                requested_functions=func_names,
                error=None
            )
            
        except Exception as e:
            error_msg = f"Unexpected error creating Python tool spec for '{tool_id}': {e}"
            # Warn this execption - no stack trace needed
            logger.warning(error_msg)
            result = ToolSpecCreationResult(
                tool_spec=None,
                requested_functions=func_names,
                error=error_msg
            )
        
        logger.debug("_create_python_tool_spec returning for '{}': error={}", tool_id, result.error)
        return result

    def _create_mcp_tool_spec(self, config: Dict[str, Any]) -> ToolSpecCreationResult:
        """Create MCP tool specification directly."""
        server_id = config.get("id", "unknown-mcp-server")
        functions = config.get("functions", [])
        
        logger.trace("_create_mcp_tool_spec called for server_id='{}', functions={}", server_id, functions)
        
        # Check MCP dependencies
        if not _STRANDS_MCP_AVAILABLE:
            error_msg = "MCP dependencies not installed"
            logger.warning(error_msg)
            result = ToolSpecCreationResult(
                tool_spec=None,
                requested_functions=functions,
                error=error_msg
            )
            logger.debug("_create_mcp_tool_spec returning for '{}': error={}", server_id, result.error)
            return result
        
        # Auto-detect transport and create transport callable
        transport_callable = None
        try:
            if "command" in config:
                transport_callable = self._create_stdio_transport(config)
                logger.debug("Created stdio transport")
            elif "url" in config:
                transport_callable = self._create_http_transport(config)
                logger.debug("Created HTTP transport")
            else:
                error_msg = "MCP config must contain either 'command' (stdio) or 'url' (HTTP)"
                logger.error(error_msg)
                result = ToolSpecCreationResult(
                    tool_spec=None,
                    requested_functions=functions,
                    error=error_msg
                )
                logger.debug("_create_mcp_tool_spec returning for '{}': error={}", server_id, result.error)
                return result
        except ImportError as e:
            error_msg = f"MCP transport dependencies not available: {e}"
            logger.error(error_msg)
            result = ToolSpecCreationResult(
                tool_spec=None,
                requested_functions=functions,
                error=error_msg
            )
            logger.debug("_create_mcp_tool_spec returning for '{}': error={}", server_id, result.error)
            return result
        
        # Create client and tool spec
        mcp_client = MCPClient(server_id, transport_callable, functions)
        tool_spec: ToolSpec = {"client": mcp_client, "tools": None}
        
        logger.info(f"Created MCP tool spec for server: {server_id}")
        result = ToolSpecCreationResult(tool_spec=tool_spec, requested_functions=functions, error=None)
        
        logger.debug("_create_mcp_tool_spec returning for '{}': error={}", server_id, result.error)
        return result

    def _create_stdio_transport(self, config: Dict[str, Any]) -> Callable:
        """Create stdio transport callable."""
        logger.trace("_create_stdio_transport called with command='{}'", config.get('command'))
        
        from mcp import StdioServerParameters
        from mcp.client.stdio import stdio_client
        
        # Prepare environment
        env = os.environ.copy()
        if 'env' in config:
            env.update(config['env'])
            logger.debug("Updated environment with {} variables", len(config['env']))
        
        params = StdioServerParameters(
            command=config["command"],
            args=config.get("args", []),
            env=env
        )
        
        transport_callable = lambda: stdio_client(params)
        logger.trace("_create_stdio_transport completed")
        return transport_callable

    def _create_http_transport(self, config: Dict[str, Any]) -> Callable:
        """Create HTTP transport callable."""
        url = config["url"]
        logger.trace("_create_http_transport called with url='{}'", url)
        
        from mcp.client.streamable_http import streamablehttp_client
        
        transport_callable = lambda: streamablehttp_client(url)
        logger.trace("_create_http_transport completed")
        return transport_callable

    def _load_tool_configs(self, file_paths: List[PathLike]) -> Tuple[List[ToolConfig], ToolDiscoveryResult]:
        """
        Load tool configurations from configuration files.
        
        Args:
            file_paths: List of file paths to configuration files
                       
        Returns:
            Tuple[List[ToolConfig], ToolDiscoveryResult]: Successfully loaded configs and discovery stats
        """
        if logger.level('TRACE').no >= logger._core.min_level:
            logger.trace("_load_tool_configs called with {} file paths", len(file_paths))
        
        path_list = file_paths or []
        successful_configs: List[ToolConfig] = []
        failed_configs: List[Dict[str, Any]] = []

        logger.debug("Loading {} tool configuration files...", len(path_list))

        for file_path in path_list:
            try:
                file_path = Path(file_path)
                config_data = load_structured_file(file_path)

                # Add source file reference for debugging
                config_data['source_file'] = str(file_path)

                # Configuration validation is performed during creation
                successful_configs.append(config_data)
                logger.info(f"Loaded tool config '{config_data.get('id', 'unknown')}' from {file_path}")

            except Exception as e:
                failed_configs.append({
                    'file_path': str(file_path),
                    'config_id': 'unknown',
                    'error': str(e),
                    'config_data': None
                })
                # Warn this exception - no stack tracing needed
                logger.warning(f"Error loading tool config '{file_path}': {e}")

        discovery_result = ToolDiscoveryResult(
            successful_configs,
            failed_configs,
            len(path_list)
        )

        logger.info(f"Tool discovery complete: {len(successful_configs)} successful, {len(failed_configs)} failed from {len(path_list)} files")
        logger.debug("_load_tool_configs returning {} successful configs", len(successful_configs))
        return successful_configs, discovery_result