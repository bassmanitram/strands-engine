"""
Tests for strands_engine core Engine functionality.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from strands_engine import Engine, EngineConfig
from strands_engine.ptypes import Message


class TestEngineConfig:
    """Test EngineConfig functionality."""
    
    def test_minimal_config(self):
        """Test minimal configuration."""
        config = EngineConfig(model="gpt-4o")
        assert config.model == "gpt-4o"
        assert config.system_prompt is None
        assert config.tool_config_paths == []
        assert config.file_paths == []
        assert config.sessions_home is None
        assert config.session_id is None
        # Conversation manager defaults
        assert config.conversation_manager_type == "sliding_window"
        assert config.sliding_window_size == 40
        assert config.preserve_recent_messages == 10
        assert config.summary_ratio == 0.3
    
    def test_full_config(self):
        """Test full configuration."""
        config = EngineConfig(
            model="claude-3-sonnet-20240229",
            system_prompt="You are helpful",
            tool_config_paths=["/path/to/tools.json"],
            file_paths=[("/path/to/doc.pdf", "application/pdf")],
            sessions_home="/path/to/sessions",
            session_id="test_session_123",
            conversation_manager_type="summarizing",
            sliding_window_size=20,
            preserve_recent_messages=5,
            summary_ratio=0.4,
            summarization_model="gpt-3.5-turbo",
            custom_summarization_prompt="Summarize this conversation",
            should_truncate_results=False
        )
        
        assert config.model == "claude-3-sonnet-20240229"
        assert config.system_prompt == "You are helpful"
        assert len(config.tool_config_paths) == 1
        assert len(config.file_paths) == 1
        assert config.sessions_home == Path("/path/to/sessions")
        assert config.session_id == "test_session_123"
        assert config.conversation_manager_type == "summarizing"
        assert config.sliding_window_size == 20
        assert config.preserve_recent_messages == 5
        assert config.summary_ratio == 0.4
        assert config.summarization_model == "gpt-3.5-turbo"
        assert config.custom_summarization_prompt == "Summarize this conversation"
        assert config.should_truncate_results is False
    
    def test_conversation_manager_properties(self):
        """Test conversation manager convenience properties."""
        # Test sliding window
        config1 = EngineConfig(model="gpt-4o", conversation_manager_type="sliding_window")
        assert config1.uses_conversation_manager is True
        assert config1.uses_sliding_window is True
        assert config1.uses_summarizing is False
        
        # Test summarizing
        config2 = EngineConfig(model="gpt-4o", conversation_manager_type="summarizing")
        assert config2.uses_conversation_manager is True
        assert config2.uses_sliding_window is False
        assert config2.uses_summarizing is True
        
        # Test null
        config3 = EngineConfig(model="gpt-4o", conversation_manager_type="null")
        assert config3.uses_conversation_manager is False
        assert config3.uses_sliding_window is False
        assert config3.uses_summarizing is False
    
    def test_model_parsing_properties(self):
        """Test model string parsing properties."""
        # With framework prefix
        config1 = EngineConfig(model="openai:gpt-4o")
        assert config1.framework_name == "openai"
        assert config1.model_name == "gpt-4o"
        
        # Without framework prefix
        config2 = EngineConfig(model="gpt-4o")
        assert config2.framework_name == "litellm"
        assert config2.model_name == "gpt-4o"
    
    def test_conversation_manager_validation(self):
        """Test conversation manager configuration validation."""
        # Invalid sliding window size
        with pytest.raises(ValueError, match="sliding_window_size must be at least 1"):
            EngineConfig(model="gpt-4o", sliding_window_size=0)
        
        with pytest.raises(ValueError, match="sliding_window_size cannot exceed 1000"):
            EngineConfig(model="gpt-4o", sliding_window_size=1001)
        
        # Invalid preserve_recent_messages
        with pytest.raises(ValueError, match="preserve_recent_messages must be at least 1"):
            EngineConfig(model="gpt-4o", preserve_recent_messages=0)
        
        with pytest.raises(ValueError, match="preserve_recent_messages cannot exceed 100"):
            EngineConfig(model="gpt-4o", conversation_manager_type="summarizing", preserve_recent_messages=101)
        
        # Invalid summary_ratio
        with pytest.raises(ValueError, match="summary_ratio must be between 0.1 and 0.8"):
            EngineConfig(model="gpt-4o", summary_ratio=0.05)
        
        with pytest.raises(ValueError, match="summary_ratio must be between 0.1 and 0.8"):
            EngineConfig(model="gpt-4o", summary_ratio=0.9)
        
        # Invalid summarization model format
        with pytest.raises(ValueError, match="Invalid summarization_model format"):
            EngineConfig(model="gpt-4o", summarization_model="invalid:")
        
        with pytest.raises(ValueError, match="Invalid summarization_model format"):
            EngineConfig(model="gpt-4o", summarization_model=":invalid")
    
    def test_file_paths_normalization(self):
        """Test that file paths are normalized correctly."""
        config = EngineConfig(
            model="gpt-4o",
            file_paths=[
                "/path/to/file1.txt",  # Just path
                ("/path/to/file2.pdf", "application/pdf"),  # Path with mimetype
            ]
        )
        
        assert len(config.file_paths) == 2
        assert config.file_paths[0] == (Path("/path/to/file1.txt"), None)
        assert config.file_paths[1] == (Path("/path/to/file2.pdf"), "application/pdf")
    
    def test_sessions_home_normalization(self):
        """Test that sessions_home is converted to Path."""
        config = EngineConfig(
            model="gpt-4o",
            sessions_home="/path/to/sessions"
        )
        
        assert config.sessions_home == Path("/path/to/sessions")
    
    def test_invalid_model_raises_error(self):
        """Test that missing model raises error."""
        with pytest.raises(ValueError, match="Model must be specified"):
            EngineConfig(model="")


class TestEngine:
    """Test Engine functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = EngineConfig(
            model="gpt-4o",
            system_prompt="Test assistant"
        )
    
    def test_engine_creation(self):
        """Test engine creation."""
        engine = Engine(self.config)
        assert engine.config == self.config
        assert not engine.is_ready
        assert not engine._initialized
        assert engine.session_manager is not None
        assert engine.session_manager.session_id == "inactive"
        assert engine._conversation_manager is None
        assert engine._tool_factory is None
        assert len(engine.loaded_tools) == 0
    
    def test_engine_creation_with_tool_paths(self):
        """Test engine creation with tool configuration paths."""
        config = EngineConfig(
            model="gpt-4o",
            tool_config_paths=["/path/to/tools.json", "/path/to/more_tools.yaml"]
        )
        
        engine = Engine(config)
        assert len(engine.config.tool_config_paths) == 2
        assert engine.config.tool_config_paths[0] == Path("/path/to/tools.json")
        assert engine.config.tool_config_paths[1] == Path("/path/to/more_tools.yaml")
    
    def test_engine_creation_with_conversation_manager(self):
        """Test engine creation with conversation manager configuration."""
        config = EngineConfig(
            model="gpt-4o",
            conversation_manager_type="summarizing",
            summary_ratio=0.5,
            preserve_recent_messages=15
        )
        
        engine = Engine(config)
        assert engine.config.conversation_manager_type == "summarizing"
        assert engine.config.summary_ratio == 0.5
        assert engine.config.preserve_recent_messages == 15
    
    def test_engine_creation_with_sessions(self):
        """Test engine creation with session configuration."""
        config = EngineConfig(
            model="gpt-4o",
            sessions_home="/path/to/sessions",
            session_id="test_session"
        )
        
        engine = Engine(config)
        assert engine.config.sessions_home == Path("/path/to/sessions")
        assert engine.config.session_id == "test_session"
        assert engine.session_manager.session_id == "test_session"
    
    def test_engine_creation_without_session_id(self):
        """Test engine creation without session_id remains inactive."""
        config = EngineConfig(
            model="gpt-4o",
            sessions_home="/path/to/sessions"
            # No session_id
        )
        
        engine = Engine(config)
        assert engine.session_manager.session_id == "inactive"
    
    @pytest.mark.asyncio
    async def test_initialization_no_tools(self):
        """Test engine initialization without tools."""
        engine = Engine(self.config)
        
        with patch.object(engine, '_process_files') as mock_process_files, \
             patch.object(engine, '_setup_framework_adapter') as mock_setup_adapter, \
             patch.object(engine, '_setup_conversation_manager') as mock_setup_conv_mgr, \
             patch.object(engine, '_setup_agent') as mock_setup_agent:
            
            mock_process_files.return_value = None
            mock_setup_adapter.return_value = None
            mock_setup_conv_mgr.return_value = None
            mock_setup_agent.return_value = None
            
            # Mock agent to make is_ready return True
            engine._agent = "mock_agent"
            
            success = await engine.initialize()
            
            assert success is True
            assert engine._initialized is True
            assert engine.is_ready is True
            assert len(engine.loaded_tools) == 0  # No tools loaded
            
            # Verify initialization steps were called
            mock_process_files.assert_called_once()
            mock_setup_adapter.assert_called_once()
            mock_setup_conv_mgr.assert_called_once()
            mock_setup_agent.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialization_with_tools(self):
        """Test engine initialization with tool loading."""
        # Create a temporary directory with a tool config
        with tempfile.TemporaryDirectory() as temp_dir:
            tool_config = {
                "id": "test_tool",
                "type": "python",
                "module_path": "os.path",
                "functions": ["exists"],
                "disabled": False
            }
            
            config_file = Path(temp_dir) / "test.tools.json"
            with open(config_file, 'w') as f:
                json.dump(tool_config, f)
            
            config = EngineConfig(
                model="gpt-4o",
                tool_config_paths=[temp_dir]
            )
            engine = Engine(config)
            
            with patch.object(engine, '_process_files') as mock_process_files, \
                 patch.object(engine, '_setup_framework_adapter') as mock_setup_adapter, \
                 patch.object(engine, '_setup_conversation_manager') as mock_setup_conv_mgr, \
                 patch.object(engine, '_setup_agent') as mock_setup_agent:
                
                mock_process_files.return_value = None
                mock_setup_adapter.return_value = None
                mock_setup_conv_mgr.return_value = None
                mock_setup_agent.return_value = None
                
                # Mock agent to make is_ready return True
                engine._agent = "mock_agent"
                
                success = await engine.initialize()
                
                assert success is True
                assert engine._initialized is True
                assert len(engine.loaded_tools) == 1  # One tool loaded
                assert callable(engine.loaded_tools[0])  # Should be os.path.exists
    
    @pytest.mark.asyncio
    async def test_initialization_failure(self):
        """Test engine initialization failure handling."""
        engine = Engine(self.config)
        
        with patch.object(engine, '_load_tools') as mock_load_tools:
            mock_load_tools.side_effect = Exception("Tool loading failed")
            
            success = await engine.initialize()
            
            assert success is False
            assert engine._initialized is False
    
    def test_conversation_manager_info(self):
        """Test conversation manager info property."""
        # Not initialized
        engine = Engine(self.config)
        assert "Not initialized" in engine.conversation_manager_info
        
        # Mock different conversation manager types
        engine._conversation_manager = "mock_manager"  # Just to make it not None
        
        # Test sliding window
        engine.config.conversation_manager_type = "sliding_window"
        engine.config.sliding_window_size = 30
        engine.config.should_truncate_results = True
        info = engine.conversation_manager_info
        assert "Sliding Window" in info
        assert "30" in info
        assert "with result truncation" in info
        
        # Test summarizing
        engine.config.conversation_manager_type = "summarizing"
        engine.config.summary_ratio = 0.4
        engine.config.preserve_recent_messages = 12
        info = engine.conversation_manager_info
        assert "Summarizing" in info
        assert "0.4" in info
        assert "12" in info
        
        # Test null
        engine.config.conversation_manager_type = "null"
        info = engine.conversation_manager_info
        assert "Disabled" in info
        assert "full history preserved" in info
    
    @pytest.mark.asyncio
    async def test_process_message_before_init_raises_error(self):
        """Test that processing message before initialization raises error."""
        engine = Engine(self.config)
        
        with pytest.raises(RuntimeError, match="Engine not initialized"):
            await engine.process_message("Hello")
    
    @pytest.mark.asyncio
    async def test_process_message(self):
        """Test message processing."""
        engine = Engine(self.config)
        engine._initialized = True
        engine._agent = "mock_agent"
        
        with patch.object(engine, '_process_with_agent') as mock_process:
            mock_process.return_value = "Test response"
            
            response = await engine.process_message("Hello")
            
            assert response == "Test response"
            mock_process.assert_called_once_with("Hello")
    
    @pytest.mark.asyncio
    async def test_shutdown(self):
        """Test engine shutdown."""
        engine = Engine(self.config)
        engine._initialized = True
        engine._agent = "mock_agent"
        
        await engine.shutdown()
        
        assert engine._initialized is False
    
    @pytest.mark.asyncio
    async def test_shutdown_with_sessions_home(self):
        """Test engine shutdown with sessions_home configured."""
        config = EngineConfig(
            model="gpt-4o",
            sessions_home="/path/to/sessions",
            session_id="test_session"
        )
        engine = Engine(config)
        engine._initialized = True
        engine._agent = "mock_agent"
        
        await engine.shutdown()
        
        assert engine._initialized is False
    
    @pytest.mark.asyncio
    async def test_double_initialization(self):
        """Test that double initialization is handled gracefully."""
        engine = Engine(self.config)
        
        with patch.object(engine, '_load_tools') as mock_load_tools:
            mock_load_tools.return_value = None
            engine._agent = "mock_agent"
            
            # First initialization
            success1 = await engine.initialize()
            assert success1 is True
            
            # Second initialization should return True but not re-run setup
            success2 = await engine.initialize()
            assert success2 is True
            
            # Should only have called _load_tools once
            mock_load_tools.assert_called_once()
    
    def test_loaded_tools_property(self):
        """Test loaded_tools property returns a copy."""
        engine = Engine(self.config)
        
        # Initially empty
        tools = engine.loaded_tools
        assert tools == []
        
        # Add a mock tool
        mock_tool = MagicMock()
        engine._loaded_tools.append(mock_tool)
        
        # Property should return a copy
        tools = engine.loaded_tools
        assert len(tools) == 1
        assert tools[0] is mock_tool
        
        # Modifying returned list shouldn't affect internal list
        tools.clear()
        assert len(engine._loaded_tools) == 1


class TestDelegatingSessionIntegration:
    """Test DelegatingSession integration with Engine."""
    
    def test_inactive_session(self):
        """Test that engine with no session_id has inactive session."""
        config = EngineConfig(model="gpt-4o")
        engine = Engine(config)
        
        assert engine.session_manager.session_id == "inactive"
        assert not engine.session_manager.is_active
    
    def test_active_session_configuration(self):
        """Test that engine with session_id configures active session."""
        config = EngineConfig(
            model="gpt-4o",
            sessions_home="/tmp/sessions",
            session_id="test_session"
        )
        engine = Engine(config)
        
        assert engine.session_manager.session_id == "test_session"
        # Session won't be active until agent is initialized
        assert not engine.session_manager.is_active
    
    def test_session_manager_property(self):
        """Test that session_manager property is accessible."""
        config = EngineConfig(model="gpt-4o", session_id="test")
        engine = Engine(config)
        
        session_manager = engine.session_manager
        assert session_manager is not None
        assert session_manager.session_id == "test"


class TestEngineToolIntegration:
    """Test engine integration with tool loading system."""
    
    @pytest.mark.asyncio
    async def test_disabled_tools_skipped(self):
        """Test that disabled tools are skipped during loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a disabled tool config
            tool_config = {
                "id": "disabled_tool",
                "type": "python",
                "module_path": "os.path",
                "functions": ["exists"],
                "disabled": True  # This tool is disabled
            }
            
            config_file = Path(temp_dir) / "disabled.tools.json"
            with open(config_file, 'w') as f:
                json.dump(tool_config, f)
            
            config = EngineConfig(
                model="gpt-4o",
                tool_config_paths=[temp_dir]
            )
            engine = Engine(config)
            
            # Mock other initialization steps
            with patch.object(engine, '_process_files'), \
                 patch.object(engine, '_setup_framework_adapter'), \
                 patch.object(engine, '_setup_conversation_manager'), \
                 patch.object(engine, '_setup_agent'):
                
                engine._agent = "mock_agent"
                await engine.initialize()
                
                # No tools should be loaded because it's disabled
                assert len(engine.loaded_tools) == 0
    
    @pytest.mark.asyncio
    async def test_tool_loading_error_handling(self):
        """Test error handling during tool loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create an invalid Python tool config
            tool_config = {
                "id": "invalid_tool",
                "type": "python",
                "module_path": "nonexistent_module",
                "functions": ["nonexistent_function"],
                "disabled": False
            }
            
            config_file = Path(temp_dir) / "invalid.tools.json"
            with open(config_file, 'w') as f:
                json.dump(tool_config, f)
            
            config = EngineConfig(
                model="gpt-4o",
                tool_config_paths=[temp_dir]
            )
            engine = Engine(config)
            
            # Mock other initialization steps
            with patch.object(engine, '_process_files'), \
                 patch.object(engine, '_setup_framework_adapter'), \
                 patch.object(engine, '_setup_conversation_manager'), \
                 patch.object(engine, '_setup_agent'):
                
                engine._agent = "mock_agent"
                success = await engine.initialize()
                
                # Initialization should still succeed despite tool loading failures
                assert success is True
                assert len(engine.loaded_tools) == 0  # No tools loaded due to errors