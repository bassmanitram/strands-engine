#!/usr/bin/env python3
"""
Basic usage examples for strands_engine.

This script demonstrates the key features and usage patterns of strands_engine,
showing how to create and configure AgentFactory instances for different use
cases. The examples illustrate the separation of concerns between strands_engine
(tool loading, configuration, coordination) and strands-agents (execution).

The examples cover:
- Basic agent creation and message processing
- Session management and conversation persistence
- File upload processing and content integration
- Tool loading and configuration
- Comprehensive scenarios combining multiple features

Each example demonstrates proper initialization, usage, and cleanup patterns
while explaining the architectural boundaries between components.
"""

import asyncio
from pathlib import Path
import tempfile

from strands_engine import AgentFactory, EngineConfig


async def basic_example():
    """
    Demonstrate basic strands_engine usage.
    
    Shows the fundamental pattern of creating an EngineConfig, initializing
    an AgentFactory, and processing messages. This example illustrates the
    minimal setup required for conversational AI with strands_engine.
    """
    print("=== Basic Strands Engine Example ===")
    
    # Create configuration with minimal required parameters
    config = EngineConfig(
        model="gpt-4o",
        system_prompt="You are a helpful assistant for demonstrating the strands engine."
    )
    
    # Create and initialize engine  
    engine = AgentFactory(config)
    print(f"Created engine with model: {config.model}")
    
    # Initialize performs async setup of tools, files, and strands-agents integration
    success = await engine.initialize()
    if not success:
        print("Failed to initialize engine")
        return
    
    print("Engine initialized successfully")
    
    try:
        # Process conversation messages
        # The engine coordinates with strands-agents Agent for LLM communication
        messages = [
            "Hello! Can you introduce yourself?",
            "What can you help me with?", 
            "Thank you for the information!"
        ]
        
        for i, message in enumerate(messages, 1):
            print(f"\\n--- Message {i} ---")
            print(f"User: {message}")
            
            # Engine processes message through strands-agents Agent
            response = await engine.process_message(message)
            print(f"Assistant: {response}")
            
    except Exception as e:
        print(f"Error during message processing: {e}")
        
    finally:
        # Cleanup is handled automatically by the engine's resource management
        print("\\nBasic example complete")


async def session_example():
    """
    Demonstrate session management and conversation persistence.
    
    Shows how strands_engine integrates with strands-agents session management
    to provide conversation persistence across multiple interactions. The engine
    configures session parameters while strands-agents handles the actual
    persistence mechanics.
    """
    print("\\n=== Session Management Example ===")
    
    # Create temporary sessions directory for demonstration
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
            # First conversation turn establishes context
            print("\\n--- First Turn ---")
            print("User: Hi! My name is Alice.")
            response1 = await engine.process_message("Hi! My name is Alice.")
            print(f"Assistant: {response1}")
            
            # Second conversation turn - strands-agents Agent should remember context
            print("\\n--- Second Turn ---")
            print("User: What's my name?")
            response2 = await engine.process_message("What's my name?")
            print(f"Assistant: {response2}")
            
        except Exception as e:
            print(f"Error during session example: {e}")
            
        finally:
            print("\\nSession example complete")


async def file_upload_example():
    """
    Demonstrate file upload processing and content integration.
    
    Shows how strands_engine processes uploaded files into content blocks
    that are made available to the strands-agents Agent. The engine handles
    file reading, MIME type detection, and content formatting while the
    Agent integrates the content into conversations.
    """
    print("\\n=== File Upload Example ===")
    
    # Create a sample text file for demonstration
    sample_file = Path("/tmp/sample_doc.txt")
    sample_file.write_text("This is a sample document for testing file uploads with strands engine.")
    
    try:
        config = EngineConfig(
            model="claude-3-5-sonnet-20241022",
            system_prompt="You are an assistant that can analyze uploaded documents.",
            file_paths=[
                (sample_file, "text/plain")  # Engine processes files into content blocks
            ]
        )
        
        engine = AgentFactory(config)
        print(f"Configured with {len(config.file_paths)} uploaded files")
        
        success = await engine.initialize()
        if not success:
            print("Failed to initialize engine")
            return
        
        try:
            # Engine processed files are available to strands-agents Agent
            print("\\n--- File Analysis ---")
            print("User: What files do you have access to? Can you summarize them?")
            response = await engine.process_message("What files do you have access to? Can you summarize them?")
            print(f"Assistant: {response}")
            
        except Exception as e:
            print(f"Error during file upload example: {e}")
            
    finally:
        # Clean up sample file
        sample_file.unlink(missing_ok=True)
        print("\\nFile upload example complete")


async def tool_example():
    """
    Demonstrate tool loading and configuration.
    
    Shows how strands_engine loads tools from configuration files and makes
    them available to strands-agents for execution. The engine handles tool
    discovery, loading, and configuration while strands-agents manages the
    actual tool execution during conversations.
    """
    print("\\n=== Tool Loading Example ===")
    
    # Create a sample tool config for demonstration
    tool_config = Path("/tmp/sample_tools.json")
    tool_config_content = '''{
    "id": "sample_python_tool",
    "type": "python", 
    "module_path": "datetime",
    "functions": ["datetime.now"],
    "source_file": "/tmp/sample_tools.json"
}'''
    tool_config.write_text(tool_config_content)
    
    try:
        config = EngineConfig(
            model="gpt-4o",
            system_prompt="You are an assistant with access to tools.",
            tool_config_paths=[tool_config]  # Engine loads tools from config files
        )
        
        engine = AgentFactory(config)
        print(f"Configured with {len(config.tool_config_paths)} tool configuration files")
        
        success = await engine.initialize()  # Loads tools and configures Agent
        if not success:
            print("Failed to initialize engine")
            return
        
        try:
            # strands-agents Agent has access to loaded tools and can execute them
            print("\\n--- Tool Usage ---")
            print("User: What tools do you have access to? Can you tell me the current time?")
            response = await engine.process_message("What tools do you have access to? Can you tell me the current time?")
            print(f"Assistant: {response}")
            
        except Exception as e:
            print(f"Error during tool example: {e}")
            
    finally:
        # Clean up sample config
        tool_config.unlink(missing_ok=True)
        print("\\nTool example complete")


async def comprehensive_example():
    """
    Demonstrate comprehensive strands_engine capabilities.
    
    Shows a complete scenario that combines multiple strands_engine features:
    session management, file uploads, tool loading, and conversation management.
    This example illustrates how the engine coordinates all these capabilities
    while strands-agents handles the execution details.
    """
    print("\\n=== Comprehensive Example ===")
    
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
        tool_config_content = '''{
    "id": "datetime_tool",
    "type": "python",
    "module_path": "datetime", 
    "functions": ["datetime.now"],
    "source_file": "''' + str(tool_config) + '''"
}'''
        tool_config.write_text(tool_config_content)
        
        config = EngineConfig(
            model="gpt-4o",
            system_prompt="You are a comprehensive AI assistant with access to documents and tools.",
            sessions_home=sessions_dir,           # strands-agents manages sessions
            session_id="comprehensive_demo",
            tool_config_paths=[tool_config],      # Engine loads tools
            file_paths=[                          # Engine processes files
                (doc_file, "text/plain")
            ],
            conversation_manager_type="sliding_window",
            sliding_window_size=40
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
                print(f"\\n--- Question {i} ---")
                print(f"User: {question}")
                
                # Engine coordinates with strands-agents Agent
                # Agent has access to loaded tools and processed files
                # Agent executes any needed tools automatically
                response = await engine.process_message(question)
                print(f"Assistant: {response}")
                
        except Exception as e:
            print(f"Error during comprehensive example: {e}")
            
        finally:
            print("\\nComprehensive example complete")


async def architecture_explanation():
    """
    Explain the strands_engine architecture and design principles.
    
    Provides an overview of how strands_engine components work together
    and the separation of concerns between strands_engine and strands-agents.
    This helps users understand the architectural patterns and design decisions.
    """
    print("\\n=== Architecture Explanation ===")
    print("Strands Engine Architecture:")
    print("1. Engine loads tools from configuration files")
    print("2. Engine processes uploaded files into content blocks")
    print("3. Engine creates strands-agents Agent with tools + files")
    print("4. Agent handles LLM communication and tool execution")
    print("5. Engine coordinates message flow and session management")
    print("")
    print("Key Separation of Concerns:")
    print("- strands_engine: Loading, configuring, coordinating")
    print("- strands-agents: Executing, communicating, processing")
    print("")
    print("Benefits:")
    print("- Clean architecture boundaries")
    print("- Testable components")
    print("- Flexible configuration")
    print("- Reusable patterns")
    print("")


async def main():
    """
    Run all strands_engine examples.
    
    Executes all example functions in sequence to demonstrate the full
    range of strands_engine capabilities. Includes comprehensive error
    handling to ensure all examples run even if individual ones fail.
    """
    print("Starting strands_engine examples...")
    
    examples = [
        ("Architecture Overview", architecture_explanation),
        ("Basic Usage", basic_example),
        ("Session Management", session_example),
        ("File Uploads", file_upload_example),
        ("Tool Loading", tool_example),
        ("Comprehensive Features", comprehensive_example)
    ]
    
    for name, example_func in examples:
        try:
            print(f"\\n{'='*60}")
            print(f"Running: {name}")
            print('='*60)
            await example_func()
            
        except Exception as e:
            print(f"Error in {name} example: {e}")
            import traceback
            traceback.print_exc()
            print(f"Continuing with remaining examples...")
    
    print(f"\\n{'='*60}")
    print("All strands_engine examples completed!")
    print('='*60)


if __name__ == "__main__":
    """
    Entry point for running strands_engine examples.
    
    This script can be run directly to see all strands_engine capabilities
    in action. It demonstrates proper async usage patterns and comprehensive
    error handling for production-like applications.
    """
    asyncio.run(main())