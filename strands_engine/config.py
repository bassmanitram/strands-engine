from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Literal
from pathlib import Path

from .ptypes import PathLike, Message

# Type for conversation manager strategies
ConversationManagerType = Literal["null", "sliding_window", "summarizing"]


@dataclass
class EngineConfig:    
    # Model configuration
    model: str
    system_prompt: Optional[str] = None
    model_config: Optional[Dict[str, Any]] = None
    
    # Tool configuration  
    tool_config_paths: List[PathLike] = field(default_factory=list)
    
    # File uploads (path, mimetype pairs)
    file_paths: List[Tuple[PathLike, Optional[str]]] = field(default_factory=list)
    
    # Session configuration - uses DelegatingSession proxy
    sessions_home: Optional[PathLike] = None
    session_id: Optional[str] = None  # If None, DelegatingSession remains inactive
    
    # Conversation management configuration
    conversation_manager_type: ConversationManagerType = "sliding_window"
    sliding_window_size: int = 40               # Maximum messages in sliding window
    preserve_recent_messages: int = 10          # Messages to always preserve in summarizing mode
    summary_ratio: float = 0.3                  # Ratio of messages to summarize (0.1-0.8)
    summarization_model: Optional[str] = None   # Optional separate model for summarization
    custom_summarization_prompt: Optional[str] = None  # Custom prompt for summarization
    should_truncate_results: bool = True        # Whether to truncate tool results on overflow
    
    # Framework-specific options
    emulate_system_prompt: bool = False
    
    # Engine behavior
    show_tool_use: bool = False     # Whether to show verbose tool execution feedback
