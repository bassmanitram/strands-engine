#!/usr/bin/env python3
"""
Basic usage example for strands_agent_factory.

This example demonstrates how to create and use an agent factory
for basic conversational AI interactions.
"""

import asyncio
from strands_agent_factory import AgentFactoryConfig, AgentFactory


async def basic_example():
    """Basic agent creation and interaction."""
    print("🚀 Basic strands_agent_factory Example")
    print("=" * 50)
    
    # Create configuration
    config = AgentFactoryConfig(
        model="gpt-4o",  # Use OpenAI GPT-4
        system_prompt="You are a helpful assistant that provides clear, concise answers."
    )
    print(f"✓ Created configuration with model: {config.model}")
    
    # Create and initialize factory
    factory = AgentFactory(config)
    print("✓ Created AgentFactory")
    
    success = await factory.initialize()
    if not success:
        print("❌ Factory initialization failed - check your API credentials")
        return
    
    print("✓ Factory initialized successfully")
    
    # Create agent
    agent = factory.create_agent()
    if not agent:
        print("❌ Agent creation failed")
        return
    
    print("✓ Agent created successfully")
    print("=" * 50)
    
    # Interactive conversation
    print("💬 Starting conversation (type 'quit' to exit)")
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ['quit', 'exit', 'bye']:
                break
                
            if not user_input:
                continue
                
            success = await agent.send_message_to_agent(user_input, show_user_input=False)
            if not success:
                print("❌ Failed to process message")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n👋 Goodbye!")


async def advanced_example():
    """Advanced configuration with tools and file processing."""
    print("🚀 Advanced strands_agent_factory Example")
    print("=" * 50)
    
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
        # Add example file (create it first)
        file_paths=[
            ("example_data.txt", "text/plain")
        ],
        # Add example tools (create config first)
        tool_config_paths=[
            "tools/example_tools.json"
        ],
        session_id="advanced_example_session"
    )
    print(f"✓ Created advanced configuration")
    
    # Create and initialize factory
    factory = AgentFactory(config)
    success = await factory.initialize()
    
    if not success:
        print("❌ Factory initialization failed")
        return
    
    print("✓ Advanced factory initialized")
    
    # Create agent
    agent = factory.create_agent()
    if not agent:
        print("❌ Agent creation failed")
        return
    
    print("✓ Advanced agent created")
    print("=" * 50)
    
    # Example interactions
    test_messages = [
        "What files do you have access to?",
        "What tools are available to you?",
        "Can you help me analyze the uploaded data?",
    ]
    
    for message in test_messages:
        print(f"\n🔹 Testing: {message}")
        success = await agent.send_message_to_agent(message, show_user_input=False)
        if not success:
            print("❌ Message failed")
        print("-" * 30)


async def litellm_example():
    """Example using LiteLLM for multi-provider support."""
    print("🚀 LiteLLM Multi-Provider Example")
    print("=" * 50)
    
    # Test different providers through LiteLLM
    providers = [
        ("litellm:gpt-4o", "OpenAI via LiteLLM"),
        ("litellm:anthropic/claude-3-5-sonnet-20241022", "Anthropic via LiteLLM"),
        ("litellm:gemini/gemini-2.5-flash", "Google Gemini via LiteLLM"),
    ]
    
    for model_string, description in providers:
        print(f"\n🔹 Testing {description}")
        print(f"   Model: {model_string}")
        
        try:
            config = AgentFactoryConfig(
                model=model_string,
                system_prompt=f"You are testing {description}. Respond briefly to confirm you're working."
            )
            
            factory = AgentFactory(config)
            success = await factory.initialize()
            
            if success:
                agent = factory.create_agent()
                if agent:
                    print(f"   ✓ {description} initialized successfully")
                    
                    # Quick test
                    success = await agent.send_message_to_agent(
                        "Hello! Please confirm you're working by saying 'System operational'",
                        show_user_input=False
                    )
                    
                    if success:
                        print(f"   ✓ {description} test completed")
                    else:
                        print(f"   ❌ {description} interaction failed")
                else:
                    print(f"   ❌ {description} agent creation failed")
            else:
                print(f"   ❌ {description} initialization failed")
                
        except Exception as e:
            print(f"   ❌ {description} error: {e}")
        
        print("-" * 40)


def main():
    """Main example selector."""
    print("strands_agent_factory Examples")
    print("=" * 30)
    print("1. Basic Usage")
    print("2. Advanced Configuration")
    print("3. LiteLLM Multi-Provider")
    print("4. All Examples")
    
    choice = input("\nSelect example [1-4]: ").strip()
    
    if choice == "1":
        asyncio.run(basic_example())
    elif choice == "2":
        asyncio.run(advanced_example())
    elif choice == "3":
        asyncio.run(litellm_example())
    elif choice == "4":
        asyncio.run(basic_example())
        asyncio.run(advanced_example())
        asyncio.run(litellm_example())
    else:
        print("Invalid choice. Running basic example...")
        asyncio.run(basic_example())


if __name__ == "__main__":
    """
    Run the strands_agent_factory examples.
    
    Prerequisites:
    - Set appropriate API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY)
    - Install strands-agents and dependencies
    - Ensure strands_agent_factory is importable
    
    Usage:
        python examples/basic_usage.py
    """
    main()