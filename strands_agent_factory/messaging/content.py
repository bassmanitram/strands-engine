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

from strands_agent_factory.core.types import PathLike

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
    """
    logger.trace("guess_mimetype called with file_path='{}'", file_path)
    
    mimetype, _ = mimetypes.guess_type(str(file_path))
    result = mimetype or 'application/octet-stream'
    
    logger.debug("guess_mimetype returning: {}", result)
    return result


def is_likely_text_file(file_path: PathLike) -> bool:
    """
    Determine if a file is likely to contain text content.
    
    Uses a combination of file extension analysis and content sampling
    to determine if a file should be treated as text or binary.

    Args:
        file_path: Path to the file to check

    Returns:
        bool: True if the file is likely text, False otherwise
    """
    logger.trace("is_likely_text_file called with file_path='{}'", file_path)
    
    path = Path(file_path)

    # Check if file exists and is a regular file
    if not path.exists() or not path.is_file():
        logger.debug("is_likely_text_file returning False (file does not exist or not regular file)")
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
        logger.debug("is_likely_text_file returning True (known text extension: {})", path.suffix.lower())
        return True

    # Check for files without extensions that are commonly text
    if not path.suffix:
        common_text_names = {
            'readme', 'license', 'changelog', 'authors', 'contributors', 'makefile',
            'dockerfile', 'jenkinsfile', 'vagrantfile', 'gemfile', 'rakefile', 'procfile'
        }
        if path.name.lower() in common_text_names:
            logger.debug("is_likely_text_file returning True (common text filename: {})", path.name.lower())
            return True

    # For small files, do a quick binary check
    try:
        if path.stat().st_size > 1024 * 1024:  # Skip files larger than 1MB
            logger.debug("is_likely_text_file returning False (file too large: {} bytes)", path.stat().st_size)
            return False

        with open(path, 'rb') as f:
            chunk = f.read(1024)  # Read first 1KB

        # Check for null bytes (common in binary files)
        if b'\x00' in chunk:
            logger.debug("is_likely_text_file returning False (null bytes found)")
            return False

        # Check if most bytes are printable ASCII or common UTF-8
        try:
            chunk.decode('utf-8')
            logger.debug("is_likely_text_file returning True (valid UTF-8)")
            return True
        except UnicodeDecodeError:
            # Try to decode as latin-1 (more permissive)
            try:
                chunk.decode('latin-1')
                # Check if it looks like text (mostly printable characters)
                printable_count = sum(1 for b in chunk if 32 <= b <= 126 or b in (9, 10, 13))
                ratio = printable_count / len(chunk)
                result = ratio > 0.7
                logger.debug("is_likely_text_file returning {} (printable ratio: {})", result, ratio)
                return result
            except UnicodeDecodeError:
                logger.debug("is_likely_text_file returning False (decode failed)")
                return False

    except (OSError, IOError) as e:
        logger.debug("is_likely_text_file returning False (IO error: {})", e)
        return False


def paths_to_file_references(file_paths: List[Tuple[PathLike, Optional[str]]]) -> List[str]:
    """
    Convert a list of file paths and mimetypes to file() reference strings.
    
    Takes a list of (path, mimetype) tuples and converts them into a list
    of file() reference strings that can be used with generate_llm_messages().
    
    Args:
        file_paths: List of (file_path, optional_mimetype) tuples
        
    Returns:
        List[str]: List of file() reference strings
    """
    if logger.level('TRACE').no >= logger._core.min_level:
        logger.trace("paths_to_file_references called with {} file paths", len(file_paths))
    
    if not file_paths:
        logger.debug("paths_to_file_references returning empty list (no file paths)")
        return []
    
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
    
    logger.debug("paths_to_file_references returning {} references", len(references))
    return references


# ============================================================================
# Schema Manipulation
# ============================================================================

def recursively_remove(obj: Union[Dict[str, Any], List[Any]], key_to_remove: str) -> None:
    """
    Recursively remove a key from nested dictionaries and lists.
    
    This utility is used to clean tool schemas for compatibility with different
    LLM providers. The function modifies the input object in-place.
    
    Args:
        obj: Dictionary or list to process (modified in-place)
        key_to_remove: Key to remove from all nested dictionaries
    """
    logger.trace("recursively_remove called with obj type={}, key_to_remove='{}'", type(obj).__name__, key_to_remove)
    
    if isinstance(obj, dict):
        # Remove the key if it exists
        if key_to_remove in obj:
            del obj[key_to_remove]
            logger.trace("Removed key '{}' from dict", key_to_remove)
        
        # Recursively process all values
        for value in obj.values():
            recursively_remove(value, key_to_remove)
            
    elif isinstance(obj, list):
        # Recursively process all items in the list
        for item in obj:
            recursively_remove(item, key_to_remove)
    
    logger.trace("recursively_remove completed for key '{}'", key_to_remove)


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
    """
    logger.trace("load_structured_file called with file_path='{}', file_format='{}'", file_path, file_format)
    
    path = Path(file_path)
    if not path.exists():
        logger.error(f"Configuration file not found: {file_path}")
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    if file_format == 'auto':
        file_format = 'yaml' if path.suffix.lower() in ('.yaml', '.yml') else 'json'
        logger.debug("Auto-detected file format: {}", file_format)

    try:
        with open(path, 'r', encoding='utf-8') as f:
            result = _FILE_PARSER[file_format](f)
            result = result if result is not None else {}
            logger.debug("load_structured_file returning config with {} top-level keys", len(result))
            return result
    except yaml.YAMLError as e:
        error_msg = f"Invalid YAML in {file_path}: {e}"
        logger.error(error_msg)
        raise yaml.YAMLError(error_msg) from e
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in {file_path}: {e}"
        logger.error(error_msg)
        raise json.JSONDecodeError(error_msg, doc="", pos=0) from e
    except Exception as e:
        error_msg = f"Problem loading file {file_path}: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e


# ============================================================================
# File Content Processing
# ============================================================================

def load_file_content(file_path: PathLike, content_type: str = 'auto') -> Union[bytes, str]:
    """
    Load file contents with format detection.

    Args:
        file_path: Path to the file
        content_type: 'text', 'binary', or 'auto' (detect from file analysis)

    Returns:
        Union[bytes, str]: File content as bytes or string depending on content_type

    Raises:
        FileNotFoundError: If file doesn't exist
        OSError: If file cannot be read
    """
    logger.trace("load_file_content called with file_path='{}', content_type='{}'", file_path, content_type)
    
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    if content_type == 'auto':
        content_type = 'text' if is_likely_text_file(path) else 'binary'
        logger.debug("Auto-detected content type: {}", content_type)

    try:
        if content_type == "text":
            with open(path, 'r', errors='replace') as f:
                content = f.read()
                logger.debug("load_file_content returning text content ({} chars)", len(content))
                return content
        else:
            with open(path, 'rb') as f:
                content = f.read()
                logger.debug("load_file_content returning binary content ({} bytes)", len(content))
                return content
    except OSError as e:
        error_msg = f"Error reading file {file_path}: {e}"
        logger.error(error_msg)
        raise OSError(error_msg) from e


DOCUMENT_TYPES = [ 'pdf', 'csv', 'doc', 'docx', 'xls', 'xlsx', 'html', 'txt', 'md' ]


def generate_file_content_block(file_path: Path, mimetype: str) -> Optional[Dict[str, Any]]:
    """
    Generate a content block for a file based on its type and content.
    
    Args:
        file_path: Path to the file to process
        mimetype: MIME type of the file
        
    Returns:
        Optional[Dict[str, Any]]: Content block or None if processing failed
    """
    logger.trace("generate_file_content_block called with file_path='{}', mimetype='{}'", file_path, mimetype)
    
    # Skip files that exceed the size limit
    if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
        logger.warning(f"Skipping file '{file_path}' because it exceeds the {MAX_FILE_SIZE_BYTES / (1024*1024):.0f}MB size limit.")
        result = {
            "type": "text",
            "text": f"\n[Content of file '{file_path.name}' was skipped because it is too large.]\n"
        }
        logger.debug("generate_file_content_block returning size limit warning block")
        return result

    detected_mimetype = mimetype or guess_mimetype(file_path) or "application/octet-stream"
    format = (mimetypes.guess_extension(detected_mimetype) or ".bin")[1:]
    likely_text = is_likely_text_file(file_path)
    file_bytes = load_file_content(file_path, 'binary')
    
    logger.debug("File analysis: mimetype={}, format={}, likely_text={}, size={}", detected_mimetype, format, likely_text, len(file_bytes))
    
    # Video files
    if detected_mimetype.startswith("video/"):
        result = {
            "video": {
                "format": format,
                "source": {"bytes": file_bytes}
            }
        }
        logger.debug("generate_file_content_block returning video block")
        return result

    # Image files
    if detected_mimetype.startswith("image/"):
        result = {
            "image": {
                "format": format,
                "source": {"bytes": file_bytes}
            }
        }
        logger.debug("generate_file_content_block returning image block")
        return result

    # Known document types
    if format in DOCUMENT_TYPES:
        result = {
            "document": {
                "name": str(file_path),
                "format": format,
                "source": {"bytes": file_bytes}
            }
        }
        logger.debug("generate_file_content_block returning document block")
        return result

    # Other text files
    if likely_text:
        result = {
            "document": {
                "name": str(file_path),
                "format": "txt",
                "source": {"bytes": file_bytes}
            }
        }
        logger.debug("generate_file_content_block returning text document block")
        return result

    # Fallback: treat as binary image
    result = {
        "image": {
            "format": format,
            "source": {"bytes": file_bytes}
        }
    }
    logger.debug("generate_file_content_block returning fallback image block")
    return result


def files_to_content_blocks(
    files: List[tuple[str, str]],
    max_files: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Convert a list of (filepath, mimetype) tuples to content blocks.
    
    This function is the main interface for converting file uploads into
    content blocks that can be consumed by strands-agents.
    
    Args:
        files: List of (filepath, mimetype) tuples to process
        max_files: Maximum number of files to process (optional)

    Returns:
        List[Dict[str, Any]]: List of content blocks ready for agent consumption
    """
    if logger.level('TRACE').no >= logger._core.min_level:
        logger.trace("files_to_content_blocks called with {} files, max_files={}", len(files), max_files)
    
    if not files:
        logger.debug("files_to_content_blocks returning empty list (no files)")
        return []

    content_blocks = []
    processed_count = 0

    for file_path_str, mimetype in files:
        if max_files and processed_count >= max_files:
            logger.debug("Reached max_files limit ({}), stopping processing", max_files)
            break

        file_path = Path(file_path_str)

        # Process the file
        file_block = generate_file_content_block(file_path, mimetype)
        if file_block:
            content_blocks.append(file_block)
            processed_count += 1

    logger.debug("files_to_content_blocks returning {} content blocks", len(content_blocks))
    return content_blocks