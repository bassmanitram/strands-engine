"""
Unit tests for strands_agent_factory.adapters modules.

Tests framework adapters, model loading, and adapter factory functionality.
"""

from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest

from strands_agent_factory.adapters.base import (
    FrameworkAdapter,
    _can_handle_generically,
    _create_generic_adapter,
    _load_explicit_adapter,
    load_framework_adapter,
)
from strands_agent_factory.adapters.generic import (
    GenericFrameworkAdapter,
    can_handle_generically,
    create_generic_adapter,
)
from strands_agent_factory.core.exceptions import (
    AdapterError,
    ConfigurationError,
    FrameworkNotSupportedError,
    ModelClassNotFoundError,
)


class TestFrameworkAdapterBase:
    """Test cases for base FrameworkAdapter functionality."""

    def test_framework_adapter_is_abstract(self):
        """Test that FrameworkAdapter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            FrameworkAdapter()

    def test_adapt_tools_default_implementation(self):
        """Test default tool adaptation behavior."""

        # Create a concrete mock adapter that inherits from FrameworkAdapter
        class MockAdapter(FrameworkAdapter):
            @property
            def framework_name(self):
                return "mock"

            def load_model(self, model_name=None, model_config=None):
                return Mock()

        adapter = MockAdapter()
        tools = [Mock(), Mock()]
        model_string = "test:model"

        result = adapter.adapt_tools(tools, model_string)

        # Default implementation should return tools unchanged
        assert result == tools

    def test_prepare_agent_args_default(self):
        """Test default agent args preparation."""

        class MockAdapter(FrameworkAdapter):
            @property
            def framework_name(self):
                return "mock"

            def load_model(self, model_name=None, model_config=None):
                return Mock()

        adapter = MockAdapter()
        system_prompt = "Test prompt"
        messages = [{"role": "user", "content": [{"text": "test"}]}]

        result = adapter.prepare_agent_args(
            system_prompt=system_prompt, messages=messages, emulate_system_prompt=False
        )

        expected = {"system_prompt": system_prompt, "messages": messages}

        assert result == expected

    def test_prepare_agent_args_with_emulation(self):
        """Test agent args preparation with system prompt emulation."""

        class MockAdapter(FrameworkAdapter):
            @property
            def framework_name(self):
                return "mock"

            def load_model(self, model_name=None, model_config=None):
                return Mock()

        adapter = MockAdapter()
        system_prompt = "Test prompt"
        messages = []

        result = adapter.prepare_agent_args(
            system_prompt=system_prompt, messages=messages, emulate_system_prompt=True
        )

        # Should prepend system prompt to messages
        assert result["system_prompt"] is None
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][0]["content"][0]["text"] == system_prompt

    def test_adapt_content_default(self):
        """Test default content adaptation."""

        class MockAdapter(FrameworkAdapter):
            @property
            def framework_name(self):
                return "mock"

            def load_model(self, model_name=None, model_config=None):
                return Mock()

        adapter = MockAdapter()
        content = [{"text": "test content"}]

        result = adapter.adapt_content(content)

        # Default implementation should return content unchanged
        assert result == content

    @pytest.mark.asyncio
    async def test_initialize_default(self):
        """Test default adapter initialization."""

        class MockAdapter(FrameworkAdapter):
            @property
            def framework_name(self):
                return "mock"

            def load_model(self, model_name=None, model_config=None):
                return Mock()

        adapter = MockAdapter()
        result = await adapter.initialize("test:model", {})

        # Default implementation should return True
        assert result is True


class TestAdapterFactory:
    """Test cases for adapter factory functionality."""

    def test_load_framework_adapter_invalid_name(self):
        """Test loading adapter with invalid name."""
        with pytest.raises(ConfigurationError, match="Invalid adapter name"):
            load_framework_adapter("")

        with pytest.raises(ConfigurationError, match="Invalid adapter name"):
            load_framework_adapter(None)

    @patch("strands_agent_factory.adapters.base._load_explicit_adapter")
    def test_load_explicit_adapter_success(self, mock_load_explicit):
        """Test successful explicit adapter loading."""
        mock_adapter = Mock()
        mock_load_explicit.return_value = mock_adapter

        with patch(
            "strands_agent_factory.adapters.base.FRAMEWORK_HANDLERS",
            {"test": "test.adapter"},
        ):
            result = load_framework_adapter("test")

        assert result == mock_adapter
        mock_load_explicit.assert_called_once_with("test")

    @patch("strands_agent_factory.adapters.base._load_explicit_adapter")
    def test_load_explicit_adapter_failure(self, mock_load_explicit):
        """Test explicit adapter loading failure."""
        mock_load_explicit.side_effect = Exception("Load failed")

        with patch(
            "strands_agent_factory.adapters.base.FRAMEWORK_HANDLERS",
            {"test": "test.adapter"},
        ):
            with pytest.raises(AdapterError, match="Failed to load explicit adapter"):
                load_framework_adapter("test")

    @patch("strands_agent_factory.adapters.base._can_handle_generically")
    @patch("strands_agent_factory.adapters.base._create_generic_adapter")
    def test_load_generic_adapter_success(self, mock_create_generic, mock_can_handle):
        """Test successful generic adapter loading."""
        mock_can_handle.return_value = True
        mock_adapter = Mock()
        mock_create_generic.return_value = mock_adapter

        result = load_framework_adapter("openai")

        assert result == mock_adapter
        mock_can_handle.assert_called_once_with("openai")
        mock_create_generic.assert_called_once_with("openai")

    @patch("strands_agent_factory.adapters.base._can_handle_generically")
    @patch("strands_agent_factory.adapters.base._create_generic_adapter")
    def test_load_generic_adapter_failure(self, mock_create_generic, mock_can_handle):
        """Test generic adapter loading failure."""
        mock_can_handle.return_value = True
        mock_create_generic.side_effect = Exception("Generic creation failed")

        with pytest.raises(AdapterError, match="Failed to create generic adapter"):
            load_framework_adapter("openai")

    @patch("strands_agent_factory.adapters.base._can_handle_generically")
    def test_load_adapter_not_supported(self, mock_can_handle):
        """Test loading unsupported adapter."""
        mock_can_handle.return_value = False

        with pytest.raises(AdapterError, match="No adapter available for framework"):
            load_framework_adapter("unsupported_framework")

    @patch("importlib.import_module")
    def test_load_explicit_adapter_success_detailed(self, mock_import):
        """Test detailed explicit adapter loading."""
        # Mock the adapter class
        mock_adapter_class = Mock()
        mock_adapter_instance = Mock()
        mock_adapter_class.return_value = mock_adapter_instance

        # Mock the module
        mock_module = Mock()
        setattr(mock_module, "TestAdapter", mock_adapter_class)
        mock_import.return_value = mock_module

        # Test with a valid class path format
        with patch(
            "strands_agent_factory.adapters.base.FRAMEWORK_HANDLERS",
            {"test": "test.module.TestAdapter"},
        ):
            result = _load_explicit_adapter("test")

        # Should import the module and instantiate the class
        mock_import.assert_called_once()
        mock_adapter_class.assert_called_once()
        assert result == mock_adapter_instance

    @patch("strands_agent_factory.adapters.generic.can_handle_generically")
    def test_can_handle_generically_wrapper(self, mock_can_handle):
        """Test the wrapper function for generic handling check."""
        mock_can_handle.return_value = True

        result = _can_handle_generically("openai")

        assert result is True
        mock_can_handle.assert_called_once_with("openai")

    @patch("strands_agent_factory.adapters.generic.can_handle_generically")
    def test_can_handle_generically_import_error(self, mock_can_handle):
        """Test generic handling check with import error."""
        mock_can_handle.side_effect = ImportError("Module not found")

        result = _can_handle_generically("openai")

        assert result is False

    @patch("strands_agent_factory.adapters.generic.create_generic_adapter")
    def test_create_generic_adapter_wrapper(self, mock_create):
        """Test the wrapper function for generic adapter creation."""
        mock_adapter = Mock()
        mock_create.return_value = mock_adapter

        result = _create_generic_adapter("openai")

        assert result == mock_adapter
        mock_create.assert_called_once_with("openai")

    @patch("strands_agent_factory.adapters.generic.create_generic_adapter")
    def test_create_generic_adapter_returns_none(self, mock_create):
        """Test generic adapter creation when it returns None."""
        mock_create.return_value = None

        with pytest.raises(AdapterError, match="Failed to create generic adapter"):
            _create_generic_adapter("openai")


class TestGenericFrameworkAdapter:
    """Test cases for GenericFrameworkAdapter."""

    @patch("strands_agent_factory.adapters.generic.importlib.import_module")
    def test_init_success(self, mock_import):
        """Test successful GenericFrameworkAdapter initialization."""
        # Mock the model class
        mock_model_class = Mock()
        mock_model_class.__annotations__ = {"model_id": str}

        # Mock the module
        mock_module = Mock()
        setattr(mock_module, "OpenaiModel", mock_model_class)
        mock_import.return_value = mock_module

        adapter = GenericFrameworkAdapter("openai")

        assert adapter.framework_name == "openai"
        assert adapter._model_class == mock_model_class
        assert adapter._model_property == "model_id"

    def test_init_framework_not_supported(self):
        """Test initialization with unsupported framework."""
        with pytest.raises(FrameworkNotSupportedError):
            GenericFrameworkAdapter("nonexistent_framework")

    @patch("strands_agent_factory.adapters.generic.importlib.import_module")
    def test_init_model_class_not_found(self, mock_import):
        """Test initialization when model class is not found."""
        # Mock module without expected model class
        mock_module = Mock()
        # Remove the attribute to simulate it not existing
        if hasattr(mock_module, "OpenaiModel"):
            delattr(mock_module, "OpenaiModel")
        mock_import.return_value = mock_module

        with pytest.raises(ModelClassNotFoundError):
            GenericFrameworkAdapter("openai")

    @patch("strands_agent_factory.adapters.generic.importlib.import_module")
    def test_load_model_success(self, mock_import):
        """Test successful model loading."""
        # Mock model class and instance
        mock_model_instance = Mock()
        mock_model_class = Mock(return_value=mock_model_instance)
        mock_model_class.__annotations__ = {"model_id": str}
        mock_model_class.__name__ = "OpenaiModel"

        mock_module = Mock()
        setattr(mock_module, "OpenaiModel", mock_model_class)
        mock_import.return_value = mock_module

        adapter = GenericFrameworkAdapter("openai")

        result = adapter.load_model("gpt-4o", {"temperature": 0.7})

        assert result == mock_model_instance
        mock_model_class.assert_called_with(model_id="gpt-4o", temperature=0.7)

    @patch("strands_agent_factory.adapters.generic.importlib.import_module")
    def test_load_model_with_model_name_override(self, mock_import):
        """Test model loading with model name override."""
        mock_model_instance = Mock()
        mock_model_class = Mock(return_value=mock_model_instance)
        mock_model_class.__annotations__ = {"model_id": str}
        mock_model_class.__name__ = "OpenaiModel"

        mock_module = Mock()
        setattr(mock_module, "OpenaiModel", mock_model_class)
        mock_import.return_value = mock_module

        adapter = GenericFrameworkAdapter("openai")

        # The implementation doesn't override model_id if it's already in config
        # It only sets it if it's not present
        result = adapter.load_model("gpt-4o", {"model_id": "old-model"})

        # The actual implementation preserves the existing model_id in config
        mock_model_class.assert_called_once()
        call_args = mock_model_class.call_args
        assert call_args[1]["model_id"] == "old-model"

    def test_can_handle_generically_success(self):
        """Test successful generic handling check."""
        with patch(
            "strands_agent_factory.adapters.generic.GenericFrameworkAdapter._validate_framework_import"
        ) as mock_validate_import:
            with patch(
                "strands_agent_factory.adapters.generic.GenericFrameworkAdapter._validate_model_property"
            ) as mock_validate_property:
                mock_validate_import.return_value = (True, Mock())
                mock_validate_property.return_value = True

                result = can_handle_generically("openai")

                assert result is True

    def test_can_handle_generically_requires_custom_adapter(self):
        """Test generic handling check for frameworks requiring custom adapters."""
        result = can_handle_generically("bedrock")

        assert result is False

    def test_can_handle_generically_invalid_framework(self):
        """Test generic handling check with invalid framework."""
        result = can_handle_generically("")

        assert result is False

        result = can_handle_generically(None)

        assert result is False

    @patch("strands_agent_factory.adapters.generic.GenericFrameworkAdapter")
    def test_create_generic_adapter_success(self, mock_adapter_class):
        """Test successful generic adapter creation."""
        mock_adapter = Mock()
        mock_adapter_class.return_value = mock_adapter

        result = create_generic_adapter("openai")

        assert result == mock_adapter
        mock_adapter_class.assert_called_once_with("openai")

    @patch("strands_agent_factory.adapters.generic.GenericFrameworkAdapter")
    def test_create_generic_adapter_failure(self, mock_adapter_class):
        """Test generic adapter creation failure with expected errors."""
        # Test expected errors (should return None)
        mock_adapter_class.side_effect = FrameworkNotSupportedError(
            "Framework not supported"
        )

        result = create_generic_adapter("unsupported_framework")

        assert result is None

    @patch("strands_agent_factory.adapters.generic.GenericFrameworkAdapter")
    def test_create_generic_adapter_unexpected_error(self, mock_adapter_class):
        """Test generic adapter creation with unexpected errors."""
        # Test unexpected errors (should raise wrapped exception)
        mock_adapter_class.side_effect = RuntimeError("Unexpected error")

        from strands_agent_factory.core.exceptions import GenericAdapterCreationError

        with pytest.raises(GenericAdapterCreationError):
            create_generic_adapter("test_framework")
