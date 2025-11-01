# A2A System Prompt Auto-Generation

## Overview

When running an A2A server with custom skill definitions, the system prompt can be automatically generated from the skill cards. This ensures the agent has complete context about its capabilities and understands its role in agent-to-agent communication.

## How It Works

### Trigger Conditions

System prompt auto-generation occurs when **ALL** of the following are true:

1. `--skill-config-paths` is provided (custom skills loaded from files)
2. No explicit `--system-prompt` in CLI arguments
3. No `system_prompt` in `--agent-config` file

### Generated Prompt Structure

The generated prompt includes three sections:

```
# Agent Role and Purpose
- Specifies this is an A2A agent (not for direct human interaction)
- Clarifies all requests come from other AI agents

# Your Capabilities
- Lists each skill with complete JSON card
- Includes all skill metadata (tags, examples, inputModes, etc.)

# Operating Guidelines
- A2A-specific best practices
- Skill usage guidelines
- Response quality expectations
```

## Examples

### Example 1: Single Comprehensive Skill

**Command:**
```bash
strands-a2a-server --model gpt-4o --skill-config-paths examples/skills/math.json
```

**Generated Prompt:**
```
# Agent Role and Purpose

You are an AI agent designed to be accessed exclusively by other AI agents through the Agent-to-Agent (A2A) protocol.
You will NOT interact directly with humans. All requests come from other AI agents acting on behalf of users.

# Your Capabilities

You provide 1 specialized skill:

## Skill 1: Mathematical Analysis

```json
{
  "description": "Perform complex mathematical calculations including algebra, calculus, statistics, and numerical analysis",
  "examples": [
    "Calculate the derivative of x^2 + 3x + 2",
    "Solve the equation 2x + 5 = 15",
    "Find the mean, median, and mode of a dataset",
    "Compute the integral of sin(x) from 0 to pi"
  ],
  "id": "math",
  "inputModes": ["text"],
  "name": "Mathematical Analysis",
  "outputModes": ["text", "structured"],
  "security": null,
  "tags": ["math", "calculation", "analysis", "numerical"]
}
```

# Operating Guidelines

1. **Agent-to-Agent Context**: All requests come from other AI agents, not humans directly
2. **Use Your Skills**: Apply the appropriate skill(s) based on the incoming request
3. **Be Precise**: Other agents expect structured, accurate responses
4. **Honor Skill Boundaries**: Only perform operations within your defined skill set
5. **Provide Context**: Include relevant details from skill examples and tags when appropriate

Focus on delivering high-quality results using your skills as defined above.
```

### Example 2: Multiple Skills

**Command:**
```bash
strands-a2a-server --model gpt-4o \
  --skill-config-paths examples/skills/math.json examples/skills/coding.json
```

**Result:**
- Prompt includes complete JSON cards for both Math and Coding skills
- Header says "You provide 2 specialized skills:"
- Each skill gets its own section with full metadata

### Example 3: Skills from Array File

**Command:**
```bash
strands-a2a-server --model gpt-4o --skill-config-paths examples/skills/all-skills.json
```

**Result:**
- Loads 3 skills (Math, Coding, Research) from array
- Generates prompt with all 3 skill cards
- Each skill shown with complete JSON (even if minimal)

## Disabling Auto-Generation

### Method 1: Provide Explicit System Prompt (CLI)

```bash
strands-a2a-server --model gpt-4o \
  --skill-config-paths examples/skills/math.json \
  --system-prompt "You are a math assistant for other AI agents."
```

**Result:** Uses explicit prompt, ignores skill cards for prompt generation

### Method 2: Provide System Prompt in Config File

**agent-config.yaml:**
```yaml
model: gpt-4o
system_prompt: "You are a math assistant for other AI agents."
```

**Command:**
```bash
strands-a2a-server --agent-config agent-config.yaml \
  --skill-config-paths examples/skills/math.json
```

**Result:** Uses config file prompt, ignores skill cards for prompt generation

### Method 3: Don't Use Custom Skills

```bash
strands-a2a-server --model gpt-4o --tool-config-paths tools.json
```

**Result:** Skills auto-detected from tools, no prompt generation (default behavior)

## Behavior Matrix

| Scenario | Skill Files | System Prompt | Result |
|----------|-------------|---------------|--------|
| Auto-generate | ✓ Provided | ✗ Not set | **Generate from skills** |
| Explicit prompt | ✓ Provided | ✓ Set | Use explicit prompt |
| No skills | ✗ Not provided | ✗ Not set | Use default (no generation) |
| Config prompt | ✓ Provided | ✓ In config file | Use config prompt |

## Why Full Skill Cards?

Including complete JSON skill cards in the system prompt provides several benefits:

### 1. Complete Context
The agent sees all skill metadata:
- **tags**: Helps categorize and understand skill domains
- **examples**: Shows the agent what types of requests to expect
- **inputModes/outputModes**: Clarifies expected data formats
- **security**: Understands any access restrictions

### 2. Self-Documentation
Other agents can query this agent about its capabilities, and the responses will be accurate because the agent has full skill context.

### 3. Consistency
The same skill definitions used for A2A protocol discovery are provided to the agent, ensuring no mismatch between advertised and actual capabilities.

### 4. Future-Proof
As the AgentSkill schema evolves, new fields are automatically included in prompts without code changes.

## Why A2A-Specific Directive?

The prompt explicitly states the agent is for A2A use:

```
You will NOT interact directly with humans. All requests come from other AI agents acting on behalf of users.
```

### Benefits:

1. **Response Style**: Agent understands it's talking to machines, not humans
   - Can be more structured
   - Less need for conversational niceties
   - Can use technical terminology freely

2. **Error Handling**: Agent knows errors should be machine-readable
   - Return structured error responses
   - Include error codes/types
   - Be precise about failures

3. **Context Awareness**: Agent understands the multi-agent architecture
   - Requests may be part of larger workflows
   - Other agents handle user interaction
   - Focus on accuracy over explanation

## Console Output

When system prompt is auto-generated, the server prints:

```
Building agent configuration...
   Skills: Loaded 2 custom skill(s) from config files
      - Mathematical Analysis (math): Perform complex mathematical calculations including algebra, calculus, statistics, and numerical analysis
      - Code Generation and Analysis (coding): Write, debug, analyze, and explain code in multiple programming languages including Python, JavaScript, Java, and more
   System Prompt: Auto-generated from 2 skill card(s)
Initializing agent factory...
```

When explicit prompt is used:

```
Building agent configuration...
   Skills: Loaded 2 custom skill(s) from config files
      - Mathematical Analysis (math): Perform complex mathematical calculations...
      - Code Generation and Analysis (coding): Write, debug, analyze, and explain code...
   System Prompt: Using explicitly provided prompt
Initializing agent factory...
```

## Testing

### Test Auto-Generation

```bash
strands-a2a-server --model gpt-4o \
  --skill-config-paths examples/skills/math.json \
  --verbose
```

Check logs for:
```
System Prompt: Auto-generated from 1 skill card(s)
```

### Test Explicit Override

```bash
strands-a2a-server --model gpt-4o \
  --skill-config-paths examples/skills/math.json \
  --system-prompt "Custom prompt" \
  --verbose
```

Check logs for:
```
System Prompt: Using explicitly provided prompt
```

### Inspect Generated Prompt

Use Python to see the exact generated prompt:

```python
from strands_agent_factory.scripts.a2a_server import (
    _load_skills_from_files, 
    _generate_system_prompt_from_skills
)

skills = _load_skills_from_files(['examples/skills/math.json'])
prompt = _generate_system_prompt_from_skills(skills)
print(prompt)
```

## Best Practices

### 1. Use Rich Skill Definitions

Include examples, tags, and modes for better context:

```json
{
  "name": "Data Analysis",
  "id": "analysis",
  "description": "Analyze datasets and generate insights",
  "tags": ["data", "analysis", "statistics"],
  "examples": [
    "Find correlations in this dataset",
    "Identify outliers and anomalies",
    "Generate summary statistics"
  ],
  "inputModes": ["text", "structured"],
  "outputModes": ["text", "structured", "visualization"]
}
```

**Why:** Richer skills generate more helpful prompts.

### 2. Keep Descriptions Concise

The description appears in the JSON card in the prompt, so keep it clear but not verbose:

```json
// Good
"description": "Perform complex mathematical calculations including algebra, calculus, and statistics"

// Too verbose
"description": "This skill allows you to perform a wide variety of complex mathematical calculations including but not limited to algebraic manipulations, calculus operations such as derivatives and integrals, statistical analyses including mean, median, mode, standard deviation, and much more."
```

### 3. Provide Meaningful Examples

Examples help the agent understand request patterns:

```json
"examples": [
  "Calculate the derivative of x^2",  // Specific, clear
  "Do math stuff"                      // Too vague
]
```

### 4. Test Generated Prompts

Before production, inspect generated prompts:

```bash
python -c "
from strands_agent_factory.scripts.a2a_server import _load_skills_from_files, _generate_system_prompt_from_skills
skills = _load_skills_from_files(['your-skills.json'])
print(_generate_system_prompt_from_skills(skills))
" > generated-prompt.txt

cat generated-prompt.txt
```

### 5. Version Your Skills

Keep skill files in version control alongside code:

```
project/
├── skills/
│   ├── v1/
│   │   └── math.json
│   └── v2/
│       └── math.json  # With new fields
└── deployments/
    └── production.yaml  # Points to skills/v2/
```

## Troubleshooting

### Prompt Not Generated

**Symptom:** Server starts but no "Auto-generated from X skill card(s)" message

**Causes:**
1. No `--skill-config-paths` provided → Skills auto-detected, no generation
2. Explicit `--system-prompt` provided → Using explicit prompt
3. `system_prompt` in config file → Using config prompt

**Solution:** Verify command includes `--skill-config-paths` and no `--system-prompt`

### Prompt Too Long

**Symptom:** Generated prompt exceeds model context limits

**Causes:**
- Too many skills (>10-20)
- Very verbose skill descriptions or examples

**Solutions:**
1. Split into multiple A2A servers (one per skill domain)
2. Use explicit system prompt instead of auto-generation
3. Simplify skill descriptions and reduce examples
4. Use model with larger context window

### Wrong Skills in Prompt

**Symptom:** Prompt includes unexpected skills

**Cause:** Loading wrong file or multiple files

**Solution:** Check `--skill-config-paths` argument carefully:
```bash
# Wrong
--skill-config-paths skills/*.json  # Shell expands this!

# Right
--skill-config-paths skills/math.json skills/coding.json
```

## Implementation Details

### Function: `_generate_system_prompt_from_skills()`

**Location:** `strands_agent_factory/scripts/a2a_server.py`

**Signature:**
```python
def _generate_system_prompt_from_skills(skills: List[AgentSkill]) -> str
```

**Logic:**
1. Creates prompt header with A2A directive
2. Loops through skills, converting each to JSON via `skill.model_dump()`
3. Wraps each skill JSON in markdown code block
4. Adds operating guidelines
5. Returns complete prompt as string

**Key Code:**
```python
for i, skill in enumerate(skills, 1):
    skill_dict = skill.model_dump()
    prompt_parts.extend([
        f"## Skill {i}: {skill.name}",
        "```json",
        json.dumps(skill_dict, indent=2),
        "```"
    ])
```

### Integration Point

Called in `run_a2a_server()` after loading skills:

```python
if args.skill_config_paths:
    skills = _load_skills_from_files(args.skill_config_paths)
    
    if not config.system_prompt:  # Only if no explicit prompt
        config.system_prompt = _generate_system_prompt_from_skills(skills)
        print(f"   System Prompt: Auto-generated from {len(skills)} skill card(s)")
```

## Related Documentation

- [A2A Skills Implementation Complete](A2A_SKILLS_IMPLEMENTATION_COMPLETE.md)
- [Skill Configuration Examples](../examples/skills/README.md)
- [Agent Factory Configuration](AGENT_FACTORY_CONFIG.md)
