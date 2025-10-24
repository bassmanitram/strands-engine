# Test Suite for strands_agent_factory

This directory contains a comprehensive test suite for the strands_agent_factory package, organized into unit tests, integration tests, and supporting fixtures.

## Test Structure

```
tests/
├── unit/                   # Unit tests for individual components
│   ├── test_config.py     # Configuration validation tests
│   ├── test_utils.py      # Utility function tests
│   ├── test_messaging.py  # Message processing tests
│   ├── test_adapters.py   # Adapter system tests
│   └── test_tools.py      # Tool loading tests
├── integration/           # Integration tests for component interactions
│   ├── test_factory_integration.py    # Factory workflow tests
│   └── test_adapter_integration.py    # Adapter system integration
├── fixtures/              # Test data and utilities
│   └── sample_configs.py  # Sample configurations and test data
├── conftest.py           # Pytest configuration and shared fixtures
└── README.md             # This file
```

## Running Tests

### Quick Start

```bash
# Run all tests
python run_tests.py

# Run only unit tests
python run_tests.py --unit

# Run only integration tests
python run_tests.py --integration

# Run with coverage report
python run_tests.py --coverage
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration

# Run specific test file
pytest tests/unit/test_config.py

# Run with coverage
pytest --cov=strands_agent_factory --cov-report=html

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

## Test Categories

### Unit Tests (`tests/unit/`)

Unit tests focus on testing individual components in isolation using mocks and stubs to eliminate external dependencies.

- **test_config.py**: Tests for `AgentFactoryConfig` including validation, initialization, and error handling
- **test_utils.py**: Tests for utility functions like `clean_dict` and `print_structured_data`
- **test_messaging.py**: Tests for message generation, content processing, and file handling
- **test_adapters.py**: Tests for adapter system, framework detection, and model loading
- **test_tools.py**: Tests for tool discovery, loading, and factory functionality

### Integration Tests (`tests/integration/`)

Integration tests verify that components work correctly together with minimal mocking.

- **test_factory_integration.py**: End-to-end factory workflow tests
- **test_adapter_integration.py**: Adapter system integration and framework support tests

## Test Fixtures

### Shared Fixtures (`conftest.py`)

- **Configuration fixtures**: `basic_config`, `config_with_tools`, `summarizing_config`
- **File fixtures**: `temp_dir`, `temp_file`, `sample_text_file`, `large_file`
- **Mock fixtures**: `mock_model`, `mock_agent`, `mock_framework_adapter`
- **Tool fixtures**: `python_tool_config`, `mcp_tool_config`, `tool_spec_python`
- **Environment fixtures**: `clean_environment`, `mock_env_vars`

### Sample Data (`fixtures/sample_configs.py`)

- Tool configurations for different types (Python, MCP, etc.)
- Agent factory configurations for various scenarios
- Model configurations for different frameworks
- Sample message data and file content
- Error test data for negative testing

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.slow`: Tests that take a long time to run
- `@pytest.mark.requires_network`: Tests requiring network access
- `@pytest.mark.requires_models`: Tests requiring actual model access (expensive)

## Running Specific Test Types

```bash
# Run only fast tests (exclude slow tests)
python run_tests.py --fast

# Skip network-dependent tests
python run_tests.py --no-network

# Skip expensive model tests
python run_tests.py --no-models

# Run specific test function
python run_tests.py --function test_basic_config_creation

# Run specific test file
python run_tests.py --file config
```

## Coverage Reports

Generate coverage reports to see test coverage:

```bash
# Terminal coverage report
python run_tests.py --coverage

# HTML coverage report
python run_tests.py --html-coverage
# Open htmlcov/index.html in browser
```

## Test Development Guidelines

### Writing Unit Tests

1. **Isolation**: Use mocks to isolate the component under test
2. **Comprehensive**: Test both success and failure scenarios
3. **Edge cases**: Include boundary conditions and error cases
4. **Clear naming**: Use descriptive test method names
5. **Arrange-Act-Assert**: Structure tests clearly

Example:
```python
def test_config_validation_success(self):
    """Test successful configuration validation."""
    # Arrange
    config_data = {"model": "openai:gpt-4o"}
    
    # Act
    config = AgentFactoryConfig(**config_data)
    
    # Assert
    assert config.model == "openai:gpt-4o"
```

### Writing Integration Tests

1. **Minimal mocking**: Only mock external dependencies
2. **Real interactions**: Test actual component interactions
3. **End-to-end flows**: Test complete workflows
4. **Error propagation**: Verify errors are handled correctly

### Using Fixtures

1. **Reuse fixtures**: Use shared fixtures from `conftest.py`
2. **Parameterize**: Use `@pytest.mark.parametrize` for multiple test cases
3. **Cleanup**: Fixtures handle cleanup automatically
4. **Scope appropriately**: Use appropriate fixture scopes

## Debugging Tests

### Running with Debug Output

```bash
# Verbose output
python run_tests.py --verbose

# Show print statements
pytest -s

# Stop on first failure
python run_tests.py --failfast

# Run last failed tests
python run_tests.py --lf
```

### Using Debugger

```python
# Add breakpoint in test
def test_something(self):
    import pdb; pdb.set_trace()
    # Test code here
```

## Continuous Integration

The test suite is designed to work in CI environments:

- All external dependencies are mocked in unit tests
- Integration tests use minimal real dependencies
- Tests are marked appropriately for selective running
- Coverage reports can be generated for CI

## Dependencies

Required packages for running tests:

```bash
pip install pytest pytest-asyncio pytest-mock
```

Optional packages for enhanced functionality:

```bash
pip install pytest-cov pytest-xdist pytest-html
```

## Contributing

When adding new functionality:

1. **Add unit tests** for new components
2. **Add integration tests** for new workflows
3. **Update fixtures** if new test data is needed
4. **Mark tests appropriately** with pytest markers
5. **Update documentation** if test structure changes

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure the package is installed in development mode
2. **Missing dependencies**: Install test dependencies with `pip install -e .[test]`
3. **Fixture conflicts**: Check fixture scopes and naming
4. **Mock issues**: Verify mock paths and return values

### Getting Help

- Check test output for specific error messages
- Use `pytest --collect-only` to see test discovery
- Run with `-v` for verbose output
- Check fixture usage with `pytest --fixtures`