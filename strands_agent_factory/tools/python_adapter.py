"""
Python tool adapter for strands_agent_factory.

This module provides the PythonToolAdapter class, which enables loading and
configuring Python functions as tools for strands-agents to execute. The
adapter supports both installed packages and local modules, with flexible
path resolution and dynamic importing capabilities.

The Python adapter handles:
- Dynamic module and function importing
- Custom package path resolution for local modules
- Function validation and error handling
- Tool metadata extraction and configuration
- Comprehensive error reporting for missing or invalid functions

This adapter is particularly useful for:
- Integrating custom business logic as agent tools
- Wrapping existing Python libraries for agent use
- Rapid prototyping of new tool capabilities
- Local development and testing of tool functions
"""

import importlib
import os
from typing import Any, Callable, Dict, Optional

from loguru import logger

from ..ptypes import ToolCreationResult
from .base_adapter import ToolAdapter


def _import_item(
    base_module: str,
    item_sub_path: str,
    package_path: Optional[str] = None,
    base_path: Optional[str] = None,
) -> Callable:
    """
    Dynamically import a Python item with flexible path resolution.
    
    This utility function provides flexible dynamic importing with support for
    both standard Python module resolution and custom path-based loading. It
    handles the complexity of different import scenarios while providing
    comprehensive error handling.
    
    The function supports two import strategies:
    1. Custom path resolution: Load modules from specific file system locations
    2. Standard Python imports: Use sys.path and installed packages
    
    Args:
        base_module: Base module path (e.g., 'mypackage.tools')
        item_sub_path: Sub-path to the item within the module (e.g., 'utils.calculator')
        package_path: Optional relative path to treat as import root
        base_path: Optional base directory for resolving package_path
        
    Returns:
        Callable: The dynamically imported item (function, class, or module)
        
    Raises:
        ValueError: If the full item path is invalid
        FileNotFoundError: If module file not found when using custom paths
        ImportError: If module cannot be loaded or imported
        AttributeError: If item not found in module
        
    Example:
        Standard import from installed package::
        
            func = _import_item("mypackage", "tools.calculator")
            # Imports mypackage.tools.calculator
            
        Custom path import from local module::
        
            func = _import_item(
                "tools", "calculator.add",
                package_path="src/mytools",
                base_path="/project/root"
            )
            # Loads from /project/root/src/mytools/tools/calculator.py
            
    Note:
        When package_path is provided, the function bypasses sys.path and loads
        modules directly from the specified file system location. This is useful
        for loading tools from project-specific directories.
    """
    # 1. Combine the inputs into a full dotted path and separate module from attribute
    full_item_path = f"{base_module}.{item_sub_path}"

    try:
        full_module_path, item_name = full_item_path.rsplit('.', 1)
        logger.debug(f"Loading item '{item_name}' from module '{full_module_path}' (base_path='{base_path}', package_path='{package_path}')")
    except ValueError as e:
        raise ValueError(f"Invalid path '{full_item_path}'.") from e

    # 2. Decide which loading strategy to use
    if package_path:
        # --- SCENARIO 1: Custom path is provided ---
        # Translate dotted module path to a relative file path
        relative_file_path = full_module_path.replace('.', os.path.sep) + '.py'
        absolute_file_path = os.path.join(base_path or "", package_path, relative_file_path)

        if not os.path.isfile(absolute_file_path):
            raise FileNotFoundError(f"Module file not found at: {absolute_file_path}")

        # Load the module directly from its file path without using sys.path
        spec = importlib.util.spec_from_file_location(full_module_path, absolute_file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {absolute_file_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        item = getattr(module, item_name)

    else:
        # --- SCENARIO 2: Use standard Python imports ---
        try:
            # First, try to import the full path as a module (for cases where the item is a module)
            item = importlib.import_module(full_item_path)
        except ImportError:
            # If that fails, import the base module and get the attribute from it
            module = importlib.import_module(full_module_path)
            item = getattr(module, item_name)

    return item


class PythonToolAdapter(ToolAdapter):
    """
    Tool adapter for loading Python functions as strands-agents tools.
    
    PythonToolAdapter enables the integration of Python functions and modules
    as tools that can be executed by strands-agents. It supports both installed
    packages and local modules with flexible path resolution and comprehensive
    error handling.
    
    The adapter handles:
    - Dynamic importing of Python modules and functions
    - Custom package path resolution for local development
    - Function validation and metadata extraction
    - Comprehensive error reporting and debugging
    - Integration with strands-agents tool execution system
    
    Key features:
    - Support for both installed and local Python modules
    - Flexible function specification (individual functions or module methods)
    - Custom package path support for project-specific tools
    - Detailed success/failure reporting with function-level granularity
    - Resource cleanup integration via ExitStack
    
    Configuration format:
        {
            "id": "calculator_tools",
            "type": "python", 
            "module_path": "tools.calculator",
            "functions": ["add", "subtract", "multiply"],
            "package_path": "src/tools",  # Optional
            "source_file": "/path/to/config.json"  # Added by discovery
        }
        
    Example:
        Loading tools from installed package::
        
            config = {
                "id": "math_tools",
                "type": "python",
                "module_path": "mypackage.math",
                "functions": ["add", "subtract"],
                "source_file": "/config/tools.json"
            }
            
            result = adapter.create(config)
            if not result.error:
                print(f"Loaded {len(result.tools)} math tools")
                
        Loading tools from local module::
        
            config = {
                "id": "local_tools", 
                "type": "python",
                "module_path": "utils",
                "functions": ["helper.format_text", "helper.parse_data"],
                "package_path": "src/tools",
                "source_file": "/project/tools.json"
            }
            
            result = adapter.create(config)
    """

    def create(self, config: Dict[str, Any], schema_normalizer=None) -> ToolCreationResult:
        """
        Create tools from Python modules based on configuration.
        
        Loads the specified Python functions from modules and creates tool
        objects that can be executed by strands-agents. The method handles
        dynamic importing, path resolution, and provides detailed reporting
        of success and failure cases.
        
        The creation process:
        1. Validates required configuration fields
        2. Resolves module and package paths
        3. Dynamically imports requested functions
        4. Creates tool objects for successful imports
        5. Reports detailed success/failure information
        
        Args:
            config: Python tool configuration dictionary containing:
                   - id: Unique identifier for the tool configuration
                   - module_path: Python module path (e.g., 'tools.calculator')
                   - functions: List of function names to load
                   - source_file: Path to configuration file (for path resolution)
                   - package_path: Optional custom package path (optional)
            schema_normalizer: Optional schema normalizer (unused, for interface compatibility)
            
        Returns:
            ToolCreationResult: Detailed result containing:
            - tools: Successfully loaded Python function objects
            - requested_functions: Function names that were requested
            - found_functions: Function names that were successfully loaded
            - missing_functions: Requested functions that couldn't be loaded
            - error: Error message if overall creation failed
            
        Example:
            Successful tool creation::
            
                config = {
                    "id": "calc",
                    "module_path": "tools.math",
                    "functions": ["add", "subtract", "multiply"],
                    "source_file": "/config/tools.json"
                }
                
                result = adapter.create(config)
                # result.tools contains 3 function objects
                # result.found_functions = ["add", "subtract", "multiply"]
                # result.missing_functions = []
                # result.error = None
                
            Partial success with missing functions::
            
                config = {
                    "id": "calc",
                    "module_path": "tools.math", 
                    "functions": ["add", "nonexistent", "multiply"],
                    "source_file": "/config/tools.json"
                }
                
                result = adapter.create(config)
                # result.tools contains 2 function objects
                # result.found_functions = ["add", "multiply"]
                # result.missing_functions = ["nonexistent"]
                # result.error = None (partial success)
                
        Note:
            The method supports both simple function names ("add") and nested
            function paths ("utils.helper.format"). Functions are loaded and
            validated but not executed - execution is handled by strands-agents.
        """
        tool_id = config.get("id")
        module_path = config.get("module_path")
        package_path = config.get("package_path")
        func_names = config.get("functions", [])
        src_file = config.get("source_file")
        
        # Validate required configuration fields
        if not all([tool_id, module_path, func_names, src_file]):
            logger.warning(f"Python tool config '{tool_id}' is missing required fields. Skipping.")
            return ToolCreationResult(
                tools=[],
                requested_functions=func_names or [],
                found_functions=[],
                missing_functions=func_names or [],
                error="Missing required configuration fields"
            )
            
        logger.debug(f"Creating Python tools for tool_id '{tool_id}' from module '{module_path}' with functions {func_names} (package_path='{package_path}', source_file='{src_file}')")

        # Resolve source directory for path-based imports
        source_dir = os.path.dirname(os.path.abspath(src_file))
        logger.debug(f"Resolved source directory for tool config '{tool_id}': {source_dir}")

        try:
            loaded_tools = []
            found_functions = []
            missing_functions = []

            # Process each requested function
            for func_spec in func_names:
                if not isinstance(func_spec, str):
                    logger.warning(f"Function spec '{func_spec}' is not a string in tool config '{tool_id}'. Skipping.")
                    missing_functions.append(str(func_spec))
                    continue

                try:
                    logger.debug(f"Attempting to load function '{func_spec}' from module '{module_path}' (package_path '{package_path}')")
                    tool = _import_item(module_path, func_spec, package_path, source_dir)
                except (ImportError, AttributeError, FileNotFoundError) as e:
                    logger.warning(f"Error loading function '{func_spec}' from module '{module_path}' (package_path '{package_path}'): {e}")
                    missing_functions.append(func_spec)
                    continue

                # Clean up the tool name to remove path prefixes
                clean_function_name = func_spec.split('.')[-1]
                loaded_tools.append(tool)
                found_functions.append(clean_function_name)
                logger.debug(f"Successfully loaded callable '{func_spec}' as '{clean_function_name}' from module '{module_path}'")

            logger.info(f"Successfully loaded {len(loaded_tools)} tools from Python module: {tool_id}")
            return ToolCreationResult(
                tools=loaded_tools,
                requested_functions=func_names,
                found_functions=found_functions,
                missing_functions=missing_functions,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Failed to extract tools from Python module '{tool_id}': {e}")
            return ToolCreationResult(
                tools=[],
                requested_functions=func_names,
                found_functions=[],
                missing_functions=func_names,
                error=str(e)
            )