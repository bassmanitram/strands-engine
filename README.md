# Strands Agent Factory

A configuration-driven factory pattern for creating and managing [strands-agents](https://github.com/pydantic/strands) Agent instances. This package provides a clean abstraction layer that handles model configuration, tool loading, session management, and framework-specific adaptations.

## Features

- **🏭 Factory Pattern**: Clean separation between configuration and instantiation
- **🔧 Multi-Framework Support**: OpenAI, Anthropic, LiteLLM, Ollama, Bedrock adapters
- **🛠️ Tool Management**: Automatic tool discovery, loading, and schema adaptation
- **📁 File Processing**: Upload and process documents in various formats
- **💬 Conversation Management**: Sliding window, summarizing, and custom conversation managers
- **🔄 Session Persistence**: Save and restore conversation state
- **⚙️ Declarative Configuration**: Simple dataclass-based configuration

## Quick Start

### Installation

```bash
pip install strands-agents  # Core dependency
# Then install strands_agent_factory (when published)
```

### Basic Usage

```python
import asyncio
from strands_agent_factory import EngineConfig, AgentFactory

async def main():
    # Create configuration
    config = EngineConfig(
        model="gpt-4o",
        system_prompt="You are a helpful assistant."
    )
    
    # Create and initialize factory
    factory = AgentFactory(config)
    await factory.initialize()
    
    # Create agent and start conversation
    agent = factory.create_agent()
    success = await agent.send_message_to_agent("Hello! How are you?")

asyncio.run(main())
```

### Multi-Provider Support via LiteLLM

```python
from strands_agent_factory import EngineConfig, AgentFactory

# OpenAI
config = EngineConfig(model="litellm:gpt-4o")

# Anthropic  
config = EngineConfig(model="litellm:anthropic/claude-3-5-sonnet-20241022")

# Google Gemini
config = EngineConfig(model="litellm:gemini/gemini-2.5-flash")

# Azure OpenAI
config = EngineConfig(
    model="litellm:azure/gpt-4o",
    model_config={
        "client_args": {
            "api_key": "your-azure-key",
            "api_base": "https://your-resource.openai.azure.com/"
        }
    }
)
```

### Advanced Configuration

```python
from pathlib import Path
from strands_agent_factory import EngineConfig, AgentFactory

config = EngineConfig(
    model="anthropic:claude-3-5-sonnet-20241022",
    system_prompt="You are an advanced assistant with tools and file access.",
    
    # Conversation management
    conversation_manager_type="sliding_window",
    sliding_window_size=20,
    
    # File uploads
    file_paths=[
        ("document.pdf", "application/pdf"),
        ("data.json", "application/json")
    ],
    
    # Tool configuration
    tool_config_paths=["tools/basic_tools.json"],
    
    # Model parameters
    model_config={
        "temperature": 0.7,
        "max_tokens": 2000
    },
    
    # Session persistence
    session_id="my_session",
    sessions_home=Path("./sessions")
)

factory = AgentFactory(config)
await factory.initialize()
agent = factory.create_agent()
```

## Configuration

### EngineConfig Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `model` | `str` | Model identifier (e.g., "gpt-4o", "litellm:gemini/gemini-2.5-flash") | Required |
| `system_prompt` | `str` | System prompt for the agent | `None` |
| `conversation_manager_type` | `str` | Type of conversation manager ("null", "sliding_window", "summarizing") | `"null"` |
| `sliding_window_size` | `int` | Size of sliding window for conversation management | `20` |
| `show_tool_use` | `bool` | Whether to show tool usage in output | `True` |
| `emulate_system_prompt` | `bool` | Emulate system prompt in user messages for unsupported models | `False` |
| `model_config` | `Dict` | Framework-specific model parameters | `None` |
| `file_paths` | `List[Tuple[str, str]]` | List of (file_path, mime_type) tuples | `None` |
| `tool_config_paths` | `List[str]` | Paths to tool configuration files | `None` |
| `session_id` | `str` | Session identifier for persistence | `None` |
| `sessions_home` | `Path` | Directory for session storage | `None` |

### Model String Formats

The factory supports various model string formats:

- **Direct**: `"gpt-4o"` → OpenAI GPT-4
- **Framework Prefix**: `"anthropic:claude-3-5-sonnet-20241022"` → Anthropic Claude
- **LiteLLM**: `"litellm:provider/model"` → Any LiteLLM-supported provider
- **Empty Model ID**: `"litellm:"` → Framework with default model

## Framework Adapters

### Supported Frameworks

- **OpenAI**: Direct OpenAI API integration
- **Anthropic**: Direct Anthropic API integration  
- **LiteLLM**: Unified interface to 100+ AI providers
- **Ollama**: Local model serving
- **Bedrock**: AWS Bedrock models

### Custom Adapters

Create custom framework adapters by extending `FrameworkAdapter`:

```python
from strands_agent_factory.framework.base_adapter import FrameworkAdapter
from strands.models import Model

class MyFrameworkAdapter(FrameworkAdapter):
    @property
    def framework_name(self) -> str:
        return "myframework"
    
    def load_model(self, model_name, model_config):
        # Implement model loading logic
        return MyModel(model_name, **model_config)
    
    def adapt_tools(self, tools, model_string):
        # Implement tool adaptation logic
        return tools
```

## Tool System

### Tool Configuration

Tools are loaded from JSON configuration files:

```json
{
  "tools": [
    {
      "type": "python_function",
      "module": "my_tools.calculator",
      "config": {
        "functions": ["add", "multiply"]
      }
    },
    {
      "type": "mcp_server",
      "config": {
        "command": ["python", "-m", "mcp_server"],
        "env": {"API_KEY": "secret"}
      }
    }
  ]
}
```

### Supported Tool Types

- **Python Functions**: Load functions from Python modules
- **MCP Servers**: Model Context Protocol servers
- **Custom Tools**: Extend the tool system with custom adapters

## File Processing

Upload and process files in various formats:

```python
config = EngineConfig(
    model="gpt-4o",
    file_paths=[
        ("document.pdf", "application/pdf"),
        ("spreadsheet.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("text.txt", "text/plain"),
        ("data.json", "application/json")
    ]
)
```

Files are automatically processed and made available to the agent as context.

## Testing

### Basic Functionality Test

```bash
python test_sniff.py
```

### Full Integration Test (requires API credentials)

```bash
# Set API credentials
export GOOGLE_API_KEY="your-key"  # For Gemini
export OPENAI_API_KEY="your-key"  # For OpenAI

# Run enhanced tests
python test_sniff_with_credentials.py

# Or use the debug script
./run_sniff_debug.sh
```

## Architecture

### Factory Pattern

The factory pattern separates configuration from agent creation:

1. **Configuration**: `EngineConfig` defines all parameters
2. **Initialization**: `AgentFactory.initialize()` sets up resources  
3. **Creation**: `AgentFactory.create_agent()` returns configured agent

### Component Layers

```
┌─────────────────┐
│   Application   │
├─────────────────┤
│ strands_agent_  │
│    factory      │
├─────────────────┤
│ Framework       │
│ Adapters        │
├─────────────────┤
│ strands-agents  │
└─────────────────┘
```

### Key Components

- **AgentFactory**: Main factory class
- **EngineConfig**: Configuration dataclass
- **FrameworkAdapter**: Abstract base for model loading
- **ToolFactory**: Tool discovery and loading
- **WrappedAgent**: Enhanced agent with framework integration

## Examples

See the `examples/` directory for comprehensive usage examples:

- `basic_usage.py`: Simple agent creation and conversation
- Advanced configurations with tools and file processing
- Multi-provider examples using LiteLLM

## Error Handling

The factory provides comprehensive error handling:

```python
factory = AgentFactory(config)

# Initialization may fail due to missing credentials
success = await factory.initialize()
if not success:
    print("Check your API credentials and configuration")
    
# Agent creation may fail due to invalid model or configuration
agent = factory.create_agent()
if not agent:
    print("Agent creation failed - check logs for details")
```

## Logging

Enable debug logging for troubleshooting:

```python
import logging
logging.getLogger("strands_agent_factory").setLevel(logging.DEBUG)

# Or with loguru
from loguru import logger
logger.configure(level="DEBUG")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run the sniff tests
5. Submit a pull request

## License

[License details]

## Support

- **Issues**: GitHub Issues
- **Documentation**: See examples and docstrings
- **Testing**: Use the provided sniff tests for validation