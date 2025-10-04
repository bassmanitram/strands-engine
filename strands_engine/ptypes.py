"""
Type definitions for strands_engine.

Provides common types used throughout the engine while maintaining
compatibility with strands-agents and wrapper applications.
"""

from typing import Any, Dict, List, Optional, Union, Protocol, runtime_checkable, NamedTuple
from typing_extensions import TypedDict
from pathlib import Path

# Common type aliases
PathLike = Union[str, Path]
JSONDict = Dict[str, Any]

# Message type for conversation content
class Message(TypedDict):
    """Standard message format for conversations."""
    role: str  # "user", "assistant", "system"
    content: str

# Tool configuration types (what engine manages)

class BaseToolConfig(TypedDict):
    """Base tool configuration that engine manages."""
    id: str
    type: str  # "mcp" or "python"
    disabled: bool

class MCPToolConfig(BaseToolConfig):
    """MCP tool configuration - engine only manages connection details."""
    # For stdio transport
    command: Optional[str]
    args: Optional[List[str]]
    env: Optional[Dict[str, str]]
    # For HTTP transport
    url: Optional[str]
    # Optional functions filter
    functions: Optional[List[str]]

class PythonToolConfig(BaseToolConfig):
    """Python tool configuration - engine only manages module loading."""
    module_path: str
    functions: List[str]
    package_path: Optional[str]
    source_file: Optional[str]  # Set by discovery process

# Union of all tool config types
ToolConfig = Union[MCPToolConfig, PythonToolConfig]

# Protocol for tool objects (what strands-agents provides)
@runtime_checkable
class Tool(Protocol):
    """
    Protocol for tool objects that strands-agents provides.
    Engine doesn't need to know implementation details.
    """
    pass

# Tool creation result
class ToolCreationResult(NamedTuple):
    """Detailed result of tool creation with missing function tracking."""
    tools: List[Any]
    requested_functions: List[str]  # Functions that were requested
    found_functions: List[str]      # Functions that were actually found
    missing_functions: List[str]    # Functions that were requested but not found
    error: Optional[str]

# Tool discovery result
class ToolDiscoveryResult(NamedTuple):
    """Result of tool configuration discovery."""
    successful_configs: List[ToolConfig]
    failed_configs: List[Dict[str, Any]]
    total_files_scanned: int

# Framework adapter protocol
@runtime_checkable
class FrameworkAdapter(Protocol):
    """Protocol for framework-specific adapters."""
    
    def adapt_tools(self, tools: List[Tool]) -> List[Tool]:
        """Adapt tools for the specific framework."""
        ...
    
    def prepare_agent_args(self, 
                          system_prompt: Optional[str] = None,
                          messages: Optional[List[Message]] = None,
                          **kwargs) -> Dict[str, Any]:
        """Prepare arguments for Agent initialization."""
        ...

# File content types for uploads
class FileContent(NamedTuple):
    """Processed file content."""
    path: Path
    content: str
    mimetype: Optional[str]
    metadata: Dict[str, Any]