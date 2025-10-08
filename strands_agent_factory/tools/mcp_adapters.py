"""
Model Context Protocol (MCP) tool adapters for strands_agent_factory.

This module provides adapters for creating MCP tool specifications that can later
be used to connect to MCP servers and load tools for strands-agents. MCP is a protocol
that enables AI agents to securely connect to external systems and access their
capabilities through standardized tool interfaces.

The MCP adapters support both transport mechanisms defined by the MCP specification:
- stdio: Communication via standard input/output with a subprocess
- HTTP: Communication via HTTP/SSE with a web service

Both adapters create tool specifications that encapsulate connection parameters
and configuration while deferring actual connection establishment until tool
execution time. This provides comprehensive error handling and logging while
maintaining the clean separation between tool loading (engine) and tool execution
(strands-agents).

Key features:
- Support for both stdio and HTTP MCP transports
- Selective tool loading via function filtering
- Deferred connection establishment for better resource management
- Comprehensive error handling and logging
- Integration with strands-agents MCP client infrastructure
"""

import os
from typing import Any, Dict, List, Optional, Callable

from loguru import logger

from ..ptypes import MCPToolSpec
from .base_adapter import ToolAdapter, ToolSpecCreationResult

# Import strands MCPClient at module level for subclassing
try:
    from strands.tools.mcp import MCPClient as StrandsMCPClient
    _STRANDS_MCP_AVAILABLE = True
except ImportError:
    _STRANDS_MCP_AVAILABLE = False
    StrandsMCPClient = object  # Fallback for type hints


class MCPClient(StrandsMCPClient):
    """
    Enhanced strands MCPClient with built-in tool filtering.
    
    This class extends the strands MCPClient to provide transparent tool filtering
    based on requested function names. It inherits all strands MCPClient functionality
    while adding filtering capabilities to the list_tools_sync method.
    
    The client handles:
    - All standard strands MCPClient functionality via inheritance
    - Transparent tool filtering in list_tools_sync
    - Server identification for logging and debugging
    - Proper context manager lifecycle inherited from parent
    """
    
    def __init__(self, server_id: str, transport_callable: Callable, requested_functions: Optional[List[str]] = None):
        """
        Initialize enhanced MCP client with filtering capabilities.
        
        Args:
            server_id: Unique identifier for this MCP server
            transport_callable: Callable that returns transport context manager
            requested_functions: Optional list of specific tool names to filter
        """
        if not _STRANDS_MCP_AVAILABLE:
            raise ImportError("MCP dependencies not installed - cannot create MCPClient")
            
        self.server_id = server_id
        self.requested_functions = requested_functions or []
        
        # Initialize the parent strands MCPClient
        super().__init__(transport_callable)
        
    def __enter__(self):
        """Enhanced context manager with logging."""
        result = super().__enter__()
        logger.debug(f"Successfully connected to MCP server: {self.server_id}")
        return result
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Enhanced context manager cleanup with logging."""
        try:
            result = super().__exit__(exc_type, exc_val, exc_tb)
            logger.debug(f"Disconnected from MCP server: {self.server_id}")
            return result
        except Exception as e:
            logger.warning(f"Error during MCP server cleanup for {self.server_id}: {e}")
            raise
    
    def list_tools_sync(self, pagination_token: Optional[str] = None):
        """
        List tools from MCP server with automatic filtering.
        
        This method extends the parent list_tools_sync() by applying
        filtering based on requested_functions if specified. Tools are filtered
        by matching tool names against the requested function list.
        
        Args:
            pagination_token: Optional pagination token for large tool lists
            
        Returns:
            Filtered list of MCPAgentTool objects matching requested functions
        """
        try:
            # Get all available tools from the parent class
            all_tools = super().list_tools_sync(pagination_token)
            
            # Apply filtering if specific functions were requested
            if self.requested_functions:
                filtered_tools = []
                found_functions = []

                for requested_func in self.requested_functions:
                    for tool in all_tools:
                        # Use tool_name property to match against requested functions
                        if tool.tool_name == requested_func:
                            filtered_tools.append(tool)
                            found_functions.append(requested_func)
                            break
                    else:
                        # Log warning if requested function not found
                        logger.warning(f"MCP server '{self.server_id}' does not provide requested function '{requested_func}'")

                logger.debug(f"Filtered {len(filtered_tools)} tools from {len(all_tools)} available on {self.server_id}")
                return filtered_tools
            else:
                # No filtering requested, return all tools
                logger.debug(f"Returning all {len(all_tools)} tools from {self.server_id}")
                return all_tools
                
        except Exception as e:
            logger.error(f"Failed to list tools from MCP server {self.server_id}: {e}")
            raise


class MCPStdIOAdapter(ToolAdapter):
    """
    Adapter for creating MCP tool specifications for stdio transport servers.
    
    MCPStdIOAdapter creates tool specifications for MCP clients configured for
    stdio transport. These specifications can later be used to establish connections
    to MCP servers via standard input/output streams, typically used for local
    tools, scripts, or command-line utilities.
    
    Configuration format:
        {
            "id": "local_tools",
            "type": "mcp-stdio",
            "command": "python",
            "args": ["-m", "my_mcp_server"],
            "env": {"API_KEY": "secret"},
            "functions": ["tool1", "tool2"]  # Optional filtering
        }
    """

    def create(self, config: Dict[str, Any]) -> ToolSpecCreationResult:
        """
        Create MCP tool specification for stdio transport server.
        
        Creates an MCPToolSpec containing an MCPClient configured for stdio transport.
        The client stores connection parameters but doesn't establish the connection
        until it's used as a context manager during tool execution.
        
        Args:
            config: MCP stdio configuration dictionary
                   
        Returns:
            ToolSpecCreationResult with tool_spec containing MCPToolSpec
        """
        server_id = config.get("id", "unknown-stdio-server")
        logger.debug(f"Creating MCP stdio tool spec for server: {server_id}")

        try:
            # Import MCP dependencies to validate availability
            from mcp import StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError as e:
            logger.error(f"MCP dependencies not available: {e}")
            return ToolSpecCreationResult(
                tool_spec=None,
                requested_functions=config.get("functions", []),
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

        def create_stdio_transport():
            return stdio_client(params)

        # Create MCPClient subclass (connection deferred until context entry)
        mcp_client = MCPClient(
            server_id=server_id,
            transport_callable=create_stdio_transport,
            requested_functions=config.get("functions", [])
        )

        # Create MCPToolSpec
        tool_spec: MCPToolSpec = {
            "type": "mcp",
            "client": mcp_client
        }

        logger.info(f"Created MCP stdio tool spec for server: {server_id}")
        return ToolSpecCreationResult(
            tool_spec=tool_spec,
            requested_functions=config.get("functions", []),
            error=None
        )


class MCPHTTPAdapter(ToolAdapter):
    """
    Adapter for creating MCP tool specifications for HTTP transport servers.
    
    MCPHTTPAdapter creates tool specifications for MCP clients configured for
    HTTP transport. These specifications can later be used to establish connections
    to MCP servers via HTTP and Server-Sent Events, typically used for web services,
    APIs, or remote tools.
    
    Configuration format:
        {
            "id": "remote_tools",
            "type": "mcp-http",
            "url": "https://api.example.com/mcp",
            "functions": ["tool1", "tool2"]  # Optional filtering
        }
    """

    def create(self, config: Dict[str, Any]) -> ToolSpecCreationResult:
        """
        Create MCP tool specification for HTTP transport server.
        
        Creates an MCPToolSpec containing an MCPClient configured for HTTP transport.
        The client stores connection parameters but doesn't establish the connection
        until it's used as a context manager during tool execution.
        
        Args:
            config: MCP HTTP configuration dictionary
                   
        Returns:
            ToolSpecCreationResult with tool_spec containing MCPToolSpec
        """
        server_id = config.get("id", "unknown-http-server")
        url = config.get("url")
        logger.debug(f"Creating MCP HTTP tool spec for server: {server_id} at {url}")

        try:
            # Import MCP dependencies to validate availability
            from mcp.client.streamable_http import streamablehttp_client
        except ImportError as e:
            logger.error(f"MCP dependencies not available: {e}")
            return ToolSpecCreationResult(
                tool_spec=None,
                requested_functions=config.get("functions", []),
                error="MCP dependencies not installed"
            )

        def create_http_transport():
            return streamablehttp_client(url)

        # Create MCPClient subclass (connection deferred until context entry)
        mcp_client = MCPClient(
            server_id=server_id,
            transport_callable=create_http_transport,
            requested_functions=config.get("functions", [])
        )

        # Create MCPToolSpec
        tool_spec: MCPToolSpec = {
            "type": "mcp",
            "client": mcp_client
        }

        logger.info(f"Created MCP HTTP tool spec for server: {server_id}")
        return ToolSpecCreationResult(
            tool_spec=tool_spec,
            requested_functions=config.get("functions", []),
            error=None
        )