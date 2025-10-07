"""
Model Context Protocol (MCP) tool adapters for strands_agent_factory.

This module provides adapters for connecting to MCP servers and loading their
tools for use by strands-agents. MCP is a protocol that enables AI agents to
securely connect to external systems and access their capabilities through
standardized tool interfaces.

The MCP adapters support both transport mechanisms defined by the MCP specification:
- stdio: Communication via standard input/output with a subprocess
- HTTP: Communication via HTTP/SSE with a web service

Both adapters handle connection management, tool discovery, and resource cleanup
while providing comprehensive error handling and logging. The loaded tools are
made available to strands-agents for execution, maintaining the clean separation
between tool loading (engine) and tool execution (strands-agents).

Key features:
- Support for both stdio and HTTP MCP transports
- Selective tool loading via function filtering
- Connection lifecycle management via ExitStack
- Comprehensive error handling and logging
- Integration with strands-agents MCP client infrastructure
"""

import os
from typing import Any, Dict

from loguru import logger

from ..ptypes import ToolCreationResult
from .base_adapter import ToolAdapter


class MCPStdIOAdapter(ToolAdapter):
    """
    Adapter for loading tools from MCP servers via stdio transport.
    
    MCPStdIOAdapter connects to MCP servers that communicate via standard
    input/output streams. This is typically used for local tools, scripts,
    or command-line utilities that implement the MCP protocol.
    
    The adapter:
    - Manages subprocess lifecycle for MCP server processes
    - Handles environment variable configuration
    - Provides connection pooling and resource cleanup
    - Supports selective tool loading via function filtering
    - Integrates with strands-agents MCP client infrastructure
    
    stdio transport is particularly useful for:
    - Local development and testing
    - Sandboxed tool execution
    - Integration with existing command-line tools
    - Scenarios requiring process isolation
    
    Configuration format:
        {
            "id": "local_tools",
            "type": "mcp-stdio",
            "command": "python",
            "args": ["-m", "my_mcp_server"],
            "env": {"API_KEY": "secret"},
            "functions": ["tool1", "tool2"]  # Optional filtering
        }
        
    Example:
        Loading tools from a Python MCP server::
        
            config = {
                "id": "file_tools",
                "type": "mcp-stdio", 
                "command": "python",
                "args": ["-m", "file_server"],
                "env": {"WORK_DIR": "/tmp"},
                "functions": ["read_file", "write_file"]
            }
            
            result = adapter.create(config)
            if not result.error:
                print(f"Loaded {len(result.tools)} file tools")
    """

    def create(self, config: Dict[str, Any]) -> ToolCreationResult:
        """
        Create tools from an MCP server via stdio transport.
        
        Establishes a stdio connection to an MCP server process and loads
        the available tools. The method handles process management,
        environment configuration, and tool discovery while providing
        detailed error reporting.
        
        The creation process:
        1. Validates configuration parameters
        2. Sets up process environment variables
        3. Creates stdio transport parameters
        4. Establishes connection to MCP server
        5. Discovers available tools from the server
        6. Filters tools if specific functions were requested
        7. Registers cleanup handlers for proper resource management
        
        Args:
            config: MCP stdio configuration dictionary containing:
                   - id: Unique identifier for the server
                   - command: Command to execute for the MCP server
                   - args: Command line arguments (optional)
                   - env: Environment variables for the process (optional)
                   - functions: Specific functions to load (optional)
                   
        Returns:
            ToolCreationResult: Detailed result containing:
            - tools: Successfully loaded MCP tool objects
            - requested_functions: Function names that were requested
            - found_functions: Function names that were found on the server
            - missing_functions: Requested functions not found on the server
            - error: Error message if connection or loading failed
            
        Example:
            Successful tool loading::
            
                config = {
                    "id": "calc_server",
                    "command": "python",
                    "args": ["-m", "calculator_mcp"],
                    "functions": ["add", "subtract"]
                }
                
                result = adapter.create(config)
                # result.tools contains MCP tool objects
                # result.found_functions = ["add", "subtract"]
                # result.missing_functions = []
                
            Partial success with missing functions::
            
                config = {
                    "id": "calc_server", 
                    "command": "python",
                    "args": ["-m", "calculator_mcp"],
                    "functions": ["add", "nonexistent"]
                }
                
                result = adapter.create(config)
                # result.tools contains 1 tool object
                # result.found_functions = ["add"]
                # result.missing_functions = ["nonexistent"]
                
        Note:
            The method uses the ExitStack to ensure proper cleanup of the
            MCP server process when the adapter scope ends. Tools are loaded
            and configured but not executed - execution is handled by strands-agents.
        """
        server_id = config.get("id", "unknown-stdio-server")
        logger.debug(f"Starting MCP server '{server_id}' with command: {config.get('command')}")

        try:
            # Import MCP dependencies when needed (lazy loading)
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

        # Prepare process environment
        process_env = os.environ.copy()
        if 'env' in config:
            process_env.update(config['env'])

        # Create stdio transport parameters
        params = StdioServerParameters(
            command=config["command"], 
            args=config.get("args", []), 
            env=process_env
        )

        def create_stdio_client():
            return stdio_client(params)

        try:
            # Create MCP client with automatic resource management
            client = self.exit_stack.enter_context(MCPClient(create_stdio_client))
            all_tools = client.list_tools_sync()

            # Handle function filtering if specific functions were requested
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
                # No specific functions requested, return all available tools
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
    Adapter for loading tools from MCP servers via HTTP transport.
    
    MCPHTTPAdapter connects to MCP servers that communicate via HTTP and
    Server-Sent Events (SSE). This is typically used for web services,
    APIs, or remote tools that implement the MCP protocol over HTTP.
    
    The adapter:
    - Manages HTTP connection lifecycle and configuration
    - Handles authentication and connection parameters
    - Provides connection pooling and error recovery
    - Supports selective tool loading via function filtering
    - Integrates with strands-agents MCP client infrastructure
    
    HTTP transport is particularly useful for:
    - Remote service integration
    - Scalable tool deployment
    - Cloud-based tool services
    - Scenarios requiring network-based tool access
    
    Configuration format:
        {
            "id": "remote_tools",
            "type": "mcp-http",
            "url": "https://api.example.com/mcp",
            "functions": ["tool1", "tool2"]  # Optional filtering
        }
        
    Example:
        Loading tools from an HTTP MCP server::
        
            config = {
                "id": "web_tools",
                "type": "mcp-http",
                "url": "https://tools.example.com/mcp",
                "functions": ["web_search", "url_fetch"]
            }
            
            result = adapter.create(config)
            if not result.error:
                print(f"Loaded {len(result.tools)} web tools")
    """

    def create(self, config: Dict[str, Any]) -> ToolCreationResult:
        """
        Create tools from an MCP server via HTTP transport.
        
        Establishes an HTTP connection to an MCP server and loads the
        available tools. The method handles connection management,
        authentication, and tool discovery while providing detailed
        error reporting.
        
        The creation process:
        1. Validates configuration parameters
        2. Creates HTTP transport client
        3. Establishes connection to MCP server
        4. Discovers available tools from the server
        5. Filters tools if specific functions were requested
        6. Registers cleanup handlers for proper connection management
        
        Args:
            config: MCP HTTP configuration dictionary containing:
                   - id: Unique identifier for the server
                   - url: HTTP endpoint URL for the MCP server
                   - functions: Specific functions to load (optional)
                   
        Returns:
            ToolCreationResult: Detailed result containing:
            - tools: Successfully loaded MCP tool objects
            - requested_functions: Function names that were requested
            - found_functions: Function names that were found on the server
            - missing_functions: Requested functions not found on the server
            - error: Error message if connection or loading failed
            
        Example:
            Successful tool loading::
            
                config = {
                    "id": "api_tools",
                    "url": "https://tools.example.com/mcp",
                    "functions": ["search", "translate"]
                }
                
                result = adapter.create(config)
                # result.tools contains MCP tool objects
                # result.found_functions = ["search", "translate"]
                # result.missing_functions = []
                
            Connection failure::
            
                config = {
                    "id": "api_tools",
                    "url": "https://invalid.example.com/mcp"
                }
                
                result = adapter.create(config)
                # result.tools = []
                # result.error = "Connection failed: ..."
                
        Note:
            The method uses the ExitStack to ensure proper cleanup of HTTP
            connections when the adapter scope ends. Tools are loaded and
            configured but not executed - execution is handled by strands-agents.
        """
        server_id = config.get("id", "unknown-http-server")
        url = config.get("url")
        logger.debug(f"Connecting to MCP server '{server_id}' via HTTP at {url}")

        try:
            # Import MCP dependencies when needed (lazy loading)
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
            # Create MCP client with automatic resource management
            client = self.exit_stack.enter_context(MCPClient(create_http_client))
            all_tools = client.list_tools_sync()

            # Handle function filtering if specific functions were requested
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
                # No specific functions requested, return all available tools
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