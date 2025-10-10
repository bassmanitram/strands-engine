#!/usr/bin/env python3
"""
Tests for strands_agent_factory.messages module.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from strands_agent_factory.messages import (
    generate_llm_messages,
    _parse_file_references,
    _resolve_file_glob,
    _create_text_content_block,
    _create_file_content_blocks,
)


class TestGenerateLLMMessages(unittest.TestCase):
    """Test the main generate_llm_messages function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create test files
        (self.temp_path / "test.txt").write_text("Hello world")
        (self.temp_path / "data.json").write_text('{"key": "value"}')
        (self.temp_path / "image.png").write_bytes(b"fake image data")
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_plain_text_only(self):
        """Test with plain text, no file references."""
        result = generate_llm_messages("Hello world")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["role"], "user")
        self.assertEqual(len(result[0]["content"]), 1)
        self.assertEqual(result[0]["content"][0], {"text": "Hello world"})
    
    def test_empty_string(self):
        """Test with empty input string."""
        result = generate_llm_messages("")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["role"], "user")
        self.assertEqual(len(result[0]["content"]), 1)
        self.assertEqual(result[0]["content"][0], {"text": ""})
    
    def test_whitespace_only(self):
        """Test with whitespace-only input."""
        result = generate_llm_messages("   \n\t  ")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["role"], "user")
        self.assertEqual(len(result[0]["content"]), 1)
        self.assertEqual(result[0]["content"][0], {"text": ""})
    
    @patch('strands_agent_factory.messages._process_single_file')
    def test_single_file_reference(self, mock_process):
        """Test with single file reference."""
        mock_process.return_value = {"type": "text", "text": "file content"}
        
        test_file = self.temp_path / "test.txt"
        result = generate_llm_messages(f"Read file('{test_file}')")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["role"], "user")
        self.assertEqual(len(result[0]["content"]), 2)
        self.assertEqual(result[0]["content"][0], {"text": "Read"})
        self.assertEqual(result[0]["content"][1], {"type": "text", "text": "file content"})
    
    @patch('strands_agent_factory.messages._process_single_file')
    def test_file_with_mimetype(self, mock_process):
        """Test file reference with explicit mimetype."""
        mock_process.return_value = {"type": "text", "text": "json content"}
        
        test_file = self.temp_path / "data.json"
        result = generate_llm_messages(f"Parse file('{test_file}', 'application/json')")
        
        self.assertEqual(len(result), 1)
        mock_process.assert_called_once()
        # Check that the mimetype was passed correctly
        call_args = mock_process.call_args[0]
        self.assertEqual(call_args[1], "application/json")
    
    @patch('strands_agent_factory.messages._process_single_file')
    def test_multiple_files(self, mock_process):
        """Test with multiple file references."""
        mock_process.return_value = {"type": "text", "text": "content"}
        
        file1 = self.temp_path / "test.txt"
        file2 = self.temp_path / "data.json"
        result = generate_llm_messages(f"First file('{file1}') then file('{file2}') done")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]["content"]), 5)  # text, file, text, file, text
        self.assertEqual(result[0]["content"][0], {"text": "First"})
        self.assertEqual(result[0]["content"][2], {"text": "then"})
        self.assertEqual(result[0]["content"][4], {"text": "done"})
    
    def test_nonexistent_file(self):
        """Test with reference to nonexistent file."""
        result = generate_llm_messages("Read file('/nonexistent/file.txt')")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]["content"]), 2)
        self.assertEqual(result[0]["content"][0], {"text": "Read"})
        self.assertIn("No files found", result[0]["content"][1]["text"])
    
    @patch('glob.glob')
    def test_glob_pattern(self, mock_glob):
        """Test with glob pattern that matches multiple files."""
        mock_glob.return_value = [str(self.temp_path / "test.txt"), str(self.temp_path / "data.json")]
        
        with patch('strands_agent_factory.messages._process_single_file') as mock_process:
            mock_process.return_value = {"type": "text", "text": "content"}
            
            result = generate_llm_messages(f"Files file('{self.temp_path}/*.txt')")
            
            self.assertEqual(len(result), 1)
            # Should have text + file content blocks
            self.assertGreaterEqual(len(result[0]["content"]), 2)


class TestParseFileReferences(unittest.TestCase):
    """Test the _parse_file_references function."""
    
    def test_no_references(self):
        """Test text with no file references."""
        result = _parse_file_references("Hello world")
        self.assertEqual(result, [])
    
    def test_single_reference(self):
        """Test single file reference."""
        text = "Read file('test.txt')"
        result = _parse_file_references(text)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "test.txt")  # glob pattern
        self.assertIsNone(result[0][1])  # mimetype
        self.assertEqual(result[0][2], text.find("file("))  # start pos
        self.assertEqual(result[0][3], text.find(")") + 1)  # end pos
    
    def test_reference_with_mimetype(self):
        """Test file reference with mimetype."""
        result = _parse_file_references("Parse file('data.json', 'application/json')")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "data.json")
        self.assertEqual(result[0][1], "application/json")
    
    def test_multiple_references(self):
        """Test multiple file references."""
        result = _parse_file_references("file('a.txt') and file('b.txt')")
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][0], "a.txt")
        self.assertEqual(result[1][0], "b.txt")
    
    def test_double_quotes(self):
        """Test file reference with double quotes."""
        result = _parse_file_references('file("test.txt")')
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "test.txt")
    
    def test_case_insensitive(self):
        """Test case insensitive matching."""
        result = _parse_file_references("FILE('test.txt') and File('data.json')")
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][0], "test.txt")
        self.assertEqual(result[1][0], "data.json")
    
    def test_whitespace_handling(self):
        """Test handling of whitespace in file references."""
        result = _parse_file_references("file( 'test.txt' , 'text/plain' )")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "test.txt")
        self.assertEqual(result[0][1], "text/plain")


class TestResolveFileGlob(unittest.TestCase):
    """Test the _resolve_file_glob function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create test files
        (self.temp_path / "test1.txt").write_text("content1")
        (self.temp_path / "test2.txt").write_text("content2")
        (self.temp_path / "data.json").write_text('{"key": "value"}')
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_single_file(self):
        """Test resolving single file."""
        test_file = self.temp_path / "test1.txt"
        result = _resolve_file_glob(str(test_file), "text/plain")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(Path(result[0][0]).name, "test1.txt")
        self.assertEqual(result[0][1], "text/plain")
    
    def test_glob_pattern(self):
        """Test resolving glob pattern."""
        pattern = str(self.temp_path / "*.txt")
        result = _resolve_file_glob(pattern, "text/plain")
        
        self.assertEqual(len(result), 2)
        # Both files should have the same mimetype
        self.assertTrue(all(r[1] == "text/plain" for r in result))
    
    def test_nonexistent_pattern(self):
        """Test glob pattern that matches nothing."""
        pattern = str(self.temp_path / "*.xyz")
        result = _resolve_file_glob(pattern, None)
        
        self.assertEqual(result, [])
    
    def test_invalid_glob(self):
        """Test handling of invalid glob pattern."""
        with patch('glob.glob', side_effect=Exception("Invalid pattern")):
            result = _resolve_file_glob("invalid[", None)
            self.assertEqual(result, [])


class TestCreateTextContentBlock(unittest.TestCase):
    """Test the _create_text_content_block function."""
    
    def test_simple_text(self):
        """Test creating text content block."""
        result = _create_text_content_block("Hello world")
        
        self.assertEqual(result, {"text": "Hello world"})
    
    def test_empty_text(self):
        """Test creating text content block with empty string."""
        result = _create_text_content_block("")
        
        self.assertEqual(result, {"text": ""})
    
    def test_multiline_text(self):
        """Test creating text content block with multiline text."""
        text = "Line 1\nLine 2\nLine 3"
        result = _create_text_content_block(text)
        
        self.assertEqual(result, {"text": text})


class TestCreateFileContentBlocks(unittest.TestCase):
    """Test the _create_file_content_blocks function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        (self.temp_path / "test.txt").write_text("Hello world")
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    @patch('strands_agent_factory.messages._process_single_file')
    def test_successful_processing(self, mock_process):
        """Test successful file processing."""
        mock_process.return_value = {"type": "text", "text": "file content"}
        
        file_paths = [(str(self.temp_path / "test.txt"), "text/plain")]
        result = _create_file_content_blocks(file_paths)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], {"type": "text", "text": "file content"})
    
    @patch('strands_agent_factory.messages._process_single_file')
    def test_processing_failure(self, mock_process):
        """Test handling of file processing failure."""
        mock_process.return_value = None  # Simulate failure
        
        file_paths = [(str(self.temp_path / "test.txt"), "text/plain")]
        result = _create_file_content_blocks(file_paths)
        
        self.assertEqual(len(result), 1)
        self.assertIn("Failed to process file", result[0]["text"])
    
    @patch('strands_agent_factory.messages._process_single_file')
    def test_processing_exception(self, mock_process):
        """Test handling of exception during file processing."""
        mock_process.side_effect = Exception("IO Error")
        
        file_paths = [(str(self.temp_path / "test.txt"), "text/plain")]
        result = _create_file_content_blocks(file_paths)
        
        self.assertEqual(len(result), 1)
        self.assertIn("Failed to read file", result[0]["text"])
        self.assertIn("IO Error", result[0]["text"])
    
    @patch('strands_agent_factory.messages._process_single_file')
    def test_multiple_files(self, mock_process):
        """Test processing multiple files."""
        mock_process.return_value = {"type": "text", "text": "content"}
        
        file_paths = [
            (str(self.temp_path / "test.txt"), "text/plain"),
            (str(self.temp_path / "data.json"), "application/json")
        ]
        result = _create_file_content_blocks(file_paths)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(mock_process.call_count, 2)


if __name__ == '__main__':
    unittest.main()