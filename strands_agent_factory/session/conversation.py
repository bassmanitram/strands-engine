"""
Conversation manager factory for strands_agent_factory.

This module provides the ConversationManagerFactory class, which creates and 
configures conversation managers based on EngineConfig settings. It supports
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

from typing import Optional
from loguru import logger

from strands.agent.conversation_manager import (
    ConversationManager,
    NullConversationManager,
    SlidingWindowConversationManager,
    SummarizingConversationManager
)
from strands import Agent

from strands_agent_factory.core.config import AgentFactoryConfig
from strands_agent_factory.adapters.base import load_framework_adapter


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
    """

    @staticmethod
    def create_conversation_manager(config: AgentFactoryConfig) -> ConversationManager:
        """
        Create a conversation manager based on engine configuration.
        
        Creates and configures a conversation manager according to the strategy
        specified in EngineConfig. Handles all configuration validation,
        optional component creation (like summarization agents), and provides
        graceful fallback behavior.
        
        Args:
            config: EngineConfig containing conversation manager settings
            
        Returns:
            ConversationManager: Configured conversation manager instance
        """
        logger.trace("create_conversation_manager called with type: {}", config.conversation_manager_type)
        
        try:
            if config.conversation_manager_type == "null":
                logger.debug("Creating NullConversationManager")
                result = NullConversationManager()

            elif config.conversation_manager_type == "sliding_window":
                logger.debug("Creating SlidingWindowConversationManager "
                             f"with window_size={config.sliding_window_size}")
                result = SlidingWindowConversationManager(
                    window_size=config.sliding_window_size,
                    should_truncate_results=config.should_truncate_results
                )

            elif config.conversation_manager_type == "summarizing":
                logger.debug("Creating SummarizingConversationManager "
                             f"with summary_ratio={config.summary_ratio}")

                # Create optional summarization agent if a different model is specified
                summarization_agent = None
                if config.summarization_model:
                    logger.debug("Creating summarization agent with model: "
                                 f"{config.summarization_model}")
                    try:
                        summarization_agent = (
                            ConversationManagerFactory
                            ._create_summarization_agent(
                                config.summarization_model)
                        )
                        if summarization_agent:
                            logger.info("Successfully created summarization agent")
                        else:
                            logger.warning("Failed to create summarization agent, "
                                           "proceeding without one")
                    except Exception as e:
                        logger.error(f"Error creating summarization agent: {e}")
                        logger.info("Proceeding without summarization agent")
                        summarization_agent = None

                # Create the summarizing conversation manager
                logger.debug("Creating SummarizingConversationManager instance")
                result = SummarizingConversationManager(
                    summary_ratio=config.summary_ratio,
                    preserve_recent_messages=config.preserve_recent_messages,
                    summarization_agent=summarization_agent,
                    summarization_system_prompt=config.custom_summarization_prompt
                )

            else:
                raise ValueError("Unknown conversation manager type: "
                                 f"{config.conversation_manager_type}")

            logger.debug("create_conversation_manager returning: {}", type(result).__name__)
            return result

        except Exception as e:
            logger.error(f"Failed to create conversation manager: {e}")
            logger.info("Falling back to NullConversationManager")
            result = NullConversationManager()
            logger.debug("create_conversation_manager returning fallback: {}", type(result).__name__)
            return result

    @staticmethod
    def _create_summarization_agent(model_string: str) -> Optional[Agent]:
        """
        Create a separate agent for summarization using a different model.
        
        Creates a lightweight Agent instance specifically for conversation
        summarization. This allows using a different (typically cheaper/faster)
        model for summarization while using a more capable model for the main
        conversation.
        
        Args:
            model_string: Model identifier for the summarization agent
            
        Returns:
            Optional[Agent]: Configured summarization agent, or None if creation fails
        """
        logger.trace("_create_summarization_agent called with model_string: {}", model_string)
        
        try:
            logger.debug("Loading summarization model: {}", model_string)

            # Parse model string - expect format like "framework:model_id"
            if ':' not in model_string:
                logger.error(f"Invalid model string format: {model_string} (expected 'framework:model_id')")
                return None

            framework, model_id = model_string.split(':', 1)
            
            adapter = load_framework_adapter(framework)
            if not adapter:
                logger.error(f"Failed to load adapter for framework: {framework}")
                return None
            
            model = adapter.load_model(model_id, model_config={})

            if not model:
                logger.warning("Failed to create summarization model: "
                               f"{model_string}")
                return None

            logger.debug("Summarization model loaded successfully")

            # Create agent args for summarization agent
            agent_args = adapter.prepare_agent_args(
                system_prompt="You are a conversation summarizer.",
                messages=[],
                emulate_system_prompt=False
            )

            logger.debug("Creating summarization agent with lightweight configuration")

            # Create a lightweight agent for summarization (no tools, simple callback)
            summarization_agent = Agent(
                model=model,
                callback_handler=None,
                agent_id="strands_agent_factory_summarization_agent",
                **agent_args
            )

            logger.info("Successfully created summarization agent with model: "
                        f"{model_string}")
            logger.debug("_create_summarization_agent returning agent")
            return summarization_agent

        except Exception as e:
            logger.error(f"Failed to create summarization agent: {e}")
            return None