# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-12-19

### Major Restructure & Dependency Fixes

#### Added
- **Modern Modular Architecture**: Reorganized codebase into logical modules
  - `core/`: Core functionality (factory, agent, config, types)
  - `adapters/`: Framework adapters (was `framework/`) 
  - `tools/`: Tool management and loading
  - `messaging/`: Message generation and content processing
  - `session/`: Session and conversation management
  - `handlers/`: Event and callback handlers

- **Correct Project Metadata & Dependencies**:
  - **CRITICAL FIX**: `strands-agents==1.10.0` (exact version - >1.10.0 breaks strands-tools)
  - **Framework Support**: Proper `strands-agents[framework]==1.10.0` extras
  - **Tools Integration**: Optional `strands-agents-tools` via `[tools]` extra (not required for base functionality)
  - **Installation Options**: `[litellm]`, `[anthropic]`, `[openai]`, `[ollama]`, `[bedrock]`, `[all-providers]`, `[full]`
  - Enhanced package metadata with correct classifiers and keywords

- **Comprehensive Documentation**:
  - Complete README rewrite with correct installation instructions
  - **Dependency explanation**: Clear guidance on exact version requirements
  - Installation examples for all provider combinations
  - Architecture documentation and advanced usage examples

#### Changed
- **Critical Dependency Strategy**: 
  - ✅ **Core**: `strands-agents==1.10.0` (exact version for strands-tools compatibility)
  - ✅ **Framework Extras**: `strands-agents[framework]==1.10.0` (maintains version alignment)
  - ✅ **Tools**: Optional `strands-agents-tools` (not required for base functionality)
  - ✅ **Installation**: Proper extras system with version constraints

- **Import Structure**: Complete reorganization with systematic updates
  - All imports updated to reflect new modular organization
  - Fixed adapter import issues (`base_adapter` → `base`, `ptypes` → `core.types`)
  - Resolved all circular import issues

- **File Organization**: Logical grouping by functionality
  - `ptypes.py` → `core/types.py`
  - `framework/` → `adapters/` 
  - `messages.py` → `messaging/generator.py`
  - `utils.py` → `messaging/content.py`
  - `callback_handler.py` → `handlers/callback.py`

- **Logging System**: Production-ready logging
  - Entry/exit logging moved to trace level (94+ statements)
  - Replaced `logger.exception()` with `logger.error()` 
  - Cleaner error output without excessive stack traces

#### Fixed
- **Version Compatibility**: 
  - `strands-agents==1.10.0` exactly (required for tools compatibility)
  - All framework extras use same version for consistency
  - Prevents broken installations with incompatible versions

- **Import Resolution**: All files now import correctly
  - Fixed remaining adapter import issues
  - Cleared cached bytecode that caused import errors
  - All modules load without circular dependencies

#### Technical Details
- **24 files** reorganized into **6 logical modules**
- **Zero breaking changes** to public API
- **Maintained backward compatibility** for all user interfaces
- **Professional dependency management** following Python packaging standards

### Installation Examples
```bash
# Basic installation (minimal dependencies)
pip install strands-agent-factory

# With specific AI provider (recommended)
pip install "strands-agent-factory[litellm]"       # LiteLLM for 100+ providers
pip install "strands-agent-factory[anthropic]"     # Anthropic Claude
pip install "strands-agent-factory[openai]"        # OpenAI GPT

# With tools integration (optional)
pip install "strands-agent-factory[tools]"         # Adds strands-agents-tools

# Complete installation
pip install "strands-agent-factory[full]"          # Everything + dev tools
```

### Dependency Rationale
- **`strands-agents==1.10.0`**: Exact version required - newer versions break strands-tools compatibility
- **`strands-agents-tools`**: Optional - only needed for strands-tools integration, not core functionality
- **Framework extras**: Use `strands-agents[framework]==1.10.0` to ensure all dependencies are compatible

### Testing
- ✅ All functionality verified with corrected dependencies
- ✅ Factory initialization and agent creation working
- ✅ Multi-framework support with proper version constraints
- ✅ Optional tools integration available when needed
- ✅ Demo and integration tests pass

---

## Pre-0.1.0 Development

### Initial Development Phase
- Core factory pattern implementation
- Multi-framework adapter system
- Tool discovery and loading system
- MCP server integration
- Session and conversation management
- File processing and content extraction