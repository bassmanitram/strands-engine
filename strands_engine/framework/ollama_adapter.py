"""
Ollama framework adapter for strands_engine.

This module provides the OllamaAdapter class, which enables strands_engine
to work with Ollama for local model serving. Ollama provides a simple API
for running various open-source language models locally, making it ideal
for development, testing, and scenarios requiring data privacy.

The Ollama adapter supports:
- Local model serving via Ollama API
- Configuration for various open-source models (Llama, Code Llama, etc.)
- Host and connection configuration for local or remote Ollama instances
- Automatic system prompt emulation for models that need it

Ollama is particularly useful for:
- Local development without API costs
- Privacy-sensitive applications requiring local processing
- Testing and experimentation with open-source models
- Offline operation scenarios
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from .base_adapter import FrameworkAdapter
from ..ptypes import Tool, Message

from strands.models.ollama import OllamaModel


class OllamaAdapter(FrameworkAdapter):
    """
    Framework adapter for Ollama local model serving.
    
    OllamaAdapter provides integration with Ollama, enabling the use of
    various open-source language models running locally. It handles Ollama-
    specific configuration, connection management, and model-specific
    optimizations for better performance with local models.
    
    The adapter handles:
    - Ollama server connection configuration
    - Model-specific optimizations and workarounds
    - System prompt emulation for models that need it
    - Host configuration for local or remote Ollama instances
    
    Key features:
    - Support for all Ollama-compatible models
    - Automatic system prompt emulation for certain models
    - Configurable host and connection parameters
    - Model-specific behavior optimizations
    - Local development friendly configuration
    
    Supported models include:
    - Llama 2 and variants
    - Code Llama for programming tasks
    - Mistral models
    - Gemma models
    - Custom fine-tuned models
    
    Example:
        Basic usage with default local Ollama::
        
            adapter = OllamaAdapter()
            model = adapter.load_model("llama2")
            
        With custom Ollama host::
        
            config = {
                "model": "llama2:13b",
                "host": "192.168.1.100:11434",
                "temperature": 0.8
            }
            model = adapter.load_model(config=config)
            
        With client-specific arguments::
        
            config = {
                "model": "codellama",
                "host": "localhost:11434",
                "ollama_client_args": {
                    "timeout": 120
                }
            }
            model = adapter.load_model(config=config)
    """

    @property
    def framework_name(self) -> str:
        """
        Get the framework name for this adapter.
        
        Returns:
            str: Framework identifier "ollama" for logging and debugging
        """
        return "ollama"

    def adapt_tools(self, tools: List[Tool], model_string: str) -> List[Tool]:
        """
        Adapt tools for Ollama model compatibility.
        
        Some Ollama models may have limitations with complex tool schemas
        or specific formatting requirements. This method can apply model-
        specific adaptations to ensure optimal tool compatibility.
        
        Args:
            tools: List of tool objects to adapt
            model_string: Model string (used for model-specific adaptations)
            
        Returns:
            List[Tool]: Tools adapted for Ollama compatibility
            
        Note:
            Current implementation returns tools unchanged. Future versions
            may add specific adaptations for different Ollama models based
            on their capabilities and limitations.
        """
        # Ollama models generally work well with standard tool schemas
        # Return tools unchanged for now
        return tools

    def load_model(self, model_name: Optional[str] = None, model_config: Optional[Dict[str, Any]] = None) -> OllamaModel:
        """
        Load an Ollama model for local serving.
        
        Creates and configures an OllamaModel instance for use with strands-agents.
        Handles Ollama-specific configuration including host settings, client
        parameters, and model-specific options.
        
        The method supports:
        - Model name specification (e.g., "llama2", "codellama:13b")
        - Host configuration for local or remote Ollama instances
        - Client timeout and connection settings
        - Model parameters (temperature, context length, etc.)
        
        Args:
            model_name: Ollama model identifier (optional if in model_config)
            model_config: Configuration dictionary with model and connection settings
            
        Returns:
            OllamaModel: Configured model instance ready for agent use
            
        Example:
            Basic local model::
            
                model = adapter.load_model("llama2")
                
            Remote Ollama instance::
            
                config = {
                    "model": "llama2:13b",
                    "host": "192.168.1.100:11434"
                }
                model = adapter.load_model(config=config)
                
            With client configuration::
            
                config = {
                    "model": "codellama",
                    "host": "localhost:11434",
                    "ollama_client_args": {
                        "timeout": 300
                    },
                    "temperature": 0.1
                }
                model = adapter.load_model(config=config)
                
        Note:
            The host parameter defaults to "127.0.0.1:11434" for local Ollama
            instances. Ollama client arguments are passed directly to the
            underlying Ollama client for advanced configuration.
        """
        model_config = model_config or {}
        
        # Set model name if provided
        if model_name:
            model_config["model"] = model_name
            
        # Extract Ollama-specific configuration
        host = model_config.pop("host", "127.0.0.1:11434")
        ollama_client_args = model_config.pop("ollama_client_args", None)
        
        # Create and return the Ollama model
        return OllamaModel(host=host, ollama_client_args=ollama_client_args, model_config=model_config)

    def prepare_agent_args(
        self,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Message]] = None,
        startup_files_content: Optional[List[Message]] = None,
        emulate_system_prompt: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Prepare agent arguments with Ollama-specific optimizations.
        
        Some Ollama models, particularly smaller or older ones, may not handle
        system prompts well. This method provides automatic detection and
        emulation for models that benefit from having system prompts prepended
        to user messages instead of using native system prompt support.
        
        Args:
            system_prompt: System prompt to use
            messages: Existing message history
            startup_files_content: Optional startup file messages
            emulate_system_prompt: Whether to force system prompt emulation
            **kwargs: Additional arguments including model_string
            
        Returns:
            Dict[str, Any]: Dictionary of arguments for Agent constructor
            
        Note:
            The method automatically enables system prompt emulation for
            certain models known to work better with this approach, including
            TinyLlama, Orca-Mini, and other smaller models. This can be
            overridden by explicitly setting emulate_system_prompt.
            
        Example:
            The method will automatically detect models like::
            
                - "tinyllama" -> enables emulation
                - "orca-mini" -> enables emulation  
                - "llama2:70b" -> uses native system prompts
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
        """
        Get comprehensive model information for Ollama.
        
        Returns detailed information about the Ollama adapter and its
        capabilities for debugging, logging, and monitoring purposes.
        
        Returns:
            Dict[str, Any]: Dictionary containing model information including:
            - framework: "ollama"
            - provider: "ollama" 
            - type: "local"
            - description: Human-readable description
            
        Example:
            >>> adapter.get_model_info()
            {
                "framework": "ollama",
                "provider": "ollama",
                "type": "local", 
                "description": "Local model serving via Ollama"
            }
        """
        return {
            "framework": self.framework_name,
            "provider": "ollama",
            "type": "local",
            "description": "Local model serving via Ollama"
        }