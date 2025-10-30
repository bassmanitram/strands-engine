"""
Tool management system for strands_agent_factory.

Provides unified tool discovery, loading, and specification creation for
Python, MCP, and A2A tools.
"""

from .factory import ToolFactory
from .mcp import MCPClient
from .a2a import A2AClientToolProvider
from .python import import_python_item
from .types import (
    TOOL_TYPE_PYTHON,
    TOOL_TYPE_MCP,
    TOOL_TYPE_MCP_STDIO,
    TOOL_TYPE_MCP_HTTP,
    TOOL_TYPE_A2A,
    MCP_TOOL_TYPES,
    ToolSpecData,
)

__all__ = [
    # Main factory
    "ToolFactory",
    
    # Tool providers
    "MCPClient",
    "A2AClientToolProvider",
    
    # Utilities
    "import_python_item",
    
    # Types and constants
    "ToolSpecData",
    "TOOL_TYPE_PYTHON",
    "TOOL_TYPE_MCP",
    "TOOL_TYPE_MCP_STDIO",
    "TOOL_TYPE_MCP_HTTP",
    "TOOL_TYPE_A2A",
    "MCP_TOOL_TYPES",
]
