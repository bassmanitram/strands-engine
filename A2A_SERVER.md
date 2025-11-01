# A2A Server Guide

This guide explains how to use strands-agent-factory's A2A (Agent-to-Agent) server wrapper to create multi-agent systems where AI agents can communicate with each other using natural language.

## Overview

The A2A server wrapper allows any agent created by strands-agent-factory to be exposed as an Agent-to-Agent server. Other agents can then discover and communicate with this server using natural language messages, creating powerful multi-agent workflows.

**Key Concept**: The A2A server exposes the agent's tools and capabilities to other agents through a conversational interface. The agent's tools (Python functions, MCP servers, A2A connections) become available for other agents to use indirectly through natural language requests.

For detailed architectural information, see [docs/A2A_ARCHITECTURE.md](docs/A2A_ARCHITECTURE.md).

## Quick Start

### 1. Install A2A Dependencies

```bash
pip install "strands-agent-factory[a2a]"
```

### 2. Create Agent Configuration

Create an agent configuration file that defines what tools and capabilities your agent provides:

**data_agent.yaml:**
```yaml
# Agent Configuration
model: "gpt-4o"
system_prompt: "You are a data analysis specialist. Use your tools to help with calculations, file processing, and data visualization."

# Tools this agent provides to other agents
tool_config_paths:
  - "tools/math_tools.json"          # Python calculation functions
  - "tools/data_processing.json"     # Python data manipulation
  - "tools/chart_mcp_server.json"    # MCP server for chart generation

# Conversation management
conversation_manager_type: "sliding_window"
sliding_window_size: 40

# Model configuration
model_config:
  temperature: 0.1  # More deterministic for data work
  max_tokens: 2000
```

### 3. Start the A2A Server

```bash
# Basic usage
strands-a2a-server data_agent.yaml

# Production deployment
strands-a2a-server data_agent.yaml \
  --host 0.0.0.0 \
  --port 8001 \
  --skills "data_analysis" "mathematical_computation" "chart_generation"
```

### 4. Connect from Other Agents

Other agents can now connect to and communicate with your data agent:

**hr_agent.yaml:**
```yaml
model: "gpt-4o"
system_prompt: "You are an HR assistant that can work with other specialized agents."

tool_config_paths:
  - "tools/company_agents.json"  # Contains A2A connection to data agent
```

**tools/company_agents.json:**
```json
{
  "id": "company_agents",
  "type": "a2a",
  "urls": [
    "http://localhost:8001/"  # The data agent A2A server
  ]
}
```

## Command Line Usage

### Basic Commands

```bash
# Start server with default settings (127.0.0.1:9000)
strands-a2a-server agent_config.yaml

# Custom host and port
strands-a2a-server agent_config.yaml --host 0.0.0.0 --port 8001

# With public URL (for load balancers)
strands-a2a-server agent_config.yaml --public-url http://my-agent.company.com:8001/

# With specific skills
strands-a2a-server agent_config.yaml --skills data_analysis math_tools file_processing

# With version and verbose logging
strands-a2a-server agent_config.yaml --version 2.0.0 --verbose
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `config_file` | Path to agent configuration file (JSON or YAML) | Required |
| `--host` | Host to bind server to | `127.0.0.1` |
| `--port` | Port to bind server to | `9000` |
| `--public-url` | Public URL where agent will be accessible | Auto-generated |
| `--version` | Agent version string | `1.0.0` |
| `--skills` | List of skills/capabilities this agent provides | None |
| `--serve-at-root` | Serve at root path (useful with load balancers) | `False` |
| `--verbose` | Enable verbose logging | `False` |

## Skills Configuration

The `--skills` parameter is a powerful feature for advertising agent capabilities and enabling agent discovery in multi-agent systems.

### Skills Overview

**Purpose**: Skills allow agents to advertise their capabilities, enabling other agents to discover and route requests to appropriate specialists.

**Type**: `list[a2a.types.AgentSkill] | None`  
**Format**: Space-separated string identifiers  
**Default**: `None` (auto-detected from agent capabilities)  
**Style**: `snake_case` naming convention  

### Common Skill Categories

#### Data & Analytics Skills
```bash
--skills data_analysis statistical_analysis data_visualization mathematical_computation chart_generation
```

#### Business Function Skills  
```bash
--skills employee_lookup policy_queries payroll_coordination payroll_data employee_coordination
```

#### Technical Function Skills
```bash
--skills file_processing math_tools reporting document_processing database_query api_integration
```

#### Domain-Specific Skills
```bash
# IT & DevOps
--skills database_management network_administration security_analysis deployment_automation

# Customer Service
--skills customer_service order_management inventory_tracking ticket_management escalation_handling

# Development & Engineering
--skills code_generation testing deployment_automation api_development system_integration
```

### Skill Naming Conventions

#### Recommended Patterns
- **`{domain}_{action}`** - `data_analysis`, `employee_lookup`
- **`{technology}_{operation}`** - `database_query`, `api_integration`  
- **`{business_function}`** - `payroll_coordination`, `inventory_management`
- **`{capability_description}`** - `mathematical_computation`, `natural_language_processing`

#### Good Examples
```bash
# Domain + Action pattern
--skills data_analysis document_processing image_generation text_summarization

# Technology + Operation pattern  
--skills database_query api_integration file_conversion email_sending

# Business Function pattern
--skills payroll_coordination inventory_management customer_onboarding order_fulfillment

# Capability Description pattern
--skills mathematical_computation natural_language_processing computer_vision
```

#### What to Avoid
- ❌ Spaces in skill names (use underscores: `data_analysis` not `data analysis`)
- ❌ Special characters beyond underscores (`data-analysis` should be `data_analysis`)
- ❌ Very long skill names (keep concise and searchable)
- ❌ Duplicate skill names in the same agent
- ❌ Generic terms that aren't discoverable (`helper`, `utility`)

### Skills Usage Examples

#### Real-World Agent Configurations

**Data Analysis Agent:**
```bash
strands-a2a-server data-agent.yaml \
  --host 0.0.0.0 \
  --port 8001 \
  --skills data_analysis statistical_analysis data_visualization mathematical_computation chart_generation
```

**HR Management Agent:**
```bash
strands-a2a-server hr-agent.yaml \
  --host 0.0.0.0 \
  --port 8002 \
  --skills employee_lookup policy_queries payroll_coordination benefits_management performance_reviews
```

**Customer Service Agent:**
```bash
strands-a2a-server customer-service.yaml \
  --host 0.0.0.0 \
  --port 8003 \
  --skills order_lookup customer_support ticket_management escalation_handling refund_processing
```

**DevOps Automation Agent:**
```bash
strands-a2a-server devops-agent.yaml \
  --host 0.0.0.0 \
  --port 8004 \
  --skills deployment_automation infrastructure_monitoring log_analysis security_scanning container_management
```

### Auto-Detection vs Manual Skills

#### Manual Skills (Explicit)
When you specify skills manually, they are advertised exactly as provided:

```bash
strands-a2a-server --model gpt-4o --skills data_analysis math_tools
# Server Output: Skills: data_analysis, math_tools
```

#### Auto-Detection (Default)
When no skills are specified, the agent attempts to detect capabilities from its tools:

```bash
strands-a2a-server --model gpt-4o  
# Server Output: Skills: (auto-detected from agent capabilities)
```

Auto-detection analyzes:
- Python function names and docstrings
- MCP server capabilities
- A2A client connections
- Tool configuration metadata

### Skills in Multi-Agent Discovery

#### Agent Discovery Process
1. **Agent A** needs help with data analysis
2. **Agent A** calls `a2a_discover_agent()` or `a2a_list_discovered_agents()`
3. **Discovery system** returns agents with their advertised skills
4. **Agent A** identifies agents with `data_analysis` skill
5. **Agent A** routes request to appropriate data analysis agent

#### Example Discovery Response
```json
{
  "id": "data-analysis-agent",
  "url": "http://data-agent:8001/",
  "skills": ["data_analysis", "statistical_analysis", "data_visualization"],
  "version": "1.0.0"
}
```

### Skills Best Practices

#### 1. Be Descriptive and Specific
```bash
# Good: Specific and discoverable
--skills financial_analysis budget_forecasting expense_tracking

# Avoid: Too generic
--skills analysis forecasting tracking
```

#### 2. Use Consistent Naming
```bash
# Good: Consistent pattern across agents
--skills data_analysis data_visualization data_export
--skills user_management user_authentication user_reporting

# Avoid: Inconsistent patterns
--skills data_analysis visualize export_data
```

#### 3. Match Agent Capabilities
```bash
# Good: Skills match actual agent tools
# Agent with pandas, matplotlib, and statistics tools:
--skills data_analysis statistical_analysis data_visualization

# Avoid: Advertising skills the agent doesn't have
--skills machine_learning  # But agent has no ML tools
```

#### 4. Consider Agent Interactions
```bash
# Design complementary skills across agents:
# Agent 1: Data collection and processing
--skills data_collection data_cleaning data_transformation

# Agent 2: Data analysis and visualization  
--skills data_analysis statistical_analysis data_visualization

# Agent 3: Reporting and presentation
--skills report_generation dashboard_creation presentation_formatting
```

#### 5. Use Skills for Routing Logic
```bash
# Customer service agent with escalation logic:
--skills customer_support order_management basic_technical_support

# Specialized technical agents:  
--skills database_technical_support network_technical_support security_technical_support
```

### Skills Validation and Testing

#### Verify Skills Match Capabilities
```bash
# Test that advertised skills work
curl -X POST http://localhost:8001/message \
  -H "Content-Type: application/json" \
  -d '{"content": "Perform data analysis on this dataset: [1,2,3,4,5]"}'
```

#### Monitor Skills Usage
```bash
# Enable verbose logging to see how skills are used
strands-a2a-server agent-config.yaml --skills data_analysis --verbose
```

#### Document Skills
```yaml
# Document skills in agent configuration comments
# Skills: data_analysis, statistical_analysis, data_visualization
# Capabilities: Can analyze datasets, generate statistics, create charts
model: "gpt-4o"
system_prompt: "Data analysis specialist with pandas, numpy, and matplotlib tools"
```

The skills system provides a foundation for intelligent agent discovery and workflow routing in complex multi-agent environments. By carefully choosing descriptive, consistent skills, you enable effective agent coordination and specialization.

## Configuration Examples

### Data Processing Agent

**data_agent.yaml:**
```yaml
model: "gpt-4o"
system_prompt: "You are a data analysis specialist. Help with calculations, data processing, and visualization."

tool_config_paths:
  - "tools/pandas_tools.json"        # Data manipulation
  - "tools/matplotlib_tools.json"    # Charting
  - "tools/statistics_tools.json"    # Statistical analysis

conversation_manager_type: "sliding_window"
sliding_window_size: 30

model_config:
  temperature: 0.1
  max_tokens: 2000
```

**Usage:**
```bash
strands-a2a-server data_agent.yaml \
  --host 0.0.0.0 \
  --port 8001 \
  --skills "data_analysis" "statistical_analysis" "data_visualization"
```

### HR System Agent

**hr_agent.yaml:**
```yaml
model: "anthropic:claude-3-5-sonnet-20241022"
system_prompt: "You are an HR assistant with access to employee data and other company systems."

tool_config_paths:
  - "tools/employee_database.json"   # Direct HR functions
  - "tools/policy_mcp_server.json"   # MCP server for policies
  - "tools/company_agents.json"      # A2A connections to other agents

session_id: "hr_agent_session"
conversation_manager_type: "summarizing"
preserve_recent_messages: 15
```

**tools/company_agents.json:**
```json
{
  "id": "company_agents",
  "type": "a2a",
  "urls": [
    "http://data-agent:8001/",      # Connect to data agent
    "http://payroll-agent:8002/",   # Connect to payroll agent
    "http://facilities-agent:8003/" # Connect to facilities agent
  ],
  "timeout": 300
}
```

**Usage:**
```bash
strands-a2a-server hr_agent.yaml \
  --host 0.0.0.0 \
  --port 8002 \
  --public-url "http://hr-agent.company.com:8002/" \
  --skills "employee_lookup" "policy_queries" "payroll_coordination"
```

### Customer Service Agent

**customer_service_agent.yaml:**
```yaml
model: "gpt-4o"
system_prompt: "You are a customer service agent with access to order management and technical support systems."

tool_config_paths:
  - "tools/order_management.json"    # Order lookup and updates
  - "tools/knowledge_base_mcp.json"  # Knowledge base MCP server
  - "tools/escalation_agents.json"   # A2A connections for escalation

conversation_manager_type: "summarizing"
preserve_recent_messages: 20
summary_ratio: 0.2

model_config:
  temperature: 0.3
  max_tokens: 1500
```

## Multi-Agent Workflows

### Example: Comprehensive Employee Report

This example shows how multiple agents work together to generate a comprehensive employee report.

#### 1. Setup Multiple Agents

**Start the data agent:**
```bash
strands-a2a-server data_agent.yaml --host 0.0.0.0 --port 8001 --skills data_analysis
```

**Start the payroll agent:**
```bash
strands-a2a-server payroll_agent.yaml --host 0.0.0.0 --port 8002 --skills payroll_data
```

**Start the HR coordinator agent:**
```bash
strands-a2a-server hr_agent.yaml --host 0.0.0.0 --port 8003 --skills employee_coordination
```

#### 2. Agent Communication Flow

```
User Request: "Generate a salary analysis report for all data scientists"
     ↓ 
HR Agent (receives request)
     ↓
HR Agent → Employee Agent: "List all employees with 'Data Scientist' job titles"
     ↓
HR Agent → Payroll Agent: "Get salary data for employee IDs [1,2,3,4,5]"
     ↓
HR Agent → Data Agent: "Create a salary distribution chart for this data: [salary data]"
     ↓
HR Agent → User: "Here's your comprehensive salary analysis report with visualization"
```

#### 3. Configuration for Multi-Agent Setup

**hr_agent.yaml:**
```yaml
model: "gpt-4o"
system_prompt: "You coordinate with other company agents to provide comprehensive HR services."

tool_config_paths:
  - "tools/company_agents.json"
  - "tools/basic_hr_tools.json"
```

**tools/company_agents.json:**
```json
{
  "id": "company_agents",
  "type": "a2a",
  "urls": [
    "http://localhost:8001/",  # Data agent
    "http://localhost:8002/"   # Payroll agent
  ],
  "timeout": 300
}
```

### Example: Technical Support Escalation

This example shows a customer service agent escalating to technical specialists.

#### Agent Hierarchy

```
Customer Service Agent (Port 8000)
    ↓ A2A connections to:
├── Database Support Agent (Port 8001)
├── Network Support Agent (Port 8002) 
└── Security Support Agent (Port 8003)
```

#### Workflow

1. **Customer**: "My login isn't working and I'm getting database errors"
2. **Customer Service Agent**: Analyzes the issue
3. **Customer Service Agent → Database Support**: "User getting login errors, can you check database connectivity?"
4. **Customer Service Agent → Security Support**: "User login failing, any security blocks on account X?"
5. **Customer Service Agent**: Synthesizes responses and provides solution

## Production Deployment

### Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy agent configuration and tools
COPY agent_config.yaml .
COPY tools/ tools/

# Start A2A server
CMD ["strands-a2a-server", "agent_config.yaml", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  data-agent:
    build: .
    ports:
      - "8001:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data_agent_config.yaml:/app/agent_config.yaml
      - ./tools:/app/tools
  
  hr-agent:
    build: .
    ports:
      - "8002:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./hr_agent_config.yaml:/app/agent_config.yaml
      - ./tools:/app/tools
    depends_on:
      - data-agent
```

### Kubernetes Deployment

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: data-agent
  template:
    metadata:
      labels:
        app: data-agent
    spec:
      containers:
      - name: data-agent
        image: my-company/data-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai-key
        command: ["strands-a2a-server", "agent_config.yaml", "--host", "0.0.0.0", "--port", "8000"]
---
apiVersion: v1
kind: Service
metadata:
  name: data-agent-service
spec:
  selector:
    app: data-agent
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

### Load Balancer Configuration

**nginx.conf:**
```nginx
upstream data-agent {
    server data-agent-1:8000;
    server data-agent-2:8000;
}

server {
    listen 80;
    server_name data-agent.company.com;
    
    location / {
        proxy_pass http://data-agent;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring and Observability

### Health Checks

A2A servers automatically expose health endpoints:

```bash
# Check if agent is healthy
curl http://localhost:8001/health

# Get agent capabilities
curl http://localhost:8001/capabilities
```

### Logging

Enable comprehensive logging:

```bash
# Verbose logging
strands-a2a-server agent_config.yaml --verbose

# Or set environment variable
export LOGURU_LEVEL=DEBUG
strands-a2a-server agent_config.yaml
```

### Metrics

Monitor agent performance:

```python
# Custom monitoring in agent config
import logging

# Configure structured logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
```

## Security Considerations

### Authentication

For production deployments, implement authentication:

```yaml
# In agent configuration
tool_config_paths:
  - "tools/authenticated_agents.json"
```

**tools/authenticated_agents.json:**
```json
{
  "id": "secure_agents",
  "type": "a2a",
  "urls": [
    "https://agent1.company.com/"
  ],
  "timeout": 300,
  "webhook_token": "secure-webhook-token"
}
```

### Network Security

- Use HTTPS in production
- Implement network segmentation
- Use service mesh for inter-agent communication
- Monitor agent-to-agent traffic

### Access Control

- Limit which agents can communicate with each other
- Implement role-based access control
- Log all inter-agent communications
- Use least privilege principles

## Troubleshooting

### Common Issues

**Agent not starting:**
```bash
# Check configuration
strands-a2a-server agent_config.yaml --verbose

# Verify dependencies
pip install "strands-agent-factory[a2a]"
```

**Connection refused:**
```bash
# Check if server is running
curl http://localhost:9000/health

# Verify port and host settings
strands-a2a-server agent_config.yaml --host 0.0.0.0 --port 8001
```

**Tool loading errors:**
```bash
# Verify tool configuration paths
ls -la tools/

# Check tool configuration syntax
python -c "import json; print(json.load(open('tools/my_tools.json')))"
```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
# Enable verbose logging
strands-a2a-server agent_config.yaml --verbose

# Or use environment variable
export LOGURU_LEVEL=TRACE
strands-a2a-server agent_config.yaml
```

## Best Practices

### Agent Design

1. **Single Responsibility**: Each agent should have a focused purpose
2. **Clear Skills**: Define clear skills/capabilities for each agent
3. **Robust Error Handling**: Handle communication failures gracefully
4. **Stateless Operations**: Design agents to be stateless where possible

### Communication Patterns

1. **Request-Response**: Simple synchronous communication
2. **Delegation**: Route requests to appropriate specialist agents
3. **Aggregation**: Combine results from multiple agents
4. **Chain of Responsibility**: Pass requests through agent hierarchy

### Performance

1. **Connection Pooling**: Reuse A2A connections
2. **Timeout Management**: Set appropriate timeouts
3. **Load Balancing**: Distribute load across agent instances
4. **Caching**: Cache frequently requested information

### Monitoring

1. **Health Checks**: Implement comprehensive health monitoring
2. **Request Tracing**: Track requests across agent boundaries
3. **Performance Metrics**: Monitor response times and success rates
4. **Error Tracking**: Log and alert on agent communication failures

## Advanced Topics

### Custom Agent Protocols

Extend A2A communication with custom protocols:

```python
# Custom message formatting
class CustomA2AProtocol:
    def format_message(self, content: str) -> dict:
        return {
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": self.agent_id
        }
```

### Agent Discovery Services

Implement dynamic agent discovery:

```yaml
# Service discovery configuration
tool_config_paths:
  - "tools/service_discovery.json"
```

### Message Routing

Implement intelligent message routing:

```python
# Route messages based on content analysis
def route_message(message: str) -> str:
    if "data analysis" in message.lower():
        return "http://data-agent:8001/"
    elif "payroll" in message.lower():
        return "http://payroll-agent:8002/"
    else:
        return "http://general-agent:8000/"
```

## Conclusion

The A2A server wrapper provides a powerful way to create sophisticated multi-agent systems using strands-agent-factory. By exposing agents as conversational endpoints, you can build complex workflows that leverage the strengths of specialized agents while maintaining clean separation of concerns.

The skills system enables intelligent agent discovery and routing, allowing you to build scalable multi-agent architectures where agents can find and collaborate with appropriate specialists automatically.

For more information, see the main [README.md](README.md) and [docs/A2A_ARCHITECTURE.md](docs/A2A_ARCHITECTURE.md) for detailed architectural documentation.