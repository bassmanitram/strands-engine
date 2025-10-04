"""
Type definitions for strands_engine.

This module provides clean type definitions focused on the engine's core responsibilities:
- Message processing
- Tool management  
- Framework adapters
- Session handling
"""

from typing import Any, Dict, List, Optional, Protocol, Tuple, Union
from pathlib import Path
from dataclasses import dataclass


# Basic types
JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONDict = Dict[str, JSONValue]
PathLike = Union[str, Path]

# Message content types
@dataclass
class TextBlock:
    """Text content block."""
    type: str = "text"
    text: str = ""

@dataclass  
class ImageBlock:
    """Image content block."""
    type: str = "image"
    source: Dict[str, Any] = None

ContentBlock = Union[TextBlock, ImageBlock, Dict[str, Any]]
MessageContent = Union[str, List[ContentBlock]]

@dataclass
class Message:
    """Conversation message."""
    role: str
    content: MessageContent
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# Tool types
class Tool(Protocol):
    """Protocol for tool objects."""
    
    @property
    def name(self) -> str:
        """Tool name."""
        ...
        
    def execute(self, *args, **kwargs) -> Any:
        """Execute the tool."""
        ...

# Framework adapter protocol
class FrameworkAdapter(Protocol):
    """Protocol for framework-specific adapters."""
    
    def adapt_tools(self, tools: List[Tool], model_string: str) -> List[Tool]:
        """Adapt tools for specific framework."""
        ...
        
    def prepare_agent_args(
        self, 
        system_prompt: str,
        messages: List[Message],
        startup_files_content: Optional[List[Message]] = None,
        emulate_system_prompt: bool = False
    ) -> Dict[str, Any]:
        """Prepare arguments for agent initialization."""
        ...
        
    def transform_content(self, content: Any) -> Any:
        """Transform content for framework."""
        ...