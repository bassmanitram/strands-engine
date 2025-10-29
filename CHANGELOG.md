# Changelog

All notable changes to strands-agent-factory will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2025-10-29

### Added
- **Summarization Model Configuration**: New `summarization_model_config` parameter in `AgentFactoryConfig` allows passing framework-specific configuration to the summarization model. This enables using the same model with different settings (e.g., lower temperature, reduced max_tokens) for summarization tasks.
  - Always creates a separate summarization agent when `conversation_manager_type` is "summarizing"
  - Uses `summarization_model` (defaults to main `model`) with `summarization_model_config` (defaults to `{}`)
  - Raises `InitializationError` if agent creation fails when explicit summarization settings are specified
  - Falls back gracefully to using main agent if no explicit summarization settings were provided

### Fixed
- **Custom Summarization Prompt**: Fixed bug where `custom_summarization_prompt` was being passed to `SummarizingConversationManager` where it was ignored. Now correctly applied to the summarization agent's system prompt.
  - System prompt is set on the agent itself during creation
  - Uses `custom_summarization_prompt` if provided, else `DEFAULT_SUMMARIZATION_PROMPT` from strands
  - No longer passes `summarization_system_prompt` to `SummarizingConversationManager` when agent is provided

### Changed
- **Summarization Agent Creation**: Refactored conversation manager factory to always create a separate summarization agent for the summarizing strategy, enabling different model configurations even when using the same model.
  - Extracted `_create_summarizing_manager()` method for cleaner code organization
  - Centralized error handling in `_handle_agent_creation_failure()` method (DRY principle)
  - Improved error messages for explicit requirement failures

### Documentation
- Updated `summarization_model` docstring to clarify it uses the same format as the `model` parameter
- Updated `summarization_model_config` docstring to explain always-create-agent behavior
- Added comprehensive examples showing same-model-different-config usage

### Technical Details
- Added 5 new tests for summarization agent creation logic
- All 184 tests pass
- No breaking changes to existing API
- Backward compatible with existing configurations

## [1.0.1] - 2025-10-28

### Fixed
- **Initial Message Adaptation**: Fixed bug where initial messages passed to the agent were not being adapted by the framework adapter's `adapt_content()` method. This caused issues with frameworks that require specific content transformations (e.g., AWS Bedrock). The fix ensures all messages, including initial messages, are properly transformed before being passed to the Agent constructor.
  - Modified `FrameworkAdapter.prepare_agent_args()` to call `adapt_content()` on initial messages
  - Added `has_initial_messages` property to `AgentProxy` for checking if initial messages are configured
  - Affects: `strands_agent_factory/adapters/base.py`, `strands_agent_factory/core/agent.py`

### Technical Details
- The bug manifested when using file uploads or initial messages with frameworks like Bedrock that require content adaptation
- All 171 tests continue to pass with this fix
- No breaking changes or API modifications

## [1.0.0] - 2024-10-24

### Added
- Comprehensive factory pattern for strands-agents Agent creation
- Multi-framework support with automatic generic adapter
- Advanced tool system supporting Python functions and MCP servers
- Smart file processing with content extraction and dynamic references
- Session persistence with conversation state management
- Conversation management strategies (sliding window, summarizing)
- Declarative configuration with comprehensive validation
- Extensible architecture with plugin support

#### Core Features
- `AgentFactory` - Main factory class for agent creation and management
- `AgentFactoryConfig` - Comprehensive configuration dataclass with validation
- `AgentProxy` - Context manager wrapper for proper resource management
- Factory pattern separating configuration from instantiation
- Automatic resource cleanup and lifecycle management

#### Framework Support
- **Generic Adapter** - Automatic support for any strands-compatible framework
- **LiteLLM Adapter** - Specialized adapter for 100+ providers via LiteLLM
- **AWS Bedrock Adapter** - Enterprise-grade AWS Bedrock integration
- **Ollama Adapter** - Local model serving with custom configuration
- Automatic framework detection and adapter selection
- Extensible adapter system for custom providers

#### Tool System
- **Python Tools** - Dynamic loading of Python functions from modules
- **MCP Tools** - Model Context Protocol server integration
- **Tool Factory** - Centralized tool discovery and configuration
- **Tool Specifications** - Unified tool description format
- Automatic tool schema adaptation for provider compatibility
- Concurrent MCP server initialization with proper cleanup

#### File Processing
- **Smart Content Extraction** - Automatic processing of various file formats
- **Dynamic File References** - `file()` syntax for runtime file inclusion
- **Glob Pattern Support** - Batch file processing with wildcards
- **MIME Type Detection** - Automatic format detection and handling
- **Binary File Support** - Base64 encoding for non-text files
- **Document Processing** - PDF, Office, CSV, and other document formats

#### Session Management
- **DelegatingSession** - Dynamic session switching and management
- **Conversation Persistence** - Save and restore conversation state
- **Session Backup** - Automatic backup of incompatible session states
- **Multi-Session Support** - Switch between conversations dynamically
- **Session Lifecycle** - Proper initialization and cleanup

#### Conversation Management
- **Sliding Window** - Keep recent messages within context limits
- **Summarizing Strategy** - Intelligent summarization of older messages
- **Null Strategy** - No conversation management for unlimited context
- **Custom Summarization** - Optional separate model for summarization
- **Configurable Parameters** - Window size, summary ratio, preservation rules

#### Configuration System
- **Comprehensive Validation** - Early error detection with clear messages
- **Type Safety** - Full type hints and runtime validation
- **Flexible Model Strings** - Support for various provider formats
- **Environment Integration** - Environment variable support
- **Serializable Configuration** - JSON/YAML compatible configuration

#### Error Handling
- **Exception Hierarchy** - Structured exception types for different error categories
- **Graceful Degradation** - Fallback behavior for failed components
- **Detailed Error Messages** - Clear error reporting with context
- **Resource Cleanup** - Proper cleanup even on errors
- **Debug Support** - Comprehensive logging and tracing

#### Examples and Documentation
- **Basic Usage Examples** - Simple getting started examples
- **Multi-Provider Examples** - Demonstrations of different AI providers
- **Tool Configuration Examples** - Python and MCP tool setup
- **File Processing Examples** - File upload and dynamic reference examples
- **Advanced Configuration** - Complex use case demonstrations
- **Comprehensive Documentation** - Detailed API documentation and guides

### Technical Implementation
- **Modern Python Architecture** - Type hints, dataclasses, async/await
- **Comprehensive Test Suite** - 171 tests with 100% pass rate
- **Resource Management** - Context managers and proper cleanup
- **Concurrent Operations** - Thread-safe MCP server initialization
- **Memory Efficiency** - Streaming and chunked processing
- **Performance Optimization** - Connection pooling and caching

### Dependencies
- **strands-agents** - Core agent framework (pinned to 1.10.0)
- **loguru** - Structured logging
- **pydantic** - Data validation (via strands-agents)
- **Optional Framework Dependencies** - Installed via extras

### Installation Options
- `[openai]` - OpenAI GPT models
- `[anthropic]` - Anthropic Claude models
- `[litellm]` - 100+ providers via LiteLLM
- `[ollama]` - Local model serving
- `[bedrock]` - AWS Bedrock integration
- `[tools]` - MCP and advanced tool support
- `[all-providers]` - All framework support
- `[full]` - Complete installation with development tools
- `[dev]` - Development dependencies

### Security
- Input validation for all user-provided data
- Safe file handling with size limits
- Secure defaults for all configuration options
- No sensitive data in logs or error messages

---

## Release Notes

### Version 1.1.0
This minor release adds support for configuring the summarization model independently from the main model, and fixes a bug where custom summarization prompts were not being applied. The new `summarization_model_config` parameter enables cost optimization by using the same model with different settings (e.g., lower max_tokens) for summarization tasks.

**Key Features:**
- Configure summarization model independently (temperature, max_tokens, etc.)
- Use same model with different config for summarization
- Custom summarization prompts now work correctly
- Explicit error handling when summarization requirements can't be met

**Breaking Changes:** None - fully backward compatible

### Version 1.0.1
This is a patch release that fixes a bug with initial message adaptation in framework adapters. Users experiencing issues with file uploads or initial messages on frameworks like AWS Bedrock should upgrade to this version.

### Version 1.0.0
This represents the initial comprehensive release of strands-agent-factory, providing a complete factory pattern implementation for strands-agents with extensive multi-framework support, advanced tool integration, and sophisticated conversation management capabilities.

The project includes a full test suite with 171 tests achieving 100% pass rate, comprehensive documentation, and working examples for all major features.

### Supported AI Providers
- OpenAI (GPT-4, GPT-4o, GPT-3.5-turbo, etc.)
- Anthropic (Claude 3.5 Sonnet, Claude 3 Opus, etc.)
- Google (Gemini 2.5 Flash, Gemini Pro, etc.)
- Ollama (Llama, Code Llama, Mistral, etc.)
- AWS Bedrock (Claude, Titan, Command, etc.)
- 100+ additional providers via LiteLLM

### Key Use Cases
- **Research Assistants** - Document analysis with tool integration
- **Code Assistants** - Development tools with file processing
- **Data Analysis** - CSV, JSON, and document processing
- **Multi-Modal Analysis** - Text, image, and document processing
- **Enterprise Applications** - AWS Bedrock with compliance features
- **Local Development** - Ollama integration for offline work

### Architecture Benefits
- **Clean Separation** - Configuration, initialization, and usage phases
- **Resource Safety** - Automatic cleanup and lifecycle management
- **Framework Agnostic** - Unified interface across providers
- **Extensible Design** - Plugin architecture for customization
- **Production Ready** - Comprehensive error handling and logging

[Unreleased]: https://github.com/bassmanitram/strands-agent-factory/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/bassmanitram/strands-agent-factory/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/bassmanitram/strands-agent-factory/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/bassmanitram/strands-agent-factory/releases/tag/v1.0.0
