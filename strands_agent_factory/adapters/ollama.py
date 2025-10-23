"""
Ollama framework adapter for strands_agent_factory.

This module provides the OllamaAdapter class, which enables strands_agent_factory
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

from .base import FrameworkAdapter
from ..core.types import Tool

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
        logger.trace("OllamaAdapter.framework_name called")
        result = "ollama"
        logger.trace("OllamaAdapter.framework_name returning: {}", result)
        return result

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
            
        Raises:
            ValueError: If neither model_name nor model in config is provided
            RuntimeError: If model creation fails
            
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
        if logger.level('TRACE').no >= logger._core.min_level:
            logger.trace("OllamaAdapter.load_model called with model_name='{}', model_config keys: {}", 
                        model_name, list(model_config.keys()) if model_config else [])
        
        model_config = model_config or {}
        logger.debug("Using model_config: {}", model_config)
        
        # Set model name if provided
        if model_name:
            model_config["model"] = model_name
            logger.debug("Set model_config['model'] to '{}'", model_name)
        
        # Validate that we have a model identifier
        if not model_config.get("model"):
            logger.error("No model identifier provided")
            raise ValueError("Model identifier must be provided either as model_name parameter or in model_config['model']")
        
        # Extract Ollama-specific configuration
        host = model_config.pop("host", "127.0.0.1:11434")
        ollama_client_args = model_config.pop("ollama_client_args", None)
        
        logger.debug("Using host: {}", host)
        if logger.level('TRACE').no >= logger._core.min_level:
            logger.trace("Extracted ollama_client_args: {}", ollama_client_args)
            logger.trace("Final model_config after extraction: {}", model_config)
        
        try:
            # Create and return the Ollama model
            logger.debug("Creating OllamaModel with host={}", host)
            model = OllamaModel(host=host, ollama_client_args=ollama_client_args, **model_config)
            
            logger.debug("OllamaModel created successfully: {}", type(model).__name__)
            logger.trace("OllamaAdapter.load_model completed successfully")
            return model
            
        except Exception as e:
            logger.error("Failed to create OllamaModel: {}", e)
            raise RuntimeError(f"Failed to create Ollama model: {e}") from e