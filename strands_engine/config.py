"""
Configuration for strands_engine.

Provides a clean, simple configuration interface that accepts
resolved parameters from the wrapper application.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Literal
from pathlib import Path

from .ptypes import PathLike, Message

# Type for conversation manager strategies
ConversationManagerType = Literal["null", "sliding_window", "summarizing"]


@dataclass
class EngineConfig:
    """
    Configuration for the Strands Engine.
    
    This configuration accepts resolved parameters from wrapper applications
    and focuses purely on engine execution needs.
    """
    
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
    framework_specific: Dict[str, Any] = field(default_factory=dict)
    
    # Engine behavior
    auto_save_session: bool = True  # DelegatingSession handles this automatically when active
    streaming: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.model:
            raise ValueError("Model must be specified")
            
        # Convert paths to Path objects
        self.tool_config_paths = [Path(p) for p in self.tool_config_paths]
        
        if self.sessions_home:
            self.sessions_home = Path(self.sessions_home)
            
        # Validate file_paths format
        validated_file_paths = []
        for item in self.file_paths:
            if isinstance(item, (str, Path)):
                # If just a path, assume no specific mimetype
                validated_file_paths.append((Path(item), None))
            elif isinstance(item, tuple) and len(item) == 2:
                validated_file_paths.append((Path(item[0]), item[1]))
            else:
                raise ValueError(f"Invalid file_path format: {item}")
        
        self.file_paths = validated_file_paths
        
        # Validate conversation manager configuration
        self._validate_conversation_manager_config()
    
    def _validate_conversation_manager_config(self) -> None:
        """Validate conversation manager configuration parameters."""
        # Validate sliding window size
        if self.sliding_window_size < 1:
            raise ValueError("sliding_window_size must be at least 1")
        if self.sliding_window_size > 1000:
            raise ValueError("sliding_window_size cannot exceed 1000 (performance limit)")

        # Validate preserve_recent_messages
        if self.preserve_recent_messages < 1:
            raise ValueError("preserve_recent_messages must be at least 1")

        # For summarizing mode, validate preserve_recent is reasonable
        if self.conversation_manager_type == "summarizing":
            if self.preserve_recent_messages > 100:
                raise ValueError("preserve_recent_messages cannot exceed 100 (performance limit)")

        # Validate summary_ratio
        if not (0.1 <= self.summary_ratio <= 0.8):
            raise ValueError("summary_ratio must be between 0.1 and 0.8")

        # Validate summarization model format if provided
        if self.summarization_model:
            if ":" in self.summarization_model:
                framework, model = self.summarization_model.split(":", 1)
                if not framework or not model:
                    raise ValueError(f"Invalid summarization_model format: {self.summarization_model}")
    
    # Convenience properties
    
    @property
    def uses_conversation_manager(self) -> bool:
        """Check if conversation management is enabled."""
        return self.conversation_manager_type != "null"

    @property
    def uses_sliding_window(self) -> bool:
        """Check if using sliding window conversation management."""
        return self.conversation_manager_type == "sliding_window"

    @property
    def uses_summarizing(self) -> bool:
        """Check if using summarizing conversation management."""
        return self.conversation_manager_type == "summarizing"
    
    @property
    def framework_name(self) -> str:
        """Extract framework name from model string for loader selection."""
        if ":" in self.model:
            return self.model.split(":", 1)[0]
        return "litellm"  # Default framework

    @property
    def model_name(self) -> str:
        """Extract model name from model string for framework configuration."""
        if ":" in self.model:
            return self.model.split(":", 1)[1]
        return self.model