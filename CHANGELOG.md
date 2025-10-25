# Changelog

All notable changes to strands-agent-factory will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- **Comprehensive Test Suite** - 139 tests with 100% pass rate
- **Resource Management** - Context managers and proper cleanup
- **Concurrent Operations** - Thread-safe MCP server initialization
- **Memory Efficiency** - Streaming and chunked processing
- **Performance Optimization** - Connection pooling and caching

### Dependencies
- **strands-agents** - Core agent framework
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

### Breaking Changes
- None (initial release)

### Deprecated
- None (initial release)

### Removed
- None (initial release)

### Fixed
- None (initial release)

### Security
- Input validation for all user-provided data
- Safe file handling with size limits
- Secure defaults for all configuration options
- No sensitive data in logs or error messages

---

## Release Notes

This represents the initial comprehensive release of strands-agent-factory, providing a complete factory pattern implementation for strands-agents with extensive multi-framework support, advanced tool integration, and sophisticated conversation management capabilities.

The project includes a full test suite with 139 tests achieving 100% pass rate, comprehensive documentation, and working examples for all major features.

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