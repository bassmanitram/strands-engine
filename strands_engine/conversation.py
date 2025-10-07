"""
Conversation manager factory for strands_engine.

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

from strands_engine.config import EngineConfig
from strands_engine.framework.base_adapter import load_framework_adapter


class ConversationManagerFactory:
    """
    Factory for creating conversation managers based on engine configuration.
    
    The ConversationManagerFactory provides a centralized way to create and
    configure conversation managers for strands_engine agents. It handles the
    complexity of different conversation management strategies while providing
    robust error handling and fallback mechanisms.
    
    The factory supports:
    - Multiple conversation management strategies
    - Optional summarization agent creation for summarizing strategy
    - Graceful fallback to NullConversationManager on errors
    - Comprehensive logging for debugging and monitoring
    
    All factory methods are static, making the class a pure factory without
    instance state management requirements.
    
    Example:
        Creating a conversation manager::
        
            config = EngineConfig(
                model="gpt-4o",
                conversation_manager_type="sliding_window",
                sliding_window_size=20
            )
            
            manager = ConversationManagerFactory.create_conversation_manager(config)
    """

    @staticmethod
    def create_conversation_manager(config: EngineConfig) -> ConversationManager:
        """
        Create a conversation manager based on engine configuration.
        
        Creates and configures a conversation manager according to the strategy
        specified in EngineConfig. Handles all configuration validation,
        optional component creation (like summarization agents), and provides
        graceful fallback behavior.
        
        The method supports three conversation management strategies:
        1. "null": No conversation management (unlimited context)
        2. "sliding_window": Maintain a fixed-size window of recent messages
        3. "summarizing": Summarize older messages when approaching context limits
        
        Args:
            config: EngineConfig containing conversation manager settings
            
        Returns:
            ConversationManager: Configured conversation manager instance
            
        Note:
            If any errors occur during creation, the method falls back to
            NullConversationManager to ensure the agent remains functional.
            Errors are logged with appropriate detail levels.
            
        Example:
            >>> config = EngineConfig(
            ...     model="gpt-4o",
            ...     conversation_manager_type="summarizing",
            ...     summary_ratio=0.3,
            ...     summarization_model="gpt-3.5-turbo"
            ... )
            >>> manager = ConversationManagerFactory.create_conversation_manager(config)
            >>> isinstance(manager, SummarizingConversationManager)
            True
        """
        try:
            if config.conversation_manager_type == "null":
                logger.debug("Creating NullConversationManager")
                return NullConversationManager()

            elif config.conversation_manager_type == "sliding_window":
                logger.debug("Creating SlidingWindowConversationManager "
                             f"with window_size={config.sliding_window_size}")
                return SlidingWindowConversationManager(
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
                return SummarizingConversationManager(
                    summary_ratio=config.summary_ratio,
                    preserve_recent_messages=config.preserve_recent_messages,
                    summarization_agent=summarization_agent,
                    summarization_system_prompt=config.custom_summarization_prompt
                )

            else:
                raise ValueError("Unknown conversation manager type: "
                                 f"{config.conversation_manager_type}")

        except Exception as e:
            logger.error(f"Failed to create conversation manager: {e}")
            logger.debug("Exception details:", exc_info=True)
            logger.info("Falling back to NullConversationManager")
            return NullConversationManager()

    @staticmethod
    def _create_summarization_agent(model_string: str) -> Optional[Agent]:
        """
        Create a separate agent for summarization using a different model.
        
        Creates a lightweight Agent instance specifically for conversation
        summarization. This allows using a different (typically cheaper/faster)
        model for summarization while using a more capable model for the main
        conversation.
        
        The summarization agent is created with:
        - No tools (summarization doesn't need external capabilities)
        - Minimal callback handling (no complex output formatting needed)
        - Simple system prompt focused on summarization task
        - Same framework adapter pattern as main agent for consistency
        
        Args:
            model_string: Model identifier for the summarization agent
            
        Returns:
            Optional[Agent]: Configured summarization agent, or None if creation fails
            
        Note:
            Errors during summarization agent creation are handled gracefully.
            The SummarizingConversationManager can operate without a dedicated
            summarization agent by using the main agent for summarization.
            
        Example:
            >>> agent = ConversationManagerFactory._create_summarization_agent("gpt-3.5-turbo")
            >>> agent.agent_id
            "yacba_summarization_agent"
        """
        try:
            logger.debug(f"Loading summarization model: {model_string}")

            framework, model_id = model_string.partition(':') 

            if not framework:
                return None
            
            adapter = load_framework_adapter(framework)
            if not adapter:
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
                startup_files_content=None,
                emulate_system_prompt=False
            )

            logger.debug("Creating summarization agent with lightweight configuration")

            # Create a lightweight agent for summarization (no tools, simple callback)
            summarization_agent = Agent(
                model=model,
                callback_handler=None,
                agent_id="strands_engine_summarization_agent",
            )

            logger.info("Successfully created summarization agent with model: "
                        f"{model_string}")
            return summarization_agent

        except Exception as e:
            logger.error(f"Failed to create summarization agent: {e}")
            logger.debug("Summarization agent creation exception:",
                         exc_info=True)
            return None