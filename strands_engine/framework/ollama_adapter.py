"""
Ollama framework adapter for strands_engine.

This adapter handles Ollama-specific functionality for local model serving.
Ollama provides a local API for running various open-source models.
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from .base_adapter import FrameworkAdapter

from ..ptypes import Message

from strands.models.ollama import OllamaModel

class OllamaAdapter(FrameworkAdapter):
    """
    Adapter for Ollama framework.
    
    Ollama provides a local API for running open-source models like Llama 2, 
    Code Llama, and other models locally. This adapter handles Ollama-specific
    configuration and behavior.
    """

    @property
    def framework_name(self) -> str:
        """Get the framework name."""
        return "ollama"

    def load_model(self, model_name = None, model_config = None):
        model_config = model_config or {}
        if model_name:
            model_config["model"] = model_name
        host = model_config.pop("host", "127.0.0.1:11434")
        ollama_client_args = model_config.pop("ollama_client_args", None)
        return OllamaModel(host=host,ollama_client_args=ollama_client_args,model_config=model_config)

    def prepare_agent_args(
        self,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Message]] = None,
        startup_files_content: Optional[List[Message]] = None,
        emulate_system_prompt: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Prepare agent arguments for Ollama models.
        
        Some Ollama models may not support system prompts well, so we provide
        an option to emulate system prompts by prepending to user messages.

        Args:
            system_prompt: System prompt to use
            messages: Existing message history
            startup_files_content: Optional startup file messages
            emulate_system_prompt: Whether to emulate system prompt in first user message
            **kwargs: Additional arguments

        Returns:
            Dictionary of arguments for Agent constructor
        """
        # Check if we should automatically emulate system prompts for certain models
        model_string = kwargs.get('model_string', '')
        
        # Some older or smaller Ollama models don't handle system prompts well
        auto_emulate_models = ['tinyllama', 'orca-mini']
        if any(model in model_string.lower() for model in auto_emulate_models):
            logger.debug(f"Auto-enabling system prompt emulation for Ollama model: {model_string}")
            emulate_system_prompt = True
        
        # Use parent class implementation with potentially modified emulation setting
        return super().prepare_agent_args(
            system_prompt=system_prompt,
            messages=messages,
            startup_files_content=startup_files_content,
            emulate_system_prompt=emulate_system_prompt,
            **kwargs
        )

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information for Ollama."""
        return {
            "framework": self.framework_name,
            "provider": "ollama",
            "type": "local",
            "description": "Local model serving via Ollama"
        }