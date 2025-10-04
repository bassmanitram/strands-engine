"""
Python tool adapter for strands_engine.

Loads tools from Python modules and functions for strands-agents to execute.
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
    Dynamically loads something, using a specific directory as the root if provided.

    Args:
        base_module: The first part of the module's dotted path (e.g., 'my_app.lib').
        item_sub_path: The second part of the path, including submodules and the
                  item name (e.g., 'utils.helpers.my_func', or even 'utils.helpers').
        package_path: (Optional) The relative path to a directory that should be
                      treated as the root for the import. If None, Python's
                      standard import search paths (sys.path) are used.
        base_path: (Optional) The base directory to resolve package_path against.
    Returns:
        A reference to the dynamically loaded attribute.
    """
    # 1. Combine the inputs into a full dotted path and separate module from attribute
    full_item_path = f"{base_module}.{item_sub_path}"

    try:
        full_module_path, item_name = full_item_path.rsplit('.', 1)
        logger.debug(f"Loading item '{item_name}' from module '{full_module_path}' (base_path='{base_path}, package_path='{package_path}')")
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
        #
        # --- SCENARIO 2: Use import tools - two cases - it's a module or it's an attribute! ---
        #
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
    Adapter for creating tools from local or installed Python modules.
    
    Loads Python functions as tools for strands-agents to execute.
    The engine loads tools but never executes them directly.
    """

    def create(self, config: Dict[str, Any], schema_normalizer=None) -> ToolCreationResult:
        """
        Create tools from Python modules based on configuration.
        
        Args:
            config: Python tool configuration
            schema_normalizer: Optional schema normalizer (unused)
            
        Returns:
            ToolCreationResult with loaded Python functions
        """
        tool_id = config.get("id")
        module_path = config.get("module_path")
        package_path = config.get("package_path")
        func_names = config.get("functions", [])
        src_file = config.get("source_file")
        
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

        source_dir = os.path.dirname(os.path.abspath(src_file))
        logger.debug(f"Resolved source directory for tool config '{tool_id}': {source_dir}")

        try:
            loaded_tools = []
            found_functions = []
            missing_functions = []

            # Look for the specific function names requested in the config
            for func_spec in func_names:
                if not isinstance(func_spec, str):
                    logger.warning(f"Function spec '{func_spec}' is not a string in tool config '{tool_id}'. Skipping.")
                    missing_functions.append(str(func_spec))
                    continue

                try:
                    logger.debug(f"Attempting to load function '{func_spec}' from module '{module_path}' (package_path '{package_path}')")
                    tool = _import_item(module_path, func_spec, package_path, source_dir)
                except (ImportError, AttributeError, FileNotFoundError) as e:
                    logger.warning(f"Error loading function '{func_spec}' from module '{module_path}' (package_path '{package_path}')): {e}")
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