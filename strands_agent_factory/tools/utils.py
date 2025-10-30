"""
Shared utilities for tool management.
"""

from pathlib import Path
from typing import Any, Callable, List, Optional

from loguru import logger

from ..core.types import ToolConfig


def extract_tool_names(tools: List[Callable]) -> List[str]:
    """Extract clean tool names from loaded tools."""
    return [getattr(tool, 'name', tool.__name__) for tool in tools]


def validate_required_fields(config: ToolConfig, required_fields: List[str]) -> Optional[str]:
    """Validate that required fields are present in config."""
    missing_fields = [field for field in required_fields if not config.get(field)]
    if missing_fields:
        return "Missing required fields: {}".format(missing_fields)
    return None


def get_config_value(config: ToolConfig, field: str, default: Any = None) -> Any:
    """Get configuration value with consistent default handling."""
    return config.get(field, default)


def create_failed_config(file_path: Path, error: Exception) -> ToolConfig:
    """Create a failed configuration entry for error tracking."""
    from .types import (
        CONFIG_FIELD_ID, CONFIG_FIELD_TYPE, CONFIG_FIELD_SOURCE_FILE, 
        CONFIG_FIELD_ERROR, DEFAULT_FAILED_CONFIG_PREFIX, TOOL_TYPE_PYTHON
    )
    
    return {
        CONFIG_FIELD_ID: DEFAULT_FAILED_CONFIG_PREFIX + file_path.name,
        CONFIG_FIELD_TYPE: TOOL_TYPE_PYTHON,  # Default type for failed configs
        CONFIG_FIELD_SOURCE_FILE: str(file_path),
        CONFIG_FIELD_ERROR: str(error),
    }
