"""
Base framework adapter for strands_agent_factory.

This module provides the abstract base class and loading infrastructure for
framework adapters that integrate strands_agent_factory with different AI providers
and frameworks. Framework adapters handle the specifics of model loading,
tool adaptation, and provider-specific configuration.

The adapter system allows strands_agent_factory to support multiple AI frameworks
through a common interface while handling the unique requirements of each provider.
It now features automatic support for standard frameworks through a fully dynamic
generic adapter system.

Components:
    - FrameworkAdapter: Abstract base class defining the adapter interface
    - load_framework_adapter: Factory function with 3-tier loading strategy
    - FRAMEWORK_HANDLERS: Registry for frameworks requiring special handling
    - Generic adapter support for automatic framework handling

Loading Strategy:
    1. Explicit adapters (priority): Custom implementations for special cases
    2. Generic adapters (automatic): Standard strands-agents providers
    3. Clear error reporting: Raise exceptions for unsupported frameworks

The adapters follow a consistent pattern for:
    - Model loading and configuration
    - Tool schema adaptation for provider compatibility
    - Message formatting and system prompt handling
    - Provider-specific initialization and cleanup

Generic Adapter System:
    The system now includes automatic support for strands-agents providers
    that follow standard patterns, significantly reducing maintenance overhead
    while providing unlimited framework support.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from strands.models import Model
from strands.types.content import Messages

from loguru import logger

from ..core.types import Tool
from ..core.exceptions import AdapterError, ConfigurationError
import importlib

# ============================================================================
# Framework Registry
# ============================================================================

FRAMEWORK_HANDLERS = {
    "litellm": "strands_agent_factory.adapters.litellm.LiteLLMAdapter",
    "bedrock": "strands_agent_factory.adapters.bedrock.BedrockAdapter",
    "ollama": "strands_agent_factory.adapters.ollama.OllamaAdapter"
}
"""
Registry mapping framework names to their explicit adapter class paths.

This registry contains frameworks that require custom adapter implementations
due to special requirements:
- litellm: Complex tool schema cleaning for multi-provider compatibility
- bedrock: BotocoreConfig handling + content adaptation + image validation
- ollama: Non-standard constructor with positional host parameter

Frameworks not in this registry (openai, anthropic, gemini, mistral, etc.)
are automatically handled by the generic adapter system if they follow
standard strands-agents patterns.

The generic adapter provides automatic support for any framework following
standard conventions:
- Module: strands.models.{framework}.{Framework}Model
- Constructor: __init__(self, *, client_args=None, **model_config)
- Config: TypedDict with model_id property
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
            str: Framework identifier (e.g., 'litellm', 'bedrock', 'ollama')
            
        Note:
            This name is used for logging, debugging, and framework selection.
            It should be unique and descriptive.
        """
        pass


    def adapt_tools(self, tools: List[Tool], model_string: str) -> List[Tool]:
        """
        Adapt tools for default compatibility.
        
        Args:
            tools: List of tool objects to adapt
            model_string: Model string for potential model-specific adaptations
            
        Returns:
            List[Tool]: Adapted Tools (unchanged by default)
            
        Note:
            Tool support varies significantly across different models.
            Some models may not support function calling at all, while others
            may have specific requirements for tool schemas. This method
            provides an extension point for model-specific adaptations.
        """
        if logger.level('TRACE').no >= logger._core.min_level:
            logger.trace("FrameworkAdapter.adapt_tools called with {} tools, model_string='{}'", len(tools) if tools else 0, model_string)
        
        # FrameworkAdapter tool support varies by model - for now, pass through unchanged
        if tools:
            logger.debug("FrameworkAdapter adapter: Tools passed through without modification")
            logger.debug("Note: Tool support varies across models. Model '{}' may have limited tool capabilities.", model_string)
        else:
            logger.debug("No tools to adapt")
        
        if logger.level('TRACE').no >= logger._core.min_level:
            logger.trace("Tool adaptation completed, returning {} tools", len(tools) if tools else 0)
        return tools
    
    def prepare_agent_args(
        self,
        system_prompt: Optional[str] = None,
        emulate_system_prompt: bool = False,
        messages: Optional[Messages] = None,
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
            emulate_system_prompt: Whether to emulate system prompt in first user message
            **kwargs: Additional arguments passed through to agent

        Returns:
            Dict[str, Any]: Dictionary of arguments for Agent constructor
            
        Note:
            System prompt emulation is used for frameworks that don't support
            system prompts natively. The prompt is prepended to the first user message.
        """
        if logger.level('TRACE').no >= logger._core.min_level:
            logger.trace("FrameworkAdapter.prepare_agent_args called with system_prompt={}, messages={}, emulate_system_prompt={}, kwargs={}", system_prompt is not None, len(messages) if messages else 0, emulate_system_prompt, list(kwargs.keys()))
        
        messages = self.adapt_content(messages) if messages else []
        
        # Handle system prompt emulation for frameworks that don't support it natively
        if emulate_system_prompt and system_prompt:
            logger.debug("Emulating system prompt by prepending to the first user message as requested.")
            messages.insert(0, {
                "role": "user",
                "content": [{"text": system_prompt}]
            })

            agent_args = {"system_prompt": None, "messages": messages}
            logger.debug("System prompt emulation applied")
        else:
            agent_args = {"system_prompt": system_prompt, "messages": messages}
            logger.debug("Using system prompt directly")

        # Add any additional kwargs
        agent_args.update(kwargs)
        
        logger.debug("prepare_agent_args returning keys: {}", list(agent_args.keys()))
        return agent_args

    def adapt_content(self, content: Messages) -> Messages:
        """
        Transform message content for the specific framework.
        
        Provides an extension point for frameworks that need to modify
        message content format or structure. The default implementation
        returns content unchanged.
        
        Args:
            content: Content to transform
            
        Returns:
            Messages: Transformed content (same type as input by default)
            
        Note:
            Override this method if your framework requires specific
            content transformations (e.g., format conversion, filtering).
        """
        logger.trace("FrameworkAdapter.adapt_content called with content type: {}", type(content))
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
        logger.trace("FrameworkAdapter.initialize called with model='{}', model_config={}", model, model_config)
        logger.debug("FrameworkAdapter.initialize: No initialization required, returning True")
        return True

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
# Framework Adapter Factory with Generic Support
# ============================================================================

def load_framework_adapter(adapter_name: str) -> FrameworkAdapter:
    """
    Load a framework adapter by name with automatic generic fallback.
    
    Enhanced factory function that dynamically loads framework adapters
    with support for automatic generic handling of standard strands-agents
    providers. The loading strategy is:
    
    1. **Explicit adapters** (highest priority): Use custom implementations
       from FRAMEWORK_HANDLERS for frameworks requiring special handling
    2. **Generic adapters** (automatic): Use generic implementation for
       frameworks following standard strands-agents patterns
    3. **Clear error reporting**: Raise AdapterError if no suitable adapter found
    
    This approach significantly reduces maintenance overhead while providing
    broader framework support and maintaining compatibility for special cases.
    
    Args:
        adapter_name: Name of the framework adapter to load
        
    Returns:
        FrameworkAdapter: Instantiated adapter
        
    Raises:
        ConfigurationError: If adapter_name is invalid
        AdapterError: If adapter cannot be loaded or framework is unsupported
        
    Example:
        Explicit adapter (custom implementation)::
        
            >>> adapter = load_framework_adapter("bedrock")  # Uses BedrockAdapter
            >>> adapter.framework_name
            "bedrock"
            
        Generic adapter (automatic support)::
        
            >>> adapter = load_framework_adapter("openai")   # Uses GenericFrameworkAdapter
            >>> adapter.framework_name
            "openai"
            
        Unsupported framework::
        
            >>> load_framework_adapter("nonexistent")
            AdapterError: No adapter available for framework: nonexistent
            
    Note:
        The function uses lazy importing to avoid loading framework
        dependencies unless they are actually needed. Generic adapters
        are only created if the framework follows standard patterns and
        has required dependencies available.
    """
    logger.debug("Loading framework adapter: {}", adapter_name)
    
    if not adapter_name or not isinstance(adapter_name, str):
        raise ConfigurationError(f"Invalid adapter name: {adapter_name}")
    
    # 1. Try explicit adapter first (highest priority)
    if adapter_name in FRAMEWORK_HANDLERS:
        logger.debug("Using explicit adapter for {}", adapter_name)
        try:
            return _load_explicit_adapter(adapter_name)
        except Exception as e:
            raise AdapterError(f"Failed to load explicit adapter for {adapter_name}") from e
    
    # 2. Try generic adapter (automatic support)
    logger.debug("Checking generic adapter support for {}", adapter_name)
    if _can_handle_generically(adapter_name):
        logger.debug("Using generic adapter for {}", adapter_name)
        try:
            return _create_generic_adapter(adapter_name)
        except Exception as e:
            raise AdapterError(f"Failed to create generic adapter for {adapter_name}") from e
    
    # 3. No suitable adapter found
    raise AdapterError(
        f"No adapter available for framework: {adapter_name}. "
        f"Supported explicit adapters: {list(FRAMEWORK_HANDLERS.keys())}. "
        f"Generic adapter support requires standard strands-agents patterns."
    )


def _load_explicit_adapter(adapter_name: str) -> FrameworkAdapter:
    """
    Load an explicit adapter from the FRAMEWORK_HANDLERS registry.
    
    Args:
        adapter_name: Framework name to load
        
    Returns:
        Instantiated explicit adapter
        
    Raises:
        AdapterError: If adapter loading fails
    """
    try:
        class_path = FRAMEWORK_HANDLERS[adapter_name]
        logger.debug("Found explicit adapter class path: {}", class_path)
        
        module_path, class_name = class_path.rsplit('.', 1)
        logger.debug("Importing module: {}, class: {}", module_path, class_name)
        
        module = importlib.import_module(module_path)
        adapter_class = getattr(module, class_name)
        adapter = adapter_class()
        
        logger.debug("Successfully created explicit adapter: {}", type(adapter).__name__)
        return adapter
        
    except Exception as e:
        raise AdapterError(f"Failed to load explicit adapter for {adapter_name}") from e


def _can_handle_generically(framework_id: str) -> bool:
    """
    Check if a framework can be handled by the generic adapter.
    
    This is a wrapper around the generic adapter's validation function
    to avoid importing the generic module unless needed.
    
    Args:
        framework_id: Framework identifier to check
        
    Returns:
        True if the framework can be handled generically
    """
    try:
        # Lazy import to avoid loading generic adapter unless needed
        from .generic import can_handle_generically
        return can_handle_generically(framework_id)
    except ImportError as e:
        logger.error(f"Generic adapter module not available: {e}")
        return False
    except Exception as e:
        logger.debug("Generic adapter validation failed for {}: {}", framework_id, e)
        return False


def _create_generic_adapter(framework_id: str) -> FrameworkAdapter:
    """
    Create a generic adapter for a framework.
    
    Args:
        framework_id: Framework identifier
        
    Returns:
        Generic adapter instance
        
    Raises:
        AdapterError: If generic adapter creation fails
    """
    try:
        # Lazy import to avoid loading generic adapter unless needed
        from .generic import create_generic_adapter
        adapter = create_generic_adapter(framework_id)
        if not adapter:
            raise AdapterError(f"Generic adapter creation returned None for {framework_id}")
        return adapter
    except ImportError as e:
        raise AdapterError(f"Generic adapter module not available: {e}") from e
    except Exception as e:
        raise AdapterError(f"Failed to create generic adapter for {framework_id}") from e