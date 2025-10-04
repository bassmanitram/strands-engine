"""
Tests for strands_engine core Engine functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from strands_engine import Engine, EngineConfig
from strands_engine.types import Message


class TestEngineConfig:
    """Test EngineConfig functionality."""
    
    def test_minimal_config(self):
        """Test minimal configuration."""
        config = EngineConfig(model="gpt-4o")
        assert config.model == "gpt-4o"
        assert config.system_prompt is None
        assert config.tool_config_paths == []
        assert config.file_paths == []
    
    def test_full_config(self):
        """Test full configuration."""
        config = EngineConfig(
            model="claude-3-sonnet-20240229",
            system_prompt="You are helpful",
            tool_config_paths=["/path/to/tools.json"],
            file_paths=[("/path/to/doc.pdf", "application/pdf")],
            session_file="/path/to/session.json",
            conversation_strategy="sliding_window",
            max_context_length=4000
        )
        
        assert config.model == "claude-3-sonnet-20240229"
        assert config.system_prompt == "You are helpful"
        assert len(config.tool_config_paths) == 1
        assert len(config.file_paths) == 1
        assert config.conversation_strategy == "sliding_window"
    
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
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test engine initialization."""
        engine = Engine(self.config)
        
        with patch.object(engine, '_load_tools') as mock_load_tools, \
             patch.object(engine, '_load_session') as mock_load_session, \
             patch.object(engine, '_process_files') as mock_process_files, \
             patch.object(engine, '_setup_framework_adapter') as mock_setup_adapter, \
             patch.object(engine, '_setup_agent') as mock_setup_agent:
            
            mock_load_tools.return_value = None
            mock_load_session.return_value = None
            mock_process_files.return_value = None
            mock_setup_adapter.return_value = None
            mock_setup_agent.return_value = None
            
            # Mock agent to make is_ready return True
            engine._agent = "mock_agent"
            
            success = await engine.initialize()
            
            assert success is True
            assert engine._initialized is True
            assert engine.is_ready is True
            
            # Verify all initialization steps were called
            mock_load_tools.assert_called_once()
            mock_load_session.assert_called_once()
            mock_process_files.assert_called_once()
            mock_setup_adapter.assert_called_once()
            mock_setup_agent.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialization_failure(self):
        """Test engine initialization failure handling."""
        engine = Engine(self.config)
        
        with patch.object(engine, '_load_tools') as mock_load_tools:
            mock_load_tools.side_effect = Exception("Tool loading failed")
            
            success = await engine.initialize()
            
            assert success is False
            assert engine._initialized is False
    
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
        
        with patch.object(engine, '_process_with_agent') as mock_process, \
             patch.object(engine, '_save_session') as mock_save:
            
            mock_process.return_value = "Test response"
            mock_save.return_value = None
            
            response = await engine.process_message("Hello")
            
            assert response == "Test response"
            assert len(engine._session_messages) == 2
            assert engine._session_messages[0].role == "user"
            assert engine._session_messages[0].content == "Hello"
            assert engine._session_messages[1].role == "assistant"
            assert engine._session_messages[1].content == "Test response"
            
            mock_process.assert_called_once_with("Hello")
            mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_shutdown(self):
        """Test engine shutdown."""
        engine = Engine(self.config)
        engine._initialized = True
        engine._agent = "mock_agent"
        engine._session_messages = [Message(role="user", content="test")]
        
        with patch.object(engine, '_save_session') as mock_save:
            mock_save.return_value = None
            
            await engine.shutdown()
            
            assert engine._initialized is False
            mock_save.assert_called_once()
    
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