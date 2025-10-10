"""
Anthropic framework adapter for strands_agent_factory.

This module provides the AnthropicAdapter class, which enables strands_agent_factory
to work directly with Anthropic's Claude models via their native API. The
adapter handles Anthropic-specific model loading, configuration, and tool
adaptation while maintaining compatibility with strands-agents.

The Anthropic adapter supports:
- Direct Anthropic API integration for Claude models
- Model configuration with Anthropic-specific parameters
- Tool schema compatibility with Anthropic's function calling
- Client configuration for authentication and connection settings

This adapter is designed for applications that need direct Anthropic integration
with Claude models without the overhead of proxy layers.
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from .base_adapter import FrameworkAdapter
from ..ptypes import Tool

from strands.models.anthropic import AnthropicModel


class AnthropicAdapter(FrameworkAdapter):
    """
    Framework adapter for direct Anthropic API integration.
    
    AnthropicAdapter provides native integration with Anthropic's Claude models,
    handling model loading, configuration, and Anthropic-specific adaptations.
    It supports all Claude model variants including Claude 3.5 Sonnet, Claude 3
    Haiku, and other models available through Anthropic's API.
    
    The adapter handles:
    - Anthropic model instantiation and configuration
    - Tool schema adaptation for Anthropic's function calling
    - Client configuration for API authentication
    - Anthropic-specific parameter handling
    
    Configuration options support both model-level and client-level
    settings, allowing fine-grained control over API behavior and
    authentication.
    
    Example:
        Basic usage::
        
            adapter = AnthropicAdapter()
            model = adapter.load_model("claude-3-5-sonnet-20241022")
            
        With custom configuration::
        
            config = {
                "temperature": 0.7,
                "max_tokens": 4000,
                "client_args": {
                    "api_key": "sk-ant-...",
                    "timeout": 60
                }
            }
            model = adapter.load_model("claude-3-5-sonnet-20241022", config)
    """

    @property
    def framework_name(self) -> str:
        """
        Get the framework name for this adapter.
        
        Returns:
            str: Framework identifier "anthropic" for logging and debugging
        """
        logger.trace("AnthropicAdapter.framework_name called")
        return "anthropic"
    
    def load_model(self, model_name: Optional[str] = None, model_config: Optional[Dict[str, Any]] = None) -> AnthropicModel:
        """
        Load an Anthropic model using the Anthropic API.
        
        Creates and configures an AnthropicModel instance for use with
        strands-agents. Handles both model-specific configuration and
        Anthropic client configuration for authentication and connection
        settings.
        
        The method supports:
        - Model name specification (e.g., "claude-3-5-sonnet-20241022")
        - Model parameters (temperature, max_tokens, etc.)
        - Client configuration (API keys, timeouts, base URLs)
        - Authentication and connection settings
        
        Args:
            model_name: Anthropic model identifier (optional if in model_config)
            model_config: Configuration dictionary with model and client settings
            
        Returns:
            AnthropicModel: Configured model instance ready for agent use
            
        Example:
            Basic model loading::
            
                model = adapter.load_model("claude-3-5-sonnet-20241022")
                
            With detailed configuration::
            
                config = {
                    "model": "claude-3-5-sonnet-20241022",
                    "temperature": 0.7,
                    "max_tokens": 4000,
                    "client_args": {
                        "api_key": "sk-ant-...",
                        "timeout": 30
                    }
                }
                model = adapter.load_model(config=config)
                
        Note:
            The model_config dictionary is split into model parameters
            and client arguments. Client arguments are passed to the
            Anthropic client constructor, while other parameters configure
            the model behavior.
        """
        logger.trace(f"AnthropicAdapter.load_model called with model_name='{model_name}', model_config={model_config}")
        
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
        
        # Create and return the Anthropic model
        logger.debug(f"Creating AnthropicModel with client_args={client_args}, model_config={model_config}")
        model = AnthropicModel(client_args=client_args, model_config=model_config)
        
        logger.debug(f"AnthropicModel created successfully: {type(model).__name__}")
        return model

    def adapt_tools(self, tools: List[Tool], model_string: str) -> List[Tool]:
        """
        Adapt tools for Anthropic compatibility.
        
        Anthropic's Claude models generally support standard tool schemas
        with minimal modification. This method performs basic compatibility
        checks and adaptations if needed, but typically returns tools unchanged.
        
        Args:
            tools: List of tool objects to adapt
            model_string: Model string for potential model-specific adaptations
            
        Returns:
            List[Tool]: Tools adapted for Anthropic (unchanged by default)
            
        Note:
            Anthropic's function calling API is generally compatible with
            standard JSON schemas. This method provides an extension point
            for future Anthropic-specific tool optimizations or schema
            adjustments if they become necessary.
        """
        logger.trace(f"AnthropicAdapter.adapt_tools called with {len(tools) if tools else 0} tools, model_string='{model_string}'")
        
        # Anthropic generally supports standard tool schemas without modification
        if tools:
            logger.debug("Anthropic adapter: Tools passed through without modification")
        else:
            logger.debug("No tools to adapt")
        
        logger.trace(f"Tool adaptation completed, returning {len(tools) if tools else 0} tools")
        return tools