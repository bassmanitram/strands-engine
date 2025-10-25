"""
Consolidated tool factory for strands_agent_factory.

This module provides the complete tool management system in a single file,
eliminating base classes and adapter patterns in favor of direct dispatch.
Supports Python tools and MCP tools with auto-detection.
"""

import os
from pathlib import Path
from typing import Any, Callable, List, Optional, TypedDict

from loguru import logger

from strands_agent_factory.messaging.content import load_structured_file
from strands_agent_factory.tools.python import import_python_item

from ..core.types import (
    PathLike,
    ToolConfig,
    EnhancedToolSpec
)

# MCP imports with availability check
try:
    from strands.tools.mcp import MCPClient as StrandsMCPClient
    _STRANDS_MCP_AVAILABLE = True
except ImportError:
    _STRANDS_MCP_AVAILABLE = False
    StrandsMCPClient = object


# Constants for tool types
TOOL_TYPE_PYTHON = "python"
TOOL_TYPE_MCP = "mcp"
TOOL_TYPE_MCP_STDIO = "mcp-stdio"
TOOL_TYPE_MCP_HTTP = "mcp-http"

MCP_TOOL_TYPES = (TOOL_TYPE_MCP, TOOL_TYPE_MCP_STDIO, TOOL_TYPE_MCP_HTTP)

# Configuration field names
CONFIG_FIELD_ID = "id"
CONFIG_FIELD_TYPE = "type"
CONFIG_FIELD_SOURCE_FILE = "source_file"
CONFIG_FIELD_DISABLED = "disabled"
CONFIG_FIELD_ERROR = "error"
CONFIG_FIELD_MODULE_PATH = "module_path"
CONFIG_FIELD_FUNCTIONS = "functions"
CONFIG_FIELD_PACKAGE_PATH = "package_path"
CONFIG_FIELD_COMMAND = "command"
CONFIG_FIELD_ARGS = "args"
CONFIG_FIELD_ENV = "env"
CONFIG_FIELD_URL = "url"

# Error messages
ERROR_MSG_MCP_DEPS_NOT_INSTALLED = "MCP dependencies not installed"
ERROR_MSG_UNKNOWN_TOOL_TYPE = "Unknown tool type '{}'"
ERROR_MSG_PYTHON_CONFIG_MISSING_FIELDS = "Python tool configuration missing required fields"
ERROR_MSG_NO_TOOLS_LOADED = "No tools could be loaded from Python module '{}'"
ERROR_MSG_MCP_TRANSPORT_MISSING = "MCP config must contain either 'command' (stdio) or 'url' (HTTP)"
ERROR_MSG_MCP_TRANSPORT_DEPS = "MCP transport dependencies not available: {}"
ERROR_MSG_TOOL_DISABLED = "Tool is disabled"
ERROR_MSG_UNEXPECTED_ERROR = "Unexpected error creating {} tool spec for '{}': {}"

# Default values
DEFAULT_TOOL_ID = "unknown"
DEFAULT_PYTHON_TOOL_ID = "unknown-python-tool"
DEFAULT_MCP_SERVER_ID = "unknown-mcp-server"
DEFAULT_FAILED_CONFIG_PREFIX = "failed-config-"


class ToolSpecData(TypedDict, total=False):
    """Data returned from tool creation methods to be merged into enhanced specs."""
    tools: Optional[List[Callable]]  # Loaded Python tools
    client: Optional['MCPClient']    # MCP client instance
    error: str                       # Error message if creation failed


def extract_tool_names(tools: List[Callable]) -> List[str]:
    """Extract clean tool names from loaded tools."""
    return [getattr(tool, 'name', tool.__name__) for tool in tools]


def validate_required_fields(config: ToolConfig, required_fields: List[str]) -> Optional[str]:
    """Validate that required fields are present in config."""
    missing_fields = [field for field in required_fields if not config.get(field)]
    if missing_fields:
        return "Missing required fields: {}".format(missing_fields)
    return None


def get_config_value(config: ToolConfig, field: str, default: Any = None) -> Any:
    """Get configuration value with consistent default handling."""
    return config.get(field, default)


def create_failed_config(file_path: Path, error: Exception) -> ToolConfig:
    """Create a failed configuration entry for error tracking."""
    return {
        CONFIG_FIELD_ID: DEFAULT_FAILED_CONFIG_PREFIX + file_path.name,
        CONFIG_FIELD_TYPE: TOOL_TYPE_PYTHON,  # Default type for failed configs
        CONFIG_FIELD_SOURCE_FILE: str(file_path),
        CONFIG_FIELD_ERROR: str(error),
    }


class MCPClient(StrandsMCPClient):
    """Enhanced strands MCPClient with filtering and server identification."""
    
    def __init__(self, server_id: str, transport_callable: Callable, requested_functions: Optional[List[str]] = None):
        logger.trace("MCPClient.__init__ called with server_id='{}', requested_functions={}", server_id, requested_functions)
        
        if not _STRANDS_MCP_AVAILABLE:
            logger.error(ERROR_MSG_MCP_DEPS_NOT_INSTALLED)
            raise ImportError(ERROR_MSG_MCP_DEPS_NOT_INSTALLED)
            
        self.server_id = server_id
        self.requested_functions = requested_functions or []
        super().__init__(transport_callable)
        
        logger.trace("MCPClient.__init__ completed for server_id='{}'", server_id)
    
    def list_tools_sync(self, pagination_token: Optional[str] = None):
        """List tools with optional filtering by requested_functions."""
        logger.trace("list_tools_sync called with pagination_token={}, requested_functions={}", pagination_token, self.requested_functions)
        
        all_tools = super().list_tools_sync(pagination_token)
        
        if not self.requested_functions:
            if logger.level('DEBUG').no >= logger._core.min_level:
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
                logger.warning("Function '{}' not found on MCP server '{}'", requested_func, self.server_id)
        
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

    def __init__(self, file_paths: List[PathLike]) -> None:
        """
        Initialize ToolFactory with configuration file paths.
        
        Args:
            file_paths: List of paths to tool configuration files
        """
        if logger.level('TRACE').no >= logger._core.min_level:
            logger.trace("ToolFactory.__init__ called with {} file paths", len(file_paths) if file_paths else 0)
        
        # Load configurations at construction time
        self._tool_configs: List[ToolConfig] = self._load_tool_configs(file_paths) if file_paths else []
        
        if logger.level('TRACE').no >= logger._core.min_level:
            logger.trace("ToolFactory.__init__ completed with {} tool configs created", len(self._tool_configs))

    def create_tool_specs(self) -> List[EnhancedToolSpec]:
        """
        Create tool specifications from loaded configurations.
        
        Returns:
            List[EnhancedToolSpec]: List of enhanced tool specification dictionaries with context
        """
        if logger.level('TRACE').no >= logger._core.min_level:
            logger.trace("create_tool_specs called with {} tool configs", len(self._tool_configs))
        
        if not self._tool_configs:
            logger.debug("create_tool_specs returning empty results (no configs)")
            return []
        
        creation_results: List[EnhancedToolSpec] = []

        for tool_config in self._tool_configs:
            enhanced_spec = self._enhance_tool_spec(tool_config)
            creation_results.append(enhanced_spec)

        logger.debug("create_tool_specs returning {} enhanced specs", len(creation_results))
        return creation_results

    def _enhance_tool_spec(self, tool_config: ToolConfig) -> EnhancedToolSpec:
        """Enhance a single tool config with loaded tool data."""
        # Start with the original config for context - this preserves source_file, id, etc.
        enhanced_spec: EnhancedToolSpec = dict(tool_config)  # type: ignore
        
        # Handle disabled tools
        if get_config_value(tool_config, CONFIG_FIELD_DISABLED, False):
            tool_id = get_config_value(tool_config, CONFIG_FIELD_ID, DEFAULT_TOOL_ID)
            logger.info("Skipping disabled tool: {}", tool_id)
            enhanced_spec[CONFIG_FIELD_ERROR] = ERROR_MSG_TOOL_DISABLED
            return enhanced_spec
        
        # Handle tools with existing errors
        existing_error = get_config_value(tool_config, CONFIG_FIELD_ERROR, None)
        if existing_error:
            tool_id = get_config_value(tool_config, CONFIG_FIELD_ID, DEFAULT_TOOL_ID)
            logger.info("Skipping tool found to be in error: {} - {}", tool_id, existing_error)
            # Error already in enhanced_spec from tool_config
            return enhanced_spec
        
        # Process valid tools
        tool_id = get_config_value(tool_config, CONFIG_FIELD_ID, DEFAULT_TOOL_ID)
        logger.debug("Creating tool spec for config: {}", tool_id)
        
        # Create the tool spec and enhance the original config with it
        tool_spec_data = self.create_tool_from_config(tool_config)
        
        # Merge the tool spec data into the enhanced spec
        if CONFIG_FIELD_ERROR in tool_spec_data:
            enhanced_spec[CONFIG_FIELD_ERROR] = tool_spec_data[CONFIG_FIELD_ERROR]
        else:
            # Merge successful tool spec data
            if 'tools' in tool_spec_data:
                enhanced_spec['tools'] = tool_spec_data['tools']
            if 'client' in tool_spec_data:
                enhanced_spec['client'] = tool_spec_data['client']
            
            # Extract tool names from loaded tools
            if enhanced_spec.get('tools'):
                enhanced_spec['tool_names'] = extract_tool_names(enhanced_spec['tools'])
            elif enhanced_spec.get('client'):
                # For MCP tools, tool_names will be populated later during agent initialization
                enhanced_spec['tool_names'] = []

        return enhanced_spec

    def create_tool_from_config(self, config: ToolConfig) -> ToolSpecData:
        """
        Create tool specification from a single configuration dictionary.
        
        Uses direct dispatch based on tool type.
        
        Args:
            config: Tool configuration dictionary
                   
        Returns:
            ToolSpecData: Tool specification data to merge into enhanced spec
        """
        tool_type = get_config_value(config, CONFIG_FIELD_TYPE)
        tool_id = get_config_value(config, CONFIG_FIELD_ID, DEFAULT_TOOL_ID)
        
        logger.trace("create_tool_from_config called for type='{}', id='{}'", tool_type, tool_id)

        # Direct dispatch to tool type handlers
        if tool_type == TOOL_TYPE_PYTHON:
            return self._create_python_tool_spec(config)
        elif tool_type in MCP_TOOL_TYPES:
            return self._create_mcp_tool_spec(config)
        else:
            logger.warning("Tool '{}' has unknown type '{}'. Skipping.", tool_id, tool_type)
            return ToolSpecData(error=ERROR_MSG_UNKNOWN_TOOL_TYPE.format(tool_type))

    def _create_python_tool_spec(self, config: ToolConfig) -> ToolSpecData:
        """Create Python tool specification directly."""
        tool_id = get_config_value(config, CONFIG_FIELD_ID, DEFAULT_PYTHON_TOOL_ID)
        logger.trace("_create_python_tool_spec called for tool_id='{}'", tool_id)
        
        try:
            # Validate required configuration
            validation_error = validate_required_fields(
                config, 
                [CONFIG_FIELD_ID, CONFIG_FIELD_MODULE_PATH, CONFIG_FIELD_FUNCTIONS, CONFIG_FIELD_SOURCE_FILE]
            )
            if validation_error:
                logger.error("Python tool '{}' configuration invalid: {}", tool_id, validation_error)
                return ToolSpecData(error=ERROR_MSG_PYTHON_CONFIG_MISSING_FIELDS)
            
            # Extract configuration
            module_path = get_config_value(config, CONFIG_FIELD_MODULE_PATH)
            func_names = get_config_value(config, CONFIG_FIELD_FUNCTIONS, [])
            package_path = get_config_value(config, CONFIG_FIELD_PACKAGE_PATH)
            src_file = get_config_value(config, CONFIG_FIELD_SOURCE_FILE)
            
            logger.debug("Python tool spec: id={}, module_path={}, functions={}", tool_id, module_path, func_names)
            
            # Load tools
            loaded_tools = self._load_python_functions(tool_id, module_path, func_names, package_path, src_file)
            
            if not loaded_tools:
                error_msg = ERROR_MSG_NO_TOOLS_LOADED.format(module_path)
                if func_names:
                    error_msg += " for functions: {}".format(func_names)
                logger.error(error_msg)
                return ToolSpecData(error=error_msg)

            logger.info("Successfully loaded {} tools from Python module: {}", len(loaded_tools), tool_id)
            return ToolSpecData(tools=loaded_tools, client=None)
            
        except Exception as e:
            tool_type = get_config_value(config, CONFIG_FIELD_TYPE, DEFAULT_TOOL_ID)
            formatted_msg = ERROR_MSG_UNEXPECTED_ERROR.format(tool_type, tool_id, e)
            logger.warning(formatted_msg)
            return ToolSpecData(error=formatted_msg)

    def _load_python_functions(self, tool_id: str, module_path: str, func_names: List[str], 
                             package_path: Optional[str], src_file: str) -> List[Callable]:
        """Load Python functions from module."""
        # Resolve base path for package_path resolution
        base_path: Optional[Path] = None
        if package_path and src_file:
            base_path = Path(src_file).parent
            logger.debug("Using base path from source file: {}", base_path)
        
        loaded_tools: List[Callable] = []

        # Look for the specific function names requested in the config
        for func_spec in func_names:
            if not isinstance(func_spec, str):
                logger.warning("Function spec '{}' is not a string in tool config '{}'. Skipping.", func_spec, tool_id)
                continue

            try:
                logger.debug("Attempting to load function '{}' from module '{}' (package_path '{}')", func_spec, module_path, package_path)
                tool = import_python_item(module_path, func_spec, package_path, base_path)
                loaded_tools.append(tool)
                
                # Clean up the tool name to remove path prefixes
                clean_function_name = func_spec.split('.')[-1]
                logger.debug("Successfully loaded callable '{}' as '{}' from module '{}'", func_spec, clean_function_name, module_path)
                
            except (ImportError, AttributeError, FileNotFoundError) as e:
                logger.warning("Error loading function '{}' from module '{}' (package_path '{}'): {}", func_spec, module_path, package_path, e)
                continue

        return loaded_tools

    def _create_mcp_tool_spec(self, config: ToolConfig) -> ToolSpecData:
        """Create MCP tool specification directly."""
        server_id = get_config_value(config, CONFIG_FIELD_ID, DEFAULT_MCP_SERVER_ID)
        functions = get_config_value(config, CONFIG_FIELD_FUNCTIONS, [])
        
        logger.trace("_create_mcp_tool_spec called for server_id='{}', functions={}", server_id, functions)
        
        try:
            # Check MCP dependencies
            if not _STRANDS_MCP_AVAILABLE:
                logger.warning(ERROR_MSG_MCP_DEPS_NOT_INSTALLED)
                return ToolSpecData(error=ERROR_MSG_MCP_DEPS_NOT_INSTALLED)
            
            # Create transport callable
            transport_callable = self._create_transport_callable(config)
            if transport_callable is None:
                logger.error(ERROR_MSG_MCP_TRANSPORT_MISSING)
                return ToolSpecData(error=ERROR_MSG_MCP_TRANSPORT_MISSING)
            
            # Create client and return tool spec data
            mcp_client = MCPClient(server_id, transport_callable, functions)
            
            logger.info("Created MCP tool spec for server: {}", server_id)
            return ToolSpecData(client=mcp_client, tools=None)
            
        except Exception as e:
            tool_type = get_config_value(config, CONFIG_FIELD_TYPE, DEFAULT_TOOL_ID)
            formatted_msg = ERROR_MSG_UNEXPECTED_ERROR.format(tool_type, server_id, e)
            logger.warning(formatted_msg)
            return ToolSpecData(error=formatted_msg)

    def _create_transport_callable(self, config: ToolConfig) -> Optional[Callable]:
        """Create appropriate transport callable based on config."""
        try:
            if CONFIG_FIELD_COMMAND in config:
                return self._create_stdio_transport(config)
            elif CONFIG_FIELD_URL in config:
                return self._create_http_transport(config)
            else:
                return None
        except ImportError as e:
            logger.error(ERROR_MSG_MCP_TRANSPORT_DEPS, e)
            raise

    def _create_stdio_transport(self, config: ToolConfig) -> Callable:
        """Create stdio transport callable."""
        command = get_config_value(config, CONFIG_FIELD_COMMAND)
        logger.trace("_create_stdio_transport called with command='{}'", command)
        
        from mcp import StdioServerParameters
        from mcp.client.stdio import stdio_client
        
        # Prepare environment
        env = os.environ.copy()
        config_env = get_config_value(config, CONFIG_FIELD_ENV)
        if config_env:
            env.update(config_env)
            if logger.level('DEBUG').no >= logger._core.min_level:
                logger.debug("Updated environment with {} variables", len(config_env))
        
        params = StdioServerParameters(
            command=command,
            args=get_config_value(config, CONFIG_FIELD_ARGS, []),
            env=env
        )
        
        transport_callable = lambda: stdio_client(params)
        logger.trace("_create_stdio_transport completed")
        return transport_callable

    def _create_http_transport(self, config: ToolConfig) -> Callable:
        """Create HTTP transport callable."""
        url = get_config_value(config, CONFIG_FIELD_URL)
        logger.trace("_create_http_transport called with url='{}'", url)
        
        from mcp.client.streamable_http import streamablehttp_client
        
        transport_callable = lambda: streamablehttp_client(url)
        logger.trace("_create_http_transport completed")
        return transport_callable

    def _load_tool_configs(self, file_paths: List[PathLike]) -> List[ToolConfig]:
        """
        Load tool configurations from configuration files.
        
        Args:
            file_paths: List of file paths to configuration files
                       
        Returns:
            List[ToolConfig]: Successfully loaded configs with error info for failed ones
        """
        if logger.level('TRACE').no >= logger._core.min_level:
            logger.trace("_load_tool_configs called with {} file paths", len(file_paths))
        
        path_list = file_paths or []
        loaded_configs: List[ToolConfig] = []
        good = 0
        bad = 0

        if logger.level('DEBUG').no >= logger._core.min_level:
            logger.debug("Loading {} tool configuration files...", len(path_list))

        for file_path in path_list:
            try:
                file_path = Path(file_path)
                config_data = load_structured_file(file_path)

                # Add source file reference for debugging
                config_data[CONFIG_FIELD_SOURCE_FILE] = str(file_path)

                # Configuration validation is performed during creation
                loaded_configs.append(config_data)  # type: ignore
                logger.info("Loaded tool config '{}' from {}", get_config_value(config_data, CONFIG_FIELD_ID, DEFAULT_TOOL_ID), file_path)
                good += 1
            except Exception as e:
                failed_config = create_failed_config(file_path, e)
                loaded_configs.append(failed_config)
                bad += 1
                # Warn this exception - no stack tracing needed
                logger.warning("Error loading tool config '{}': {}", file_path, e)

        logger.debug("Tool discovery complete: {} successful, {} failed from {} files", good, bad, len(path_list))
        return loaded_configs