"""
OpenAI framework adapter for strands_agent_factory.

This module provides the OpenAIAdapter class, which enables strands_agent_factory
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

from typing import List, Optional, Dict, Any
from loguru import logger
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
        logger.debug("OpenAIAdapter.framework_name called")
        return "openai"

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
        logger.debug(f"OpenAIAdapter.load_model called with model_name='{model_name}', model_config={model_config}")
        
        model_config = model_config or {}
        logger.debug(f"Using model_config: {model_config}")
        
        # Set model name if provided
        if model_name:
            model_config["model"] = model_name
            logger.debug(f"Set model_config['model'] to '{model_name}'")
        
        # Extract client-specific arguments
        client_args = model_config.pop("client_args", None)
        logger.debug(f"Extracted client_args: {client_args}")
        logger.debug(f"Final model_config after client_args extraction: {model_config}")
        
        # Create and return the OpenAI model
        logger.debug(f"Creating OpenAIModel with client_args={client_args}, model_config={model_config}")
        model = OpenAIModel(client_args=client_args, model_config=model_config)
        
        logger.debug(f"OpenAIModel created successfully: {type(model).__name__}")
        return model

    def adapt_tools(self, tools: List[Tool], model_string: str) -> List[Tool]:
        """
        Adapt tools for OpenAI compatibility.
        
        OpenAI generally supports standard tool schemas without modification,
        so this method performs minimal adaptation. The default implementation
        returns tools unchanged, but could be extended for OpenAI-specific
        optimizations or schema adjustments if needed.
        
        Args:
            tools: List of tool objects to adapt
            model_string: Model string for potential model-specific adaptations
            
        Returns:
            List[Tool]: Tools adapted for OpenAI (unchanged by default)
            
        Note:
            OpenAI's function calling API is generally compatible with
            standard JSON schemas, so extensive adaptation is typically
            not required. This method provides an extension point for
            future OpenAI-specific tool optimizations.
        """
        logger.debug(f"OpenAIAdapter.adapt_tools called with {len(tools) if tools else 0} tools, model_string='{model_string}'")
        
        # OpenAI generally supports standard tool schemas without modification
        if tools:
            logger.debug("OpenAI adapter: Tools passed through without modification")
        else:
            logger.debug("No tools to adapt")
        
        logger.debug(f"Tool adaptation completed, returning {len(tools) if tools else 0} tools")
        return tools