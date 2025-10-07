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
    def __init__(self, config: EngineConfig):
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
        if self._initialized:
            logger.warning("Engine already initialized")
            return True
            
        try:
            logger.info("Initializing strands engine...")
            
            # 3. Initialize framework adapter
            self._setup_framework_adapter()
            
            # 1. Load tools from provided config paths (for Agent configuration, not direct execution)
            await self._load_tools()
            
            # 2. Process uploaded files
            await self._load_initial_files()
            
            # 4. Create conversation manager
            self._setup_conversation_manager()
            
            return True
            
        except Exception as e:
            logger.error(f"Engine initialization failed: {e}")
            return False
    
    async def process_message(self, message: str) -> str:
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
    
    async def _load_tools(self) -> None:
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
        if not self.config.file_paths:
            return
        
        self.startup_files_content = files_to_content_blocks(self.config.file_paths)
    
    def _setup_framework_adapter(self) -> None:
        self._framework_adapter = load_framework_adapter(self.framework_name)()
    
    def _create_conversation_manager(self) -> ConversationManager:
        try:
            manager = ConversationManagerFactory.create_conversation_manager(self.config)
            return manager
        except Exception as e:
            logger.error(f"Failed to create conversation manager: {e}")
            logger.info("Falling back to null conversation manager")
            from strands.agent.conversation_manager import NullConversationManager
            return NullConversationManager()

    def create_agent(self) -> Optional[Agent]:
        try:
            model = self.framework_adapter.create_model(self.config.model_string, self.config.model_config)
            if not model: return None

            # Allow the adapter to make any necessary modifications to the tool schemas.

            agent_args = self.framework_adapter.prepare_agent_args(
                system_prompt=self.config.system_prompt,
                messages=self.initial_messages,
                startup_files_content=self.config.startup_files_content,
                emulate_system_prompt=self.config.emulate_system_prompt
            )

            self.agent = WrappedAgent(
                adapter=self.framework_adapter,
                agent_id=self.config.agent_id or "yacba_agent",
                model=model,
                tools=self.loaded_tools,
                callback_handler=PrintingCallbackHandler(),
                session_manager=self.session_manager,
                conversation_manager=self.conversation_manager,  # Add conversation manager
                **agent_args
            )

            return self.agent
        except Exception as e:
            logger.error(f"Fatal error initializing the agent: {e}", exc_info=True)
            return None
