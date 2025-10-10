#!/usr/bin/env python3
"""
Enhanced sniff test for strands_agent_factory with real credentials.

This test uses the available litellm:gemini/gemini-2.5-flash model to verify
complete end-to-end functionality including actual agent creation and interaction.
"""

import asyncio
import sys
import os
from pathlib import Path

# Test basic imports
try:
    from strands_agent_factory import AgentFactoryConfig, AgentFactory
    print("✓ Successfully imported strands_agent_factory components")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

async def test_with_real_credentials():
    """Test complete functionality with real Gemini credentials."""
    print("\n=== Testing with Real Gemini Credentials ===")
    
    try:
        # Use the available Gemini model via LiteLLM
        config = AgentFactoryConfig(
            model="litellm:gemini/gemini-2.5-flash",
            system_prompt="You are a helpful test assistant for verifying strands_agent_factory functionality."
        )
        print("✓ Created EngineConfig with Gemini model")
        
        # Create the factory
        factory = AgentFactory(config)
        print("✓ Created AgentFactory successfully")
        
        # Test initialization - should succeed with valid credentials
        print("⚡ Attempting initialization with Gemini credentials...")
        success = await factory.initialize()
        
        if success:
            print("✓ Factory initialization succeeded!")
            
            # Try to create an agent - should work with valid credentials
            agent = factory.create_agent()
            if agent:
                print("✓ Agent creation succeeded!")
                print(f"✓ Agent type: {type(agent).__name__}")
                
                # Test actual interaction with the model
                print("🤖 Testing actual model interaction...")
                try:
                    success = await agent.send_message_to_agent(
                        "Hello! Please respond with exactly: 'strands_agent_factory test successful'"
                    )
                    
                    if success:
                        print("✓ Model interaction completed successfully!")
                        return True
                    else:
                        print("✗ Model interaction failed")
                        return False
                        
                except Exception as e:
                    print(f"✗ Model interaction error: {e}")
                    return False
            else:
                print("✗ Agent creation failed")
                return False
        else:
            print("✗ Factory initialization failed")
            return False
            
    except Exception as e:
        print(f"✗ Error during credential testing: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_complex_configuration_with_gemini():
    """Test complex configuration options with Gemini."""
    print("\n=== Testing Complex Configuration with Gemini ===")
    
    try:
        # Test with various conversation management options
        config = AgentFactoryConfig(
            model="litellm:gemini/gemini-2.5-flash",
            system_prompt="You are a test assistant with conversation management.",
            conversation_manager_type="sliding_window",
            sliding_window_size=10,
            show_tool_use=False,
            model_config={
                "temperature": 0.3,
                "max_tokens": 100
            }
        )
        print("✓ Created complex EngineConfig with Gemini")
        
        factory = AgentFactory(config)
        print("✓ Created AgentFactory with complex config")
        
        success = await factory.initialize()
        if success:
            print("✓ Complex configuration initialization succeeded")
            
            agent = factory.create_agent()
            if agent:
                print("✓ Agent creation with complex config succeeded")
                
                # Test multiple interactions to verify conversation management
                print("🔄 Testing conversation management...")
                
                for i in range(3):
                    success = await agent.send_message_to_agent(
                        f"Message {i+1}: Please respond briefly that you received message {i+1}",
                        show_user_input=False
                    )
                    if not success:
                        print(f"✗ Message {i+1} failed")
                        return False
                
                print("✓ Conversation management test completed")
                return True
            else:
                print("✗ Agent creation failed with complex config")
                return False
        else:
            print("✗ Complex configuration initialization failed")
            return False
            
    except Exception as e:
        print(f"✗ Complex configuration test failed: {e}")
        return False

async def test_file_processing_with_gemini():
    """Test file processing capabilities with Gemini."""
    print("\n=== Testing File Processing with Gemini ===")
    
    try:
        # Create a temporary test file
        test_file = Path("/tmp/strands_test.txt")
        test_file.write_text("This is a test document for strands_agent_factory validation.\nIt contains multiple lines of test content.")
        
        config = AgentFactoryConfig(
            model="litellm:gemini/gemini-2.5-flash",
            system_prompt="You are a test assistant that can analyze uploaded files.",
            file_paths=[
                (str(test_file), "text/plain")
            ]
        )
        print("✓ Created EngineConfig with file upload")
        
        factory = AgentFactory(config)
        success = await factory.initialize()
        
        if success:
            print("✓ Factory with file upload initialized")
            
            agent = factory.create_agent()
            if agent:
                print("✓ Agent with file upload created")
                
                # Test file analysis
                print("📄 Testing file analysis...")
                success = await agent.send_message_to_agent(
                    "What files do you have access to? Please briefly describe their content.",
                    show_user_input=False
                )
                
                if success:
                    print("✓ File analysis completed successfully")
                    
                    # Cleanup
                    test_file.unlink(missing_ok=True)
                    return True
                else:
                    print("✗ File analysis failed")
                    test_file.unlink(missing_ok=True)
                    return False
            else:
                print("✗ Agent creation failed with file upload")
                test_file.unlink(missing_ok=True)
                return False
        else:
            print("✗ Factory initialization failed with file upload")
            test_file.unlink(missing_ok=True)
            return False
            
    except Exception as e:
        print(f"✗ File processing test failed: {e}")
        # Cleanup on error
        test_file = Path("/tmp/strands_test.txt")
        test_file.unlink(missing_ok=True)
        return False

def check_environment():
    """Check that required environment variables are set."""
    print("\n=== Checking Environment ===")
    
    # Check for various possible credential environment variables
    gemini_creds = [
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY", 
        "VERTEX_PROJECT_ID"
    ]
    
    found_creds = []
    for cred in gemini_creds:
        if os.getenv(cred):
            found_creds.append(cred)
            print(f"✓ Found credential: {cred}")
    
    if found_creds:
        print(f"✓ Environment check passed - found {len(found_creds)} credential(s)")
        return True
    else:
        print("⚠ No Gemini credentials found in environment variables")
        print("  Expected one of: GOOGLE_API_KEY, GEMINI_API_KEY, VERTEX_PROJECT_ID")
        return False

async def main():
    """Run all enhanced sniff tests with real credentials."""
    print("🚀 Starting enhanced strands_agent_factory sniff test with Gemini...")
    print("This test verifies complete functionality including real model interaction.")
    
    # Check environment first
    env_ok = check_environment()
    
    tests = [
        ("Real Credentials Test", test_with_real_credentials),
        ("Complex Configuration Test", test_complex_configuration_with_gemini),
        ("File Processing Test", test_file_processing_with_gemini),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print('='*60)
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("ENHANCED SNIFF TEST RESULTS")
    print('='*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nSummary: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All enhanced tests passed! strands_agent_factory is fully functional with Gemini!")
        print("✨ The factory pattern successfully creates working agents that can interact with LLMs.")
        return 0
    elif passed > 0:
        print(f"\n⚠ Partial success: {passed}/{len(results)} tests passed.")
        if not env_ok:
            print("Some failures may be due to missing or incorrect API credentials.")
        return 0
    else:
        print("\n❌ All tests failed.")
        if not env_ok:
            print("This is likely due to missing API credentials.")
        else:
            print("There may be issues with the strands_agent_factory implementation.")
        return 1

if __name__ == "__main__":
    """
    Entry point for the enhanced sniff test.
    
    This test requires valid Gemini API credentials and tests complete functionality:
    python test_sniff_with_credentials.py
    """
    exit_code = asyncio.run(main())
    sys.exit(exit_code)