"""
strands_engine - A clean engine interface for AI agents.

This package provides a simplified interface for creating AI agents using strands-agents,
extracted from YACBA's core functionality.
"""

from .config import EngineConfig
from .engine import AgentFactory  
from .framework import ModelLoader, FrameworkAdapter, DefaultAdapter, LiteLLMAdapter, BedrockAdapter, OllamaAdapter

__version__ = "0.1.0"

__all__ = [
    "EngineConfig",
    "AgentFactory",
    "ModelLoader",
    "FrameworkAdapter", 
    "DefaultAdapter",
    "LiteLLMAdapter",
    "BedrockAdapter",
    "OllamaAdapter"
]