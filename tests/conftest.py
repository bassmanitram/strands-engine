"""
Pytest configuration and shared fixtures for strands_agent_factory tests.

This module provides common test fixtures, configuration, and utilities
used across the test suite.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock

import pytest
from loguru import logger

from strands_agent_factory.core.config import AgentFactoryConfig
from strands_agent_factory.core.types import ToolConfig, ToolSpec


# ============================================================================
# Test Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_network: mark test as requiring network access"
    )
    config.addinivalue_line(
        "markers", "requires_models: mark test as requiring actual model access"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Mark unit tests
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


# ============================================================================
# Logging Configuration
# ============================================================================

@pytest.fixture(autouse=True)
def configure_test_logging():
    """Configure logging for tests with appropriate levels."""
    # Remove default logger
    logger.remove()
    
    # Add test-specific logger with higher level to reduce noise
    logger.add(
        lambda msg: None,  # Suppress output during tests
        level="WARNING",
        format="{time} | {level} | {name}:{function}:{line} - {message}"
    )
    
    yield
    
    # Cleanup
    logger.remove()


# ============================================================================
# Temporary Directory Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_file(temp_dir):
    """Create a temporary file for testing."""
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("Test content")
    return file_path


@pytest.fixture
def temp_json_file(temp_dir):
    """Create a temporary JSON file for testing."""
    import json
    
    file_path = temp_dir / "test_config.json"
    test_data = {
        "id": "test_tool",
        "type": "python",
        "module_path": "test.module",
        "functions": ["test_function"]
    }
    
    with open(file_path, 'w') as f:
        json.dump(test_data, f)
    
    return file_path


@pytest.fixture
def temp_yaml_file(temp_dir):
    """Create a temporary YAML file for testing."""
    import yaml
    
    file_path = temp_dir / "test_config.yaml"
    test_data = {
        "id": "test_tool_yaml",
        "type": "mcp",
        "command": "test-server",
        "functions": ["test_function"]
    }
    
    with open(file_path, 'w') as f:
        yaml.dump(test_data, f)
    
    return file_path


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def basic_config():
    """Create a basic AgentFactoryConfig for testing."""
    return AgentFactoryConfig(
        model="anthropic:claude-3-5-sonnet",
        system_prompt="You are a helpful assistant.",
        conversation_manager_type="sliding_window",
        sliding_window_size=20
    )


@pytest.fixture
def config_with_tools(temp_json_file):
    """Create an AgentFactoryConfig with tool configuration."""
    return AgentFactoryConfig(
        model="anthropic:claude-3-5-sonnet",
        tool_config_paths=[str(temp_json_file)],
        conversation_manager_type="null"
    )


@pytest.fixture
def config_with_files(temp_file):
    """Create an AgentFactoryConfig with file uploads."""
    return AgentFactoryConfig(
        model="anthropic:claude-3-5-sonnet",
        file_paths=[(str(temp_file), "text/plain")],
        initial_message="Process this file"
    )


@pytest.fixture
def summarizing_config():
    """Create an AgentFactoryConfig with summarizing conversation manager."""
    return AgentFactoryConfig(
        model="anthropic:claude-3-5-sonnet",
        conversation_manager_type="summarizing",
        summary_ratio=0.3,
        preserve_recent_messages=5,
        summarization_model="gpt-4o-mini"
    )


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_model():
    """Create a mock strands Model for testing."""
    mock = Mock()
    mock.model_id = "test-model"
    mock.__class__.__name__ = "MockModel"
    return mock


@pytest.fixture
def mock_agent():
    """Create a mock strands Agent for testing."""
    mock = Mock()
    mock.messages = []
    mock.model = Mock()
    mock.agent_id = "test-agent"
    mock.stream_async = Mock()
    mock.__aenter__ = Mock(return_value=mock)
    mock.__aexit__ = Mock(return_value=None)
    return mock


@pytest.fixture
def mock_framework_adapter():
    """Create a mock FrameworkAdapter for testing."""
    mock = Mock()
    mock.framework_name = "test_framework"
    mock.load_model.return_value = Mock()
    mock.adapt_tools.return_value = []
    mock.prepare_agent_args.return_value = {
        "system_prompt": "Test prompt",
        "messages": []
    }
    mock.adapt_content.return_value = []
    return mock


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client for testing."""
    mock = Mock()
    mock.server_id = "test_server"
    mock.list_tools_sync.return_value = []
    mock.__enter__ = Mock(return_value=mock)
    mock.__exit__ = Mock(return_value=None)
    return mock


@pytest.fixture
def mock_callback_handler():
    """Create a mock callback handler for testing."""
    mock = Mock()
    mock.show_tool_use = False
    mock.response_prefix = None
    return mock


# ============================================================================
# Tool Configuration Fixtures
# ============================================================================

@pytest.fixture
def python_tool_config():
    """Create a Python tool configuration for testing."""
    return {
        "id": "test_python_tool",
        "type": "python",
        "module_path": "test.tools",
        "functions": ["add", "subtract"],
        "package_path": None
    }


@pytest.fixture
def mcp_tool_config():
    """Create an MCP tool configuration for testing."""
    return {
        "id": "test_mcp_server",
        "type": "mcp",
        "command": "test-mcp-server",
        "args": ["--port", "8080"],
        "functions": ["get_weather", "send_email"]
    }


@pytest.fixture
def tool_spec_python():
    """Create a Python ToolSpec for testing."""
    def mock_function(x: int, y: int) -> int:
        return x + y
    
    return {
        "tools": [mock_function],
        "client": None
    }


@pytest.fixture
def tool_spec_mcp(mock_mcp_client):
    """Create an MCP ToolSpec for testing."""
    return {
        "tools": None,
        "client": mock_mcp_client
    }


# ============================================================================
# File Content Fixtures
# ============================================================================

@pytest.fixture
def sample_text_file(temp_dir):
    """Create a sample text file for content processing tests."""
    file_path = temp_dir / "sample.txt"
    content = """This is a sample text file.
It contains multiple lines.
Used for testing file processing."""
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_json_file(temp_dir):
    """Create a sample JSON file for content processing tests."""
    import json
    
    file_path = temp_dir / "sample.json"
    data = {
        "name": "Test Data",
        "values": [1, 2, 3, 4, 5],
        "metadata": {
            "created": "2024-01-01",
            "version": "1.0"
        }
    }
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return file_path


@pytest.fixture
def sample_binary_file(temp_dir):
    """Create a sample binary file for content processing tests."""
    file_path = temp_dir / "sample.bin"
    # Create some binary data
    binary_data = bytes(range(256))
    file_path.write_bytes(binary_data)
    return file_path


@pytest.fixture
def large_file(temp_dir):
    """Create a large file for size limit testing."""
    file_path = temp_dir / "large_file.txt"
    # Create a file larger than the typical size limit
    content = "A" * (15 * 1024 * 1024)  # 15MB
    file_path.write_text(content)
    return file_path


# ============================================================================
# Session Fixtures
# ============================================================================

@pytest.fixture
def temp_sessions_dir(temp_dir):
    """Create a temporary sessions directory."""
    sessions_dir = temp_dir / "sessions"
    sessions_dir.mkdir()
    return sessions_dir


@pytest.fixture
def mock_session_manager():
    """Create a mock session manager for testing."""
    mock = Mock()
    mock.session_name = "test_session"
    mock.is_active = True
    mock.initialize = Mock()
    mock.append_message = Mock()
    mock.sync_agent = Mock()
    mock.clear = Mock()
    return mock


# ============================================================================
# Error Testing Fixtures
# ============================================================================

@pytest.fixture
def invalid_config_data():
    """Create invalid configuration data for error testing."""
    return {
        "model": "",  # Invalid empty model
        "sliding_window_size": -1,  # Invalid negative size
        "summary_ratio": 2.0,  # Invalid ratio > 1.0
        "file_paths": "not_a_list"  # Invalid type
    }


@pytest.fixture
def corrupted_json_file(temp_dir):
    """Create a corrupted JSON file for error testing."""
    file_path = temp_dir / "corrupted.json"
    file_path.write_text('{"invalid": json content}')
    return file_path


@pytest.fixture
def corrupted_yaml_file(temp_dir):
    """Create a corrupted YAML file for error testing."""
    file_path = temp_dir / "corrupted.yaml"
    file_path.write_text('invalid: yaml: content: [')
    return file_path


# ============================================================================
# Environment Fixtures
# ============================================================================

@pytest.fixture
def clean_environment():
    """Provide a clean environment for testing."""
    # Store original environment
    original_env = dict(os.environ)
    
    # Clear test-related environment variables
    test_vars = [
        'SHOW_FULL_TOOL_INPUT',
        'STRANDS_LOG_LEVEL',
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY'
    ]
    
    for var in test_vars:
        os.environ.pop(var, None)
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_env_vars():
    """Set mock environment variables for testing."""
    original_env = dict(os.environ)
    
    # Set test environment variables
    os.environ.update({
        'SHOW_FULL_TOOL_INPUT': 'true',
        'STRANDS_LOG_LEVEL': 'DEBUG',
        'TEST_MODE': 'true'
    })
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# ============================================================================
# Parametrized Fixtures
# ============================================================================

@pytest.fixture(params=["anthropic:claude-3-5-sonnet", "litellm:gpt-4o", "gpt-4o"])
def model_strings(request):
    """Parametrized fixture for different model string formats."""
    return request.param


@pytest.fixture(params=["null", "sliding_window", "summarizing"])
def conversation_manager_types(request):
    """Parametrized fixture for different conversation manager types."""
    return request.param


@pytest.fixture(params=[".json", ".yaml", ".yml"])
def config_file_extensions(request):
    """Parametrized fixture for different configuration file extensions."""
    return request.param