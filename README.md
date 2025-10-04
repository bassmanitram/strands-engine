# Strands Engine

A conversational AI engine built on strands-agents for orchestrating LLM interactions with tools, session management, and multi-framework support.

## Overview

Strands Engine is a focused library for building conversational AI applications. It provides:

- **Multi-LLM Support**: OpenAI, Anthropic, AWS Bedrock, LiteLLM integration
- **Tool Integration**: MCP servers, Python modules, custom tools
- **Session Management**: Conversation persistence and state handling
- **Content Processing**: File uploads, multimodal content support
- **Framework Adapters**: Clean abstractions for different LLM providers

## Key Features

- **Engine-First Design**: Focused on conversation orchestration, not UI
- **Framework Agnostic**: Works with multiple LLM providers through adapters
- **Tool Ecosystem**: Extensible tool system with MCP protocol support
- **Session Persistence**: Conversation state management and history
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

```python
import asyncio
from strands_engine import Engine, EngineConfig

async def main():
    # Configure the engine
    config = EngineConfig(
        model="gpt-4o",
        system_prompt="You are a helpful assistant",
        tool_config_paths=["/path/to/tools.json"],
        file_paths=[("/path/to/doc.pdf", "application/pdf")]
    )
    
    # Create and initialize engine
    engine = Engine(config)
    await engine.initialize()
    
    try:
        # Process messages
        response = await engine.process_message("Hello! How can you help me?")
        print(response)
        
        # Continue conversation
        response = await engine.process_message("What files do you have access to?")
        print(response)
        
    finally:
        await engine.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## Architecture

Strands Engine is built around clean separation of concerns:

- **Engine Core**: Message processing and conversation orchestration
- **Framework Adapters**: LLM provider integrations (OpenAI, Anthropic, etc.)
- **Tool System**: Extensible tool loading and execution
- **Session Management**: Conversation state and persistence
- **Content Processing**: File handling and multimodal support

## Configuration

The engine accepts a simple configuration object with all necessary parameters:

```python
config = EngineConfig(
    # Model configuration
    model="claude-3-sonnet-20240229",
    system_prompt="Custom system prompt",
    
    # Tool configuration
    tool_config_paths=[
        "/path/to/mcp_tools.json",
        "/path/to/python_tools.yaml"
    ],
    
    # File uploads
    file_paths=[
        ("/path/to/document.pdf", "application/pdf"),
        ("/path/to/image.jpg", "image/jpeg")
    ],
    
    # Session configuration
    session_file="/path/to/session.json",
    
    # Conversation management
    conversation_strategy="sliding_window",
    max_context_length=4000
)
```

## Framework Support

- **OpenAI**: GPT-4, GPT-3.5, and compatible models
- **Anthropic**: Claude 3 family models
- **AWS Bedrock**: Claude, Titan, and other Bedrock models
- **LiteLLM**: 100+ models through unified interface
- **Custom**: Extensible adapter system for new providers

## Tool Integration

- **MCP Protocol**: Model Context Protocol servers
- **Python Modules**: Direct Python function integration
- **Custom Tools**: Extensible tool adapter system

## License

MIT License - see LICENSE file for details.

## Contributing

This project is part of the strands ecosystem. Contributions welcome!

## Related Projects

- **YACBA**: CLI wrapper that uses strands-engine
- **repl-toolkit**: Interactive interface components
- **strands-agents**: Underlying agent framework