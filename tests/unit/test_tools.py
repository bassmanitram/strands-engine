"""
Unit tests for strands_agent_factory.tools modules.

Tests tool discovery, loading, and factory functionality.
"""

import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from typing import Dict, Any, List

import pytest

from strands_agent_factory.tools.factory import ToolFactory, ToolSpecCreationResult
from strands_agent_factory.tools.python import import_python_item
from strands_agent_factory.core.exceptions import (
    ToolLoadError,
    ConfigurationError
)


class TestPythonToolImport:
    """Test cases for Python tool import functionality."""

    def test_import_python_item_success(self):
        """Test successful Python item import."""
        # Import a real Python function
        result = import_python_item("os.path", "join")
        
        assert callable(result)
        assert result.__name__ == "join"

    def test_import_python_item_module_only(self):
        """Test importing module without specific item."""
        result = import_python_item("os", "path")
        
        assert hasattr(result, 'join')
        assert hasattr(result, 'exists')

    def test_import_python_item_nonexistent_module(self):
        """Test importing nonexistent module."""
        with pytest.raises(ImportError, match="Cannot load nonexistent_module"):
            import_python_item("nonexistent_module", "function")

    def test_import_python_item_nonexistent_attribute(self):
        """Test importing nonexistent attribute from valid module."""
        with pytest.raises(ImportError, match="Cannot load os.nonexistent_function"):
            import_python_item("os", "nonexistent_function")

    @patch('importlib.import_module')
    def test_import_python_item_import_error(self, mock_import):
        """Test handling import errors."""
        mock_import.side_effect = ImportError("Module not found")
        
        with pytest.raises(ImportError, match="Cannot load test.module.function"):
            import_python_item("test.module", "function")

    def test_import_python_item_with_custom_path(self):
        """Test importing with custom package path."""
        # Create a temporary Python file
        with tempfile.TemporaryDirectory() as temp_dir:
            module_dir = Path(temp_dir) / "test_package"
            module_dir.mkdir()
            
            # Create a simple Python module
            module_file = module_dir / "test_module.py"
            module_file.write_text("""
def test_function():
    return "test_result"

TEST_CONSTANT = "test_value"
""")
            
            # Test importing function from custom path
            result = import_python_item(
                "test_package.test_module", 
                "test_function",
                package_path=".",
                base_path=temp_dir
            )
            
            assert callable(result)
            assert result() == "test_result"

    def test_import_python_item_custom_path_nonexistent_file(self):
        """Test importing with custom path when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            import_python_item(
                "nonexistent.module",
                "function",
                package_path=".",
                base_path="/tmp"
            )


class TestToolFactory:
    """Test cases for ToolFactory functionality."""

    def test_tool_factory_init_empty(self):
        """Test ToolFactory initialization with empty file list."""
        factory = ToolFactory([])
        
        assert factory is not None
        assert factory._tool_configs == []

    def test_tool_factory_init_none(self):
        """Test ToolFactory initialization with None."""
        factory = ToolFactory(None)
        
        assert factory is not None
        assert factory._tool_configs == []

    @patch('strands_agent_factory.tools.factory.load_structured_file')
    def test_tool_factory_init_with_configs(self, mock_load_file):
        """Test ToolFactory initialization with configuration files."""
        mock_config = {
            "id": "test_tool",
            "type": "python",
            "module_path": "test.module",
            "functions": ["test_func"]
        }
        mock_load_file.return_value = mock_config
        
        factory = ToolFactory(["/path/to/config.json"])
        
        assert len(factory._tool_configs) == 1
        assert factory._tool_configs[0]["id"] == "test_tool"
        mock_load_file.assert_called_once()

    @patch('strands_agent_factory.tools.factory.load_structured_file')
    def test_tool_factory_init_with_failed_config(self, mock_load_file):
        """Test ToolFactory initialization with failed configuration loading."""
        mock_load_file.side_effect = Exception("File not found")
        
        factory = ToolFactory(["/path/to/bad_config.json"])
        
        # Should handle the error gracefully
        assert factory._tool_configs == []

    def test_create_tool_specs_empty(self):
        """Test creating tool specs with no configurations."""
        factory = ToolFactory([])
        
        discovery_result, creation_results = factory.create_tool_specs()
        
        assert discovery_result is None
        assert creation_results == []

    @patch('strands_agent_factory.tools.factory.import_python_item')
    def test_create_python_tool_spec_success(self, mock_import):
        """Test successful Python tool spec creation."""
        mock_function = Mock()
        mock_function.__name__ = "test_func"
        mock_import.return_value = mock_function
        
        config = {
            "id": "test_tool",
            "type": "python",
            "module_path": "test.module",
            "functions": ["test_func"],
            "source_file": "/path/to/config.json"
        }
        
        factory = ToolFactory([])
        result = factory._create_python_tool_spec(config)
        
        assert result.error is None
        assert result.tool_spec is not None
        assert len(result.tool_spec["tools"]) == 1
        assert result.requested_functions == ["test_func"]

    def test_create_python_tool_spec_missing_fields(self):
        """Test Python tool spec creation with missing required fields."""
        config = {
            "id": "test_tool",
            "type": "python"
            # Missing required fields
        }
        
        factory = ToolFactory([])
        result = factory._create_python_tool_spec(config)
        
        assert result.error is not None
        assert "missing required fields" in result.error
        assert result.tool_spec is None

    @patch('strands_agent_factory.tools.factory.import_python_item')
    def test_create_python_tool_spec_import_failure(self, mock_import):
        """Test Python tool spec creation with import failure."""
        mock_import.side_effect = ImportError("Module not found")
        
        config = {
            "id": "test_tool",
            "type": "python",
            "module_path": "nonexistent.module",
            "functions": ["test_func"],
            "source_file": "/path/to/config.json"
        }
        
        factory = ToolFactory([])
        result = factory._create_python_tool_spec(config)
        
        assert result.error is not None
        assert "No tools could be loaded" in result.error
        assert result.tool_spec is None

    @patch('strands_agent_factory.tools.factory._STRANDS_MCP_AVAILABLE', True)
    @patch('strands_agent_factory.tools.factory.MCPClient')
    def test_create_mcp_tool_spec_success(self, mock_mcp_client):
        """Test successful MCP tool spec creation."""
        mock_client_instance = Mock()
        mock_mcp_client.return_value = mock_client_instance
        
        config = {
            "id": "test_mcp_tool",
            "type": "mcp",
            "command": ["test-server"],
            "functions": ["test_func"]
        }
        
        factory = ToolFactory([])
        
        with patch.object(factory, '_create_stdio_transport') as mock_transport:
            mock_transport.return_value = Mock()
            result = factory._create_mcp_tool_spec(config)
        
        assert result.error is None
        assert result.tool_spec is not None
        assert result.tool_spec["client"] == mock_client_instance
        assert result.requested_functions == ["test_func"]

    @patch('strands_agent_factory.tools.factory._STRANDS_MCP_AVAILABLE', False)
    def test_create_mcp_tool_spec_dependencies_unavailable(self):
        """Test MCP tool spec creation when dependencies are unavailable."""
        config = {
            "id": "test_mcp_tool",
            "type": "mcp",
            "command": ["test-server"],
            "functions": ["test_func"]
        }
        
        factory = ToolFactory([])
        result = factory._create_mcp_tool_spec(config)
        
        assert result.error is not None
        assert "MCP dependencies not installed" in result.error
        assert result.tool_spec is None

    def test_create_mcp_tool_spec_missing_transport(self):
        """Test MCP tool spec creation with missing transport configuration."""
        config = {
            "id": "test_mcp_tool",
            "type": "mcp",
            "functions": ["test_func"]
            # Missing command or url
        }
        
        factory = ToolFactory([])
        result = factory._create_mcp_tool_spec(config)
        
        assert result.error is not None
        assert "must contain either 'command'" in result.error
        assert result.tool_spec is None

    def test_create_tool_spec_from_config_unknown_type(self):
        """Test tool spec creation with unknown tool type."""
        config = {
            "id": "test_tool",
            "type": "unknown_type"
        }
        
        factory = ToolFactory([])
        result = factory.create_tool_spec_from_config(config)
        
        assert result.error is not None
        assert "Unknown tool type" in result.error
        assert result.tool_spec is None

    def test_create_tool_spec_from_config_disabled_tool(self):
        """Test that disabled tools are skipped."""
        config = {
            "id": "disabled_tool",
            "type": "python",
            "disabled": True,
            "module_path": "test.module",
            "functions": ["test_func"],
            "source_file": "/path/to/config.json"
        }
        
        factory = ToolFactory([])
        factory._tool_configs = [config]
        
        discovery_result, creation_results = factory.create_tool_specs()
        
        # Disabled tool should be skipped
        assert len(creation_results) == 0

    @patch('mcp.StdioServerParameters')
    @patch('mcp.client.stdio.stdio_client')
    def test_create_stdio_transport(self, mock_stdio_client, mock_params):
        """Test stdio transport creation."""
        config = {
            "command": ["test-server"],
            "args": ["--verbose"],
            "env": {"TEST_VAR": "test_value"}
        }
        
        factory = ToolFactory([])
        transport_callable = factory._create_stdio_transport(config)
        
        assert callable(transport_callable)
        mock_params.assert_called_once()

    @patch('mcp.client.streamable_http.streamablehttp_client')
    def test_create_http_transport(self, mock_http_client):
        """Test HTTP transport creation."""
        config = {
            "url": "http://localhost:8000/mcp"
        }
        
        factory = ToolFactory([])
        transport_callable = factory._create_http_transport(config)
        
        assert callable(transport_callable)

    def test_tool_spec_creation_result_init(self):
        """Test ToolSpecCreationResult initialization."""
        # Test with all parameters
        mock_tool_spec = {"tools": [Mock()]}
        result = ToolSpecCreationResult(
            tool_spec=mock_tool_spec,
            requested_functions=["func1", "func2"],
            error="test error"
        )
        
        assert result.tool_spec == mock_tool_spec
        assert result.requested_functions == ["func1", "func2"]
        assert result.error == "test error"

    def test_tool_spec_creation_result_defaults(self):
        """Test ToolSpecCreationResult with default values."""
        result = ToolSpecCreationResult()
        
        assert result.tool_spec is None
        assert result.requested_functions == []
        assert result.error is None

    @patch('strands_agent_factory.tools.factory._STRANDS_MCP_AVAILABLE', True)
    def test_mcp_client_init(self):
        """Test MCPClient initialization."""
        from strands_agent_factory.tools.factory import MCPClient
        
        mock_transport = Mock()
        
        with patch('strands_agent_factory.tools.factory.StrandsMCPClient.__init__', return_value=None):
            client = MCPClient("test_server", mock_transport, ["func1", "func2"])
        
        assert client.server_id == "test_server"
        assert client.requested_functions == ["func1", "func2"]

    @patch('strands_agent_factory.tools.factory._STRANDS_MCP_AVAILABLE', True)
    def test_mcp_client_list_tools_sync_filtered(self):
        """Test MCPClient list_tools_sync with filtering."""
        from strands_agent_factory.tools.factory import MCPClient
        
        mock_transport = Mock()
        mock_tool1 = Mock()
        mock_tool1.tool_name = "func1"
        mock_tool2 = Mock()
        mock_tool2.tool_name = "func2"
        mock_tool3 = Mock()
        mock_tool3.tool_name = "func3"
        
        with patch('strands_agent_factory.tools.factory.StrandsMCPClient.__init__', return_value=None):
            with patch('strands_agent_factory.tools.factory.StrandsMCPClient.list_tools_sync') as mock_list:
                mock_list.return_value = [mock_tool1, mock_tool2, mock_tool3]
                
                client = MCPClient("test_server", mock_transport, ["func1", "func3"])
                result = client.list_tools_sync()
        
        # Should return only requested functions
        assert len(result) == 2
        assert mock_tool1 in result
        assert mock_tool3 in result
        assert mock_tool2 not in result

    @patch('strands_agent_factory.tools.factory._STRANDS_MCP_AVAILABLE', True)
    def test_mcp_client_list_tools_sync_unfiltered(self):
        """Test MCPClient list_tools_sync without filtering."""
        from strands_agent_factory.tools.factory import MCPClient
        
        mock_transport = Mock()
        mock_tools = [Mock(), Mock(), Mock()]
        
        with patch('strands_agent_factory.tools.factory.StrandsMCPClient.__init__', return_value=None):
            with patch('strands_agent_factory.tools.factory.StrandsMCPClient.list_tools_sync') as mock_list:
                mock_list.return_value = mock_tools
                
                client = MCPClient("test_server", mock_transport, [])
                result = client.list_tools_sync()
        
        # Should return all tools when no filtering requested
        assert result == mock_tools