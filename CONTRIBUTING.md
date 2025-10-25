# Contributing to Strands Agent Factory

Thank you for your interest in contributing to Strands Agent Factory! This document provides guidelines for contributing to the project.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/bassmanitram/strands-agent-factory.git
cd strands-agent-factory
```

2. Install in development mode with all dependencies:
```bash
pip install -e ".[dev,all-providers]"
```

3. Run tests to ensure everything works:
```bash
pytest tests/
```

## Development Workflow

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Create** a feature branch: `git checkout -b feature/amazing-feature`
4. **Make** your changes with comprehensive tests
5. **Add tests** for new functionality
6. **Run tests**: `pytest tests/`
7. **Test examples**: `python examples/basic_usage.py`
8. **Commit** your changes: `git commit -am 'Add amazing feature'`
9. **Push** to your fork: `git push origin feature/amazing-feature`
10. **Submit** a pull request with detailed description

## Code Style

- Follow PEP 8 for Python code style
- Use type hints for all function parameters and return values
- Write comprehensive docstrings for all public APIs
- Keep functions focused and small
- Use meaningful variable and function names
- Follow existing patterns in the codebase

### Code Formatting

```bash
# Format code with black
black strands_agent_factory/

# Sort imports with isort
isort strands_agent_factory/

# Type checking with mypy
mypy strands_agent_factory/
```

## Testing

We maintain a comprehensive test suite with high coverage. All contributions should include appropriate tests.

### Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_config.py      # Configuration validation tests
│   ├── test_adapters.py    # Framework adapter tests
│   ├── test_tools.py       # Tool system tests
│   ├── test_messaging.py   # Message processing tests
│   └── test_utils.py       # Utility function tests
└── integration/            # Integration tests
    ├── test_factory_integration.py
    └── test_adapter_integration.py
```

### Writing Tests

- Write tests for all new functionality
- Maintain or improve test coverage
- Test both success and failure cases
- Use descriptive test names that explain what is being tested
- Group related tests in classes
- Mock external dependencies appropriately

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/test_config.py

# Run with coverage
pytest tests/ --cov=strands_agent_factory

# Run with verbose output
pytest tests/ -v

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

## Architecture Guidelines

### Factory Pattern Responsibilities
- Configuration validation and management
- Framework adapter selection and initialization
- Tool discovery, loading, and lifecycle management
- File content processing and upload
- Session persistence coordination
- Agent creation and resource management

### Framework Adapters
- Model loading and configuration
- Tool schema adaptation for provider compatibility
- Message formatting and system prompt handling
- Provider-specific initialization and cleanup

### Tool System
- Python function discovery and loading
- MCP server lifecycle management
- Tool specification creation and validation
- Dynamic tool loading and configuration

### What the Factory Should NOT Do
- Direct tool execution (delegated to strands-agents)
- CLI argument parsing (handled by wrapper applications)
- User interface concerns
- Direct file system discovery without configuration

## Adding New Framework Support

### Generic Adapter (Preferred)
Most frameworks work automatically with the generic adapter if they follow standard strands-agents patterns:

1. Module: `strands.models.{framework}.{Framework}Model`
2. Standard constructor: `__init__(self, *, model_id, **config)`
3. Inherits from `strands.models.Model`

### Custom Adapter (Special Cases)
For frameworks requiring special handling:

1. Create adapter in `strands_agent_factory/adapters/{framework}.py`
2. Inherit from `FrameworkAdapter`
3. Implement required methods: `framework_name`, `load_model`
4. Add to `FRAMEWORK_HANDLERS` in `adapters/base.py`
5. Add comprehensive tests

Example:
```python
from .base import FrameworkAdapter

class MyFrameworkAdapter(FrameworkAdapter):
    @property
    def framework_name(self) -> str:
        return "myframework"
    
    def load_model(self, model_name, model_config):
        # Custom model loading logic
        return MyFrameworkModel(model_name, **model_config or {})
```

## Adding New Tool Types

1. Add tool type handler to `tools/factory.py`
2. Implement configuration validation
3. Create tool specification generation
4. Add comprehensive tests
5. Update documentation

## Documentation

- Update README.md for public API changes
- Add docstrings to new functions and classes
- Include examples for complex functionality
- Update type hints when adding new interfaces
- Create example scripts for new features

## Examples

When adding new features, include working examples:

1. Add to existing example files or create new ones in `examples/`
2. Include error handling and cleanup
3. Add clear comments explaining the feature
4. Test examples with real API credentials

## Submitting Changes

### Pull Request Guidelines

- Include a clear description of what your changes do
- Reference any related issues
- Include tests for new functionality
- Ensure all tests pass
- Update documentation as needed
- Add examples for new features
- Follow the existing code style

### Commit Messages

Use clear, descriptive commit messages following conventional commits:

- `feat: add support for new framework adapter`
- `fix: handle edge case in session loading`
- `docs: update configuration examples`
- `test: add comprehensive adapter tests`
- `refactor: improve tool loading performance`

## Testing with Real Providers

For testing with actual AI providers:

```bash
# Set up API credentials
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"

# Run integration tests
python examples/basic_usage.py
python examples/tool_configuration_example.py
python examples/file_processing_example.py
```

## Issue Reporting

When reporting issues, please include:

- Python version and operating system
- strands-agent-factory version
- Relevant framework versions (strands-agents, etc.)
- Steps to reproduce the issue
- Expected vs actual behavior
- Any error messages or stack traces
- Relevant configuration details
- Minimal reproducible example

## Feature Requests

Feature requests are welcome! Please:

- Search existing issues first
- Clearly describe the use case
- Explain why this feature would be useful
- Consider the impact on existing functionality
- Provide examples of how it would be used
- Consider submitting a pull request

## Performance Considerations

- Use async/await patterns appropriately
- Implement proper resource cleanup
- Consider memory usage for large file processing
- Use connection pooling where applicable
- Profile performance-critical code paths

## Security Guidelines

- Never commit API keys or sensitive data
- Validate all user inputs
- Use secure defaults for configuration
- Handle file uploads safely
- Follow security best practices for external integrations

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers get started
- Maintain a welcoming environment
- Follow the project's code of conduct

## Release Process

For maintainers:

1. Update version in `__init__.py`
2. Update CHANGELOG.md
3. Run full test suite
4. Test with multiple providers
5. Create release notes
6. Tag release
7. Update documentation

## Questions?

If you have questions about contributing, feel free to:

- Open an issue for discussion
- Check existing documentation
- Look at example implementations
- Contact the maintainers

Thank you for contributing to Strands Agent Factory!