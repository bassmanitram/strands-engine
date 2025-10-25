"""
Unit tests for strands_agent_factory.core.config module.

Tests configuration validation, initialization, and error handling.
"""

import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from strands_agent_factory.core.config import AgentFactoryConfig
from strands_agent_factory.core.exceptions import ConfigurationError


class TestAgentFactoryConfig:
    """Test cases for AgentFactoryConfig class."""

    def test_basic_config_creation(self):
        """Test basic configuration creation with minimal parameters."""
        config = AgentFactoryConfig(model="openai:gpt-4o")
        
        assert config.model == "openai:gpt-4o"
        assert config.system_prompt is None
        assert config.tool_config_paths == []
        assert config.sliding_window_size == 40
        assert config.preserve_recent_messages == 10

    def test_config_with_system_prompt(self):
        """Test configuration with system prompt."""
        system_prompt = "You are a helpful assistant."
        config = AgentFactoryConfig(
            model="openai:gpt-4o",
            system_prompt=system_prompt
        )
        
        assert config.system_prompt == system_prompt

    def test_config_with_tool_config_paths(self):
        """Test configuration with tool config paths (individual files only)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Create a valid tool config file
            tool_config = {
                "id": "test_tool",
                "type": "python",
                "module_path": "test.module",
                "functions": ["test_func"]
            }
            json.dump(tool_config, f)
            tool_config_file = f.name
        
        try:
            config = AgentFactoryConfig(
                model="openai:gpt-4o",
                tool_config_paths=[tool_config_file]
            )
            
            assert config.tool_config_paths == [tool_config_file]
        finally:
            os.unlink(tool_config_file)

    def test_config_with_file_paths(self):
        """Test configuration with file paths."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_file = f.name
        
        try:
            config = AgentFactoryConfig(
                model="openai:gpt-4o",
                file_paths=[(temp_file, "text/plain")]
            )
            
            assert config.file_paths == [(temp_file, "text/plain")]
        finally:
            os.unlink(temp_file)

    def test_config_with_conversation_management(self):
        """Test configuration with conversation management parameters."""
        config = AgentFactoryConfig(
            model="openai:gpt-4o",
            sliding_window_size=20,
            preserve_recent_messages=8,
            conversation_manager_type="summarizing"
        )
        
        assert config.sliding_window_size == 20
        assert config.preserve_recent_messages == 8
        assert config.conversation_manager_type == "summarizing"

    def test_config_with_model_config(self):
        """Test configuration with model-specific configuration."""
        model_config = {"temperature": 0.7, "max_tokens": 1000}
        config = AgentFactoryConfig(
            model="openai:gpt-4o",
            model_config=model_config
        )
        
        assert config.model_config == model_config

    def test_full_config_creation(self):
        """Test configuration with many parameters."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_file = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tool_f:
            # Create a valid tool config file
            tool_config = {
                "id": "test_tool",
                "type": "python", 
                "module_path": "test.module",
                "functions": ["test_func"]
            }
            json.dump(tool_config, tool_f)
            tool_config_file = tool_f.name
        
        try:
            config = AgentFactoryConfig(
                model="openai:gpt-4o",
                system_prompt="You are helpful",
                tool_config_paths=[tool_config_file],
                file_paths=[(temp_file, "text/plain")],
                sliding_window_size=15,
                preserve_recent_messages=7,
                conversation_manager_type="summarizing",
                model_config={"temperature": 0.5}
            )
            
            assert config.model == "openai:gpt-4o"
            assert config.system_prompt == "You are helpful"
            assert len(config.tool_config_paths) == 1
            assert config.file_paths == [(temp_file, "text/plain")]
            assert config.sliding_window_size == 15
            assert config.preserve_recent_messages == 7
            assert config.conversation_manager_type == "summarizing"
            assert config.model_config["temperature"] == 0.5
        finally:
            os.unlink(temp_file)
            os.unlink(tool_config_file)

    def test_model_validation_required(self):
        """Test that model parameter is required."""
        with pytest.raises(TypeError):
            AgentFactoryConfig()

    def test_model_validation_not_empty(self):
        """Test that model cannot be empty string."""
        with pytest.raises(ConfigurationError, match="Model identifier is required"):
            AgentFactoryConfig(model="")

    def test_model_validation_format(self):
        """Test model format validation."""
        # Valid formats
        valid_models = [
            "openai:gpt-4o",
            "anthropic:claude-3-sonnet",
            "local_model",
            "provider:model-name-123"
        ]
        
        for model in valid_models:
            config = AgentFactoryConfig(model=model)
            assert config.model == model

    def test_model_validation_invalid_format(self):
        """Test model format validation with invalid formats."""
        invalid_models = [
            "model with spaces",
            "model@invalid",
            "model#invalid"
        ]
        
        for model in invalid_models:
            with pytest.raises(ConfigurationError):
                AgentFactoryConfig(model=model)

    def test_sliding_window_validation_positive(self):
        """Test sliding window size must be positive."""
        with pytest.raises(ConfigurationError, match="sliding_window_size must be positive"):
            AgentFactoryConfig(
                model="openai:gpt-4o",
                sliding_window_size=0
            )
        
        with pytest.raises(ConfigurationError, match="sliding_window_size must be positive"):
            AgentFactoryConfig(
                model="openai:gpt-4o",
                sliding_window_size=-1
            )

    def test_preserve_messages_validation_non_negative(self):
        """Test preserve recent messages must be non-negative."""
        with pytest.raises(ConfigurationError, match="preserve_recent_messages cannot be negative"):
            AgentFactoryConfig(
                model="openai:gpt-4o",
                preserve_recent_messages=-1
            )

    def test_preserve_messages_validation_within_window(self):
        """Test preserve recent messages cannot exceed sliding window size."""
        with pytest.raises(ConfigurationError, match="preserve_recent_messages.*cannot exceed sliding_window_size"):
            AgentFactoryConfig(
                model="openai:gpt-4o",
                sliding_window_size=5,
                preserve_recent_messages=10
            )

    def test_files_validation_exist(self):
        """Test that specified files must exist."""
        with pytest.raises(ConfigurationError, match="File does not exist"):
            AgentFactoryConfig(
                model="openai:gpt-4o",
                file_paths=[("/nonexistent/file.txt", None)]
            )

    def test_files_validation_readable(self):
        """Test that specified files must be readable."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name
        
        try:
            # Make file unreadable
            os.chmod(temp_file, 0o000)
            
            with pytest.raises(ConfigurationError, match="File is not readable"):
                AgentFactoryConfig(
                    model="openai:gpt-4o",
                    file_paths=[(temp_file, None)]
                )
        finally:
            # Restore permissions and cleanup
            os.chmod(temp_file, 0o644)
            os.unlink(temp_file)

    def test_file_paths_validation_format(self):
        """Test file_paths must be list of tuples."""
        with pytest.raises(ConfigurationError, match="file_paths must be a list"):
            AgentFactoryConfig(
                model="openai:gpt-4o",
                file_paths="not_a_list"
            )

    def test_file_paths_validation_tuple_format(self):
        """Test file_paths items must be tuples."""
        with pytest.raises(ConfigurationError, match="must be a \\(path, mimetype\\) tuple"):
            AgentFactoryConfig(
                model="openai:gpt-4o",
                file_paths=["not_a_tuple"]
            )

    def test_tool_config_paths_validation_list(self):
        """Test tool_config_paths must be a list."""
        with pytest.raises(ConfigurationError, match="tool_config_paths must be a list"):
            AgentFactoryConfig(
                model="openai:gpt-4o",
                tool_config_paths="not_a_list"
            )

    def test_tool_config_paths_validation_exist(self):
        """Test tool config paths must exist."""
        with pytest.raises(ConfigurationError, match="Tool config path does not exist"):
            AgentFactoryConfig(
                model="openai:gpt-4o",
                tool_config_paths=["/nonexistent/path"]
            )

    def test_tool_config_paths_validation_files_only(self):
        """Test tool config paths must be files, not directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ConfigurationError, match="Tool config path must be an individual file, not a directory"):
                AgentFactoryConfig(
                    model="openai:gpt-4o",
                    tool_config_paths=[temp_dir]
                )

    def test_tool_config_paths_validation_file_extension_warning(self):
        """Test tool config paths with non-standard extensions generate warnings."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test content")
            temp_file = f.name
        
        try:
            # This should work but may generate a warning
            config = AgentFactoryConfig(
                model="openai:gpt-4o",
                tool_config_paths=[temp_file]
            )
            assert config.tool_config_paths == [temp_file]
        finally:
            os.unlink(temp_file)

    def test_model_config_validation_dict(self):
        """Test model_config must be a dictionary."""
        with pytest.raises(ConfigurationError, match="model_config must be a dictionary"):
            AgentFactoryConfig(
                model="openai:gpt-4o",
                model_config="not_a_dict"
            )

    def test_model_config_temperature_validation(self):
        """Test model_config temperature validation."""
        # Valid temperature
        config = AgentFactoryConfig(
            model="openai:gpt-4o",
            model_config={"temperature": 0.7}
        )
        assert config.model_config["temperature"] == 0.7
        
        # Invalid temperature (too high)
        with pytest.raises(ConfigurationError, match="temperature must be between 0.0 and 2.0"):
            AgentFactoryConfig(
                model="openai:gpt-4o",
                model_config={"temperature": 3.0}
            )

    def test_model_config_max_tokens_validation(self):
        """Test model_config max_tokens validation."""
        # Valid max_tokens
        config = AgentFactoryConfig(
            model="openai:gpt-4o",
            model_config={"max_tokens": 1000}
        )
        assert config.model_config["max_tokens"] == 1000
        
        # Invalid max_tokens (negative)
        with pytest.raises(ConfigurationError, match="max_tokens must be positive"):
            AgentFactoryConfig(
                model="openai:gpt-4o",
                model_config={"max_tokens": -1}
            )

    def test_summary_ratio_validation(self):
        """Test summary_ratio validation."""
        # Valid ratio
        config = AgentFactoryConfig(
            model="openai:gpt-4o",
            summary_ratio=0.5
        )
        assert config.summary_ratio == 0.5
        
        # Invalid ratio (too high)
        with pytest.raises(ConfigurationError, match="summary_ratio must be between 0.1 and 0.8"):
            AgentFactoryConfig(
                model="openai:gpt-4o",
                summary_ratio=0.9
            )

    def test_session_id_validation(self):
        """Test session_id validation."""
        # Valid session_id
        config = AgentFactoryConfig(
            model="openai:gpt-4o",
            session_id="valid_session_123"
        )
        assert config.session_id == "valid_session_123"
        
        # Invalid session_id (invalid characters)
        with pytest.raises(ConfigurationError, match="session_id contains invalid characters"):
            AgentFactoryConfig(
                model="openai:gpt-4o",
                session_id="invalid/session"
            )

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Minimum valid sliding window with preserve messages
        config = AgentFactoryConfig(
            model="openai:gpt-4o",
            sliding_window_size=1,
            preserve_recent_messages=1
        )
        assert config.sliding_window_size == 1
        assert config.preserve_recent_messages == 1
        
        # Zero preserve messages (valid)
        config = AgentFactoryConfig(
            model="openai:gpt-4o",
            preserve_recent_messages=0
        )
        assert config.preserve_recent_messages == 0

    def test_config_immutability(self):
        """Test that configuration values are properly set."""
        config = AgentFactoryConfig(
            model="openai:gpt-4o",
            system_prompt="Test prompt"
        )
        
        # Values should be accessible
        assert config.model == "openai:gpt-4o"
        assert config.system_prompt == "Test prompt"

    def test_default_values(self):
        """Test default values are set correctly."""
        config = AgentFactoryConfig(model="openai:gpt-4o")
        
        assert config.system_prompt is None
        assert config.tool_config_paths == []
        assert config.file_paths == []
        assert config.sliding_window_size == 40
        assert config.preserve_recent_messages == 10
        assert config.conversation_manager_type == "sliding_window"
        assert config.model_config is None

    def test_config_with_empty_lists(self):
        """Test configuration with explicitly empty lists."""
        config = AgentFactoryConfig(
            model="openai:gpt-4o",
            tool_config_paths=[],
            file_paths=[]
        )
        
        assert config.tool_config_paths == []
        assert config.file_paths == []

    def test_config_representation(self):
        """Test string representation of configuration."""
        config = AgentFactoryConfig(
            model="openai:gpt-4o",
            system_prompt="Test"
        )
        
        # Should be able to convert to string without error
        str_repr = str(config)
        assert "openai:gpt-4o" in str_repr

    @patch('os.path.exists')
    @patch('os.access')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_file_validation_mocked(self, mock_is_file, mock_path_exists, mock_access, mock_os_exists):
        """Test file validation with mocked filesystem."""
        mock_os_exists.return_value = True
        mock_path_exists.return_value = True
        mock_is_file.return_value = True
        mock_access.return_value = True
        
        config = AgentFactoryConfig(
            model="openai:gpt-4o",
            file_paths=[("/mocked/file.txt", "text/plain")]
        )
        
        assert config.file_paths == [("/mocked/file.txt", "text/plain")]

    def test_conversation_manager_types(self):
        """Test different conversation manager types."""
        valid_types = ["null", "sliding_window", "summarizing"]
        
        for manager_type in valid_types:
            config = AgentFactoryConfig(
                model="openai:gpt-4o",
                conversation_manager_type=manager_type
            )
            assert config.conversation_manager_type == manager_type

    def test_optional_parameters(self):
        """Test various optional parameters."""
        config = AgentFactoryConfig(
            model="openai:gpt-4o",
            initial_message="Hello!",
            summarization_model="gpt-3.5-turbo",
            custom_summarization_prompt="Summarize this:",
            should_truncate_results=False,
            emulate_system_prompt=True,
            show_tool_use=True,
            response_prefix="Bot: "
        )
        
        assert config.initial_message == "Hello!"
        assert config.summarization_model == "gpt-3.5-turbo"
        assert config.custom_summarization_prompt == "Summarize this:"
        assert config.should_truncate_results is False
        assert config.emulate_system_prompt is True
        assert config.show_tool_use is True
        assert config.response_prefix == "Bot: "