"""
Base framework adapter for strands_engine.

Provides the abstract base class that all framework adapters must implement.
Framework adapters handle the specifics of integrating with strands-agents
for different AI providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from strands.models import Model

from loguru import logger

from strands_engine.framework.litellm_adapter import LiteLLMAdapter

from ..ptypes import Tool, Message
import importlib

FRAMEWORK_HANDLERS = {
    "litellm": "strands_engine.framework.litellm_adapter.LiteLLMAdapter",
    "openai":  "strands_engine.framework.openai_adapter.OpenAIAdapter",
    "anthropic": "strands_engine.framework.anthropic_adapter.AnthropicAdapter",
    "bedrock": "strands_engine.framework.bedrock_adapter.BedrockAdapter",
    "ollama": "strands_engine.framework.ollama_adapter.OllamaAdapter"
}

class FrameworkAdapter(ABC):
    """
    Abstract base class for framework adapters.
    
    Framework adapters handle the specifics of integrating with different
    AI providers and frameworks for strands-agents compatibility.
    """

    @property
    @abstractmethod
    def framework_name(self) -> str:
        """Get the name of this framework (e.g., 'litellm', 'anthropic')."""
        pass

    @abstractmethod
    def adapt_tools(self, tools: List[Tool], model_string: str) -> List[Tool]:
        """
        Adapt tools for the specific framework.
        
        Different frameworks may require different tool formats or modifications.
        
        Args:
            tools: List of tool objects loaded by the engine
            model_string: Model string to determine adaptations needed
            
        Returns:
            List of framework-adapted tool objects
        """
        pass

    def prepare_agent_args(
        self,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Message]] = None,
        startup_files_content: Optional[List[Message]] = None,
        emulate_system_prompt: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Prepares the arguments for the Agent constructor.
        
        Handles message preparation and system prompt handling according to YACBA's logic.

        Args:
            system_prompt: System prompt to use
            messages: Existing message history
            startup_files_content: Optional startup file messages
            emulate_system_prompt: Whether to emulate system prompt in first user message
            **kwargs: Additional arguments

        Returns:
            Dictionary of arguments for Agent constructor
        """
        messages = messages or []
        
        # Combine startup files with existing messages
        if startup_files_content:
            messages = startup_files_content + messages

        # Handle system prompt emulation for frameworks that don't support it natively
        if emulate_system_prompt and system_prompt:
            logger.debug("Emulating system prompt by prepending to the first user message as requested.")
            first_user_msg_index = next(
                (i for i, msg in enumerate(messages) if msg["role"] == "user"), -1
            )

            if first_user_msg_index != -1:
                current_content = messages[first_user_msg_index]["content"]
                if isinstance(current_content, list):
                    messages[first_user_msg_index]["content"].insert(
                        0, {"type": "text", "text": system_prompt}
                    )
                else:
                    new_content = f"{system_prompt}\n\n{current_content}"
                    messages[first_user_msg_index]["content"] = new_content
            else:
                messages.insert(0, {
                    "role": "user",
                    "content": [{"type": "text", "text": system_prompt}]
                })

            agent_args = {"system_prompt": None, "messages": messages}
        else:
            agent_args = {"system_prompt": system_prompt, "messages": messages}

        # Add any additional kwargs
        agent_args.update(kwargs)
        
        return agent_args

    def transform_content(self, content: Any) -> Any:
        """
        Transform message content for the specific framework.
        
        Args:
            content: Content to transform
            
        Returns:
            Transformed content
        """
        return content

    # Optional methods with default implementations
    async def initialize(self, model: str, model_config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Initialize the framework adapter.
        
        Args:
            model: Model identifier
            model_config: Optional model-specific configuration
            
        Returns:
            True if initialization successful
        """
        return True

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        return {"framework": self.framework_name}
    
    @abstractmethod
    def load_model(self, 
                   model_name: Optional[str] = None, 
                   model_config: Optional[Dict[str, Any]] = None) -> Model:
        """
        Load a strands-agents model using the appropriate framework.
        
        This follows exactly the same pattern as YACBA's StrandsModelLoader.create_model().
        
        Args:
            model_string: Model string (e.g., 'gpt-4o', 'ollama:llama2:7b', 'anthropic:claude-3-5-sonnet-20241022')
            model_config: Optional model-specific configuration (passed opaquely to strands model)
            
        Returns:
            Tuple of (strands Model instance, FrameworkAdapter instance)
            
        Raises:
            ValueError: If framework not supported 
            RuntimeError: If model loading fails
        """
        pass

def load_framework_adapter(adapter_name: str) -> Optional[FrameworkAdapter]:
    class_path = FRAMEWORK_HANDLERS.get(adapter_name)
    if class_path:
        module_path, class_name = class_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        adapter_class = getattr(module, class_name)
        return adapter_class()
