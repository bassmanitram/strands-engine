"""
Strands Agent Factory - Factory-based agent creation framework for strands-agents.

This package provides a configuration-driven factory pattern for creating and managing
strands-agents Agent instances. It serves as a clean abstraction layer that handles:

- Model configuration and loading across multiple AI frameworks
- Tool discovery, loading, and lifecycle management  
- Session persistence and conversation management
- Framework-specific adaptations

The factory is designed to be embedded in larger applications while maintaining
compatibility with strands-agents' core architecture patterns.

Core Components:
    - AgentFactoryConfig: Configuration dataclass for agent parameters
    - AgentFactory: Main factory class for creating configured agents

Example:
    Basic agent creation::

        from strands_agent_factory import AgentFactoryConfig, AgentFactory
        
        config = AgentFactoryConfig(
            model="gpt-4o",
            system_prompt="You are a helpful assistant."
        )
        
        factory = AgentFactory(config)
        await factory.initialize()
        agent = factory.create_agent()
"""
import nest_asyncio; 
nest_asyncio.apply()

from .core.config import AgentFactoryConfig
from .core.factory import AgentFactory  

__version__ = "0.1.0"

__all__ = [
    "AgentFactoryConfig",
    "AgentFactory",
]