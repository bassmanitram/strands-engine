"""
MCP (Model Context Protocol) tool adapters for strands_engine.

Loads tools from MCP servers via stdio or HTTP for strands-agents to execute.
"""

import os
from typing import Any, Dict

from loguru import logger

from ..ptypes import ToolCreationResult
from .base_adapter import ToolAdapter


class MCPStdIOAdapter(ToolAdapter):
    """
    Adapter for creating MCP tools from a stdio command.
    
    Connects to MCP servers via stdio transport and loads their tools
    for strands-agents to execute. The engine loads tools but never executes them.
    """

    def create(self, config: Dict[str, Any]) -> ToolCreationResult:
        """
        Create tools from MCP server via stdio.
        
        Args:
            config: MCP stdio configuration
            
        Returns:
            ToolCreationResult with loaded MCP tools
        """
        server_id = config.get("id", "unknown-stdio-server")
        logger.debug(f"Starting MCP server '{server_id}' with command: {config.get('command')}")

        try:
            # Import MCP dependencies when needed
            from mcp import StdioServerParameters
            from strands.tools.mcp import MCPClient
            from mcp.client.stdio import stdio_client
        except ImportError as e:
            logger.error(f"MCP dependencies not available: {e}")
            return ToolCreationResult(
                tools=[],
                requested_functions=config.get("functions", []),
                found_functions=[],
                missing_functions=config.get("functions", []),
                error="MCP dependencies not installed"
            )

        process_env = os.environ.copy()
        if 'env' in config:
            process_env.update(config['env'])

        params = StdioServerParameters(
            command=config["command"], 
            args=config.get("args", []), 
            env=process_env
        )

        def create_stdio_client():
            return stdio_client(params)

        try:
            client = self.exit_stack.enter_context(MCPClient(create_stdio_client))
            all_tools = client.list_tools_sync()

            # Check if specific functions were requested
            requested_functions = config.get("functions", [])
            if requested_functions:
                # Filter tools to only include requested functions
                found_functions = []
                filtered_tools = []

                for requested_func in requested_functions:
                    found = False
                    for tool in all_tools:
                        if hasattr(tool, 'tool_spec') and tool.tool_spec.get('name') == requested_func:
                            filtered_tools.append(tool)
                            found_functions.append(requested_func)
                            found = True
                            break
                    if not found:
                        logger.warning(f"MCP server '{server_id}' does not provide requested function '{requested_func}'")

                missing_functions = [f for f in requested_functions if f not in found_functions]
                tools_to_return = filtered_tools
            else:
                # No specific functions requested, return all tools
                requested_functions = []
                found_functions = [tool.tool_spec.get('name', 'unnamed') for tool in all_tools if hasattr(tool, 'tool_spec')]
                missing_functions = []
                tools_to_return = all_tools

            logger.info(f"Successfully loaded {len(tools_to_return)} tools from MCP server: {server_id}")
            return ToolCreationResult(
                tools=tools_to_return,
                requested_functions=requested_functions,
                found_functions=found_functions,
                missing_functions=missing_functions,
                error=None
            )
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server_id}: {e}")
            return ToolCreationResult(
                tools=[],
                requested_functions=config.get("functions", []),
                found_functions=[],
                missing_functions=config.get("functions", []),
                error=str(e)
            )


class MCPHTTPAdapter(ToolAdapter):
    """
    Adapter for creating MCP tools from an HTTP endpoint.
    
    Connects to MCP servers via HTTP transport and loads their tools
    for strands-agents to execute. The engine loads tools but never executes them.
    """

    def create(self, config: Dict[str, Any]) -> ToolCreationResult:
        """
        Create tools from MCP server via HTTP.
        
        Args:
            config: MCP HTTP configuration
            
        Returns:
            ToolCreationResult with loaded MCP tools
        """
        server_id = config.get("id", "unknown-http-server")
        url = config.get("url")
        logger.debug(f"Connecting to MCP server '{server_id}' via HTTP at {url}")

        try:
            # Import MCP dependencies when needed
            from strands.tools.mcp import MCPClient
            from mcp.client.streamable_http import streamablehttp_client
        except ImportError as e:
            logger.error(f"MCP dependencies not available: {e}")
            return ToolCreationResult(
                tools=[],
                requested_functions=config.get("functions", []),
                found_functions=[],
                missing_functions=config.get("functions", []),
                error="MCP dependencies not installed"
            )

        def create_http_client():
            return streamablehttp_client(url)

        try:
            client = self.exit_stack.enter_context(MCPClient(create_http_client))
            all_tools = client.list_tools_sync()

            # Check if specific functions were requested
            requested_functions = config.get("functions", [])
            if requested_functions:
                # Filter tools to only include requested functions
                found_functions = []
                filtered_tools = []

                for requested_func in requested_functions:
                    found = False
                    for tool in all_tools:
                        if hasattr(tool, 'tool_spec') and tool.tool_spec.get('name') == requested_func:
                            filtered_tools.append(tool)
                            found_functions.append(requested_func)
                            found = True
                            break
                    if not found:
                        logger.warning(f"MCP server '{server_id}' does not provide requested function '{requested_func}'")

                missing_functions = [f for f in requested_functions if f not in found_functions]
                tools_to_return = filtered_tools
            else:
                # No specific functions requested, return all tools
                requested_functions = []
                found_functions = [tool.tool_spec.get('name', 'unnamed') for tool in all_tools if hasattr(tool, 'tool_spec')]
                missing_functions = []
                tools_to_return = all_tools

            logger.info(f"Successfully loaded {len(tools_to_return)} tools from MCP server: {server_id}")
            return ToolCreationResult(
                tools=tools_to_return,
                requested_functions=requested_functions,
                found_functions=found_functions,
                missing_functions=missing_functions,
                error=None
            )
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server_id}: {e}")
            return ToolCreationResult(
                tools=[],
                requested_functions=config.get("functions", []),
                found_functions=[],
                missing_functions=config.get("functions", []),
                error=str(e)
            )