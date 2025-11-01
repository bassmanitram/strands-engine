"""
Python tool utilities for strands_agent_factory.

This module provides utilities for dynamically importing and loading Python tools
from modules and packages. It supports both installed packages and local modules
with flexible path resolution.
"""

import importlib
import os
import sys
from pathlib import Path
from typing import Any, Callable, Optional

from loguru import logger


def import_python_item(
    base_module: str,
    item_sub_path: str,
    package_path: Optional[str] = None,
    base_path: Optional[str] = None,
) -> Any:
    """
    Dynamically load a Python item (function, class, or module) from a specified path.

    This function provides flexible loading of Python items with support for both
    standard Python import paths and custom package locations. It handles two
    main scenarios:

    1. Custom path loading: When package_path is provided, loads modules directly
       from the filesystem without modifying sys.path
    2. Standard import: Uses Python's standard import mechanism when no custom
       path is specified

    The function automatically handles both module imports and attribute access,
    trying to import the full path as a module first, then falling back to
    importing the parent module and accessing the item as an attribute.

    Args:
        base_module: The first part of the module's dotted path (e.g., 'my_app.lib')
        item_sub_path: The second part of the path, including submodules and the
                      item name (e.g., 'utils.helpers.my_func', or 'utils.helpers')
        package_path: Optional relative path to a directory that should be
                     treated as the root for the import. If None, Python's
                     standard import search paths (sys.path) are used
        base_path: Optional base directory to resolve package_path against

    Returns:
        Any: Reference to the dynamically loaded item (function, class, module, etc.)

    Raises:
        ValueError: If the item path format is invalid
        FileNotFoundError: If custom path is specified but module file not found
        ImportError: If module cannot be imported or loaded
        AttributeError: If item cannot be found in the module

    Examples:
        Standard import::

            # Load function from installed package
            func = import_python_item("mypackage.utils", "helper_function")

        Custom path import::

            # Load from local directory
            tool = import_python_item("tools.math", "calculator",
                                    package_path="./local_tools",
                                    base_path="/project/root")
    """
    logger.trace(
        "import_python_item called with base_module='{}', item_sub_path='{}', package_path='{}', base_path='{}'",
        base_module,
        item_sub_path,
        package_path,
        base_path,
    )

    # 1. Combine the inputs into a full dotted path and separate module from attribute
    full_item_path = "{}.{}".format(base_module, item_sub_path)

    try:
        full_module_path, item_name = full_item_path.rsplit(".", 1)
        logger.debug(
            "Loading item '{}' from module '{}' (base_path='{}', package_path='{}')",
            item_name,
            full_module_path,
            base_path,
            package_path,
        )
    except ValueError as e:
        logger.error("Invalid path format: '{}'", full_item_path)
        raise ValueError("Invalid path '{}'.".format(full_item_path)) from e

    # 2. Decide which loading strategy to use
    if package_path:
        logger.trace("Using custom path loading strategy")
        item = _load_from_custom_path(
            full_module_path, item_name, package_path, base_path
        )
    else:
        logger.trace("Using standard import strategy")
        item = _load_from_standard_import(full_item_path, full_module_path, item_name)

    logger.trace(
        "import_python_item completed successfully, returning item type: {}",
        type(item).__name__,
    )
    return item


def _load_from_custom_path(
    full_module_path: str, item_name: str, package_path: str, base_path: Optional[str]
) -> Any:
    """
    Load item from custom filesystem path without modifying sys.path.

    Args:
        full_module_path: Full dotted module path
        item_name: Name of the item to extract from the module
        package_path: Relative path to the package directory
        base_path: Optional base directory for resolving package_path

    Returns:
        Any: The loaded item

    Raises:
        FileNotFoundError: If module file doesn't exist
        ImportError: If module cannot be loaded
        AttributeError: If item cannot be found in module
    """
    logger.trace("_load_from_custom_path called")

    # --- SCENARIO 1: Custom path is provided ---
    # Translate dotted module path to a relative file path
    relative_file_path = full_module_path.replace(".", os.path.sep) + ".py"
    absolute_file_path = os.path.join(base_path or "", package_path, relative_file_path)

    logger.debug("Resolved module file path: {}", absolute_file_path)

    if not os.path.isfile(absolute_file_path):
        logger.error("Module file not found at: {}", absolute_file_path)
        raise FileNotFoundError(f"Module file not found at: {absolute_file_path}")

    # Load the module directly from its file path without using sys.path
    try:
        spec = importlib.util.spec_from_file_location(
            full_module_path, absolute_file_path
        )
        if spec is None or spec.loader is None:
            logger.error("Could not create module spec from {}", absolute_file_path)
            raise ImportError(f"Could not load module from {absolute_file_path}")

        logger.trace("Creating module from spec")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        logger.trace("Extracting item '{}' from loaded module", item_name)
        item = getattr(module, item_name)

        logger.debug("Successfully loaded item '{}' from custom path", item_name)
        return item

    except Exception as e:
        logger.error("Error loading module from {}: {}", absolute_file_path, e)
        raise ImportError("Could not load module from {absolute_file_path}") from e


def _load_from_standard_import(
    full_item_path: str, full_module_path: str, item_name: str
) -> Any:
    """
    Load item using Python's standard import mechanism.

    Tries two approaches:
    1. Import the full path as a module (for cases where the item is a module)
    2. Import the parent module and access the item as an attribute

    Args:
        full_item_path: Complete dotted path to the item
        full_module_path: Dotted path to the parent module
        item_name: Name of the item to extract

    Returns:
        Any: The loaded item

    Raises:
        ImportError: If neither import strategy succeeds
        AttributeError: If item cannot be found in the parent module
    """
    logger.trace("_load_from_standard_import called")

    # --- SCENARIO 2: Use standard import mechanism ---
    try:
        # First, try to import the full path as a module (for cases where the item is a module)
        logger.trace("Attempting to import full path as module: {}", full_item_path)
        item = importlib.import_module(full_item_path)
        logger.debug("Successfully imported '{}' as module", full_item_path)
        return item

    except ImportError as e:
        logger.trace("Full path import failed, trying parent module approach: {}", e)

        try:
            # If that fails, import the base module and get the attribute from it
            logger.trace("Importing parent module: {}", full_module_path)
            module = importlib.import_module(full_module_path)

            logger.trace("Extracting item '{}' from parent module", item_name)
            item = getattr(module, item_name)

            logger.debug(
                "Successfully loaded item '{}' from parent module '{}'",
                item_name,
                full_module_path,
            )
            return item

        except (ImportError, AttributeError) as e2:
            logger.error(
                "Cannot load {}: parent module import failed with {}",
                full_item_path,
                e2,
            )
            raise ImportError(f"Cannot load {full_item_path}: {e2}") from e2
