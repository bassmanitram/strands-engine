"""
Type definitions and data structures for strands_agent_factory.

This module defines the core types, protocols, and data structures used throughout
strands_agent_factory for configuration, tool management, and runtime operations.
The types provide strong typing guarantees while maintaining flexibility for
extensibility and framework adaptation.

Key type categories:
- Configuration types: For loading and validating user configurations
- Tool specification types: For describing how tools should be loaded
- Runtime protocol types: For tool execution and framework integration
- Discovery and reporting types: For tool discovery and error reporting

All types are designed to be JSON-serializable where appropriate and provide
clear interfaces for the various components of strands_agent_factory.
"""

from typing import Any, Dict, List, Optional, Union, TypedDict, Protocol, runtime_checkable
from pathlib import Path

# ============================================================================
# Core Type Aliases
# ============================================================================

PathLike = Union[str, Path]
"""Type alias for filesystem paths - accepts both strings and Path objects."""

JSONDict = Dict[str, Any]
"""Type alias for JSON-like dictionary structures."""

ToolConfig = Dict[str, Any]
"""
Configuration dictionary for a single tool.

Common fields across all tool types:
- id: Unique identifier for the tool
- type: Tool type ("python", "mcp", etc.)
- disabled: Optional boolean to skip tool loading
- functions: Optional list of specific functions to load

Additional fields vary by tool type and are validated by the appropriate adapter.
"""

Tool = Any
"""
Type alias for tool instances.

Tools can be any callable object (function, class method, etc.) that conforms
to the strands-agents tool interface. The actual type depends on the tool
source and framework adapter.
"""

FrameworkAdapter = Any
"""
Type alias for framework adapter instances.

Framework adapters handle model loading, tool adaptation, and framework-specific
configuration. The actual type depends on the specific framework being used.
"""


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
# Tool Discovery and Reporting Types  
# ============================================================================

class ToolDiscoveryResult:
    """
    Results from tool configuration discovery operations.
    
    Provides comprehensive reporting on tool configuration loading including
    success/failure statistics and detailed error information for debugging
    and monitoring purposes.
    
    Attributes:
        successful_configs: List of successfully loaded configurations
        failed_configs: List of failed configurations with error details
        total_files_scanned: Total number of configuration files processed
        
    Example:
        Processing discovery results::
        
            configs, discovery = factory.load_tool_configs(paths)
            
            print(f"Loaded {len(discovery.successful_configs)} configurations")
            print(f"Failed {len(discovery.failed_configs)} configurations")
            
            for failed in discovery.failed_configs:
                print(f"Error in {failed['file_path']}: {failed['error']}")
    """

    def __init__(self, successful_configs: List[ToolConfig], failed_configs: List[Dict[str, Any]], total_files_scanned: int):
        """
        Initialize discovery result with configuration loading statistics.
        
        Args:
            successful_configs: Configurations that loaded successfully
            failed_configs: Configurations that failed with error details
            total_files_scanned: Total number of files that were processed
        """
        self.successful_configs = successful_configs
        self.failed_configs = failed_configs
        self.total_files_scanned = total_files_scanned

    @property
    def success_rate(self) -> float:
        """Calculate the success rate as a percentage."""
        if self.total_files_scanned == 0:
            return 0.0
        return (len(self.successful_configs) / self.total_files_scanned) * 100

    def __repr__(self) -> str:
        return (f"ToolDiscoveryResult(successful={len(self.successful_configs)}, "
                f"failed={len(self.failed_configs)}, "
                f"total={self.total_files_scanned}, "
                f"success_rate={self.success_rate:.1f}%)")


# ============================================================================
# Tool Specification Types
# ============================================================================

class ToolSpec(TypedDict, total=False):
    """
    Unified tool specification for all tool types.
    
    A ToolSpec describes how to load and execute tools but does not contain
    the actual tool instances. It serves as a bridge between tool discovery
    and tool execution, allowing strands-agents to handle the actual tool
    instantiation and execution.
    
    The specification supports both standard Python tools (loaded immediately)
    and MCP tools (connection deferred until execution).
    
    Attributes:
        client: MCPClient instance for MCP tools (None for standard tools)
        tools: List of tool instances for standard tools (None for MCP tools)
        
    Examples:
        Standard Python tool spec::
        
            spec = {
                "tools": [add_function, subtract_function],
                "client": None
            }
            
        MCP tool spec::
        
            spec = {
                "client": mcp_client_instance,
                "tools": None
            }
            
    Note:
        Exactly one of 'client' or 'tools' should be set. The other should be None.
        This design allows for easy extension to additional tool types in the future.
    """
    client: Optional[Any]  # MCPClient for MCP tools, None for others
    tools: Optional[List[Tool]]  # Tool instances for standard tools, None for MCP


# ============================================================================
# Tool Runtime Protocols
# ============================================================================

@runtime_checkable
class ToolExecutor(Protocol):
    """
    Protocol for tool execution interfaces.
    
    Defines the interface that tool executors must implement to participate
    in the strands-agents tool execution system. This protocol ensures
    compatibility across different tool sources while allowing framework-
    specific adaptations.
    """

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool with the given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Dictionary of arguments to pass to the tool
            
        Returns:
            Any: Result of tool execution
            
        Raises:
            ToolExecutionError: If tool execution fails
            ToolNotFoundError: If requested tool is not available
        """
        ...

    def list_available_tools(self) -> List[str]:
        """
        List all available tools that can be executed.
        
        Returns:
            List[str]: Names of available tools
        """
        ...


# ============================================================================
# Configuration Management Types
# ============================================================================

class ConfigurationError(Exception):
    """
    Exception raised for configuration-related errors.
    
    Used when configuration files cannot be loaded, parsed, or validated.
    Provides detailed error information for debugging and user feedback.
    
    Attributes:
        config_path: Path to the configuration file that caused the error
        config_key: Specific configuration key that caused the error (optional)
        original_error: The underlying exception that triggered this error (optional)
    """

    def __init__(self, message: str, config_path: Optional[PathLike] = None, 
                 config_key: Optional[str] = None, original_error: Optional[Exception] = None):
        """
        Initialize configuration error with detailed context.
        
        Args:
            message: Human-readable error description
            config_path: Path to the problematic configuration file
            config_key: Specific configuration key that failed
            original_error: Underlying exception that caused this error
        """
        super().__init__(message)
        self.config_path = config_path
        self.config_key = config_key
        self.original_error = original_error

    def __str__(self) -> str:
        """Return formatted error message with context."""
        parts = [super().__str__()]
        
        if self.config_path:
            parts.append(f"Config file: {self.config_path}")
        if self.config_key:
            parts.append(f"Config key: {self.config_key}")
        if self.original_error:
            parts.append(f"Caused by: {self.original_error}")
            
        return " | ".join(parts)


# ============================================================================
# Tool Execution Error Types
# ============================================================================

class ToolExecutionError(Exception):
    """
    Exception raised when tool execution fails.
    
    Provides detailed context about tool execution failures including
    the tool name, arguments, and underlying error information.
    """

    def __init__(self, tool_name: str, message: str, arguments: Optional[Dict[str, Any]] = None,
                 original_error: Optional[Exception] = None):
        """
        Initialize tool execution error.
        
        Args:
            tool_name: Name of the tool that failed
            message: Human-readable error description
            arguments: Arguments that were passed to the tool
            original_error: Underlying exception that caused the failure
        """
        super().__init__(message)
        self.tool_name = tool_name
        self.arguments = arguments or {}
        self.original_error = original_error


class ToolNotFoundError(Exception):
    """
    Exception raised when a requested tool cannot be found.
    
    Used when attempting to execute a tool that is not available
    in the current tool registry or MCP server.
    """

    def __init__(self, tool_name: str, available_tools: Optional[List[str]] = None):
        """
        Initialize tool not found error.
        
        Args:
            tool_name: Name of the requested tool that was not found
            available_tools: List of available tool names for reference
        """
        message = f"Tool '{tool_name}' not found"
        if available_tools:
            message += f". Available tools: {', '.join(available_tools)}"
        
        super().__init__(message)
        self.tool_name = tool_name
        self.available_tools = available_tools or []


# ============================================================================
# Legacy Type Aliases (Deprecated)
# ============================================================================

# These are kept for backward compatibility but should not be used in new code
StandardToolSpec = ToolSpec  # Deprecated: Use ToolSpec instead
MCPToolSpec = ToolSpec      # Deprecated: Use ToolSpec instead