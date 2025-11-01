"""
Integration tests for AgentFactory and related components.

Tests the complete factory workflow including configuration validation,
tool loading, adapter selection, and agent creation.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from strands_agent_factory.core.config import AgentFactoryConfig
from strands_agent_factory.core.exceptions import (
    AdapterError,
    ConfigurationError,
    InitializationError,
)
from strands_agent_factory.core.factory import AgentFactory


class TestAgentFactoryIntegration:
    """Integration tests for AgentFactory."""

    @pytest.mark.integration
    def test_factory_initialization_basic(self, basic_config):
        """Test basic factory initialization without external dependencies."""
        factory = AgentFactory(basic_config)

        assert factory.config == basic_config
        assert factory._initialized is False
        assert factory._framework_name == "anthropic"
        assert factory._model_id == "claude-3-5-sonnet"

    @pytest.mark.integration
    def test_factory_model_string_parsing(self):
        """Test various model string parsing scenarios."""
        test_cases = [
            ("gpt-4o", ("openai", "gpt-4o")),
            ("gemini:gemini-2.5-flash", ("gemini", "gemini-2.5-flash")),
            ("anthropic:claude-3-5-sonnet", ("anthropic", "claude-3-5-sonnet")),
            ("litellm:gemini/gemini-2.5-flash", ("litellm", "gemini/gemini-2.5-flash")),
            ("ollama:llama2:7b", ("ollama", "llama2:7b")),
        ]

        for model_string, expected in test_cases:
            config = AgentFactoryConfig(model=model_string)
            factory = AgentFactory(config)

            assert factory._framework_name == expected[0]
            assert factory._model_id == expected[1]

    @pytest.mark.integration
    def test_factory_with_tool_configs(self, temp_dir):
        """Test factory initialization with tool configurations."""
        # Create a simple Python tool config
        tool_config = {
            "id": "test_math_tools",
            "type": "python",
            "module_path": "operator",
            "functions": ["add", "mul"],
            "package_path": None,
        }

        config_file = temp_dir / "math_tools.json"
        with open(config_file, "w") as f:
            json.dump(tool_config, f)

        config = AgentFactoryConfig(
            model="anthropic:claude-3-5-sonnet", tool_config_paths=[str(config_file)]
        )

        factory = AgentFactory(config)

        assert len(factory.config.tool_config_paths) == 1
        assert str(config_file) in factory.config.tool_config_paths

    @pytest.mark.integration
    def test_factory_with_file_uploads(self, temp_file):
        """Test factory initialization with file uploads."""
        config = AgentFactoryConfig(
            model="anthropic:claude-3-5-sonnet",
            file_paths=[(str(temp_file), "text/plain")],
            initial_message="Please analyze this file",
        )

        factory = AgentFactory(config)

        assert len(factory.config.file_paths) == 1
        assert factory.config.initial_message == "Please analyze this file"

    @pytest.mark.integration
    def test_factory_session_configuration(self, temp_sessions_dir):
        """Test factory with session management configuration."""
        config = AgentFactoryConfig(
            model="anthropic:claude-3-5-sonnet",
            sessions_home=str(temp_sessions_dir),
            session_id="test_session_123",
            conversation_manager_type="sliding_window",
            sliding_window_size=30,
        )

        factory = AgentFactory(config)

        # DelegatingSession uses session_id, not session_name
        assert factory._session_manager.session_id == "test_session_123"
        assert factory.config.conversation_manager_type == "sliding_window"

    @pytest.mark.integration
    @patch("strands_agent_factory.core.factory.load_framework_adapter")
    async def test_factory_initialization_workflow(
        self, mock_load_adapter, basic_config
    ):
        """Test the complete factory initialization workflow."""
        # Mock the adapter
        mock_adapter = Mock()
        mock_adapter.framework_name = "anthropic"
        mock_load_adapter.return_value = mock_adapter

        factory = AgentFactory(basic_config)

        # Initialize the factory
        await factory.initialize()

        assert factory._initialized is True
        assert factory._framework_adapter == mock_adapter
        mock_load_adapter.assert_called_once_with("anthropic")

    @pytest.mark.integration
    @patch("strands_agent_factory.core.factory.load_framework_adapter")
    async def test_factory_initialization_with_tools(self, mock_load_adapter, temp_dir):
        """Test factory initialization with tool loading."""
        # Create a tool configuration
        tool_config = {
            "id": "test_tool",
            "type": "python",
            "module_path": "builtins",
            "functions": ["len", "str"],
            "package_path": None,
        }

        config_file = temp_dir / "tools.json"
        with open(config_file, "w") as f:
            json.dump(tool_config, f)

        config = AgentFactoryConfig(
            model="anthropic:claude-3-5-sonnet", tool_config_paths=[str(config_file)]
        )

        # Mock the adapter
        mock_adapter = Mock()
        mock_adapter.framework_name = "anthropic"
        mock_load_adapter.return_value = mock_adapter

        factory = AgentFactory(config)
        await factory.initialize()

        assert factory._initialized is True
        assert len(factory._loaded_tool_specs) > 0

    @pytest.mark.integration
    @patch("strands_agent_factory.core.factory.load_framework_adapter")
    async def test_factory_initialization_with_files(
        self, mock_load_adapter, temp_file
    ):
        """Test factory initialization with file processing."""
        config = AgentFactoryConfig(
            model="anthropic:claude-3-5-sonnet",
            file_paths=[(str(temp_file), "text/plain")],
            initial_message="Process this file",
        )

        # Mock the adapter
        mock_adapter = Mock()
        mock_adapter.framework_name = "anthropic"
        mock_load_adapter.return_value = mock_adapter

        factory = AgentFactory(config)
        await factory.initialize()

        assert factory._initialized is True
        assert factory._initial_messages is not None
        assert len(factory._initial_messages) > 0

    @pytest.mark.integration
    async def test_factory_initialization_adapter_failure(self, basic_config):
        """Test factory initialization when adapter loading fails."""
        with patch(
            "strands_agent_factory.core.factory.load_framework_adapter"
        ) as mock_load:
            mock_load.side_effect = AdapterError("Adapter not found")

            factory = AgentFactory(basic_config)

            with pytest.raises(
                InitializationError, match="Factory initialization failed"
            ):
                await factory.initialize()

    @pytest.mark.integration
    @patch("strands_agent_factory.core.factory.load_framework_adapter")
    async def test_factory_create_agent(self, mock_load_adapter, basic_config):
        """Test agent creation after successful initialization."""
        # Mock the adapter
        mock_adapter = Mock()
        mock_adapter.framework_name = "anthropic"
        mock_adapter.load_model.return_value = Mock()
        mock_adapter.prepare_agent_args.return_value = {
            "system_prompt": "Test prompt",
            "messages": [],
        }
        mock_load_adapter.return_value = mock_adapter

        factory = AgentFactory(basic_config)
        await factory.initialize()

        agent = factory.create_agent()

        # Just verify that an agent was created, not the exact mock instance
        assert agent is not None
        assert hasattr(agent, "__enter__")  # AgentProxy should be a context manager
        mock_adapter.load_model.assert_called_once()

    @pytest.mark.integration
    def test_factory_create_agent_not_initialized(self, basic_config):
        """Test agent creation when factory is not initialized."""
        factory = AgentFactory(basic_config)

        with pytest.raises(InitializationError, match="factory not initialized"):
            factory.create_agent()

    @pytest.mark.integration
    @patch("strands_agent_factory.core.factory.load_framework_adapter")
    async def test_factory_conversation_manager_setup(
        self, mock_load_adapter, basic_config
    ):
        """Test conversation manager setup during initialization."""
        # Mock the adapter
        mock_adapter = Mock()
        mock_load_adapter.return_value = mock_adapter

        factory = AgentFactory(basic_config)
        await factory.initialize()

        # Just verify that a conversation manager was created
        assert factory._conversation_manager is not None
        # Check for a method that actually exists on conversation managers
        assert hasattr(factory._conversation_manager, "apply_management")

    @pytest.mark.integration
    async def test_factory_error_handling_during_initialization(self, basic_config):
        """Test error handling during various initialization phases."""
        factory = AgentFactory(basic_config)

        # Test adapter loading failure
        with patch(
            "strands_agent_factory.core.factory.load_framework_adapter"
        ) as mock_load:
            mock_load.side_effect = Exception("Unexpected adapter error")

            with pytest.raises(
                InitializationError, match="Factory initialization failed"
            ):
                await factory.initialize()

    @pytest.mark.integration
    def test_factory_callback_handler_setup(self):
        """Test callback handler setup with different configurations."""
        # Test with default callback handler
        config1 = AgentFactoryConfig(
            model="anthropic:claude-3-5-sonnet",
            show_tool_use=True,
            response_prefix="AI: ",
        )

        factory1 = AgentFactory(config1)

        assert factory1._callback_handler is not None
        assert factory1._callback_handler.show_tool_use is True
        assert factory1._callback_handler.response_prefix == "AI: "

        # Test with custom callback handler
        custom_handler = Mock()
        config2 = AgentFactoryConfig(
            model="anthropic:claude-3-5-sonnet", callback_handler=custom_handler
        )

        factory2 = AgentFactory(config2)

        assert factory2._callback_handler == custom_handler

    @pytest.mark.integration
    def test_factory_configuration_validation_integration(self):
        """Test that factory properly validates configuration during creation."""
        # Test invalid model configuration
        with pytest.raises(ConfigurationError):
            AgentFactoryConfig(model="")

        # Test invalid file paths
        with pytest.raises(ConfigurationError):
            AgentFactoryConfig(
                model="anthropic:claude-3-5-sonnet",
                file_paths=[("/nonexistent/file.txt", "text/plain")],
            )

        # Test invalid conversation manager settings
        with pytest.raises(ConfigurationError):
            AgentFactoryConfig(
                model="anthropic:claude-3-5-sonnet", sliding_window_size=-1
            )

    @pytest.mark.integration
    @patch("strands_agent_factory.core.factory.load_framework_adapter")
    async def test_factory_tool_loading_integration(self, mock_load_adapter, temp_dir):
        """Test integration between factory and tool loading system."""
        # Create tool configuration
        tool_config = {
            "id": "integration_test_tool",
            "type": "python",
            "module_path": "math",
            "functions": ["sqrt", "pow"],
        }

        config_file = temp_dir / "integration_tools.json"
        with open(config_file, "w") as f:
            json.dump(tool_config, f)

        config = AgentFactoryConfig(
            model="anthropic:claude-3-5-sonnet", tool_config_paths=[str(config_file)]
        )

        # Mock adapter
        mock_adapter = Mock()
        mock_load_adapter.return_value = mock_adapter

        factory = AgentFactory(config)
        await factory.initialize()

        # Just verify that tools were loaded
        assert len(factory._loaded_tool_specs) > 0

    @pytest.mark.integration
    def test_factory_exit_stack_management(self, basic_config):
        """Test that factory properly manages resources with ExitStack."""
        factory = AgentFactory(basic_config)

        # ExitStack should be initialized
        assert factory._exit_stack is not None

        # Test that it's properly configured for resource management
        assert hasattr(factory._exit_stack, "enter_context")
        assert hasattr(factory._exit_stack, "close")
