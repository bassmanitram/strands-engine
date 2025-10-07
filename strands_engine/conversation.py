"""
Factory for creating conversation managers based on configuration.

This module provides a centralized way to create and configure conversation managers
for the YACBA agent, supporting different strategies for managing conversation history.
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
    """Factory for creating conversation managers based on YACBA configuration."""

    @staticmethod
    def create_conversation_manager(config: EngineConfig) -> ConversationManager:
        """
        Create a conversation manager based on the configuration.

        Args:
            config: YACBA configuration containing conversation manager settings

        Returns:
            Configured conversation manager instance

        Raises:
            ValueError: If configuration is invalid
            Exception: If manager creation fails
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

                # Create optional summarization agent if a different model is
                # specified
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

        Args:
            model_string: Model string for the summarization agent

        Returns:
            Configured agent for summarization, or None if creation fails
        """
        try:
            logger.debug(f"Loading summarization model: {model_string}")

            framework, model_id = model_string.partition(':') 

            if not framework:
                return None
            
            adapter = load_framework_adapter(framework)
            if not adapter:
                return None
            
            model = adapter.create_model(model_id, model_config={})

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

            logger.debug("Creating summarization agent with lightweight "
                         "configuration")

            # Create a lightweight agent for summarization (no tools, simple
            # callback)
            summarization_agent = Agent(
                model=model,
                callback_handler=None,
                agent_id="yacba_summarization_agent",
            )

            logger.info("Successfully created summarization agent with model: "
                        f"{model_string}")
            return summarization_agent

        except Exception as e:
            logger.error(f"Failed to create summarization agent: {e}")
            logger.debug("Summarization agent creation exception:",
                         exc_info=True)
            return None
