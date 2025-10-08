"""
Utility functions for strands_agent_factory operations.

This module provides common utility functions used throughout the strands_agent_factory
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
from typing import Any, Dict, List, Optional, Tuple, Union

from loguru import logger
import yaml

from strands_agent_factory.ptypes import PathLike

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

def paths_to_file_references(file_paths: List[Tuple[PathLike, Optional[str]]]) -> str:
    """
    Convert a list of file paths and mimetypes to file() reference string.
    
    Takes a list of (path, mimetype) tuples and converts them into a string
    containing space-separated file() references that can be used with
    generate_llm_messages().
    
    Args:
        file_paths: List of (file_path, optional_mimetype) tuples
        
    Returns:
        list file() references separated
        
    Example:
        >>> paths = [("doc.txt", "text/plain"), ("data.json", None)]
        >>> result = paths_to_file_references(paths)
        >>> print(result)
        ["file('doc.txt', 'text/plain')", "file('data.json')"]
        
        >>> # Can be used with generate_llm_messages
        >>> message = generate_llm_messages(f"Process {result}")
    """
    if not file_paths:
        return ""
    
    references = []
    for file_path, mimetype in file_paths:
        path_str = str(file_path)
        
        if mimetype:
            # Include mimetype with single quotes
            ref = f"file('{path_str}', '{mimetype}')"
        else:
            # Just the file path
            ref = f"file('{path_str}')"
        
        references.append(ref)
    
    return references

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

def load_file_content(file_path: PathLike, content_type: str = 'auto') -> Union[bytes, str]:
    """
    Load file contents with format detection and caching.

    Args:
        file_path: Path to the file
        content_type: 'text', 'binary', or 'auto' (detect from file analysis)

    Returns:
        Dictionary with 'type' and 'content' keys, plus optional metadata

    Raises:
        FileNotFoundError: If file doesn't exist
        OSError: If file cannot be read
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if content_type == 'auto':
        content_type = 'text' if is_likely_text_file(path) else 'binary'

    try:
        if content_type == "text":
            with open(path, 'r', errors='replace') as f:
                return f.read()
        else:
            with open(path, 'rb') as f:
                return f.read()
    except OSError as e:
        raise OSError(f"Error reading file {file_path}: {e}")

DOCUMENT_TYPES = [ 'pdf', 'csv', 'doc', 'docx', 'xls', 'xlsx', 'html', 'txt', 'md' ]

def generate_file_content_block(file_path: Path, mimetype: str) -> Optional[Dict[str, Any]]:
    # Skip files that exceed the size limit
    if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
        logger.warning(f"Skipping file '{file_path}' because it exceeds the {MAX_FILE_SIZE_BYTES / (1024*1024):.0f}MB size limit.")
        return {
            "type": "text",
            "text": f"\n[Content of file '{file_path.name}' was skipped because it is too large.]\n"
        }

    detected_mimetype = mimetype or guess_mimetype(file_path) or "application/octet-stream"
    format = (mimetypes.guess_extension(detected_mimetype) or ".bin")[1:]
    likely_text = is_likely_text_file(file_path)
    file_bytes = load_file_content(file_path, 'binary')
    
    # Video files
    if detected_mimetype.startswith("video/"):
        return {
            "video": {
                "format": format,
                "source": {"bytes": file_bytes}
            }
        }

    # Image files
    if detected_mimetype.startswith("image/"):
        return {
            "image": {
                "format": format,
                "source": {"bytes": file_bytes}
            }
        }

    # Known document types
    if format in DOCUMENT_TYPES:
        return {
            "document": {
                "name": str(file_path),
                "format": format,
                "source": {"bytes": file_bytes}
            }
        }

    # Other text files
    if likely_text:
        return {
            "document": {
                "name": str(file_path),
                "format": "txt",
                "source": {"bytes": file_bytes}
            }
        }

    # Fallback: treat as binary image
    return {
        "image": {
            "format": format,
            "source": {"bytes": file_bytes}
        }
    }

def files_to_content_blocks(
    files: List[tuple[str, str]],
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

        # Process the file
        file_block = generate_file_content_block(file_path, mimetype)
        if file_block:
            content_blocks.append(file_block)
            processed_count += 1

    return content_blocks