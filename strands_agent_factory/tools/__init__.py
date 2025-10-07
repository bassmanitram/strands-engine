"""
Tool management system for strands_agent_factory.

This package provides comprehensive tool loading, configuration, and lifecycle
management for strands_agent_factory. It supports multiple tool types and sources
while maintaining compatibility with the strands-agents execution environment.

The tool system is designed around a clear separation of concerns:
- strands_agent_factory: Discovers, loads, and configures tools
- strands-agents: Executes tools and manages their lifecycle

Supported Tool Types:
    - MCP Tools: Model Context Protocol tools via stdio or HTTP
    - Python Tools: Native Python functions and modules
    - Custom Tools: Extensible adapter system for new tool types

Key Components:
    - ToolFactory: Main factory for creating tool instances
    - ToolAdapter: Base class for tool type adapters
    - Tool Configuration System: JSON/YAML configuration loading
    - Resource Management: Lifecycle management for tool connections

The tool system provides:
    - Automatic tool discovery from configuration files
    - Robust error handling and reporting
    - Resource cleanup and lifecycle management
    - Framework-specific tool adaptation
    - Detailed logging and debugging support

Example:
    Basic tool factory usage::
    
        from strands_agent_factory.tools import ToolFactory
        
        factory = ToolFactory()
        configs, result = factory.load_tool_configs(["/path/to/tools/"])
        tools = factory.create_tools(configs)

Note:
    Tools are loaded and configured by strands_agent_factory but executed entirely
    by strands-agents. This separation ensures clean architecture boundaries
    while providing flexibility in tool sources and types.
"""

from .base_adapter import ToolAdapter
from .factory import ToolFactory
from .mcp_adapters import MCPStdIOAdapter, MCPHTTPAdapter
from .python_adapter import PythonToolAdapter

__all__ = [
    'ToolAdapter', 
    'ToolFactory',
    'MCPStdIOAdapter', 
    'MCPHTTPAdapter', 
    'PythonToolAdapter'
]