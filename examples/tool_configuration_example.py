#!/usr/bin/env python3
"""
Tool Configuration Example for strands_agent_factory.

This example demonstrates how to configure and use tools with the agent factory,
including Python function tools and MCP server tools.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from strands_agent_factory import AgentFactoryConfig, AgentFactory


def create_example_python_tools():
    """Create example Python tools for demonstration."""
    
    # Create a temporary directory for our tools
    tools_dir = Path(tempfile.mkdtemp(prefix="strands_tools_"))
    
    # Create a simple Python module with tools
    math_tools_file = tools_dir / "math_tools.py"
    math_tools_file.write_text('''
"""Simple math tools for demonstration."""

def add_numbers(a: float, b: float) -> float:
    """Add two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of a and b
    """
    return a + b


def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Product of a and b
    """
    return a * b


def calculate_percentage(value: float, total: float) -> float:
    """Calculate percentage of value relative to total.
    
    Args:
        value: The value to calculate percentage for
        total: The total value (100%)
        
    Returns:
        Percentage as a decimal (e.g., 0.25 for 25%)
    """
    if total == 0:
        return 0.0
    return (value / total) * 100
''')
    
    # Create individual tool configuration files (not directories)
    config_file1 = tools_dir / "math_tools_config.json"
    config_data1 = {
        "id": "math_tools",
        "type": "python",
        "module_path": "math_tools",
        "functions": ["add_numbers", "multiply_numbers"],
        "package_path": ".",
    }
    config_file1.write_text(json.dumps(config_data1, indent=2))
    
    config_file2 = tools_dir / "percentage_tools_config.json"
    config_data2 = {
        "id": "percentage_tools",
        "type": "python",
        "module_path": "math_tools",
        "functions": ["calculate_percentage"],
        "package_path": ".",
    }
    config_file2.write_text(json.dumps(config_data2, indent=2))
    
    return tools_dir, [config_file1, config_file2]


def create_example_mcp_config():
    """Create example MCP server configuration."""
    
    config_dir = Path(tempfile.mkdtemp(prefix="strands_mcp_"))
    
    # Example MCP server configuration (stdio)
    mcp_config_file = config_dir / "example_mcp.json"
    mcp_config_data = {
        "id": "filesystem_server",
        "type": "mcp",
        "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem"],
        "args": ["/tmp"],
        "functions": ["read_file", "write_file", "list_directory"]
    }
    
    mcp_config_file.write_text(json.dumps(mcp_config_data, indent=2))
    
    return config_dir, [mcp_config_file]


async def python_tools_example():
    """Demonstrate Python function tools."""
    print("Python Tools Example")
    print("=" * 40)
    
    # Create example tools
    tools_dir, config_files = create_example_python_tools()
    
    try:
        # Configure agent with Python tools (individual files, not directories)
        config = AgentFactoryConfig(
            model="gpt-4o",
            system_prompt="You are a helpful assistant with access to math tools. Use them to help with calculations.",
            tool_config_paths=[str(f) for f in config_files],  # Individual files
            show_tool_use=True,  # Show detailed tool usage
        )
        
        factory = AgentFactory(config)
        await factory.initialize()
        agent = factory.create_agent()
        
        print(f"Created agent with Python tools from individual config files:")
        for config_file in config_files:
            print(f"  - {config_file.name}")
        print("Available tools: add_numbers, multiply_numbers, calculate_percentage")
        
        # Test the tools
        test_queries = [
            "What tools do you have available?",
            "Can you add 15 and 27?",
            "What's 8 multiplied by 12?",
            "If I scored 85 out of 100, what percentage is that?",
            "Can you calculate 25% of 200 and then add 50 to the result?"
        ]
        
        with agent as a:
            for query in test_queries:
                print(f"\n{'='*50}")
                print(f"Query: {query}")
                print("-" * 50)
                
                success = await a.send_message_to_agent(query, show_user_input=False)
                if not success:
                    print("Failed to process query")
                    
    except Exception as e:
        print(f"Python tools example error: {e}")
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(tools_dir)
        print(f"\nCleaned up tools directory: {tools_dir}")


async def mcp_tools_example():
    """Demonstrate MCP server tools."""
    print("MCP Tools Example")
    print("=" * 40)
    
    # Create example MCP configuration
    config_dir, config_files = create_example_mcp_config()
    
    try:
        # Configure agent with MCP tools (individual files, not directories)
        config = AgentFactoryConfig(
            model="gpt-4o",
            system_prompt="You are a helpful assistant with access to filesystem tools via MCP. Help users with file operations.",
            tool_config_paths=[str(f) for f in config_files],  # Individual files
            show_tool_use=True,
        )
        
        factory = AgentFactory(config)
        await factory.initialize()
        agent = factory.create_agent()
        
        print(f"Created agent with MCP tools from individual config files:")
        for config_file in config_files:
            print(f"  - {config_file.name}")
        print("Available tools: read_file, write_file, list_directory")
        print("Note: This example requires Node.js and the MCP filesystem server")
        
        # Test the MCP tools
        test_queries = [
            "What tools do you have available?",
            "Can you list the contents of the /tmp directory?",
            "Can you create a test file in /tmp with some sample content?",
        ]
        
        with agent as a:
            for query in test_queries:
                print(f"\n{'='*50}")
                print(f"Query: {query}")
                print("-" * 50)
                
                success = await a.send_message_to_agent(query, show_user_input=False)
                if not success:
                    print("Failed to process query")
                    
    except Exception as e:
        print(f"MCP tools example error: {e}")
        print("Note: MCP tools require additional dependencies and servers to be running")
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(config_dir)
        print(f"\nCleaned up config directory: {config_dir}")


async def mixed_tools_example():
    """Demonstrate using both Python and MCP tools together."""
    print("Mixed Tools Example")
    print("=" * 40)
    
    # Create both types of tools
    python_tools_dir, python_configs = create_example_python_tools()
    mcp_config_dir, mcp_configs = create_example_mcp_config()
    
    try:
        # Configure agent with both tool types (all individual files)
        all_config_files = [str(f) for f in python_configs + mcp_configs]
        
        config = AgentFactoryConfig(
            model="gpt-4o",
            system_prompt="You are a helpful assistant with access to both math tools and filesystem tools. Use them as needed to help users.",
            tool_config_paths=all_config_files,  # Individual files only
            show_tool_use=True,
        )
        
        factory = AgentFactory(config)
        await factory.initialize()
        agent = factory.create_agent()
        
        print("Created agent with both Python and MCP tools from individual config files:")
        print("Python tool configs:")
        for config_file in python_configs:
            print(f"  - {config_file.name}")
        print("MCP tool configs:")
        for config_file in mcp_configs:
            print(f"  - {config_file.name}")
        print("Python tools: add_numbers, multiply_numbers, calculate_percentage")
        print("MCP tools: read_file, write_file, list_directory")
        
        # Test mixed tool usage
        test_queries = [
            "What tools do you have available?",
            "Can you calculate 15 + 27 and then save the result to a file in /tmp?",
            "List the files in /tmp and count how many there are using your math tools",
        ]
        
        with agent as a:
            for query in test_queries:
                print(f"\n{'='*50}")
                print(f"Query: {query}")
                print("-" * 50)
                
                success = await a.send_message_to_agent(query, show_user_input=False)
                if not success:
                    print("Failed to process query")
                    
    except Exception as e:
        print(f"Mixed tools example error: {e}")
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(python_tools_dir)
        shutil.rmtree(mcp_config_dir)
        print(f"\nCleaned up directories")


def main():
    """Main example selector."""
    print("Tool Configuration Examples")
    print("=" * 30)
    print("1. Python Function Tools")
    print("2. MCP Server Tools")
    print("3. Mixed Tools (Python + MCP)")
    print("4. All Examples")
    
    choice = input("\nSelect example [1-4]: ").strip()
    
    if choice == "1":
        asyncio.run(python_tools_example())
    elif choice == "2":
        asyncio.run(mcp_tools_example())
    elif choice == "3":
        asyncio.run(mixed_tools_example())
    elif choice == "4":
        asyncio.run(python_tools_example())
        asyncio.run(mcp_tools_example())
        asyncio.run(mixed_tools_example())
    else:
        print("Invalid choice. Running Python tools example...")
        asyncio.run(python_tools_example())


if __name__ == "__main__":
    """
    Run the tool configuration examples.
    
    Prerequisites:
    - Set OPENAI_API_KEY environment variable
    - Install strands-agent-factory with tool support
    - For MCP examples: Install Node.js and MCP server packages
    
    Usage:
        python examples/tool_configuration_example.py
    """
    
    print("Tool Configuration Examples")
    print("=" * 30)
    print("Prerequisites:")
    print("- Set OPENAI_API_KEY environment variable")
    print("- Install: pip install 'strands-agent-factory[openai,tools]'")
    print("- For MCP examples: Node.js and MCP filesystem server")
    print()
    print("Note: tool_config_paths accepts individual configuration files only.")
    print("Directories and glob patterns are not supported.")
    print()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Unexpected error: {e}")