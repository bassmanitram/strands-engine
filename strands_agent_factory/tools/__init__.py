"""
Tool management system for strands_agent_factory.

This package provides comprehensive tool loading, configuration, and lifecycle
management for strands_agent_factory. It supports multiple tool types and sources
while maintaining compatibility with the strands-agents execution environment.

The tool system uses direct dispatch instead of adapter patterns for simplicity:
- strands_agent_factory: Discovers, loads, and configures tools
- strands-agents: Executes tools and manages their lifecycle

Supported Tool Types:
    - Python Tools: Native Python functions and modules
    - MCP Tools: Model Context Protocol tools via stdio or HTTP

Key Components:
    - ToolFactory: Consolidated factory with direct dispatch
    - Tool Configuration Types: Comprehensive type system for tool configs
    - Python Tools: Utilities for importing Python tools
    - MCP Integration: Support for Model Context Protocol tools

Example:
    Basic tool factory usage::
    
        from strands_agent_factory.tools import (
            ToolFactory, 
            ToolConfig,
            EnhancedToolSpec
        )
        
        factory = ToolFactory(["/path/to/tools/"])
        enhanced_specs: List[EnhancedToolSpec] = factory.create_tool_specs()
        
    Tool configuration::
    
        from strands_agent_factory.tools import PythonToolConfig
        
        config: PythonToolConfig = {
            "id": "my_tool",
            "type": "python",
            "module_path": "my_module",
            "functions": ["my_function"]
        }
"""

# Import tool configuration types from core.types (centralized location)
from ..core.types import (
    BaseToolConfig,
    PythonToolConfig,
    MCPToolConfig,
    ToolConfig,
    EnhancedToolSpec,
    ToolSpec,  # Legacy support
)

# Import factory components
from .factory import (
    ToolFactory,
    ToolSpecData,
    MCPClient,
    # Tool type constants
    TOOL_TYPE_PYTHON,
    TOOL_TYPE_MCP,
    TOOL_TYPE_MCP_STDIO,
    TOOL_TYPE_MCP_HTTP,
    MCP_TOOL_TYPES,
    # Configuration field constants
    CONFIG_FIELD_ID,
    CONFIG_FIELD_TYPE,
    CONFIG_FIELD_SOURCE_FILE,
    CONFIG_FIELD_DISABLED,
    CONFIG_FIELD_ERROR,
    CONFIG_FIELD_MODULE_PATH,
    CONFIG_FIELD_FUNCTIONS,
    CONFIG_FIELD_PACKAGE_PATH,
    CONFIG_FIELD_COMMAND,
    CONFIG_FIELD_ARGS,
    CONFIG_FIELD_ENV,
    CONFIG_FIELD_URL,
    # Error message constants
    ERROR_MSG_MCP_DEPS_NOT_INSTALLED,
    ERROR_MSG_UNKNOWN_TOOL_TYPE,
    ERROR_MSG_PYTHON_CONFIG_MISSING_FIELDS,
    ERROR_MSG_NO_TOOLS_LOADED,
    ERROR_MSG_MCP_TRANSPORT_MISSING,
    ERROR_MSG_MCP_TRANSPORT_DEPS,
    ERROR_MSG_TOOL_DISABLED,
    ERROR_MSG_UNEXPECTED_ERROR,
    # Default value constants
    DEFAULT_TOOL_ID,
    DEFAULT_PYTHON_TOOL_ID,
    DEFAULT_MCP_SERVER_ID,
    DEFAULT_FAILED_CONFIG_PREFIX,
    # Utility functions
    extract_tool_names,
    validate_required_fields,
    get_config_value,
    create_failed_config
)

__all__ = [
    # Main factory class
    'ToolFactory',
    
    # Tool configuration types
    'BaseToolConfig',
    'PythonToolConfig', 
    'MCPToolConfig',
    'ToolConfig',
    'EnhancedToolSpec',
    'ToolSpec',  # Legacy support
    
    # Factory data types
    'ToolSpecData',
    'MCPClient',
    
    # Tool type constants
    'TOOL_TYPE_PYTHON',
    'TOOL_TYPE_MCP',
    'TOOL_TYPE_MCP_STDIO',
    'TOOL_TYPE_MCP_HTTP',
    'MCP_TOOL_TYPES',
    
    # Configuration field constants
    'CONFIG_FIELD_ID',
    'CONFIG_FIELD_TYPE',
    'CONFIG_FIELD_SOURCE_FILE',
    'CONFIG_FIELD_DISABLED',
    'CONFIG_FIELD_ERROR',
    'CONFIG_FIELD_MODULE_PATH',
    'CONFIG_FIELD_FUNCTIONS',
    'CONFIG_FIELD_PACKAGE_PATH',
    'CONFIG_FIELD_COMMAND',
    'CONFIG_FIELD_ARGS',
    'CONFIG_FIELD_ENV',
    'CONFIG_FIELD_URL',
    
    # Error message constants
    'ERROR_MSG_MCP_DEPS_NOT_INSTALLED',
    'ERROR_MSG_UNKNOWN_TOOL_TYPE',
    'ERROR_MSG_PYTHON_CONFIG_MISSING_FIELDS',
    'ERROR_MSG_NO_TOOLS_LOADED',
    'ERROR_MSG_MCP_TRANSPORT_MISSING',
    'ERROR_MSG_MCP_TRANSPORT_DEPS',
    'ERROR_MSG_TOOL_DISABLED',
    'ERROR_MSG_UNEXPECTED_ERROR',
    
    # Default value constants
    'DEFAULT_TOOL_ID',
    'DEFAULT_PYTHON_TOOL_ID',
    'DEFAULT_MCP_SERVER_ID',
    'DEFAULT_FAILED_CONFIG_PREFIX',
    
    # Utility functions
    'extract_tool_names',
    'validate_required_fields',
    'get_config_value',
    'create_failed_config'
]