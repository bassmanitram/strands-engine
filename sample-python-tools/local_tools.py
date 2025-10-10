# local_tools.py
# A sample Python module with a function to be used as a tool.

import os
import glob
from typing import List
from strands import tool  # <-- Import the decorator

@tool  # <-- Apply the decorator to the function
def list_files(directory: str, filter_glob: str = "*") -> List[str]:
    """
    Lists files in a given local directory, with an optional filter.

    Args:
        directory: The path to the directory to scan.
        filter_glob: A glob pattern to filter the files by (e.g., "*.txt").

    Returns:
        A list of file paths matching the filter.
    """
    if not os.path.isdir(directory):
        return [f"Error: Directory not found at '{directory}'"]
    
    search_path = os.path.join(directory, filter_glob)
    return glob.glob(search_path)