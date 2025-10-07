"""
Core engine implementation for strands_engine.

This module provides the AgentFactory class, which serves as the main entry point
for creating and managing strands-agents Agent instances. The factory handles the
complete lifecycle of agent creation including:

- Tool discovery and loading from configuration
- Framework adapter selection and initialization  
- File content processing and upload
- Conversation management setup
- Session persistence management
- Resource cleanup and lifecycle management

The AgentFactory follows a factory pattern that separates configuration from
instantiation, allowing for flexible agent creation while managing the complexity
of the underlying strands-agents ecosystem.
"""

from contextlib import ExitStack
from typing import List, Optional

from loguru import logger
from strands import Agent

from strands_engine.agent import WrappedAgent
from strands_engine.conversation import ConversationManagerFactory
from strands_engine.framework.base_adapter import load_framework_adapter
from strands.agent.conversation_manager import ConversationManager
from strands.handlers.callback_handler import PrintingCallbackHandler

from strands_engine.utils import files_to_content_blocks

from .config import EngineConfig
from .ptypes import Tool, FrameworkAdapter
from .session import DelegatingSession
from .tools import ToolFactory


class AgentFactory:
    """
    Factory for creating configured strands-agents Agent instances.
    
    The AgentFactory provides a high-level interface for creating strands-agents
    Agent instances based on declarative configuration. It handles the complexity
    of tool loading, framework adaptation, conversation management, and resource
    lifecycle while providing a clean API for agent creation.
    
    The factory follows a two-phase initialization pattern:
    1. Constructor creates the factory with configuration
    2. initialize() method performs async setup operations
    3. create_agent() method creates the configured agent
    
    This allows for proper async resource management while maintaining a
    clean construction interface.
    
    Attributes:
        config: The EngineConfig used to configure this factory
        
    Example:
        Basic usage::
        
            config = EngineConfig(model="gpt-4o", system_prompt="Hello!")
            factory = AgentFactory(config)
            
            if await factory.initialize():
                agent = factory.create_agent()
                if agent:
                    # Use the agent for conversations
                    response = await agent.send_message_to_agent("How are you?")
    """
    
    def __init__(self, config: EngineConfig):
        """
        Initialize the AgentFactory with configuration.
        
        Creates the factory instance with the provided configuration but does
        not perform any async initialization. Call initialize() after construction
        to complete the setup process.
        
        Args:
            config: EngineConfig instance with agent parameters
        """
        self.config = config
        self._initialized = False
        self._agent = None  # strands-agents Agent instance
        self._loaded_tools: List[Tool] = []  # Tools loaded for Agent, not executed by engine
        self._framework_adapter: Optional[FrameworkAdapter] = None
        self._callback_handler : Optional[PrintingCallbackHandler] = None
        self._conversation_manager = None  # strands-agents ConversationManager
        self._exit_stack = ExitStack()  # For resource management
        self._tool_factory: Optional[ToolFactory] = None
        
        # Create DelegatingSession proxy - will be inactive if no session_id provided
        self._session_manager = DelegatingSession(
            session_name=config.session_id,
            sessions_home=config.sessions_home
        )

        self._callback_handler = PrintingCallbackHandler()

        logger.debug(f"Engine created with config: {config}")
    
    async def initialize(self) -> bool:
        """
        Perform async initialization of the agent factory.
        
        This method handles all the async setup operations required to create
        a functional agent including tool discovery, framework setup, file
        processing, and conversation management initialization.
        
        Returns:
            bool: True if initialization successful, False otherwise
            
        Note:
            This method is idempotent - calling it multiple times will not
            cause problems, though subsequent calls will return early.
        """
        if self._initialized:
            logger.warning("Engine already initialized")
            return True
            
        try:
            logger.info("Initializing strands engine...")
            
            # 1. Initialize framework adapter
            self._setup_framework_adapter()
            
            # 2. Load tools from provided config paths (for Agent configuration, not direct execution)
            await self._load_tools()
            
            # 3. Process uploaded files
            await self._load_initial_files()
            
            # 4. Create conversation manager
            self._setup_conversation_manager()
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Engine initialization failed: {e}")
            return False

    async def _load_tools(self) -> None:
        """
        Load tools from configured tool configuration paths.
        
        This method discovers tool configurations from the paths specified in
        EngineConfig.tool_config_paths and creates tool objects that will be
        passed to the strands-agents Agent for execution.
        
        Tool loading includes:
        - Configuration file discovery and parsing
        - Tool object creation and validation
        - Framework-specific tool adaptation
        - Error handling and reporting
        
        Note:
            The engine loads tools for Agent configuration but does not execute
            them directly. All tool execution is delegated to strands-agents.
        """
        if not self.config.tool_config_paths:
            return
            
        logger.debug(f"Loading tools from {len(self.config.tool_config_paths)} config paths")
        
        # Create tool factory with exit stack for resource management
        tool_factory = ToolFactory(self._exit_stack)
        
        # Discover tool configurations from provided paths
        tool_configs, discovery_result = tool_factory.load_tool_configs(self.config.tool_config_paths)
        
        if discovery_result.failed_configs:
            logger.warning(f"Failed to load {len(discovery_result.failed_configs)} tool configurations")
            for failed_config in discovery_result.failed_configs:
                logger.warning(f"  - {failed_config.get('config_id', 'unknown')}: {failed_config.get('error', 'unknown error')}")
        
        all_loaded_tools = tool_factory.create_tools(tool_configs)
        self._loaded_tools = all_loaded_tools
        self.loaded_tools = self.framework_adapter.adapt_tools(self.loaded_tools)

    async def _load_initial_files(self) -> None:
        """
        Process and load files specified in configuration.
        
        Converts file paths from EngineConfig.file_paths into content blocks
        that can be included in agent conversations. Files are processed
        according to their MIME type and made available for agent consumption.
        
        The processed files are stored as startup content that gets included
        in the agent's initial context.
        """
        if not self.config.file_paths:
            return
        
        self.startup_files_content = files_to_content_blocks(self.config.file_paths)
    
    def _setup_framework_adapter(self) -> None:
        """
        Initialize the framework adapter for the configured model.
        
        Determines the appropriate framework adapter based on the model string
        in the configuration and creates an instance. The adapter handles
        framework-specific model loading, tool adaptation, and configuration.
        
        Raises:
            ValueError: If the framework is not supported
            RuntimeError: If adapter initialization fails
        """
        self._framework_adapter = load_framework_adapter(self.framework_name)()
    
    def _setup_conversation_manager(self) -> None:
        """
        Create and configure the conversation manager.
        
        Creates the appropriate ConversationManager implementation based on
        the conversation_manager_type specified in EngineConfig. Handles
        fallback to NullConversationManager if creation fails.
        
        The conversation manager is stored in self._conversation_manager
        for use during agent creation.
        
        Note:
            This method includes error handling and fallback logic to ensure
            a ConversationManager is always available, even if configuration
            is invalid.
        """
        try:
            self._conversation_manager = ConversationManagerFactory.create_conversation_manager(self.config)
        except Exception as e:
            logger.error(f"Failed to create conversation manager: {e}")
            logger.info("Falling back to null conversation manager")
            from strands.agent.conversation_manager import NullConversationManager
            self._conversation_manager = NullConversationManager()

    def create_agent(self) -> Optional[Agent]:
        """
        Create the actual strands-agents Agent instance.
        
        This method performs the final agent creation step, bringing together
        all the initialized components (model, tools, conversation manager, etc.)
        into a functional strands-agents Agent instance.
        
        The created agent is wrapped in a WrappedAgent that provides additional
        functionality while maintaining compatibility with the strands-agents
        interface.
        
        Returns:
            Optional[Agent]: Created agent instance, or None if creation fails
            
        Example:
            Creating an agent after initialization::
            
                factory = AgentFactory(config)
                if await factory.initialize():
                    agent = factory.create_agent()
                    if agent:
                        # Agent is ready for use
                        await agent.send_message_to_agent("Hello!")
                        
        Note:
            This method should only be called after successful initialization.
            The agent is ready for immediate use after creation.
        """
        try:
            model = self.framework_adapter.create_model(self.config.model_string, self.config.model_config)
            if not model: 
                return None

            # Allow the adapter to make any necessary modifications to the tool schemas
            agent_args = self.framework_adapter.prepare_agent_args(
                system_prompt=self.config.system_prompt,
                messages=self.initial_messages,
                startup_files_content=self.config.startup_files_content,
                emulate_system_prompt=self.config.emulate_system_prompt
            )

            return WrappedAgent(
                adapter=self.framework_adapter,
                agent_id=self.config.agent_id or "strands_engine_agent",
                model=model,
                tools=self.loaded_tools,
                callback_handler=PrintingCallbackHandler(),
                session_manager=self.session_manager,
                conversation_manager=self.conversation_manager,
                **agent_args
            )
        except Exception as e:
            logger.error(f"Fatal error initializing the agent: {e}", exc_info=True)
            return None