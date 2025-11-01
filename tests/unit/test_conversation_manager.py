"""Tests for conversation manager factory."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from strands_agent_factory.core.config import AgentFactoryConfig
from strands_agent_factory.core.exceptions import InitializationError
from strands_agent_factory.session.conversation import ConversationManagerFactory


class TestSummarizingConversationManager:
    """Test summarizing conversation manager creation logic."""

    def test_creates_agent_when_summarization_model_config_specified(self):
        """Should create separate agent when summarization_model_config is specified."""
        config = AgentFactoryConfig(
            model="openai:gpt-4o",
            conversation_manager_type="summarizing",
            summarization_model_config={"temperature": 0.3},
        )

        with patch(
            "strands_agent_factory.session.conversation.load_framework_adapter"
        ) as mock_load:
            mock_adapter = Mock()
            mock_model = Mock()
            mock_adapter.load_model.return_value = mock_model
            mock_adapter.prepare_agent_args.return_value = {}
            mock_load.return_value = mock_adapter

            with patch(
                "strands_agent_factory.session.conversation.Agent"
            ) as mock_agent_class:
                mock_agent_class.return_value = Mock()

                manager = ConversationManagerFactory.create_conversation_manager(config)

                # Should have called load_model with the config
                mock_adapter.load_model.assert_called_once()
                assert mock_adapter.load_model.call_args[0][1] == {"temperature": 0.3}

    def test_uses_main_model_when_no_summarization_model_specified(self):
        """Should use main model when only summarization_model_config is specified."""
        config = AgentFactoryConfig(
            model="openai:gpt-4o",
            conversation_manager_type="summarizing",
            summarization_model_config={"temperature": 0.3},
        )

        with patch(
            "strands_agent_factory.session.conversation.load_framework_adapter"
        ) as mock_load:
            mock_adapter = Mock()
            mock_model = Mock()
            mock_adapter.load_model.return_value = mock_model
            mock_adapter.prepare_agent_args.return_value = {}
            mock_load.return_value = mock_adapter

            with patch(
                "strands_agent_factory.session.conversation.Agent"
            ) as mock_agent_class:
                mock_agent_class.return_value = Mock()

                manager = ConversationManagerFactory.create_conversation_manager(config)

                # Should have used main model
                mock_adapter.load_model.assert_called_once()
                assert mock_adapter.load_model.call_args[0][0] == "gpt-4o"

    def test_raises_error_when_agent_creation_fails_with_explicit_config(self):
        """Should raise InitializationError when agent creation fails with explicit config."""
        config = AgentFactoryConfig(
            model="openai:gpt-4o",
            conversation_manager_type="summarizing",
            summarization_model_config={"temperature": 0.3},
        )

        with patch(
            "strands_agent_factory.session.conversation.load_framework_adapter"
        ) as mock_load:
            mock_adapter = Mock()
            mock_adapter.load_model.return_value = None  # Simulate failure
            mock_load.return_value = mock_adapter

            with pytest.raises(InitializationError) as exc_info:
                ConversationManagerFactory.create_conversation_manager(config)

            assert (
                "Cannot fulfill explicit summarization configuration requirements"
                in str(exc_info.value)
            )

    def test_fallback_when_agent_creation_fails_without_explicit_config(self):
        """Should fallback gracefully when agent creation fails without explicit config."""
        config = AgentFactoryConfig(
            model="openai:gpt-4o", conversation_manager_type="summarizing"
        )

        with patch(
            "strands_agent_factory.session.conversation.load_framework_adapter"
        ) as mock_load:
            mock_adapter = Mock()
            mock_adapter.load_model.return_value = None  # Simulate failure
            mock_load.return_value = mock_adapter

            with patch(
                "strands_agent_factory.session.conversation.SummarizingConversationManager"
            ) as mock_scm:
                mock_scm.return_value = Mock()

                manager = ConversationManagerFactory.create_conversation_manager(config)

                # Should have created manager without agent
                mock_scm.assert_called_once()
                call_kwargs = mock_scm.call_args[1]
                assert call_kwargs["summarization_agent"] is None
                assert "summarization_system_prompt" in call_kwargs

    def test_raises_error_when_summarization_model_specified_and_fails(self):
        """Should raise InitializationError when summarization_model specified and fails."""
        config = AgentFactoryConfig(
            model="openai:gpt-4o",
            conversation_manager_type="summarizing",
            summarization_model="openai:gpt-3.5-turbo",
        )

        with patch(
            "strands_agent_factory.session.conversation.load_framework_adapter"
        ) as mock_load:
            mock_adapter = Mock()
            mock_adapter.load_model.return_value = None  # Simulate failure
            mock_load.return_value = mock_adapter

            with pytest.raises(InitializationError) as exc_info:
                ConversationManagerFactory.create_conversation_manager(config)

            assert (
                "Cannot fulfill explicit summarization configuration requirements"
                in str(exc_info.value)
            )
