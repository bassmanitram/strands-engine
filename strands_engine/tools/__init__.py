"""
Tool adapters for strands_engine.

This module provides adapters for loading tools from different sources
(MCP servers, Python modules, etc.) for use by strands-agents.

The engine loads and configures tools, but does NOT execute them.
Tool execution is handled entirely by strands-agents.
"""

from .base_adapter import ToolAdapter
from .factory import ToolFactory
from .mcp_adapters import MCPStdIOAdapter, MCPHTTPAdapter
from .python_adapter import PythonToolAdapter
from .discovery import discover_tool_configs

__all__ = [
    'ToolAdapter', 
    'ToolFactory',
    'MCPStdIOAdapter', 
    'MCPHTTPAdapter', 
    'PythonToolAdapter',
    'discover_tool_configs'
]