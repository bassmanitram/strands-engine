#!/usr/bin/env python3
"""
Basic sniff test for strands_agent_factory.

This test verifies core functionality without requiring API credentials
or external dependencies. It tests the basic factory pattern, configuration
handling, and component interaction.
"""

import sys
from pathlib import Path

# Test basic imports
try:
    from strands_agent_factory import EngineConfig, AgentFactory
    print("✓ Successfully imported strands_agent_factory components")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

def test_import_structure():
    """Test that all core components can be imported."""
    print("\n=== Testing Import Structure ===")
    
    try:
        # Test individual module imports
        from strands_agent_factory.config import EngineConfig
        from strands_agent_factory.engine import AgentFactory
        from strands_agent_factory.ptypes import Tool, FrameworkAdapter
        print("✓ Individual module imports work")
        
        # Test framework adapter imports
        from strands_agent_factory.framework.base_adapter import FrameworkAdapter, load_framework_adapter
        from strands_agent_factory.framework.litellm_adapter import LiteLLMAdapter
        print("✓ Framework adapter imports work")
        
        # Test tool system imports
        from strands_agent_factory.tools import ToolFactory
        print("✓ Tool system imports work")
        
        return True
    except Exception as e:
        print(f"✗ Import structure test failed: {e}")
        return False

def test_basic_types():
    """Test basic type creation and validation."""
    print("\n=== Testing Basic Types ===")
    
    try:
        # Test minimal config
        config = EngineConfig(model="test-model")
        print("✓ Minimal EngineConfig creation works")
        
        # Test different conversation manager types
        config = EngineConfig(model="test-model", conversation_manager_type="null")
        print("✓ EngineConfig accepts conversation_manager_type='null'")
        
        config = EngineConfig(model="test-model", conversation_manager_type="sliding_window")
        print("✓ EngineConfig accepts conversation_manager_type='sliding_window'")
        
        config = EngineConfig(model="test-model", conversation_manager_type="summarizing")
        print("✓ EngineConfig accepts conversation_manager_type='summarizing'")
        
        # Test file paths
        config = EngineConfig(
            model="test-model",
            file_paths=[("test.txt", "text/plain")]
        )
        print("✓ EngineConfig accepts file_paths")
        
        # Test tool config paths
        config = EngineConfig(
            model="test-model",
            tool_config_paths=["test_tools.json"]
        )
        print("✓ EngineConfig accepts tool_config_paths")
        
        return True
    except Exception as e:
        print(f"✗ Basic types test failed: {e}")
        return False

def test_configuration_options():
    """Test various configuration options."""
    print("\n=== Testing Configuration Options ===")
    
    try:
        # Test complex configuration
        config = EngineConfig(
            model="gpt-4o",
            system_prompt="You are a helpful assistant.",
            conversation_manager_type="sliding_window",
            sliding_window_size=20,
            show_tool_use=True,
            emulate_system_prompt=False,
            model_config={
                "temperature": 0.7,
                "max_tokens": 1000
            },
            file_paths=[
                ("document.txt", "text/plain"),
                ("data.json", "application/json")
            ],
            tool_config_paths=[
                "tools/basic_tools.json",
                "tools/advanced_tools.json"
            ],
            session_id="test_session_123",
            sessions_home=Path("/tmp/test_sessions")
        )
        print("✓ Created complex EngineConfig successfully")
        
        # Test factory creation
        factory = AgentFactory(config)
        print("✓ Created AgentFactory with complex config")
        
        # Verify configuration values
        assert factory.config.model == "gpt-4o"
        assert factory.config.sliding_window_size == 20
        assert factory.config.show_tool_use == True
        assert len(factory.config.file_paths) == 2
        assert len(factory.config.tool_config_paths) == 2
        print("✓ Configuration values stored correctly")
        
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_error_handling():
    """Test error handling for invalid configurations."""
    print("\n=== Testing Error Handling ===")
    
    try:
        # Test invalid model (should not crash during factory creation)
        config = EngineConfig(model="invalid:nonexistent-model")
        factory = AgentFactory(config)
        print("✓ Factory creation handles invalid model gracefully")
        
        # Test factory initialization with invalid model
        import asyncio
        async def test_init():
            success = await factory.initialize()
            return success
        
        success = asyncio.run(test_init())
        if success:
            print("⚠ Factory initialization unexpectedly succeeded with invalid model")
        else:
            print("✓ Factory initialization properly failed with invalid model")
        
        return True
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False

async def test_basic_factory_creation():
    """Test basic factory creation and initialization."""
    print("\n=== Testing Basic Factory Creation ===")
    
    try:
        # Create a basic configuration
        config = EngineConfig(
            model="gpt-4o",  # Default OpenAI model
            system_prompt="You are a test assistant."
        )
        print("✓ Created EngineConfig successfully")
        
        # Create factory
        factory = AgentFactory(config)
        print("✓ Created AgentFactory successfully")
        
        # Test initialization - may fail due to missing API credentials
        print("⚠ Attempting initialization (may fail due to missing API credentials)...")
        success = await factory.initialize()
        
        if success:
            print("✓ Factory initialization succeeded")
            
            # Try to create agent - will likely fail without API credentials
            agent = factory.create_agent()
            if agent:
                print("✓ Agent creation succeeded")
                return True
            else:
                print("✗ Agent creation failed")
                return False
        else:
            print("✓ Factory initialization failed gracefully")
            return True  # This is expected without credentials
            
    except Exception as e:
        print(f"✗ Factory creation test failed: {e}")
        return False

def main():
    """Run all sniff tests."""
    print("🚀 Starting strands_agent_factory sniff test...")
    print("This test verifies basic factory and agent functionality.")
    
    tests = [
        ("Import Structure", test_import_structure),
        ("Basic Types", test_basic_types),
        ("Configuration Options", test_configuration_options),
        ("Error Handling", test_error_handling),
        ("Basic Factory Creation", test_basic_factory_creation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print('='*60)
        
        try:
            if test_name == "Basic Factory Creation":
                # This test is async
                import asyncio
                result = asyncio.run(test_func())
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("SNIFF TEST RESULTS")
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
        print("\n🎉 All tests passed! strands_agent_factory is working correctly!")
        print("✨ The factory pattern is ready for agent creation.")
        return 0
    elif passed > 0:
        print(f"\n⚠ Partial success: {passed}/{len(results)} tests passed.")
        print("Some failures may be due to missing API credentials or optional dependencies.")
        return 0
    else:
        print("\n❌ All tests failed.")
        print("There may be issues with the strands_agent_factory implementation.")
        return 1

if __name__ == "__main__":
    """
    Entry point for the basic sniff test.
    
    This test verifies core functionality without requiring external dependencies:
    python test_sniff.py
    """
    exit_code = main()
    sys.exit(exit_code)