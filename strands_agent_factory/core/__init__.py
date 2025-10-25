"""
Core components for strands_agent_factory.

This package provides the fundamental building blocks for the strands_agent_factory
system, including configuration management, agent creation, framework adapters,
and error handling.

Key Components:
    - AgentFactory: Main factory for creating and managing agents
    - AgentProxy: Proxy for managing agent lifecycle and MCP clients
    - AgentFactoryConfig: Configuration dataclass for agent creation
    - Framework adapters: Integration with different AI providers
    - Exception hierarchy: Structured error handling across the system
    - Utilities: Common utility functions for data processing

The core module serves as the foundation for the entire strands_agent_factory
system, providing clean interfaces and robust error handling for agent
creation and management workflows.

Note: Tool-related types and configurations are exported from the tools module.
This module focuses on agent creation and framework integration.

Example:
    Basic usage of core components::
    
        from strands_agent_factory.core import (
            AgentFactory,
            AgentFactoryConfig
        )
        
        config = AgentFactoryConfig(
            model="gpt-4",
            tool_config_paths=["/path/to/tools/"]
        )
        
        factory = AgentFactory(config)
        await factory.initialize()
        
        with factory.create_agent() as agent:
            await agent.send_message_to_agent("Hello!")
"""

# Main factory and agent classes
from .factory import AgentFactory
from .agent import AgentProxy
from .config import AgentFactoryConfig

# Core type aliases (non-tool related)
from .types import (
    PathLike,
    Tool,
    FrameworkAdapter,
    Message,
    ToolDiscoveryResult,
)

# Exception hierarchy (from exceptions.py)
from .exceptions import (
    # Base exceptions
    FactoryError,
    ConfigurationError,
    ModelLoadError,
    ToolLoadError,
    AdapterError,
    SessionError,
    InitializationError,
    
    # Adapter-specific exceptions
    FrameworkNotSupportedError,
    ModelClassNotFoundError,
    ModelPropertyDetectionError,
    GenericAdapterCreationError,
    
    # Content processing exceptions
    ContentProcessingError,
    FileFormatError,
    FileAccessError,
    
    # Session management exceptions
    SessionBackupError,
    SessionActivationError,
    
    # Validation exceptions
    ValidationError,
    ModelStringFormatError,
    PathValidationError,
)

# Utility functions
from .utils import (
    clean_dict,
    print_structured_data,
)

__all__ = [
    # Main classes
    'AgentFactory',
    'AgentProxy',
    'AgentFactoryConfig',
    
    # Core type aliases (non-tool related)
    'PathLike',
    'Tool',
    'FrameworkAdapter',
    'Message',
    'ToolDiscoveryResult',
    
    # Base exceptions
    'FactoryError',
    'ConfigurationError',
    'ModelLoadError',
    'ToolLoadError',
    'AdapterError',
    'SessionError',
    'InitializationError',
    
    # Adapter-specific exceptions
    'FrameworkNotSupportedError',
    'ModelClassNotFoundError',
    'ModelPropertyDetectionError',
    'GenericAdapterCreationError',
    
    # Content processing exceptions
    'ContentProcessingError',
    'FileFormatError',
    'FileAccessError',
    
    # Session management exceptions
    'SessionBackupError',
    'SessionActivationError',
    
    # Validation exceptions
    'ValidationError',
    'ModelStringFormatError',
    'PathValidationError',
    
    # Utility functions
    'clean_dict',
    'print_structured_data',
]