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

from .base_adapter import FrameworkAdapter
from ..ptypes import Tool

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
        return "ollama"

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
        logger.trace(f"OllamaAdapter.load_model called with model_name='{model_name}', model_config={model_config}")
        
        model_config = model_config or {}
        logger.debug(f"Using model_config: {model_config}")
        
        # Set model name if provided
        if model_name:
            model_config["model"] = model_name
            logger.debug(f"Set model_config['model'] to '{model_name}'")
        
        # Extract Ollama-specific configuration
        host = model_config.pop("host", "127.0.0.1:11434")
        ollama_client_args = model_config.pop("ollama_client_args", None)
        
        logger.debug(f"Using host: {host}")
        logger.debug(f"Extracted ollama_client_args: {ollama_client_args}")
        logger.debug(f"Final model_config after extraction: {model_config}")
        
        # Create and return the Ollama model
        logger.debug(f"Creating OllamaModel with host={host}, ollama_client_args={ollama_client_args}, model_config={model_config}")
        model = OllamaModel(host=host, ollama_client_args=ollama_client_args, model_config=model_config)
        
        logger.debug(f"OllamaModel created successfully: {type(model).__name__}")
        return model

    def adapt_tools(self, tools: List[Tool], model_string: str) -> List[Tool]:
        """
        Adapt tools for Ollama compatibility.
        
        Many Ollama models have varying levels of tool support, and some may
        require specific formatting or limitations. This method provides a
        place to handle Ollama-specific tool adaptations, though the default
        implementation passes tools through unchanged.
        
        Args:
            tools: List of tool objects to adapt
            model_string: Model string for potential model-specific adaptations
            
        Returns:
            List[Tool]: Tools adapted for Ollama (unchanged by default)
            
        Note:
            Tool support varies significantly across different Ollama models.
            Some models may not support function calling at all, while others
            may have specific requirements for tool schemas. This method
            provides an extension point for model-specific adaptations.
        """
        logger.trace(f"OllamaAdapter.adapt_tools called with {len(tools) if tools else 0} tools, model_string='{model_string}'")
        
        # Ollama tool support varies by model - for now, pass through unchanged
        if tools:
            logger.debug("Ollama adapter: Tools passed through without modification")
            logger.debug(f"Note: Tool support varies across Ollama models. Model '{model_string}' may have limited tool capabilities.")
        else:
            logger.debug("No tools to adapt")
        
        logger.trace(f"Tool adaptation completed, returning {len(tools) if tools else 0} tools")
        return tools