# Testing strands_agent_factory

This document describes the testing approach for strands_agent_factory and how to verify that the factory and agent interaction work correctly.

## Sniff Test

The `test_sniff.py` script provides a quick "sniff test" to verify that strands_agent_factory is functioning correctly. This test checks core functionality without requiring API credentials or external dependencies.

### Running the Sniff Test

```bash
python test_sniff.py
```

### What the Sniff Test Checks

1. **Import Structure**: Verifies all core components can be imported
2. **Basic Types**: Tests EngineConfig creation with various options
3. **Configuration Options**: Validates complex configuration handling
4. **Error Handling**: Ensures invalid configurations are handled gracefully
5. **Basic Factory Creation**: Tests factory initialization and agent creation

### Expected Results

The sniff test should show mostly passing results:

```
SNIFF TEST RESULTS
============================================================
✓ PASS   Import Structure
✓ PASS   Basic Types
✓ PASS   Configuration Options
✓ PASS   Error Handling
⚠ FAIL   Basic Factory Creation  # Expected without API credentials

Summary: 4 passed, 1 failed
```

The "Basic Factory Creation" test is expected to fail if you don't have API credentials configured. This is normal and indicates the system is working correctly - it successfully initializes the factory but cannot create agents without valid API access.

### Testing with API Credentials

To test complete functionality including agent creation, set up API credentials:

```bash
# For OpenAI (default)
export OPENAI_API_KEY="your-openai-api-key"

# For other providers, see strands-agents documentation
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_API_KEY="your-google-key"
```

Then run the sniff test again. With valid credentials, all tests should pass.

## Enhanced Testing with Credentials

### Full Integration Test

```bash
python test_sniff_with_credentials.py
```

This test uses real API credentials to verify complete end-to-end functionality:

1. **Real Credentials Test**: Complete agent creation and LLM interaction
2. **Complex Configuration Test**: Advanced features like conversation management
3. **File Processing Test**: File upload and processing capabilities

### Debug Testing

Use the debug script for comprehensive logging:

```bash
./run_sniff_debug.sh
```

This script provides:
- Environment validation
- Dependency checking
- Interactive test selection
- Comprehensive debug logging
- Detailed error reporting

## Integration Testing

For more comprehensive testing in your own projects:

### Basic Usage Example

```python
import asyncio
from strands_agent_factory import EngineConfig, AgentFactory

async def test_basic_usage():
    # Create configuration
    config = EngineConfig(
        model="gpt-4o",  # or "litellm:gemini/gemini-2.5-flash"
        system_prompt="You are a helpful assistant."
    )
    
    # Create and initialize factory
    factory = AgentFactory(config)
    success = await factory.initialize()
    
    if success:
        # Create agent
        agent = factory.create_agent()
        if agent:
            # Test basic interaction
            success = await agent.send_message_to_agent("Hello! Can you help me?")
            print(f"Message processed: {success}")
        else:
            print("Agent creation failed")
    else:
        print("Factory initialization failed")

# Run the test
asyncio.run(test_basic_usage())
```

### Testing with Tools

```python
import asyncio
from strands_agent_factory import EngineConfig, AgentFactory

async def test_with_tools():
    config = EngineConfig(
        model="gpt-4o",
        system_prompt="You are an assistant with access to tools.",
        tool_config_paths=["path/to/your/tools.json"]
    )
    
    factory = AgentFactory(config)
    success = await factory.initialize()
    
    if success:
        agent = factory.create_agent()
        if agent:
            # Test tool usage
            success = await agent.send_message_to_agent(
                "What tools do you have access to?"
            )
            print(f"Tool query processed: {success}")

asyncio.run(test_with_tools())
```

### Testing with File Uploads

```python
import asyncio
from strands_agent_factory import EngineConfig, AgentFactory

async def test_with_files():
    config = EngineConfig(
        model="gpt-4o",
        system_prompt="You are an assistant that can analyze uploaded files.",
        file_paths=[
            ("path/to/document.txt", "text/plain"),
            ("path/to/data.json", "application/json")
        ]
    )
    
    factory = AgentFactory(config)
    success = await factory.initialize()
    
    if success:
        agent = factory.create_agent()
        if agent:
            # Test file analysis
            success = await agent.send_message_to_agent(
                "What files do you have access to? Can you summarize them?"
            )
            print(f"File analysis processed: {success}")

asyncio.run(test_with_files())
```

### Testing Multi-Provider Support

```python
import asyncio
from strands_agent_factory import EngineConfig, AgentFactory

async def test_multi_provider():
    providers = [
        ("litellm:gpt-4o", "OpenAI via LiteLLM"),
        ("litellm:anthropic/claude-3-5-sonnet-20241022", "Anthropic via LiteLLM"),
        ("litellm:gemini/gemini-2.5-flash", "Google Gemini via LiteLLM"),
    ]
    
    for model_string, description in providers:
        print(f"Testing {description}...")
        
        config = EngineConfig(
            model=model_string,
            system_prompt=f"You are testing {description}."
        )
        
        factory = AgentFactory(config)
        success = await factory.initialize()
        
        if success:
            agent = factory.create_agent()
            if agent:
                success = await agent.send_message_to_agent(
                    "Please confirm you're working.", 
                    show_user_input=False
                )
                print(f"✓ {description}: {'Success' if success else 'Failed'}")
            else:
                print(f"✗ {description}: Agent creation failed")
        else:
            print(f"✗ {description}: Initialization failed")

asyncio.run(test_multi_provider())
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure strands-agents is installed and available
2. **API Credential Errors**: Set appropriate environment variables for your chosen provider
3. **Tool Loading Errors**: Check tool configuration file paths and formats
4. **File Upload Errors**: Verify file paths exist and are readable
5. **Model Loading Errors**: Check model string format and provider availability

### Debug Logging

Enable debug logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Your test code here
```

Or with loguru (used by strands_agent_factory):

```python
from loguru import logger
logger.remove()  # Remove default handler
logger.add(lambda msg: print(msg, end=""), level="DEBUG")
```

### Environment Variables for Testing

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Google (for Gemini via LiteLLM)
export GOOGLE_API_KEY="AI..."

# Azure OpenAI
export AZURE_OPENAI_API_KEY="..."
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"

# Enable debug logging
export LOGURU_LEVEL="DEBUG"
```

## Test Environment Setup

### Development Environment

```bash
# Install in development mode
pip install -e .

# Install development dependencies (if available)
pip install -e .[dev]

# Run tests
python test_sniff.py
python test_sniff_with_credentials.py
./run_sniff_debug.sh
```

### CI/CD Environment

```bash
# Basic functionality test (no credentials required)
python test_sniff.py

# Exit code indicates success/failure
echo $?  # 0 = success, 1 = failure
```

### Docker Testing

```dockerfile
FROM python:3.10-slim

COPY . /app
WORKDIR /app

RUN pip install strands-agents loguru
ENV PYTHONPATH=/app

# Test basic functionality
RUN python test_sniff.py

# Test with credentials (if provided)
ARG OPENAI_API_KEY
ENV OPENAI_API_KEY=$OPENAI_API_KEY
RUN if [ -n "$OPENAI_API_KEY" ]; then python test_sniff_with_credentials.py; fi
```

## Test Structure

### Test Categories

1. **Unit Tests**: Individual component testing
   - Configuration validation
   - Framework adapter loading
   - Tool discovery and loading
   - Message transformation

2. **Integration Tests**: Component interaction testing
   - Factory → Agent creation pipeline
   - Tool integration with agents
   - File processing pipeline
   - Session management

3. **End-to-End Tests**: Complete workflow testing
   - Real API interaction
   - Multi-turn conversations
   - Tool usage in context
   - File analysis workflows

### Test Data

Create test data for comprehensive testing:

```bash
mkdir -p test_data/
echo "This is a test document." > test_data/document.txt
echo '{"test": "data"}' > test_data/data.json

mkdir -p test_tools/
cat > test_tools/basic_tools.json << EOF
{
  "tools": [
    {
      "type": "python_function",
      "module": "builtins",
      "config": {
        "functions": ["len", "str"]
      }
    }
  ]
}
EOF
```

## Performance Testing

### Basic Performance Test

```python
import asyncio
import time
from strands_agent_factory import EngineConfig, AgentFactory

async def performance_test():
    config = EngineConfig(model="gpt-4o", system_prompt="You are a test assistant.")
    
    # Test factory creation time
    start = time.time()
    factory = AgentFactory(config)
    factory_time = time.time() - start
    
    # Test initialization time
    start = time.time()
    await factory.initialize()
    init_time = time.time() - start
    
    # Test agent creation time
    start = time.time()
    agent = factory.create_agent()
    agent_time = time.time() - start
    
    print(f"Factory creation: {factory_time:.3f}s")
    print(f"Initialization: {init_time:.3f}s")
    print(f"Agent creation: {agent_time:.3f}s")
    print(f"Total setup time: {factory_time + init_time + agent_time:.3f}s")

asyncio.run(performance_test())
```

This comprehensive testing approach ensures strands_agent_factory works correctly across different configurations, providers, and use cases.