"""
Base adapter interface for tool specification creation in strands_agent_factory.

This module provides the abstract ToolAdapter base class that defines the
interface for all tool adapters in strands_agent_factory. Tool adapters are responsible
for loading and configuring tools from different sources (MCP servers, Python
modules, etc.) and creating tool specifications that can be processed later.

The tool adapter system enables:
- Pluggable tool source support (MCP, Python, custom types)
- Consistent configuration and error handling across tool types
- Resource lifecycle management via ExitStack integration
- Tool specification creation for deferred tool loading
- Detailed result reporting with success/failure tracking

Tool adapters follow a common pattern:
1. Accept configuration dictionaries specific to their tool type
2. Create tool specifications (not actual tool instances)
3. Return detailed results including success/failure information
4. Register cleanup handlers with the provided ExitStack
"""

from abc import ABC, abstractmethod
from contextlib import ExitStack
from typing import Any, Dict

from ..ptypes import ToolSpec


class ToolSpecCreationResult:
    """
    Result of tool specification creation operations.
    
    Provides comprehensive information about tool spec creation success/failure
    including metadata for debugging and tracking.
    
    Attributes:
        tool_spec: Successfully created tool specification (None if failed)
        requested_functions: Function names that were requested (default: empty list)
        error: Error message if creation failed (default: None)
    """
    
    def __init__(self, tool_spec: ToolSpec = None, requested_functions: list = None, error: str = None):
        self.tool_spec = tool_spec
        self.requested_functions = requested_functions or []
        self.error = error


class ToolAdapter(ABC):
    """
    Abstract base class for tool adapters.
    
    ToolAdapter defines the interface that all tool adapters must implement
    to participate in the strands_agent_factory tool loading system. Adapters are
    responsible for converting tool configurations into tool specifications that
    can be processed later to create actual tool instances.
    
    Key responsibilities:
    - Parse and validate tool-specific configuration
    - Create tool specifications (not actual tool instances)
    - Register cleanup handlers for resource management  
    - Provide detailed success/failure reporting
    
    The adapter pattern allows strands_agent_factory to support multiple tool
    types through a common interface while encapsulating the complexity
    of each tool source type.
    
    Attributes:
        exit_stack: ExitStack for registering cleanup handlers
        
    Example:
        Implementing a custom tool adapter::
        
            class MyToolAdapter(ToolAdapter):
                def create(self, config: Dict[str, Any]) -> ToolSpecCreationResult:
                    # Parse configuration
                    tool_id = config["id"]
                    
                    # Create tool specification
                    tool_spec = {
                        "type": "custom",
                        "config": config,
                        "metadata": {"id": tool_id}
                    }
                    
                    # Register cleanup if needed
                    self.exit_stack.callback(self._cleanup_resources)
                    
                    return ToolSpecCreationResult(
                        tool_spec=tool_spec,
                        requested_functions=config.get("functions", []),
                        error=None
                    )
    """

    def __init__(self, exit_stack: ExitStack):
        """
        Initialize the tool adapter with resource management.
        
        Creates a tool adapter instance with access to an ExitStack for
        registering cleanup handlers. The ExitStack enables proper resource
        management across the lifetime of tool connections and processes.
        
        Args:
            exit_stack: ExitStack instance for registering cleanup handlers.
                       Adapters should register any cleanup operations
                       (closing connections, terminating processes, etc.)
                       with this stack to ensure proper resource management.
                       
        Note:
            Adapters should register cleanup handlers immediately when
            creating resources that need cleanup. The ExitStack will
            ensure proper cleanup order and exception handling.
        """
        self.exit_stack = exit_stack

    @abstractmethod
    def create(self, config: Dict[str, Any]) -> ToolSpecCreationResult:
        """
        Create tool specification based on the provided configuration.
        
        This is the main method that tool adapters must implement. It takes
        a configuration dictionary specific to the tool type and returns
        a ToolSpecCreationResult with the created tool specification.
        
        The method should:
        1. Validate the configuration for required fields
        2. Create appropriate tool specification
        3. Register cleanup handlers with self.exit_stack if needed
        4. Return comprehensive result information
        
        Args:
            config: Tool configuration dictionary. The structure depends on
                   the specific tool adapter, but typically includes:
                   - id: Unique identifier for the tool configuration
                   - type: Tool type (used to select the appropriate adapter)
                   - Additional fields specific to the tool type
                   
        Returns:
            ToolSpecCreationResult: Detailed result of the spec creation process
            including:
            - tool_spec: Successfully created tool specification
            - requested_functions: Functions that were requested
            - error: Error message if creation failed (None on success)
            
        Raises:
            NotImplementedError: If not implemented by subclass (abstract method)
            
        Example:
            Implementation pattern::
            
                def create(self, config: Dict[str, Any]) -> ToolSpecCreationResult:
                    try:
                        # Validate configuration
                        required_fields = ["id", "source"]
                        for field in required_fields:
                            if field not in config:
                                return ToolSpecCreationResult(
                                    tool_spec=None,
                                    requested_functions=[],
                                    error=f"Missing required field: {field}"
                                )
                        
                        # Create tool specification
                        tool_spec = {
                            "type": "my_type",
                            "config": config,
                            "metadata": {"id": config["id"]}
                        }
                        
                        # Return success result
                        return ToolSpecCreationResult(
                            tool_spec=tool_spec,
                            requested_functions=config.get("functions", []),
                            error=None
                        )
                        
                    except Exception as e:
                        return ToolSpecCreationResult(
                            tool_spec=None,
                            requested_functions=config.get("functions", []),
                            error=str(e)
                        )
        """
        pass