"""
Base framework adapter for strands_agent_factory.

This module provides the abstract base class and loading infrastructure for
framework adapters that integrate strands_agent_factory with different AI providers
and frameworks. Framework adapters handle the specifics of model loading,
tool adaptation, and provider-specific configuration.

The adapter system allows strands_agent_factory to support multiple AI frameworks
(OpenAI, Anthropic, Ollama, Bedrock, etc.) through a common interface while
handling the unique requirements of each provider.

Components:
    - FrameworkAdapter: Abstract base class defining the adapter interface
    - load_framework_adapter: Factory function for loading specific adapters
    - FRAMEWORK_HANDLERS: Registry mapping framework names to adapter classes

The adapters follow a consistent pattern for:
    - Model loading and configuration
    - Tool schema adaptation for provider compatibility
    - Message formatting and system prompt handling
    - Provider-specific initialization and cleanup
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from strands.models import Model

from loguru import logger

from ..ptypes import Tool, Message
import importlib

# ============================================================================
# Framework Registry
# ============================================================================

FRAMEWORK_HANDLERS = {
    "litellm": "strands_agent_factory.framework.litellm_adapter.LiteLLMAdapter",
    "openai":  "strands_agent_factory.framework.openai_adapter.OpenAIAdapter",
    "anthropic": "strands_agent_factory.framework.anthropic_adapter.AnthropicAdapter",
    "bedrock": "strands_agent_factory.framework.bedrock_adapter.BedrockAdapter",
    "ollama": "strands_agent_factory.framework.ollama_adapter.OllamaAdapter"
}
"""
Registry mapping framework names to their adapter class paths.

This registry enables dynamic loading of framework adapters based on
model string prefixes or explicit framework selection. Each entry
maps a framework identifier to its fully qualified class path.
"""


# ============================================================================
# Base Framework Adapter
# ============================================================================

class FrameworkAdapter(ABC):
    """
    Abstract base class for framework adapters.
    
    Framework adapters provide a standardized interface for integrating
    strands_agent_factory with different AI providers and frameworks. Each adapter
    handles the specifics of its target framework while presenting a common
    interface to the factory.
    
    Adapters are responsible for:
    - Loading models using framework-specific APIs
    - Adapting tool schemas for provider compatibility
    - Formatting messages and handling system prompts
    - Managing provider-specific initialization and configuration
    
    Subclasses must implement all abstract methods and may override
    optional methods to provide framework-specific behavior.
    
    Example:
        Creating a custom adapter::
        
            class MyFrameworkAdapter(FrameworkAdapter):
                @property
                def framework_name(self) -> str:
                    return "myframework"
                    
                def load_model(self, model_name, model_config):
                    # Implementation specific to MyFramework
                    pass
    """

    @property
    @abstractmethod
    def framework_name(self) -> str:
        """
        Get the name of this framework.
        
        Returns:
            str: Framework identifier (e.g., 'litellm', 'anthropic', 'ollama')
            
        Note:
            This name is used for logging, debugging, and framework selection.
            It should be unique and descriptive.
        """
        pass

    @abstractmethod
    def adapt_tools(self, tools: List[Tool], model_string: str) -> List[Tool]:
        """
        Adapt tools for the specific framework.
        
        Different frameworks may require different tool formats, schema
        modifications, or capability filtering. This method handles those
        transformations while preserving tool functionality.
        
        Common adaptations include:
        - Removing unsupported schema properties
        - Converting between different tool specification formats
        - Filtering tools based on model capabilities
        - Adding framework-specific metadata
        
        Args:
            tools: List of tool objects loaded by the factory
            model_string: Model string to determine adaptations needed
            
        Returns:
            List[Tool]: List of framework-adapted tool objects
            
        Note:
            Tools are loaded by the factory but executed by strands-agents.
            This method only modifies tool metadata and schemas.
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
        Prepare arguments for the Agent constructor.
        
        Handles message preparation and system prompt processing according to
        framework requirements and compatibility needs. This method provides
        a default implementation that works for most frameworks.
        
        The method handles:
        - Combining startup files with existing messages
        - System prompt emulation for frameworks that don't support it natively
        - Message format validation and conversion
        - Framework-specific argument preparation
        
        Args:
            system_prompt: System prompt to use (optional)
            messages: Existing message history (optional)
            startup_files_content: Optional startup file messages
            emulate_system_prompt: Whether to emulate system prompt in first user message
            **kwargs: Additional arguments passed through to agent

        Returns:
            Dict[str, Any]: Dictionary of arguments for Agent constructor
            
        Note:
            System prompt emulation is used for frameworks that don't support
            system prompts natively. The prompt is prepended to the first user message.
        """
        logger.debug(f"FrameworkAdapter.prepare_agent_args called with system_prompt={system_prompt is not None}, messages={len(messages) if messages else 0}, startup_files_content={len(startup_files_content) if startup_files_content else 0}, emulate_system_prompt={emulate_system_prompt}, kwargs={list(kwargs.keys())}")
        
        messages = messages or []
        
        # Combine startup files with existing messages
        if startup_files_content:
            messages = startup_files_content + messages
            logger.debug(f"Combined startup files with messages, total messages: {len(messages)}")

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
                    new_content = f"{system_prompt}\\n\\n{current_content}"
                    messages[first_user_msg_index]["content"] = new_content
            else:
                messages.insert(0, {
                    "role": "user",
                    "content": [{"type": "text", "text": system_prompt}]
                })

            agent_args = {"system_prompt": None, "messages": messages}
            logger.debug("System prompt emulation applied")
        else:
            agent_args = {"system_prompt": system_prompt, "messages": messages}
            logger.debug("Using system prompt directly")

        # Add any additional kwargs
        agent_args.update(kwargs)
        
        logger.debug(f"prepare_agent_args returning keys: {list(agent_args.keys())}")
        return agent_args

    def transform_content(self, content: Any) -> Any:
        """
        Transform message content for the specific framework.
        
        Provides an extension point for frameworks that need to modify
        message content format or structure. The default implementation
        returns content unchanged.
        
        Args:
            content: Content to transform
            
        Returns:
            Any: Transformed content (same type as input by default)
            
        Note:
            Override this method if your framework requires specific
            content transformations (e.g., format conversion, filtering).
        """
        logger.debug(f"FrameworkAdapter.transform_content called with content type: {type(content)}")
        return content

    # ========================================================================
    # Optional Framework Methods
    # ========================================================================

    async def initialize(self, model: str, model_config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Initialize the framework adapter.
        
        Performs any async initialization required by the framework,
        such as authentication, connection setup, or resource allocation.
        The default implementation returns True (no initialization needed).
        
        Args:
            model: Model identifier
            model_config: Optional model-specific configuration
            
        Returns:
            bool: True if initialization successful, False otherwise
            
        Note:
            Override this method if your framework requires async setup.
            Called during factory initialization before model loading.
        """
        logger.debug(f"FrameworkAdapter.initialize called with model='{model}', model_config={model_config}")
        return True

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns metadata about the currently loaded model for debugging
        and logging purposes. The default implementation returns minimal
        framework information.
        
        Returns:
            Dict[str, Any]: Dictionary with model information
            
        Example:
            >>> adapter.get_model_info()
            {"framework": "openai", "model": "gpt-4o", "provider": "openai"}
        """
        logger.debug("FrameworkAdapter.get_model_info called")
        return {"framework": self.framework_name}
    
    @abstractmethod
    def load_model(self, 
                   model_name: Optional[str] = None, 
                   model_config: Optional[Dict[str, Any]] = None) -> Model:
        """
        Load a strands-agents model using the appropriate framework.
        
        This method is the core of the framework adapter, responsible for
        creating a strands-agents Model instance that can be used by the
        Agent. It must handle framework-specific model loading, configuration,
        and initialization.
        
        The method should:
        - Parse the model name/identifier appropriately
        - Apply any model-specific configuration
        - Create and configure the strands Model instance
        - Handle authentication and connection setup
        - Provide appropriate error handling and logging
        
        Args:
            model_name: Model identifier string (optional if configured elsewhere)
            model_config: Framework-specific model configuration (optional)
            
        Returns:
            Model: Configured strands-agents Model instance
            
        Raises:
            ValueError: If model identifier is invalid or unsupported
            RuntimeError: If model loading fails
            
        Example:
            >>> model = adapter.load_model("gpt-4o", {"temperature": 0.7})
            >>> isinstance(model, strands.models.Model)
            True
        """
        pass


# ============================================================================
# Framework Adapter Factory
# ============================================================================

def load_framework_adapter(adapter_name: str) -> Optional[FrameworkAdapter]:
    """
    Load a framework adapter by name.
    
    Factory function that dynamically loads and instantiates framework
    adapters based on their registered names. Handles the complexity of
    module importing and class instantiation.
    
    Args:
        adapter_name: Name of the adapter to load (must be in FRAMEWORK_HANDLERS)
        
    Returns:
        Optional[FrameworkAdapter]: Instantiated adapter, or None if loading fails
        
    Raises:
        ImportError: If the adapter module cannot be imported
        AttributeError: If the adapter class is not found in the module
        
    Example:
        >>> adapter = load_framework_adapter("openai")
        >>> print(adapter.framework_name)
        "openai"
        
    Note:
        The function uses dynamic importing to avoid loading all framework
        dependencies unless they are actually needed.
    """
    logger.debug(f"load_framework_adapter called with adapter_name: '{adapter_name}'")
    
    class_path = FRAMEWORK_HANDLERS.get(adapter_name)
    if class_path:
        logger.debug(f"Found adapter class path: {class_path}")
        module_path, class_name = class_path.rsplit('.', 1)
        logger.debug(f"Importing module: {module_path}, class: {class_name}")
        module = importlib.import_module(module_path)
        adapter_class = getattr(module, class_name)
        adapter = adapter_class()
        logger.debug(f"Successfully created adapter: {type(adapter).__name__}")
        return adapter
    else:
        logger.error(f"No adapter found for: {adapter_name}")
        return None