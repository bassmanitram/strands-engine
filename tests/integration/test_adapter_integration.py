"""
Integration tests for adapter system and framework support.

Tests the complete adapter loading workflow, generic adapter functionality,
and framework detection mechanisms.
"""

from unittest.mock import Mock, patch, MagicMock

import pytest

from strands_agent_factory.adapters.base import (
    load_framework_adapter,
    FRAMEWORK_HANDLERS
)
from strands_agent_factory.adapters.generic import (
    GenericFrameworkAdapter,
    can_handle_generically,
    create_generic_adapter
)
from strands_agent_factory.core.exceptions import (
    AdapterError,
    FrameworkNotSupportedError,
    ModelClassNotFoundError
)


class TestAdapterSystemIntegration:
    """Integration tests for the complete adapter system."""

    @pytest.mark.integration
    def test_adapter_loading_priority_system(self):
        """Test that adapter loading follows the correct priority order."""
        # Test 1: Explicit adapter has highest priority
        with patch('strands_agent_factory.adapters.base._load_explicit_adapter') as mock_explicit:
            mock_adapter = Mock()
            mock_explicit.return_value = mock_adapter
            
            # Use a framework that's in FRAMEWORK_HANDLERS
            framework_name = list(FRAMEWORK_HANDLERS.keys())[0] if FRAMEWORK_HANDLERS else "litellm"
            
            with patch('strands_agent_factory.adapters.base.FRAMEWORK_HANDLERS', {framework_name: "test.adapter"}):
                result = load_framework_adapter(framework_name)
                
                assert result == mock_adapter
                mock_explicit.assert_called_once_with(framework_name)

    @pytest.mark.integration
    @patch('strands_agent_factory.adapters.base._can_handle_generically')
    @patch('strands_agent_factory.adapters.base._create_generic_adapter')
    def test_adapter_loading_generic_fallback(self, mock_create_generic, mock_can_handle):
        """Test that generic adapter is used when no explicit adapter exists."""
        mock_can_handle.return_value = True
        mock_adapter = Mock()
        mock_create_generic.return_value = mock_adapter
        
        # Use a framework not in FRAMEWORK_HANDLERS
        result = load_framework_adapter("openai")
        
        assert result == mock_adapter
        mock_can_handle.assert_called_once_with("openai")
        mock_create_generic.assert_called_once_with("openai")

    @pytest.mark.integration
    @patch('strands_agent_factory.adapters.base._can_handle_generically')
    def test_adapter_loading_no_support(self, mock_can_handle):
        """Test adapter loading when framework is not supported."""
        mock_can_handle.return_value = False
        
        with pytest.raises(AdapterError, match="No adapter available for framework"):
            load_framework_adapter("unsupported_framework")

    @pytest.mark.integration
    def test_generic_adapter_validation_workflow(self):
        """Test the complete generic adapter validation workflow."""
        # Test framework that should be handled generically
        with patch('strands_agent_factory.adapters.generic.GenericFrameworkAdapter._validate_framework_import') as mock_validate_import:
            with patch('strands_agent_factory.adapters.generic.GenericFrameworkAdapter._validate_model_property') as mock_validate_property:
                # Mock successful validation
                from strands.models import Model
                mock_model_class = type('MockModel', (Model,), {})
                mock_validate_import.return_value = (True, mock_model_class)
                mock_validate_property.return_value = True
                
                result = can_handle_generically("test_framework")
                
                assert result is True
                mock_validate_import.assert_called_once_with("test_framework")
                mock_validate_property.assert_called_once_with(mock_model_class)

    @pytest.mark.integration
    def test_generic_adapter_validation_failure_cases(self):
        """Test generic adapter validation failure scenarios."""
        # Test invalid framework ID
        assert can_handle_generically("") is False
        assert can_handle_generically(None) is False
        
        # Test framework requiring custom adapter
        assert can_handle_generically("bedrock") is False
        
        # Test import failure
        with patch('strands_agent_factory.adapters.generic.GenericFrameworkAdapter._validate_framework_import') as mock_validate:
            mock_validate.return_value = (False, None)
            
            result = can_handle_generically("nonexistent_framework")
            assert result is False

    @pytest.mark.integration
    @patch('strands_agent_factory.adapters.generic.importlib.import_module')
    def test_generic_adapter_creation_workflow(self, mock_import):
        """Test the complete generic adapter creation workflow."""
        # Mock successful model class import
        mock_model_class = Mock()
        mock_model_class.__annotations__ = {"model_id": str}
        
        mock_module = Mock()
        mock_module.TestModel = mock_model_class
        mock_import.return_value = mock_module
        
        # Create adapter
        adapter = GenericFrameworkAdapter("test")
        
        assert adapter.framework_name == "test"
        assert adapter._model_class == mock_model_class
        assert adapter._model_property == "model_id"

    @pytest.mark.integration
    @patch('strands_agent_factory.adapters.generic.importlib.import_module')
    def test_generic_adapter_model_loading_integration(self, mock_import):
        """Test model loading through generic adapter."""
        # Mock model class and instance
        mock_model_instance = Mock()
        mock_model_class = Mock(return_value=mock_model_instance)
        mock_model_class.__annotations__ = {"model_id": str}
        
        mock_module = Mock()
        mock_module.TestModel = mock_model_class
        mock_import.return_value = mock_module
        
        # Create adapter and load model
        adapter = GenericFrameworkAdapter("test")
        result = adapter.load_model("test-model", {"temperature": 0.7})
        
        assert result == mock_model_instance
        mock_model_class.assert_called_once_with(model_id="test-model", temperature=0.7)

    @pytest.mark.integration
    def test_adapter_error_propagation(self):
        """Test that errors are properly propagated through the adapter system."""
        # Test explicit adapter loading error
        with patch('strands_agent_factory.adapters.base._load_explicit_adapter') as mock_explicit:
            mock_explicit.side_effect = Exception("Explicit adapter failed")
            
            with patch('strands_agent_factory.adapters.base.FRAMEWORK_HANDLERS', {"test": "test.adapter"}):
                with pytest.raises(AdapterError, match="Failed to load explicit adapter"):
                    load_framework_adapter("test")

        # Test generic adapter creation error
        with patch('strands_agent_factory.adapters.base._can_handle_generically') as mock_can_handle:
            with patch('strands_agent_factory.adapters.base._create_generic_adapter') as mock_create:
                mock_can_handle.return_value = True
                mock_create.side_effect = Exception("Generic adapter failed")
                
                with pytest.raises(AdapterError, match="Failed to create generic adapter"):
                    load_framework_adapter("test")

    @pytest.mark.integration
    @patch('strands_agent_factory.adapters.generic.GenericFrameworkAdapter')
    def test_create_generic_adapter_integration(self, mock_adapter_class):
        """Test the create_generic_adapter function integration."""
        mock_adapter = Mock()
        mock_adapter_class.return_value = mock_adapter
        
        result = create_generic_adapter("test_framework")
        
        assert result == mock_adapter
        mock_adapter_class.assert_called_once_with("test_framework")

    @pytest.mark.integration
    @patch('strands_agent_factory.adapters.generic.GenericFrameworkAdapter')
    def test_create_generic_adapter_error_handling(self, mock_adapter_class):
        """Test error handling in create_generic_adapter."""
        # Test expected errors (should return None)
        mock_adapter_class.side_effect = FrameworkNotSupportedError("Framework not supported")
        
        result = create_generic_adapter("unsupported_framework")
        
        assert result is None

        # Test unexpected errors (should raise wrapped exception)
        mock_adapter_class.side_effect = RuntimeError("Unexpected error")
        
        with pytest.raises(Exception):  # Should be wrapped in GenericAdapterCreationError
            create_generic_adapter("test_framework")

    @pytest.mark.integration
    def test_adapter_framework_name_consistency(self):
        """Test that adapter framework names are consistent."""
        # Test that generic adapters return the correct framework name
        with patch('strands_agent_factory.adapters.generic.importlib.import_module') as mock_import:
            mock_model_class = Mock()
            mock_model_class.__annotations__ = {"model_id": str}
            
            mock_module = Mock()
            mock_module.TestModel = mock_model_class
            mock_import.return_value = mock_module
            
            adapter = GenericFrameworkAdapter("test")
            
            assert adapter.framework_name == "test"

    @pytest.mark.integration
    @patch('importlib.import_module')
    def test_explicit_adapter_loading_integration(self, mock_import):
        """Test explicit adapter loading with real import mechanics."""
        # Mock adapter class
        mock_adapter_class = Mock()
        mock_adapter_instance = Mock()
        mock_adapter_instance.framework_name = "test_framework"
        mock_adapter_class.return_value = mock_adapter_instance
        
        # Mock module
        mock_module = Mock()
        mock_module.TestAdapter = mock_adapter_class
        mock_import.return_value = mock_module
        
        # Test loading
        from strands_agent_factory.adapters.base import _load_explicit_adapter
        
        result = _load_explicit_adapter("test")
        
        assert result == mock_adapter_instance
        mock_adapter_class.assert_called_once()

    @pytest.mark.integration
    def test_adapter_tool_adaptation_integration(self):
        """Test tool adaptation through adapter system."""
        with patch('strands_agent_factory.adapters.generic.importlib.import_module') as mock_import:
            mock_model_class = Mock()
            mock_model_class.__annotations__ = {"model_id": str}
            
            mock_module = Mock()
            mock_module.TestModel = mock_model_class
            mock_import.return_value = mock_module
            
            adapter = GenericFrameworkAdapter("test")
            
            # Test tool adaptation (should use default implementation)
            mock_tools = [Mock(), Mock()]
            result = adapter.adapt_tools(mock_tools, "test:model")
            
            assert result == mock_tools  # Default implementation returns unchanged

    @pytest.mark.integration
    def test_adapter_agent_args_preparation_integration(self):
        """Test agent args preparation through adapter system."""
        with patch('strands_agent_factory.adapters.generic.importlib.import_module') as mock_import:
            mock_model_class = Mock()
            mock_model_class.__annotations__ = {"model_id": str}
            
            mock_module = Mock()
            mock_module.TestModel = mock_model_class
            mock_import.return_value = mock_module
            
            adapter = GenericFrameworkAdapter("test")
            
            # Test agent args preparation
            system_prompt = "Test system prompt"
            messages = [{"role": "user", "content": [{"text": "test"}]}]
            
            result = adapter.prepare_agent_args(
                system_prompt=system_prompt,
                messages=messages,
                emulate_system_prompt=False
            )
            
            expected = {
                "system_prompt": system_prompt,
                "messages": messages
            }
            
            assert result == expected

    @pytest.mark.integration
    def test_adapter_content_adaptation_integration(self):
        """Test content adaptation through adapter system."""
        with patch('strands_agent_factory.adapters.generic.importlib.import_module') as mock_import:
            mock_model_class = Mock()
            mock_model_class.__annotations__ = {"model_id": str}
            
            mock_module = Mock()
            mock_module.TestModel = mock_model_class
            mock_import.return_value = mock_module
            
            adapter = GenericFrameworkAdapter("test")
            
            # Test content adaptation (should use default implementation)
            content = [{"text": "test content"}]
            result = adapter.adapt_content(content)
            
            assert result == content  # Default implementation returns unchanged

    @pytest.mark.integration
    def test_adapter_system_with_multiple_frameworks(self):
        """Test adapter system handling multiple frameworks simultaneously."""
        frameworks_to_test = ["openai", "anthropic", "test_framework"]
        
        with patch('strands_agent_factory.adapters.base._can_handle_generically') as mock_can_handle:
            with patch('strands_agent_factory.adapters.base._create_generic_adapter') as mock_create:
                mock_can_handle.return_value = True
                
                adapters = []
                for framework in frameworks_to_test:
                    mock_adapter = Mock()
                    mock_adapter.framework_name = framework
                    adapters.append(mock_adapter)
                
                mock_create.side_effect = adapters
                
                results = []
                for framework in frameworks_to_test:
                    result = load_framework_adapter(framework)
                    results.append(result)
                
                # Verify each adapter was created correctly
                assert len(results) == len(frameworks_to_test)
                for i, result in enumerate(results):
                    assert result.framework_name == frameworks_to_test[i]