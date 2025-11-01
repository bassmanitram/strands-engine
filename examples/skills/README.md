# A2A Skills Configuration Examples

This directory contains example skill definition files for the A2A server.

## What are Skills?

Skills define how your agent is presented to other A2A (Agent-to-Agent) agents. They describe the capabilities your agent can perform in a standardized format that other agents can discover and understand.

## Auto-Detection vs Custom Skills

### Auto-Detection (Default)
By default, skills are automatically detected from your agent's tool configurations:
```bash
strands-a2a-server --model gpt-4o --tool-config-paths ../tools/python_tools.json
# Skills automatically created from tool descriptions
```

### Custom Skills
Use `--skill-config-paths` to provide custom skill definitions:
```bash
strands-a2a-server --model gpt-4o --skill-config-paths skills/math.json
```

## System Prompt Auto-Generation

**NEW:** When you provide custom skills WITHOUT an explicit system prompt, the agent's system prompt is automatically generated from your skill definitions.

### How It Works

```bash
# This command auto-generates system prompt from math.json
strands-a2a-server --model gpt-4o --skill-config-paths examples/skills/math.json

# Console output:
#   Skills: Loaded 1 custom skill(s) from config files
#   System Prompt: Auto-generated from 1 skill card(s)
```

The generated prompt includes:
- **A2A Role**: Specifies the agent is for agent-to-agent communication only
- **Full Skill Cards**: Complete JSON representation of each skill
- **Operating Guidelines**: Best practices for A2A interactions

### Example Generated Prompt

For `math.json`, the system generates:

```
# Agent Role and Purpose

You are an AI agent designed to be accessed exclusively by other AI agents through the Agent-to-Agent (A2A) protocol.
You will NOT interact directly with humans. All requests come from other AI agents acting on behalf of users.

# Your Capabilities

You provide 1 specialized skill:

## Skill 1: Mathematical Analysis

```json
{
  "name": "Mathematical Analysis",
  "id": "math",
  "description": "Perform complex mathematical calculations...",
  "tags": ["math", "calculation", "analysis", "numerical"],
  "examples": ["Calculate derivatives", "Solve equations", ...]
}
```

# Operating Guidelines

1. **Agent-to-Agent Context**: All requests come from other AI agents, not humans directly
2. **Use Your Skills**: Apply the appropriate skill(s) based on the incoming request
3. **Be Precise**: Other agents expect structured, accurate responses
...
```

### Disabling Auto-Generation

To use your own system prompt instead:

```bash
# Option 1: CLI argument
strands-a2a-server --model gpt-4o \
  --skill-config-paths examples/skills/math.json \
  --system-prompt "Your custom prompt here"

# Option 2: Config file
strands-a2a-server --agent-config config.yaml \
  --skill-config-paths examples/skills/math.json
```

**See [A2A System Prompt Generation docs](../../docs/A2A_SYSTEM_PROMPT_GENERATION.md) for complete details.**

## When to Use Custom Skills

Use custom skill definitions when you want:
- Custom skill names/descriptions different from tool names
- Additional metadata (tags, examples, inputModes, outputModes)
- Skills that aggregate multiple tools into higher-level capabilities
- Skills that represent conceptual capabilities beyond individual tools
- Control which capabilities are exposed to other agents
- **Auto-generated system prompts with A2A-specific guidance**
- Professional presentation for production multi-agent systems

## File Format

Skills are defined using the A2A `AgentSkill` format.

### Required Fields

- **name** (str): Display name of the skill
- **id** (str): Unique identifier for the skill
- **description** (str): Description of what the skill does
- **tags** (list[str]): Categorization tags (can be empty list)

### Optional Fields

- **examples** (list[str]): Example use cases or requests
- **inputModes** (list[str]): Supported input types (e.g., ["text", "url"])
- **outputModes** (list[str]): Supported output types (e.g., ["text", "structured"])
- **security** (list[dict]): Security requirements

## Example Files

### math.json
Single skill for mathematical analysis with comprehensive metadata.

**Usage:**
```bash
strands-a2a-server --model gpt-4o --skill-config-paths examples/skills/math.json
```

**Features:**
- Rich description and examples
- inputModes and outputModes specified
- Will generate comprehensive system prompt

### coding.json
Single skill for code generation and analysis with examples.

**Usage:**
```bash
strands-a2a-server --model gpt-4o --skill-config-paths examples/skills/coding.json
```

**Features:**
- Multiple detailed examples
- Code-specific input/output modes
- Debugging and review capabilities

### research.yaml
Single skill in YAML format for research assistance.

**Usage:**
```bash
strands-a2a-server --model gpt-4o --skill-config-paths examples/skills/research.yaml
```

**Features:**
- YAML format example
- Document and URL input modes
- Research-specific tags and examples

### all-skills.json
Multiple skills in one file (array format).

**Usage:**
```bash
strands-a2a-server --model gpt-4o --skill-config-paths examples/skills/all-skills.json
```

**Features:**
- Minimal skill format (required fields only)
- Three different skills in one file
- Demonstrates array format

## Usage Examples

### Single Skill File
```bash
strands-a2a-server --model gpt-4o --skill-config-paths examples/skills/math.json
# Auto-generates system prompt from math skill
```

### Multiple Skill Files
```bash
strands-a2a-server --model gpt-4o \
  --skill-config-paths examples/skills/math.json examples/skills/coding.json
# Auto-generates system prompt from both skills
```

### Multiple Skills from One File
```bash
strands-a2a-server --model gpt-4o --skill-config-paths examples/skills/all-skills.json
# Auto-generates system prompt from 3 skills
```

### Override Auto-Detected Skills
```bash
# Agent has many internal tools, but only expose specific skills
strands-a2a-server --model gpt-4o \
  --tool-config-paths ../tools/internal-tools.json \
  --skill-config-paths examples/skills/math.json
# Only math skill exposed, prompt generated from math skill
```

### Mix JSON and YAML
```bash
strands-a2a-server --model gpt-4o \
  --skill-config-paths examples/skills/math.json examples/skills/research.yaml
# Works with both formats
```

### Custom System Prompt
```bash
strands-a2a-server --model gpt-4o \
  --skill-config-paths examples/skills/math.json \
  --system-prompt "You are a specialized math agent for automated workflows."
# Uses explicit prompt, skills still registered with A2A server
```

## Creating Your Own Skill Files

### Minimal Skill (JSON)
```json
{
  "name": "My Skill",
  "id": "my-skill",
  "description": "What this skill does",
  "tags": ["category"]
}
```

### Rich Skill (JSON)
**Recommended for best system prompt generation:**

```json
{
  "name": "Advanced Analysis",
  "id": "analysis",
  "description": "Perform complex data analysis and visualization",
  "tags": ["analysis", "data", "visualization"],
  "examples": [
    "Analyze this dataset and identify trends",
    "Create visualizations for this data",
    "Compare these two datasets statistically"
  ],
  "inputModes": ["text", "structured"],
  "outputModes": ["text", "structured", "visualization"]
}
```

**Note:** Rich skills with examples and modes generate more helpful system prompts!

### Rich Skill (YAML)
```yaml
name: Advanced Analysis
id: analysis
description: Perform complex data analysis and visualization
tags:
  - analysis
  - data
  - visualization
examples:
  - Analyze this dataset and identify trends
  - Create visualizations for this data
  - Compare these two datasets statistically
inputModes:
  - text
  - structured
outputModes:
  - text
  - structured
  - visualization
```

### Multiple Skills in One File
```json
[
  {
    "name": "Skill 1",
    "id": "skill1",
    "description": "First skill",
    "tags": ["tag1"]
  },
  {
    "name": "Skill 2",
    "id": "skill2",
    "description": "Second skill",
    "tags": ["tag2"]
  }
]
```

## Validation

Skills are validated using Pydantic. If a required field is missing or has an invalid type, you'll get a clear error message:

```
ConfigurationError: Invalid skill definition in skills/bad.json at index 0: 
Field required [type=missing, input_value={'name': 'Math', 'id': 'math'}, input_type=dict]
```

## Best Practices

1. **Use descriptive names**: Make it clear what the skill does
2. **Provide examples**: Help other agents understand how to use the skill (and improve generated prompts!)
3. **Use meaningful IDs**: Use lowercase with hyphens (e.g., "data-analysis")
4. **Tag appropriately**: Use tags for discoverability and categorization
5. **Keep descriptions concise**: One or two sentences is usually enough (appears in system prompt)
6. **Specify input/output modes**: Helps agents understand data format expectations
7. **Include rich metadata**: Examples, tags, and modes make better system prompts
8. **Aggregate when appropriate**: One skill can represent multiple related tools
9. **Version control**: Keep skill files in version control alongside your code
10. **Test generated prompts**: Use `--verbose` to see what system prompt is generated

## Testing Generated Prompts

To see the generated system prompt without starting the server:

```python
from strands_agent_factory.scripts.a2a_server import (
    _load_skills_from_files,
    _generate_system_prompt_from_skills
)

skills = _load_skills_from_files(['examples/skills/math.json'])
prompt = _generate_system_prompt_from_skills(skills)
print(prompt)
```

Or check the console output when starting the server:
```bash
strands-a2a-server --model gpt-4o --skill-config-paths examples/skills/math.json
# Look for: "System Prompt: Auto-generated from 1 skill card(s)"
```

## Troubleshooting

### "Skill config file not found"
- Check the file path is correct
- Use absolute paths or paths relative to where you run the command

### "Invalid skill definition"
- Verify all required fields are present (name, id, description, tags)
- Check JSON/YAML syntax is valid
- Ensure tags is an array, even if empty: `"tags": []`

### "A2A dependencies not available"
```bash
pip install 'strands-agents[a2a]'
```

### System prompt not being generated
- Ensure `--skill-config-paths` is provided
- Verify no `--system-prompt` argument
- Check config file doesn't have `system_prompt` field
- See "Using explicitly provided prompt" message? You have a system prompt set somewhere

## More Information

See the project documentation:
- [A2A System Prompt Generation](../../docs/A2A_SYSTEM_PROMPT_GENERATION.md) - Complete guide to auto-generation
- [A2A Skills Implementation](../../docs/A2A_SKILLS_IMPLEMENTATION_COMPLETE.md) - Technical implementation details
- Agent configuration options - AgentFactoryConfig documentation
- Tool configuration - Tool setup guide
- Multi-agent workflows - Building agent networks
