"""
Utility functions for strands_engine operations.

This module provides common utility functions used throughout the strands_engine
package, including file processing, content handling, MIME type detection,
and configuration parsing utilities.

The utilities are organized into several categories:
- File type detection and content processing
- Configuration file loading and parsing
- Content block generation for agent consumption
- Binary file handling with base64 encoding
- Schema manipulation for framework compatibility

These utilities support the engine's file upload capabilities and tool
configuration processing while maintaining compatibility with strands-agents
content format requirements.
"""

import base64
import json
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from loguru import logger
import yaml

from strands_engine.ptypes import PathLike

# ============================================================================
# Constants
# ============================================================================

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
"""Maximum file size (10MB) for processing to prevent memory issues."""


# ============================================================================
# MIME Type and File Detection
# ============================================================================

def guess_mimetype(file_path: PathLike) -> str:
    """
    Guess the MIME type of a file based on its extension.
    
    Uses the standard mimetypes library to determine the MIME type,
    falling back to a generic binary type if detection fails.

    Args:
        file_path: Path to the file to analyze

    Returns:
        str: MIME type string, defaults to 'application/octet-stream'
        
    Example:
        >>> guess_mimetype("document.pdf")
        'application/pdf'
        >>> guess_mimetype("unknown.xyz")
        'application/octet-stream'
    """
    mimetype, _ = mimetypes.guess_type(str(file_path))
    return mimetype or 'application/octet-stream'


def is_likely_text_file(file_path: PathLike) -> bool:
    """
    Determine if a file is likely to contain text content.
    
    Uses a combination of file extension analysis and content sampling
    to determine if a file should be treated as text or binary.
    
    The function checks:
    1. File extension against known text file types
    2. Common text file names without extensions
    3. Binary content detection via null byte scanning
    4. UTF-8/Latin-1 decoding attempts with printable character analysis

    Args:
        file_path: Path to the file to check

    Returns:
        bool: True if the file is likely text, False otherwise
        
    Note:
        Files larger than 1MB are assumed to be binary for performance.
        The function performs a quick scan of the first 1KB for detection.
    """
    path = Path(file_path)

    # Check if file exists and is a regular file
    if not path.exists() or not path.is_file():
        return False

    # Common text file extensions
    text_extensions = {
        '.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
        '.ini', '.cfg', '.con', '.log', '.csv', '.tsv', '.sql', '.sh', '.bat', '.ps1',
        '.c', '.cpp', '.h', '.hpp', '.java', '.cs', '.php', '.rb', '.go', '.rs', '.swift',
        '.kt', '.scala', '.clj', '.hs', '.ml', '.fs', '.vb', '.pl', '.r', '.m', '.tex',
        '.rst', '.adoc', '.org', '.wiki', '.dockerfile', '.gitignore', '.gitattributes',
        '.editorconfig', '.eslintrc', '.prettierrc', '.babelrc', '.tsconfig', '.package',
        '.lock', '.toml', '.properties', '.env', '.example', '.sample', '.template'
    }

    # Check extension
    if path.suffix.lower() in text_extensions:
        return True

    # Check for files without extensions that are commonly text
    if not path.suffix:
        common_text_names = {
            'readme', 'license', 'changelog', 'authors', 'contributors', 'makefile',
            'dockerfile', 'jenkinsfile', 'vagrantfile', 'gemfile', 'rakefile', 'procfile'
        }
        if path.name.lower() in common_text_names:
            return True

    # For small files, do a quick binary check
    try:
        if path.stat().st_size > 1024 * 1024:  # Skip files larger than 1MB
            return False

        with open(path, 'rb') as f:
            chunk = f.read(1024)  # Read first 1KB

        # Check for null bytes (common in binary files)
        if b'\x00' in chunk:
            return False

        # Check if most bytes are printable ASCII or common UTF-8
        try:
            chunk.decode('utf-8')
            return True
        except UnicodeDecodeError:
            # Try to decode as latin-1 (more permissive)
            try:
                chunk.decode('latin-1')
                # Check if it looks like text (mostly printable characters)
                printable_count = sum(1 for b in chunk if 32 <= b <= 126 or b in (9, 10, 13))
                return printable_count / len(chunk) > 0.7
            except UnicodeDecodeError:
                return False

    except (OSError, IOError):
        return False


# ============================================================================
# Schema Manipulation
# ============================================================================

def recursively_remove(obj: Union[Dict[str, Any], List[Any]], key_to_remove: str) -> None:
    """
    Recursively remove a key from nested dictionaries and lists.
    
    This utility is used to clean tool schemas for compatibility with different
    LLM providers. For example, removing 'additionalProperties' for Google
    VertexAI compatibility or other provider-specific schema modifications.
    
    The function modifies the input object in-place, traversing all nested
    dictionaries and lists to remove the specified key wherever it appears.
    
    Args:
        obj: Dictionary or list to process (modified in-place)
        key_to_remove: Key to remove from all nested dictionaries
        
    Example:
        >>> schema = {"properties": {"name": {"type": "string", "additionalProperties": False}}}
        >>> recursively_remove(schema, "additionalProperties")
        >>> # schema now: {"properties": {"name": {"type": "string"}}}
    """
    if isinstance(obj, dict):
        # Remove the key if it exists
        if key_to_remove in obj:
            del obj[key_to_remove]
        
        # Recursively process all values
        for value in obj.values():
            recursively_remove(value, key_to_remove)
            
    elif isinstance(obj, list):
        # Recursively process all items in the list
        for item in obj:
            recursively_remove(item, key_to_remove)


# ============================================================================
# Configuration File Loading
# ============================================================================

_FILE_PARSER = {
    "json": json.load,
    "yaml": yaml.safe_load
}
"""Mapping of file formats to their respective parsing functions."""


def load_structured_file(file_path: PathLike, file_format: str = 'auto') -> Dict[str, Any]:
    """
    Load and parse structured configuration files (JSON/YAML).
    
    Provides a unified interface for loading configuration files in either
    JSON or YAML format, with automatic format detection based on file
    extension when requested.
    
    Args:
        file_path: Path to the configuration file
        file_format: File format - 'json', 'yaml', or 'auto' for auto-detection

    Returns:
        Dict[str, Any]: Parsed configuration as dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML parsing fails
        json.JSONDecodeError: If JSON parsing fails
        ValueError: If unsupported file format
        
    Example:
        >>> config = load_structured_file("config.yaml")
        >>> tools = config.get("tools", [])
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    if file_format == 'auto':
        file_format = 'yaml' if path.suffix.lower() in ('.yaml', '.yml') else 'json'

    try:
        with open(path, 'r', encoding='utf-8') as f:
            result = _FILE_PARSER[file_format](f)
            return result if result is not None else {}
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in {file_path}: {e}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {file_path}: {e}", doc="", pos=0)
    except Exception as e:
        raise ValueError(f"Problem loading file {file_path}: {e}")


# ============================================================================
# File Content Processing
# ============================================================================

def load_file_content(file_path: PathLike, content_type: str = 'auto') -> Dict[str, Any]:
    """
    Load file contents with format detection.
    
    Loads file content as either text or binary data based on the specified
    content type or automatic detection. Binary files are base64-encoded
    for safe transmission and storage.
    
    Args:
        file_path: Path to the file to load
        content_type: Content type - 'text', 'binary', or 'auto' for detection

    Returns:
        Dict[str, Any]: Dictionary with 'type', 'content', and metadata keys
        - For text files: {"type": "text", "content": str}
        - For binary files: {"type": "binary", "content": str, "encoding": "base64", "mimetype": str}

    Raises:
        FileNotFoundError: If file doesn't exist
        OSError: If file cannot be read
        
    Example:
        >>> content = load_file_content("image.png")
        >>> print(content["type"])  # "binary"
        >>> print(content["encoding"])  # "base64"
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if content_type == 'auto':
        content_type = 'text' if is_likely_text_file(path) else 'binary'

    try:
        if content_type == 'text':
            with open(path, 'r', errors='replace') as f:
                return {"type": "text", "content": f.read()}
        else:
            with open(path, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
                return {
                    "type": "binary",
                    "content": encoded,
                    "encoding": "base64",
                    "mimetype": guess_mimetype(path)
                }
    except OSError as e:
        raise OSError(f"Error reading file {file_path}: {e}")


def _process_single_file(file_path: Path, mimetype: str) -> Optional[Dict[str, Any]]:
    """
    Process a single file into a content block for agent consumption.
    
    Internal utility function that reads a file and converts it into the
    appropriate content block format expected by strands-agents. Handles
    both text and binary files, with size limits and error handling.
    
    Args:
        file_path: Path to the file to process
        mimetype: MIME type of the file

    Returns:
        Optional[Dict[str, Any]]: Content block dictionary, or None if processing fails
        - Text files: {"type": "text", "text": str}
        - Binary files: {"type": "image", "source": {"type": "base64", "media_type": str, "data": str}}
        - Large files: {"type": "text", "text": "[skipped message]"}
        
    Note:
        Files larger than MAX_FILE_SIZE_BYTES are skipped with a placeholder message.
        The function uses 'image' type for binary data as per strands conventions.
    """
    try:
        # Check file size before attempting to read
        if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
            logger.warning(f"Skipping file '{file_path}' because it exceeds the {MAX_FILE_SIZE_BYTES / (1024*1024):.0f}MB size limit.")
            return {"type": "text", "text": f"\\n[Content of file '{file_path.name}' was skipped because it is too large.]\\n"}
        
        # Let the file utility handle text vs binary detection automatically
        result = load_file_content(file_path, 'auto')

        if result['type'] == 'text':
            logger.debug(f"Reading file '{file_path}' as text.")
            return {"type": "text", "text": result['content']}
        else:
            logger.debug(f"Reading file '{file_path}' as base64-encoded binary.")
            # The 'source' dictionary is the standard way to send binary data.
            return {
                "type": "image", # This is a generic type for binary data in strands
                "source": {
                    "type": "base64",
                    "media_type": result.get('mimetype', mimetype),  # Use detected or provided
                    "data": result['content']
                }
            }
    except Exception as e:
        logger.error(f"Could not read or encode file {file_path}: {e}")
        return None


def files_to_content_blocks(
    files: List[tuple[str, str]],
    add_headers: bool = True,
    max_files: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Convert a list of (filepath, mimetype) tuples to content blocks.
    
    This function is the main interface for converting file uploads into
    content blocks that can be consumed by strands-agents. It handles both
    text and binary files, with optional headers and file count limits.
    
    Args:
        files: List of (filepath, mimetype) tuples to process
        add_headers: Whether to add file header markers (default: True)
        max_files: Maximum number of files to process (optional)

    Returns:
        List[Dict[str, Any]]: List of content blocks ready for agent consumption
        
    Example:
        >>> files = [("readme.txt", "text/plain"), ("image.png", "image/png")]
        >>> blocks = files_to_content_blocks(files)
        >>> print(len(blocks))  # 4 (2 headers + 2 content blocks)
        
    Note:
        Used by both startup file processing and inline file parsing throughout
        the engine. Content blocks follow strands-agents format conventions.
    """
    if not files:
        return []

    content_blocks = []
    processed_count = 0

    for file_path_str, mimetype in files:
        if max_files and processed_count >= max_files:
            break

        file_path = Path(file_path_str)

        # Add header if requested
        if add_headers:
            content_blocks.append({
                "type": "text",
                "text": f"\\n--- File: {file_path_str} ({mimetype}) ---\\n"
            })

        # Process the file
        file_block = _process_single_file(file_path, mimetype)
        if file_block:
            content_blocks.append(file_block)
            processed_count += 1

    return content_blocks