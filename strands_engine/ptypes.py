"""
Type definitions for strands_engine.

This module provides clean type definitions focused on the engine's core responsibilities:
- Message processing
- Tool configuration and loading (NOT execution)
- Framework adapters
- Session handling

Note: Tools are loaded and configured by the engine, but executed by strands-agents.
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

# Tool types - NOTE: Tools are loaded by engine but executed by strands-agents
class Tool(Protocol):
    """
    Protocol for tool objects that are loaded by the engine and passed to strands-agents.
    
    The engine is responsible ONLY for loading and configuring tools from config files.
    Tool execution is handled entirely by strands-agents - the engine never executes tools directly.
    """
    
    @property
    def name(self) -> str:
        """Tool name for identification."""
        ...

# Tool loading result types
@dataclass
class ToolCreationResult:
    """Result of tool creation from configuration."""
    tools: List[Tool]
    requested_functions: List[str]
    found_functions: List[str] 
    missing_functions: List[str]
    error: Optional[str] = None

# Framework adapter protocol
class FrameworkAdapter(Protocol):
    """
    Protocol for framework-specific adapters.
    
    Adapters are responsible for:
    - Adapting tool schemas for specific LLM providers
    - Preparing agent initialization arguments
    - Transforming content for framework compatibility
    """
    
    def adapt_tools(self, tools: List[Tool], model_string: str) -> List[Tool]:
        """
        Adapt tools for specific framework.
        
        This modifies tool schemas as needed for the LLM provider
        (e.g., removing unsupported properties).
        """
        ...
        
    def prepare_agent_args(
        self, 
        system_prompt: str,
        messages: List[Message],
        startup_files_content: Optional[List[Message]] = None,
        emulate_system_prompt: bool = False
    ) -> Dict[str, Any]:
        """
        Prepare arguments for strands-agents Agent initialization.
        
        This handles framework-specific agent configuration needs.
        """
        ...
        
    def transform_content(self, content: Any) -> Any:
        """Transform content for framework compatibility."""
        ...
        
    @property
    def expected_exceptions(self) -> Tuple[type[Exception], ...]:
        """Expected exception types for this framework."""
        ...