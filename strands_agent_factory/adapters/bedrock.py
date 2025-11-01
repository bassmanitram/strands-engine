"""
AWS Bedrock framework adapter for strands_agent_factory.

This module provides the BedrockAdapter class, which enables strands_agent_factory
to work with AWS Bedrock managed AI services. AWS Bedrock provides access to
foundation models from multiple providers (Anthropic, Amazon, Cohere, etc.)
through a unified AWS API with enterprise features.

The Bedrock adapter handles:
- AWS Bedrock model instantiation and configuration
- Content adaptation for Bedrock's specific format requirements
- Tool schema compatibility with Bedrock's function calling
- AWS authentication and configuration management
- Image format validation and binary file handling

This adapter is designed for enterprise applications that need AWS integration,
compliance features, and managed model serving without direct provider APIs.
"""

import configparser
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from botocore.config import Config as BotocoreConfig
from loguru import logger
from strands.models.bedrock import BedrockModel
from strands.types.content import Messages

from ..core.types import Tool
from .base import FrameworkAdapter

# Valid image formats supported by AWS Bedrock
VALID_IMAGE_FORMATS = frozenset({"gif", "jpeg", "png", "webp"})

# Pre-compiled regex patterns for optimized name sanitization
_INVALID_CHARS_PATTERN = re.compile(r"[^a-zA-Z0-9\s\-\(\)\[\]]")
_MULTIPLE_HYPHENS_PATTERN = re.compile(r"-{2,}")  # More specific: 2 or more hyphens
_MULTIPLE_SPACES_PATTERN = re.compile(r"\s{2,}")  # More specific: 2 or more spaces

# Optimized accent-to-non-accent transformation mapping
# Using frozenset for O(1) lookups and pre-compiled translation table
_ACCENT_MAP = {
    # Latin-1 Supplement - most common European accents
    "À": "A",
    "Á": "A",
    "Â": "A",
    "Ã": "A",
    "Ä": "A",
    "Å": "A",
    "Æ": "AE",
    "Ç": "C",
    "È": "E",
    "É": "E",
    "Ê": "E",
    "Ë": "E",
    "Ì": "I",
    "Í": "I",
    "Î": "I",
    "Ï": "I",
    "Ð": "D",
    "Ñ": "N",
    "Ò": "O",
    "Ó": "O",
    "Ô": "O",
    "Õ": "O",
    "Ö": "O",
    "Ø": "O",
    "Ù": "U",
    "Ú": "U",
    "Û": "U",
    "Ü": "U",
    "Ý": "Y",
    "Þ": "TH",
    "ß": "ss",
    "à": "a",
    "á": "a",
    "â": "a",
    "ã": "a",
    "ä": "a",
    "å": "a",
    "æ": "ae",
    "ç": "c",
    "è": "e",
    "é": "e",
    "ê": "e",
    "ë": "e",
    "ì": "i",
    "í": "i",
    "î": "i",
    "ï": "i",
    "ð": "d",
    "ñ": "n",
    "ò": "o",
    "ó": "o",
    "ô": "o",
    "õ": "o",
    "ö": "o",
    "ø": "o",
    "ù": "u",
    "ú": "u",
    "û": "u",
    "ü": "u",
    "ý": "y",
    "þ": "th",
    "ÿ": "y",
    # Extended Latin-A - Central/Eastern European (most common)
    "Ā": "A",
    "ā": "a",
    "Ă": "A",
    "ă": "a",
    "Ą": "A",
    "ą": "a",
    "Ć": "C",
    "ć": "c",
    "Ĉ": "C",
    "ĉ": "c",
    "Ċ": "C",
    "ċ": "c",
    "Č": "C",
    "č": "c",
    "Ď": "D",
    "ď": "d",
    "Đ": "D",
    "đ": "d",
    "Ē": "E",
    "ē": "e",
    "Ĕ": "E",
    "ĕ": "e",
    "Ė": "E",
    "ė": "e",
    "Ę": "E",
    "ę": "e",
    "Ě": "E",
    "ě": "e",
    "Ĝ": "G",
    "ĝ": "g",
    "Ğ": "G",
    "ğ": "g",
    "Ġ": "G",
    "ġ": "g",
    "Ģ": "G",
    "ģ": "g",
    "Ĥ": "H",
    "ĥ": "h",
    "Ħ": "H",
    "ħ": "h",
    "Ĩ": "I",
    "ĩ": "i",
    "Ī": "I",
    "ī": "i",
    "Ĭ": "I",
    "ĭ": "i",
    "Į": "I",
    "į": "i",
    "İ": "I",
    "ı": "i",
    "Ĵ": "J",
    "ĵ": "j",
    "Ķ": "K",
    "ķ": "k",
    "ĸ": "k",
    "Ĺ": "L",
    "ĺ": "l",
    "Ļ": "L",
    "ļ": "l",
    "Ľ": "L",
    "ľ": "l",
    "Ŀ": "L",
    "ŀ": "l",
    "Ł": "L",
    "ł": "l",
    "Ń": "N",
    "ń": "n",
    "Ņ": "N",
    "ņ": "n",
    "Ň": "N",
    "ň": "n",
    "ŉ": "n",
    "Ō": "O",
    "ō": "o",
    "Ŏ": "O",
    "ŏ": "o",
    "Ő": "O",
    "ő": "o",
    "Œ": "OE",
    "œ": "oe",
    "Ŕ": "R",
    "ŕ": "r",
    "Ŗ": "R",
    "ŗ": "r",
    "Ř": "R",
    "ř": "r",
    "Ś": "S",
    "ś": "s",
    "Ŝ": "S",
    "ŝ": "s",
    "Ş": "S",
    "ş": "s",
    "Š": "S",
    "š": "s",
    "Ţ": "T",
    "ţ": "t",
    "Ť": "T",
    "ť": "t",
    "Ŧ": "T",
    "ŧ": "t",
    "Ũ": "U",
    "ũ": "u",
    "Ū": "U",
    "ū": "u",
    "Ŭ": "U",
    "ŭ": "u",
    "Ů": "U",
    "ů": "u",
    "Ű": "U",
    "ű": "u",
    "Ų": "U",
    "ų": "u",
    "Ŵ": "W",
    "ŵ": "w",
    "Ŷ": "Y",
    "ŷ": "y",
    "Ÿ": "Y",
    "Ź": "Z",
    "ź": "z",
    "Ż": "Z",
    "ż": "z",
    "Ž": "Z",
    "ž": "z",
}

# Pre-compile accent transformation for maximum performance
_ACCENT_TRANSLATION = str.maketrans(_ACCENT_MAP)

# Cache for common path patterns to avoid repeated processing
_PATH_CACHE = {}
_CACHE_MAX_SIZE = 1000


def _resolve_region_from_profile(
    profile_name: str, visited: Optional[Set[str]] = None
) -> Optional[str]:
    """
    Resolve AWS region from profile configuration with inheritance support.

    Reads ~/.aws/config and follows source_profile chains to find region.
    Handles circular references and malformed configurations safely.

    Args:
        profile_name: AWS profile name to look up
        visited: Set of already visited profiles (for loop detection)

    Returns:
        Region name if found, None otherwise

    Example:
        ~/.aws/config:
        [profile dev]
        source_profile = base

        [profile base]
        region = us-west-2

        >>> _resolve_region_from_profile("dev")
        'us-west-2'
    """
    if visited is None:
        visited = set()

    # Prevent infinite loops in profile chains
    if profile_name in visited:
        logger.debug(f"Circular profile reference detected: {profile_name}")
        return None
    visited.add(profile_name)

    # Locate AWS config file
    config_path = Path.home() / ".aws" / "config"
    if not config_path.exists():
        logger.debug(f"AWS config file not found: {config_path}")
        return None

    try:
        config = configparser.ConfigParser()
        config.read(config_path)

        # Determine section name (default profile has no "profile " prefix)
        section_name = (
            f"profile {profile_name}" if profile_name != "default" else "default"
        )

        if section_name not in config:
            logger.debug(f"Profile section not found: {section_name}")
            return None

        section = config[section_name]

        # Check for region in current profile
        if "region" in section:
            region = section["region"]
            logger.debug(f"Found region '{region}' in profile '{profile_name}'")
            return region

        # Follow source_profile chain if present
        if "source_profile" in section:
            source_profile = section["source_profile"]
            logger.debug(
                f"Following source_profile: {profile_name} -> {source_profile}"
            )
            return _resolve_region_from_profile(source_profile, visited)

        logger.debug(f"No region or source_profile found in profile '{profile_name}'")
        return None

    except Exception as e:
        logger.debug(f"Failed to parse AWS config for profile '{profile_name}': {e}")
        return None


def _resolve_region_name(model_config: Dict[str, Any]) -> Optional[str]:
    """
    Resolve AWS region name using standard AWS fallback hierarchy.

    Resolution order follows AWS SDK conventions:
    1. Existing 'region_name' in model_config (highest priority - never override)
    2. AWS_REGION environment variable
    3. AWS_DEFAULT_REGION environment variable
    4. AWS_PROFILE configuration file with source_profile inheritance
    5. None (allow boto3 to use its own defaults)

    Args:
        model_config: Model configuration dictionary that may contain region_name

    Returns:
        Resolved region name, or None if not determinable

    Example:
        >>> os.environ['AWS_REGION'] = 'us-east-1'
        >>> _resolve_region_name({})
        'us-east-1'

        >>> _resolve_region_name({'region_name': 'eu-west-1'})
        'eu-west-1'  # Existing value preserved
    """
    # 1. Don't override existing region_name
    if "region_name" in model_config:
        existing = model_config["region_name"]
        logger.debug(f"Using existing region_name from config: {existing}")
        return existing

    # 2. Check AWS_REGION environment variable
    region = os.environ.get("AWS_REGION")
    if region:
        logger.debug(f"Resolved region_name from AWS_REGION: {region}")
        return region

    # 3. Check AWS_DEFAULT_REGION environment variable
    region = os.environ.get("AWS_DEFAULT_REGION")
    if region:
        logger.debug(f"Resolved region_name from AWS_DEFAULT_REGION: {region}")
        return region

    # 4. Check AWS_PROFILE configuration
    profile = os.environ.get("AWS_PROFILE")
    if profile:
        logger.debug(f"Attempting to resolve region from AWS_PROFILE: {profile}")
        region = _resolve_region_from_profile(profile)
        if region:
            logger.debug(f"Resolved region_name from profile '{profile}': {region}")
            return region

    # 5. No region found - let boto3 use its defaults
    logger.debug("No region_name resolved, will use boto3 defaults")
    return None


class BedrockAdapter(FrameworkAdapter):
    """
    Framework adapter for AWS Bedrock managed AI services.

    BedrockAdapter provides integration with AWS Bedrock, which offers access
    to foundation models from multiple providers through AWS's managed platform.
    The adapter handles Bedrock-specific content formatting, authentication,
    and configuration requirements.

    Key features:
    - Integration with AWS Bedrock managed models
    - Strict content formatting for Bedrock Converse API compliance
    - Image format validation and binary file handling
    - AWS authentication and configuration management
    - Support for multiple model providers through Bedrock

    The adapter is particularly valuable for:
    - Enterprise applications requiring AWS integration
    - Applications needing compliance and governance features
    - Multi-provider model access through a single AWS interface
    - Scenarios requiring AWS security and billing integration

    Supported model providers through Bedrock:
    - Anthropic Claude models
    - Amazon Titan models
    - Cohere Command models
    - Meta Llama models
    - Stability AI models

    Example:
        Basic usage with Claude on Bedrock::

            adapter = BedrockAdapter()
            model = adapter.load_model("anthropic.claude-3-5-sonnet-20241022-v2:0")

        With AWS configuration::

            config = {
                "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
                "temperature": 0.7,
                "boto_client_config": {
                    "region_name": "us-east-1",
                    "aws_access_key_id": "AKIA...",
                    "aws_secret_access_key": "...",
                }
            }
            model = adapter.load_model(config=config)
    """

    @property
    def framework_name(self) -> str:
        """Get the framework name for this adapter."""
        return "bedrock"

    def load_model(
        self,
        model_name: Optional[str] = None,
        model_config: Optional[Dict[str, Any]] = None,
    ) -> BedrockModel:
        """
        Load a model using AWS Bedrock.

        Creates and configures a BedrockModel instance for use with strands-agents.
        Handles AWS-specific configuration including region settings, authentication,
        and Bedrock model identifiers.

        Args:
            model_name: Bedrock model identifier (optional if in model_config)
            model_config: Configuration dictionary with model and AWS settings

        Returns:
            BedrockModel: Configured model instance ready for agent use
        """
        logger.trace(
            "BedrockAdapter.load_model called with model_name='{}', model_config={}",
            model_name,
            model_config,
        )

        model_config = model_config or {}

        # Set model identifier if provided
        if model_name:
            model_config["model_id"] = model_name

        # Resolve region_name using AWS fallback hierarchy
        region_name = _resolve_region_name(model_config)
        if region_name and "region_name" not in model_config:
            model_config["region_name"] = region_name
            logger.debug(f"Set region_name in model_config: {region_name}")

        # Extract AWS boto client configuration
        boto_client_config = model_config.pop("boto_client_config", None)
        if boto_client_config:
            boto_client_config = BotocoreConfig(**boto_client_config)

        # Create and return the Bedrock model
        model = BedrockModel(boto_client_config=boto_client_config, **model_config)
        logger.debug("BedrockModel created successfully")
        return model

    def adapt_content(self, messages: Messages) -> Messages:
        """
        Adapt message content for AWS Bedrock Converse API compliance.

        Transforms message content to meet Bedrock's strict formatting requirements:
        - Validates image formats (gif, jpeg, png, webp only)
        - Sanitizes document names to meet AWS naming constraints
        - Creates text placeholders for unsupported binary files

        Args:
            messages: Input messages to adapt

        Returns:
            Messages: Adapted messages compliant with Bedrock requirements
        """
        if not messages:
            return messages

        transformed_messages = []

        has_text = False

        for message in messages:
            content = message.get("content")
            if not isinstance(content, list):
                # Handle non-list content by converting to text
                if content:
                    transformed_messages.append({"text": str(content)})
                continue

            transformed_content = []

            for block in content:
                # Handle image blocks in the 'strands' format
                if "image" in block:
                    block_content = block.get("image", {})
                    if "source" in block_content:
                        source = block_content.get("source", {})
                        image_format = block_content.get("format")
                        if image_format in VALID_IMAGE_FORMATS and source.get("bytes"):
                            # Valid image format, pass through
                            transformed_content.append(block)
                        else:
                            # Invalid or unsupported format, create placeholder
                            placeholder_text = f"[User uploaded a binary file of type '{image_format}' that cannot be displayed.]"
                            transformed_content.append({"text": placeholder_text})
                        continue

                # Handle document blocks - sanitize name for Bedrock compliance
                if "document" in block:
                    block_content = block.get("document", {})
                    sanitize_name(block_content)
                    transformed_content.append(block)
                    continue

                # Pass through other block types unchanged
                transformed_content.append(block)

                if "text" in block:
                    has_text = True

            # Update message content if we have transformed blocks
            if transformed_content:
                if not has_text:
                    # Ensure at least one text block exists
                    transformed_content.append({"text": "See attached content. "})
                new_message = message.copy()
                new_message["content"] = transformed_content
                transformed_messages.append(new_message)

        return transformed_messages


def _sanitize_part(text: str) -> str:
    """
    Sanitize a single string part with maximum performance optimization.

    Uses pre-compiled patterns and single-pass operations for optimal speed.

    Args:
        text: String part to sanitize

    Returns:
        str: Sanitized string part compliant with AWS Bedrock requirements
    """
    if not text:
        return ""

    # Single pass: accent transformation, underscore replacement, invalid char removal
    text = _INVALID_CHARS_PATTERN.sub(
        "", text.translate(_ACCENT_TRANSLATION).replace("_", "-")
    )

    # Consolidate multiple hyphens and spaces in single operations
    if "--" in text:
        text = _MULTIPLE_HYPHENS_PATTERN.sub("-", text)
    if "  " in text:
        text = _MULTIPLE_SPACES_PATTERN.sub(" ", text)

    # Strip leading/trailing hyphens and spaces
    return text.strip("- ")


def sanitize_name(block: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize a 'name' field with maximum performance optimization.

    Ultra-optimized version with caching, fast paths, and minimal string operations.
    Converts accented characters to non-accented equivalents for better user experience.

    Args:
        block: Dictionary containing 'name' field to sanitize

    Returns:
        Dict[str, Any]: Dictionary with sanitized 'name' field
    """
    if "name" not in block:
        return block

    raw_name = block.get("name", "document")
    if not raw_name:
        block["name"] = "document"
        return block

    # Check cache first for common patterns
    if raw_name in _PATH_CACHE:
        block["name"] = _PATH_CACHE[raw_name]
        return block

    original_name = raw_name  # Store for caching

    # Ultra-fast path for simple ASCII filenames (most common case)
    if "/" not in raw_name and raw_name.isascii():
        if "." not in raw_name:
            # Simple ASCII filename
            sanitized = _sanitize_part(raw_name)
            result = sanitized if sanitized else "document"
        elif raw_name.count(".") == 1:
            # Single extension ASCII file
            name_part, ext_part = raw_name.split(".", 1)
            sanitized_name = _sanitize_part(name_part)
            sanitized_ext = _sanitize_part(ext_part)

            if not sanitized_name:
                sanitized_name = "document"

            result = sanitized_name
            if sanitized_ext:
                result += f"[{sanitized_ext}]"
        else:
            # Multiple extensions - fall through to full processing
            result = None

        if result is not None:
            # Cache result and return
            if len(_PATH_CACHE) < _CACHE_MAX_SIZE:
                _PATH_CACHE[original_name] = result
            block["name"] = result
            return block

    # Handle special root cases
    if raw_name in ("/", "./"):
        result = "[-]" if raw_name == "/" else "document"
        block["name"] = result
        return block

    # Full processing for complex paths
    # Separate path and filename efficiently
    if raw_name.endswith("/"):
        dir_name, base_name = raw_name[:-1], ""
    else:
        slash_pos = raw_name.rfind("/")
        if slash_pos == -1:
            dir_name, base_name = "", raw_name
        else:
            dir_name, base_name = raw_name[:slash_pos], raw_name[slash_pos + 1 :]

    # Extract extensions efficiently
    extensions = []
    filename = base_name
    while True:
        dot_pos = filename.rfind(".")
        if dot_pos <= 0:  # No dot or dot at start
            break
        ext = filename[dot_pos + 1 :]
        extensions.append(ext)
        filename = filename[:dot_pos]
    extensions.reverse()  # Restore original order

    # Build result parts efficiently
    result_parts = []

    # Process directory path
    if dir_name:
        is_relative = dir_name.startswith("./")
        if is_relative:
            dir_name = dir_name[2:]  # Remove './' prefix
        elif dir_name.startswith("/"):
            dir_name = dir_name[1:]  # Remove leading '/' for processing

        if dir_name:
            # Split and sanitize path segments efficiently
            segments = []
            for seg in dir_name.split("/"):
                if seg:  # Skip empty segments
                    sanitized_seg = _sanitize_part(seg)
                    if sanitized_seg:  # Only add non-empty sanitized segments
                        segments.append(sanitized_seg)

            if segments:
                path_content = "-".join(segments)
                result_parts.append(
                    f"[-{path_content}]" if is_relative else f"[{path_content}]"
                )
            elif is_relative or raw_name.startswith("/"):
                result_parts.append("[-]")
        elif is_relative or raw_name.startswith("/"):
            result_parts.append("[-]")

    # Process filename
    if filename:
        sanitized_filename = _sanitize_part(filename)
        if sanitized_filename:
            result_parts.append(sanitized_filename)

    # Process extensions
    for ext in extensions:
        sanitized_ext = _sanitize_part(ext)
        if sanitized_ext:
            result_parts.append(f"[{sanitized_ext}]")

    # Default if nothing remains
    if not result_parts:
        result_parts.append("document")

    # Single join operation
    result = "".join(result_parts)

    # Cache result for future use
    if len(_PATH_CACHE) < _CACHE_MAX_SIZE:
        _PATH_CACHE[original_name] = result

    block["name"] = result
    return block
