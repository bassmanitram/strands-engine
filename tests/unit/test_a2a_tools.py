"""
Unit tests for A2A tool functionality in strands_agent_factory.
"""

from unittest.mock import Mock, patch

import pytest

from strands_agent_factory.tools.factory import ToolFactory


class TestA2ATools:
    """Test cases for A2A tool functionality."""

    @patch("strands_agent_factory.tools.a2a._A2A_AVAILABLE", True)
    @patch("strands_agent_factory.tools.a2a.A2AClientToolProvider")
    def test_create_a2a_tool_spec_success(self, mock_a2a_provider_class):
        """Test successful A2A tool spec creation."""
        # Mock the provider instance
        mock_provider = Mock()
        mock_tool1 = Mock()
        mock_tool1.name = "a2a_discover_agent"
        mock_tool2 = Mock()
        mock_tool2.name = "a2a_list_discovered_agents"
        mock_tool3 = Mock()
        mock_tool3.name = "a2a_send_message"
        mock_provider.tools = [mock_tool1, mock_tool2, mock_tool3]
        mock_a2a_provider_class.return_value = mock_provider

        config = {
            "id": "test_a2a_provider",
            "type": "a2a",
            "urls": ["http://localhost:8001/", "http://localhost:8002/"],
            "timeout": 300,
        }

        factory = ToolFactory([])
        result = factory.create_tool_from_config(config)

        assert "error" not in result
        assert "tools" in result
        assert len(result["tools"]) == 3
        assert result["client"] is None

        # Verify provider was created with correct parameters
        mock_a2a_provider_class.assert_called_once_with(
            provider_id="test_a2a_provider",
            known_agent_urls=["http://localhost:8001/", "http://localhost:8002/"],
            timeout=300,
            webhook_url=None,
            webhook_token=None,
        )

    @patch("strands_agent_factory.tools.a2a._A2A_AVAILABLE", True)
    @patch("strands_agent_factory.tools.a2a.A2AClientToolProvider")
    def test_create_a2a_tool_spec_with_webhook(self, mock_a2a_provider_class):
        """Test A2A tool spec creation with webhook configuration."""
        mock_provider = Mock()
        mock_provider.tools = []
        mock_a2a_provider_class.return_value = mock_provider

        config = {
            "id": "test_a2a_provider",
            "type": "a2a",
            "urls": ["http://localhost:8001/"],
            "timeout": 600,
            "webhook_url": "https://example.com/webhook",
            "webhook_token": "secret-token",
        }

        factory = ToolFactory([])
        result = factory.create_tool_from_config(config)

        assert "error" not in result

        # Verify provider was created with webhook config
        mock_a2a_provider_class.assert_called_once_with(
            provider_id="test_a2a_provider",
            known_agent_urls=["http://localhost:8001/"],
            timeout=600,
            webhook_url="https://example.com/webhook",
            webhook_token="secret-token",
        )

    @patch("strands_agent_factory.tools.a2a._A2A_AVAILABLE", False)
    def test_create_a2a_tool_spec_dependencies_unavailable(self):
        """Test A2A tool spec creation when dependencies are unavailable."""
        config = {
            "id": "test_a2a_provider",
            "type": "a2a",
            "urls": ["http://localhost:8001/"],
        }

        factory = ToolFactory([])
        result = factory.create_tool_from_config(config)

        assert "error" in result
        assert "A2A dependencies not installed" in result["error"]

    def test_create_a2a_tool_spec_missing_urls(self):
        """Test A2A tool spec creation with missing URLs."""
        config = {
            "id": "test_a2a_provider",
            "type": "a2a",
            # Missing urls field
        }

        factory = ToolFactory([])
        result = factory.create_tool_from_config(config)

        assert "error" in result
        assert "missing required 'urls' field" in result["error"]

    def test_create_a2a_tool_spec_empty_urls(self):
        """Test A2A tool spec creation with empty URLs list."""
        config = {"id": "test_a2a_provider", "type": "a2a", "urls": []}

        factory = ToolFactory([])
        result = factory.create_tool_from_config(config)

        assert "error" in result
        assert "missing required 'urls' field" in result["error"]

    def test_create_a2a_tool_spec_invalid_urls_type(self):
        """Test A2A tool spec creation with invalid URLs type."""
        config = {
            "id": "test_a2a_provider",
            "type": "a2a",
            "urls": "http://localhost:8001/",  # Should be a list
        }

        factory = ToolFactory([])
        result = factory.create_tool_from_config(config)

        assert "error" in result
        assert "missing required 'urls' field" in result["error"]

    @patch("strands_agent_factory.tools.a2a._A2A_AVAILABLE", True)
    def test_a2a_client_provider_init(self):
        """Test A2AClientToolProvider initialization."""
        from strands_agent_factory.tools.a2a import A2AClientToolProvider

        with patch(
            "strands_tools.a2a_client.A2AClientToolProvider.__init__", return_value=None
        ):
            provider = A2AClientToolProvider(
                provider_id="test_provider",
                known_agent_urls=["http://localhost:8001/"],
                timeout=300,
            )

        assert provider.provider_id == "test_provider"

    @patch("strands_agent_factory.tools.a2a._A2A_AVAILABLE", True)
    @patch("strands_agent_factory.tools.a2a.A2AClientToolProvider")
    def test_a2a_tool_spec_integration(self, mock_a2a_provider_class):
        """Test A2A tool spec creation through factory integration."""

        # Create mock tools with proper name and __name__ attributes
        def create_mock_tool(name):
            tool = Mock()
            tool.name = name
            tool.__name__ = name
            return tool

        mock_tool1 = create_mock_tool("a2a_discover_agent")
        mock_tool2 = create_mock_tool("a2a_list_discovered_agents")
        mock_tool3 = create_mock_tool("a2a_send_message")

        mock_provider = Mock()
        mock_provider.tools = [mock_tool1, mock_tool2, mock_tool3]
        mock_a2a_provider_class.return_value = mock_provider

        config = {
            "id": "company_agents",
            "type": "a2a",
            "urls": ["http://employee-agent:8001/", "http://payroll-agent:8002/"],
        }

        factory = ToolFactory([])
        factory._tool_configs = [config]

        results = factory.create_tool_specs()

        assert len(results) == 1
        assert results[0]["id"] == "company_agents"
        assert results[0]["type"] == "a2a"
        assert len(results[0]["tools"]) == 3
        assert results[0]["tool_names"] == [
            "a2a_discover_agent",
            "a2a_list_discovered_agents",
            "a2a_send_message",
        ]
        assert results[0].get("client") is None

    @patch("strands_agent_factory.tools.a2a._A2A_AVAILABLE", True)
    @patch("strands_agent_factory.tools.a2a.A2AClientToolProvider")
    def test_a2a_tool_spec_with_exception(self, mock_a2a_provider_class):
        """Test A2A tool spec creation with unexpected exception."""
        mock_a2a_provider_class.side_effect = Exception("Unexpected error")

        config = {
            "id": "test_a2a_provider",
            "type": "a2a",
            "urls": ["http://localhost:8001/"],
        }

        factory = ToolFactory([])
        result = factory.create_tool_from_config(config)

        assert "error" in result
        assert "Unexpected error" in result["error"]
