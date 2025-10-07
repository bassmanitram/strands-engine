# Sample Model Configurations

This directory contains example configurations for common models and frameworks. These are provided as starting points - users should customize them for their specific needs.

## Configuration Structure

Each configuration file contains a dictionary that is **completely opaque** to strands_engine. It is merged directly with the model identifier and passed to the underlying Strands model class constructor.

**Users are responsible for:**
- Providing parameters that the specific Strands model class accepts
- Understanding the parameter names expected by each framework
- Ensuring values are valid for the target model API

## Framework-Specific Examples

### OpenAI Direct (`openai:model-name`)
**Uses**: `strands.models.openai.OpenAIModel`

- `openai-gpt4o.json` - GPT-4o with standard parameters
- `openai-gpt35-turbo.json` - GPT-3.5 Turbo with bias controls and user tracking

**Key OpenAI Parameters:**
- `temperature`, `max_tokens`, `top_p` - Generation controls
- `frequency_penalty`, `presence_penalty` - Repetition controls  
- `logit_bias` - Token probability adjustments
- `seed` - Deterministic generation
- `user` - User tracking identifier
- `stream` - Streaming response mode

### Anthropic Direct (`anthropic:model-name`)
**Uses**: `strands.models.anthropic.AnthropicModel`

- `anthropic-claude35-sonnet.json` - Claude 3.5 Sonnet balanced settings
- `anthropic-claude3-haiku.json` - Claude 3 Haiku fast response settings

**Key Anthropic Parameters:**
- `temperature`, `max_tokens`, `top_p`, `top_k` - Generation controls
- `stop_sequences` - Custom stop sequences
- `metadata` - Request metadata (user tracking, etc.)

### AWS Bedrock (`bedrock:model-id`)
**Uses**: `strands.models.bedrock.BedrockModel`

- `bedrock-claude3-sonnet.json` - Claude 3 Sonnet on Bedrock
- `bedrock-titan-text.json` - Amazon Titan Text with nested config
- `bedrock-llama2-70b.json` - Llama 2 70B on Bedrock

**Key Bedrock Parameters:**
- `temperature`, `max_tokens`, `top_p`, `top_k` - Generation controls
- `textGenerationConfig` - Nested configuration object (model-specific)
- `stop_sequences` - Stop sequences
- `max_gen_len` - Alternative max length parameter (Llama models)

### LiteLLM Multi-Provider (`litellm:provider/model` or `litellm:model`)  
**Uses**: `strands.models.litellm.LiteLLMModel`

- `litellm-gpt4o.json` - GPT-4o via LiteLLM
- `litellm-azure-gpt4.json` - Azure OpenAI with deployment settings
- `litellm-vertex-gemini.json` - Google Vertex AI Gemini with safety settings
- `litellm-cohere-command.json` - Cohere Command model settings

**Key LiteLLM Parameters:**
- Standard: `temperature`, `max_tokens`, `top_p`, `frequency_penalty`, `presence_penalty`
- Azure: `api_base`, `api_version`, `azure_deployment`
- Vertex AI: `vertex_project`, `vertex_location`, `safety_settings`
- Cohere: `return_likelihoods`, `truncate`
- Provider-specific authentication and endpoint parameters

### Ollama Local (`ollama:model-name`)
**Uses**: `strands.models.ollama.OllamaModel`

- `ollama-llama2.json` - Llama 2 7B local serving
- `ollama-codellama.json` - Code Llama 13B with code-specific settings  
- `ollama-mistral.json` - Mistral 7B with advanced Ollama parameters

**Key Ollama Parameters:**
- `host` - Ollama server URL (default: http://localhost:11434)
- `temperature`, `max_tokens`, `top_p`, `top_k` - Generation controls
- `repeat_penalty`, `repeat_last_n` - Repetition controls
- `num_predict`, `num_ctx` - Context and prediction limits
- `num_batch`, `num_gpu` - Performance tuning
- `stop` - Stop sequences
- Model-specific parameters vary by base model

## Parameter References

Consult Strands documentation and model class constructors for complete parameter lists:

- **strands.models.openai.OpenAIModel**: [OpenAI API Parameters](https://platform.openai.com/docs/api-reference/chat/create)
- **strands.models.anthropic.AnthropicModel**: [Anthropic API Parameters](https://docs.anthropic.com/claude/reference/messages_post)  
- **strands.models.litellm.LiteLLMModel**: [LiteLLM Providers](https://docs.litellm.ai/docs/providers)
- **strands.models.bedrock.BedrockModel**: [AWS Bedrock Models](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters.html)
- **strands.models.ollama.OllamaModel**: [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)

## Usage

These configurations are loaded as the `model_config` parameter:

```python
import json
from strands_engine import EngineConfig

# Load a sample configuration
with open('code/sample-model-configs/openai-gpt4o.json') as f:
    model_config = json.load(f)

# Use with EngineConfig
config = EngineConfig(
    model="openai:gpt-4o",
    model_config=model_config,
    system_prompt="You are a helpful assistant."
)
```

Parameters must match what the Strands model constructors expect, not necessarily the raw API parameters.