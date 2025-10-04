"""
Core engine for strands_engine.

Provides the main Engine class for orchestrating conversational AI interactions
with tool loading, conversation management, session management, and multi-framework support.

Key Responsibilities:
- Load tools from configuration files (tools are executed by strands-agents)
- Process uploaded files into content blocks
- Create conversation manager based on configuration
- Create DelegatingSession proxy for optional session management
- Configure and initialize strands-agents Agent with tools and settings
- Orchestrate message processing through the Agent
"""

import asyncio
from typing import Any, Dict, List, Optional
from pathlib import Path

from loguru import logger

from .config import EngineConfig
from .ptypes import Message, Tool, FrameworkAdapter, ToolCreationResult
from .session import DelegatingSession


class Engine:
    """
    Core conversational AI engine.
    
    Orchestrates LLM interactions by:
    - Loading and configuring tools for strands-agents (does NOT execute tools directly)
    - Processing files into content blocks
    - Creating conversation manager based on configuration
    - Creating DelegatingSession proxy for optional session management
    - Creating and configuring strands-agents Agent
    - Coordinating message processing through the Agent
    
    The engine is designed to be used by wrapper applications that handle
    configuration resolution and user interface concerns.
    """
    
    def __init__(self, config: EngineConfig):
        """
        Initialize the engine with resolved configuration.
        
        Args:
            config: Engine configuration with all parameters resolved
        """
        self.config = config
        self._initialized = False
        self._agent = None  # strands-agents Agent instance
        self._loaded_tools: List[Tool] = []  # Tools loaded for Agent, not executed by engine
        self._framework_adapter: Optional[FrameworkAdapter] = None
        self._conversation_manager = None  # strands-agents ConversationManager
        
        # Create DelegatingSession proxy - will be inactive if no session_id provided
        self._session_manager = DelegatingSession(
            session_name=config.session_id,
            sessions_home=config.sessions_home
        )
        
        logger.info(f"Engine created with model: {config.model}")
        logger.info(f"Conversation manager: {config.conversation_manager_type}")
        if config.uses_sliding_window:
            logger.info(f"Sliding window size: {config.sliding_window_size}")
        elif config.uses_summarizing:
            logger.info(f"Summarizing (ratio: {config.summary_ratio}, preserve: {config.preserve_recent_messages})")
            if config.summarization_model:
                logger.info(f"Summarization model: {config.summarization_model}")
        
        if config.sessions_home:
            logger.info(f"Sessions home: {config.sessions_home}")
        if config.session_id:
            logger.info(f"Session ID: {config.session_id} (will activate session)")
        else:
            logger.info("No session_id specified - session will remain inactive")
    
    async def initialize(self) -> bool:
        """
        Initialize the engine with tools, conversation manager, session proxy, and agent.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            logger.warning("Engine already initialized")
            return True
            
        try:
            logger.info("Initializing strands engine...")
            
            # 1. Load tools from provided config paths (for Agent configuration, not direct execution)
            await self._load_tools()
            
            # 2. Process uploaded files
            await self._process_files()
            
            # 3. Initialize framework adapter
            self._setup_framework_adapter()
            
            # 4. Create conversation manager
            self._setup_conversation_manager()
            
            # 5. Create and configure strands-agents Agent with tools, conversation manager, and session proxy
            await self._setup_agent()
            
            self._initialized = True
            logger.info("Engine initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Engine initialization failed: {e}")
            return False
    
    async def process_message(self, message: str) -> str:
        """
        Process a user message and return response.
        
        Args:
            message: User message to process
            
        Returns:
            Response string from the strands-agents Agent
            
        Raises:
            RuntimeError: If engine not initialized
        """
        if not self._initialized:
            raise RuntimeError("Engine not initialized. Call initialize() first.")
        
        logger.debug(f"Processing message: {message}")
        
        try:
            # Process with strands-agents Agent (which handles tool execution internally)
            # The ConversationManager will handle context management
            # The DelegatingSession will handle session persistence if active
            response = await self._process_with_agent(message)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise
    
    async def shutdown(self) -> None:
        """
        Clean shutdown of the engine.
        
        Session saving is handled automatically by DelegatingSession if active.
        """
        logger.info("Shutting down engine...")
        
        try:
            # Clean up agent and tool resources
            if self._agent:
                # TODO: Implement agent cleanup when strands-agents integration is complete
                # This may include cleaning up tool connections (MCP servers, etc.)
                pass
            
            # DelegatingSession automatically handles session persistence if active
            logger.info("Session management handled by DelegatingSession")
                
            self._initialized = False
            logger.info("Engine shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during engine shutdown: {e}")
    
    @property
    def is_ready(self) -> bool:
        """Check if engine is initialized and ready."""
        return self._initialized and self._agent is not None
    
    @property
    def session_manager(self) -> DelegatingSession:
        """Get the session manager for external control."""
        return self._session_manager
    
    @property
    def conversation_manager_info(self) -> str:
        """Get information about the current conversation manager."""
        if not self._conversation_manager:
            return "Conversation Management: Not initialized"
        
        if self.config.conversation_manager_type == "null":
            return "Conversation Management: Disabled (full history preserved)"
        elif self.config.conversation_manager_type == "sliding_window":
            truncate_info = ("with result truncation" if self.config.should_truncate_results 
                           else "without result truncation")
            return (f"Conversation Management: Sliding Window "
                   f"(size: {self.config.sliding_window_size}, {truncate_info})")
        elif self.config.conversation_manager_type == "summarizing":
            summarization_model = self.config.summarization_model or "<same as main model>"
            return (f"Conversation Management: Summarizing "
                   f"(model: {summarization_model}, ratio: {self.config.summary_ratio}, "
                   f"preserve: {self.config.preserve_recent_messages})")
        else:
            return f"Conversation Management: {type(self._conversation_manager).__name__}"
    
    # Private implementation methods
    
    async def _load_tools(self) -> None:
        """
        Load tools from configuration paths for Agent configuration.
        
        IMPORTANT: The engine loads and configures tools, but does NOT execute them.
        Tool execution is handled entirely by strands-agents when the Agent processes messages.
        """
        logger.info(f"Loading tools from {len(self.config.tool_config_paths)} config paths")
        
        # TODO: Implement tool loading from paths using tool factory pattern
        # This will involve:
        # 1. Reading tool config files (JSON/YAML)
        # 2. Instantiating appropriate tool adapters (MCP, Python, etc.)
        # 3. Creating tool objects that strands-agents can use
        # 4. Collecting ToolCreationResult for each config
        
        # The loaded tools will be passed to strands-agents Agent constructor
        # The Agent will handle all tool execution - engine never executes tools directly
        
        # Placeholder
        self._loaded_tools = []
        logger.info(f"Loaded {len(self._loaded_tools)} tools for Agent configuration")
    
    async def _process_files(self) -> None:
        """Process uploaded files and add to context."""
        if not self.config.file_paths:
            return
            
        logger.info(f"Processing {len(self.config.file_paths)} uploaded files")
        
        # TODO: Implement file processing
        # This will involve:
        # 1. Reading file contents based on mimetype
        # 2. Creating appropriate content blocks (text, image, etc.)
        # 3. Adding processed content to initial messages or context
        
        # Placeholder
        logger.info("File processing complete")
    
    def _setup_framework_adapter(self) -> None:
        """Setup framework-specific adapter."""
        # TODO: Implement framework detection and adapter selection
        # This will involve:
        # 1. Determining the framework from model string (OpenAI, Anthropic, Bedrock, LiteLLM)
        # 2. Instantiating appropriate adapter
        # 3. The adapter will later be used to adapt tools and prepare agent args
        
        logger.info(f"Setting up framework adapter for model: {self.config.model}")
        self._framework_adapter = None  # Placeholder
    
    def _setup_conversation_manager(self) -> None:
        """Create conversation manager based on configuration."""
        # TODO: Implement conversation manager creation similar to YACBA's factory
        # This will involve:
        # 1. Creating appropriate ConversationManager based on conversation_manager_type
        # 2. Configuring with parameters (window_size, summary_ratio, etc.)
        # 3. Creating summarization agent if needed for summarizing mode
        
        logger.info(f"Setting up conversation manager: {self.config.conversation_manager_type}")
        
        if self.config.conversation_manager_type == "null":
            logger.info("Using null conversation manager (full history preserved)")
        elif self.config.conversation_manager_type == "sliding_window":
            logger.info(f"Using sliding window (size: {self.config.sliding_window_size}, "
                       f"truncate: {self.config.should_truncate_results})")
        elif self.config.conversation_manager_type == "summarizing":
            logger.info(f"Using summarizing (ratio: {self.config.summary_ratio}, "
                       f"preserve: {self.config.preserve_recent_messages})")
            if self.config.summarization_model:
                logger.info(f"Will create summarization agent with model: {self.config.summarization_model}")
        
        self._conversation_manager = None  # Placeholder - will be actual ConversationManager instance
    
    async def _setup_agent(self) -> None:
        """
        Setup the strands-agents Agent with loaded tools, conversation manager, and DelegatingSession.
        
        The Agent receives the tools, conversation manager, and session proxy, handling all 
        tool execution and session management internally. The engine's role is complete once 
        the Agent is configured.
        """
        # TODO: Implement agent setup with strands-agents
        # This will involve:
        # 1. Using framework adapter to adapt tool schemas for the LLM provider
        # 2. Using framework adapter to prepare agent initialization arguments
        # 3. Creating strands-agents Agent instance with:
        #    - Model configuration
        #    - Loaded tools (which Agent will execute, not engine)
        #    - ConversationManager for context handling
        #    - DelegatingSession proxy (handles session activation/deactivation)
        #    - Callback handlers for streaming responses
        # 4. Initialize the DelegatingSession with the agent
        
        logger.info("Setting up strands-agents Agent")
        if self.config.sessions_home:
            logger.info(f"DelegatingSession configured with sessions_home: {self.config.sessions_home}")
        if self._loaded_tools:
            logger.info(f"Agent will be configured with {len(self._loaded_tools)} tools")
        if self._conversation_manager:
            logger.info(f"Agent will use conversation manager: {self.config.conversation_manager_type}")
        
        # TODO: Create actual strands-agents Agent and initialize session proxy
        self._agent = None  # Placeholder - will be strands-agents Agent instance
        
        # TODO: Initialize the DelegatingSession with the agent
        # self._session_manager.initialize(self._agent)
        # This will activate the session if session_id was provided, or keep it inactive
    
    async def _process_with_agent(self, message: str) -> str:
        """
        Process message with the strands-agents Agent.
        
        The Agent handles all the actual work including:
        - Tool execution (engine does not execute tools)
        - LLM communication
        - Conversation management (context window, summarization, etc.)
        - Session management via DelegatingSession proxy
        - Response generation
        """
        # TODO: Implement actual agent processing
        # This will involve:
        # 1. Calling agent.stream_async() or similar strands-agents method
        # 2. The Agent will handle tool calls internally if needed
        # 3. The ConversationManager will handle context management
        # 4. The DelegatingSession will handle session persistence if active
        # 5. Return the Agent's response
        
        logger.debug("Processing with strands-agents Agent (placeholder)")
        return f"Echo: {message}"