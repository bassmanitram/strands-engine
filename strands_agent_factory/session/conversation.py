"""
Conversation manager factory for strands_agent_factory.

This module provides the ConversationManagerFactory class, which creates and
configures conversation managers based on AgentFactoryConfig settings. It supports
different conversation management strategies for handling context length limits
and conversation history management.

The factory supports multiple conversation management strategies:
- NullConversationManager: No conversation management (unlimited context)
- SlidingWindowConversationManager: Keep only recent messages within window
- SummarizingConversationManager: Summarize older messages when approaching limits

The factory handles the complexity of creating optional summarization agents
for the summarizing strategy while providing graceful fallbacks when
configuration or creation fails.
"""

from typing import Any, Dict, Optional

from loguru import logger
from strands import Agent
from strands.agent.conversation_manager import (
    ConversationManager,
    NullConversationManager,
    SlidingWindowConversationManager,
    SummarizingConversationManager,
)
from strands.agent.conversation_manager.summarizing_conversation_manager import (
    DEFAULT_SUMMARIZATION_PROMPT,
)

from strands_agent_factory.adapters.base import load_framework_adapter
from strands_agent_factory.core.config import AgentFactoryConfig
from strands_agent_factory.core.exceptions import InitializationError


class ConversationManagerFactory:
    """
    Factory for creating conversation managers based on engine configuration.

    The ConversationManagerFactory provides a centralized way to create and
    configure conversation managers for strands_agent_factory agents. It handles the
    complexity of different conversation management strategies while providing
    robust error handling and fallback mechanisms.

    The factory supports:
    - Multiple conversation management strategies
    - Optional summarization agent creation for summarizing strategy
    - Graceful fallback to NullConversationManager on errors
    - Comprehensive logging for debugging and monitoring

    All factory methods are static, making the class a pure factory without
    instance state management requirements.

    Conversation Management Strategies:
        null: No conversation management - unlimited context length
        sliding_window: Maintains only the most recent N messages
        summarizing: Summarizes older messages when approaching context limits
    """

    @staticmethod
    def create_conversation_manager(config: AgentFactoryConfig) -> ConversationManager:
        """
        Create a conversation manager based on engine configuration.

        Creates and configures a conversation manager according to the strategy
        specified in AgentFactoryConfig. Handles all configuration validation,
        optional component creation (like summarization agents), and provides
        graceful fallback behavior.

        The method supports three conversation management strategies:
        1. Null: No management, unlimited context
        2. Sliding Window: Keep only recent messages within window size
        3. Summarizing: Summarize older messages when approaching limits

        For the summarizing strategy:
        - Always attempts to create a separate summarization agent
        - Uses summarization_model (or model if not specified)
        - Uses summarization_model_config (or {} if not specified)
        - If agent creation fails and user specified summarization_model or
          summarization_model_config, raises InitializationError
        - If agent creation fails and user did NOT specify either, falls back
          to using main agent for summarization

        Args:
            config: AgentFactoryConfig containing conversation manager settings

        Returns:
            ConversationManager: Configured conversation manager instance

        Raises:
            InitializationError: If summarization agent creation fails when user
                               explicitly specified summarization_model or
                               summarization_model_config

        Note:
            If creation fails for any reason (except explicit summarization
            requirements), falls back to NullConversationManager to ensure
            the agent can still function.
        """
        logger.trace(
            "create_conversation_manager called with type: {}",
            config.conversation_manager_type,
        )

        try:
            if config.conversation_manager_type == "null":
                logger.debug("Creating NullConversationManager")
                result = NullConversationManager()

            elif config.conversation_manager_type == "sliding_window":
                logger.debug(
                    "Creating SlidingWindowConversationManager with window_size={}",
                    config.sliding_window_size,
                )
                result = SlidingWindowConversationManager(
                    window_size=config.sliding_window_size,
                    should_truncate_results=config.should_truncate_results,
                )

            elif config.conversation_manager_type == "summarizing":
                result = ConversationManagerFactory._create_summarizing_manager(config)

            else:
                logger.error(
                    "Unknown conversation manager type: {}",
                    config.conversation_manager_type,
                )
                raise ValueError(
                    "Unknown conversation manager type: {}".format(
                        config.conversation_manager_type
                    )
                )

            logger.debug(
                "create_conversation_manager returning: {}", type(result).__name__
            )
            logger.trace("create_conversation_manager completed successfully")
            return result

        except InitializationError:
            # Re-raise InitializationError - don't fallback for explicit requirements
            raise
        except Exception as e:
            logger.error("Failed to create conversation manager: {}", e)
            logger.info("Falling back to NullConversationManager")
            result = NullConversationManager()
            logger.debug(
                "create_conversation_manager returning fallback: {}",
                type(result).__name__,
            )
            logger.trace("create_conversation_manager completed with fallback")
            return result

    @staticmethod
    def _create_summarizing_manager(
        config: AgentFactoryConfig,
    ) -> SummarizingConversationManager:
        """
        Create a summarizing conversation manager with optional separate agent.

        Always attempts to create a separate summarization agent to allow applying
        summarization_model_config even when using the same model as the main agent.

        Args:
            config: AgentFactoryConfig containing summarization settings

        Returns:
            SummarizingConversationManager: Configured manager instance

        Raises:
            InitializationError: If agent creation fails and user explicitly
                               specified summarization_model or summarization_model_config
        """
        logger.debug(
            "Creating SummarizingConversationManager with summary_ratio={}",
            config.summary_ratio,
        )

        # Determine if user explicitly requested summarization-specific settings
        has_explicit_requirements = bool(
            config.summarization_model or config.summarization_model_config
        )

        # Always attempt to create a separate summarization agent
        model_to_use = (
            config.summarization_model if config.summarization_model else config.model
        )

        logger.debug("Creating summarization agent with model: {}", model_to_use)
        try:
            summarization_agent = (
                ConversationManagerFactory._create_summarization_agent(
                    model_to_use,
                    config.summarization_model_config or {},
                    config.custom_summarization_prompt,
                )
            )

            if summarization_agent:
                logger.info("Successfully created summarization agent")
                # Create manager with agent, no system prompt (agent has it)
                return SummarizingConversationManager(
                    summary_ratio=config.summary_ratio,
                    preserve_recent_messages=config.preserve_recent_messages,
                    summarization_agent=summarization_agent,
                )
            else:
                # Agent creation returned None - handle based on whether requirements were explicit
                return ConversationManagerFactory._handle_agent_creation_failure(
                    config, model_to_use, has_explicit_requirements, error=None
                )

        except InitializationError:
            # Re-raise InitializationError as-is
            raise
        except Exception as e:
            # Exception during creation - handle based on whether requirements were explicit
            return ConversationManagerFactory._handle_agent_creation_failure(
                config, model_to_use, has_explicit_requirements, error=e
            )

    @staticmethod
    def _handle_agent_creation_failure(
        config: AgentFactoryConfig,
        model_to_use: str,
        has_explicit_requirements: bool,
        error: Optional[Exception],
    ) -> SummarizingConversationManager:
        """
        Handle summarization agent creation failure.

        Args:
            config: AgentFactoryConfig containing settings
            model_to_use: Model string that was attempted
            has_explicit_requirements: Whether user specified summarization_model
                                      or summarization_model_config
            error: Optional exception that caused the failure

        Returns:
            SummarizingConversationManager: Fallback manager using main agent

        Raises:
            InitializationError: If has_explicit_requirements is True
        """
        if has_explicit_requirements:
            # User explicitly requested summarization-specific settings - must error
            if error:
                logger.error("Error creating summarization agent: {}", error)
                raise InitializationError(
                    f"Failed to create summarization agent: {error}. "
                    f"Cannot fulfill explicit summarization configuration requirements."
                ) from error
            else:
                raise InitializationError(
                    f"Failed to create summarization agent with model '{model_to_use}'. "
                    f"Cannot fulfill explicit summarization configuration requirements."
                )
        else:
            # No explicit requirements - fallback to using main agent
            if error:
                logger.error("Error creating summarization agent: {}", error)
            else:
                logger.warning("Failed to create summarization agent")

            logger.info("Falling back to using main agent for summarization")
            return SummarizingConversationManager(
                summary_ratio=config.summary_ratio,
                preserve_recent_messages=config.preserve_recent_messages,
                summarization_agent=None,
                summarization_system_prompt=config.custom_summarization_prompt,
            )

    @staticmethod
    def _create_summarization_agent(
        model_string: str,
        model_config: Optional[Dict[str, Any]] = None,
        custom_summarization_prompt: Optional[str] = None,
    ) -> Optional[Agent]:
        """
        Create a separate agent for summarization using a different model.

        Creates a lightweight Agent instance specifically for conversation
        summarization. This allows using a different (typically cheaper/faster)
        model for summarization while using a more capable model for the main
        conversation.

        The summarization agent is configured with:
        - A system prompt for summarization tasks (custom or default)
        - No tools (lightweight operation)
        - No callback handler (silent operation)
        - Minimal configuration for efficiency

        Args:
            model_string: Model identifier for the summarization agent in format
                         "framework:model_id" (e.g., "openai:gpt-3.5-turbo")
            model_config: Optional framework-specific configuration for the
                         summarization model. Passed directly to adapter without
                         validation. If None, uses empty dict {}.
            custom_summarization_prompt: Optional custom system prompt for summarization.
                         If None, uses DEFAULT_SUMMARIZATION_PROMPT from strands.

        Returns:
            Optional[Agent]: Configured summarization agent, or None if creation fails

        Raises:
            No exceptions - all errors are caught and logged, returning None

        Example:
            >>> agent = ConversationManagerFactory._create_summarization_agent(
            ...     "openai:gpt-3.5-turbo",
            ...     {"temperature": 0.3, "max_tokens": 1000},
            ...     "Custom summarization prompt"
            ... )
            >>> if agent:
            ...     # Use agent for summarization
            ...     pass
        """
        logger.trace(
            "_create_summarization_agent called with model_string: {}, model_config: {}, custom_prompt: {}",
            model_string,
            model_config,
            custom_summarization_prompt is not None,
        )

        try:
            logger.debug("Loading summarization model: {}", model_string)

            # Parse model string - expect format like "framework:model_id"
            if ":" not in model_string:
                logger.error(
                    "Invalid model string format: {} (expected 'framework:model_id')",
                    model_string,
                )
                logger.trace(
                    "_create_summarization_agent returning None (invalid format)"
                )
                return None

            framework, model_id = model_string.split(":", 1)
            logger.trace(
                "Parsed model string: framework='{}', model_id='{}'",
                framework,
                model_id,
            )

            # Load framework adapter
            logger.trace("Loading framework adapter for: {}", framework)
            adapter = load_framework_adapter(framework)
            if not adapter:
                logger.error("Failed to load adapter for framework: {}", framework)
                logger.trace(
                    "_create_summarization_agent returning None (adapter load failed)"
                )
                return None

            # Load the model with config
            logger.trace("Loading model with adapter and config")
            model = adapter.load_model(model_id, model_config or {})

            if not model:
                logger.warning("Failed to create summarization model: {}", model_string)
                logger.trace(
                    "_create_summarization_agent returning None (model creation failed)"
                )
                return None

            logger.debug("Summarization model loaded successfully")

            # Determine system prompt: use custom if provided, otherwise use default from strands
            system_prompt = (
                custom_summarization_prompt
                if custom_summarization_prompt is not None
                else DEFAULT_SUMMARIZATION_PROMPT
            )
            logger.trace(
                "Using {} summarization prompt",
                "custom" if custom_summarization_prompt is not None else "default",
            )

            # Create agent args for summarization agent
            logger.trace("Preparing agent arguments for summarization agent")
            agent_args = adapter.prepare_agent_args(
                system_prompt=system_prompt, messages=[], emulate_system_prompt=False
            )

            logger.debug("Creating summarization agent with lightweight configuration")

            # Create a lightweight agent for summarization (no tools, simple callback)
            logger.trace("Creating Agent instance for summarization")
            summarization_agent = Agent(
                model=model,
                callback_handler=None,
                agent_id="strands_agent_factory_summarization_agent",
                **agent_args,
            )

            logger.info(
                "Successfully created summarization agent with model: {}", model_string
            )
            logger.trace("_create_summarization_agent returning agent successfully")
            return summarization_agent

        except Exception as e:
            logger.error("Failed to create summarization agent: {}", e)
            logger.trace(
                "_create_summarization_agent returning None (exception occurred)"
            )
            return None
