"""
Configuration for strands_engine.

Provides a clean, simple configuration interface that accepts
resolved parameters from the wrapper application.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from .types import PathLike, Message


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
    
    # Session configuration
    session_file: Optional[PathLike] = None
    initial_messages: List[Message] = field(default_factory=list)
    
    # Conversation management
    conversation_strategy: str = "full_history"
    max_context_length: Optional[int] = None
    
    # Framework-specific options
    emulate_system_prompt: bool = False
    framework_specific: Dict[str, Any] = field(default_factory=dict)
    
    # Engine behavior
    auto_save_session: bool = True
    streaming: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.model:
            raise ValueError("Model must be specified")
            
        # Convert paths to Path objects
        self.tool_config_paths = [Path(p) for p in self.tool_config_paths]
        
        if self.session_file:
            self.session_file = Path(self.session_file)
            
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