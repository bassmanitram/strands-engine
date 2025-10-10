#!/usr/bin/env python3
"""
Simple agentic chatbot using strands_agent_factory.

This chatbot demonstrates:
- Tool usage (filesystem operations, Python code execution)
- Context management with conversation history
- File handling and analysis
- Real-time interaction via command line
"""

import asyncio
import glob
import sys

from strands_agent_factory import AgentFactoryConfig, AgentFactory

class AgenticChatbot:

    def __init__(self, model: str = "gpt-4o-mini", tool_config_paths: list[str] = []):
        """Initialize the chatbot with agentic capabilities."""
        

        # Agent configuration with system prompt for agentic behavior
        self.config = AgentFactoryConfig(
            model=model,
            system_prompt="""You are an intelligent assistant with access to tools to investigate the users filesystem:

**Guidelines:**
- When users ask about files or directories, use the available tools to explore and provide accurate information
- Always explain what you're doing when using tools
- Be helpful and proactive in using your capabilities
- If a user asks about files that don't exist, use tools to check and confirm
- NEVER modify the users file system

Engage naturally in conversation while leveraging your tools when appropriate.""",
            tool_config_paths=tool_config_paths
        )
        
        self.factory = None
        self.agent = None

    async def start(self):
        """Initialize the agent factory and start the chatbot."""
        print("🤖 Starting Agentic Chatbot...")
        print("   Initializing tools and agent...")
        
        self.factory = AgentFactory(self.config)
        await self.factory.initialize()
        with self.factory.create_agent() as agent:
            self.agent = agent
            print(f"   Model: {self.config.model}")
            print(f"   Tools available: {len(self.config.tool_config_paths)} tool sets")
            print("   Ready! Type 'help' for commands or start chatting.\n")
            
            await self._chat_loop()

    async def _chat_loop(self):
        """Main conversation loop."""
        while True:
            try:
                # Get user input
                user_input = input("👤 You: ").strip()
                
                if not user_input:
                    continue
                    
                # Handle special commands
                if user_input.lower() in ['/quit', '/exit', '/bye']:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == '/help':
                    self._show_help()
                    continue
                elif user_input.lower() == '/clear':
                    self.agent.clear_messages()
                    print("🧹 Conversation history cleared.\n")
                    continue

                # Process the message with the agent
                print("🤖 Assistant: ", end="", flush=True)
                
                # Invoke agent - the agents own infrasturcture handles the responses
                await self.agent.send_message_to_agent(user_input)

                print("\n")
                                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Type 'help' for available commands.\n")

    def _show_help(self):
        """Show available commands."""
        print("""
🤖 Agentic Chatbot Commands:

**Chat Commands:**
  /help              - Show this help message
  /clear             - Clear conversation history  
  /quit, /exit, /bye - Exit the chatbot

**Example Interactions:**
  "What files are in this directory?"
  "What's my current working directory?"
  "Check if README.md exists"
  "Show me the contents of the examples folder"
  "List all Python files in the current directory"

Just chat naturally - the assistant will use tools when appropriate!
""")

async def main():
    """Main entry point."""
    print("🚀 Agentic Chatbot with Tool Capabilities")
    print("=" * 50)
    
    model = sys.argv[1] if len(sys.argv) > 1 else "litellm:gemini/gemini-2.5-flash"
    
    chatbot = AgenticChatbot(model=model, tool_config_paths=glob.glob("./sample-tool-configs/*.tools.json"))
    await chatbot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Failed to start chatbot: {e}")
        sys.exit(1)