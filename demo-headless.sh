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

echo "🚀 Agentic Chatbot Demo (Headless)"
echo "=================================="
echo "Model: $MODEL"
echo "Running chatbot with demo inputs..."
echo

#
# Kinda necessary for headless - so be careful what tools you enable!
#
export BYPASS_TOOL_CONSENT=true

#
# Gets noisy is not
#
export LOGURU_LEVEL=ERROR

# Run chatbot and filter out terminal escape sequences and aiohttp warnings
python3 "$SCRIPT_DIR/chatbot.py" "$MODEL" 2>/dev/null << 'EOF' | sed $'s/\033\[[0-9;]*[a-zA-Z]//g' | sed 's/[;][0-9]*R//g'
What's my current working directory?
List the files in this directory and tell me what you see.
Check if there's a file called 'README.md' in the current directory.
What Python files are in this directory?
EOF

echo
echo "✅ Demo completed!"