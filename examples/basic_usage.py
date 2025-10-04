#!/usr/bin/env python3
"""
Basic usage example for strands_engine.

Shows how to create and use the engine for conversational AI.
"""

import asyncio
from pathlib import Path

from strands_engine import Engine, EngineConfig


async def basic_example():
    """Basic engine usage example."""
    print("=== Basic Strands Engine Example ===")
    
    # Create configuration
    config = EngineConfig(
        model="gpt-4o",
        system_prompt="You are a helpful assistant for demonstrating the strands engine.",
        conversation_strategy="full_history"
    )
    
    # Create and initialize engine  
    engine = Engine(config)
    print(f"Created engine with model: {config.model}")
    
    success = await engine.initialize()
    if not success:
        print("Failed to initialize engine")
        return
    
    print("Engine initialized successfully")
    
    try:
        # Process some messages
        messages = [
            "Hello! Can you introduce yourself?",
            "What can you help me with?",
            "Thank you for the information!"
        ]
        
        for i, message in enumerate(messages, 1):
            print(f"\n--- Message {i} ---")
            print(f"User: {message}")
            
            response = await engine.process_message(message)
            print(f"Assistant: {response}")
            
    finally:
        await engine.shutdown()
        print("\nEngine shutdown complete")


async def file_upload_example():
    """Example with file uploads."""
    print("\n=== File Upload Example ===")
    
    # Create a sample text file for demonstration
    sample_file = Path("/tmp/sample_doc.txt")
    sample_file.write_text("This is a sample document for testing file uploads with strands engine.")
    
    config = EngineConfig(
        model="claude-3-sonnet-20240229",
        system_prompt="You are an assistant that can analyze uploaded documents.",
        file_paths=[
            (sample_file, "text/plain")
        ]
    )
    
    engine = Engine(config)
    success = await engine.initialize()
    
    if not success:
        print("Failed to initialize engine")
        return
    
    try:
        response = await engine.process_message("What files do you have access to? Can you summarize them?")
        print(f"Response: {response}")
        
    finally:
        await engine.shutdown()
        # Clean up sample file
        sample_file.unlink(missing_ok=True)


async def tool_example():
    """Example with tool configuration."""
    print("\n=== Tool Configuration Example ===")
    
    # Create a sample tool config for demonstration
    tool_config = Path("/tmp/sample_tools.json")
    tool_config.write_text('''{
    "tools": [
        {
            "id": "sample_python_tool",
            "type": "python",
            "module": "datetime",
            "functions": ["now"]
        }
    ]
}''')
    
    config = EngineConfig(
        model="gpt-4o",
        system_prompt="You are an assistant with access to tools.",
        tool_config_paths=[tool_config]
    )
    
    engine = Engine(config)
    success = await engine.initialize()
    
    if not success:
        print("Failed to initialize engine")
        return
    
    try:
        response = await engine.process_message("What tools do you have access to?")
        print(f"Response: {response}")
        
    finally:
        await engine.shutdown()
        # Clean up sample config
        tool_config.unlink(missing_ok=True)


async def main():
    """Run all examples."""
    try:
        await basic_example()
        await file_upload_example()
        await tool_example()
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())