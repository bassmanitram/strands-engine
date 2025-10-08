"""
Type definitions and protocols for strands_agent_factory.

This module provides the core type definitions, protocols, and data structures used
throughout the strands_agent_factory package. It defines interfaces for tools, framework
adapters, and configuration objects while maintaining compatibility with strands-agents.

The types are organized into several categories:
- Common type aliases for paths and JSON data
- Message and conversation types
- Tool configuration and discovery types  
- Framework adapter protocols
- File content handling types
- Tool specification types for runtime handling

These types provide strong typing support and clear contracts between components
while allowing flexibility in implementation details.
"""

from typing import Any, Dict, List, Optional, Union, Protocol, runtime_checkable, NamedTuple
from typing_extensions import TypedDict
from pathlib import Path

# ============================================================================
# Common Type Aliases
# ============================================================================

PathLike = Union[str, Path]
"""Type alias for filesystem paths - accepts strings or Path objects."""

JSONDict = Dict[str, Any]
"""Type alias for JSON-like dictionary structures."""


# ============================================================================
# Message and Conversation Types
# ============================================================================

class Message(TypedDict):
    """
    Standard message format for agent conversations.
    
    Represents a single message in a conversation thread with role-based
    content structure compatible with strands-agents message format.
    
    Attributes:
        role: Message role - one of "user", "assistant", "system"
        content: Message content as string or structured content
    """
    role: str
    content: str


# ============================================================================
# Tool Configuration Types
# ============================================================================

class BaseToolConfig(TypedDict):
    """
    Base configuration for all tool configurations.
    
    Provides the common fields that all tool configurations must include,
    regardless of their specific implementation type.
    
    Attributes:
        id: Unique identifier for the tool configuration
        type: Tool type - determines which adapter handles the tool
        disabled: Whether the tool should be skipped during loading
    """
    id: str
    type: str
    disabled: bool


class MCPToolConfig(BaseToolConfig):
    """
    Configuration for Model Context Protocol (MCP) tools.
    
    Handles configuration for MCP-based tools that communicate via stdio
    or HTTP transports. The engine manages connection lifecycle but delegates
    actual tool execution to strands-agents.
    
    Attributes:
        command: Command to execute for stdio transport (optional)
        args: Command line arguments for stdio transport (optional)
        env: Environment variables for process (optional)
        url: URL for HTTP transport (optional)
        functions: Filter for specific functions to expose (optional)
    """
    # For stdio transport
    command: Optional[str]
    args: Optional[List[str]]
    env: Optional[Dict[str, str]]
    # For HTTP transport  
    url: Optional[str]
    # Optional function filtering
    functions: Optional[List[str]]


class PythonToolConfig(BaseToolConfig):
    """
    Configuration for Python-based tools.
    
    Handles configuration for tools implemented as Python modules or functions.
    The engine handles module loading and discovery while strands-agents manages
    execution.
    
    Attributes:
        module_path: Python module path (e.g., 'mypackage.tools')
        functions: List of function names to expose as tools
        package_path: Optional package search path (optional)
        source_file: Discovered source file path (set by discovery process)
    """
    module_path: str
    functions: List[str]
    package_path: Optional[str]
    source_file: Optional[str]


ToolConfig = Union[MCPToolConfig, PythonToolConfig]
"""Union type representing all possible tool configuration types."""


# ============================================================================
# Tool Specification Types
# ============================================================================

class StandardToolSpec(TypedDict):
    """
    Tool specification for standard (Python-based) tools.
    
    Standard tools are loaded directly as tool instances and are ready
    for immediate use by strands-agents.
    
    Attributes:
        type: Always "standard" for standard tools
        tool: The loaded tool instance ready for execution
    """
    type: str  # Always "standard"
    tool: Any


class MCPToolSpec(TypedDict):
    """
    Tool specification for MCP (Model Context Protocol) tools.
    
    MCP tools require a client connection to access their functionality.
    The client encapsulates all connection details, filtering, and server
    identification.
    
    Attributes:
        type: Always "mcp" for MCP tools
        client: MCPClient instance with connection and filtering capabilities
    """
    type: str  # Always "mcp"
    client: Any  # MCPClient instance


ToolSpec = Union[StandardToolSpec, MCPToolSpec]
"""Union type representing all possible tool specifications."""


# ============================================================================
# Tool Runtime Protocols
# ============================================================================

@runtime_checkable
class Tool(Protocol):
    """
    Protocol for tool objects provided by strands-agents.
    
    This protocol defines the interface that the engine expects from tool
    objects, without requiring knowledge of specific implementation details.
    The actual tool execution is handled by strands-agents.
    """
    pass


# ============================================================================
# Tool Operation Result Types
# ============================================================================

class ToolCreationResult(NamedTuple):
    """
    Detailed result of tool creation operations.
    
    Provides comprehensive information about tool creation success/failure
    including tracking of requested vs. found functions for debugging.
    
    Attributes:
        tools: Successfully created tool objects (default: empty list)
        requested_functions: Function names that were requested (default: empty list)
        found_functions: Function names that were successfully found (default: empty list)
        missing_functions: Function names that were requested but not found (default: empty list)
        error: Error message if creation failed (default: None)
        mcp_client: MCP client instance for MCP-based tools (default: None)
    """
    tools: List[Any] = []
    requested_functions: List[str] = []
    found_functions: List[str] = []
    missing_functions: List[str] = []
    error: Optional[str] = None
    mcp_client: Optional[Any] = None


class ToolDiscoveryResult(NamedTuple):
    """
    Result of tool configuration discovery operations.
    
    Provides summary information about configuration file scanning and
    parsing operations across multiple configuration sources.
    
    Attributes:
        successful_configs: Tool configurations that were successfully parsed
        failed_configs: Configuration entries that failed to parse
        total_files_scanned: Total number of configuration files processed
    """
    successful_configs: List[ToolConfig]
    failed_configs: List[Dict[str, Any]]
    total_files_scanned: int


# ============================================================================
# Framework Adapter Protocol
# ============================================================================

@runtime_checkable
class FrameworkAdapter(Protocol):
    """
    Protocol for framework-specific adapters.
    
    Framework adapters handle the integration between strands_agent_factory and
    different AI provider frameworks (OpenAI, Anthropic, etc.). They manage
    model loading, tool adaptation, and framework-specific configuration.
    
    Methods:
        adapt_tools: Transform tools for framework compatibility
        prepare_agent_args: Prepare arguments for Agent initialization
    """
    
    def adapt_tools(self, tools: List[Tool]) -> List[Tool]:
        """
        Adapt tools for the specific framework.
        
        Different frameworks may require different tool formats, schemas,
        or modifications. This method handles those transformations.
        
        Args:
            tools: List of tool objects to adapt
            
        Returns:
            List of framework-adapted tool objects
        """
        ...
    
    def prepare_agent_args(self, 
                          system_prompt: Optional[str] = None,
                          messages: Optional[List[Message]] = None,
                          **kwargs) -> Dict[str, Any]:
        """
        Prepare arguments for Agent initialization.
        
        Handles framework-specific argument preparation including message
        formatting, system prompt handling, and other configuration.
        
        Args:
            system_prompt: System prompt to use (optional)
            messages: Existing message history (optional)
            **kwargs: Additional framework-specific arguments
            
        Returns:
            Dictionary of arguments for Agent constructor
        """
        ...


# ============================================================================
# File Content Types
# ============================================================================

class FileContent(NamedTuple):
    """
    Processed file content for agent consumption.
    
    Represents a file that has been processed and prepared for inclusion
    in agent conversations or system prompts.
    
    Attributes:
        path: Original file path
        content: Processed text content
        mimetype: Detected MIME type (optional)
        metadata: Additional file metadata
    """
    path: Path
    content: str
    mimetype: Optional[str]
    metadata: Dict[str, Any]