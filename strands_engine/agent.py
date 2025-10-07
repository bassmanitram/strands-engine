import sys
from typing import Union, List, Dict, Any

from loguru import logger
from strands import Agent

from strands_engine.framework.base_adapter import FrameworkAdapter

class WrappedAgent(Agent):
    def __init__(self, adapter: FrameworkAdapter, **kwargs: Any) -> None:
        # Store adapter before calling parent constructor
        self.adapter = adapter

        # Call parent constructor with all other arguments
        super().__init__(**kwargs)

    async def handle_agent_stream(self,
        message: Union[str, List[Dict[str, Any]]]) -> bool:
        if not message:
            return True

        try:
            # Transform the message using the framework adapter
            transformed_message = self.adapter.transform_content(message)

            # Stream the response - the CustomCallbackHandler handles all output formatting
            async for _ in self.stream_async(transformed_message):
                pass

            return True
        except Exception as e:
            logger.error(f"Unexpected error in agent stream: {e}")
            print(
                f"\nAn unexpected error occurred while generating the response: {e}",
                file=sys.stderr,
            )
            return False

    async def send_message_to_agent(self,
        message: Union[str, List[Dict[str, Any]]],
        show_user_input: bool = True
    ) -> bool:
        """
        Higher-level function to send a message to the agent with optional input display.

        Args:
            message: Message to send
            show_user_input: Whether to display the user input

        Returns:
            True on success, False on failure
        """
        if show_user_input and isinstance(message, str):
            print(f"You: {message}")

        return await self.handle_agent_stream(message)
