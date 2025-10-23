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
        logger.debug("Loading item '{}' from module '{}' (base_path='{}, package_path='{}')", item_name, full_module_path, base_path, package_path)
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
            logger.error(f"Cannot load {full_item_path}")
            # If that fails, import the base module and get the attribute from it
            module = importlib.import_module(full_module_path)
            item = getattr(module, item_name)

    return item