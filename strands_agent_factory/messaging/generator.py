"""
LLM message generator for strands_agent_factory.

This module provides functionality to generate strands-formatted message lists
from input strings containing text and file references. File references use
the format file('file_GLOB'[,optional_mimetype]) and are resolved to actual
file content blocks.
"""

import glob
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from ..core.types import PathLike
from .content import generate_file_content_block


def generate_llm_messages(input_string: str) -> List[Dict[str, Any]]:
    """
    Generate a strands-formatted message list from input string with file references.

    Parses an input string containing text and file() references, resolving
    file globs and creating appropriate content blocks. Returns a single user
    message containing all text and file content blocks in order.

    File reference format: file('file_glob'[,mimetype])
    Examples:
        - file('document.txt')
        - file('*.py', 'text/plain')
        - file('data/*.json', 'application/json')

    Args:
        input_string: String containing text and file() references

    Returns:
        List containing single user message dict with content blocks
    """
    if logger.level("TRACE").no >= logger._core.min_level:
        logger.trace(
            "generate_llm_messages called with input length: {}", len(input_string)
        )

    # Parse file references and text segments
    file_refs = _parse_file_references(input_string)
    logger.debug("Found {} file references", len(file_refs))

    # Build content blocks in order
    content_blocks = []
    last_end = 0

    for glob_pattern, mimetype, start_pos, end_pos in file_refs:
        # Add text content before this file reference
        if start_pos > last_end:
            text_segment = input_string[last_end:start_pos].strip()
            if text_segment:
                content_blocks.append(_create_text_content_block(text_segment))
                if logger.level("TRACE").no >= logger._core.min_level:
                    logger.trace("Added text block: {}...", text_segment[:50])

        # Resolve file glob and create file content blocks
        file_paths = _resolve_file_glob(glob_pattern, mimetype)
        if file_paths:
            file_blocks = _create_file_content_blocks(file_paths)
            content_blocks.extend(file_blocks)
            logger.debug(
                "Added {} file blocks from glob: {}", len(file_blocks), glob_pattern
            )
        else:
            # Add explanatory text if no files resolved
            error_text = f"No files found matching pattern: {glob_pattern}"
            content_blocks.append(_create_text_content_block(f"[{error_text}]"))
            logger.warning(error_text)

        last_end = end_pos

    # Add any remaining text after the last file reference
    if last_end < len(input_string):
        text_segment = input_string[last_end:].strip()
        if text_segment:
            content_blocks.append(_create_text_content_block(text_segment))
            if logger.level("TRACE").no >= logger._core.min_level:
                logger.trace("Added final text block: {}...", text_segment[:50])

    # If no content blocks were created, add the entire input as text
    if not content_blocks:
        if input_string.strip():
            content_blocks.append(_create_text_content_block(input_string.strip()))
        else:
            content_blocks.append(_create_text_content_block(""))

    # Return single user message with all content blocks
    message = {"role": "user", "content": content_blocks}

    logger.debug(
        "generate_llm_messages returning message with {} content blocks",
        len(content_blocks),
    )
    return [message]


def _parse_file_references(text: str) -> List[Tuple[str, Optional[str], int, int]]:
    """
    Parse file() references from input text.

    Finds all file() references using regex and extracts the glob pattern
    and optional mimetype from each reference.

    Args:
        text: Input text to parse

    Returns:
        List of tuples: (glob_pattern, mimetype, start_pos, end_pos)
        where mimetype is None if not specified
    """
    if logger.level("TRACE").no >= logger._core.min_level:
        logger.trace("_parse_file_references called with text length: {}", len(text))

    # Regex pattern to match file('glob'[,mimetype])
    # Supports both single and double quotes, optional mimetype
    pattern = r"file\(\s*['\"]([^'\"]+)['\"](?:\s*,\s*['\"]([^'\"]*)['\"])?\s*\)"

    file_refs = []
    for match in re.finditer(pattern, text, re.IGNORECASE):
        glob_pattern = match.group(1)
        mimetype = match.group(2) if match.group(2) else None
        start_pos = match.start()
        end_pos = match.end()

        file_refs.append((glob_pattern, mimetype, start_pos, end_pos))
        logger.trace(
            "Parsed file reference: glob='{}', mimetype='{}'", glob_pattern, mimetype
        )

    logger.debug("_parse_file_references returning {} file references", len(file_refs))
    return file_refs


def _resolve_file_glob(
    glob_pattern: str, mimetype: Optional[str]
) -> List[Tuple[str, Optional[str]]]:
    """
    Resolve a file glob pattern to actual file paths.

    Uses glob.glob to expand patterns and filters out non-existent files.
    Returns list of (filepath, mimetype) tuples where the same mimetype
    is used for all resolved files from the glob.

    Args:
        glob_pattern: File glob pattern to resolve
        mimetype: Optional mimetype to use for all resolved files

    Returns:
        List of (filepath, mimetype) tuples for existing files
    """
    logger.trace(
        "_resolve_file_glob called with glob_pattern='{}', mimetype='{}'",
        glob_pattern,
        mimetype,
    )

    try:
        # Resolve glob pattern
        matched_paths = glob.glob(glob_pattern, recursive=True)
        logger.debug("Glob matched {} paths", len(matched_paths))

        # Filter to existing files only
        existing_files = []
        for path in matched_paths:
            path_obj = Path(path)
            if path_obj.exists() and path_obj.is_file():
                existing_files.append((str(path_obj.resolve()), mimetype))
                logger.trace("Resolved file: {}", path_obj.resolve())
            else:
                logger.warning(f"File does not exist or is not a file: {path}")

        logger.debug(
            "_resolve_file_glob returning {} existing files", len(existing_files)
        )
        return existing_files

    except Exception as e:
        logger.error(f"Error resolving glob pattern '{glob_pattern}': {e}")
        return []


def _create_text_content_block(text: str) -> Dict[str, str]:
    """
    Create a text content block for strands message format.

    Args:
        text: Text content for the block

    Returns:
        Dict with text content block format: {"text": "..."}
    """
    if logger.level("TRACE").no >= logger._core.min_level:
        logger.trace(
            "_create_text_content_block called with text length: {}", len(text)
        )

    result = {"text": text}

    logger.debug("_create_text_content_block returning text block")
    return result


def _create_file_content_blocks(
    file_paths: List[Tuple[str, Optional[str]]],
) -> List[Dict[str, Any]]:
    """
    Create file content blocks from resolved file paths.

    Uses utils.generate_file_content_block to create content blocks for each file.
    Handles IO errors gracefully by creating explanatory text blocks instead.

    Args:
        file_paths: List of (filepath, mimetype) tuples

    Returns:
        List of content blocks (mix of file blocks and error text blocks)
    """
    if logger.level("TRACE").no >= logger._core.min_level:
        logger.trace(
            "_create_file_content_blocks called with {} file paths", len(file_paths)
        )

    content_blocks = []

    for file_path, mimetype in file_paths:
        try:
            logger.debug(
                "Creating content block for file: {} (mimetype: {})",
                file_path,
                mimetype,
            )

            path_obj = Path(file_path)
            # Use mimetype from glob or detect automatically (pass None to let utils handle it)
            file_block = generate_file_content_block(path_obj, mimetype or "")

            if file_block:
                content_blocks.append(file_block)
                logger.trace("Successfully created content block for: {}", file_path)
            else:
                # generate_file_content_block returned None due to error
                error_text = f"Failed to process file: {file_path}"
                logger.warning(error_text)
                content_blocks.append(_create_text_content_block(f"[{error_text}]"))

        except Exception as e:
            # Create explanatory text block for failed file
            error_text = f"Failed to read file '{file_path}': {str(e)}"
            logger.error(error_text)
            content_blocks.append(_create_text_content_block(f"[{error_text}]"))

    logger.debug(
        "_create_file_content_blocks returning {} content blocks", len(content_blocks)
    )
    return content_blocks
