"""
Configuration management for strands_agent_factory.

This module provides the main configuration dataclass for the strands_agent_factory
package. AgentFactoryConfig consolidates all the configuration parameters needed
to create and manage strands-agents Agent instances.

The configuration covers:
- Model selection and parameters
- Tool configuration paths
- File uploads and content
- Session and conversation management
- Framework-specific options

The configuration is designed to be serializable and to provide sensible
defaults for all optional parameters.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

from dataclass_args import cli_exclude, cli_file_loadable
from loguru import logger

from .exceptions import ConfigurationError
from .types import Message, PathLike

# ============================================================================
# Type Definitions
# ============================================================================

ConversationManagerType = Literal["null", "sliding_window", "summarizing"]
"""
Type for conversation manager strategies.

- null: No conversation management (unlimited context)
- sliding_window: Keep only recent messages within window size
- summarizing: Summarize older messages when approaching limits
"""


# ============================================================================
# Main Configuration Class
# ============================================================================


@dataclass
class AgentFactoryConfig:
    """
    Comprehensive configuration for strands_agent_factory agent creation.

    This configuration class consolidates all parameters needed to create
    and manage a strands-agents Agent instance. It provides a clean interface
    for specifying model settings, tool configurations, conversation management,
    and framework-specific options.

    The configuration is designed to be:
    - Serializable for persistence and transfer
    - Validated for required vs. optional parameters
    - Extensible for framework-specific options
    - Compatible with strands-agents patterns

    Attributes:
        model: Model identifier string (required)
        system_prompt: System prompt for the agent (optional, supports @file.txt)
        model_config: Framework-specific model configuration (optional)
        tool_config_paths: Paths to individual tool configuration files
        file_paths: Files to upload as (path, mimetype) pairs
        sessions_home: Base directory for session storage (optional)
        session_id: Session identifier for persistence (optional)
        conversation_manager_type: Strategy for conversation management
        sliding_window_size: Maximum messages in sliding window mode
        preserve_recent_messages: Messages to preserve in summarizing mode
        summary_ratio: Ratio of messages to summarize (0.1-0.8)
        summarization_model: Optional separate model for summarization
        custom_summarization_prompt: Custom prompt for summarization (supports @file.txt)
        should_truncate_results: Whether to truncate tool results on overflow
        emulate_system_prompt: Use system prompt emulation for compatibility
        callback_handler: Optional custom callback handler for agent events (CLI hidden)
        show_tool_use: Whether to show verbose tool execution feedback
        response_prefix: Optional prefix to display before agent responses
        output_printer: Optional custom printer function for formatted output (CLI hidden)
    """

    # ========================================================================
    # Model Configuration (Required)
    # ========================================================================

    model: str
    """
    Model identifier string.
    
    Examples:
        - "gpt-4o" (OpenAI)
        - "anthropic:claude-3-5-sonnet-20241022" (Anthropic)
        - "ollama:llama2:7b" (Ollama)
        - "bedrock:anthropic.claude-3-sonnet-20240229-v1:0" (AWS Bedrock)
    """

    # ========================================================================
    # Model Parameters (Optional)
    # ========================================================================

    system_prompt: Optional[str] = cli_file_loadable(default=None)
    """
    System prompt to guide agent behavior.
    
    Supports loading from file using '@file.txt' syntax.
    
    Examples:
        - "You are a helpful assistant"  # Literal text
        - "@prompts/coding-assistant.txt"  # Load from file
    """

    initial_message: Optional[str] = None
    """Initial user prompt to send (along with any uploaded files)"""

    model_config: Optional[Dict[str, Any]] = None
    """
    Framework-specific model configuration.
    
    Passed directly to the underlying model implementation.
    Examples: temperature, max_tokens, top_p, etc.
    """

    # ========================================================================
    # Tool Configuration
    # ========================================================================

    tool_config_paths: List[PathLike] = field(default_factory=list)
    """
    Paths to individual tool configuration files.
    
    Must be individual JSON or YAML files containing tool configurations.
    
    Examples:
        - "tools/math_tools.json"
        - "configs/file_tools.yaml"
        - "/path/to/custom_tools.json"
    """

    # ========================================================================
    # File Upload Configuration
    # ========================================================================

    file_paths: List[Tuple[PathLike, Optional[str]]] = field(default_factory=list)
    """
    Files to upload as (path, mimetype) pairs.
    
    Files are processed and made available to the agent at startup.
    Mimetype can be None for auto-detection.
    """

    # ========================================================================
    # Session Management Configuration
    # ========================================================================

    sessions_home: Optional[PathLike] = None
    """
    Base directory for session storage.
    
    If None, session persistence is disabled. Used in conjunction
    with session_id to enable conversation persistence.
    """

    session_id: Optional[str] = None
    """
    Session identifier for persistence.
    
    If None, DelegatingSession remains inactive and no persistence
    occurs. If provided, conversation state is saved/restored.
    """

    # ========================================================================
    # Conversation Management Configuration
    # ========================================================================

    conversation_manager_type: ConversationManagerType = "sliding_window"
    """
    Strategy for managing conversation context length.
    
    - "null": No management (unlimited context)
    - "sliding_window": Keep only recent messages
    - "summarizing": Summarize older messages when needed
    """

    sliding_window_size: int = 40
    """
    Maximum messages in sliding window mode.
    
    When using sliding_window conversation management, only the most
    recent N messages are kept in context.
    """

    preserve_recent_messages: int = 10
    """
    Messages to always preserve in summarizing mode.
    
    When using summarizing conversation management, this many recent
    messages are never summarized.
    """

    summary_ratio: float = 0.3
    """
    Ratio of messages to summarize (0.1-0.8).
    
    When summarizing, this proportion of older messages are
    condensed into summaries. Valid range: 0.1 to 0.8.
    """

    summarization_model: Optional[str] = None
    """
    Optional separate model for summarization.
    
    Uses the same format as the model parameter. If None, uses the same model
    as the main agent. Can specify a different (usually cheaper/faster) model
    for summarization tasks.
    
    Examples:
        - "gpt-4o-mini" (OpenAI)
        - "anthropic:claude-3-haiku-20240307" (Anthropic)
        - "openai:gpt-3.5-turbo" (OpenAI with explicit framework)
    """

    summarization_model_config: Optional[Dict[str, Any]] = None
    """
    Framework-specific configuration for the summarization model.
    
    When conversation_manager_type is "summarizing", a separate summarization
    agent is always created using:
    - Model: summarization_model (or model if not specified)
    - Config: summarization_model_config (or {} if not specified)
    
    This allows using the same model with different configuration for
    summarization (e.g., lower temperature, reduced max_tokens).
    
    Passed directly to the underlying model implementation without validation.
    Examples: temperature, max_tokens, top_p, etc.
    
    Note: If agent creation fails and summarization_model_config was specified,
    an InitializationError is raised (explicit requirements must be met).
    """

    custom_summarization_prompt: Optional[str] = cli_file_loadable(default=None)
    """
    Custom prompt for summarization operations.
    
    If None, uses default summarization prompt. Allows customization
    of how conversation history is condensed.
    
    Supports loading from file using '@file.txt' syntax.
    
    Examples:
        - "Summarize the conversation concisely"  # Literal text
        - "@prompts/summarization.txt"  # Load from file
    """

    should_truncate_results: bool = True
    """
    Whether to truncate tool results on overflow.
    
    When True, large tool results are truncated to fit within
    context limits. When False, full results are preserved.
    """

    # ========================================================================
    # Framework-Specific Options
    # ========================================================================

    emulate_system_prompt: bool = False
    """
    Use system prompt emulation for compatibility.
    
    Some frameworks don't support system prompts natively. When True,
    the system prompt is prepended to the first user message.
    """

    # ========================================================================
    # Callback and Output Configuration (Hidden from CLI)
    # ========================================================================

    callback_handler: Optional[Callable] = cli_exclude(default=None)
    """
    Optional custom callback handler for agent events.
    
    If None, a ConfigurableCallbackHandler will be created using the
    show_tool_use, response_prefix, and output_printer settings. If provided,
    this custom handler will be used instead.
    
    NOTE: This field is excluded from CLI arguments as it requires a Python
    callable object that cannot be specified via command line.
    """

    show_tool_use: bool = False
    """
    Whether to show verbose tool execution feedback.
    
    When True, detailed information about tool calls and results
    is displayed. Only used if callback_handler is None.
    """

    response_prefix: Optional[str] = None
    """
    Optional prefix to display before agent responses.
    
    Example: "Assistant: " or "<b>Bot:</b> ". Can contain HTML or ANSI
    formatting codes. Only used if callback_handler is None.
    """

    output_printer: Optional[Callable] = cli_exclude(default=None)
    """
    Optional custom printer function for formatted output.
    
    If None, uses standard print(). Can be set to a custom printer
    that handles HTML/ANSI formatting (e.g., from repl-toolkit's
    create_auto_printer()). Only used if callback_handler is None.
    
    The printer function should have the signature:
        printer(text: str, **kwargs) -> None
    
    Where kwargs can include: end, flush, etc. (same as print()).
    
    Example:
        from repl_toolkit import create_auto_printer
        config = AgentFactoryConfig(
            model="gpt-4o",
            response_prefix="<b>Assistant:</b> ",
            output_printer=create_auto_printer()  # Auto-formats HTML/ANSI
        )
    
    NOTE: This field is excluded from CLI arguments as it requires a Python
    callable object that cannot be specified via command line.
    """

    def __post_init__(self):
        """
        Validate configuration after initialization.

        Performs comprehensive validation of all configuration parameters
        to catch errors early and provide clear feedback about invalid
        configurations.

        Raises:
            ConfigurationError: If any configuration parameter is invalid
        """
        logger.trace("AgentFactoryConfig.__post_init__ called")

        self._validate_model()
        self._validate_conversation_management()
        self._validate_file_paths()
        self._validate_tool_config_paths()
        self._validate_session_config()
        self._validate_model_config()
        self._validate_output_printer()

        logger.trace("AgentFactoryConfig.__post_init__ completed")

    def _validate_model(self):
        """
        Validate model identifier string.

        Ensures the model identifier is properly formatted and contains
        valid characters for framework and model specification.

        Raises:
            ConfigurationError: If model identifier is invalid
        """
        logger.trace("_validate_model called with model: '{}'", self.model)

        if not self.model:
            raise ConfigurationError("Model identifier is required")

        if not isinstance(self.model, str):
            raise ConfigurationError(
                f"Model must be a string, got {type(self.model).__name__}"
            )

        if not self.model.strip():
            raise ConfigurationError("Model identifier cannot be empty or whitespace")

        # Validate model string format (basic pattern check)
        # Patterns: "model", "framework:model", "framework:provider/model"
        model_pattern = r"^[a-zA-Z0-9_-]+(?::[a-zA-Z0-9_/.-]+)*$"
        if not re.match(model_pattern, self.model):
            raise ConfigurationError(
                f"Invalid model identifier format: '{self.model}'. "
                f"Expected patterns: 'model', 'framework:model', or 'framework:provider/model'"
            )

        logger.trace("_validate_model completed successfully")

    def _validate_conversation_management(self):
        """
        Validate conversation management parameters.

        Ensures all conversation management settings are within valid ranges
        and are compatible with each other.

        Raises:
            ConfigurationError: If conversation management parameters are invalid
        """
        logger.trace("_validate_conversation_management called")

        # Validate sliding window size
        if not isinstance(self.sliding_window_size, int):
            raise ConfigurationError(
                f"sliding_window_size must be an integer, got {type(self.sliding_window_size).__name__}"
            )

        if self.sliding_window_size <= 0:
            raise ConfigurationError(
                f"sliding_window_size must be positive, got {self.sliding_window_size}"
            )

        if self.sliding_window_size > 1000:
            raise ConfigurationError(
                f"sliding_window_size too large (max 1000), got {self.sliding_window_size}"
            )

        # Validate preserve_recent_messages
        if not isinstance(self.preserve_recent_messages, int):
            raise ConfigurationError(
                f"preserve_recent_messages must be an integer, got {type(self.preserve_recent_messages).__name__}"
            )

        if self.preserve_recent_messages < 0:
            raise ConfigurationError(
                f"preserve_recent_messages cannot be negative, got {self.preserve_recent_messages}"
            )

        if self.preserve_recent_messages > self.sliding_window_size:
            raise ConfigurationError(
                f"preserve_recent_messages ({self.preserve_recent_messages}) cannot exceed "
                f"sliding_window_size ({self.sliding_window_size})"
            )

        # Validate summary_ratio
        if not isinstance(self.summary_ratio, (int, float)):
            raise ConfigurationError(
                f"summary_ratio must be a number, got {type(self.summary_ratio).__name__}"
            )

        if not (0.1 <= self.summary_ratio <= 0.8):
            raise ConfigurationError(
                f"summary_ratio must be between 0.1 and 0.8, got {self.summary_ratio}"
            )

    def _validate_file_paths(self):
        """
        Validate file upload paths.

        Ensures all specified files exist, are readable, and have valid
        mimetype specifications.

        Raises:
            ConfigurationError: If any file path is invalid or inaccessible
        """
        if logger.level("TRACE").no >= logger._core.min_level:
            logger.trace(
                "_validate_file_paths called with {} file paths", len(self.file_paths)
            )

        if not isinstance(self.file_paths, list):
            raise ConfigurationError(
                f"file_paths must be a list, got {type(self.file_paths).__name__}"
            )

        for i, file_entry in enumerate(self.file_paths):
            if not isinstance(file_entry, (tuple, list)) or len(file_entry) != 2:
                raise ConfigurationError(
                    f"file_paths[{i}] must be a (path, mimetype) tuple, got {type(file_entry).__name__}"
                )

            file_path, mimetype = file_entry

            # Convert to Path for validation
            try:
                path_obj = Path(file_path)
            except (TypeError, ValueError) as e:
                raise ConfigurationError(
                    f"Invalid file path at file_paths[{i}]: {file_path}"
                ) from e

            # Check if file exists and is readable
            if not path_obj.exists():
                raise ConfigurationError(f"File does not exist: {file_path}")

            if not path_obj.is_file():
                raise ConfigurationError(f"Path is not a file: {file_path}")

            if not os.access(path_obj, os.R_OK):
                raise ConfigurationError(f"File is not readable: {file_path}")

            # Validate mimetype if provided
            if mimetype is not None and not isinstance(mimetype, str):
                raise ConfigurationError(
                    f"Mimetype must be a string or None, got {type(mimetype).__name__} at file_paths[{i}]"
                )

    def _validate_tool_config_paths(self):
        """
        Validate tool configuration paths.

        Ensures all tool configuration paths are individual files that exist
        and are readable.

        Raises:
            ConfigurationError: If any tool config path is invalid or inaccessible
        """
        if logger.level("TRACE").no >= logger._core.min_level:
            logger.trace(
                "_validate_tool_config_paths called with {} tool config paths",
                len(self.tool_config_paths),
            )

        if not isinstance(self.tool_config_paths, list):
            raise ConfigurationError(
                f"tool_config_paths must be a list, got {type(self.tool_config_paths).__name__}"
            )

        for i, tool_path in enumerate(self.tool_config_paths):
            try:
                path_obj = Path(tool_path)
            except (TypeError, ValueError) as e:
                raise ConfigurationError(
                    f"Invalid tool config path at tool_config_paths[{i}]: {tool_path}"
                ) from e

            # Check if path exists
            if not path_obj.exists():
                raise ConfigurationError(
                    f"Tool config path does not exist: {tool_path}"
                )

            # Must be a file (directories are not supported)
            if not path_obj.is_file():
                if path_obj.is_dir():
                    raise ConfigurationError(
                        f"Tool config path must be an individual file, not a directory: {tool_path}. "
                        f"Directories are not supported. Please specify individual configuration files."
                    )
                else:
                    raise ConfigurationError(
                        f"Tool config path must be a file: {tool_path}"
                    )

            # Check if file is readable
            if not os.access(path_obj, os.R_OK):
                raise ConfigurationError(
                    f"Tool config file is not readable: {tool_path}"
                )

            # Validate file extension (should be JSON or YAML)
            valid_extensions = {".json", ".yaml", ".yml"}
            if path_obj.suffix.lower() not in valid_extensions:
                logger.warning(
                    f"Tool config file '{tool_path}' has extension '{path_obj.suffix}'. "
                    f"Expected one of: {', '.join(valid_extensions)}"
                )

    def _validate_session_config(self):
        """
        Validate session management configuration.

        Ensures session directory is writable and session ID contains
        only filesystem-safe characters.

        Raises:
            ConfigurationError: If session configuration is invalid
        """
        logger.trace("_validate_session_config called")

        # Validate sessions_home if provided
        if self.sessions_home is not None:
            try:
                sessions_path = Path(self.sessions_home)
            except (TypeError, ValueError) as e:
                raise ConfigurationError(
                    f"Invalid sessions_home path: {self.sessions_home}"
                ) from e

            # Create directory if it doesn't exist
            if not sessions_path.exists():
                try:
                    sessions_path.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    raise ConfigurationError(
                        f"Cannot create sessions_home directory: {self.sessions_home}"
                    ) from e

            # Check if it's a directory and writable
            if not sessions_path.is_dir():
                raise ConfigurationError(
                    f"sessions_home must be a directory: {self.sessions_home}"
                )

            if not os.access(sessions_path, os.W_OK):
                raise ConfigurationError(
                    f"sessions_home directory is not writable: {self.sessions_home}"
                )

        # Validate session_id if provided
        if self.session_id is not None:
            if not isinstance(self.session_id, str):
                raise ConfigurationError(
                    f"session_id must be a string, got {type(self.session_id).__name__}"
                )

            if not self.session_id.strip():
                raise ConfigurationError("session_id cannot be empty or whitespace")

            # Check for invalid characters in session_id (filesystem safety)
            invalid_chars = set('<>:"/\\|?*')
            if any(char in self.session_id for char in invalid_chars):
                raise ConfigurationError(
                    f"session_id contains invalid characters: {self.session_id}"
                )

    def _validate_model_config(self):
        """
        Validate model configuration parameters.

        Ensures common model parameters like temperature, max_tokens, and top_p
        are within valid ranges when specified.

        Raises:
            ConfigurationError: If model configuration parameters are invalid
        """
        logger.trace("_validate_model_config called")

        if self.model_config is not None:
            if not isinstance(self.model_config, dict):
                raise ConfigurationError(
                    f"model_config must be a dictionary, got {type(self.model_config).__name__}"
                )

            # Validate common model parameters if present
            if "temperature" in self.model_config:
                temp = self.model_config["temperature"]
                if not isinstance(temp, (int, float)):
                    raise ConfigurationError(
                        f"model_config.temperature must be a number, got {type(temp).__name__}"
                    )
                if not (0.0 <= temp <= 2.0):
                    raise ConfigurationError(
                        f"model_config.temperature must be between 0.0 and 2.0, got {temp}"
                    )

            if "max_tokens" in self.model_config:
                max_tokens = self.model_config["max_tokens"]
                if not isinstance(max_tokens, int):
                    raise ConfigurationError(
                        f"model_config.max_tokens must be an integer, got {type(max_tokens).__name__}"
                    )
                if max_tokens <= 0:
                    raise ConfigurationError(
                        f"model_config.max_tokens must be positive, got {max_tokens}"
                    )
                if max_tokens > 200000:  # Reasonable upper limit
                    raise ConfigurationError(
                        f"model_config.max_tokens too large (max 200000), got {max_tokens}"
                    )

            if "top_p" in self.model_config:
                top_p = self.model_config["top_p"]
                if not isinstance(top_p, (int, float)):
                    raise ConfigurationError(
                        f"model_config.top_p must be a number, got {type(top_p).__name__}"
                    )
                if not (0.0 <= top_p <= 1.0):
                    raise ConfigurationError(
                        f"model_config.top_p must be between 0.0 and 1.0, got {top_p}"
                    )

    def _validate_output_printer(self):
        """
        Validate output_printer parameter.

        Ensures output_printer is callable if provided.

        Raises:
            ConfigurationError: If output_printer is not callable
        """
        logger.trace("_validate_output_printer called")

        if self.output_printer is not None:
            if not callable(self.output_printer):
                raise ConfigurationError(
                    f"output_printer must be callable, got {type(self.output_printer).__name__}"
                )

        logger.trace("_validate_output_printer completed successfully")
