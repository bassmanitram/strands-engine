# Strands Agent Factory

A configuration-driven factory framework for creating and managing [strands-agents](https://github.com/strands-agents) Agent instances. This package provides a clean abstraction layer that handles multi-framework AI provider support, tool management, session persistence, and conversation management.

## Features

- **Factory Pattern**: Clean separation between configuration and instantiation
- **Multi-Framework Support**: Automatic support for any strands-compatible framework plus specialized adapters
- **Advanced Tool System**: Python functions, MCP servers, A2A agent communication, automatic schema adaptation
- **File Processing**: Upload and process documents in various formats with smart content extraction
- **Smart Conversation Management**: Sliding window, summarizing, and custom strategies
- **Session Persistence**: Save and restore conversation state across sessions
- **Declarative Configuration**: Simple dataclass-based configuration with validation
- **File-Loadable CLI Parameters**: Load long prompts and configurations from files using `@filename` syntax
- **CLI Tools**: Interactive chatbot and A2A server with full CLI configuration support  
- **Extensible Architecture**: Plugin system for custom adapters and tools

## Quick Start

### Installation

```bash
# Basic installation with core functionality
pip install strands-agent-factory

# Install with specific AI provider support
pip install "strands-agent-factory[anthropic]"    # Anthropic Claude
pip install "strands-agent-factory[openai]"       # OpenAI GPT models
pip install "strands-agent-factory[litellm]"      # LiteLLM (100+ providers)
pip install "strands-agent-factory[ollama]"       # Ollama local models
pip install "strands-agent-factory[bedrock]"      # AWS Bedrock

# Install with multiple providers
pip install "strands-agent-factory[anthropic,openai,litellm]"

# Install with all providers
pip install "strands-agent-factory[all-providers]"

# Install with tools integration (optional)
pip install "strands-agent-factory[tools]"        # Python functions, MCP tools
pip install "strands-agent-factory[a2a]"          # Agent-to-Agent communication

# Install with all tools
pip install "strands-agent-factory[all-tools]"

# Full installation with everything
pip install "strands-agent-factory[full]"
```

**Note**: The framework extras automatically install the correct `strands-agents[framework]` dependencies with all required packages.

## CLI Tools

After installation, two command-line tools are available:

### Interactive Chatbot

```bash
# Basic usage with default model
strands-chatbot --model gpt-4o

# With custom system prompt and tools
strands-chatbot \
  --model anthropic:claude-3-5-sonnet-20241022 \
  --system-prompt "You are a helpful coding assistant" \
  --tool-config-paths tools/code_tools.json tools/file_tools.json \
  --show-tool-use

# Load system prompt from file (new file-loadable feature!)
strands-chatbot \
  --model gpt-4o \
  --system-prompt "@prompts/coding_assistant.txt" \
  --custom-summarization-prompt "@prompts/tech_summary.txt" \
  --conversation-manager-type summarizing

# Load from configuration file
strands-chatbot --agent-config my_chatbot_config.yaml

# With file uploads for analysis
strands-chatbot \
  --model gpt-4o \
  --file-paths "document.pdf,application/pdf" "data.csv,text/csv" \
  --initial-message "Please analyze these files"

# All CLI options from AgentFactoryConfig are available:
strands-chatbot \
  --model litellm:gemini/gemini-2.5-flash \
  --conversation-manager-type summarizing \
  --sliding-window-size 50 \
  --session-id research_session \
  --response-prefix "AI: "
```

### A2A Server

```bash
# Run any agent configuration as an A2A server
strands-a2a-server \
  --model gpt-4o \
  --system-prompt "I am a specialist math agent" \
  --tool-config-paths tools/math_tools.json \
  --host 0.0.0.0 --port 8001

# Load system prompt from file
strands-a2a-server \
  --model gpt-4o \
  --system-prompt "@prompts/math_specialist.txt" \
  --tool-config-paths tools/math_tools.json \
  --port 8001

# Load from configuration file  
strands-a2a-server --agent-config specialist_agent.yaml --port 8002
```

### File-Loadable CLI Parameters

Several CLI parameters support loading content from files using the `@filename` syntax:

- `--system-prompt @path/to/prompt.txt` - Load system prompt from file
- `--custom-summarization-prompt @path/to/summary_prompt.txt` - Load summarization prompt from file

#### Examples

```bash
# Create prompt files
mkdir -p prompts
cat > prompts/coding_assistant.txt << 'EOF'
You are an expert coding assistant with deep knowledge of software engineering best practices.

**Your Role:**
- Help users write clean, efficient, and maintainable code
- Explain complex programming concepts clearly
- Provide debugging assistance and optimization suggestions
- Follow industry standards and best practices

**Guidelines:**
- Always explain your reasoning when making code suggestions
- Include comments in code examples for clarity
- Suggest testing approaches when appropriate
- Consider security implications in your recommendations

Ready to help with your coding challenges!
EOF

# Use the prompt file
strands-chatbot \
  --model gpt-4o \
  --system-prompt "@prompts/coding_assistant.txt" \
  --tool-config-paths tools/code_tools.json

# Mix literal and file-loaded parameters
strands-chatbot \
  --model gpt-4o \
  --system-prompt "You are a helpful assistant" \
  --custom-summarization-prompt "@prompts/tech_summary.txt" \
  --conversation-manager-type summarizing
```

#### File-Loadable Benefits

- **Version Control**: Store prompts in version-controlled files
- **Collaboration**: Share and collaborate on prompt development
- **Maintenance**: Easily update complex prompts without touching command lines
- **Reusability**: Use the same prompts across different configurations
- **Security**: Keep sensitive prompts in protected files rather than command history

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

# Google Gemini (automatic generic adapter support)
config = AgentFactoryConfig(model="gemini:gemini-2.5-flash")

# Ollama (requires: pip install "strands-agent-factory[ollama]")
config = AgentFactoryConfig(model="ollama:llama3.1:8b")

# AWS Bedrock (requires: pip install "strands-agent-factory[bedrock]")
config = AgentFactoryConfig(model="bedrock:anthropic.claude-3-sonnet-20240229-v1:0")

# LiteLLM for 100+ providers (requires: pip install "strands-agent-factory[litellm]")
config = AgentFactoryConfig(model="litellm:gemini/gemini-2.5-flash")
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
    
    # Tool configuration files
    tool_config_paths=[
        "tools/math_tools.json",
        "tools/file_tools.json", 
        "tools/a2a_agents.json",
        "custom_tools.yaml"
    ],
    
    # Model parameters
    model_config={
        "temperature": 0.7,
        "max_tokens": 4000
    },
    
    # Session persistence
    session_id="research_session_001",
    sessions_home=Path("./sessions"),
    
    # Output customization
    show_tool_use=True,
    response_prefix="Assistant: "
)

factory = AgentFactory(config)
await factory.initialize()
agent = factory.create_agent()
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architectural documentation including the factory pattern benefits, component design, and internal structure.

## Framework Support

The factory includes a powerful generic adapter that automatically supports any framework following standard strands-agents patterns, plus specialized adapters for frameworks requiring custom handling.

See [docs/FRAMEWORK_ADAPTERS.md](docs/FRAMEWORK_ADAPTERS.md) for comprehensive framework adapter documentation.

### Automatic Generic Adapter

```python
# These work automatically without custom adapters:
config = AgentFactoryConfig(model="gemini:gemini-2.5-flash")      # Google Gemini
config = AgentFactoryConfig(model="mistral:mistral-large")        # Mistral
config = AgentFactoryConfig(model="cohere:command-r-plus")        # Cohere
config = AgentFactoryConfig(model="openai:gpt-4o")               # OpenAI
config = AgentFactoryConfig(model="anthropic:claude-3-5-sonnet") # Anthropic
```

### Specialized Adapters

| Framework | Adapter | Special Features |
|-----------|---------|------------------|
| **LiteLLM** | `LiteLLMAdapter` | Tool schema cleaning, 100+ provider support |
| **AWS Bedrock** | `BedrockAdapter` | BotocoreConfig handling, content adaptation |
| **Ollama** | `OllamaAdapter` | Host configuration, local model support |

## Configuration

### AgentFactoryConfig Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `model` | `str` | Model identifier with optional framework prefix | Required |
| `system_prompt` | `Optional[str]` | System prompt for the agent (**supports @file.txt**) | `None` |
| `initial_message` | `Optional[str]` | Initial user message (sent with files) | `None` |
| `model_config` | `Optional[Dict[str, Any]]` | Framework-specific model parameters | `None` |
| `tool_config_paths` | `List[PathLike]` | Paths to individual tool configuration files | `[]` |
| `file_paths` | `List[Tuple[PathLike, Optional[str]]]` | Files as (path, mimetype) tuples | `[]` |
| `sessions_home` | `Optional[PathLike]` | Directory for session storage | `None` |
| `session_id` | `Optional[str]` | Session identifier for persistence | `None` |
| `conversation_manager_type` | `ConversationManagerType` | Strategy: "null", "sliding_window", "summarizing" | `"sliding_window"` |
| `sliding_window_size` | `int` | Number of messages to keep in sliding window | `40` |
| `preserve_recent_messages` | `int` | Messages to preserve in summarizing mode | `10` |
| `summary_ratio` | `float` | Ratio of messages to summarize (0.1-0.8) | `0.3` |
| `summarization_model` | `Optional[str]` | Optional separate model for summarization | `None` |
| `summarization_model_config` | `Optional[Dict[str, Any]]` | Framework-specific config for summarization model | `None` |
| `custom_summarization_prompt` | `Optional[str]` | Custom prompt for summarization (**supports @file.txt**) | `None` |
| `should_truncate_results` | `bool` | Whether to truncate tool results on overflow | `True` |
| `emulate_system_prompt` | `bool` | Emulate system prompt for unsupported models | `False` |
| `show_tool_use` | `bool` | Show verbose tool execution feedback | `False` |
| `response_prefix` | `Optional[str]` | Prefix to display before agent responses | `None` |

**Note**: The `callback_handler` and `output_printer` parameters are available for programmatic use but are not exposed in CLI tools as they require Python callable objects.

### File-Loadable Parameters

Parameters marked with **supports @file.txt** can load their content from files using the `@filename` syntax:

```bash
# Instead of inline prompts:
--system-prompt "You are a helpful assistant..."

# Load from file:
--system-prompt "@prompts/assistant.txt"
```

This feature enables:
- **Version control** of complex prompts
- **Collaborative prompt development**
- **Easy maintenance** of long prompts
- **Reusable prompt libraries**

### Model String Formats

The factory intelligently handles various model identifier formats:

```python
# Direct provider names (uses generic adapter)
"gpt-4o"                    # → OpenAI GPT-4
"claude-3-5-sonnet"         # → Anthropic Claude
"gemini-2.5-flash"          # → Google Gemini

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

## Advanced Tool System

### Tool Configuration

Tools are loaded from individual JSON/YAML configuration files:

#### Python Tools
```json
{
  "id": "calculator_tools",
  "type": "python",
  "module_path": "my_tools.calculator", 
  "functions": ["add", "multiply", "divide"],
  "package_path": "src/",
  "base_path": "/project/root"
}
```

#### MCP (Model Context Protocol) Tools
```json
{
  "id": "mcp_server_tools",
  "type": "mcp",
  "command": ["python", "-m", "my_mcp_server"],
  "args": ["--port", "8080"],
  "env": {"API_KEY": "${SECRET_KEY}"},
  "functions": ["search", "analyze"]
}
```

#### A2A (Agent-to-Agent) Tools
```json
{
  "id": "company_agents",
  "type": "a2a",
  "urls": [
    "http://employee-service:8001/",
    "http://payroll-service:8002/",
    "http://benefits-service:8003/"
  ],
  "timeout": 300,
  "webhook_url": "https://my-app.example.com/webhook",
  "webhook_token": "secret-webhook-token"
}
```

### Tool Types

| Tool Type | Description | Use Cases |
|-----------|-------------|-----------|
| **Python Functions** | Load functions from any Python module/package | Calculations, data processing, file operations |
| **MCP Servers** | Model Context Protocol servers via stdio or HTTP | External APIs, databases, specialized services |
| **A2A Agents** | Communication with other AI agents | Multi-agent workflows, specialist agent consultation |

### A2A (Agent-to-Agent) Communication

A2A tools enable your agent to communicate with other AI agents as peers, creating powerful multi-agent workflows:

#### Key Features
- **Natural Language Communication**: Agents send natural language messages to each other
- **Agent Discovery**: Dynamically discover available agents and their capabilities
- **Multi-Agent Workflows**: Orchestrate complex tasks across specialized agents

#### Available A2A Tools
When you configure A2A agents, your agent automatically gets these tools:

| Tool | Description |
|------|-------------|
| `a2a_discover_agent` | Discover a new agent by URL and get its capabilities |
| `a2a_list_discovered_agents` | List all known agents and their details |
| `a2a_send_message` | Send a natural language message to another agent |

#### A2A vs MCP Comparison

| Aspect | MCP Tools | A2A Tools |
|--------|-----------|-----------|
| **Communication** | Direct function calls | Natural language messages |
| **Interface** | Tool schemas (JSON) | Conversational |
| **Use Case** | External APIs, databases | Agent collaboration |
| **Complexity** | Tool-specific parameters | Human-like requests |

**Important Note**: A2A tools are not filterable - all three tools (`discover`, `list`, `send_message`) work together as a cohesive communication system.

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
    summarization_model="gpt-4o-mini",  # Use cheaper model for summaries
    summarization_model_config={"temperature": 0.3, "max_tokens": 1000}  # Config for summarization model
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
├── session_user_123_project_alpha/
│   ├── conversation.json      # Message history
│   ├── metadata.json         # Session metadata
│   └── uploads/              # Uploaded files
└── session_other_session_id/
    └── ...
```

## CLI Examples & Use Cases

### Interactive Chatbot with Tools

```bash
# Start chatbot with filesystem and code analysis tools
strands-chatbot \
  --model gpt-4o \
  --system-prompt "@prompts/coding_assistant.txt" \
  --tool-config-paths tools/filesystem.json tools/code_analysis.json \
  --show-tool-use \
  --response-prefix "Code Assistant: "

# Example interaction:
# You: What Python files are in the current directory?
# Code Assistant: I'll check the current directory for Python files...
# [Tool Use: list_directory with pattern *.py]
# Code Assistant: I found 3 Python files: main.py, utils.py, and test_main.py
```

### Multi-Agent HR System

```bash
# Start HR agent that can coordinate with other specialist agents
strands-a2a-server \
  --model anthropic:claude-3-5-sonnet-20241022 \
  --system-prompt "@prompts/hr_coordinator.txt" \
  --tool-config-paths tools/company_agents.json tools/hr_tools.json \
  --conversation-manager-type summarizing \
  --custom-summarization-prompt "@prompts/hr_summary.txt" \
  --session-id hr_main_agent \
  --port 8000

# Example A2A workflow:
# User -> HR Agent: "I need a report on all AI engineers hired in 2024 with salary bands"
# HR Agent -> Employee Agent: "List all employees with 'AI Engineer' titles hired in 2024"
# HR Agent -> Payroll Agent: "Get salary band information for employee IDs [list]"
# HR Agent -> User: "Here's your comprehensive report..."
```

### Research Assistant with Document Analysis

```bash
# Start research assistant with document uploads
strands-chatbot \
  --model litellm:gemini/gemini-2.5-flash \
  --system-prompt "@prompts/research_assistant.txt" \
  --tool-config-paths tools/research_tools.json \
  --file-paths "papers/paper1.pdf,application/pdf" "papers/paper2.pdf,application/pdf" \
  --file-paths "data/results.csv,text/csv" \
  --initial-message "Please analyze these research papers and data files" \
  --conversation-manager-type summarizing \
  --custom-summarization-prompt "@prompts/research_summary.txt" \
  --session-id research_2024 \
  --show-tool-use
```

### Code Assistant with Project Context

```bash
# Load project files and start coding session
strands-chatbot \
  --model gpt-4o \
  --system-prompt "@prompts/code_assistant.txt" \
  --tool-config-paths tools/code_analysis.json tools/git_tools.yaml \
  --file-paths "src/main.py,text/plain" "requirements.txt,text/plain" \
  --file-paths "README.md,text/markdown" \
  --conversation-manager-type sliding_window \
  --sliding-window-size 50 \
  --session-id coding_session
```

## Programmatic Examples

### Multi-Agent HR System

```python
config = AgentFactoryConfig(
    model="gpt-4o",
    system_prompt="You are an HR assistant that coordinates with specialist agents.",
    tool_config_paths=[
        "tools/company_agents.json",  # A2A agent connections
        "tools/hr_tools.json"         # Direct HR functions
    ],
    conversation_manager_type="summarizing",
    session_id="hr_session"
)

# Example interaction:
# User: "I need a report on all AI engineers hired in 2024 with their salary bands"
# HR Agent -> Employee Agent: "List all employees with 'AI Engineer' or similar titles hired in 2024"
# HR Agent -> Payroll Agent: "Get salary band information for employee IDs [list]"
# HR Agent -> User: "Here's your comprehensive report..."
```

### Research Assistant

```python
config = AgentFactoryConfig(
    model="anthropic:claude-3-5-sonnet-20241022",
    system_prompt="You are a research assistant with access to document analysis tools.",
    tool_config_paths=["tools/research_tools.json"],
    file_paths=[
        ("papers/paper1.pdf", "application/pdf"),
        ("papers/paper2.pdf", "application/pdf"),
        ("data/results.csv", "text/csv")
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
    tool_config_paths=[
        "tools/code_analysis.json",
        "tools/git_tools.yaml"
    ],
    file_paths=[
        ("src/main.py", "text/plain"),
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
    model="gemini:gemini-2.0-flash-exp",  # Supports vision
    system_prompt="Analyze documents and images for insights.",
    file_paths=[
        ("charts/chart1.png", "image/png"),
        ("charts/chart2.png", "image/png"),
        ("reports/summary.pdf", "application/pdf"),
        ("data/metrics.json", "application/json")
    ],
    tool_config_paths=["tools/analysis_tools.yaml"]
)
```

## Error Handling & Debugging

### Comprehensive Error Handling

```python
from strands_agent_factory.core.exceptions import (
    InitializationError, ConfigurationError, ModelLoadError
)

try:
    factory = AgentFactory(config)
    await factory.initialize()
    agent = factory.create_agent()
    
    with agent as a:
        success = await a.send_message_to_agent("Hello")
        if not success:
            print("Message processing failed")
            
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except InitializationError as e:
    print(f"Initialization failed: {e}")
except ModelLoadError as e:
    print(f"Model loading failed: {e}")
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
- Use A2A agents for complex multi-agent workflows
- Store complex prompts in files using the `@filename` syntax for better maintainability

## A2A Server Wrapper

For multi-agent deployments, strands-agent-factory includes a generic A2A server wrapper that exposes any agent created by the factory as an Agent-to-Agent server that other agents can communicate with.

```bash
# Run any agent configuration as an A2A server
strands-a2a-server --agent-config agent_config.yaml --host 0.0.0.0 --port 8001

# Other agents can now connect and communicate with this agent
```

See [A2A_SERVER.md](A2A_SERVER.md) for detailed multi-agent system setup documentation and [docs/A2A_ARCHITECTURE.md](docs/A2A_ARCHITECTURE.md) for comprehensive architectural details.

## Testing & Development

### Running Examples

```bash
# Test the interactive chatbot
strands-chatbot --model gpt-4o-mini --system-prompt "You are a test assistant"

# Test with file-loaded prompt
strands-chatbot --model gpt-4o-mini --system-prompt "@prompts/test_assistant.txt"

# Test the A2A server
strands-a2a-server --model gpt-4o-mini --port 8001

# Set up API credentials for testing
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"  
export GOOGLE_API_KEY="your-key"
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

## Contributing

We welcome contributions! Please see our contribution guidelines:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Make** your changes with comprehensive tests
4. **Test** using the provided test suite
5. **Submit** a pull request with detailed description

### Development Setup

```bash
git clone https://github.com/your-username/strands-agent-factory.git
cd strands-agent-factory
pip install -e ".[dev,all-providers,all-tools]"
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support & Community

- **Issues**: [GitHub Issues](https://github.com/bassmanitram/strands-agent-factory/issues)
- **Documentation**: See examples and comprehensive docstrings
- **Testing**: Use provided test suite for validation
- **Discussions**: GitHub Discussions for questions and ideas

## Roadmap

- Enhanced MCP server discovery and management
- Advanced A2A agent orchestration and workflow management
- Plugin system for custom conversation managers
- Streaming response support for all frameworks
- Advanced file processing with OCR and vision models
- Distributed agent orchestration
- Web UI for configuration and testing