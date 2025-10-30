# Architecture Documentation

This document provides detailed architectural information about strands-agent-factory's design patterns, internal structure, and technical implementation details.

## Modern Modular Structure

```
strands_agent_factory/
├── core/                    # Core functionality
│   ├── factory.py          # Main AgentFactory
│   ├── agent.py            # AgentProxy wrapper
│   ├── config.py           # Configuration classes
│   ├── types.py            # Type definitions
│   ├── exceptions.py       # Exception hierarchy
│   └── utils.py            # Utility functions
├── adapters/               # Framework adapters
│   ├── base.py            # Base adapter interface
│   ├── generic.py         # Generic adapter (automatic support)
│   ├── litellm.py         # LiteLLM integration
│   ├── ollama.py          # Local models
│   └── bedrock.py         # AWS Bedrock
├── tools/                  # Tool management
│   ├── factory.py         # Tool loading & configuration
│   ├── python.py          # Python function utilities
│   ├── mcp.py             # MCP server integration
│   └── a2a.py             # Agent-to-Agent communication
├── messaging/              # Message processing
│   ├── generator.py       # Message generation with file()
│   └── content.py         # File content processing
├── session/                # Session management
│   ├── manager.py         # Session persistence
│   └── conversation.py    # Conversation strategies
├── handlers/               # Event handlers
│   └── callback.py        # Output handling
└── scripts/                # Command-line tools
    ├── chatbot.py         # Interactive chatbot
    └── a2a_server.py      # A2A server wrapper
```

## Factory Pattern Benefits

- **Separation of Concerns**: Configuration, initialization, and usage are cleanly separated
- **Resource Management**: Automatic cleanup of MCP servers and sessions
- **Framework Abstraction**: Unified interface across different AI providers
- **Extensibility**: Plugin architecture for custom adapters and tools

## Core Components

### AgentFactory

The central orchestrator that:
- Loads and validates configuration
- Initializes framework adapters
- Sets up tool systems (Python, MCP, A2A)
- Manages session persistence
- Creates AgentProxy instances

### AgentProxy

A wrapper around strands-agents Agent that:
- Manages agent lifecycle (context manager)
- Handles MCP server cleanup
- Provides consistent interface
- Supports both interactive and programmatic usage

### Framework Adapters

Pluggable adapters that handle framework-specific concerns:
- **Generic Adapter**: Automatic support for standard strands-agents patterns
- **Specialized Adapters**: Custom handling for LiteLLM, Bedrock, Ollama
- **Extensible**: Easy to add new framework support

### Tool System

Multi-type tool loading and management:
- **Python Tools**: Direct function imports from modules
- **MCP Tools**: Model Context Protocol server integration
- **A2A Tools**: Agent-to-Agent communication capabilities
- **Schema Adaptation**: Automatic tool schema cleaning for different providers

## Design Principles

### 1. Configuration-Driven

All behavior is controlled through declarative configuration:
```python
config = AgentFactoryConfig(
    model="gpt-4o",
    tool_config_paths=["tools/math.json"],
    conversation_manager_type="sliding_window"
)
```

### 2. Fail-Fast Validation

Configuration and dependencies are validated early:
- Model availability checking
- Tool configuration validation
- Framework adapter selection
- Dependency availability verification

### 3. Resource Lifecycle Management

Proper resource cleanup through context managers:
```python
with agent_proxy as agent:
    # MCP servers started automatically
    await agent.send_message("Hello")
    # MCP servers cleaned up automatically
```

### 4. Plugin Architecture

Easy extensibility through well-defined interfaces:
- Framework adapters implement `FrameworkAdapter`
- Tool types implement tool creation patterns
- Conversation managers implement strategy patterns

### 5. Error Boundary Isolation

Each component has clear error boundaries:
- Tool loading failures don't crash the system
- Framework adapter errors are contained
- MCP server failures are handled gracefully

## Data Flow

### Agent Creation Flow

```
Configuration → Factory → Adapter Selection → Tool Loading → Agent Creation
     ↓              ↓           ↓               ↓              ↓
AgentFactoryConfig → Framework → Tools → SessionManager → AgentProxy
```

### Message Processing Flow

```
User Message → File Processing → Tool Execution → Model Interaction → Response
     ↓              ↓               ↓               ↓               ↓
  file() refs → Content Blocks → Tool Calls → LLM Request → Formatted Output
```

### Tool Integration Flow

```
Tool Config → Tool Factory → Tool Loading → Schema Adaptation → Agent Integration
     ↓             ↓             ↓              ↓                 ↓
   JSON/YAML → Type Detection → Import/Start → Framework Compat → Tool Registration
```

## Threading and Concurrency

### Async/Await Pattern

All I/O operations use async/await:
- Model requests are async
- File processing is async
- MCP communication is async
- Tool execution respects async patterns

### Thread Safety

- Configuration is immutable after creation
- Tool factories are thread-safe
- MCP servers use proper async coordination
- Session managers handle concurrent access

### Resource Pools

- Framework adapters manage connection pools
- MCP servers reuse connections where possible
- File processing uses bounded memory

## Error Handling Strategy

### Exception Hierarchy

```
StrandsAgentFactoryError (base)
├── ConfigurationError
├── InitializationError
├── ModelLoadError
├── ToolLoadError
└── SessionError
```

### Graceful Degradation

- Individual tool failures don't stop agent creation
- MCP server failures are logged but handled
- Framework adapter fallbacks to generic adapter
- Session failures fall back to stateless operation

### Recovery Mechanisms

- Automatic retry for transient failures
- Tool reload capabilities
- MCP server restart handling
- Configuration reload support

## Performance Considerations

### Memory Management

- Conversation managers prevent memory bloat
- File processing has size limits
- Tool results can be truncated
- Session storage is configurable

### Caching Strategy

- Framework adapters cache models
- Tool schemas are cached after loading
- File content blocks are cached per session
- Configuration parsing is memoized

### Optimization Points

- Lazy loading of heavy dependencies
- Batch processing of file uploads
- Connection pooling for external services
- Efficient tool schema adaptation

## Security Model

### Input Validation

- All configuration is validated against schemas
- File uploads are size-limited and type-checked
- Tool parameters are validated
- User input is sanitized

### Sandboxing

- Python tools run in controlled environments
- MCP servers are isolated processes
- File access is restricted to configured paths
- Network access is controlled per tool type

### Credential Management

- API keys are handled through environment variables
- MCP server authentication is configurable
- A2A communication supports token-based auth
- Session data is stored securely

## Extension Points

### Custom Framework Adapters

```python
class MyFrameworkAdapter(FrameworkAdapter):
    @property
    def framework_name(self) -> str:
        return "myframework"
    
    def load_model(self, model_name, model_config):
        return MyFrameworkModel(model_name, **model_config or {})
```

### Custom Tool Types

```python
def create_custom_tool_spec(config: Dict[str, Any]) -> Dict[str, Any]:
    # Load tools from custom source
    tools = load_custom_tools(config)
    return {"tools": tools, "client": None}
```

### Custom Conversation Managers

```python
class MyConversationManager(ConversationManager):
    def manage_conversation(self, messages: List[Message]) -> List[Message]:
        # Custom conversation management logic
        return processed_messages
```

## Testing Strategy

### Unit Testing

- Each component is tested in isolation
- Mock dependencies for external services
- Property-based testing for configuration validation
- Async testing patterns for I/O operations

### Integration Testing

- End-to-end agent creation workflows
- Tool integration testing
- Framework adapter compatibility testing
- Session persistence testing

### Performance Testing

- Memory usage profiling
- Response time benchmarking
- Concurrent usage testing
- Resource cleanup verification

## Deployment Patterns

### Single Agent Deployment

```python
factory = AgentFactory(config)
await factory.initialize()
agent = factory.create_agent()
```

### Multi-Agent Systems

```bash
# Agent 1: Data processing
strands-a2a-server data_agent.yaml --port 8001

# Agent 2: HR functions  
strands-a2a-server hr_agent.yaml --port 8002
```

### Containerized Deployment

```dockerfile
FROM python:3.11-slim
RUN pip install "strands-agent-factory[full]"
COPY config.yaml /app/
CMD ["strands-a2a-server", "/app/config.yaml", "--host", "0.0.0.0"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-deployment
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: agent
        image: my-agent:latest
        command: ["strands-a2a-server", "config.yaml", "--host", "0.0.0.0"]
```

## Monitoring and Observability

### Logging Strategy

- Structured logging with loguru
- Configurable log levels
- Component-specific loggers
- Performance metrics logging

### Health Checks

- Agent readiness probes
- Tool availability monitoring
- MCP server health checks
- Session storage health

### Metrics Collection

- Request/response latencies
- Tool execution times
- Memory usage patterns
- Error rates by component

This architecture provides a solid foundation for building production-ready AI agent systems with proper separation of concerns, extensibility, and operational reliability.