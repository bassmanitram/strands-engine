"""
Tool factory implementation for strands_engine.

This module provides the ToolFactory class, which serves as the central coordinator
for tool discovery, loading, and creation in strands_engine. The factory uses a
registry of adapters to support multiple tool types while providing consistent
error handling and resource management.

The factory handles the complete tool lifecycle from configuration discovery
through tool object creation, but does not execute tools. Tool execution is
delegated entirely to strands-agents, maintaining clear separation of concerns.

Key capabilities:
- Multi-source tool configuration loading (JSON/YAML files)
- Adapter-based tool creation supporting MCP, Python, and custom types
- Comprehensive error handling and reporting
- Resource lifecycle management via ExitStack integration
- Detailed logging and debugging support
"""

from contextlib import ExitStack
from pathlib import Path
from typing import Any, Dict, List, Tuple

from loguru import logger

from strands_engine.utils import load_structured_file

from ..ptypes import PathLike, Tool, ToolConfig, ToolCreationResult, ToolDiscoveryResult
from .base_adapter import ToolAdapter
from .python_adapter import PythonToolAdapter
from .mcp_adapters import MCPHTTPAdapter, MCPStdIOAdapter


class ToolFactory:
    """
    Centralized factory for tool discovery, loading, and creation.
    
    ToolFactory coordinates the complete tool management lifecycle for
    strands_engine, from configuration file discovery through tool object
    creation. It uses a registry of tool adapters to support multiple tool
    types while providing consistent error handling and resource management.
    
    The factory is designed around these principles:
    - Configuration-driven tool discovery and loading
    - Adapter pattern for extensible tool type support
    - Comprehensive error handling with detailed reporting
    - Resource lifecycle management via ExitStack integration
    - Clear separation between tool loading and execution
    
    Supported tool types:
    - "python": Native Python functions and modules
    - "mcp-stdio": Model Context Protocol via stdio transport
    - "mcp-http": Model Context Protocol via HTTP transport
    - "mcp": Auto-detect MCP transport based on configuration
    
    The factory loads and configures tools for strands-agents but never
    executes them directly. This separation ensures clean architecture
    boundaries and allows strands-agents to handle tool execution with
    its own security and error handling mechanisms.
    
    Attributes:
        _adapters: Registry of tool adapters by type
        
    Example:
        Basic usage::
        
            with ExitStack() as stack:
                factory = ToolFactory(stack)
                
                # Load configurations from files
                configs, result = factory.load_tool_configs(["/path/to/tools/"])
                
                # Create tool objects
                tools = factory.create_tools(configs)
                
                # Tools are now ready for strands-agents to use
    """

    def __init__(self, exit_stack: ExitStack):
        """
        Initialize the tool factory with resource management.
        
        Creates a ToolFactory with the standard set of tool adapters
        and associates it with an ExitStack for proper resource lifecycle
        management. The ExitStack ensures that all tool connections and
        resources are properly cleaned up when the factory scope ends.
        
        Args:
            exit_stack: ExitStack instance for resource cleanup management.
                       All tool adapters will register their cleanup handlers
                       with this stack to ensure proper resource management.
                       
        Note:
            The factory automatically registers standard adapters for Python,
            MCP stdio, and MCP HTTP tool types. Custom adapters can be added
            by extending the _adapters registry after initialization.
        """
        self._adapters: Dict[str, ToolAdapter] = {
            "python": PythonToolAdapter(exit_stack),
            "mcp-stdio": MCPStdIOAdapter(exit_stack),
            "mcp-http": MCPHTTPAdapter(exit_stack)
        }

    def create_tools(self, tool_configs: List[ToolConfig]) -> List[ToolCreationResult]:
        """
        Create tools from a list of tool configurations.
        
        Processes multiple tool configurations to create tool objects using
        the appropriate adapters. This is the main entry point for bulk tool
        creation, handling configuration validation, adapter selection, and
        comprehensive error reporting.
        
        The method:
        1. Filters out disabled tool configurations
        2. Routes each configuration to the appropriate adapter
        3. Collects and aggregates creation results
        4. Provides detailed logging for debugging and monitoring
        
        Args:
            tool_configs: List of validated tool configuration dictionaries
            
        Returns:
            List[ToolCreationResult]: Results from each tool creation attempt,
            including both successful and failed creations. Each result contains:
            - tools: Successfully created tool objects
            - requested_functions: Functions that were requested
            - found_functions: Functions that were actually created
            - missing_functions: Requested functions that couldn't be found
            - error: Error message if creation failed
            
        Example:
            Processing multiple tool configurations::
            
                configs = [
                    {"id": "calc", "type": "python", "module_path": "calculator"},
                    {"id": "web", "type": "mcp", "command": "web-server", "args": []}
                ]
                
                results = factory.create_tools(configs)
                
                for result in results:
                    if result.error:
                        print(f"Failed: {result.error}")
                    else:
                        print(f"Created {len(result.tools)} tools")
                        
        Note:
            Configurations marked with "disabled": true are automatically
            skipped with appropriate logging. This allows temporarily
            disabling tools without removing their configurations.
        """
        creation_results = []

        for tool_config in tool_configs:
            # Skip disabled tools
            if tool_config.get('disabled', False):
                logger.info(f"Skipping disabled tool: {tool_config.get('id', 'unknown')}")
                continue
                
            logger.debug(f"Creating tools for config: {tool_config.get('id', 'unknown')}")
            
            try:
                result = self.create_tools_from_config(tool_config)
                creation_results.append(result)

            except Exception as e:
                message = f"Exception loading tools from '{tool_config.get('id', 'unknown')}': {e}"
                creation_results.append(ToolCreationResult(
                    tools=[],
                    requested_functions=tool_config.get("functions", []),
                    found_functions=[],
                    missing_functions=tool_config.get("functions", []),
                    error=message
                ))
                logger.error(message)
        
        return creation_results

    def create_tools_from_config(self, config: Dict[str, Any]) -> ToolCreationResult:
        """
        Create tools from a single configuration dictionary.
        
        Processes a single tool configuration to create tool objects using
        the appropriate adapter. This method handles adapter selection,
        including special logic for MCP transport detection, and delegates
        the actual tool creation to the selected adapter.
        
        Tool type selection logic:
        - "python": Uses PythonToolAdapter directly
        - "mcp-stdio": Uses MCPStdIOAdapter directly  
        - "mcp-http": Uses MCPHTTPAdapter directly
        - "mcp": Auto-detects transport based on "command" vs "url" fields
        
        Args:
            config: Tool configuration dictionary containing:
                   - id: Unique identifier for the tool
                   - type: Tool type ("python", "mcp", "mcp-stdio", "mcp-http")
                   - Additional fields specific to the tool type
                   
        Returns:
            ToolCreationResult: Detailed result of the tool creation process
            
        Raises:
            Exception: Propagated from adapter.create() if tool creation fails
            
        Example:
            Creating tools from configuration::
            
                config = {
                    "id": "calculator",
                    "type": "python", 
                    "module_path": "tools.calculator",
                    "functions": ["add", "subtract", "multiply"]
                }
                
                result = factory.create_tools_from_config(config)
                if not result.error:
                    print(f"Created {len(result.tools)} calculator tools")
                    
        Note:
            For MCP configurations with type "mcp", the method automatically
            detects the appropriate transport based on the presence of "command"
            (stdio) or "url" (HTTP) fields in the configuration.
        """
        tool_type = config.get("type")

        # Special handling for MCP to distinguish between stdio and http
        if tool_type == "mcp":
            if "command" in config:
                tool_type = "mcp-stdio"
            elif "url" in config:
                tool_type = "mcp-http"
            else:
                logger.error(f"MCP config for '{config.get('id')}' is missing 'url' or 'command'. Cannot connect.")
                return ToolCreationResult(
                    tools=[],
                    requested_functions=config.get("functions", []),
                    found_functions=[],
                    missing_functions=config.get("functions", []),
                    error="MCP config missing 'url' or 'command'"
                )

        adapter = self._adapters.get(tool_type)
        if adapter:
            logger.debug(f"Creating tools using {tool_type} adapter for '{config.get('id')}'")
            return adapter.create(config)
        else:
            logger.warning(f"Tool '{config.get('id')}' has unknown type '{tool_type}'. Skipping.")
            return ToolCreationResult(
                tools=[],
                requested_functions=config.get("functions", []),
                found_functions=[],
                missing_functions=config.get("functions", []),
                error=f"Unknown tool type '{tool_type}'"
            )

    def load_tool_configs(self, file_paths: List[PathLike]) -> Tuple[List[ToolConfig], ToolDiscoveryResult]:
        """
        Load tool configurations from configuration files.
        
        Discovers and loads tool configurations from the specified file paths,
        validating configuration structure and providing detailed error reporting.
        This method handles the file discovery and parsing phase of tool loading.
        
        The method:
        1. Processes each provided file path
        2. Loads and parses JSON/YAML configuration files
        3. Validates basic configuration structure
        4. Collects detailed success/failure information
        5. Returns both successful configurations and discovery results
        
        Args:
            file_paths: List of file paths to configuration files. Can include:
                       - Direct paths to .json or .yaml files
                       - Directory paths (implementation may scan for configs)
                       - Empty list to disable tool loading
                       
        Returns:
            Tuple[List[ToolConfig], ToolDiscoveryResult]: A tuple containing:
            - List of successfully loaded and validated tool configurations
            - ToolDiscoveryResult with comprehensive discovery statistics including:
                * successful_configs: Configurations that loaded successfully
                * failed_configs: Configurations that failed with error details
                * total_files_scanned: Total number of files processed
                
        Example:
            Loading configurations from multiple sources::
            
                file_paths = [
                    "/path/to/python-tools.yaml",
                    "/path/to/mcp-tools.json",
                    "/path/to/tools-directory/"
                ]
                
                configs, result = factory.load_tool_configs(file_paths)
                
                print(f"Loaded {len(configs)} configurations")
                print(f"Failed: {len(result.failed_configs)}")
                
                for failed in result.failed_configs:
                    print(f"  {failed['file_path']}: {failed['error']}")
                    
        Note:
            The method only validates configuration file structure and required
            fields. It does not validate that tools can actually be created or
            that referenced modules/servers are available. That validation
            occurs during tool creation.
        """
        path_list = file_paths or []

        successful_configs: List[ToolConfig] = []
        failed_configs: List[Dict[str, Any]] = []

        logger.debug(f"Loading {len(path_list)} tool configuration files...")

        for file_path in path_list:
            try:
                file_path = Path(file_path)
                config_data = load_structured_file(file_path)

                # Add source file reference for debugging
                config_data['source_file'] = str(file_path)

                # Configuration validation is performed by adapters during creation
                successful_configs.append(config_data)
                logger.info(f"Loaded tool config '{config_data.get('id', 'unknown')}' from {file_path}")

            except Exception as e:
                failed_configs.append({
                    'file_path': str(file_path),
                    'config_id': 'unknown',
                    'error': str(e),
                    'config_data': None
                })
                logger.error(f"Error loading tool config '{file_path}': {e}")

        discovery_result = ToolDiscoveryResult(
            successful_configs,
            failed_configs,
            len(path_list)
        )

        logger.info(f"Tool discovery complete: {len(successful_configs)} successful, {len(failed_configs)} failed from {len(path_list)} files")
        return successful_configs, discovery_result