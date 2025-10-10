"""
Simplified tool management system for strands_agent_factory.

This package provides streamlined tool loading, configuration, and lifecycle
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
    - Python Tools: Utilities for importing Python tools
    - Tool Configuration System: JSON/YAML configuration loading

Example:
    Basic tool factory usage::
    
        from strands_agent_factory.tools import ToolFactory
        
        factory = ToolFactory()
        configs, result = factory.load_tool_configs(["/path/to/tools/"])
        tools = factory.create_tool_specs(configs)
"""

from .factory import ToolFactory, ToolSpecCreationResult

__all__ = [
    'ToolFactory',
    'ToolSpecCreationResult'
]