#!/usr/bin/env python3
"""
Basic usage example for strands_engine.

Shows how to create and use the engine for conversational AI with proper
tool loading architecture (engine loads tools, strands-agents executes them).
"""

import asyncio
from pathlib import Path
import tempfile

from strands_engine import AgentFactory, EngineConfig


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
    engine = AgentFactory(config)
    print(f"Created engine with model: {config.model}")
    
    success = await engine.initialize()
    if not success:
        print("Failed to initialize engine")
        return
    
    print("Engine initialized successfully")
    
    try:
        # Process some messages
        # The strands-agents Agent (created by engine) handles LLM communication
        messages = [
            "Hello! Can you introduce yourself?",
            "What can you help me with?", 
            "Thank you for the information!"
        ]
        
        for i, message in enumerate(messages, 1):
            print(f"\n--- Message {i} ---")
            print(f"User: {message}")
            
            # Engine coordinates with strands-agents Agent for response
            response = await engine.process_message(message)
            print(f"Assistant: {response}")
            
    finally:
        await engine.shutdown()
        print("\nEngine shutdown complete")


async def session_example():
    """Example with session management via strands-agents."""
    print("\n=== Session Management Example ===")
    
    # Create temporary sessions directory
    with tempfile.TemporaryDirectory() as sessions_dir:
        config = EngineConfig(
            model="gpt-4o",
            system_prompt="You are an assistant with session memory.",
            sessions_home=sessions_dir,  # strands-agents manages sessions here
            session_id="demo_conversation_123"
        )
        
        engine = AgentFactory(config)
        print(f"Sessions managed by strands-agents in: {config.sessions_home}")
        print(f"Session ID: {config.session_id}")
        
        success = await engine.initialize()
        if not success:
            print("Failed to initialize engine")
            return
        
        try:
            # First conversation turn
            response1 = await engine.process_message("Hi! My name is Alice.")
            print(f"Response 1: {response1}")
            
            # Second conversation turn - strands-agents Agent should remember context
            response2 = await engine.process_message("What's my name?")
            print(f"Response 2: {response2}")
            
        finally:
            await engine.shutdown()


async def file_upload_example():
    """Example with file uploads processed by engine."""
    print("\n=== File Upload Example ===")
    
    # Create a sample text file for demonstration
    sample_file = Path("/tmp/sample_doc.txt")
    sample_file.write_text("This is a sample document for testing file uploads with strands engine.")
    
    config = EngineConfig(
        model="claude-3-sonnet-20240229",
        system_prompt="You are an assistant that can analyze uploaded documents.",
        file_paths=[
            (sample_file, "text/plain")  # Engine processes files into content blocks
        ]
    )
    
    engine = AgentFactory(config)
    success = await engine.initialize()
    
    if not success:
        print("Failed to initialize engine")
        return
    
    try:
        # Engine processed files are available to strands-agents Agent
        response = await engine.process_message("What files do you have access to? Can you summarize them?")
        print(f"Response: {response}")
        
    finally:
        await engine.shutdown()
        # Clean up sample file
        sample_file.unlink(missing_ok=True)


async def tool_example():
    """Example with tool loading (engine loads, strands-agents executes)."""
    print("\n=== Tool Loading Example ===")
    
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
        tool_config_paths=[tool_config]  # Engine loads tools from config files
    )
    
    engine = AgentFactory(config)
    success = await engine.initialize()  # Loads tools and configures Agent
    
    if not success:
        print("Failed to initialize engine")
        return
    
    try:
        # strands-agents Agent has access to loaded tools and can execute them
        response = await engine.process_message("What tools do you have access to? Can you tell me the current time?")
        print(f"Response: {response}")
        
    finally:
        await engine.shutdown()
        # Clean up sample config
        tool_config.unlink(missing_ok=True)


async def comprehensive_example():
    """Comprehensive example showing engine's coordination role."""
    print("\n=== Comprehensive Example ===")
    
    # Create temporary files and directories
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        sessions_dir = temp_path / "sessions"
        sessions_dir.mkdir()
        
        # Sample document (engine will process)
        doc_file = temp_path / "sample.txt"
        doc_file.write_text("This document contains important information about AI engines.")
        
        # Sample tool config (engine will load)
        tool_config = temp_path / "tools.json"
        tool_config.write_text('''{
    "tools": [
        {
            "id": "datetime_tool",
            "type": "python",
            "module": "datetime",
            "functions": ["now", "date"]
        }
    ]
}''')
        
        config = EngineConfig(
            model="gpt-4o",
            system_prompt="You are a comprehensive AI assistant with access to documents and tools.",
            sessions_home=sessions_dir,           # strands-agents manages sessions
            session_id="comprehensive_demo",
            tool_config_paths=[tool_config],      # Engine loads tools
            file_paths=[                          # Engine processes files
                (doc_file, "text/plain")
            ],
            conversation_strategy="sliding_window",
            max_context_length=4000
        )
        
        engine = AgentFactory(config)
        print(f"Configuration:")
        print(f"  Model: {config.model}")
        print(f"  Sessions managed by strands-agents in: {config.sessions_home}")
        print(f"  Session ID: {config.session_id}")
        print(f"  Tool configs (engine loads): {len(config.tool_config_paths)}")
        print(f"  Files (engine processes): {len(config.file_paths)}")
        
        success = await engine.initialize()
        if not success:
            print("Failed to initialize engine")
            return
        
        try:
            questions = [
                "What capabilities do you have?",
                "What documents do you have access to?",
                "What tools are available to you?",
                "Can you tell me the current time using your tools?"
            ]
            
            for i, question in enumerate(questions, 1):
                print(f"\n--- Question {i} ---")
                print(f"User: {question}")
                
                # Engine coordinates with strands-agents Agent
                # Agent has access to loaded tools and processed files
                # Agent executes any needed tools automatically
                response = await engine.process_message(question)
                print(f"Assistant: {response}")
                
        finally:
            await engine.shutdown()


async def architecture_explanation():
    """Explain the architecture with a simple example."""
    print("\n=== Architecture Explanation ===")
    print("Strands Engine Architecture:")
    print("1. Engine loads tools from config files")
    print("2. Engine processes uploaded files")
    print("3. Engine creates strands-agents Agent with tools + files")
    print("4. Agent handles LLM communication and tool execution")
    print("5. Engine coordinates message flow and session management")
    print("")
    print("Key Separation:")
    print("- Engine: Loading, configuring, coordinating")
    print("- strands-agents Agent: Executing, communicating, processing")
    print("")


async def main():
    """Run all examples."""
    try:
        await architecture_explanation()
        await basic_example()
        await session_example()
        await file_upload_example()
        await tool_example()
        await comprehensive_example()
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())