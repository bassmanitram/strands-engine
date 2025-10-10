"""
Core utility functions for strands_agent_factory.

This module provides general-purpose utility functions used across
the strands_agent_factory codebase.
"""

import collections.abc
from typing import Any, Dict

from loguru import logger

# A sensible maximum length for tool input values
MAX_VALUE_LENGTH = 90


def clean_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove None values from a dictionary (shallow operation).
    
    Args:
        d: Dictionary to clean
        
    Returns:
        New dictionary with None values removed
    """
    logger.trace(f"clean_dict called with dict containing {len(d)} items")
    
    result = {k: v for k, v in d.items() if v is not None}
    
    logger.trace(f"clean_dict completed, returning dict with {len(result)} items")
    return result


def print_structured_data(data: Any, indent_level: int = 0, initial_max_len: int = MAX_VALUE_LENGTH, printer=print):
    """
    Print structured data with hierarchical formatting and intelligent truncation.
    
    Formatting rules:
    - Dictionaries: Keys sorted alphabetically, values indented recursively
    - Elementary types (int, float, bool, None): Printed without truncation
    - Other types (str, list, objects): Converted to string and potentially truncated
    - Truncation length decreases with indentation depth
    - Set initial_max_len to -1 to disable all truncation
    
    Args:
        data: The data to print (any type)
        indent_level: Current indentation level for recursive calls (default: 0)
        initial_max_len: Maximum string length at top level, -1 for no limit (default: 90)
        printer: Function used for output (default: print)
        
    Note:
        For non-dictionary top-level data, prints the value directly without key prefix.
        Recursive calls automatically increase indentation and reduce truncation length.
    """
    logger.trace(f"print_structured_data called with data type: {type(data).__name__}, indent_level: {indent_level}, initial_max_len: {initial_max_len}")
    
    indent_str = "  " * indent_level

    # Determine effective maximum length for truncation
    if initial_max_len == -1:
        effective_max_len = float('inf')  # No truncation
    else:
        # Reduce effective max length for truncation as indentation increases.
        # Ensures at least 6 chars for "abc..." to accommodate truncation ellipsis.
        effective_max_len = max(6, initial_max_len - (indent_level * 8))

    def _format_and_print_value(value_to_format: Any, prefix: str = ""):
        """Format and print a single value according to the formatting rules."""
        logger.trace(f"_format_and_print_value called with value type: {type(value_to_format).__name__}, prefix: '{prefix}'")
        
        if value_to_format is None:
            printer(f"{indent_str}{prefix}None")
        elif isinstance(value_to_format, (int, float, bool)):
            # Elementary types (int, float, bool) are printed without truncation
            printer(f"{indent_str}{prefix}{str(value_to_format)}")
        elif isinstance(value_to_format, collections.abc.Mapping):
            printer(f"{indent_str}{prefix}")  # Print key then recurse on next line
            print_structured_data(value_to_format, indent_level + 1, initial_max_len, printer)
        else:  # Handle all other types (strings, lists, objects, etc.) with potential truncation
            value_as_str = str(value_to_format)
            display_value = value_as_str
            # Apply truncation only if effective_max_len is not infinite
            if effective_max_len != float('inf') and len(value_as_str) > effective_max_len:
                display_value = value_as_str[:effective_max_len - 3] + "..."
            printer(f"{indent_str}{prefix}{display_value}")
        
        logger.trace("_format_and_print_value completed")

    if isinstance(data, collections.abc.Mapping):
        # Top-level 'data' is a dictionary, iterate through its sorted properties
        for key, value in sorted(data.items()):
            key_name = str(key)
            _format_and_print_value(value, prefix=f"{key_name}: ")
    else:
        # Top-level 'data' is not a dictionary. Apply value rules directly without a key prefix.
        _format_and_print_value(data)
    
    logger.trace("print_structured_data completed")