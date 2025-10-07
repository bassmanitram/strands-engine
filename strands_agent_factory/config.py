"""
Configuration management for strands_agent_factory.

This module provides the main configuration dataclass for the strands_agent_factory
package. EngineConfig consolidates all the configuration parameters needed
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

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Literal
from pathlib import Path

from .ptypes import PathLike, Message

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
class EngineConfig:
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
        system_prompt: System prompt for the agent (optional)
        model_config: Framework-specific model configuration (optional)
        tool_config_paths: Paths to tool configuration files/directories
        file_paths: Files to upload as (path, mimetype) pairs
        sessions_home: Base directory for session storage (optional)
        session_id: Session identifier for persistence (optional)
        conversation_manager_type: Strategy for conversation management
        sliding_window_size: Maximum messages in sliding window mode
        preserve_recent_messages: Messages to preserve in summarizing mode
        summary_ratio: Ratio of messages to summarize (0.1-0.8)
        summarization_model: Optional separate model for summarization
        custom_summarization_prompt: Custom prompt for summarization
        should_truncate_results: Whether to truncate tool results on overflow
        emulate_system_prompt: Use system prompt emulation for compatibility
        show_tool_use: Whether to show verbose tool execution feedback
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
    
    system_prompt: Optional[str] = None
    """System prompt to guide agent behavior."""
    
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
    Paths to tool configuration files or directories.
    
    Can include:
    - Individual JSON configuration files
    - Directories containing configuration files
    - Python package paths for tool discovery
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
    
    If None, uses the same model as the main agent. Can specify
    a different (usually cheaper/faster) model for summarization tasks.
    """
    
    custom_summarization_prompt: Optional[str] = None
    """
    Custom prompt for summarization operations.
    
    If None, uses default summarization prompt. Allows customization
    of how conversation history is condensed.
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
    # Engine Behavior Options
    # ========================================================================
    
    show_tool_use: bool = False
    """
    Whether to show verbose tool execution feedback.
    
    When True, detailed information about tool calls and results
    is displayed. Useful for debugging and development.
    """