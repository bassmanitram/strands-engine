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