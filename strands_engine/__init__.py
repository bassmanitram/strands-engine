"""
Strands Engine - A conversational AI engine built on strands-agents.

Provides tool loading, conversation management, session management, 
and multi-framework support for building conversational AI applications.
"""

from .engine import Engine
from .config import EngineConfig
from .session import DelegatingSession
from .tools import ToolFactory, ToolAdapter, discover_tool_configs

__version__ = "0.1.0"

__all__ = [
    "Engine",
    "EngineConfig", 
    "DelegatingSession",
    "ToolFactory",
    "ToolAdapter",
    "discover_tool_configs"
]