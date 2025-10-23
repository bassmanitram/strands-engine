"""
Generic Framework Adapter for Dynamic Framework Support

This module provides automatic adapter support for any framework that follows
standard strands-agents patterns. It uses dynamic discovery to detect and
support frameworks without requiring explicit adapter implementations.

Key Features:
- Automatic framework detection via import validation
- Dynamic model class discovery using naming conventions  
- Flexible model property detection (model_id, model, model_name, etc.)
- Zero-configuration support for standard frameworks

The generic adapter works by:
1. Attempting to import the framework's strands model class
2. Detecting the model configuration property name
3. Creating and configuring the model dynamically

This approach provides broad framework compatibility while maintaining
the flexibility to add custom adapters for frameworks with special requirements.
"""

import importlib
from typing import Any, Dict, Optional, Set

from loguru import logger
from strands.models import Model

from strands_agent_factory.adapters.base import FrameworkAdapter


class GenericFrameworkAdapter(FrameworkAdapter):
    """
    Generic adapter that provides automatic support for any framework following
    standard strands-agents patterns.
    
    This adapter uses dynamic discovery to:
    - Import the framework's strands model class
    - Detect the model configuration property
    - Create and configure models automatically
    
    Works with any framework that:
    - Has strands model support in strands.models.{framework}
    - Follows standard naming: strands.models.{framework}.{Framework}Model
    - Uses standard model properties (model_id, model, model_name, etc.)
    
    Examples:
        >>> adapter = GenericFrameworkAdapter("gemini")
        >>> model = adapter.load_model("gemini-2.5-flash")
        
        >>> adapter = GenericFrameworkAdapter("anthropic") 
        >>> model = adapter.load_model("claude-3-5-sonnet-20241022")
    """
    
    def __init__(self, framework_id: str):
        """
        Initialize the generic adapter for a specific framework.
        
        Args:
            framework_id: Framework identifier (e.g., "gemini", "anthropic")
            
        Raises:
            ImportError: If the framework's strands support is not installed
            AttributeError: If the model class cannot be found
        """
        self._framework_id = framework_id
        self._model_class = None
        self._model_property = None
        
        # Perform dynamic discovery during initialization
        self._model_class = self._import_model_class()
        self._model_property = self._detect_model_property(self._model_class)
        
        logger.debug("Initialized GenericFrameworkAdapter for: {}", self._framework_id)
    
    @property
    def framework_name(self) -> str:
        """
        Get the name of this framework.
        
        Returns:
            str: Framework identifier
        """
        return self._framework_id
    
    def _derive_import_paths(self) -> tuple[str, list[str]]:
        """
        Derive the module path and possible class names for the framework.
        
        Uses standard strands naming conventions with variations:
        - Module: strands.models.{framework}
        - Class variations: 
          1. {Framework}Model (e.g., "GeminiModel")
          2. {FrameworkCamelCase}Model (e.g., "LlamaCppModel" for "llamacpp")
        
        Returns:
            Tuple of (module_path, list_of_possible_class_names)
            
        Examples:
            >>> adapter._derive_import_paths()  # framework_id = "gemini"
            ("strands.models.gemini", ["GeminiModel"])
            >>> adapter._derive_import_paths()  # framework_id = "llamacpp"  
            ("strands.models.llamacpp", ["LlamacppModel", "LlamaCppModel"])
        """
        module_path = f"strands.models.{self._framework_id}"
        
        # Generate possible class name variations
        class_names = []
        
        # Standard pattern: {Framework}Model
        standard_name = f"{self._framework_id.capitalize()}Model"
        class_names.append(standard_name)
        
        # Handle special cases with compound names (e.g., llamacpp -> LlamaCppModel)
        if 'cpp' in self._framework_id:
            # Handle cases like "llamacpp" -> "LlamaCppModel"
            parts = self._framework_id.split('cpp')
            if len(parts) == 2:
                camel_case = f"{parts[0].capitalize()}Cpp{parts[1].capitalize()}Model"
                class_names.append(camel_case)
        
        # Handle other compound patterns as needed
        # Add more patterns here if discovered
        
        logger.debug("Derived paths: {} with class names: {}", module_path, class_names)
        return module_path, class_names
    
    def _import_model_class(self):
        """
        Dynamically import the framework's strands model class.
        
        Returns:
            The imported model class
            
        Raises:
            ImportError: If the module cannot be imported
            AttributeError: If the class cannot be found in the module
        """
        module_path, class_names = self._derive_import_paths()
        
        try:
            logger.debug("Importing from {}", module_path)
            module = importlib.import_module(module_path)
            
            # Try each possible class name
            for class_name in class_names:
                if hasattr(module, class_name):
                    self._model_class = getattr(module, class_name)
                    logger.debug("Successfully imported: {} as {}", class_name, self._model_class)
                    return self._model_class
            
            # If no class found, raise error
            raise AttributeError(f"None of the expected classes {class_names} found in {module_path}")
                
        except ImportError as e:
            logger.debug("Failed to import module {}: {}", module_path, e)
            raise ImportError(f"Could not import {module_path}. Framework {self._framework_id} may not be supported in strands.models or dependencies missing") from e
        except AttributeError as e:
            logger.debug("Failed to find classes {} in {}: {}", class_names, module_path, e)
            raise
    
    def _detect_model_property(self, model_class) -> str:
        """
        Detect the model configuration property name for the framework.
        
        Searches for common model property names in order of preference:
        1. model_id (most common)
        2. model 
        3. model_name
        4. name
        
        Args:
            model_class: The imported model class to inspect
            
        Returns:
            The detected property name, defaults to "model_id" if none found
        """
        # Common model property names in order of preference
        COMMON_MODEL_PROPERTIES = [
            "model_id",
            "model", 
            "model_name",
            "name"
        ]
        
        try:
            # Check class annotations first (most reliable)
            if hasattr(model_class, '__annotations__'):
                for prop_name in COMMON_MODEL_PROPERTIES:
                    if prop_name in model_class.__annotations__:
                        logger.debug("Detected model property: {} from annotations", prop_name)
                        return prop_name
            
            # Check nested config class annotations (common pattern in strands)
            for attr_name in dir(model_class):
                if attr_name.endswith('Config') and not attr_name.startswith('_'):
                    config_class = getattr(model_class, attr_name)
                    if hasattr(config_class, '__annotations__'):
                        for prop_name in COMMON_MODEL_PROPERTIES:
                            if prop_name in config_class.__annotations__:
                                logger.debug("Detected model property: {} from {}", prop_name, attr_name)
                                return prop_name
            
            # Check class attributes as fallback
            for prop_name in COMMON_MODEL_PROPERTIES:
                for attr_name in dir(model_class):
                    if attr_name == prop_name and not attr_name.startswith('_'):
                        if hasattr(model_class, attr_name):
                            logger.debug("Detected model property: {} from {}", prop_name, attr_name)
                            return prop_name
            
            # Default fallback
            logger.debug("No model property detected, using default: model_id")
            return "model_id"
            
        except Exception as e:
            logger.debug("Error detecting model property: {}", e)
            return "model_id"
    
    def load_model(self, model_name: str, model_config: Optional[Dict[str, Any]] = None):
        """
        Load and configure a model for the framework.
        
        Uses dynamic discovery to:
        1. Create the model configuration with the detected property name
        2. Instantiate the model class with the configuration
        
        Args:
            model_name: Name/identifier of the model to load
            model_config: Optional additional configuration parameters
            
        Returns:
            Configured model instance ready for use
            
        Example:
            >>> adapter = GenericFrameworkAdapter("gemini")
            >>> model = adapter.load_model("gemini-2.5-flash", {"temperature": 0.7})
        """
        if not self._model_class:
            raise RuntimeError("Model class not available. Adapter may not be properly initialized.")
        
        if not self._model_property:
            raise RuntimeError("Model property not detected. Adapter may not be properly initialized.")
        
        # Prepare model configuration
        model_config = model_config or {}
        
        logger.debug("Dynamic adapter loading model for {}", self._framework_id)
        logger.debug("model_name: {}, model_config: {}", model_name, model_config)
        
        # Set the model identifier using the detected property name
        if self._model_property not in model_config:
            model_config[self._model_property] = model_name
            
        # Handle special case where model_name is provided but property is different
        if self._model_property != "model_name" and "model_name" in model_config:
            if self._model_property not in model_config:
                logger.debug("Set {} = {}", self._model_property, model_name)
                model_config[self._model_property] = model_config["model_name"]
        
        try:
            logger.debug("Creating {} with config: {}", self._model_class.__name__, model_config)
            model = self._model_class(**model_config)
            
            logger.debug("{} created successfully", self._model_class.__name__)
            return model
            
        except Exception as e:
            raise RuntimeError(f"Failed to create {self._model_class.__name__} with config {model_config}") from e


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
        logger.debug("Framework {} requires custom adapter", framework_id)
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
            logger.debug("Class {} is not a strands Model", model_class)
            return False
        
        # Additional validation: check if we can detect model property
        model_property = test_adapter._detect_model_property(model_class)
        if not model_property:
            logger.debug("Could not detect model property for {}", framework_id)
            return False
        
        logger.debug("Framework {} can be handled generically", framework_id)
        return True
        
    except Exception as e:
        logger.debug("Framework {} cannot be handled generically: {}", framework_id, e)
        return False


def create_generic_adapter(framework_id: str) -> Optional[GenericFrameworkAdapter]:
    """
    Create a dynamic generic adapter for any framework.
    
    This function provides a safe way to create generic adapters with
    proper error handling and logging.
    
    Args:
        framework_id: Framework identifier to create adapter for
        
    Returns:
        GenericFrameworkAdapter instance if successful, None if failed
        
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
        logger.info("Created dynamic generic adapter for framework: {}", framework_id)
        return adapter
    except Exception as e:
        logger.error(f"Failed to create generic adapter for {framework_id}: {e}")
        return None