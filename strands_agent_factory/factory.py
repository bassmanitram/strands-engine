"""
Core engine implementation for strands_agent_factory.

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
from typing import List, Optional, Tuple

from loguru import logger
from strands import Agent

from strands_agent_factory.agent import WrappedAgent
from strands_agent_factory.conversation import ConversationManagerFactory
from strands_agent_factory.framework.base_adapter import load_framework_adapter
from strands.agent.conversation_manager import ConversationManager
from strands.handlers.callback_handler import PrintingCallbackHandler
from strands.types.content import Messages

from strands_agent_factory.messages import generate_llm_messages
from strands_agent_factory.utils import files_to_content_blocks, paths_to_file_references

from .config import AgentFactoryConfig
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
    
    def __init__(self, config: AgentFactoryConfig):
        """
        Initialize the AgentFactory with configuration.
        
        Creates the factory instance with the provided configuration but does
        not perform any async initialization. Call initialize() after construction
        to complete the setup process.
        
        Args:
            config: EngineConfig instance with agent parameters
        """
        logger.debug(f"AgentFactory.__init__ called with config: {config}")
        
        self.config = config
        self._initialized = False
        self._agent = None  # strands-agents Agent instance
        self._loaded_tools: List[Tool] = []  # Tools loaded for Agent, not executed by factory
        self._framework_adapter: Optional[FrameworkAdapter] = None
        self._callback_handler : Optional[PrintingCallbackHandler] = None
        self._conversation_manager = None  # strands-agents ConversationManager
        self._exit_stack = ExitStack()  # For resource management
        self._tool_factory: Optional[ToolFactory] = None
        self._initial_messages: Optional[Messages] = None
        
        # Parse model string into framework and model parts during initialization
        self._framework_name, self._model_id = self._parse_model_string(config.model)
        
        # Create DelegatingSession proxy - will be inactive if no session_id provided
        self._session_manager = DelegatingSession(
            session_name=config.session_id,
            sessions_home=config.sessions_home
        )

        self._callback_handler = PrintingCallbackHandler()

        logger.debug(f"Factory created with config: {config}")
        logger.debug(f"Parsed model string '{config.model}' -> framework='{self._framework_name}', model_id='{self._model_id}'")
    
    def _parse_model_string(self, model_string: str) -> Tuple[str, str]:
        """
        Parse model string into framework and model ID parts.
        
        Handles various model string formats:
        - "gpt-4o" -> ("openai", "gpt-4o")
        - "litellm:gemini/gemini-2.5-flash" -> ("litellm", "gemini/gemini-2.5-flash") 
        - "anthropic:claude-3-5-sonnet" -> ("anthropic", "claude-3-5-sonnet")
        - "litellm:" -> ("litellm", "")  # Empty model ID is allowed
        - "ollama:llama2" -> ("ollama", "llama2")
        
        Args:
            model_string: Model identifier string from configuration
            
        Returns:
            Tuple[str, str]: (framework_name, model_id) where model_id can be empty
        """
        logger.debug(f"_parse_model_string called with model_string: '{model_string}'")
        
        if ":" in model_string:
            # Format like "framework:model_id" or "framework:" (empty model_id)
            framework, model_id = model_string.split(":", 1)
            result = (framework.lower(), model_id)
        else:
            # Default to OpenAI for simple model names like "gpt-4o"
            result = ("openai", model_string)
        
        logger.debug(f"_parse_model_string returning: {result}")
        return result
    
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
        logger.debug(f"initialize called, _initialized={self._initialized}")
        
        if self._initialized:
            logger.warning("Factory already initialized")
            return True
            
        try:
            logger.info("Initializing strands agent factory...")
            
            # 1. Initialize framework adapter
            self._setup_framework_adapter()
            
            # 2. Load tools from provided config paths (for Agent configuration, not direct execution)
            await self._load_tools()
            
            # 3. Initial messages
            await self._build_initial_messages()
            
            # 4. Create conversation manager
            self._setup_conversation_manager()
            
            self._initialized = True
            logger.debug("initialize completed successfully")
            return True
            
        except Exception as e:
            logger.exception("Factory initialization failed")
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
            The factory loads tools for Agent configuration but does not execute
            them directly. All tool execution is delegated to strands-agents.
        """
        logger.debug(f"_load_tools called with tool_config_paths: {self.config.tool_config_paths}")
        
        if not self.config.tool_config_paths:
            logger.debug("No tool config paths provided, skipping tool loading")
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
        logger.debug(f"Loaded {len(self._loaded_tools)} tools")
        
        # Adapt tools for the specific framework after adapter is set up
        if self._framework_adapter:
            logger.debug(f"Adapting tools for framework: {self._framework_name}")
            self._loaded_tools = self._framework_adapter.adapt_tools(self._loaded_tools, self._model_id)
            logger.debug(f"Tool adaptation completed, {len(self._loaded_tools)} tools after adaptation")

    async def _build_initial_messages(self) -> None:
        logger.debug(f"_build_initial_messages called with file_paths: {self.config.file_paths}; initial_message:  {self.config.initial_message}")

        if not (self.config.file_paths or self.config.initial_message):
            logger.debug("No file paths provided, skipping file loading")
            return
        
        initial_message = self.config.initial_message or "The user has provided the following resources. Acknowledge receipt and await instructions."
        startup_files_references = paths_to_file_references(self.config.file_paths) if self.config.file_paths else []

        self._initial_messages = generate_llm_messages("\n".join([initial_message] + startup_files_references))

        logger.debug(f"Created initial messages")
    
    def _setup_framework_adapter(self) -> None:
        """
        Initialize the framework adapter for the configured model.
        
        Uses the parsed framework name to load the appropriate adapter.
        The adapter handles framework-specific model loading, tool adaptation, 
        and configuration.
        
        Raises:
            ValueError: If the framework is not supported
            RuntimeError: If adapter initialization fails
        """
        logger.debug(f"_setup_framework_adapter called with framework_name: '{self._framework_name}'")
        
        self._framework_adapter = load_framework_adapter(self._framework_name)
        if not self._framework_adapter:
            logger.error(f"Failed to load framework adapter for: {self._framework_name}")
            raise ValueError(f"Unsupported framework: {self._framework_name}")
        
        logger.debug(f"Framework adapter loaded successfully: {type(self._framework_adapter).__name__}")
    
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
        logger.debug(f"_setup_conversation_manager called with conversation_manager_type: {self.config.conversation_manager_type}")
        
        try:
            self._conversation_manager = ConversationManagerFactory.create_conversation_manager(self.config)
            logger.debug(f"Conversation manager created: {type(self._conversation_manager).__name__}")
        except Exception as e:
            logger.error(f"Failed to create conversation manager: {e}")
            logger.info("Falling back to null conversation manager")
            from strands.agent.conversation_manager import NullConversationManager
            self._conversation_manager = NullConversationManager()
            logger.debug("Fallback conversation manager created: NullConversationManager")

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
        logger.debug(f"create_agent called, _initialized={self._initialized}, _framework_adapter={self._framework_adapter is not None}")
        
        if not self._initialized:
            logger.error("Cannot create agent: factory not initialized. Call initialize() first.")
            return None
            
        if not self._framework_adapter:
            logger.error("Cannot create agent: no framework adapter available")
            return None
            
        try:
            # Pass the parsed model_id (without framework prefix) to the adapter
            # The model_id can be empty string if the format was "framework:"
            logger.debug(f"Loading model with model_id='{self._model_id}', model_config={self.config.model_config}")
            model = self._framework_adapter.load_model(self._model_id, self.config.model_config)
            if not model: 
                logger.error("Framework adapter returned None for model")
                return None
            
            logger.debug(f"Model loaded successfully: {type(model).__name__}")

            # Allow the adapter to make any necessary modifications to the tool schemas
            logger.debug(f"Preparing agent args with system_prompt={self.config.system_prompt is not None}, emulate_system_prompt={self.config.emulate_system_prompt}")
            agent_args = self._framework_adapter.prepare_agent_args(
                system_prompt=self.config.system_prompt,
                emulate_system_prompt=self.config.emulate_system_prompt,
                messages=self._initial_messages
            )
            logger.debug(f"Agent args prepared: {list(agent_args.keys())}")

            logger.debug(f"Creating WrappedAgent with {len(self._loaded_tools)} tools")
            wrapped_agent = WrappedAgent(
                adapter=self._framework_adapter,
                agent_id="strands_agent_factory_agent",
                model=model,
                tools=self._loaded_tools,
                callback_handler=self._callback_handler,
                session_manager=self._session_manager,
                conversation_manager=self._conversation_manager,
                **agent_args
            )
            logger.debug(f"WrappedAgent created successfully: {type(wrapped_agent).__name__}")

            return wrapped_agent
            
        except Exception as e:
            logger.exception("Error initializing the agent")
            return None