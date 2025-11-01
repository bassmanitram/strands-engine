"""
Unit tests for strands_agent_factory.tools modules.

Tests tool discovery, loading, and factory functionality.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from strands_agent_factory.core.exceptions import ConfigurationError, ToolLoadError
from strands_agent_factory.tools.factory import ToolFactory
from strands_agent_factory.tools.python import import_python_item


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

        assert hasattr(result, "join")
        assert hasattr(result, "exists")

    def test_import_python_item_nonexistent_module(self):
        """Test importing nonexistent module."""
        with pytest.raises(ImportError, match="Cannot load nonexistent_module"):
            import_python_item("nonexistent_module", "function")

    def test_import_python_item_nonexistent_attribute(self):
        """Test importing nonexistent attribute from valid module."""
        with pytest.raises(ImportError, match="Cannot load os.nonexistent_function"):
            import_python_item("os", "nonexistent_function")

    @patch("importlib.import_module")
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
            module_file.write_text(
                """
def test_function():
    return "test_result"

TEST_CONSTANT = "test_value"
"""
            )

            # Test importing function from custom path
            result = import_python_item(
                "test_package.test_module",
                "test_function",
                package_path=".",
                base_path=temp_dir,
            )

            assert callable(result)
            assert result() == "test_result"

    def test_import_python_item_custom_path_nonexistent_file(self):
        """Test importing with custom path when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            import_python_item(
                "nonexistent.module", "function", package_path=".", base_path="/tmp"
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

    @patch("strands_agent_factory.tools.factory.load_structured_file")
    def test_tool_factory_init_with_configs(self, mock_load_file):
        """Test ToolFactory initialization with configuration files."""
        mock_config = {
            "id": "test_tool",
            "type": "python",
            "module_path": "test.module",
            "functions": ["test_func"],
        }
        mock_load_file.return_value = mock_config

        factory = ToolFactory(["/path/to/config.json"])

        assert len(factory._tool_configs) == 1
        assert factory._tool_configs[0]["id"] == "test_tool"
        mock_load_file.assert_called_once()

    @patch("strands_agent_factory.tools.factory.load_structured_file")
    def test_tool_factory_init_with_failed_config(self, mock_load_file):
        """Test ToolFactory initialization with failed configuration loading."""
        mock_load_file.side_effect = Exception("File not found")

        factory = ToolFactory(["/path/to/bad_config.json"])

        # Should handle the error gracefully and store error info
        assert len(factory._tool_configs) == 1
        assert factory._tool_configs[0]["error"] == "File not found"
        assert "failed-config-" in factory._tool_configs[0]["id"]

    def test_create_tool_specs_empty(self):
        """Test creating tool specs with no configurations."""
        factory = ToolFactory([])

        creation_results = factory.create_tool_specs()

        assert creation_results == []

    @patch("strands_agent_factory.tools.factory.import_python_item")
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
            "source_file": "/path/to/config.json",
        }

        factory = ToolFactory([])
        result = factory._create_python_tool_spec(config)

        assert "error" not in result
        assert "tools" in result
        assert len(result["tools"]) == 1

    def test_create_python_tool_spec_missing_fields(self):
        """Test Python tool spec creation with missing required fields."""
        config = {
            "id": "test_tool",
            "type": "python",
            # Missing required fields
        }

        factory = ToolFactory([])
        result = factory._create_python_tool_spec(config)

        assert "error" in result
        assert "missing required fields" in result["error"]

    @patch("strands_agent_factory.tools.factory.import_python_item")
    def test_create_python_tool_spec_import_failure(self, mock_import):
        """Test Python tool spec creation with import failure."""
        mock_import.side_effect = ImportError("Module not found")

        config = {
            "id": "test_tool",
            "type": "python",
            "module_path": "nonexistent.module",
            "functions": ["test_func"],
            "source_file": "/path/to/config.json",
        }

        factory = ToolFactory([])
        result = factory._create_python_tool_spec(config)

        assert "error" in result
        assert "No tools could be loaded" in result["error"]

    @patch("strands_agent_factory.tools.mcp._STRANDS_MCP_AVAILABLE", True)
    @patch("strands_agent_factory.tools.mcp.MCPClient")
    def test_create_mcp_tool_spec_success(self, mock_mcp_client):
        """Test successful MCP tool spec creation."""
        mock_client_instance = Mock()
        mock_mcp_client.return_value = mock_client_instance

        config = {
            "id": "test_mcp_tool",
            "type": "mcp",
            "command": "test-server",  # Use string instead of list
            "functions": ["test_func"],
        }

        factory = ToolFactory([])
        result = factory.create_tool_from_config(config)  # Use public method

        assert "error" not in result
        assert "tools" in result or "client" in result

    @patch("strands_agent_factory.tools.mcp._STRANDS_MCP_AVAILABLE", False)
    def test_create_mcp_tool_spec_dependencies_unavailable(self):
        """Test MCP tool spec creation when dependencies are unavailable."""
        config = {
            "id": "test_mcp_tool",
            "type": "mcp",
            "command": "test-server",
            "functions": ["test_func"],
        }

        factory = ToolFactory([])
        result = factory.create_tool_from_config(config)  # Use public method

        assert "error" in result
        assert "MCP dependencies not installed" in result["error"]

    def test_create_mcp_tool_spec_missing_transport(self):
        """Test MCP tool spec creation with missing transport configuration."""
        config = {
            "id": "test_mcp_tool",
            "type": "mcp",
            "functions": ["test_func"],
            # Missing command or url
        }

        factory = ToolFactory([])
        result = factory.create_tool_from_config(config)  # Use public method

        assert "error" in result
        assert "must contain either 'command'" in result["error"]

    def test_create_tool_spec_from_config_unknown_type(self):
        """Test tool spec creation with unknown tool type."""
        config = {"id": "test_tool", "type": "unknown_type"}

        factory = ToolFactory([])
        result = factory.create_tool_from_config(config)

        assert "error" in result
        assert "Unknown tool type" in result["error"]

    def test_create_tool_spec_from_config_disabled_tool(self):
        """Test that disabled tools are handled properly."""
        config = {
            "id": "disabled_tool",
            "type": "python",
            "disabled": True,
            "module_path": "test.module",
            "functions": ["test_func"],
            "source_file": "/path/to/config.json",
        }

        factory = ToolFactory([])
        factory._tool_configs = [config]

        creation_results = factory.create_tool_specs()

        # Disabled tool should be included with error
        assert len(creation_results) == 1
        assert creation_results[0]["error"] == "Tool is disabled"

    @patch("strands_agent_factory.tools.mcp._STRANDS_MCP_AVAILABLE", True)
    def test_mcp_client_init(self):
        """Test MCPClient initialization."""
        from strands_agent_factory.tools.mcp import MCPClient

        mock_transport = Mock()

        with patch(
            "strands_agent_factory.tools.mcp.StrandsMCPClient.__init__",
            return_value=None,
        ):
            client = MCPClient("test_server", mock_transport, ["func1", "func2"])

        assert client.server_id == "test_server"
        assert client.requested_functions == ["func1", "func2"]

    @patch("strands_agent_factory.tools.mcp._STRANDS_MCP_AVAILABLE", True)
    def test_mcp_client_list_tools_sync_filtered(self):
        """Test MCPClient list_tools_sync with filtering."""
        from strands_agent_factory.tools.mcp import MCPClient

        mock_transport = Mock()
        mock_tool1 = Mock()
        mock_tool1.tool_name = "func1"
        mock_tool2 = Mock()
        mock_tool2.tool_name = "func2"
        mock_tool3 = Mock()
        mock_tool3.tool_name = "func3"

        with patch(
            "strands_agent_factory.tools.mcp.StrandsMCPClient.__init__",
            return_value=None,
        ):
            with patch(
                "strands_agent_factory.tools.mcp.StrandsMCPClient.list_tools_sync"
            ) as mock_list:
                mock_list.return_value = [mock_tool1, mock_tool2, mock_tool3]

                client = MCPClient("test_server", mock_transport, ["func1", "func3"])
                result = client.list_tools_sync()

        # Should return only requested functions
        assert len(result) == 2
        assert mock_tool1 in result
        assert mock_tool3 in result
        assert mock_tool2 not in result

    @patch("strands_agent_factory.tools.mcp._STRANDS_MCP_AVAILABLE", True)
    def test_mcp_client_list_tools_sync_unfiltered(self):
        """Test MCPClient list_tools_sync without filtering."""
        from strands_agent_factory.tools.mcp import MCPClient

        mock_transport = Mock()
        mock_tools = [Mock(), Mock(), Mock()]

        with patch(
            "strands_agent_factory.tools.mcp.StrandsMCPClient.__init__",
            return_value=None,
        ):
            with patch(
                "strands_agent_factory.tools.mcp.StrandsMCPClient.list_tools_sync"
            ) as mock_list:
                mock_list.return_value = mock_tools

                client = MCPClient("test_server", mock_transport, [])
                result = client.list_tools_sync()

        # Should return all tools when no filtering requested
        assert result == mock_tools
