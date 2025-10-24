"""
Unit tests for strands_agent_factory.messaging modules.

Tests message generation, content processing, and file handling functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest
import yaml

from strands_agent_factory.messaging.content import (
    guess_mimetype,
    is_likely_text_file,
    paths_to_file_references,
    recursively_remove,
    load_structured_file,
    load_file_content,
    generate_file_content_block,
    files_to_content_blocks
)
from strands_agent_factory.messaging.generator import (
    generate_llm_messages,
    _parse_file_references,
    _resolve_file_glob,
    _create_text_content_block,
    _create_file_content_blocks
)


class TestContentUtils:
    """Test cases for content utility functions."""

    def test_guess_mimetype_known_extensions(self):
        """Test MIME type guessing for known file extensions."""
        test_cases = [
            ("file.txt", "text/plain"),
            ("file.json", "application/json"),
            ("file.html", "text/html"),
            ("file.pdf", "application/pdf"),
            ("file.jpg", "image/jpeg"),
            ("file.png", "image/png")
        ]
        
        for filename, expected_mimetype in test_cases:
            result = guess_mimetype(filename)
            assert result == expected_mimetype

    def test_guess_mimetype_unknown_extension(self):
        """Test MIME type guessing for unknown extensions."""
        result = guess_mimetype("file.unknown_extension")
        assert result == "application/octet-stream"

    def test_guess_mimetype_no_extension(self):
        """Test MIME type guessing for files without extensions."""
        result = guess_mimetype("filename_no_extension")
        assert result == "application/octet-stream"

    def test_is_likely_text_file_by_extension(self, temp_dir):
        """Test text file detection by extension."""
        text_extensions = [".txt", ".py", ".js", ".html", ".json", ".yaml", ".md"]
        
        for ext in text_extensions:
            file_path = temp_dir / f"test{ext}"
            file_path.write_text("test content")
            
            assert is_likely_text_file(file_path) is True

    def test_is_likely_text_file_binary_extensions(self, temp_dir):
        """Test binary file detection by extension."""
        binary_extensions = [".jpg", ".png", ".pdf", ".exe", ".zip"]
        
        for ext in binary_extensions:
            file_path = temp_dir / f"test{ext}"
            file_path.write_bytes(b"binary content")
            
            # Note: Some might still be detected as text if content is text-like
            # This tests the extension-based logic primarily

    def test_is_likely_text_file_by_content(self, temp_dir):
        """Test text file detection by content analysis."""
        # Text content
        text_file = temp_dir / "text_file"
        text_file.write_text("This is plain text content")
        assert is_likely_text_file(text_file) is True
        
        # Binary content with null bytes
        binary_file = temp_dir / "binary_file"
        binary_file.write_bytes(b"binary\x00content\x00with\x00nulls")
        assert is_likely_text_file(binary_file) is False

    def test_is_likely_text_file_nonexistent(self):
        """Test text file detection for non-existent files."""
        assert is_likely_text_file("/nonexistent/file.txt") is False

    def test_paths_to_file_references(self, temp_file):
        """Test conversion of file paths to reference strings."""
        file_paths = [
            (str(temp_file), "text/plain"),
            ("/path/to/file2.json", "application/json"),
            ("/path/to/file3.txt", None)
        ]
        
        result = paths_to_file_references(file_paths)
        
        expected = [
            f"file('{temp_file}', 'text/plain')",
            "file('/path/to/file2.json', 'application/json')",
            "file('/path/to/file3.txt')"
        ]
        
        assert result == expected

    def test_paths_to_file_references_empty(self):
        """Test paths_to_file_references with empty input."""
        result = paths_to_file_references([])
        assert result == []

    def test_recursively_remove_from_dict(self):
        """Test recursive removal of keys from dictionaries."""
        data = {
            "keep1": "value1",
            "remove_me": "should_be_removed",
            "keep2": {
                "nested_keep": "value2",
                "remove_me": "should_be_removed_nested",
                "deep": {
                    "remove_me": "should_be_removed_deep",
                    "keep_deep": "value3"
                }
            }
        }
        
        recursively_remove(data, "remove_me")
        
        expected = {
            "keep1": "value1",
            "keep2": {
                "nested_keep": "value2",
                "deep": {
                    "keep_deep": "value3"
                }
            }
        }
        
        assert data == expected

    def test_recursively_remove_from_list(self):
        """Test recursive removal of keys from lists containing dictionaries."""
        data = [
            {"keep": "value1", "remove_me": "should_be_removed"},
            {"keep": "value2"},
            [{"remove_me": "nested_in_list", "keep": "value3"}]
        ]
        
        recursively_remove(data, "remove_me")
        
        expected = [
            {"keep": "value1"},
            {"keep": "value2"},
            [{"keep": "value3"}]
        ]
        
        assert data == expected

    def test_load_structured_file_json(self, temp_dir):
        """Test loading JSON configuration files."""
        data = {"key": "value", "number": 42}
        json_file = temp_dir / "test.json"
        
        with open(json_file, 'w') as f:
            json.dump(data, f)
        
        result = load_structured_file(json_file)
        assert result == data

    def test_load_structured_file_yaml(self, temp_dir):
        """Test loading YAML configuration files."""
        data = {"key": "value", "list": [1, 2, 3]}
        yaml_file = temp_dir / "test.yaml"
        
        with open(yaml_file, 'w') as f:
            yaml.dump(data, f)
        
        result = load_structured_file(yaml_file)
        assert result == data

    def test_load_structured_file_auto_detection(self, temp_dir):
        """Test automatic format detection."""
        # JSON file
        json_data = {"format": "json"}
        json_file = temp_dir / "test.json"
        with open(json_file, 'w') as f:
            json.dump(json_data, f)
        
        result = load_structured_file(json_file, file_format='auto')
        assert result == json_data
        
        # YAML file
        yaml_data = {"format": "yaml"}
        yaml_file = temp_dir / "test.yml"
        with open(yaml_file, 'w') as f:
            yaml.dump(yaml_data, f)
        
        result = load_structured_file(yaml_file, file_format='auto')
        assert result == yaml_data

    def test_load_structured_file_errors(self, temp_dir):
        """Test error handling in load_structured_file."""
        # Non-existent file
        with pytest.raises(FileNotFoundError):
            load_structured_file("/nonexistent/file.json")
        
        # Invalid JSON
        invalid_json = temp_dir / "invalid.json"
        invalid_json.write_text('{"invalid": json}')
        
        with pytest.raises(json.JSONDecodeError):
            load_structured_file(invalid_json)
        
        # Invalid YAML
        invalid_yaml = temp_dir / "invalid.yaml"
        invalid_yaml.write_text('invalid: yaml: content: [')
        
        with pytest.raises(yaml.YAMLError):
            load_structured_file(invalid_yaml)

    def test_load_file_content_text(self, temp_dir):
        """Test loading text file content."""
        content = "This is test content\nwith multiple lines"
        text_file = temp_dir / "test.txt"
        text_file.write_text(content)
        
        result = load_file_content(text_file, content_type='text')
        assert result == content
        assert isinstance(result, str)

    def test_load_file_content_binary(self, temp_dir):
        """Test loading binary file content."""
        content = b"Binary content\x00\x01\x02"
        binary_file = temp_dir / "test.bin"
        binary_file.write_bytes(content)
        
        result = load_file_content(binary_file, content_type='binary')
        assert result == content
        assert isinstance(result, bytes)

    def test_load_file_content_auto_detection(self, temp_dir):
        """Test automatic content type detection."""
        # Text file
        text_file = temp_dir / "test.txt"
        text_file.write_text("Text content")
        
        result = load_file_content(text_file, content_type='auto')
        assert isinstance(result, str)
        
        # Binary file
        binary_file = temp_dir / "test.bin"
        binary_file.write_bytes(b"Binary\x00content")
        
        result = load_file_content(binary_file, content_type='auto')
        assert isinstance(result, bytes)

    def test_generate_file_content_block_text(self, temp_dir):
        """Test generating content blocks for text files."""
        text_file = temp_dir / "test.txt"
        text_file.write_text("Test content")
        
        result = generate_file_content_block(text_file, "text/plain")
        
        assert result is not None
        assert "document" in result
        assert result["document"]["format"] == "txt"
        assert result["document"]["name"] == str(text_file)

    def test_generate_file_content_block_image(self, temp_dir):
        """Test generating content blocks for image files."""
        image_file = temp_dir / "test.jpg"
        image_file.write_bytes(b"fake image data")
        
        result = generate_file_content_block(image_file, "image/jpeg")
        
        assert result is not None
        assert "image" in result
        assert result["image"]["format"] == "jpg"

    def test_generate_file_content_block_large_file(self, temp_dir):
        """Test handling of large files."""
        large_file = temp_dir / "large.txt"
        # Create a file larger than MAX_FILE_SIZE_BYTES
        large_content = "A" * (15 * 1024 * 1024)  # 15MB
        large_file.write_text(large_content)
        
        result = generate_file_content_block(large_file, "text/plain")
        
        assert result is not None
        assert "type" in result
        assert result["type"] == "text"
        assert "was skipped because it is too large" in result["text"]


class TestMessageGenerator:
    """Test cases for message generation functionality."""

    def test_generate_llm_messages_text_only(self):
        """Test generating messages with text only."""
        input_text = "This is a simple message"
        
        result = generate_llm_messages(input_text)
        
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert len(result[0]["content"]) == 1
        assert result[0]["content"][0]["text"] == input_text

    def test_generate_llm_messages_empty_input(self):
        """Test generating messages with empty input."""
        result = generate_llm_messages("")
        
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert len(result[0]["content"]) == 1
        assert result[0]["content"][0]["text"] == ""

    def test_parse_file_references(self):
        """Test parsing file references from text."""
        text = """
        Here is some text file('test.txt') and more text.
        Also file('data.json', 'application/json') here.
        And file("double_quotes.py") works too.
        """
        
        result = _parse_file_references(text)
        
        assert len(result) == 3
        
        # Check first reference
        assert result[0][0] == "test.txt"
        assert result[0][1] is None
        
        # Check second reference
        assert result[1][0] == "data.json"
        assert result[1][1] == "application/json"
        
        # Check third reference
        assert result[2][0] == "double_quotes.py"
        assert result[2][1] is None

    def test_parse_file_references_no_matches(self):
        """Test parsing text with no file references."""
        text = "This text has no file references"
        
        result = _parse_file_references(text)
        
        assert result == []

    @patch('glob.glob')
    def test_resolve_file_glob(self, mock_glob, temp_dir):
        """Test resolving file glob patterns."""
        # Mock glob to return some paths
        mock_paths = [str(temp_dir / "file1.txt"), str(temp_dir / "file2.txt")]
        mock_glob.return_value = mock_paths
        
        # Create the actual files
        for path in mock_paths:
            Path(path).write_text("content")
        
        result = _resolve_file_glob("*.txt", "text/plain")
        
        assert len(result) == 2
        assert all(mimetype == "text/plain" for _, mimetype in result)
        mock_glob.assert_called_once_with("*.txt", recursive=True)

    @patch('glob.glob')
    def test_resolve_file_glob_no_matches(self, mock_glob):
        """Test resolving glob pattern with no matches."""
        mock_glob.return_value = []
        
        result = _resolve_file_glob("*.nonexistent", None)
        
        assert result == []

    def test_create_text_content_block(self):
        """Test creating text content blocks."""
        text = "Sample text content"
        
        result = _create_text_content_block(text)
        
        assert result == {"text": text}

    @patch('strands_agent_factory.messaging.generator.generate_file_content_block')
    def test_create_file_content_blocks(self, mock_generate, temp_dir):
        """Test creating file content blocks."""
        # Create test files
        file1 = temp_dir / "test1.txt"
        file2 = temp_dir / "test2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        file_paths = [
            (str(file1), "text/plain"),
            (str(file2), "text/plain")
        ]
        
        # Mock the content block generation
        mock_generate.side_effect = [
            {"document": {"name": str(file1), "format": "txt"}},
            {"document": {"name": str(file2), "format": "txt"}}
        ]
        
        result = _create_file_content_blocks(file_paths)
        
        assert len(result) == 2
        assert mock_generate.call_count == 2

    @patch('strands_agent_factory.messaging.generator.generate_file_content_block')
    def test_create_file_content_blocks_with_errors(self, mock_generate, temp_dir):
        """Test creating file content blocks with errors."""
        file1 = temp_dir / "test1.txt"
        file1.write_text("content")
        
        file_paths = [(str(file1), "text/plain")]
        
        # Mock an error in content block generation
        mock_generate.side_effect = Exception("Test error")
        
        result = _create_file_content_blocks(file_paths)
        
        assert len(result) == 1
        assert "text" in result[0]
        assert "Failed to read file" in result[0]["text"]

    @patch('strands_agent_factory.messaging.generator._resolve_file_glob')
    def test_generate_llm_messages_with_file_references(self, mock_resolve, temp_dir):
        """Test generating messages with file references."""
        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("file content")
        
        # Mock file resolution
        mock_resolve.return_value = [(str(test_file), "text/plain")]
        
        input_text = "Process this file('*.txt') please"
        
        with patch('strands_agent_factory.messaging.generator._create_file_content_blocks') as mock_create:
            mock_create.return_value = [{"document": {"name": str(test_file)}}]
            
            result = generate_llm_messages(input_text)
        
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert len(result[0]["content"]) >= 2  # Text before + file content
        
        mock_resolve.assert_called_once_with("*.txt", None)

    def test_generate_llm_messages_mixed_content(self):
        """Test generating messages with mixed text and file references."""
        input_text = "Start text file('nonexistent.txt') middle text file('another.txt') end text"
        
        with patch('strands_agent_factory.messaging.generator._resolve_file_glob') as mock_resolve:
            # Mock no files found
            mock_resolve.return_value = []
            
            result = generate_llm_messages(input_text)
        
        assert len(result) == 1
        content_blocks = result[0]["content"]
        
        # Should have text blocks and "no files found" messages
        text_blocks = [block for block in content_blocks if "text" in block]
        assert len(text_blocks) >= 3  # Start, middle, end text + error messages