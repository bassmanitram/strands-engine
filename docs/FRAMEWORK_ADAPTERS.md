# Framework Adapters

This document details the framework adapter system that enables strands-agent-factory to work with any AI provider while providing specialized handling for specific frameworks.

## Overview

Framework adapters provide a pluggable system for integrating different AI providers and frameworks. The system includes both automatic generic support and specialized adapters for frameworks requiring custom handling.

## Automatic Generic Adapter

The factory includes a powerful generic adapter that automatically supports any framework following standard strands-agents patterns:

```python
# These work automatically without custom adapters:
config = AgentFactoryConfig(model="gemini:gemini-2.5-flash")      # Google Gemini
config = AgentFactoryConfig(model="mistral:mistral-large")        # Mistral  
config = AgentFactoryConfig(model="cohere:command-r-plus")        # Cohere
config = AgentFactoryConfig(model="openai:gpt-4o")               # OpenAI
config = AgentFactoryConfig(model="anthropic:claude-3-5-sonnet") # Anthropic
```

### Generic Adapter Features

- **Automatic Detection**: Uses strands-agents' built-in framework detection
- **Standard Tool Support**: Works with any framework that supports standard tool schemas
- **Zero Configuration**: No adapter-specific configuration required
- **Fallback Safety**: Used as fallback when specialized adapters aren't available

## Specialized Adapters

For frameworks requiring special handling:

| Framework | Adapter | Special Features |
|-----------|---------|------------------|
| **LiteLLM** | `LiteLLMAdapter` | Tool schema cleaning, 100+ provider support |
| **AWS Bedrock** | `BedrockAdapter` | BotocoreConfig handling, content adaptation |
| **Ollama** | `OllamaAdapter` | Host configuration, local model support |

### LiteLLM Adapter

Handles LiteLLM's specific requirements:

```python
class LiteLLMAdapter(FrameworkAdapter):
    @property
    def framework_name(self) -> str:
        return "litellm"
    
    def adapt_tools(self, tools, model_string):
        # Clean tool schemas for LiteLLM compatibility
        cleaned_tools = []
        for tool in tools:
            # Remove 'title' fields that cause issues
            recursively_remove(tool, 'title')
            cleaned_tools.append(tool)
        return cleaned_tools
```

**Key Features:**
- Removes problematic `title` fields from tool schemas
- Supports 100+ providers through LiteLLM
- Handles provider-specific model naming conventions
- Automatic tool schema cleaning

### AWS Bedrock Adapter

Specialized for AWS Bedrock deployment:

```python
class BedrockAdapter(FrameworkAdapter):
    @property  
    def framework_name(self) -> str:
        return "bedrock"
    
    def load_model(self, model_name, model_config):
        # Handle BotocoreConfig and AWS-specific settings
        return load_bedrock_model(model_name, model_config)
```

**Key Features:**
- BotocoreConfig integration
- AWS credential handling
- Region-specific model loading
- Content format adaptation for Bedrock APIs

### Ollama Adapter

Optimized for local Ollama deployments:

```python
class OllamaAdapter(FrameworkAdapter):
    @property
    def framework_name(self) -> str:
        return "ollama"
    
    def load_model(self, model_name, model_config):
        # Handle local host configuration
        return load_ollama_model(model_name, model_config)
```

**Key Features:**
- Local host and port configuration
- Model availability checking
- Efficient local model loading
- Custom Ollama-specific parameters

## Creating Custom Adapters

Extend support to new AI providers by implementing the `FrameworkAdapter` interface:

```python
from strands_agent_factory.adapters.base import FrameworkAdapter

class MyProviderAdapter(FrameworkAdapter):
    @property
    def framework_name(self) -> str:
        return "myprovider"
    
    def load_model(self, model_name, model_config):
        """Load model with provider-specific logic."""
        # Custom model loading logic
        return MyProviderModel(model_name, **model_config or {})
    
    def adapt_tools(self, tools, model_string):
        """Adapt tool schemas for provider compatibility."""
        adapted_tools = []
        for tool in tools:
            # Provider-specific tool schema adaptation
            adapted_tool = self._adapt_tool_schema(tool)
            adapted_tools.append(adapted_tool)
        return adapted_tools
    
    def _adapt_tool_schema(self, tool):
        """Provider-specific tool schema transformation."""
        # Example: Convert schema format
        if 'parameters' in tool:
            tool['arguments'] = tool.pop('parameters')
        return tool
```

### FrameworkAdapter Interface

```python
class FrameworkAdapter(ABC):
    @property
    @abstractmethod
    def framework_name(self) -> str:
        """Return the framework identifier."""
        pass
    
    def load_model(self, model_name: str, model_config: Optional[Dict[str, Any]]):
        """Load model with framework-specific configuration."""
        # Default implementation uses strands-agents auto-detection
        return load_agent_model(model_name, model_config)
    
    def adapt_tools(self, tools: List[Any], model_string: str) -> List[Any]:
        """Adapt tools for framework compatibility."""
        # Default implementation returns tools unchanged
        return tools
    
    def get_model_config_schema(self) -> Optional[Dict[str, Any]]:
        """Return JSON schema for framework-specific model config."""
        return None
```

## Adapter Registration

Adapters are automatically discovered and registered:

```python
# In strands_agent_factory/adapters/__init__.py
from .litellm import LiteLLMAdapter
from .bedrock import BedrockAdapter  
from .ollama import OllamaAdapter

FRAMEWORK_ADAPTERS = {
    "litellm": LiteLLMAdapter(),
    "bedrock": BedrockAdapter(),
    "ollama": OllamaAdapter(),
}
```

## Adapter Selection Logic

The factory uses this logic to select adapters:

```python
def get_framework_adapter(model_string: str) -> FrameworkAdapter:
    # Extract framework from model string
    framework = extract_framework_name(model_string)
    
    # Check for specialized adapter
    if framework in FRAMEWORK_ADAPTERS:
        return FRAMEWORK_ADAPTERS[framework]
    
    # Fall back to generic adapter
    return GenericAdapter()
```

### Model String Parsing

The factory intelligently handles various model identifier formats:

```python
# Direct provider names (uses generic adapter)
"gpt-4o"                    # → OpenAI GPT-4
"claude-3-5-sonnet"         # → Anthropic Claude  
"gemini-2.5-flash"          # → Google Gemini

# Explicit framework prefixes
"anthropic:claude-3-5-sonnet-20241022"     # → Anthropic Claude
"ollama:llama3.1:8b"                       # → Ollama Llama
"bedrock:anthropic.claude-3-sonnet"        # → AWS Bedrock

# LiteLLM for 100+ providers
"litellm:gemini/gemini-2.5-flash"          # → Google Gemini
"litellm:azure/gpt-4o"                     # → Azure OpenAI
"litellm:openrouter/anthropic/claude-3.5"  # → OpenRouter
"litellm:cohere/command-r-plus"            # → Cohere
```

## Tool Schema Adaptation

Different providers have varying tool schema requirements:

### Common Adaptations

1. **Field Removal**: Remove problematic fields
```python
def clean_schema(schema):
    recursively_remove(schema, 'title')    # LiteLLM
    recursively_remove(schema, 'examples') # Some providers
```

2. **Field Mapping**: Rename fields for compatibility
```python
def adapt_parameters(tool):
    if 'parameters' in tool:
        tool['arguments'] = tool.pop('parameters')
```

3. **Format Conversion**: Convert between schema formats
```python
def convert_to_provider_format(tool):
    # Convert OpenAI format to provider-specific format
    return transformed_tool
```

### Provider-Specific Requirements

- **OpenAI**: Standard function calling format
- **Anthropic**: Claude-specific tool format  
- **LiteLLM**: Cleaned schemas without certain fields
- **Bedrock**: AWS-specific content blocks
- **Local Models**: Simplified schemas for better performance

## Configuration Validation

Adapters can provide configuration schemas:

```python
class MyProviderAdapter(FrameworkAdapter):
    def get_model_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "api_key": {"type": "string"},
                "endpoint": {"type": "string", "format": "uri"},
                "timeout": {"type": "number", "minimum": 1}
            },
            "required": ["api_key"]
        }
```

## Error Handling

Adapters handle provider-specific errors:

```python
class MyProviderAdapter(FrameworkAdapter):
    def load_model(self, model_name, model_config):
        try:
            return super().load_model(model_name, model_config)
        except ProviderSpecificError as e:
            raise ModelLoadError(f"Failed to load {model_name}: {e}")
```

## Testing Framework Adapters

### Unit Testing

```python
def test_adapter_tool_adaptation():
    adapter = LiteLLMAdapter()
    tools = [{"name": "test", "title": "Test Tool"}]
    
    adapted = adapter.adapt_tools(tools, "litellm:gpt-4")
    
    assert "title" not in adapted[0]
    assert adapted[0]["name"] == "test"
```

### Integration Testing

```python
async def test_adapter_integration():
    config = AgentFactoryConfig(model="litellm:gpt-4o")
    factory = AgentFactory(config)
    
    await factory.initialize()
    agent = factory.create_agent()
    
    assert isinstance(factory._framework_adapter, LiteLLMAdapter)
```

## Performance Considerations

### Lazy Loading

Adapters are loaded only when needed:

```python
def get_adapter(framework_name):
    if framework_name not in _loaded_adapters:
        _loaded_adapters[framework_name] = load_adapter(framework_name)
    return _loaded_adapters[framework_name]
```

### Caching

Model instances and configurations are cached:

```python
class FrameworkAdapter:
    def __init__(self):
        self._model_cache = {}
    
    def load_model(self, model_name, model_config):
        cache_key = (model_name, hash(frozenset(model_config.items())))
        if cache_key not in self._model_cache:
            self._model_cache[cache_key] = self._create_model(model_name, model_config)
        return self._model_cache[cache_key]
```

## Best Practices

### Adapter Development

1. **Minimal Interface**: Only override methods that need customization
2. **Error Handling**: Provide clear error messages for adapter-specific issues
3. **Documentation**: Document any special requirements or limitations
4. **Testing**: Include both unit and integration tests
5. **Performance**: Cache expensive operations

### Configuration

1. **Explicit Prefixes**: Use framework prefixes for clarity
2. **Validation**: Validate adapter-specific configuration early
3. **Fallbacks**: Ensure graceful fallback to generic adapter
4. **Documentation**: Document framework-specific options

This adapter system provides a flexible foundation for supporting any AI provider while maintaining clean separation of concerns and optimal performance for each framework.