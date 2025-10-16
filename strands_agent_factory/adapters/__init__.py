"""
Framework adapters for strands_agent_factory.

This module provides adapters that bridge strands_agent_factory with various
AI frameworks and providers. The adapter system supports both explicit
adapters for complex cases and generic adapters for standard frameworks.

Available Adapters:
    - Explicit adapters: Custom implementations for special requirements
    - Generic adapter: Automatic support for standard strands-agents providers

Key Components:
    - FrameworkAdapter: Base class for all adapters
    - load_framework_adapter: Factory function with automatic fallback
    - GenericFrameworkAdapter: Automatic support for standard frameworks

Usage:
    >>> from strands_agent_factory.adapters import load_framework_adapter
    >>> 
    >>> # Load any supported framework
    >>> adapter = load_framework_adapter("gemini")
    >>> model = adapter.load_model("gemini-2.5-flash")
"""

# Core adapter infrastructure
from .base import (
    FrameworkAdapter,
    load_framework_adapter,
    FRAMEWORK_HANDLERS
)

# Generic adapter for automatic framework support
from .generic import (
    GenericFrameworkAdapter,
    can_handle_generically,
    create_generic_adapter
)

__all__ = [
    # Base classes and factory
    'FrameworkAdapter',
    'load_framework_adapter', 
    'FRAMEWORK_HANDLERS',
    
    # Generic adapter system
    'GenericFrameworkAdapter',
    'can_handle_generically',
    'create_generic_adapter'
]