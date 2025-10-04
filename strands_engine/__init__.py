"""
Strands Engine - A conversational AI engine built on strands-agents.

This package provides a focused engine for orchestrating LLM interactions
with tools, session management, and multi-framework support.

Main entry points:
- Engine: Core conversation orchestration engine
- EngineConfig: Configuration object for engine setup
"""

from .engine import Engine
from .config import EngineConfig
from .types import Message, Tool, FrameworkAdapter

__version__ = "0.1.0"
__all__ = [
    # Core engine
    "Engine",
    "EngineConfig",
    
    # Common types
    "Message",
    "Tool", 
    "FrameworkAdapter",
]