"""
OpenAI framework adapter for strands_engine.

This module provides the OpenAIAdapter class, which enables strands_engine
to work directly with OpenAI's API services. The adapter handles OpenAI-specific
model loading, configuration, and tool adaptation while maintaining compatibility
with the strands-agents ecosystem.

The OpenAI adapter supports:
- Direct OpenAI API integration
- Model configuration with OpenAI-specific parameters
- Tool schema compatibility with OpenAI's function calling
- Client configuration for authentication and connection settings

This adapter is designed for applications that need direct OpenAI integration
without the overhead of proxy layers like LiteLLM.
"""

from typing import Optional, Dict, Any, List
from strands.models.openai import OpenAIModel

from .base_adapter import FrameworkAdapter
from ..ptypes import Tool


class OpenAIAdapter(FrameworkAdapter):
    """
    Framework adapter for direct OpenAI API integration.
    
    OpenAIAdapter provides native integration with OpenAI's API services,
    handling model loading, configuration, and OpenAI-specific adaptations.
    It supports all OpenAI models including GPT-4, GPT-3.5, and other
    offerings available through the OpenAI API.
    
    The adapter handles:
    - OpenAI model instantiation and configuration
    - Tool schema adaptation for OpenAI function calling
    - Client configuration for API authentication
    - OpenAI-specific parameter handling
    
    Configuration options support both model-level and client-level
    settings, allowing fine-grained control over API behavior and
    authentication.
    
    Example:
        Basic usage::
        
            adapter = OpenAIAdapter()
            model = adapter.load_model("gpt-4o")
            
        With custom configuration::
        
            config = {
                "temperature": 0.7,
                "max_tokens": 2000,
                "client_args": {
                    "api_key": "custom-key",
                    "base_url": "https://custom.openai.endpoint/"
                }
            }
            model = adapter.load_model("gpt-4o", config)
    """

    @property
    def framework_name(self) -> str:
        """
        Get the framework name for this adapter.
        
        Returns:
            str: Framework identifier for logging and debugging
            
        Note:
            Returns "openai" to identify this as the OpenAI adapter,
            distinguishing it from other framework adapters.
        """
        return "openai"

    def adapt_tools(self, tools: List[Tool], model_string: str) -> List[Tool]:
        """
        Adapt tools for OpenAI function calling compatibility.
        
        OpenAI's function calling API has specific requirements for tool
        schemas. This method ensures that tools are properly formatted
        for OpenAI's expectations while preserving their functionality.
        
        Args:
            tools: List of tool objects to adapt
            model_string: Model string (used for model-specific adaptations)
            
        Returns:
            List[Tool]: Tools adapted for OpenAI compatibility
            
        Note:
            OpenAI generally has good tool schema compatibility, so this
            method typically returns tools unchanged. Future versions
            may add specific adaptations as needed.
        """
        # OpenAI generally has good tool compatibility
        # Return tools unchanged for now
        return tools

    def load_model(self, model_name: Optional[str] = None, model_config: Optional[Dict[str, Any]] = None) -> OpenAIModel:
        """
        Load an OpenAI model using the OpenAI API.
        
        Creates and configures an OpenAIModel instance for use with
        strands-agents. Handles both model-specific configuration and
        OpenAI client configuration for authentication and connection
        settings.
        
        The method supports:
        - Model name specification (e.g., "gpt-4o", "gpt-3.5-turbo")
        - Model parameters (temperature, max_tokens, etc.)
        - Client configuration (API keys, base URLs, timeouts)
        - Authentication and connection settings
        
        Args:
            model_name: OpenAI model identifier (optional if in model_config)
            model_config: Configuration dictionary with model and client settings
            
        Returns:
            OpenAIModel: Configured model instance ready for agent use
            
        Example:
            Basic model loading::
            
                model = adapter.load_model("gpt-4o")
                
            With detailed configuration::
            
                config = {
                    "model": "gpt-4o",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "client_args": {
                        "api_key": "sk-...",
                        "organization": "org-...",
                        "timeout": 60
                    }
                }
                model = adapter.load_model(config=config)
                
        Note:
            The model_config dictionary is split into model parameters
            and client arguments. Client arguments are passed to the
            OpenAI client constructor, while other parameters configure
            the model behavior.
        """
        model_config = model_config or {}
        
        # Set model name if provided
        if model_name:
            model_config["model"] = model_name
            
        # Extract client-specific arguments
        client_args = model_config.pop("client_args", None)
        
        # Create and return the OpenAI model
        return OpenAIModel(client_args=client_args, model_config=model_config)