"""
Base adapter interface for tool creation in strands_engine.

This module provides the abstract ToolAdapter base class that defines the
interface for all tool adapters in strands_engine. Tool adapters are responsible
for loading and configuring tools from different sources (MCP servers, Python
modules, etc.) while maintaining consistent behavior and error handling.

The tool adapter system enables:
- Pluggable tool source support (MCP, Python, custom types)
- Consistent configuration and error handling across tool types
- Resource lifecycle management via ExitStack integration
- Detailed result reporting with success/failure tracking

Tool adapters follow a common pattern:
1. Accept configuration dictionaries specific to their tool type
2. Load/connect to tool sources using the configuration
3. Create tool objects compatible with strands-agents
4. Return detailed results including success/failure information
5. Register cleanup handlers with the provided ExitStack
"""

from abc import ABC, abstractmethod
from contextlib import ExitStack
from typing import Any, Dict

from ..ptypes import ToolCreationResult


class ToolAdapter(ABC):
    """
    Abstract base class for tool adapters.
    
    ToolAdapter defines the interface that all tool adapters must implement
    to participate in the strands_engine tool loading system. Adapters are
    responsible for converting tool configurations into tool objects that
    can be used by strands-agents.
    
    Key responsibilities:
    - Parse and validate tool-specific configuration
    - Establish connections to tool sources (if applicable)
    - Create tool objects compatible with strands-agents
    - Register cleanup handlers for resource management  
    - Provide detailed success/failure reporting
    
    The adapter pattern allows strands_engine to support multiple tool
    types through a common interface while encapsulating the complexity
    of each tool source type.
    
    Attributes:
        exit_stack: ExitStack for registering cleanup handlers
        
    Example:
        Implementing a custom tool adapter::
        
            class MyToolAdapter(ToolAdapter):
                def create(self, config: Dict[str, Any]) -> ToolCreationResult:
                    # Parse configuration
                    tool_id = config["id"]
                    
                    # Create tool objects
                    tools = self._load_my_tools(config)
                    
                    # Register cleanup if needed
                    self.exit_stack.callback(self._cleanup_resources)
                    
                    return ToolCreationResult(
                        tools=tools,
                        requested_functions=config.get("functions", []),
                        found_functions=[t.name for t in tools],
                        missing_functions=[],
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
    def create(self, config: Dict[str, Any]) -> ToolCreationResult:
        """
        Create tools based on the provided configuration.
        
        This is the main method that tool adapters must implement. It takes
        a configuration dictionary specific to the tool type and returns
        a ToolCreationResult with detailed information about the creation
        process.
        
        The method should:
        1. Validate the configuration for required fields
        2. Establish connections/load modules as needed
        3. Create tool objects compatible with strands-agents
        4. Register cleanup handlers with self.exit_stack if needed
        5. Return comprehensive result information
        
        Args:
            config: Tool configuration dictionary. The structure depends on
                   the specific tool adapter, but typically includes:
                   - id: Unique identifier for the tool configuration
                   - type: Tool type (used to select the appropriate adapter)
                   - Additional fields specific to the tool type
                   
        Returns:
            ToolCreationResult: Detailed result of the tool creation process
            including:
            - tools: List of successfully created tool objects
            - requested_functions: Functions that were requested
            - found_functions: Functions that were actually found/created
            - missing_functions: Requested functions that couldn't be found
            - error: Error message if creation failed (None on success)
            
        Raises:
            NotImplementedError: If not implemented by subclass (abstract method)
            
        Example:
            Implementation pattern::
            
                def create(self, config: Dict[str, Any]) -> ToolCreationResult:
                    try:
                        # Validate configuration
                        required_fields = ["id", "source"]
                        for field in required_fields:
                            if field not in config:
                                return ToolCreationResult(
                                    tools=[], 
                                    requested_functions=[],
                                    found_functions=[],
                                    missing_functions=[],
                                    error=f"Missing required field: {field}"
                                )
                        
                        # Create tools
                        tools = self._create_tools_from_config(config)
                        
                        # Return success result
                        return ToolCreationResult(
                            tools=tools,
                            requested_functions=config.get("functions", []),
                            found_functions=[t.name for t in tools],
                            missing_functions=[],
                            error=None
                        )
                        
                    except Exception as e:
                        return ToolCreationResult(
                            tools=[],
                            requested_functions=config.get("functions", []),
                            found_functions=[],
                            missing_functions=config.get("functions", []),
                            error=str(e)
                        )
        """
        pass