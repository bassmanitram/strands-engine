# A2A (Agent-to-Agent) Architecture

This document provides detailed architectural information about the A2A (Agent-to-Agent) system in strands-agent-factory, covering both client-side tool integration and server-side agent exposure.

## Architecture Overview

The A2A system enables agents to communicate with each other using natural language, creating sophisticated multi-agent workflows. The architecture consists of two main components:

1. **A2A Client Tools**: Allow agents to discover and communicate with other agents
2. **A2A Server Wrapper**: Exposes agents as HTTP endpoints for other agents to consume

```
┌─────────────────┐    A2A Protocol    ┌─────────────────┐
│   Agent A       │◄──────────────────►│   Agent B       │
│ (with A2A tools)│                    │ (A2A Server)    │
│                 │                    │                 │
│ • discover      │                    │ • Python tools  │
│ • list_agents   │                    │ • MCP servers   │
│ • send_message  │                    │ • A2A clients   │
└─────────────────┘                    └─────────────────┘
```

## A2A Client Architecture

### Tool Integration

A2A client tools are integrated through the standard tool configuration system:

```json
{
  "id": "company_agents",
  "type": "a2a",
  "urls": [
    "http://data-agent:8001/",
    "http://hr-agent:8002/"
  ],
  "timeout": 300,
  "webhook_url": "https://app.com/webhook",
  "webhook_token": "secret-token"
}
```

### A2A Tool Provider

The `A2AClientToolProvider` wraps the underlying A2A client functionality:

```python
class A2AClientToolProvider:
    def __init__(self, provider_id: str, known_agent_urls: List[str], 
                 timeout: int = 300, webhook_url: Optional[str] = None,
                 webhook_token: Optional[str] = None):
        self.provider_id = provider_id
        self.known_agent_urls = known_agent_urls
        # Initialize underlying A2A client
        
    @property
    def tools(self) -> List[Any]:
        """Return the three A2A tools as a cohesive set."""
        return [
            self._create_discover_tool(),
            self._create_list_agents_tool(), 
            self._create_send_message_tool()
        ]
```

### Tool Set Design

A2A tools work as a cohesive set of three tools:

1. **`a2a_discover_agent`**: Discover new agents and their capabilities
2. **`a2a_list_discovered_agents`**: List all known agents  
3. **`a2a_send_message`**: Send natural language messages to agents

**Important**: These tools are not individually filterable - they work together as a complete communication system.

### Communication Flow

```
Agent A wants to ask Agent B a question:

1. Agent A calls a2a_list_discovered_agents()
   └─► Returns list of known agents

2. If Agent B not found:
   Agent A calls a2a_discover_agent("http://agent-b:8002/")
   └─► Discovers Agent B's capabilities

3. Agent A calls a2a_send_message("agent-b", "What are your capabilities?")
   └─► Sends natural language message
   └─► Returns Agent B's response
```

## A2A Server Architecture

### Server Wrapper

The A2A server wrapper exposes any strands-agent-factory agent as an HTTP endpoint:

```python
# Agent Config → AgentFactory → Agent → A2AServer → HTTP Endpoint
config = AgentFactoryConfig(model="gpt-4o", tool_config_paths=["tools/"])
factory = AgentFactory(config)
agent = factory.create_agent()

# Wrap as A2A server
a2a_server = A2AServer(agent, host="0.0.0.0", port=8001)
a2a_server.serve()
```

### Tool Exposure

When an agent is wrapped as an A2A server, its tools become available to other agents indirectly:

```
Agent Tools → Agent Capabilities → A2A Server → Other Agents
     ↓              ↓                  ↓           ↓
Python funcs   Tool usage        HTTP API    Natural language
MCP servers    Skill execution   Endpoints   Communication
A2A clients    Task completion   Discovery   Workflow requests
```

### Resource Management

The A2A server wrapper properly manages agent resources:

```python
with agent_proxy as agent:  # MCP servers started
    a2a_server = A2AServer(agent, ...)
    a2a_server.serve()  # Server runs
    # MCP servers automatically cleaned up on exit
```

## Multi-Agent Workflows

### Workflow Patterns

1. **Request-Response**: Simple synchronous communication
2. **Delegation**: Route requests to appropriate specialist agents  
3. **Aggregation**: Combine results from multiple agents
4. **Chain of Responsibility**: Pass requests through agent hierarchy

### Example: HR Report Generation

```
User: "Generate salary report for data scientists"
   ↓
HR Agent receives request
   ↓
HR Agent → Employee Agent: "List employees with 'Data Scientist' titles"
   ↓
HR Agent → Payroll Agent: "Get salary data for IDs [1,2,3,4,5]"
   ↓  
HR Agent → Data Agent: "Create salary distribution chart"
   ↓
HR Agent → User: "Here's your comprehensive report with visualization"
```

### Agent Specialization

Each agent can be specialized for specific domains:

- **Data Agent**: Mathematical computation, data analysis, visualization
- **HR Agent**: Employee lookup, policy queries, coordination
- **Payroll Agent**: Salary data, benefits information
- **Facilities Agent**: Office management, resource booking

## Communication Protocol

### Message Format

A2A communication uses natural language messages:

```python
# Instead of structured API calls:
get_employee_data(employee_id=123, fields=["name", "salary"])

# A2A uses natural language:
a2a_send_message("hr-agent", "What is the salary for employee ID 123?")
```

### Discovery Protocol

Agents can dynamically discover other agents:

```python
# Discover agent capabilities
capabilities = a2a_discover_agent("http://new-agent:8003/")
# Returns: {"skills": ["data_analysis", "reporting"], "version": "1.0.0"}

# List all known agents
agents = a2a_list_discovered_agents()
# Returns: [{"id": "hr-agent", "url": "http://hr:8001/", "skills": [...]}]
```

### Error Handling

A2A communication includes robust error handling:

- **Connection failures**: Automatic retry with backoff
- **Timeout handling**: Configurable timeouts per agent
- **Graceful degradation**: Continue with available agents
- **Error propagation**: Clear error messages to requesting agent

## Deployment Patterns

### Single Host Development

```bash
# Terminal 1: Start data agent
strands-a2a-server data_agent.yaml --port 8001

# Terminal 2: Start hr agent (connects to data agent)  
strands-a2a-server hr_agent.yaml --port 8002

# Terminal 3: Interactive session with hr agent
strands-chatbot hr_client_config.yaml
```

### Container Orchestration

```yaml
# docker-compose.yml
version: '3.8'
services:
  data-agent:
    image: my-company/data-agent
    ports: ["8001:8000"]
    
  hr-agent:
    image: my-company/hr-agent  
    ports: ["8002:8000"]
    depends_on: [data-agent]
    environment:
      - DATA_AGENT_URL=http://data-agent:8000/
```

### Kubernetes Deployment

```yaml
apiVersion: v1
kind: Service
metadata:
  name: data-agent-service
spec:
  selector:
    app: data-agent
  ports:
  - port: 8000
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hr-agent
spec:
  template:
    spec:
      containers:
      - name: hr-agent
        env:
        - name: DATA_AGENT_URL
          value: "http://data-agent-service:8000/"
```

## Security Architecture

### Authentication

A2A communication supports token-based authentication:

```json
{
  "id": "secure_agents",
  "type": "a2a", 
  "urls": ["https://secure-agent.company.com/"],
  "webhook_token": "secure-webhook-token"
}
```

### Network Security

- **TLS Encryption**: HTTPS for production deployments  
- **Network Segmentation**: Isolate agent networks
- **Service Mesh**: Use Istio/Linkerd for advanced security
- **Access Control**: Limit which agents can communicate

### Input Validation  

- **Message Sanitization**: Clean natural language inputs
- **Rate Limiting**: Prevent abuse of A2A endpoints
- **Content Filtering**: Block inappropriate requests
- **Audit Logging**: Track all inter-agent communications

## Performance Considerations

### Connection Management

- **Connection Pooling**: Reuse HTTP connections between agents
- **Keep-Alive**: Maintain persistent connections for frequent communication
- **Circuit Breakers**: Handle agent failures gracefully
- **Load Balancing**: Distribute requests across agent instances

### Caching Strategy

- **Agent Discovery**: Cache agent capabilities and metadata
- **Response Caching**: Cache responses for idempotent requests  
- **Connection Metadata**: Cache connection health and latency
- **Skill Information**: Cache agent skill descriptions

### Scalability Patterns

- **Horizontal Scaling**: Deploy multiple instances of each agent
- **Load Balancing**: Use load balancers for high availability
- **Service Discovery**: Dynamic agent registration and discovery
- **Circuit Breakers**: Isolate failures and prevent cascading issues

## Monitoring and Observability

### Metrics Collection

- **Request Latency**: Track inter-agent communication times
- **Success Rates**: Monitor successful vs failed requests
- **Agent Availability**: Track agent uptime and health
- **Message Volume**: Monitor communication patterns

### Distributed Tracing

```python
# Trace requests across agent boundaries
@trace_span("a2a_request")
async def send_message(agent_id: str, message: str):
    # Tracing automatically propagates across A2A calls
    return await self.client.send_message(agent_id, message)
```

### Health Checks

Each A2A server exposes health endpoints:

```bash
# Check agent health
curl http://agent:8001/health

# Get agent capabilities  
curl http://agent:8001/capabilities
```

### Logging Strategy

- **Structured Logging**: JSON logs for easy parsing
- **Correlation IDs**: Track requests across agent boundaries
- **Performance Logs**: Log timing and performance metrics
- **Error Tracking**: Detailed error logging with context

## Testing Strategy

### Unit Testing

```python
@patch('strands_agent_factory.tools.a2a.A2AClientToolProvider')
def test_a2a_tool_creation(mock_provider):
    config = {"id": "test", "type": "a2a", "urls": ["http://test/"]}
    factory = ToolFactory([])
    result = factory.create_tool_from_config(config)
    
    assert 'tools' in result
    assert len(result['tools']) == 3  # discover, list, send_message
```

### Integration Testing

```python
async def test_multi_agent_workflow():
    # Start test agents
    data_agent = await start_test_agent("data_agent.yaml", port=8001)
    hr_agent = await start_test_agent("hr_agent.yaml", port=8002)
    
    # Test communication
    response = await hr_agent.send_message("Generate report")
    assert "data visualization" in response
```

### End-to-End Testing

```bash
# Start test environment
docker-compose -f test-compose.yml up -d

# Run E2E tests
pytest tests/e2e/test_multi_agent_workflows.py
```

## Error Recovery and Resilience

### Failure Modes

1. **Agent Unavailable**: Target agent is down or unreachable
2. **Network Partition**: Network connectivity issues between agents
3. **Timeout**: Agent takes too long to respond
4. **Resource Exhaustion**: Agent overloaded or out of resources

### Recovery Strategies

1. **Retry Logic**: Exponential backoff for transient failures
2. **Circuit Breakers**: Stop calling failed agents temporarily  
3. **Fallback Agents**: Route to backup agents when primary fails
4. **Graceful Degradation**: Continue with reduced functionality

### Monitoring and Alerting

- **Agent Health Dashboards**: Real-time agent status monitoring
- **Communication Metrics**: Track success rates and latencies
- **Error Rate Alerts**: Alert on increased failure rates
- **Capacity Monitoring**: Track resource usage and scaling needs

## Best Practices

### Agent Design

1. **Single Responsibility**: Each agent should have a focused purpose
2. **Clear Interfaces**: Well-defined capabilities and skills
3. **Stateless Design**: Minimize shared state between agents
4. **Error Handling**: Robust error handling and recovery

### Communication Patterns

1. **Async by Default**: Use async communication patterns
2. **Timeout Management**: Set appropriate timeouts for all requests
3. **Batching**: Batch multiple requests when possible
4. **Caching**: Cache frequently requested information

### Deployment

1. **Health Checks**: Implement comprehensive health checking
2. **Graceful Shutdown**: Handle shutdown signals properly
3. **Resource Limits**: Set appropriate CPU and memory limits
4. **Auto Scaling**: Implement horizontal pod autoscaling

This A2A architecture provides a robust foundation for building sophisticated multi-agent systems with natural language communication, proper resource management, and production-ready reliability.