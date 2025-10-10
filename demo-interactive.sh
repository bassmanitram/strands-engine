#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for and activate virtual environment if it exists
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    echo "🔧 Activating virtual environment..."
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

# Get model argument or use default
MODEL="${1:-litellm:gemini/gemini-2.5-flash}"

echo "🚀 Agentic Chatbot (Interactive)"
echo "==============================="
echo "Model: $MODEL"
echo "Starting interactive chatbot session..."
echo "Type '/help' for commands, '/quit' to exit, or Ctrl+D for EOF exit"
echo

# Hide aiohttp unclosed session warnings from litellm
exec python3 "$SCRIPT_DIR/chatbot.py" "$MODEL" 2>/dev/null