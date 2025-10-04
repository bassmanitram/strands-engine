# Strands Engine

A conversational AI engine built on strands-agents for orchestrating LLM interactions with tool loading, conversation management, session management, and multi-framework support.

## Overview

Strands Engine is a focused library for building conversational AI applications. It provides:

- **Multi-LLM Support**: OpenAI, Anthropic, AWS Bedrock, LiteLLM integration
- **Tool Loading & Configuration**: MCP servers, Python modules, custom tools
- **Conversation Management**: Sliding window, summarization, or full history strategies
- **Optional Session Management**: DelegatingSession proxy for flexible session handling
- **Content Processing**: File uploads, multimodal content support
- **Framework Adapters**: Clean abstractions for different LLM providers

## Key Architecture

**Tool Execution Model**: 
- **Engine Responsibility**: Load and configure tools from config files
- **strands-agents Responsibility**: Execute tools during conversation
- **Clean Separation**: Engine never executes tools directly

**Conversation Management Model**:
- **Sliding Window**: Keep last N messages (default)
- **Summarizing**: Summarize old messages, preserve recent ones
- **Null**: Keep full conversation history (no management)

**Session Management Model**:
- **DelegatingSession Proxy**: Can be inactive (ignores session ops) or active (manages sessions)
- **Flexible**: No session_id = inactive, with session_id = active when agent available
- **Automatic**: Session persistence handled by strands-agents when active

## Key Features

- **Engine-First Design**: Focused on conversation orchestration, not UI
- **Framework Agnostic**: Works with multiple LLM providers through adapters
- **Flexible Conversation Management**: Multiple strategies for handling conversation context
- **Tool Ecosystem**: Loads tools for strands-agents execution (MCP protocol, Python modules)
- **Optional Sessions**: DelegatingSession can be inactive or active based on configuration
- **Content Processing**: Handle text, images, files, and structured data  
- **Type Safety**: Full type hints for better development experience

## Installation

```bash
pip install strands-engine
```

For development with all LLM provider support:
```bash
pip install strands-engine[dev]
```

## Quick Start

### Basic Usage with Conversation Management
```python
import asyncio
from strands_engine import Engine, EngineConfig

async def main():
    # Configure engine with sliding window conversation management
    config = EngineConfig(
        model="gpt-4o",
        system_prompt="You are a helpful assistant",
        conversation_manager_type="sliding_window",  # Keep last 40 messages
        sliding_window_size=40,
        tool_config_paths=["/path/to/tools.json"]
    )
    
    # Create and initialize engine
    engine = Engine(config)
    await engine.initialize()
    
    try:
        # Process messages - conversation context managed automatically
        response = await engine.process_message("Hello! How can you help me?")
        print(response)
        
        # Continue conversation - older messages automatically managed
        for i in range(50):  # This would exceed sliding window
            response = await engine.process_message(f"Message {i}")
            print(f"Response {i}: {response}")
        
    finally:
        await engine.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

### Advanced: Summarizing Conversation Management
```python
import asyncio
from strands_engine import Engine, EngineConfig

async def main():
    # Configure engine with summarizing conversation management
    config = EngineConfig(
        model="gpt-4o",
        system_prompt="You are a helpful assistant",
        conversation_manager_type="summarizing",
        summary_ratio=0.3,                    # Summarize 30% of old messages
        preserve_recent_messages=10,          # Always keep last 10 messages
        summarization_model="gpt-3.5-turbo", # Optional separate model for summaries
        custom_summarization_prompt="Summarize the key points from this conversation",
        sessions_home="/path/to/sessions",
        session_id="long_conversation"
    )
    
    engine = Engine(config)
    await engine.initialize()
    
    try:
        # Long conversation - old messages automatically summarized
        for i in range(100):
            response = await engine.process_message(f"Tell me about topic {i}")
            print(f"Response {i}: {response}")
        
        # Check conversation manager info
        print(f"Conversation management: {engine.conversation_manager_info}")
        
    finally:
        await engine.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

### Complete Configuration Example
```python
config = EngineConfig(
    # Model configuration
    model="claude-3-sonnet-20240229",  # or "openai:gpt-4o", "bedrock/claude-v3", etc.
    system_prompt="Custom system prompt",
    
    # Tool configuration (engine loads, agent executes)
    tool_config_paths=[
        "/path/to/mcp_tools.json",
        "/path/to/python_tools.yaml"
    ],
    
    # File uploads (engine processes, agent accesses)
    file_paths=[
        ("/path/to/document.pdf", "application/pdf"),
        ("/path/to/image.jpg", "image/jpeg")
    ],
    
    # Conversation management
    conversation_manager_type="sliding_window",  # "sliding_window", "summarizing", or "null"
    sliding_window_size=40,                      # For sliding_window mode
    preserve_recent_messages=10,                 # For summarizing mode
    summary_ratio=0.3,                          # For summarizing mode (0.1-0.8)
    summarization_model="gpt-3.5-turbo",       # Optional separate model for summaries
    custom_summarization_prompt="...",          # Optional custom summary prompt
    should_truncate_results=True,               # Truncate tool results on overflow
    
    # Optional session configuration
    sessions_home="/path/to/sessions",          # Directory for session storage
    session_id="conversation_123",              # Specific session (omit for no sessions)
    
    # Framework-specific options
    emulate_system_prompt=False,                # For frameworks without system prompt support
    framework_specific={"temperature": 0.7}    # Framework-specific parameters
)
```

## Conversation Management Options

### 1. Sliding Window (Default)
```python
config = EngineConfig(
    model="gpt-4o",
    conversation_manager_type="sliding_window",
    sliding_window_size=40,              # Keep last 40 messages
    should_truncate_results=True         # Truncate long tool results
)
# Automatically drops oldest messages when window is full
# Good for: Most conversations, memory efficiency
```

### 2. Summarizing
```python
config = EngineConfig(
    model="gpt-4o",
    conversation_manager_type="summarizing",
    summary_ratio=0.3,                   # Summarize 30% of old messages
    preserve_recent_messages=10,         # Always keep last 10 messages
    summarization_model="gpt-3.5-turbo", # Optional separate model
    custom_summarization_prompt="Provide a concise summary of the key discussion points"
)
# Summarizes old messages while preserving recent context
# Good for: Long conversations, maintaining context while saving tokens
```

### 3. Null (Full History)
```python
config = EngineConfig(
    model="gpt-4o", 
    conversation_manager_type="null"
)
# Keeps full conversation history, no management
# Good for: Short conversations, maximum context retention
```

### 4. Configuration Validation
```python
# Automatic validation ensures:
# - sliding_window_size: 1-1000
# - preserve_recent_messages: 1-100 (for summarizing mode)
# - summary_ratio: 0.1-0.8
# - summarization_model: valid "framework:model" format if provided
```

## Session Management Options

### No Sessions (DelegatingSession Inactive)
```python
config = EngineConfig(model="gpt-4o")
# DelegatingSession remains inactive
# No conversation persistence
# Agent memory cleared between runs
```

### With Sessions (DelegatingSession Active)
```python
config = EngineConfig(
    model="gpt-4o",
    sessions_home="/path/to/sessions",
    session_id="my_chat"
)
# DelegatingSession activates when agent is available
# Conversation automatically persisted
# Agent memory restored from session
```

### Session Control
```python
engine = Engine(config)
session_manager = engine.session_manager

# Check session status
if session_manager.is_active:
    print(f"Active session: {session_manager.session_id}")

# Switch sessions dynamically (if needed)
session_manager.set_active_session("different_session")

# List available sessions
sessions = session_manager.list_sessions()
```

## Tool Integration

**Engine Responsibilities**:
- Read tool configuration files
- Instantiate tool adapters (MCP, Python, etc.)
- Create tool objects for strands-agents
- Pass configured tools to Agent

**strands-agents Responsibilities**:
- Execute tools during conversations
- Handle tool call/response cycles
- Manage tool execution context
- Stream tool results to user

**Supported Tool Types**:
- **MCP Protocol**: Model Context Protocol servers
- **Python Modules**: Direct Python function integration  
- **Custom Tools**: Extensible tool adapter system

## Framework Support

- **OpenAI**: GPT-4, GPT-3.5, and compatible models
- **Anthropic**: Claude 3 family models
- **AWS Bedrock**: Claude, Titan, and other Bedrock models
- **LiteLLM**: 100+ models through unified interface
- **Custom**: Extensible adapter system for new providers

## License

MIT License - see LICENSE file for details.

## Contributing

This project is part of the strands ecosystem. Contributions welcome!

## Related Projects

- **YACBA**: CLI wrapper that uses strands-engine
- **repl-toolkit**: Interactive interface components
- **strands-agents**: Underlying agent framework that executes tools