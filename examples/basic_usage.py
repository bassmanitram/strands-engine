#!/usr/bin/env python3
"""
Basic usage examples for strands_agent_factory.

This example demonstrates how to create and use an agent factory
for basic conversational AI interactions with various providers.
"""

import asyncio
import sys
from pathlib import Path
from strands_agent_factory import AgentFactoryConfig, AgentFactory
from strands_agent_factory.core.exceptions import (
    FactoryError, ConfigurationError, InitializationError, ModelLoadError
)


async def basic_example():
    """Basic agent creation and interaction."""
    print("Basic strands_agent_factory Example")
    print("=" * 50)
    
    # Create configuration
    config = AgentFactoryConfig(
        model="gpt-4o",  # Use OpenAI GPT-4 (requires OPENAI_API_KEY)
        system_prompt="You are a helpful assistant that provides clear, concise answers."
    )
    print(f"Created configuration with model: {config.model}")
    
    try:
        # Create and initialize factory
        factory = AgentFactory(config)
        print("Created AgentFactory")
        
        await factory.initialize()
        print("Factory initialized successfully")
        
        # Create agent
        agent = factory.create_agent()
        print("Agent created successfully")
        print("=" * 50)
        
        # Interactive conversation
        print("Starting conversation (type 'quit' to exit)")
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    break
                    
                if not user_input:
                    continue
                    
                with agent as a:
                    success = await a.send_message_to_agent(user_input, show_user_input=False)
                    if not success:
                        print("Failed to process message")
                        
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("\nGoodbye!")
        
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
    except InitializationError as e:
        print(f"Initialization failed: {e}")
        print("   Check your API credentials and configuration")
    except ModelLoadError as e:
        print(f"Model loading failed: {e}")
    except FactoryError as e:
        print(f"Factory error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


async def multi_provider_example():
    """Example showing different AI providers."""
    print("Multi-Provider strands_agent_factory Example")
    print("=" * 50)
    
    # Test different providers
    providers = [
        ("gpt-4o", "OpenAI GPT-4 (requires OPENAI_API_KEY)"),
        ("anthropic:claude-3-5-sonnet-20241022", "Anthropic Claude (requires ANTHROPIC_API_KEY)"),
        ("gemini:gemini-2.5-flash", "Google Gemini (requires GOOGLE_API_KEY)"),
        ("ollama:llama3.1:8b", "Ollama Llama (requires local Ollama server)"),
    ]
    
    for model_string, description in providers:
        print(f"\nTesting {description}")
        print(f"   Model: {model_string}")
        
        try:
            config = AgentFactoryConfig(
                model=model_string,
                system_prompt=f"You are testing {description}. Respond briefly to confirm you're working."
            )
            
            factory = AgentFactory(config)
            await factory.initialize()
            agent = factory.create_agent()
            
            print(f"   {description} initialized successfully")
            
            # Quick test
            with agent as a:
                success = await a.send_message_to_agent(
                    "Hello! Please confirm you're working by saying 'System operational'",
                    show_user_input=False
                )
                
                if success:
                    print(f"   {description} test completed")
                else:
                    print(f"   {description} interaction failed")
                    
        except ConfigurationError as e:
            print(f"   {description} configuration error: {e}")
        except InitializationError as e:
            print(f"   {description} initialization failed: {e}")
        except FactoryError as e:
            print(f"   {description} factory error: {e}")
        except Exception as e:
            print(f"   {description} unexpected error: {e}")
        
        print("-" * 40)


async def advanced_example():
    """Advanced configuration with tools and file processing."""
    print("Advanced strands_agent_factory Example")
    print("=" * 50)
    
    # Create example files for demonstration
    example_dir = Path("example_data")
    example_dir.mkdir(exist_ok=True)
    
    # Create example text file
    example_file = example_dir / "sample.txt"
    example_file.write_text("This is sample data for the advanced example.\nIt contains multiple lines of text.")
    
    # Create example tool configuration file
    tool_config_file = example_dir / "math_tools.json"
    tool_config_file.write_text("""{
  "id": "basic_math",
  "type": "python",
  "module_path": "operator",
  "functions": ["add", "mul", "sub"]
}""")
    
    try:
        # Create advanced configuration
        config = AgentFactoryConfig(
            model="anthropic:claude-3-5-sonnet-20241022",  # Use Anthropic Claude
            system_prompt="You are an advanced assistant with access to tools and uploaded files.",
            conversation_manager_type="sliding_window",
            sliding_window_size=15,
            show_tool_use=True,
            model_config={
                "temperature": 0.7,
                "max_tokens": 2000
            },
            # Add example file
            file_paths=[
                (str(example_file), "text/plain")
            ],
            # Add example tool configuration file (individual file, not directory)
            tool_config_paths=[
                str(tool_config_file)
            ],
            session_id="advanced_example_session"
        )
        print(f"Created advanced configuration")
        
        # Create and initialize factory
        factory = AgentFactory(config)
        await factory.initialize()
        print("Advanced factory initialized")
        
        # Create agent
        agent = factory.create_agent()
        print("Advanced agent created")
        print("=" * 50)
        
        # Example interactions
        test_messages = [
            "What files do you have access to?",
            "What tools are available to you?",
            "Can you help me analyze the uploaded data?",
            "Can you add 15 and 27 using your tools?",
        ]
        
        with agent as a:
            for message in test_messages:
                print(f"\nTesting: {message}")
                success = await a.send_message_to_agent(message, show_user_input=False)
                if not success:
                    print("Message failed")
                print("-" * 30)
            
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
    except InitializationError as e:
        print(f"Initialization failed: {e}")
    except FactoryError as e:
        print(f"Factory error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Cleanup example files
        import shutil
        if example_dir.exists():
            shutil.rmtree(example_dir)
            print(f"\nCleaned up example directory: {example_dir}")


async def session_example():
    """Example demonstrating session persistence."""
    print("Session Persistence Example")
    print("=" * 50)
    
    session_dir = Path("example_sessions")
    session_id = "demo_session"
    
    try:
        config = AgentFactoryConfig(
            model="gpt-4o",
            system_prompt="You are a helpful assistant. Remember our conversation across sessions.",
            session_id=session_id,
            sessions_home=session_dir,
            conversation_manager_type="sliding_window",
            sliding_window_size=20
        )
        
        factory = AgentFactory(config)
        await factory.initialize()
        agent = factory.create_agent()
        
        print(f"Created agent with session persistence")
        print(f"Session ID: {session_id}")
        print(f"Sessions stored in: {session_dir}")
        
        # Demonstrate session persistence
        with agent as a:
            print("\nFirst interaction:")
            await a.send_message_to_agent("My name is Alice. Please remember this.", show_user_input=True)
            
            print("\nSecond interaction (should remember name):")
            await a.send_message_to_agent("What is my name?", show_user_input=True)
            
        print(f"\nSession data has been saved to: {session_dir / f'session_{session_id}'}")
        print("You can restart this example and the agent will remember the conversation.")
        
    except Exception as e:
        print(f"Session example error: {e}")
    finally:
        # Note: We don't cleanup session directory so user can see persistence
        print(f"\nSession directory preserved at: {session_dir}")


def main():
    """Main example selector."""
    print("strands_agent_factory Examples")
    print("=" * 30)
    print("1. Basic Usage")
    print("2. Multi-Provider Support")
    print("3. Advanced Configuration")
    print("4. Session Persistence")
    print("5. All Examples")
    
    choice = input("\nSelect example [1-5]: ").strip()
    
    if choice == "1":
        asyncio.run(basic_example())
    elif choice == "2":
        asyncio.run(multi_provider_example())
    elif choice == "3":
        asyncio.run(advanced_example())
    elif choice == "4":
        asyncio.run(session_example())
    elif choice == "5":
        asyncio.run(basic_example())
        asyncio.run(multi_provider_example())
        asyncio.run(advanced_example())
        asyncio.run(session_example())
    else:
        print("Invalid choice. Running basic example...")
        asyncio.run(basic_example())


if __name__ == "__main__":
    """
    Run the strands_agent_factory examples.
    
    Prerequisites:
    - Set appropriate API keys as environment variables:
      * OPENAI_API_KEY for OpenAI models
      * ANTHROPIC_API_KEY for Anthropic models  
      * GOOGLE_API_KEY for Google models
    - Install strands-agents with desired provider support
    - Ensure strands_agent_factory is installed
    
    Usage:
        python examples/basic_usage.py
    """
    
    # Check for basic requirements
    print("strands_agent_factory Examples")
    print("=" * 30)
    print("Prerequisites:")
    print("- Set API keys as environment variables (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)")
    print("- Install: pip install 'strands-agent-factory[openai,anthropic]'")
    print("- For Ollama: Install and run Ollama locally")
    print()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)