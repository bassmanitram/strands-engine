"""
Unit tests for strands_agent_factory.core.utils module.

Tests utility functions and helper classes.
"""

import io
import sys
from unittest.mock import Mock, patch

import pytest

from strands_agent_factory.core.utils import clean_dict, print_structured_data


class TestCleanDict:
    """Test cases for clean_dict utility function."""

    def test_clean_dict_removes_none_values(self):
        """Test that clean_dict removes None values."""
        input_dict = {"key1": "value1", "key2": None, "key3": "value3", "key4": None}

        result = clean_dict(input_dict)

        expected = {"key1": "value1", "key3": "value3"}

        assert result == expected

    def test_clean_dict_preserves_non_none_values(self):
        """Test that clean_dict preserves non-None values."""
        input_dict = {
            "string": "value",
            "number": 42,
            "zero": 0,
            "false": False,
            "empty_string": "",
            "empty_list": [],
            "empty_dict": {},
            "none": None,
        }

        result = clean_dict(input_dict)

        expected = {
            "string": "value",
            "number": 42,
            "zero": 0,
            "false": False,
            "empty_string": "",
            "empty_list": [],
            "empty_dict": {},
        }

        assert result == expected

    def test_clean_dict_empty_input(self):
        """Test clean_dict with empty dictionary."""
        result = clean_dict({})

        assert result == {}

    def test_clean_dict_all_none_values(self):
        """Test clean_dict when all values are None."""
        input_dict = {"key1": None, "key2": None, "key3": None}

        result = clean_dict(input_dict)

        assert result == {}

    def test_clean_dict_no_none_values(self):
        """Test clean_dict when no None values exist."""
        input_dict = {"key1": "value1", "key2": "value2", "key3": 42}

        result = clean_dict(input_dict)

        assert result == input_dict

    def test_clean_dict_mixed_types(self):
        """Test clean_dict with mixed data types."""
        mock_object = Mock()

        input_dict = {
            "string": "value",
            "number": 42,
            "list": [1, 2, 3],
            "dict": {"nested": True},
            "object": mock_object,
            "none": None,
        }

        result = clean_dict(input_dict)

        expected = {
            "string": "value",
            "number": 42,
            "list": [1, 2, 3],
            "dict": {"nested": True},
            "object": mock_object,
        }

        assert result == expected


class TestPrintStructuredData:
    """Test cases for print_structured_data utility function."""

    def test_print_simple_dict(self):
        """Test printing a simple dictionary."""
        data = {"key1": "value1", "key2": "value2"}

        # Capture stdout
        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            print_structured_data(data, printer=print)

        output = captured_output.getvalue()

        assert "key1: value1" in output
        assert "key2: value2" in output

    def test_print_nested_dict(self):
        """Test printing a nested dictionary."""
        data = {"level1": {"key1": "value1", "key2": "value2"}, "other": "value"}

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            print_structured_data(data, printer=print)

        output = captured_output.getvalue()

        assert "level1:" in output
        assert "key1: value1" in output
        assert "other: value" in output

    def test_print_with_indentation(self):
        """Test printing with indentation levels."""
        data = {"nested": {"key": "value"}}

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            print_structured_data(data, printer=print)

        output = captured_output.getvalue()

        # Check that nested content is indented
        lines = output.strip().split("\n")
        nested_lines = [line for line in lines if "key: value" in line]
        assert len(nested_lines) > 0
        # The nested line should have some indentation
        assert any(line.startswith("  ") for line in nested_lines)

    def test_print_list_values(self):
        """Test printing dictionary with list values."""
        data = {"items": ["item1", "item2", "item3"], "other": "value"}

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            print_structured_data(data, printer=print)

        output = captured_output.getvalue()

        assert "items:" in output
        assert "other: value" in output

    def test_print_empty_containers(self):
        """Test printing empty containers."""
        data = {"empty_dict": {}, "empty_list": [], "empty_string": ""}

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            print_structured_data(data, printer=print)

        output = captured_output.getvalue()

        assert "empty_dict:" in output
        assert "empty_list: []" in output
        assert "empty_string:" in output

    def test_print_mixed_types(self):
        """Test printing dictionary with mixed value types."""
        data = {
            "string": "text",
            "number": 42,
            "boolean": True,
            "none_value": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
        }

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            print_structured_data(data, printer=print)

        output = captured_output.getvalue()

        assert "string: text" in output
        assert "number: 42" in output
        assert "boolean: True" in output
        assert "none_value: None" in output

    def test_print_elementary_types_no_truncation(self):
        """Test that elementary types (int, float, bool) are not truncated."""
        data = {
            "large_int": 123456789012345,
            "large_float": 123456789.12345679,  # Use Python's actual float precision
            "boolean": True,
        }

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            print_structured_data(data, initial_max_len=10, printer=print)

        output = captured_output.getvalue()

        # Elementary types should not be truncated even with small max_len
        assert "large_int: 123456789012345" in output
        assert (
            "large_float: 123456789.12345679" in output
        )  # Match actual Python float precision
        assert "boolean: True" in output

    def test_print_string_truncation(self):
        """Test string truncation functionality."""
        long_string = "a" * 100
        data = {"long_text": long_string}

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            print_structured_data(data, initial_max_len=20, printer=print)

        output = captured_output.getvalue()

        # String should be truncated with ellipsis
        assert "long_text:" in output
        assert "..." in output
        # Should not contain the full string
        assert long_string not in output

    def test_print_no_truncation_when_disabled(self):
        """Test that truncation is disabled when initial_max_len is -1."""
        long_string = "a" * 200
        data = {"long_text": long_string}

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            print_structured_data(data, initial_max_len=-1, printer=print)

        output = captured_output.getvalue()

        # Full string should be present when truncation is disabled
        assert long_string in output

    def test_print_deep_nesting(self):
        """Test printing deeply nested structures."""
        data = {"level1": {"level2": {"level3": {"deep_value": "found"}}}}

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            print_structured_data(data, printer=print)

        output = captured_output.getvalue()

        assert "level1:" in output
        assert "level2:" in output
        assert "level3:" in output
        assert "deep_value: found" in output

    def test_print_empty_dict(self):
        """Test printing empty dictionary."""
        data = {}

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            print_structured_data(data, printer=print)

        output = captured_output.getvalue()

        # Should handle empty dict gracefully (no output expected)
        assert output.strip() == ""

    def test_print_non_dict_data(self):
        """Test printing non-dictionary data."""
        test_cases = ["simple string", 42, [1, 2, 3], True, None]

        for data in test_cases:
            captured_output = io.StringIO()
            with patch("sys.stdout", captured_output):
                print_structured_data(data, printer=print)

            output = captured_output.getvalue()

            # Should handle non-dict data without crashing
            assert len(output) > 0

    def test_print_custom_printer(self):
        """Test using custom printer function."""
        data = {"key": "value"}
        printed_lines = []

        def custom_printer(text):
            printed_lines.append(text)

        print_structured_data(data, printer=custom_printer)

        assert len(printed_lines) > 0
        assert any("key: value" in line for line in printed_lines)
