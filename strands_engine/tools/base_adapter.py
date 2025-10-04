"""
Base adapter for tool creation in strands_engine.

Provides the abstract interface for tool adapters that load tools
from different sources for strands-agents to execute.
"""

from abc import ABC, abstractmethod
from contextlib import ExitStack
from typing import Any, Dict

from ..ptypes import ToolCreationResult


class ToolAdapter(ABC):
    """
    Abstract base class for tool adapters.
    
    Tool adapters are responsible for loading and configuring tools
    from different sources (MCP servers, Python modules, etc.) for
    use by strands-agents. The engine loads tools but never executes them.
    """

    def __init__(self, exit_stack: ExitStack):
        """
        Initialize the tool adapter.
        
        Args:
            exit_stack: Context manager for resource cleanup
        """
        self.exit_stack = exit_stack

    @abstractmethod
    def create(self, config: Dict[str, Any]) -> ToolCreationResult:
        """
        Create tools based on the provided configuration.
        
        Args:
            config: Tool configuration dictionary
            
        Returns:
            ToolCreationResult with loaded tools and metadata
        """
        pass