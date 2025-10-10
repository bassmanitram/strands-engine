# Strands Agent Factory

A configuration-driven factory framework for creating and managing [strands-agents](https://github.com/pydantic/strands) Agent instances. This package provides a clean abstraction layer that handles multi-framework AI provider support, tool management, session persistence, and conversation management.

## Features

- **🏭 Factory Pattern**: Clean separation between configuration and instantiation
- **🌐 Multi-Framework Support**: OpenAI, Anthropic, LiteLLM, Ollama, AWS Bedrock adapters
- **🛠️ Advanced Tool System**: Python functions, MCP servers, automatic schema adaptation
- **📁 File Processing**: Upload and process documents in various formats with smart content extraction
- **💬 Smart Conversation Management**: Sliding window, summarizing, and custom strategies
- **🔄 Session Persistence**: Save and restore conversation state across sessions
- **⚙️ Declarative Configuration**: Simple dataclass-based configuration with validation
- **🔧 Extensible Architecture**: Plugin system for custom adapters and tools

## Quick Start

### Installation

```bash
# Basic installation with core functionality
pip install strands-agent-factory

# Install with specific AI provider support
pip install "strands-agent-factory[litellm]"      # LiteLLM (100+ providers)
pip install "strands-agent-factory[anthropic]"    # Anthropic Claude
pip install "strands-agent-factory[openai]"       # OpenAI GPT models
pip install "strands-agent-factory[ollama]"       # Ollama local models
pip install "strands-agent-factory[bedrock]"      # AWS Bedrock

# Install with multiple providers
pip install "strands-agent-factory[anthropic,openai,litellm]"

# Install with all providers
pip install "strands-agent-factory[all-providers]"

# Install with tools integration (optional)
pip install "strands-agent-factory[tools]"

# Full installation with everything
pip install "strands-agent-factory[full]"
```

**Note**: The framework extras (`[litellm]`, `[anthropic]`, etc.) automatically install the correct `strands-agents[framework]` dependencies with all required packages.

### Basic Usage

```python
import asyncio
from strands_agent_factory import AgentFactoryConfig, AgentFactory

async def main():
    # Create configuration
    config = AgentFactoryConfig(
        model="gpt-4o",
        system_prompt="You are a helpful assistant."
    )
    
    # Create and initialize factory
    factory = AgentFactory(config)
    await factory.initialize()
    
    # Create agent and start conversation
    agent = factory.create_agent()
    
    with agent as a:
        success = await a.send_message_to_agent("Hello! How are you?")

asyncio.run(main())
```

### Multi-Provider Support

```python
from strands_agent_factory import AgentFactoryConfig, AgentFactory

# OpenAI (requires: pip install "strands-agent-factory[openai]")
config = AgentFactoryConfig(model="gpt-4o")

# Anthropic (requires: pip install "strands-agent-factory[anthropic]")  
config = AgentFactoryConfig(model="anthropic:claude-3-5-sonnet-20241022")

# Google Gemini (requires: pip install "strands-agent-factory[litellm]")
config = AgentFactoryConfig(model="litellm:gemini/gemini-2.5-flash")

# Ollama (requires: pip install "strands-agent-factory[ollama]")
config = AgentFactoryConfig(model="ollama:llama3.1:8b")

# AWS Bedrock (requires: pip install "strands-agent-factory[bedrock]")
config = AgentFactoryConfig(model="bedrock:anthropic.claude-3-sonnet-20240229-v1:0")
```

### Advanced Configuration

```python
from pathlib import Path
from strands_agent_factory import AgentFactoryConfig, AgentFactory

config = AgentFactoryConfig(
    model="anthropic:claude-3-5-sonnet-20241022",
    system_prompt="You are an advanced assistant with tools and file access.",
    
    # Conversation management
    conversation_manager_type="sliding_window",
    sliding_window_size=40,
    
    # File uploads with automatic processing
    file_paths=[
        ("document.pdf", "application/pdf"),
        ("data.csv", "text/csv"),
        ("config.json", "application/json")
    ],
    
    # Tool configuration paths
    tool_config_paths=["tools/", "custom_tools.json"],
    
    # Model parameters
    model_config={
        "temperature": 0.7,
        "max_tokens": 4000
    },
    
    # Session persistence
    session_id="research_session_001",
    sessions_home=Path("./sessions")
)

factory = AgentFactory(config)
await factory.initialize()
agent = factory.create_agent()
```

## Installation Options

### Framework Dependencies

strands-agent-factory uses `strands-agents[framework]` extras to ensure all necessary dependencies are installed:

| Extra | Includes | Use For |
|-------|----------|---------|
| `[litellm]` | `strands-agents[litellm]` | 100+ AI providers via LiteLLM |
| `[anthropic]` | `strands-agents[anthropic]` | Direct Anthropic Claude API |
| `[openai]` | `strands-agents[openai]` | Direct OpenAI GPT API |
| `[ollama]` | `strands-agents[ollama]` | Ollama local models |
| `[bedrock]` | `strands-agents[bedrock]` | AWS Bedrock models |
| `[tools]` | `strands-agents-tools` | strands-tools integration |
| `[all-providers]` | All framework extras | Everything except tools |
| `[full]` | All extras including dev tools | Complete installation |

### Development Installation

```bash
# Clone repository
git clone https://github.com/bassmanitram/strands-agent-factory.git
cd strands-agent-factory

# Install in development mode with all features
pip install -e ".[full]"

# Or minimal development setup
pip install -e ".[dev]"
```

## Architecture

### Modern Modular Structure

```
strands_agent_factory/
├── core/                    # Core functionality
│   ├── factory.py          # Main AgentFactory
│   ├── agent.py            # AgentProxy wrapper
│   ├── config.py           # Configuration classes
│   └── types.py            # Type definitions
├── adapters/               # Framework adapters
│   ├── base.py            # Base adapter interface
│   ├── openai.py          # OpenAI integration
│   ├── anthropic.py       # Anthropic integration
│   ├── litellm.py         # LiteLLM (100+ providers)
│   ├── ollama.py          # Local models
│   └── bedrock.py         # AWS Bedrock
├── tools/                  # Tool management
│   ├── factory.py         # Tool loading & configuration
│   └── python.py          # Python function utilities
├── messaging/              # Message processing
│   ├── generator.py       # Message generation with file()
│   └── content.py         # File content processing
├── session/                # Session management
│   ├── manager.py         # Session persistence
│   └── conversation.py    # Conversation strategies
└── handlers/               # Event handlers
    └── callback.py        # Output handling
```

### Factory Pattern Benefits

- **Separation of Concerns**: Configuration, initialization, and usage are cleanly separated
- **Resource Management**: Automatic cleanup of MCP servers and sessions
- **Framework Abstraction**: Unified interface across different AI providers
- **Extensibility**: Plugin architecture for custom adapters and tools

## Configuration

### AgentFactoryConfig Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `model` | `str` | Model identifier with optional framework prefix | Required |
| `system_prompt` | `Optional[str]` | System prompt for the agent | `None` |
| `initial_message` | `Optional[str]` | Initial user message (sent with files) | `None` |
| `model_config` | `Optional[Dict[str, Any]]` | Framework-specific model parameters | `None` |
| `tool_config_paths` | `List[PathLike]` | Paths to tool configuration files/dirs | `[]` |
| `file_paths` | `List[Tuple[PathLike, Optional[str]]]` | Files as (path, mimetype) tuples | `[]` |
| `sessions_home` | `Optional[PathLike]` | Directory for session storage | `None` |
| `session_id` | `Optional[str]` | Session identifier for persistence | `None` |
| `conversation_manager_type` | `ConversationManagerType` | Strategy: "null", "sliding_window", "summarizing" | `"sliding_window"` |
| `sliding_window_size` | `int` | Number of messages to keep in sliding window | `40` |
| `preserve_recent_messages` | `int` | Messages to preserve in summarizing mode | `10` |
| `summary_ratio` | `float` | Ratio of messages to summarize (0.1-0.8) | `0.3` |
| `summarization_model` | `Optional[str]` | Optional separate model for summarization | `None` |
| `custom_summarization_prompt` | `Optional[str]` | Custom prompt for summarization | `None` |
| `should_truncate_results` | `bool` | Whether to truncate tool results on overflow | `True` |
| `emulate_system_prompt` | `bool` | Emulate system prompt for unsupported models | `False` |
| `show_tool_use` | `bool` | Show detailed tool execution | `False` |

### Model String Formats

The factory intelligently handles various model identifier formats:

```python
# Direct provider names (defaults to OpenAI)
"gpt-4o"                    # → OpenAI GPT-4
"gpt-4o-mini"              # → OpenAI GPT-4 Mini

# Explicit framework prefixes
"anthropic:claude-3-5-sonnet-20241022"     # → Anthropic Claude
"ollama:llama3.1:8b"                       # → Ollama Llama
"bedrock:anthropic.claude-3-sonnet"        # → AWS Bedrock

# LiteLLM for 100+ providers
"litellm:gemini/gemini-2.5-flash"          # → Google Gemini
"litellm:azure/gpt-4o"                     # → Azure OpenAI
"litellm:openrouter/anthropic/claude-3.5"  # → OpenRouter
"litellm:cohere/command-r-plus"            # → Cohere
```

## Framework Adapters

### Built-in Adapters

- **OpenAI**: Direct OpenAI API with all GPT models
- **Anthropic**: Direct Anthropic API with Claude models  
- **LiteLLM**: Unified interface to 100+ providers (Gemini, Azure, Cohere, etc.)
- **Ollama**: Local model serving with custom models
- **Bedrock**: AWS Bedrock with Claude, Titan, and other models

### Custom Framework Adapters

Extend support to new AI providers:

```python
from strands_agent_factory.adapters.base import FrameworkAdapter
from strands.models import Model

class MyProviderAdapter(FrameworkAdapter):
    @property
    def framework_name(self) -> str:
        return "myprovider"
    
    def load_model(self, model_name, model_config):
        # Implement provider-specific model loading
        return MyProviderModel(model_name, **model_config or {})
    
    def adapt_tools(self, tools, model_string):
        # Adapt tool schemas for provider compatibility
        return [self._adapt_tool_schema(tool) for tool in tools]
```

## Advanced Tool System

### Tool Configuration

Tools are loaded from JSON/YAML configuration files with flexible discovery:

```json
{
  "tools": [
    {
      "type": "python_function",
      "module": "my_tools.calculator", 
      "config": {
        "functions": ["add", "multiply", "divide"],
        "package_path": "src/",
        "base_path": "/project/root"
      }
    },
    {
      "type": "mcp_server",
      "config": {
        "command": ["python", "-m", "my_mcp_server"],
        "args": ["--port", "8080"],
        "env": {"API_KEY": "${SECRET_KEY}"},
        "functions": ["search", "analyze"]
      }
    }
  ]
}
```

### Tool Types

- **Python Functions**: Load functions from any Python module/package
- **MCP Servers**: Model Context Protocol servers via stdio or HTTP
- **Custom Tools**: Extend with custom tool adapters

### Automatic Tool Discovery

```python
# Load tools from multiple sources
config = AgentFactoryConfig(
    model="gpt-4o",
    tool_config_paths=[
        "tools/",                    # Directory scan
        "custom_tools.json",         # Specific file
    ]
)
```

## Smart File Processing

### File Upload with Content Extraction

```python
config = AgentFactoryConfig(
    model="gpt-4o",
    file_paths=[
        ("research.pdf", "application/pdf"),        # PDF extraction
        ("data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("notes.md", "text/markdown"),              # Markdown processing
        ("results.csv", "text/csv"),                # CSV parsing
        ("config.json", "application/json")         # JSON structure
    ],
    initial_message="Analyze these documents and provide insights."
)
```

### Dynamic File References

Use `file()` syntax in messages for dynamic file inclusion:

```python
# In your prompts or messages
message = """
Please analyze the following files:
file('data/*.csv')
file('reports/summary.pdf', 'application/pdf')

What patterns do you see in the data?
"""
```

## Conversation Management

### Sliding Window Strategy

Automatically manages context length by keeping recent messages:

```python
config = AgentFactoryConfig(
    model="gpt-4o",
    conversation_manager_type="sliding_window",
    sliding_window_size=40  # Keep last 40 messages
)
```

### Summarizing Strategy

Intelligently summarizes older messages while preserving recent context:

```python
config = AgentFactoryConfig(
    model="gpt-4o", 
    conversation_manager_type="summarizing",
    preserve_recent_messages=10,  # Never summarize last 10
    summary_ratio=0.3,            # Summarize 30% of older messages
    summarization_model="gpt-4o-mini"  # Use cheaper model for summaries
)
```

## Session Persistence

### Automatic Session Management

```python
config = AgentFactoryConfig(
    model="gpt-4o",
    session_id="user_123_project_alpha",
    sessions_home=Path("./user_sessions")
)

factory = AgentFactory(config)
await factory.initialize()

# Sessions automatically save/restore conversation state
agent = factory.create_agent()
```

### Session Directory Structure

```
user_sessions/
├── user_123_project_alpha/
│   ├── conversation.json      # Message history
│   ├── metadata.json         # Session metadata
│   └── uploads/              # Uploaded files
└── other_session_id/
    └── ...
```

## Examples & Use Cases

### Research Assistant

```python
config = AgentFactoryConfig(
    model="anthropic:claude-3-5-sonnet-20241022",
    system_prompt="You are a research assistant with access to document analysis tools.",
    tool_config_paths=["tools/research_tools.json"],
    file_paths=[
        ("papers/*.pdf", "application/pdf"),
        ("data/*.csv", "text/csv")
    ],
    conversation_manager_type="summarizing",
    session_id="research_2024"
)
```

### Code Assistant

```python
config = AgentFactoryConfig(
    model="gpt-4o",
    system_prompt="You are a code assistant with access to development tools.",
    tool_config_paths=["tools/dev_tools/"],
    file_paths=[
        ("src/**/*.py", "text/plain"),
        ("requirements.txt", "text/plain"),
        ("README.md", "text/markdown")
    ],
    conversation_manager_type="sliding_window",
    sliding_window_size=50
)
```

### Multi-Modal Analysis

```python
config = AgentFactoryConfig(
    model="litellm:gemini/gemini-2.0-flash-exp",  # Supports vision
    system_prompt="Analyze documents and images for insights.",
    file_paths=[
        ("charts/*.png", "image/png"),
        ("reports/*.pdf", "application/pdf"),
        ("data/*.json", "application/json")
    ],
    tool_config_paths=["tools/analysis_tools.yaml"]
)
```

## Testing & Development

### Quick Functionality Test

```bash
python test_messages.py
```

### Integration Testing

```bash
# Set up API credentials
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"  
export GOOGLE_API_KEY="your-key"

# Run comprehensive tests
python test_sniff_with_credentials.py

# Interactive demo
./demo-headless.sh
```

### Development Tools

```bash
# Install development dependencies
pip install -e ".[dev]"

# Code formatting
black strands_agent_factory/
isort strands_agent_factory/

# Type checking
mypy strands_agent_factory/

# Run tests
pytest tests/
```

## Error Handling & Debugging

### Comprehensive Error Handling

```python
factory = AgentFactory(config)

# Initialization may fail due to credentials/configuration
success = await factory.initialize()
if not success:
    logger.error("Factory initialization failed - check credentials and config")
    return

# Agent creation may fail due to invalid model
agent = factory.create_agent()
if not agent:
    logger.error("Agent creation failed - check model name and configuration")
    return

# Use context manager for proper resource cleanup
with agent as a:
    success = await a.send_message_to_agent("Hello")
    if not success:
        logger.error("Message processing failed")
```

### Debug Logging

```python
# Enable trace-level logging for detailed debugging
from loguru import logger
logger.remove()
logger.add(sys.stderr, level="TRACE")

# Or configure specific loggers
import logging
logging.getLogger("strands_agent_factory").setLevel(logging.DEBUG)
```

## Performance & Scalability

### Resource Management

- **Automatic Cleanup**: Context managers ensure proper resource cleanup
- **Connection Pooling**: Framework adapters manage connections efficiently  
- **Memory Management**: Conversation strategies prevent memory bloat
- **Concurrent Safety**: Thread-safe MCP server initialization

### Best Practices

- Use sliding window for long conversations
- Choose appropriate models for different tasks (GPT-4 for complex reasoning, GPT-4-mini for simple tasks)
- Configure session persistence for multi-turn interactions
- Use MCP servers for external system integration

## Contributing

We welcome contributions! Please see our contribution guidelines:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Make** your changes with comprehensive tests
4. **Test** using the sniff tests: `./demo-headless.sh`
5. **Submit** a pull request with detailed description

### Development Setup

```bash
git clone https://github.com/your-username/strands-agent-factory.git
cd strands-agent-factory
pip install -e ".[dev,all-providers]"
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support & Community

- **🐛 Issues**: [GitHub Issues](https://github.com/bassmanitram/strands-agent-factory/issues)
- **📖 Documentation**: See examples and comprehensive docstrings
- **🧪 Testing**: Use provided test suite for validation
- **💬 Discussions**: GitHub Discussions for questions and ideas

## Roadmap

- [ ] Enhanced MCP server discovery and management
- [ ] Plugin system for custom conversation managers
- [ ] Streaming response support for all frameworks
- [ ] Advanced file processing with OCR and vision models
- [ ] Distributed agent orchestration
- [ ] Web UI for configuration and testing