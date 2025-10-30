"""
Tool-specific types and constants.

Extends core types with tool implementation details.
"""

from typing import Any, Callable, List, Optional, TypedDict

# Tool type constants
TOOL_TYPE_PYTHON = "python"
TOOL_TYPE_MCP = "mcp"
TOOL_TYPE_MCP_STDIO = "mcp-stdio"
TOOL_TYPE_MCP_HTTP = "mcp-http"
TOOL_TYPE_A2A = "a2a"

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
CONFIG_FIELD_URLS = "urls"
CONFIG_FIELD_TIMEOUT = "timeout"
CONFIG_FIELD_WEBHOOK_URL = "webhook_url"
CONFIG_FIELD_WEBHOOK_TOKEN = "webhook_token"

# Error messages
ERROR_MSG_MCP_DEPS_NOT_INSTALLED = "MCP dependencies not installed"
ERROR_MSG_A2A_DEPS_NOT_INSTALLED = "A2A dependencies not installed (strands-agents-tools[a2a_client])"
ERROR_MSG_UNKNOWN_TOOL_TYPE = "Unknown tool type '{}'"
ERROR_MSG_PYTHON_CONFIG_MISSING_FIELDS = "Python tool configuration missing required fields"
ERROR_MSG_NO_TOOLS_LOADED = "No tools could be loaded from Python module '{}'"
ERROR_MSG_MCP_TRANSPORT_MISSING = "MCP config must contain either 'command' (stdio) or 'url' (HTTP)"
ERROR_MSG_MCP_TRANSPORT_DEPS = "MCP transport dependencies not available: {}"
ERROR_MSG_A2A_CONFIG_MISSING_URLS = "A2A tool configuration missing required 'urls' field"
ERROR_MSG_TOOL_DISABLED = "Tool is disabled"
ERROR_MSG_UNEXPECTED_ERROR = "Unexpected error creating {} tool spec for '{}': {}"

# Default values
DEFAULT_TOOL_ID = "unknown"
DEFAULT_PYTHON_TOOL_ID = "unknown-python-tool"
DEFAULT_MCP_SERVER_ID = "unknown-mcp-server"
DEFAULT_A2A_PROVIDER_ID = "unknown-a2a-provider"
DEFAULT_FAILED_CONFIG_PREFIX = "failed-config-"


class ToolSpecData(TypedDict, total=False):
    """Data returned from tool creation methods to be merged into enhanced specs."""
    tools: Optional[List[Callable]]  # Loaded Python/A2A tools
    client: Optional[Any]            # MCP client instance
    error: str                       # Error message if creation failed
