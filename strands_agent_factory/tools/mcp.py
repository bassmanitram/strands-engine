"""
MCP (Model Context Protocol) tool handling.

Provides MCPClient subclass with filtering and MCP tool specification creation.
"""

import os
from typing import Any, Callable, List, Optional

from loguru import logger

from ..core.types import ToolConfig
from .types import (
    CONFIG_FIELD_ARGS,
    CONFIG_FIELD_COMMAND,
    CONFIG_FIELD_ENV,
    CONFIG_FIELD_FUNCTIONS,
    CONFIG_FIELD_ID,
    CONFIG_FIELD_TYPE,
    CONFIG_FIELD_URL,
    DEFAULT_MCP_SERVER_ID,
    DEFAULT_TOOL_ID,
    ERROR_MSG_MCP_DEPS_NOT_INSTALLED,
    ERROR_MSG_MCP_TRANSPORT_DEPS,
    ERROR_MSG_MCP_TRANSPORT_MISSING,
    ERROR_MSG_UNEXPECTED_ERROR,
    ToolSpecData,
)
from .utils import get_config_value

# MCP imports with availability check
try:
    from strands.tools.mcp import MCPClient as StrandsMCPClient

    _STRANDS_MCP_AVAILABLE = True
except ImportError:
    _STRANDS_MCP_AVAILABLE = False
    StrandsMCPClient = object


class MCPClient(StrandsMCPClient):
    """Enhanced strands MCPClient with filtering and server identification."""

    def __init__(
        self,
        server_id: str,
        transport_callable: Callable,
        requested_functions: Optional[List[str]] = None,
    ):
        logger.trace(
            "MCPClient.__init__ called with server_id='{}', requested_functions={}",
            server_id,
            requested_functions,
        )

        if not _STRANDS_MCP_AVAILABLE:
            logger.error(ERROR_MSG_MCP_DEPS_NOT_INSTALLED)
            raise ImportError(ERROR_MSG_MCP_DEPS_NOT_INSTALLED)

        self.server_id = server_id
        self.requested_functions = requested_functions or []
        super().__init__(transport_callable)

        logger.trace("MCPClient.__init__ completed for server_id='{}'", server_id)

    def list_tools_sync(self, pagination_token: Optional[str] = None):
        """List tools with optional filtering by requested_functions."""
        logger.trace(
            "list_tools_sync called with pagination_token={}, requested_functions={}",
            pagination_token,
            self.requested_functions,
        )

        all_tools = super().list_tools_sync(pagination_token)

        if not self.requested_functions:
            if logger.level("DEBUG").no >= logger._core.min_level:
                logger.debug(
                    "list_tools_sync returning {} unfiltered tools",
                    len(all_tools) if all_tools else 0,
                )
            return all_tools

        # Filter tools by requested function names
        filtered_tools = []
        for requested_func in self.requested_functions:
            for tool in all_tools:
                if tool.tool_name == requested_func:
                    filtered_tools.append(tool)
                    break
            else:
                logger.warning(
                    "Function '{}' not found on MCP server '{}'",
                    requested_func,
                    self.server_id,
                )

        logger.debug("list_tools_sync returning {} filtered tools", len(filtered_tools))
        return filtered_tools


def create_mcp_tool_spec(config: ToolConfig) -> ToolSpecData:
    """Create MCP tool specification from configuration."""
    server_id = get_config_value(config, CONFIG_FIELD_ID, DEFAULT_MCP_SERVER_ID)
    functions = get_config_value(config, CONFIG_FIELD_FUNCTIONS, [])

    logger.trace(
        "create_mcp_tool_spec called for server_id='{}', functions={}",
        server_id,
        functions,
    )

    try:
        # Check MCP dependencies
        if not _STRANDS_MCP_AVAILABLE:
            logger.warning(ERROR_MSG_MCP_DEPS_NOT_INSTALLED)
            return ToolSpecData(error=ERROR_MSG_MCP_DEPS_NOT_INSTALLED)

        # Create transport callable
        transport_callable = _create_transport_callable(config)
        if transport_callable is None:
            logger.error(ERROR_MSG_MCP_TRANSPORT_MISSING)
            return ToolSpecData(error=ERROR_MSG_MCP_TRANSPORT_MISSING)

        # Create client and return tool spec data
        mcp_client = MCPClient(server_id, transport_callable, functions)

        logger.info("Created MCP tool spec for server: {}", server_id)
        return ToolSpecData(client=mcp_client, tools=None)

    except Exception as e:
        tool_type = get_config_value(config, CONFIG_FIELD_TYPE, DEFAULT_TOOL_ID)
        formatted_msg = ERROR_MSG_UNEXPECTED_ERROR.format(tool_type, server_id, e)
        logger.warning(formatted_msg)
        return ToolSpecData(error=formatted_msg)


def _create_transport_callable(config: ToolConfig) -> Optional[Callable]:
    """Create appropriate transport callable based on config."""
    try:
        if CONFIG_FIELD_COMMAND in config:
            return _create_stdio_transport(config)
        elif CONFIG_FIELD_URL in config:
            return _create_http_transport(config)
        else:
            return None
    except ImportError as e:
        logger.error(ERROR_MSG_MCP_TRANSPORT_DEPS, e)
        raise


def _create_stdio_transport(config: ToolConfig) -> Callable:
    """Create stdio transport callable."""
    command = get_config_value(config, CONFIG_FIELD_COMMAND)
    logger.trace("_create_stdio_transport called with command='{}'", command)

    from mcp import StdioServerParameters
    from mcp.client.stdio import stdio_client

    # Prepare environment
    env = os.environ.copy()
    config_env = get_config_value(config, CONFIG_FIELD_ENV)
    if config_env:
        env.update(config_env)
        if logger.level("DEBUG").no >= logger._core.min_level:
            logger.debug("Updated environment with {} variables", len(config_env))

    params = StdioServerParameters(
        command=command, args=get_config_value(config, CONFIG_FIELD_ARGS, []), env=env
    )

    transport_callable = lambda: stdio_client(params)
    logger.trace("_create_stdio_transport completed")
    return transport_callable


def _create_http_transport(config: ToolConfig) -> Callable:
    """Create HTTP transport callable."""
    url = get_config_value(config, CONFIG_FIELD_URL)
    logger.trace("_create_http_transport called with url='{}'", url)

    from mcp.client.streamable_http import streamablehttp_client

    transport_callable = lambda: streamablehttp_client(url)
    logger.trace("_create_http_transport completed")
    return transport_callable
