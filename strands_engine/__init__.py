"""
Strands Engine - A conversational AI engine built on strands-agents.

This package provides a focused engine for orchestrating LLM interactions
with tool loading, session management, and multi-framework support.

Key Architecture:
- Engine loads and configures tools (strands-agents executes them)
- Engine processes files and manages sessions
- Engine creates and coordinates strands-agents Agent
- Agent handles all tool execution and LLM communication

Main entry points:
- Engine: Core conversation orchestration engine
- EngineConfig: Configuration object for engine setup
"""

from .engine import Engine
from .config import EngineConfig
from .ptypes import Message, Tool, FrameworkAdapter, ToolCreationResult

__version__ = "0.1.0"
__all__ = [
    # Core engine
    "Engine",
    "EngineConfig",
    
    # Common types
    "Message",
    "Tool", 
    "FrameworkAdapter",
    "ToolCreationResult",
]