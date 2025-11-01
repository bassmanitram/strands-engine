"""
A2A (Agent-to-Agent) tool handling.

Provides A2AClientToolProvider subclass and A2A tool specification creation.
"""

from typing import List, Optional

from loguru import logger

from ..core.types import ToolConfig
from .types import (
    CONFIG_FIELD_ID,
    CONFIG_FIELD_TIMEOUT,
    CONFIG_FIELD_TYPE,
    CONFIG_FIELD_URLS,
    CONFIG_FIELD_WEBHOOK_TOKEN,
    CONFIG_FIELD_WEBHOOK_URL,
    DEFAULT_A2A_PROVIDER_ID,
    DEFAULT_TOOL_ID,
    ERROR_MSG_A2A_CONFIG_MISSING_URLS,
    ERROR_MSG_A2A_DEPS_NOT_INSTALLED,
    ERROR_MSG_UNEXPECTED_ERROR,
    ToolSpecData,
)
from .utils import get_config_value

# A2A imports with availability check
try:
    from strands_tools.a2a_client import (
        A2AClientToolProvider as A2AClientToolProviderBase,
    )

    _A2A_AVAILABLE = True
except ImportError:
    _A2A_AVAILABLE = False
    A2AClientToolProviderBase = object


class A2AClientToolProvider(A2AClientToolProviderBase):
    """Enhanced A2AClientToolProvider with provider identification."""

    def __init__(
        self,
        provider_id: str,
        known_agent_urls: list[str] | None = None,
        timeout: int = 300,
        webhook_url: str | None = None,
        webhook_token: str | None = None,
    ):
        """
        Initialize A2A client tool provider.

        Args:
            provider_id: Unique identifier for this provider instance
            known_agent_urls: List of A2A agent URLs to connect to
            timeout: Timeout for HTTP operations in seconds
            webhook_url: Optional webhook URL for push notifications
            webhook_token: Optional authentication token for webhooks
        """
        logger.trace(
            "A2AClientToolProvider.__init__ called with provider_id='{}', urls={}",
            provider_id,
            known_agent_urls,
        )

        if not _A2A_AVAILABLE:
            logger.error(ERROR_MSG_A2A_DEPS_NOT_INSTALLED)
            raise ImportError(ERROR_MSG_A2A_DEPS_NOT_INSTALLED)

        self.provider_id = provider_id

        super().__init__(
            known_agent_urls=known_agent_urls,
            timeout=timeout,
            webhook_url=webhook_url,
            webhook_token=webhook_token,
        )

        logger.trace(
            "A2AClientToolProvider.__init__ completed for provider_id='{}'", provider_id
        )


def create_a2a_tool_spec(config: ToolConfig) -> ToolSpecData:
    """Create A2A tool specification from configuration."""
    provider_id = get_config_value(config, CONFIG_FIELD_ID, DEFAULT_A2A_PROVIDER_ID)

    logger.trace("create_a2a_tool_spec called for provider_id='{}'", provider_id)

    try:
        # Check A2A dependencies
        if not _A2A_AVAILABLE:
            logger.warning(ERROR_MSG_A2A_DEPS_NOT_INSTALLED)
            return ToolSpecData(error=ERROR_MSG_A2A_DEPS_NOT_INSTALLED)

        # Validate required fields
        urls = get_config_value(config, CONFIG_FIELD_URLS)
        if not urls or not isinstance(urls, list):
            logger.error("A2A tool '{}' missing required 'urls' field", provider_id)
            return ToolSpecData(error=ERROR_MSG_A2A_CONFIG_MISSING_URLS)

        # Extract optional configuration
        timeout = get_config_value(config, CONFIG_FIELD_TIMEOUT, 300)
        webhook_url = get_config_value(config, CONFIG_FIELD_WEBHOOK_URL)
        webhook_token = get_config_value(config, CONFIG_FIELD_WEBHOOK_TOKEN)

        logger.debug(
            "A2A tool spec: id={}, urls={}, timeout={}", provider_id, urls, timeout
        )

        # Create A2A provider
        provider = A2AClientToolProvider(
            provider_id=provider_id,
            known_agent_urls=urls,
            timeout=timeout,
            webhook_url=webhook_url,
            webhook_token=webhook_token,
        )

        # Extract all tools from provider (always 3 tools)
        tools = provider.tools

        logger.info(
            "Successfully created A2A tool provider '{}' with {} agents, {} tools",
            provider_id,
            len(urls),
            len(tools),
        )
        return ToolSpecData(tools=tools, client=None)

    except Exception as e:
        tool_type = get_config_value(config, CONFIG_FIELD_TYPE, DEFAULT_TOOL_ID)
        formatted_msg = ERROR_MSG_UNEXPECTED_ERROR.format(tool_type, provider_id, e)
        logger.warning(formatted_msg)
        return ToolSpecData(error=formatted_msg)
