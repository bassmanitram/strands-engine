"""
LiteLLM framework adapter for strands_agent_factory.

This module provides the LiteLLMAdapter class, which enables strands_agent_factory
to work with LiteLLM's unified interface to multiple AI providers. LiteLLM
acts as a proxy layer that provides consistent APIs across different AI
providers (OpenAI, Anthropic, Google, Azure, etc.).

The LiteLLM adapter handles:
- Model loading through LiteLLM's unified interface
- Tool schema cleaning for provider compatibility
- Provider-specific adaptations through LiteLLM
- Configuration management for various underlying providers

LiteLLM is particularly useful for applications that need to support multiple
AI providers without managing provider-specific code, or for switching between
providers based on cost, availability, or capability requirements.
"""

from typing import List, Optional, Dict, Any
from loguru import logger
from strands.models.litellm import LiteLLMModel

from .base_adapter import FrameworkAdapter
from ..ptypes import Tool
from ..utils import recursively_remove


class LiteLLMAdapter(FrameworkAdapter):
    """
    Framework adapter for LiteLLM unified AI provider interface.
    
    LiteLLMAdapter provides integration with LiteLLM, which offers a unified
    interface to multiple AI providers including OpenAI, Anthropic, Google,
    Azure, Cohere, and many others. This adapter handles the complexities
    of multi-provider support while maintaining compatibility with strands-agents.
    
    Key features:
    - Unified interface to 100+ AI models and providers
    - Automatic tool schema cleaning for provider compatibility
    - Support for provider-specific configurations
    - Cost optimization through provider switching
    - Fallback and retry mechanisms via LiteLLM
    
    The adapter is particularly valuable for:
    - Applications requiring multi-provider support
    - Cost optimization across different providers
    - High availability with provider fallbacks
    - Experimentation with different models and capabilities
    
    Example:
        Basic usage with OpenAI::
        
            adapter = LiteLLMAdapter()
            model = adapter.load_model("gpt-4o")
            
        With provider-specific configuration::
        
            config = {
                "model_id": "anthropic/claude-3-5-sonnet-20241022",
                "temperature": 0.7,
                "client_args": {
                    "api_key": "sk-ant-...",
                    "timeout": 60
                }
            }
            model = adapter.load_model(config=config)
            
        With Azure OpenAI::
        
            config = {
                "model_id": "azure/gpt-4o",
                "client_args": {
                    "api_key": "your-azure-key",
                    "api_base": "https://your-resource.openai.azure.com/",
                    "api_version": "2023-12-01-preview"
                }
            }
            model = adapter.load_model(config=config)
    """

    @property
    def framework_name(self) -> str:
        """
        Get the framework name for this adapter.
        
        Returns:
            str: Framework identifier "litellm" for logging and debugging
        """
        logger.debug("LiteLLMAdapter.framework_name called")
        return "litellm"

    def load_model(self, model_name: Optional[str] = None, model_config: Optional[Dict[str, Any]] = None) -> LiteLLMModel:
        """
        Load a model using LiteLLM's unified interface.
        
        Creates and configures a LiteLLMModel instance that can access any
        of the 100+ models supported by LiteLLM. The method handles both
        model-specific configuration and client-level settings for different
        providers.
        
        LiteLLM model identifiers follow the pattern:
        - "gpt-4o" (OpenAI, default provider)
        - "anthropic/claude-3-5-sonnet-20241022" (Anthropic)
        - "azure/gpt-4o" (Azure OpenAI)
        - "vertex_ai/gemini-pro" (Google Vertex AI)
        - "bedrock/anthropic.claude-3-sonnet-20240229-v1:0" (AWS Bedrock)
        
        Args:
            model_name: LiteLLM model identifier (optional if in model_config)
            model_config: Configuration dictionary with model and client settings
            
        Returns:
            LiteLLMModel: Configured model instance ready for agent use
            
        Example:
            Loading different provider models::
            
                # OpenAI GPT-4
                model = adapter.load_model("gpt-4o")
                
                # Anthropic Claude
                model = adapter.load_model("anthropic/claude-3-5-sonnet-20241022")
                
                # Azure OpenAI with custom config
                config = {
                    "temperature": 0.8,
                    "client_args": {
                        "api_key": "azure-key",
                        "api_base": "https://myresource.openai.azure.com/"
                    }
                }
                model = adapter.load_model("azure/gpt-4o", config)
                
        Note:
            The model_config dictionary is split into model parameters and
            client arguments. Client arguments are provider-specific and
            passed to the underlying provider's client constructor.
        """
        logger.debug(f"LiteLLMAdapter.load_model called with model_name='{model_name}', model_config={model_config}")
        
        model_config = model_config or {}
        logger.debug(f"Using model_config: {model_config}")
        
        # Set model identifier if provided - this must be at the top level for strands-agents
        if model_name:
            model_config["model_id"] = model_name
            logger.debug(f"Set model_config['model_id'] to '{model_name}' at top level")
            
        # Extract client-specific arguments
        client_args = model_config.pop("client_args", None)
        logger.debug(f"Extracted client_args: {client_args}")
        logger.debug(f"Final model_config after client_args extraction: {model_config}")
        
        # Create the LiteLLM model - pass model_config directly, not nested
        # The LiteLLMModel constructor expects the config to be passed as model_config parameter
        # but strands-agents expects model_id to be accessible at the top level of model.config
        logger.debug(f"Creating LiteLLMModel with client_args={client_args}, model_config={model_config}")
        model = LiteLLMModel(client_args=client_args, **model_config)
        
        logger.debug(f"LiteLLMModel created successfully: {type(model).__name__}")
        return model

    def adapt_tools(self, tools: List[Tool], model_string: str) -> List[Tool]:
        """
        Adapt tool schemas for LiteLLM provider compatibility.
        
        LiteLLM supports many different underlying providers, each with their
        own tool schema requirements and limitations. This method cleans tool
        schemas to ensure compatibility across all providers, particularly
        removing properties that cause issues with certain providers.
        
        The primary adaptation is removing 'additionalProperties' fields from
        tool schemas, which are not supported by some providers like Google
        Vertex AI. This cleaning is applied recursively to all nested objects
        in the tool specifications.
        
        Args:
            tools: List of tool objects to adapt
            model_string: Model string (used for future provider-specific adaptations)
            
        Returns:
            List[Tool]: Tools with schemas adapted for LiteLLM compatibility
            
        Note:
            The method modifies tool schemas in-place and also returns the
            tool list for consistency with the adapter interface. The cleaning
            is applied to various tool specification formats including TOOL_SPEC,
            _tool_spec, and function-level specifications.
            
        Example:
            Tool schema before adaptation::
            
                {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "additionalProperties": false}
                    },
                    "additionalProperties": false
                }
                
            Tool schema after adaptation::
            
                {
                    "type": "object", 
                    "properties": {
                        "name": {"type": "string"}
                    }
                }
        """
        logger.debug(f"LiteLLMAdapter.adapt_tools called with {len(tools) if tools else 0} tools, model_string='{model_string}'")
        
        # For LiteLLM, always clean additionalProperties regardless of underlying provider
        if tools:
            logger.debug("LiteLLM adapter: Cleaning tool schemas to remove 'additionalProperties'.")
            
            for tool in tools:
                if hasattr(tool, 'TOOL_SPEC'):
                    tool_name = getattr(tool, 'name', 'unnamed-tool')
                    logger.trace(f"Cleaning TOOL_SPEC for tool: {tool_name}")
                    recursively_remove(tool.TOOL_SPEC, "additionalProperties")
                elif hasattr(tool, '_tool_spec'):
                    tool_name = getattr(tool, 'name', 'unnamed-tool')
                    logger.trace(f"Cleaning _tool_spec for tool: {tool_name}")
                    recursively_remove(tool._tool_spec, "additionalProperties")
                else:
                    # Handle module-based tools
                    module_funcs = [name for name in dir(tool) if callable(getattr(tool, name))]
                    for func_name in module_funcs:
                        func = getattr(tool, func_name)
                        if hasattr(func, '_tool_spec'):
                            func_name_or_attr = getattr(func, 'name', func_name)
                            logger.trace(f"Cleaning _tool_spec for tool: {func_name_or_attr}")
                            recursively_remove(func._tool_spec, "additionalProperties")
        else:
            logger.debug("No tools to adapt")

        logger.debug(f"Tool adaptation completed, returning {len(tools) if tools else 0} tools")
        return tools