"""
Tool factory implementation for strands_agent_factory.

This module provides the ToolFactory class, which serves as the central coordinator
for tool discovery, loading, and specification creation in strands_agent_factory. The factory
uses a registry of adapters to support multiple tool types while providing consistent
error handling and resource management.

The factory handles the complete tool specification lifecycle from configuration discovery
through tool spec creation, but does not create actual tool instances. Tool specification
describes how tools should be loaded and executed later, maintaining clear separation of
concerns between tool discovery and tool execution.

Key capabilities:
- Multi-source tool configuration loading (JSON/YAML files)
- Adapter-based tool specification creation supporting MCP, Python, and custom types
- Comprehensive error handling and reporting
- Resource lifecycle management via ExitStack integration
- Detailed logging and debugging support
"""

from contextlib import ExitStack
from pathlib import Path
from typing import Any, Dict, List, Tuple

from loguru import logger

from strands_agent_factory.utils import load_structured_file

from ..ptypes import PathLike, ToolConfig, ToolDiscoveryResult, ToolSpec
from .base_adapter import ToolAdapter, ToolSpecCreationResult
from .python_adapter import PythonToolAdapter
from .mcp_adapters import MCPHTTPAdapter, MCPStdIOAdapter


class ToolFactory:
    """
    Centralized factory for tool discovery, loading, and specification creation.
    
    ToolFactory coordinates the complete tool specification management lifecycle for
    strands_agent_factory, from configuration file discovery through tool specification
    creation. It uses a registry of tool adapters to support multiple tool
    types while providing consistent error handling and resource management.
    
    The factory is designed around these principles:
    - Configuration-driven tool discovery and loading
    - Adapter pattern for extensible tool type support
    - Tool specification creation (not actual tool instances)
    - Comprehensive error handling with detailed reporting
    - Resource lifecycle management via ExitStack integration
    - Clear separation between tool specification and execution
    
    Supported tool types:
    - "python": Native Python functions and modules
    - "mcp-stdio": Model Context Protocol via stdio transport
    - "mcp-http": Model Context Protocol via HTTP transport
    - "mcp": Auto-detect MCP transport based on configuration
    
    The factory creates tool specifications that describe how to load and execute
    tools, but never executes tools directly. This separation ensures clean
    architecture boundaries and allows strands-agents to handle tool execution
    with its own security and error handling mechanisms.
    
    Attributes:
        _adapters: Registry of tool adapters by type
        
    Example:
        Basic usage::
        
            with ExitStack() as stack:
                factory = ToolFactory(stack)
                
                # Load configurations from files
                configs, result = factory.load_tool_configs(["/path/to/tools/"])
                
                # Create tool specifications
                tool_specs = factory.create_tool_specs(configs)
                
                # Tool specs are now ready for strands-agents to process
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

    def create_tool_specs(self, tool_configs: List[ToolConfig]) -> List[ToolSpecCreationResult]:
        """
        Create tool specifications from a list of tool configurations.
        
        Processes multiple tool configurations to create tool specifications using
        the appropriate adapters. This is the main entry point for bulk tool
        specification creation, handling configuration validation, adapter selection,
        and comprehensive error reporting.
        
        The method:
        1. Filters out disabled tool configurations
        2. Routes each configuration to the appropriate adapter
        3. Collects and aggregates creation results
        4. Provides detailed logging for debugging and monitoring
        
        Args:
            tool_configs: List of validated tool configuration dictionaries
            
        Returns:
            List[ToolSpecCreationResult]: Results from each tool spec creation attempt,
            including both successful and failed creations. Each result contains:
            - tool_spec: Successfully created tool specification (or None)
            - requested_functions: Functions that were requested
            - error: Error message if creation failed
            
        Example:
            Processing multiple tool configurations::
            
                configs = [
                    {"id": "calc", "type": "python", "module_path": "calculator"},
                    {"id": "web", "type": "mcp", "command": "web-server", "args": []}
                ]
                
                results = factory.create_tool_specs(configs)
                
                for result in results:
                    if result.error:
                        print(f"Failed: {result.error}")
                    else:
                        print(f"Created tool spec: {result.tool_spec['type']}")
                        
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
                
            logger.debug(f"Creating tool spec for config: {tool_config.get('id', 'unknown')}")
            
            try:
                result = self.create_tool_spec_from_config(tool_config)
                creation_results.append(result)

            except Exception as e:
                message = f"Exception creating tool spec from '{tool_config.get('id', 'unknown')}': {e}"
                creation_results.append(ToolSpecCreationResult(
                    tool_spec=None,
                    requested_functions=tool_config.get("functions", []),
                    error=message
                ))
                logger.error(message)
        
        return creation_results

    def create_tool_spec_from_config(self, config: Dict[str, Any]) -> ToolSpecCreationResult:
        """
        Create tool specification from a single configuration dictionary.
        
        Processes a single tool configuration to create a tool specification using
        the appropriate adapter. This method handles adapter selection,
        including special logic for MCP transport detection, and delegates
        the actual tool specification creation to the selected adapter.
        
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
            ToolSpecCreationResult: Detailed result of the tool spec creation process
            
        Raises:
            Exception: Propagated from adapter.create() if tool spec creation fails
            
        Example:
            Creating tool spec from configuration::
            
                config = {
                    "id": "calculator",
                    "type": "python", 
                    "module_path": "tools.calculator",
                    "functions": ["add", "subtract", "multiply"]
                }
                
                result = factory.create_tool_spec_from_config(config)
                if not result.error:
                    print(f"Created {result.tool_spec['type']} tool spec")
                    
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
                return ToolSpecCreationResult(
                    tool_spec=None,
                    requested_functions=config.get("functions", []),
                    error="MCP config missing 'url' or 'command'"
                )

        adapter = self._adapters.get(tool_type)
        if adapter:
            logger.debug(f"Creating tool spec using {tool_type} adapter for '{config.get('id')}'")
            return adapter.create(config)
        else:
            logger.warning(f"Tool '{config.get('id')}' has unknown type '{tool_type}'. Skipping.")
            return ToolSpecCreationResult(
                tool_spec=None,
                requested_functions=config.get("functions", []),
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
            fields. It does not validate that tool specs can actually be created or
            that referenced modules/servers are available. That validation
            occurs during tool specification creation.
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

    # Backward compatibility method
    def create_tools(self, tool_configs: List[ToolConfig]) -> List[ToolSpecCreationResult]:
        """
        Backward compatibility method - creates tool specifications.
        
        This method provides backward compatibility with the old interface
        while actually creating tool specifications instead of tool instances.
        
        Args:
            tool_configs: List of validated tool configuration dictionaries
            
        Returns:
            List[ToolSpecCreationResult]: Results from tool spec creation
            
        Note:
            This method is deprecated. Use create_tool_specs() instead.
        """
        logger.warning("create_tools() is deprecated. Use create_tool_specs() instead.")
        return self.create_tool_specs(tool_configs)