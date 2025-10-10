# Agentic Chatbot

A demonstration chatbot built with `strands_agent_factory` that showcases agentic capabilities through tool usage.

## Features

🤖 **Agentic Capabilities:**
- **File Operations**: Read, write, and analyze files using built-in tools
- **Shell Commands**: Execute system commands and get real-time output  
- **Python Integration**: Access Python modules and functions
- **Context Awareness**: Maintains conversation history for coherent interactions

🛠️ **Available Tools:**
- `file_read` - Read and analyze files (supports various formats)
- `file_write` - Create and modify files
- `shell` - Execute shell commands with real-time output
- Python modules: `pathlib`, `os` for filesystem operations

## Usage

### Basic Usage
```bash
# Use default model (gpt-4o-mini)
python chatbot.py

# Specify a different model
python chatbot.py gpt-4o
python chatbot.py claude-3-sonnet-20240229
```

### Environment Setup
Make sure you have the appropriate API key set:
```bash
# For OpenAI models
export OPENAI_API_KEY="your-api-key"

# For Anthropic models  
export ANTHROPIC_API_KEY="your-api-key"
```

### Example Interactions

**File Operations:**
```
👤 You: What files are in this directory?
🤖 Assistant: [Uses tools to list and describe files]

👤 You: Read the README.md file and summarize it
🤖 Assistant: [Reads file and provides summary]

👤 You: Create a Python script that calculates fibonacci numbers
🤖 Assistant: [Creates the file using file_write tool]
```

**System Commands:**
```
👤 You: What's my current working directory?
🤖 Assistant: [Uses shell tool to run 'pwd']

👤 You: Show me disk usage
🤖 Assistant: [Runs 'df -h' command]
```

**Code Analysis:**
```
👤 You: Analyze the main factory.py file
🤖 Assistant: [Reads and analyzes the code structure]
```

## Commands

- `help` - Show available commands
- `clear` - Clear conversation history
- `files [path]` - Quick file listing (shortcut)
- `quit/exit/bye` - Exit the chatbot

## How it Works

The chatbot demonstrates the key capabilities of `strands_agent_factory`:

1. **Tool Configuration**: Sets up multiple tool types (Python modules, built-in tools)
2. **Context Management**: Uses the context manager pattern for proper resource handling
3. **Streaming Responses**: Shows real-time response generation
4. **Agent Interaction**: Demonstrates how to build conversational agents with tool access

The agent automatically decides when and how to use tools based on the conversation context, making it truly "agentic" rather than just a simple Q&A bot.