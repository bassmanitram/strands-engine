"""
Tests for strands_engine tool factory and adapters.
"""

import pytest
import tempfile
import json
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch, MagicMock

from strands_engine.tools import ToolFactory, discover_tool_configs
from strands_engine.tools.python_adapter import PythonToolAdapter
from strands_engine.tools.mcp_adapters import MCPStdIOAdapter, MCPHTTPAdapter
from strands_engine.ptypes import ToolCreationResult


class TestToolDiscovery:
    """Test tool configuration discovery."""
    
    def test_discover_no_paths(self):
        """Test discovery with no paths provided."""
        configs, result = discover_tool_configs(None)
        
        assert configs == []
        assert result.successful_configs == []
        assert result.failed_configs == []
        assert result.total_files_scanned == 0
    
    def test_discover_empty_paths(self):
        """Test discovery with empty path list."""
        configs, result = discover_tool_configs([])
        
        assert configs == []
        assert result.successful_configs == []
        assert result.failed_configs == []
        assert result.total_files_scanned == 0
    
    def test_discover_nonexistent_path(self):
        """Test discovery with nonexistent directory."""
        configs, result = discover_tool_configs(["/nonexistent/path"])
        
        assert configs == []
        assert result.successful_configs == []
        assert result.failed_configs == []
        assert result.total_files_scanned == 0
    
    def test_discover_valid_tool_config(self):
        """Test discovery with valid tool configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a valid tool config file
            tool_config = {
                "id": "test_tool",
                "type": "python",
                "module_path": "test_module",
                "functions": ["test_function"],
                "disabled": False
            }
            
            config_file = Path(temp_dir) / "test.tools.json"
            with open(config_file, 'w') as f:
                json.dump(tool_config, f)
            
            configs, result = discover_tool_configs([temp_dir])
            
            assert len(configs) == 1
            assert configs[0]["id"] == "test_tool"
            assert configs[0]["type"] == "python"
            assert "source_file" in configs[0]
            assert result.total_files_scanned == 1
            assert len(result.successful_configs) == 1
            assert len(result.failed_configs) == 0
    
    def test_discover_invalid_tool_config(self):
        """Test discovery with invalid tool configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create an invalid tool config file (missing required fields)
            tool_config = {
                "id": "test_tool"
                # Missing "type" field
            }
            
            config_file = Path(temp_dir) / "invalid.tools.json"
            with open(config_file, 'w') as f:
                json.dump(tool_config, f)
            
            configs, result = discover_tool_configs([temp_dir])
            
            assert len(configs) == 0
            assert result.total_files_scanned == 1
            assert len(result.successful_configs) == 0
            assert len(result.failed_configs) == 1
            assert "missing required field 'type'" in result.failed_configs[0]["error"]
    
    def test_discover_malformed_json(self):
        """Test discovery with malformed JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "malformed.tools.json"
            with open(config_file, 'w') as f:
                f.write("{ invalid json")
            
            configs, result = discover_tool_configs([temp_dir])
            
            assert len(configs) == 0
            assert result.total_files_scanned == 1
            assert len(result.successful_configs) == 0
            assert len(result.failed_configs) == 1
            assert "JSON parsing error" in result.failed_configs[0]["error"]


class TestToolFactory:
    """Test tool factory functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.exit_stack = ExitStack()
        self.factory = ToolFactory(self.exit_stack)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.exit_stack.close()
    
    def test_factory_creation(self):
        """Test tool factory creation."""
        assert self.factory is not None
        supported_types = self.factory.get_supported_types()
        assert "python" in supported_types
        assert "mcp-stdio" in supported_types
        assert "mcp-http" in supported_types
    
    def test_unknown_tool_type(self):
        """Test handling of unknown tool type."""
        config = {
            "id": "unknown_tool",
            "type": "unknown_type"
        }
        
        result = self.factory.create_tools(config)
        
        assert result.tools == []
        assert result.error == "Unknown tool type 'unknown_type'"
        assert result.requested_functions == []
        assert result.found_functions == []
        assert result.missing_functions == []
    
    def test_mcp_type_disambiguation(self):
        """Test MCP type disambiguation between stdio and http."""
        # Test stdio detection
        stdio_config = {
            "id": "mcp_stdio",
            "type": "mcp",
            "command": "test_command"
        }
        
        with patch.object(self.factory._adapters["mcp-stdio"], "create") as mock_stdio_create:
            mock_stdio_create.return_value = ToolCreationResult([], [], [], [], None)
            self.factory.create_tools(stdio_config)
            mock_stdio_create.assert_called_once_with(stdio_config)
        
        # Test http detection
        http_config = {
            "id": "mcp_http",
            "type": "mcp",
            "url": "http://test.example.com"
        }
        
        with patch.object(self.factory._adapters["mcp-http"], "create") as mock_http_create:
            mock_http_create.return_value = ToolCreationResult([], [], [], [], None)
            self.factory.create_tools(http_config)
            mock_http_create.assert_called_once_with(http_config)
    
    def test_mcp_missing_connection_info(self):
        """Test MCP config missing connection information."""
        config = {
            "id": "invalid_mcp",
            "type": "mcp"
            # Missing both "command" and "url"
        }
        
        result = self.factory.create_tools(config)
        
        assert result.tools == []
        assert "missing 'url' or 'command'" in result.error
    
    def test_register_adapter(self):
        """Test registering a new adapter."""
        mock_adapter = MagicMock()
        
        self.factory.register_adapter("custom", mock_adapter)
        
        assert "custom" in self.factory.get_supported_types()
        assert self.factory._adapters["custom"] is mock_adapter


class TestPythonToolAdapter:
    """Test Python tool adapter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.exit_stack = ExitStack()
        self.adapter = PythonToolAdapter(self.exit_stack)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.exit_stack.close()
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        config = {
            "id": "incomplete_python"
            # Missing required fields
        }
        
        result = self.adapter.create(config)
        
        assert result.tools == []
        assert "Missing required configuration fields" in result.error
        assert result.requested_functions == []
        assert result.found_functions == []
        assert result.missing_functions == []
    
    def test_successful_function_loading(self):
        """Test successful function loading."""
        config = {
            "id": "test_python",
            "module_path": "os.path",
            "functions": ["exists"],
            "source_file": "/tmp/test.py"
        }
        
        result = self.adapter.create(config)
        
        # Should successfully load os.path.exists
        assert len(result.tools) == 1
        assert callable(result.tools[0])
        assert result.error is None
        assert result.requested_functions == ["exists"]
        assert result.found_functions == ["exists"]
        assert result.missing_functions == []
    
    def test_missing_function(self):
        """Test handling of missing function."""
        config = {
            "id": "test_python",
            "module_path": "os.path",
            "functions": ["nonexistent_function"],
            "source_file": "/tmp/test.py"
        }
        
        result = self.adapter.create(config)
        
        assert result.tools == []
        assert result.error is None  # Not a fatal error
        assert result.requested_functions == ["nonexistent_function"]
        assert result.found_functions == []
        assert result.missing_functions == ["nonexistent_function"]
    
    def test_mixed_success_failure(self):
        """Test mixed success and failure loading."""
        config = {
            "id": "test_python",
            "module_path": "os.path",
            "functions": ["exists", "nonexistent_function"],
            "source_file": "/tmp/test.py"
        }
        
        result = self.adapter.create(config)
        
        assert len(result.tools) == 1  # Only one successful
        assert callable(result.tools[0])
        assert result.error is None
        assert result.requested_functions == ["exists", "nonexistent_function"]
        assert result.found_functions == ["exists"]
        assert result.missing_functions == ["nonexistent_function"]


class TestMCPAdapters:
    """Test MCP tool adapters - basic functionality only."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.exit_stack = ExitStack()
        self.stdio_adapter = MCPStdIOAdapter(self.exit_stack)
        self.http_adapter = MCPHTTPAdapter(self.exit_stack)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.exit_stack.close()
    
    def test_mcp_adapters_creation(self):
        """Test that MCP adapters can be created."""
        assert self.stdio_adapter is not None
        assert self.http_adapter is not None
        assert hasattr(self.stdio_adapter, 'create')
        assert hasattr(self.http_adapter, 'create')
    
    def test_mcp_stdio_config_handling(self):
        """Test MCP stdio adapter handles config appropriately."""
        config = {
            "id": "test_mcp",
            "command": "nonexistent_command"  # This will fail but that's expected
        }
        
        result = self.stdio_adapter.create(config)
        
        # Should return a valid ToolCreationResult regardless of success/failure
        assert isinstance(result, ToolCreationResult)
        assert isinstance(result.tools, list)
        assert isinstance(result.requested_functions, list)
        assert isinstance(result.found_functions, list)
        assert isinstance(result.missing_functions, list)
    
    def test_mcp_http_config_handling(self):
        """Test MCP HTTP adapter handles config appropriately."""
        config = {
            "id": "test_mcp_http", 
            "url": "http://nonexistent.example.com"  # This will fail but that's expected
        }
        
        result = self.http_adapter.create(config)
        
        # Should return a valid ToolCreationResult regardless of success/failure
        assert isinstance(result, ToolCreationResult)
        assert isinstance(result.tools, list)
        assert isinstance(result.requested_functions, list)
        assert isinstance(result.found_functions, list)
        assert isinstance(result.missing_functions, list)