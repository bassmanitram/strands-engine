#!/usr/bin/env python3
"""
Interactive Chatbot Script for strands-agent-factory

Provides an interactive chatbot interface using agents created by AgentFactory.
Supports tool usage, conversation management, file processing, and all agent capabilities.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List, Optional, Set

# Add the package root to sys.path so we can import strands_agent_factory
script_dir = Path(__file__).parent
package_root = script_dir.parent.parent
sys.path.insert(0, str(package_root))

from dataclass_args import GenericConfigBuilder
from loguru import logger

from strands_agent_factory import AgentFactory
from strands_agent_factory.core.config import AgentFactoryConfig
from strands_agent_factory.core.exceptions import (
    ConfigurationError,
    InitializationError,
    ModelLoadError,
)


def _generate_adaptive_system_prompt(tool_names: List[str]) -> str:
    """
    Generate an adaptive system prompt based on available tools.

    Args:
        tool_names: List of available tool names

    Returns:
        str: Generated system prompt tailored to available capabilities
    """
    if not tool_names:
        return """You are a helpful AI assistant. I can engage in conversation, answer questions, help with analysis, and provide information on a wide variety of topics.

While I don't have access to external tools in this session, I can still help with:
- General questions and explanations
- Analysis and reasoning
- Writing and editing assistance
- Problem-solving guidance

Feel free to ask me anything!"""

    # Categorize tools to understand capabilities
    tool_set = set(tool_names)
    capabilities = []
    guidelines = []
    examples = []

    # Filesystem tools
    if any(
        tool in tool_set
        for tool in ["file_read", "file_write", "list_files", "get_file_info"]
    ):
        capabilities.append(
            "- File system operations (read, analyze, and explore files and directories)"
        )
        guidelines.append("- Use file tools when users ask about files or directories")
        examples.extend(
            [
                '"What files are in this directory?"',
                '"Show me the contents of README.md"',
                '"Check if a specific file exists"',
            ]
        )

    # Code execution tools
    if any(
        tool in tool_set for tool in ["python_exec", "python_execute", "code_execute"]
    ):
        capabilities.append("- Python code execution and analysis")
        guidelines.append(
            "- Use Python execution for calculations, data analysis, and code testing"
        )
        examples.extend(
            [
                '"Calculate the fibonacci sequence"',
                '"Analyze this data with Python"',
                '"Test this code snippet"',
            ]
        )

    # Shell/system tools
    if any(tool in tool_set for tool in ["shell", "shell_execute", "run_command"]):
        capabilities.append("- Shell command execution")
        guidelines.append("- Use shell commands for system operations when appropriate")
        examples.extend(
            [
                '"Run ls -la to see directory contents"',
                '"Check system information"',
                '"Execute git status"',
            ]
        )

    # Web/search tools
    if any(tool in tool_set for tool in ["web_search", "search", "browse_web"]):
        capabilities.append("- Web search and information retrieval")
        guidelines.append("- Use web search to find current information")
        examples.extend(
            [
                '"Search for recent news about AI"',
                '"Find information about a specific topic"',
            ]
        )

    # MCP/A2A tools (external agents/servers)
    mcp_a2a_tools = [
        tool
        for tool in tool_names
        if any(prefix in tool.lower() for prefix in ["mcp_", "a2a_", "agent_"])
    ]
    if mcp_a2a_tools:
        capabilities.append("- Integration with external agents and services")
        guidelines.append(
            "- Use external tools and agents when their specialized capabilities are needed"
        )

    # Generic tools (catch remaining tools)
    other_tools = (
        tool_set
        - {
            "file_read",
            "file_write",
            "list_files",
            "get_file_info",
            "python_exec",
            "python_execute",
            "code_execute",
            "shell",
            "shell_execute",
            "run_command",
            "web_search",
            "search",
            "browse_web",
        }
        - set(mcp_a2a_tools)
    )

    if other_tools:
        capabilities.append(f"- Specialized tools: {', '.join(sorted(other_tools))}")
        guidelines.append(
            "- Use specialized tools when their specific capabilities match user needs"
        )

    # Build the system prompt
    prompt_parts = [
        "You are an intelligent assistant with access to various tools and capabilities.",
        "",
        "Available capabilities:",
    ]
    prompt_parts.extend(capabilities)

    prompt_parts.extend(["", "Guidelines:"])
    prompt_parts.extend(guidelines)
    prompt_parts.extend(
        [
            "- Always explain what you're doing when using tools",
            "- Be helpful and accurate in your responses",
            "- Ask for clarification if requests are unclear",
        ]
    )

    if examples:
        prompt_parts.extend(["", "Example requests:"])
        prompt_parts.extend(examples)

    return "\n".join(prompt_parts)


def _generate_tool_aware_help(tool_names: List[str]) -> str:
    """
    Generate help text based on available tools.

    Args:
        tool_names: List of available tool names

    Returns:
        str: Tool-aware help text
    """
    help_text = """
Agentic Chatbot Commands:

**Chat Commands:**
  /help              - Show this help message
  /clear             - Clear conversation history  
  /quit, /exit, /bye - Exit the chatbot
"""

    if not tool_names:
        help_text += """
**Current Capabilities:**
  - General conversation and assistance
  - No specialized tools available
  
To add tools, restart with tool configuration:
  strands-chatbot --model your-model --tool-config-paths path/to/tools.json
"""
    else:
        tool_set = set(tool_names)
        capabilities = []
        examples = []

        # Categorize and describe capabilities
        if any(
            tool in tool_set
            for tool in ["file_read", "file_write", "list_files", "get_file_info"]
        ):
            capabilities.append("  - File system exploration and analysis")
            examples.extend(
                [
                    '  "What files are in this directory?"',
                    '  "Show me the contents of README.md"',
                    '  "List all Python files in the project"',
                ]
            )

        if any(
            tool in tool_set
            for tool in ["python_exec", "python_execute", "code_execute"]
        ):
            capabilities.append("  - Python code execution and analysis")
            examples.extend(
                [
                    '  "Calculate the sum of numbers 1 to 100"',
                    '  "Generate a plot of this data"',
                    '  "Test this Python code"',
                ]
            )

        if any(tool in tool_set for tool in ["shell", "shell_execute", "run_command"]):
            capabilities.append("  - Shell command execution")
            examples.extend(
                [
                    '  "Run git status"',
                    '  "Check disk usage with df -h"',
                    '  "List running processes"',
                ]
            )

        if any(tool in tool_set for tool in ["web_search", "search", "browse_web"]):
            capabilities.append("  - Web search and information retrieval")
            examples.extend(
                [
                    '  "Search for recent AI developments"',
                    '  "Find documentation for a library"',
                ]
            )

        # Add other tools
        other_tools = tool_set - {
            "file_read",
            "file_write",
            "list_files",
            "get_file_info",
            "python_exec",
            "python_execute",
            "code_execute",
            "shell",
            "shell_execute",
            "run_command",
            "web_search",
            "search",
            "browse_web",
        }
        if other_tools:
            capabilities.append(
                f"  - Specialized tools: {', '.join(sorted(other_tools))}"
            )

        help_text += f"""
**Current Capabilities:**
  - General conversation and assistance
{chr(10).join(capabilities)}

**Example Requests:**
{chr(10).join(examples)}

Just chat naturally - I'll use tools when appropriate!
"""

    return help_text


class AgenticChatbot:
    """Interactive chatbot with agentic capabilities."""

    def __init__(self, config: AgentFactoryConfig):
        """Initialize the chatbot with agentic capabilities."""
        self.config = config
        self.factory = None
        self.agent = None
        self._tool_aware_help = None

    async def start(self):
        """Initialize the agent factory and start the chatbot."""
        print("Starting Agentic Chatbot...")
        print("   Initializing tools and agent...")

        try:
            self.factory = AgentFactory(self.config)
            await self.factory.initialize()

            with self.factory.create_agent() as agent:
                self.agent = agent

                # Generate tool-aware help after agent is created
                self._tool_aware_help = _generate_tool_aware_help(self.agent.tool_names)

                print(f"   Model: {self.config.model}")
                print(f"   Tools available: {len(self.agent.tool_names)} tools")
                if self.agent.tool_names:
                    print(
                        f"   Tool types: {', '.join(sorted(set(self.agent.tool_names)))}"
                    )
                else:
                    print("   Mode: General conversational assistant")
                print("   Ready! Type '/help' for commands or start chatting.\n")

                await self._chat_loop()

        except ConfigurationError as e:
            print(f"Configuration error: {e}")
        except InitializationError as e:
            print(f"Initialization failed: {e}")
            print("   Check your API credentials and tool configurations")
        except ModelLoadError as e:
            print(f"Model loading failed: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    async def _chat_loop(self):
        """Main conversation loop."""
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ["/quit", "/exit", "/bye"]:
                    print("Goodbye!")
                    break
                elif user_input.lower() == "/help":
                    self._show_help()
                    continue
                elif user_input.lower() == "/clear":
                    self.agent.clear_messages()
                    print("Conversation history cleared.\n")
                    continue

                # Process the message with the agent
                # Don't show user input since they already typed it
                await self.agent.send_message_to_agent(
                    user_input, show_user_input=False
                )

            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                print("Type '/help' for available commands.\n")

    def _show_help(self):
        """Show available commands."""
        print(self._tool_aware_help or "Help not available")


async def run_chatbot(
    config_builder: GenericConfigBuilder, args: argparse.Namespace
) -> None:
    """
    Run interactive chatbot.

    Args:
        config_builder: GenericConfigBuilder instance
        args: Parsed command-line arguments

    Raises:
        InitializationError: If agent initialization fails
        ConfigurationError: If configuration is invalid
    """
    print("Building agent configuration...")
    try:
        config = config_builder.build_config(args, "agent_config")
    except Exception as e:
        raise ConfigurationError(f"Failed to build configuration: {e}") from e

    # Initialize factory to determine available tools for adaptive system prompt
    temp_factory = AgentFactory(config)
    await temp_factory.initialize()

    # Get tool names from the factory
    available_tools = []
    try:
        # The factory should have tool information available after initialization
        if hasattr(temp_factory, "tool_configs") and temp_factory.tool_configs:
            available_tools = list(temp_factory.tool_configs.keys())
        elif hasattr(temp_factory, "_tool_registry") and temp_factory._tool_registry:
            available_tools = list(temp_factory._tool_registry.keys())
    except Exception:
        # If we can't determine tools, that's OK - we'll default to general prompt
        pass

    # Apply chatbot-specific defaults if not explicitly set
    if not config.system_prompt:
        # Generate adaptive system prompt based on available tools
        config.system_prompt = _generate_adaptive_system_prompt(available_tools)
        logger.debug(
            f"Generated adaptive system prompt for {len(available_tools)} tools"
        )
    else:
        logger.debug("Using user-provided system prompt")

    if not config.response_prefix:
        config.response_prefix = "Assistant: "

    logger.info(f"Loading chatbot configuration with model: {config.model}")

    # Close the temporary factory
    if hasattr(temp_factory, "close"):
        await temp_factory.close()

    # Create and start chatbot with the configured prompt
    chatbot = AgenticChatbot(config)
    await chatbot.start()


def main():
    """Command line entry point."""
    parser = argparse.ArgumentParser(
        description="Interactive agentic chatbot with tool capabilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with model (general assistant mode)
  strands-chatbot --model gpt-4o
  
  # With filesystem tools
  strands-chatbot --model gpt-4o --tool-config-paths tools/filesystem.json
  
  # With custom system prompt (overrides adaptive prompt)
  strands-chatbot --model anthropic:claude-3-5-sonnet-20241022 \\
    --system-prompt "You are a helpful coding assistant" \\
    --tool-config-paths tools/code_tools.json
  
  # With file uploads for analysis
  strands-chatbot --model gpt-4o \\
    --file-paths "document.pdf,application/pdf" \\
    --file-paths "data.csv,text/csv" \\
    --initial-message "Please analyze these files"

System Prompt Behavior:
  - If you provide --system-prompt, it will be used exactly as specified
  - If no system prompt is provided, one will be generated based on available tools:
    * No tools: General conversational assistant
    * File tools: File system exploration assistant  
    * Code tools: Programming and execution assistant
    * Mixed tools: Multi-capability assistant with appropriate guidance

Agent Configuration:
  All AgentFactoryConfig parameters are available as CLI options:
  - Single parameters override base config values
  - List parameters (--tool-config-paths) accept multiple values
  - Object parameters (--model-config) load from files and support property overrides
  
  Property Override Format:
    --mc temperature:0.7           # Set model_config.temperature = 0.7
    --mc client.timeout:30         # Set model_config.client.timeout = 30

Chatbot Features:
  - Adaptive system prompts based on available tools
  - Interactive conversation with natural language
  - Tool usage (Python functions, MCP servers, A2A agents)
  - File processing and analysis
  - Session persistence and conversation management
  - All strands-agent-factory capabilities

  The chatbot automatically adapts its behavior and help text based on
  the tools you provide, ensuring accurate capability communication.
        """,
    )

    # Chatbot-specific parameters (not part of AgentFactoryConfig)
    chatbot_group = parser.add_argument_group("Chatbot Options")
    chatbot_group.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    # Add all AgentFactoryConfig parameters using the generic builder
    config_builder = GenericConfigBuilder(AgentFactoryConfig)
    config_builder.add_arguments(
        parser,
        base_config_name="agent-config",
        base_config_help="Base agent configuration file (JSON or YAML)",
    )

    args = parser.parse_args()

    # Configure logging - default to ERROR level, verbose enables DEBUG
    logger.remove()  # Remove default handler
    if args.verbose:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="ERROR")

    try:
        asyncio.run(run_chatbot(config_builder, args))

    except ConfigurationError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
    except InitializationError as e:
        print(f"Initialization Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ModelLoadError as e:
        print(f"Model Load Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nGoodbye!", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        logger.exception("Unexpected error in chatbot")
        sys.exit(1)


if __name__ == "__main__":
    main()
