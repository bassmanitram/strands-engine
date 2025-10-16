"""
Generic framework adapter for strands_agent_factory.

This module provides the GenericFrameworkAdapter class, which enables automatic
support for strands-agents providers using fully dynamic discovery and 
introspection, requiring no configuration registry.

The generic adapter achieves complete automation through:
- Dynamic module and class name derivation from framework ID
- Automatic model property detection via Config class introspection
- Direct client_args pass-through without extraction
- Pure import-based validation for framework support

This approach eliminates all configuration overhead while providing
automatic support for any strands-agents provider following standard patterns.
"""

import importlib
import inspect
from typing import Any, Dict, List, Optional, Set
from loguru import logger

from strands.models import Model

from .base import FrameworkAdapter
from ..core.types import Tool


class GenericFrameworkAdapter(FrameworkAdapter):
    """
    Fully dynamic adapter that automatically supports any strands-agents provider
    following standard patterns without requiring any configuration.
    
    This adapter achieves complete automation by:
    - Deriving module and class names from framework ID
    - Automatically detecting model property names via introspection
    - Passing client_args directly without extraction
    - Using pure import success for validation
    
    The adapter works with any framework following strands-agents conventions:
    - Module: strands.models.{framework}.{Framework}Model
    - Constructor: __init__(self, *, client_args=None, **model_config)
    - Config: Nested TypedDict with model property (usually model_id)
    
    Example:
        Automatic support for any framework::
        
            adapter = GenericFrameworkAdapter("gemini")
            model = adapter.load_model("gemini-2.5-flash", {
                "temperature": 0.7,
                "client_args": {"api_key": "key"}
            })
            
        Works with any framework::
        
            adapter = GenericFrameworkAdapter("newframework")
            # Automatically handles strands.models.newframework.NewframeworkModel
    """
    
    def __init__(self, framework_id: str):
        """
        Initialize dynamic adapter for any framework.
        
        Args:
            framework_id: The framework identifier (e.g., 'gemini', 'mistral')
            
        Raises:
            ValueError: If framework_id is invalid or empty
        """
        if not framework_id or not isinstance(framework_id, str):
            raise ValueError("framework_id must be a non-empty string")
            
        self.framework_id = framework_id.lower()
        self._model_class = None
        self._model_property = None
        
        logger.debug(f"Initialized GenericFrameworkAdapter for: {self.framework_id}")
    
    def _get_model_class_path(self) -> tuple[str, str]:
        """
        Derive module and class names from framework ID.
        
        Uses strands-agents naming conventions to automatically determine
        the correct module path and class name for any framework.
        
        Returns:
            Tuple of (module_path, class_name)
            
        Example:
            >>> adapter = GenericFrameworkAdapter("gemini")
            >>> adapter._get_model_class_path()
            ("strands.models.gemini", "GeminiModel")
        """
        module_path = f"strands.models.{self.framework_id}"
        class_name = f"{self.framework_id.capitalize()}Model"
        
        logger.debug(f"Derived paths: {module_path}.{class_name}")
        return module_path, class_name
    
    def _import_model_class(self):
        """
        Dynamically import the model class with caching.
        
        Returns:
            The imported strands model class
            
        Raises:
            ImportError: If the module cannot be imported
            AttributeError: If the class is not found in the module
        """
        if self._model_class is not None:
            return self._model_class
            
        module_path, class_name = self._get_model_class_path()
        logger.debug(f"Importing {class_name} from {module_path}")
        
        try:
            module = importlib.import_module(module_path)
            self._model_class = getattr(module, class_name)
            
            logger.debug(f"Successfully imported: {self._model_class}")
            return self._model_class
            
        except ImportError as e:
            logger.debug(f"Failed to import module {module_path}: {e}")
            raise
        except AttributeError as e:
            logger.debug(f"Failed to find class {class_name} in {module_path}: {e}")
            raise
    
    def _detect_model_property(self, model_class) -> str:
        """
        Automatically detect the model property name via introspection.
        
        Examines the model class's Config TypedDict to determine the
        correct property name for the model identifier.
        
        Args:
            model_class: The model class to inspect
            
        Returns:
            The detected model property name (defaults to 'model_id')
            
        Note:
            This method looks for nested Config classes with TypedDict
            annotations containing 'model_id' or 'model' properties.
        """
        if self._model_property is not None:
            return self._model_property
            
        try:
            # Look for nested Config class with annotations
            for attr_name in dir(model_class):
                attr = getattr(model_class, attr_name)
                if (isinstance(attr, type) and 
                    'Config' in attr_name and 
                    hasattr(attr, '__annotations__')):
                    
                    annotations = getattr(attr, '__annotations__', {})
                    
                    # Check for common model property names
                    for prop_name in ['model_id', 'model']:
                        if prop_name in annotations:
                            logger.debug(f"Detected model property: {prop_name} from {attr_name}")
                            self._model_property = prop_name
                            return prop_name
            
            # Fallback to most common default
            logger.debug("No model property detected, using default: model_id")
            self._model_property = 'model_id'
            return self._model_property
            
        except Exception as e:
            logger.debug(f"Error detecting model property: {e}")
            self._model_property = 'model_id'
            return self._model_property
    
    @property
    def framework_name(self) -> str:
        """
        Get the framework name for this adapter.
        
        Returns:
            str: Framework identifier for logging and debugging
        """
        return self.framework_id
    
    def load_model(self, model_name: Optional[str] = None, model_config: Optional[Dict[str, Any]] = None) -> Model:
        """
        Load a model using fully dynamic discovery and instantiation.
        
        This method achieves complete automation by:
        1. Dynamically importing the framework's model class
        2. Auto-detecting the model property name via introspection
        3. Setting the model identifier if provided
        4. Passing all configuration (including client_args) directly to constructor
        
        Args:
            model_name: Model identifier (optional if in model_config)
            model_config: Complete model configuration including client_args
            
        Returns:
            Configured strands Model instance
            
        Raises:
            ImportError: If the framework's model class cannot be imported
            RuntimeError: If model instantiation fails
            
        Example:
            Complete automation::
            
                config = {
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "client_args": {
                        "api_key": "your-key",
                        "timeout": 60
                    }
                }
                model = adapter.load_model("model-name", config)
                
        Note:
            The client_args are passed directly to the constructor without
            extraction, as all strands models accept this parameter.
        """
        logger.debug(f"Dynamic adapter loading model for {self.framework_id}")
        logger.debug(f"model_name: {model_name}, model_config: {model_config}")
        
        model_config = model_config or {}
        
        try:
            # 1. Dynamically import the model class
            model_class = self._import_model_class()
            
            # 2. Auto-detect the model property name
            model_property = self._detect_model_property(model_class)
            
            # 3. Set model identifier if provided
            if model_name:
                model_config[model_property] = model_name
                logger.debug(f"Set {model_property} = {model_name}")
            
            # 4. Pass everything directly to constructor (including client_args)
            # No need to extract client_args - strands models handle it automatically
            logger.debug(f"Creating {model_class.__name__} with config: {model_config}")
            
            model = model_class(**model_config)
            
            logger.debug(f"{model_class.__name__} created successfully")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model for framework {self.framework_id}: {e}")
            raise RuntimeError(f"Model loading failed for {self.framework_id}: {e}") from e
    
    def adapt_tools(self, tools: List[Tool], model_string: str) -> List[Tool]:
        """
        Adapt tools for framework compatibility.
        
        Uses the base class implementation by default. The dynamic nature
        of this adapter makes framework-specific tool adaptations difficult
        to implement generically.
        
        Args:
            tools: List of tool objects to adapt
            model_string: Model string for potential model-specific adaptations
            
        Returns:
            List[Tool]: Adapted tools (unchanged by default)
        """
        logger.trace(f"GenericFrameworkAdapter.adapt_tools called for {self.framework_id}")
        return super().adapt_tools(tools, model_string)


def can_handle_generically(framework_id: str) -> bool:
    """
    Check if a framework can be handled by the dynamic generic adapter.
    
    Uses pure import-based validation - if the strands model class can be
    imported successfully, the framework is fully supported with all dependencies.
    
    Args:
        framework_id: Framework identifier to check
        
    Returns:
        True if the framework can be handled generically, False otherwise
        
    Note:
        This validation approach is both simple and reliable: if strands
        support is installed for a framework, all necessary dependencies
        are automatically available.
    """
    if not framework_id or not isinstance(framework_id, str):
        logger.debug("Invalid framework_id provided")
        return False
        
    framework_id = framework_id.lower()
    
    # Known frameworks that require custom adapters
    REQUIRES_CUSTOM_ADAPTER: Set[str] = {
        'bedrock',  # Needs BotocoreConfig handling
        # Add other frameworks that need special treatment
    }
    
    if framework_id in REQUIRES_CUSTOM_ADAPTER:
        logger.debug(f"Framework {framework_id} requires custom adapter")
        return False
    
    try:
        # Create a test adapter to validate dynamic discovery
        test_adapter = GenericFrameworkAdapter(framework_id)
        
        # Try to import the model class - this validates:
        # 1. Framework follows strands naming conventions
        # 2. Strands support is installed with all dependencies  
        # 3. Model class exists and is importable
        model_class = test_adapter._import_model_class()
        
        # Verify it's actually a strands Model
        if not issubclass(model_class, Model):
            logger.debug(f"Class {model_class} is not a strands Model")
            return False
        
        # Additional validation: check if we can detect model property
        model_property = test_adapter._detect_model_property(model_class)
        if not model_property:
            logger.debug(f"Could not detect model property for {framework_id}")
            return False
        
        logger.debug(f"Framework {framework_id} can be handled generically")
        return True
        
    except Exception as e:
        logger.debug(f"Framework {framework_id} cannot be handled generically: {e}")
        return False


def create_generic_adapter(framework_id: str) -> Optional[GenericFrameworkAdapter]:
    """
    Create a dynamic generic adapter for any framework.
    
    Factory function that creates and validates a GenericFrameworkAdapter
    instance using fully dynamic discovery.
    
    Args:
        framework_id: Framework identifier
        
    Returns:
        GenericFrameworkAdapter instance or None if creation fails
        
    Example:
        >>> adapter = create_generic_adapter("gemini")
        >>> if adapter:
        ...     model = adapter.load_model("gemini-2.5-flash")
        ...     
        >>> adapter = create_generic_adapter("any_new_framework")
        >>> # Works automatically if strands support is installed
    """
    try:
        adapter = GenericFrameworkAdapter(framework_id)
        logger.info(f"Created dynamic generic adapter for framework: {framework_id}")
        return adapter
    except Exception as e:
        logger.error(f"Failed to create generic adapter for {framework_id}: {e}")
        return None