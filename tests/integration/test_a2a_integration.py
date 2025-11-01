"""
Integration tests for A2A tool functionality with AgentFactory.

Tests the complete workflow of:
- Loading A2A tool configurations
- Creating agents with A2A tools
- Tool integration with the factory system
- Error handling and edge cases
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from strands_agent_factory.core.config import AgentFactoryConfig
from strands_agent_factory.core.exceptions import InitializationError
from strands_agent_factory.core.factory import AgentFactory


class TestA2AToolIntegration:
    """Integration tests for A2A tool functionality with factory."""

    @pytest.mark.integration
    @patch("strands_agent_factory.tools.a2a._A2A_AVAILABLE", True)
    @patch("strands_agent_factory.tools.a2a.A2AClientToolProvider")
    def test_a2a_tool_loading_with_factory(self, mock_a2a_provider_class, temp_dir):
        """Test loading A2A tools through factory configuration."""
        # Create mock A2A tools
        mock_tool1 = Mock()
        mock_tool1.name = "a2a_discover_agent"
        mock_tool1.__name__ = "a2a_discover_agent"
        mock_tool2 = Mock()
        mock_tool2.name = "a2a_list_discovered_agents"
        mock_tool2.__name__ = "a2a_list_discovered_agents"
        mock_tool3 = Mock()
        mock_tool3.name = "a2a_send_message"
        mock_tool3.__name__ = "a2a_send_message"

        mock_provider = Mock()
        mock_provider.tools = [mock_tool1, mock_tool2, mock_tool3]
        mock_a2a_provider_class.return_value = mock_provider

        # Create A2A tool configuration
        a2a_config = {
            "id": "test_company_agents",
            "type": "a2a",
            "urls": ["http://localhost:8001/", "http://localhost:8002/"],
            "timeout": 300,
        }

        config_file = temp_dir / "a2a_tools.json"
        with open(config_file, "w") as f:
            json.dump(a2a_config, f)

        # Create factory config with A2A tools
        config = AgentFactoryConfig(
            model="anthropic:claude-3-5-sonnet", tool_config_paths=[str(config_file)]
        )

        factory = AgentFactory(config)

        # Verify tools are not loaded until initialization
        assert len(factory._loaded_tool_specs) == 0

        # Initialize
        with patch(
            "strands_agent_factory.core.factory.load_framework_adapter"
        ) as mock_load:
            mock_adapter = Mock()
            mock_adapter.framework_name = "anthropic"
            mock_load.return_value = mock_adapter

            import asyncio

            asyncio.run(factory.initialize())

        # Verify tools were loaded
        assert len(factory._loaded_tool_specs) >= 1
        # Find the A2A spec
        a2a_spec = next(
            (
                spec
                for spec in factory._loaded_tool_specs
                if spec.get("id") == "test_company_agents"
            ),
            None,
        )
        assert a2a_spec is not None
        assert a2a_spec["type"] == "a2a"
        assert len(a2a_spec["tools"]) == 3

    @pytest.mark.integration
    @patch("strands_agent_factory.tools.a2a._A2A_AVAILABLE", True)
    @patch("strands_agent_factory.tools.a2a.A2AClientToolProvider")
    def test_a2a_tool_with_webhook_configuration(
        self, mock_a2a_provider_class, temp_dir
    ):
        """Test A2A tool loading with webhook configuration."""
        mock_provider = Mock()
        mock_provider.tools = []
        mock_a2a_provider_class.return_value = mock_provider

        # Create A2A tool config with webhook
        a2a_config = {
            "id": "secure_agents",
            "type": "a2a",
            "urls": ["https://secure-agent.company.com/"],
            "timeout": 600,
            "webhook_url": "https://my-app.com/webhook",
            "webhook_token": "secret-webhook-token",
        }

        config_file = temp_dir / "secure_a2a.json"
        with open(config_file, "w") as f:
            json.dump(a2a_config, f)

        config = AgentFactoryConfig(
            model="gpt-4o", tool_config_paths=[str(config_file)]
        )

        factory = AgentFactory(config)

        # Initialize factory
        with patch(
            "strands_agent_factory.core.factory.load_framework_adapter"
        ) as mock_load:
            mock_adapter = Mock()
            mock_adapter.framework_name = "openai"
            mock_load.return_value = mock_adapter

            import asyncio

            asyncio.run(factory.initialize())

        # Verify provider was created with webhook config (check if it was called at all)
        assert mock_a2a_provider_class.called
        # Check the call arguments
        call_args = mock_a2a_provider_class.call_args
        assert call_args is not None
        assert call_args[1]["provider_id"] == "secure_agents"
        assert call_args[1]["known_agent_urls"] == ["https://secure-agent.company.com/"]
        assert call_args[1]["timeout"] == 600
        assert call_args[1]["webhook_url"] == "https://my-app.com/webhook"
        assert call_args[1]["webhook_token"] == "secret-webhook-token"

    @pytest.mark.integration
    @patch("strands_agent_factory.tools.a2a._A2A_AVAILABLE", False)
    def test_a2a_tool_loading_without_dependencies(self, temp_dir):
        """Test graceful handling when A2A dependencies are not installed."""
        # Create A2A tool configuration
        a2a_config = {
            "id": "test_agents",
            "type": "a2a",
            "urls": ["http://localhost:8001/"],
        }

        config_file = temp_dir / "a2a_tools.json"
        with open(config_file, "w") as f:
            json.dump(a2a_config, f)

        config = AgentFactoryConfig(
            model="gpt-4o", tool_config_paths=[str(config_file)]
        )

        factory = AgentFactory(config)

        # Initialize - should handle missing dependencies gracefully
        with patch(
            "strands_agent_factory.core.factory.load_framework_adapter"
        ) as mock_load:
            mock_adapter = Mock()
            mock_adapter.framework_name = "openai"
            mock_load.return_value = mock_adapter

            import asyncio

            asyncio.run(factory.initialize())

        # Factory should initialize successfully but A2A tools should be marked as failed
        assert factory._initialized is True
        # Tool specs should include error information
        assert len(factory._loaded_tool_specs) > 0
        # The failed tool should have an error field
        a2a_spec = next(
            (
                spec
                for spec in factory._loaded_tool_specs
                if spec.get("id") == "test_agents"
            ),
            None,
        )
        if a2a_spec:
            assert "error" in a2a_spec

    @pytest.mark.integration
    @patch("strands_agent_factory.tools.a2a._A2A_AVAILABLE", True)
    @patch("strands_agent_factory.tools.a2a.A2AClientToolProvider")
    def test_multiple_a2a_configurations(self, mock_a2a_provider_class, temp_dir):
        """Test loading multiple A2A tool configurations."""
        # Create first provider mock
        mock_provider1 = Mock()
        mock_tool1a = Mock()
        mock_tool1a.name = "a2a_discover_agent"
        mock_tool1a.__name__ = "a2a_discover_agent"
        mock_provider1.tools = [mock_tool1a]

        # Create second provider mock
        mock_provider2 = Mock()
        mock_tool2a = Mock()
        mock_tool2a.name = "a2a_discover_agent"
        mock_tool2a.__name__ = "a2a_discover_agent"
        mock_provider2.tools = [mock_tool2a]

        # Mock will return different providers based on call order
        mock_a2a_provider_class.side_effect = [mock_provider1, mock_provider2]

        # Create two A2A configurations
        config1 = {
            "id": "internal_agents",
            "type": "a2a",
            "urls": ["http://internal-agent1:8001/"],
        }

        config2 = {
            "id": "external_agents",
            "type": "a2a",
            "urls": ["http://external-agent1:9001/"],
        }

        config_file1 = temp_dir / "internal_a2a.json"
        with open(config_file1, "w") as f:
            json.dump(config1, f)

        config_file2 = temp_dir / "external_a2a.json"
        with open(config_file2, "w") as f:
            json.dump(config2, f)

        config = AgentFactoryConfig(
            model="gpt-4o", tool_config_paths=[str(config_file1), str(config_file2)]
        )

        factory = AgentFactory(config)

        # Initialize
        with patch(
            "strands_agent_factory.core.factory.load_framework_adapter"
        ) as mock_load:
            mock_adapter = Mock()
            mock_adapter.framework_name = "openai"
            mock_load.return_value = mock_adapter

            import asyncio

            asyncio.run(factory.initialize())

        # Verify both tool sets were loaded
        assert len(factory._loaded_tool_specs) >= 2
        tool_ids = [spec["id"] for spec in factory._loaded_tool_specs]
        assert "internal_agents" in tool_ids
        assert "external_agents" in tool_ids

    @pytest.mark.integration
    @patch("strands_agent_factory.tools.a2a._A2A_AVAILABLE", True)
    @patch("strands_agent_factory.tools.a2a.A2AClientToolProvider")
    def test_a2a_tool_with_invalid_url_format(self, mock_a2a_provider_class, temp_dir):
        """Test A2A tool configuration with invalid URL format."""
        # Create invalid A2A configuration
        a2a_config = {
            "id": "invalid_agents",
            "type": "a2a",
            "urls": "http://localhost:8001/",  # Should be a list, not a string
        }

        config_file = temp_dir / "invalid_a2a.json"
        with open(config_file, "w") as f:
            json.dump(a2a_config, f)

        config = AgentFactoryConfig(
            model="gpt-4o", tool_config_paths=[str(config_file)]
        )

        factory = AgentFactory(config)

        # Initialize - should handle invalid config gracefully
        with patch(
            "strands_agent_factory.core.factory.load_framework_adapter"
        ) as mock_load:
            mock_adapter = Mock()
            mock_adapter.framework_name = "openai"
            mock_load.return_value = mock_adapter

            import asyncio

            asyncio.run(factory.initialize())

        # Factory should initialize but tool should be marked as failed
        assert factory._initialized is True
        # The invalid tool spec should have an error
        invalid_spec = next(
            (
                spec
                for spec in factory._loaded_tool_specs
                if spec.get("id") == "invalid_agents"
            ),
            None,
        )
        if invalid_spec:
            assert "error" in invalid_spec

    @pytest.mark.integration
    @patch("strands_agent_factory.tools.a2a._A2A_AVAILABLE", True)
    @patch("strands_agent_factory.tools.a2a.A2AClientToolProvider")
    def test_a2a_tools_with_mixed_tool_types(self, mock_a2a_provider_class, temp_dir):
        """Test loading A2A tools alongside other tool types."""
        # Mock A2A provider
        mock_a2a_tool = Mock()
        mock_a2a_tool.name = "a2a_discover_agent"
        mock_a2a_tool.__name__ = "a2a_discover_agent"
        mock_provider = Mock()
        mock_provider.tools = [mock_a2a_tool]
        mock_a2a_provider_class.return_value = mock_provider

        # Create A2A config
        a2a_config = {
            "id": "company_agents",
            "type": "a2a",
            "urls": ["http://localhost:8001/"],
        }

        # Create Python tools config
        python_config = {
            "id": "math_tools",
            "type": "python",
            "module_path": "math",
            "functions": ["sqrt", "pow"],
        }

        a2a_file = temp_dir / "a2a_tools.json"
        with open(a2a_file, "w") as f:
            json.dump(a2a_config, f)

        python_file = temp_dir / "python_tools.json"
        with open(python_file, "w") as f:
            json.dump(python_config, f)

        config = AgentFactoryConfig(
            model="gpt-4o", tool_config_paths=[str(a2a_file), str(python_file)]
        )

        factory = AgentFactory(config)

        # Initialize
        with patch(
            "strands_agent_factory.core.factory.load_framework_adapter"
        ) as mock_load:
            mock_adapter = Mock()
            mock_adapter.framework_name = "openai"
            mock_load.return_value = mock_adapter

            import asyncio

            asyncio.run(factory.initialize())

        # Verify both tool types were loaded
        assert len(factory._loaded_tool_specs) >= 2
        tool_types = [spec.get("type") for spec in factory._loaded_tool_specs]
        assert "a2a" in tool_types
        assert "python" in tool_types

    @pytest.mark.integration
    @patch("strands_agent_factory.tools.a2a._A2A_AVAILABLE", True)
    @patch("strands_agent_factory.tools.a2a.A2AClientToolProvider")
    @patch("strands_agent_factory.core.factory.load_framework_adapter")
    async def test_a2a_tool_provider_lifecycle(
        self, mock_load_adapter, mock_a2a_provider_class, temp_dir
    ):
        """Test A2A tool provider lifecycle management."""
        # Mock A2A provider with cleanup method
        mock_provider = Mock()
        mock_provider.tools = []
        mock_provider.close = AsyncMock()
        mock_a2a_provider_class.return_value = mock_provider

        # Mock adapter
        mock_adapter = Mock()
        mock_adapter.framework_name = "openai"
        mock_load_adapter.return_value = mock_adapter

        # Create A2A config
        a2a_config = {
            "id": "test_agents",
            "type": "a2a",
            "urls": ["http://localhost:8001/"],
        }

        config_file = temp_dir / "a2a_tools.json"
        with open(config_file, "w") as f:
            json.dump(a2a_config, f)

        config = AgentFactoryConfig(
            model="gpt-4o", tool_config_paths=[str(config_file)]
        )

        factory = AgentFactory(config)
        await factory.initialize()

        # Verify provider was created
        assert mock_a2a_provider_class.called

        # Factory cleanup should not directly call provider cleanup
        # (A2A providers don't require explicit cleanup like MCP servers)
        factory._exit_stack.close()

    @pytest.mark.integration
    @patch("strands_agent_factory.tools.a2a._A2A_AVAILABLE", True)
    @patch("strands_agent_factory.tools.a2a.A2AClientToolProvider")
    def test_a2a_tool_error_propagation(self, mock_a2a_provider_class, temp_dir):
        """Test error propagation from A2A tool creation."""
        # Mock provider creation to raise an exception
        mock_a2a_provider_class.side_effect = ValueError("Invalid agent URL format")

        # Create A2A config
        a2a_config = {
            "id": "failing_agents",
            "type": "a2a",
            "urls": ["http://localhost:8001/"],
        }

        config_file = temp_dir / "a2a_tools.json"
        with open(config_file, "w") as f:
            json.dump(a2a_config, f)

        config = AgentFactoryConfig(
            model="gpt-4o", tool_config_paths=[str(config_file)]
        )

        factory = AgentFactory(config)

        # Initialize - should handle error gracefully
        with patch(
            "strands_agent_factory.core.factory.load_framework_adapter"
        ) as mock_load:
            mock_adapter = Mock()
            mock_adapter.framework_name = "openai"
            mock_load.return_value = mock_adapter

            import asyncio

            asyncio.run(factory.initialize())

        # Factory should still initialize successfully
        assert factory._initialized is True
        # The failed tool should be in specs with error
        failing_spec = next(
            (
                spec
                for spec in factory._loaded_tool_specs
                if spec.get("id") == "failing_agents"
            ),
            None,
        )
        if failing_spec:
            assert "error" in failing_spec
            assert "Invalid agent URL format" in failing_spec["error"]


class TestA2AToolSpecCreation:
    """Test A2A tool specification creation in isolation."""

    @pytest.mark.integration
    @patch("strands_agent_factory.tools.a2a._A2A_AVAILABLE", True)
    @patch("strands_agent_factory.tools.a2a.A2AClientToolProvider")
    def test_create_a2a_tool_spec_with_all_parameters(self, mock_a2a_provider_class):
        """Test A2A tool spec creation with all parameters."""
        from strands_agent_factory.tools.a2a import create_a2a_tool_spec

        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_provider = Mock()
        mock_provider.tools = [mock_tool]
        mock_a2a_provider_class.return_value = mock_provider

        config = {
            "id": "full_config_agents",
            "type": "a2a",
            "urls": [
                "http://agent1:8001/",
                "http://agent2:8002/",
                "http://agent3:8003/",
            ],
            "timeout": 600,
            "webhook_url": "https://webhook.example.com/notify",
            "webhook_token": "webhook-secret-token",
        }

        result = create_a2a_tool_spec(config)

        # Verify successful creation
        assert "error" not in result
        assert "tools" in result
        assert len(result["tools"]) == 1

        # Verify provider was created with all parameters
        mock_a2a_provider_class.assert_called_once_with(
            provider_id="full_config_agents",
            known_agent_urls=[
                "http://agent1:8001/",
                "http://agent2:8002/",
                "http://agent3:8003/",
            ],
            timeout=600,
            webhook_url="https://webhook.example.com/notify",
            webhook_token="webhook-secret-token",
        )

    @pytest.mark.integration
    @patch("strands_agent_factory.tools.a2a._A2A_AVAILABLE", True)
    @patch("strands_agent_factory.tools.a2a.A2AClientToolProvider")
    def test_create_a2a_tool_spec_with_default_timeout(self, mock_a2a_provider_class):
        """Test A2A tool spec creation uses default timeout when not specified."""
        from strands_agent_factory.tools.a2a import create_a2a_tool_spec

        mock_provider = Mock()
        mock_provider.tools = []
        mock_a2a_provider_class.return_value = mock_provider

        config = {
            "id": "default_timeout_agents",
            "type": "a2a",
            "urls": ["http://localhost:8001/"],
            # timeout not specified
        }

        result = create_a2a_tool_spec(config)

        # Verify default timeout of 300 was used
        mock_a2a_provider_class.assert_called_once()
        call_kwargs = mock_a2a_provider_class.call_args[1]
        assert call_kwargs["timeout"] == 300

    @pytest.mark.integration
    def test_create_a2a_tool_spec_validates_empty_urls(self):
        """Test A2A tool spec creation rejects empty URLs list."""
        from strands_agent_factory.tools.a2a import create_a2a_tool_spec

        config = {"id": "empty_urls_agents", "type": "a2a", "urls": []}

        result = create_a2a_tool_spec(config)

        # Should return error for empty URLs
        assert "error" in result
        assert "missing required 'urls' field" in result["error"]
