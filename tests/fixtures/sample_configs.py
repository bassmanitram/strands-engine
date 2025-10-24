"""
Sample configuration data for testing.

This module provides various configuration examples and test data
used across the test suite.
"""

from typing import Dict, Any, List

# ============================================================================
# Sample Tool Configurations
# ============================================================================

PYTHON_TOOL_CONFIG: Dict[str, Any] = {
    "id": "sample_python_tool",
    "type": "python",
    "module_path": "math",
    "functions": ["sqrt", "pow", "sin", "cos"],
    "package_path": None,
    "description": "Basic mathematical functions"
}

PYTHON_TOOL_CONFIG_WITH_PACKAGE: Dict[str, Any] = {
    "id": "custom_python_tool",
    "type": "python",
    "module_path": "custom.tools",
    "functions": ["process_data", "analyze_results"],
    "package_path": "tools",
    "description": "Custom data processing tools"
}

MCP_STDIO_CONFIG: Dict[str, Any] = {
    "id": "sample_mcp_stdio",
    "type": "mcp",
    "command": "sample-mcp-server",
    "args": ["--port", "8080", "--verbose"],
    "env": {
        "MCP_LOG_LEVEL": "DEBUG",
        "MCP_DATA_DIR": "/tmp/mcp_data"
    },
    "functions": ["get_weather", "send_email", "search_web"],
    "description": "Sample MCP server with stdio transport"
}

MCP_HTTP_CONFIG: Dict[str, Any] = {
    "id": "sample_mcp_http",
    "type": "mcp",
    "url": "http://localhost:8080/mcp",
    "functions": ["database_query", "file_operations"],
    "description": "Sample MCP server with HTTP transport"
}

DISABLED_TOOL_CONFIG: Dict[str, Any] = {
    "id": "disabled_tool",
    "type": "python",
    "module_path": "disabled.module",
    "functions": ["disabled_function"],
    "disabled": True,
    "description": "This tool is disabled and should be skipped"
}

INVALID_TOOL_CONFIG: Dict[str, Any] = {
    "id": "invalid_tool",
    "type": "unknown_type",
    "description": "Tool with unknown type"
}

# ============================================================================
# Sample Agent Factory Configurations
# ============================================================================

BASIC_CONFIG_DATA: Dict[str, Any] = {
    "model": "openai:gpt-4o",
    "system_prompt": "You are a helpful assistant.",
    "conversation_manager_type": "sliding_window",
    "sliding_window_size": 20
}

ADVANCED_CONFIG_DATA: Dict[str, Any] = {
    "model": "anthropic:claude-3-5-sonnet",
    "system_prompt": "You are an expert AI assistant specialized in data analysis.",
    "model_config": {
        "temperature": 0.7,
        "max_tokens": 2000,
        "top_p": 0.9
    },
    "conversation_manager_type": "summarizing",
    "summary_ratio": 0.4,
    "preserve_recent_messages": 8,
    "summarization_model": "openai:gpt-3.5-turbo",
    "custom_summarization_prompt": "Summarize the conversation concisely.",
    "show_tool_use": True,
    "response_prefix": "AI Assistant: ",
    "emulate_system_prompt": False
}

CONFIG_WITH_FILES_DATA: Dict[str, Any] = {
    "model": "openai:gpt-4o",
    "initial_message": "Please analyze the provided files.",
    "file_paths": [
        ("/path/to/document.pdf", "application/pdf"),
        ("/path/to/data.csv", "text/csv"),
        ("/path/to/image.png", "image/png")
    ]
}

CONFIG_WITH_SESSION_DATA: Dict[str, Any] = {
    "model": "openai:gpt-4o",
    "sessions_home": "/tmp/test_sessions",
    "session_id": "test_session_123",
    "conversation_manager_type": "sliding_window",
    "sliding_window_size": 50
}

INVALID_CONFIG_DATA: Dict[str, Any] = {
    "model": "",  # Invalid empty model
    "sliding_window_size": -1,  # Invalid negative size
    "summary_ratio": 2.0,  # Invalid ratio > 1.0
    "preserve_recent_messages": -5,  # Invalid negative value
    "file_paths": "not_a_list"  # Invalid type
}

# ============================================================================
# Sample Model Configurations
# ============================================================================

OPENAI_MODEL_CONFIG: Dict[str, Any] = {
    "temperature": 0.7,
    "max_tokens": 1500,
    "top_p": 0.9,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
}

ANTHROPIC_MODEL_CONFIG: Dict[str, Any] = {
    "temperature": 0.8,
    "max_tokens": 2000,
    "top_p": 0.95
}

OLLAMA_MODEL_CONFIG: Dict[str, Any] = {
    "temperature": 0.6,
    "num_ctx": 4096,
    "top_p": 0.9,
    "top_k": 40
}

BEDROCK_MODEL_CONFIG: Dict[str, Any] = {
    "temperature": 0.7,
    "max_tokens": 1000,
    "top_p": 0.9,
    "region_name": "us-east-1"
}

# ============================================================================
# Sample Message Data
# ============================================================================

SAMPLE_MESSAGES: List[Dict[str, Any]] = [
    {
        "role": "user",
        "content": [{"text": "Hello, how are you?"}]
    },
    {
        "role": "assistant", 
        "content": [{"text": "I'm doing well, thank you! How can I help you today?"}]
    },
    {
        "role": "user",
        "content": [{"text": "Can you help me with some math problems?"}]
    }
]

SAMPLE_SYSTEM_PROMPTS: List[str] = [
    "You are a helpful assistant.",
    "You are an expert in mathematics and science.",
    "You are a creative writing assistant.",
    "You are a code review assistant specialized in Python.",
    "You are a data analysis expert."
]

# ============================================================================
# Sample File Content Data
# ============================================================================

SAMPLE_TEXT_CONTENT: str = """This is a sample text file.
It contains multiple lines of text.
Used for testing file processing functionality.

The content includes:
- Plain text
- Multiple paragraphs
- Various formatting
"""

SAMPLE_JSON_CONTENT: Dict[str, Any] = {
    "name": "Sample Data",
    "version": "1.0.0",
    "data": {
        "numbers": [1, 2, 3, 4, 5],
        "strings": ["hello", "world", "test"],
        "nested": {
            "key1": "value1",
            "key2": "value2"
        }
    },
    "metadata": {
        "created": "2024-01-01T00:00:00Z",
        "author": "Test Suite"
    }
}

SAMPLE_YAML_CONTENT: str = """
name: Sample YAML Configuration
version: 1.0.0
settings:
  debug: true
  log_level: INFO
  features:
    - feature1
    - feature2
    - feature3
database:
  host: localhost
  port: 5432
  name: testdb
"""

# ============================================================================
# Error Test Data
# ============================================================================

CORRUPTED_JSON_CONTENT: str = '{"invalid": json content}'

CORRUPTED_YAML_CONTENT: str = """
invalid: yaml: content: [
  - missing closing bracket
"""

LARGE_TEXT_CONTENT: str = "A" * (15 * 1024 * 1024)  # 15MB of text

# ============================================================================
# Utility Functions
# ============================================================================

def get_sample_config(config_type: str) -> Dict[str, Any]:
    """
    Get a sample configuration by type.
    
    Args:
        config_type: Type of configuration to retrieve
        
    Returns:
        Dictionary containing the sample configuration
        
    Raises:
        ValueError: If config_type is not recognized
    """
    configs = {
        "basic": BASIC_CONFIG_DATA,
        "advanced": ADVANCED_CONFIG_DATA,
        "with_files": CONFIG_WITH_FILES_DATA,
        "with_session": CONFIG_WITH_SESSION_DATA,
        "invalid": INVALID_CONFIG_DATA
    }
    
    if config_type not in configs:
        raise ValueError(f"Unknown config type: {config_type}")
    
    return configs[config_type].copy()


def get_sample_tool_config(tool_type: str) -> Dict[str, Any]:
    """
    Get a sample tool configuration by type.
    
    Args:
        tool_type: Type of tool configuration to retrieve
        
    Returns:
        Dictionary containing the sample tool configuration
        
    Raises:
        ValueError: If tool_type is not recognized
    """
    configs = {
        "python": PYTHON_TOOL_CONFIG,
        "python_with_package": PYTHON_TOOL_CONFIG_WITH_PACKAGE,
        "mcp_stdio": MCP_STDIO_CONFIG,
        "mcp_http": MCP_HTTP_CONFIG,
        "disabled": DISABLED_TOOL_CONFIG,
        "invalid": INVALID_TOOL_CONFIG
    }
    
    if tool_type not in configs:
        raise ValueError(f"Unknown tool type: {tool_type}")
    
    return configs[tool_type].copy()


def get_sample_model_config(framework: str) -> Dict[str, Any]:
    """
    Get a sample model configuration by framework.
    
    Args:
        framework: Framework name
        
    Returns:
        Dictionary containing the sample model configuration
        
    Raises:
        ValueError: If framework is not recognized
    """
    configs = {
        "openai": OPENAI_MODEL_CONFIG,
        "anthropic": ANTHROPIC_MODEL_CONFIG,
        "ollama": OLLAMA_MODEL_CONFIG,
        "bedrock": BEDROCK_MODEL_CONFIG
    }
    
    if framework not in configs:
        raise ValueError(f"Unknown framework: {framework}")
    
    return configs[framework].copy()