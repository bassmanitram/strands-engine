"""
Tool management system for strands_agent_factory.

Provides unified tool discovery, loading, and specification creation for
Python, MCP, and A2A tools.
"""

# Import enhanced tool spec from core types
from ..core.types import EnhancedToolSpec
from .a2a import A2AClientToolProvider, create_a2a_tool_spec
from .factory import ToolFactory

# These are available for backward compatibility but are considered internal API
# Client code should typically use the main ToolFactory interface
from .mcp import MCPClient, create_mcp_tool_spec
from .python import import_python_item
from .types import (
    MCP_TOOL_TYPES,
    TOOL_TYPE_A2A,
    TOOL_TYPE_MCP,
    TOOL_TYPE_MCP_HTTP,
    TOOL_TYPE_MCP_STDIO,
    TOOL_TYPE_PYTHON,
    ToolSpecData,
)
from .utils import extract_tool_names

__all__ = [
    # Main factory - primary public interface
    "ToolFactory",
    # Utilities that clients might reasonably use
    "import_python_item",
    "extract_tool_names",
    # Types and constants - public configuration interface
    "ToolSpecData",
    "EnhancedToolSpec",  # Enhanced tool specification type
    "TOOL_TYPE_PYTHON",
    "TOOL_TYPE_MCP",
    "TOOL_TYPE_MCP_STDIO",
    "TOOL_TYPE_MCP_HTTP",
    "TOOL_TYPE_A2A",
    "MCP_TOOL_TYPES",
    # Tool providers - for backward compatibility
    # These are typically managed by ToolFactory but may be used directly
    "MCPClient",
    "A2AClientToolProvider",
    # Tool creation functions - for backward compatibility
    # These are typically called by ToolFactory but may be used directly
    "create_mcp_tool_spec",
    "create_a2a_tool_spec",
]
