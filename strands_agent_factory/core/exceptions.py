"""
Exception hierarchy for strands_agent_factory.

This module defines the exception classes used throughout the strands_agent_factory
package to provide consistent error handling and reporting.
"""


class FactoryError(Exception):
    """Base exception for factory operations."""
    pass


class ConfigurationError(FactoryError):
    """Configuration is invalid or incomplete."""
    pass


class ModelLoadError(FactoryError):
    """Model loading failed."""
    pass


class ToolLoadError(FactoryError):
    """Tool loading failed."""
    pass


class AdapterError(FactoryError):
    """Framework adapter operation failed."""
    pass


class SessionError(FactoryError):
    """Session operation failed."""
    pass


class InitializationError(FactoryError):
    """Factory initialization failed."""
    pass


# ============================================================================
# Specific Adapter Exceptions (for replacing broad Exception catching)
# ============================================================================

class FrameworkNotSupportedError(AdapterError):
    """Framework is not supported or dependencies are missing."""
    pass


class ModelClassNotFoundError(AdapterError):
    """Expected model class not found in framework module."""
    pass


class ModelPropertyDetectionError(AdapterError):
    """Could not detect model configuration property."""
    pass


class GenericAdapterCreationError(AdapterError):
    """Generic adapter creation failed."""
    pass


# ============================================================================
# Content Processing Exceptions
# ============================================================================

class ContentProcessingError(FactoryError):
    """Base exception for content processing operations."""
    pass


class FileFormatError(ContentProcessingError):
    """File format is not supported or invalid."""
    pass


class FileAccessError(ContentProcessingError):
    """File cannot be accessed or read."""
    pass


# ============================================================================
# Session Management Exceptions  
# ============================================================================

class SessionBackupError(SessionError):
    """Session backup operation failed."""
    pass


class SessionActivationError(SessionError):
    """Session activation failed."""
    pass


# ============================================================================
# Validation Exceptions
# ============================================================================

class ValidationError(FactoryError):
    """Input validation failed."""
    pass


class ModelStringFormatError(ValidationError):
    """Model string format is invalid."""
    pass


class PathValidationError(ValidationError):
    """Path validation failed."""
    pass