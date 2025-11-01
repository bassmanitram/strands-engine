"""
Unit tests for ConfigurableCallbackHandler bug fix - max_line_length None handling.

Tests that the callback handler correctly handles the case where max_line_length
is None, addressing the bug where None was passed to arithmetic operations.
"""

import os
from unittest.mock import Mock, patch

import pytest

from strands_agent_factory.handlers.callback import ConfigurableCallbackHandler


class TestCallbackHandlerMaxLineLengthBugFix:
    """Test ConfigurableCallbackHandler with None max_line_length."""

    def test_callback_handler_with_none_max_line_length(self):
        """Test that handler works when max_line_length is None (bug fix verification)."""
        # Create handler with None max_line_length (default)
        handler = ConfigurableCallbackHandler(
            show_tool_use=True, max_line_length=None  # The bug scenario
        )

        assert handler.max_line_length is None
        assert handler.show_tool_use is True
        assert handler.disable_truncation is False

    @patch("strands_agent_factory.handlers.callback.print_structured_data")
    def test_tool_input_formatting_with_none_max_line_length(
        self, mock_print_structured
    ):
        """Test tool input formatting when max_line_length is None."""
        # Create handler with None max_line_length
        handler = ConfigurableCallbackHandler(show_tool_use=True, max_line_length=None)

        # Simulate tool use event sequence
        # 1. Start tool use
        handler(
            event={},
            current_tool_use={"name": "test_tool", "input": {"param1": "value1"}},
        )

        # 2. End tool use with messageStop
        handler(event={"messageStop": True}, current_tool_use=None)

        # Verify print_structured_data was called with correct parameters
        assert mock_print_structured.called
        call_args = mock_print_structured.call_args

        # The third argument should be 90 (default), not None
        max_len_arg = call_args[0][2]  # Third positional argument
        assert max_len_arg == 90  # Default value when None
        assert max_len_arg is not None  # Verify not None

    @patch("strands_agent_factory.handlers.callback.print_structured_data")
    def test_tool_input_formatting_with_explicit_max_line_length(
        self, mock_print_structured
    ):
        """Test tool input formatting with explicit max_line_length."""
        # Create handler with explicit max_line_length
        handler = ConfigurableCallbackHandler(show_tool_use=True, max_line_length=120)

        # Simulate tool use sequence
        handler(current_tool_use={"name": "test_tool", "input": {"param": "value"}})
        handler(event={"messageStop": True})

        # Verify print_structured_data was called with explicit value
        call_args = mock_print_structured.call_args
        max_len_arg = call_args[0][2]
        assert max_len_arg == 120

    @patch("strands_agent_factory.handlers.callback.print_structured_data")
    def test_tool_input_formatting_with_env_override(self, mock_print_structured):
        """Test tool input formatting with SHOW_FULL_TOOL_INPUT env override."""
        # Mock environment variable
        with patch.dict("os.environ", {"SHOW_FULL_TOOL_INPUT": "true"}):
            # Create new handler (reads env var in __init__)
            handler = ConfigurableCallbackHandler(
                show_tool_use=True, max_line_length=None
            )

            # Simulate tool use
            handler(current_tool_use={"name": "test", "input": {"a": "b"}})
            handler(event={"messageStop": True})

            # Verify print_structured_data was called with -1 (no truncation)
            call_args = mock_print_structured.call_args
            max_len_arg = call_args[0][2]
            assert max_len_arg == -1  # Truncation disabled by env var

    def test_original_bug_scenario(self):
        """
        Test the exact scenario from the bug report:
        - max_line_length is None (default)
        - disable_truncation is False (default)
        - Tool use triggers formatting

        This reproduces the original bug where None was passed to arithmetic operation.
        """
        # Create handler with defaults (bug scenario)
        handler = ConfigurableCallbackHandler(
            show_tool_use=True
            # max_line_length defaults to None
            # disable_truncation defaults to False (checked via env var)
        )

        assert handler.max_line_length is None
        assert handler.disable_truncation is False

        # Mock print_structured_data to verify correct argument
        with patch(
            "strands_agent_factory.handlers.callback.print_structured_data"
        ) as mock_print:
            # Simulate tool use event sequence
            handler(
                current_tool_use={
                    "name": "file_read",
                    "input": {"path": "/test/file.txt", "mode": "view"},
                }
            )

            # Trigger tool display with messageStop
            handler(event={"messageStop": True})

            # Should have been called (not raised TypeError)
            assert mock_print.called

            # Verify the max_len argument is not None
            call_args = mock_print.call_args[0]
            max_len_arg = call_args[2]

            # This should be 90, not None (bug fix verification)
            assert max_len_arg == 90
            assert max_len_arg is not None

    @patch("strands_agent_factory.handlers.callback.print_structured_data")
    def test_callback_handler_default_values(self, mock_print_structured):
        """Test that all default values work together without errors."""
        # Create handler with all defaults
        handler = ConfigurableCallbackHandler()

        # Defaults should be:
        assert handler.show_tool_use is False  # Default
        assert handler.max_line_length is None  # Default
        assert handler.disable_truncation is False  # Default (no env var)

        # With show_tool_use=False, tool formatting shouldn't be called
        handler(current_tool_use={"name": "test", "input": {}})
        handler(event={"messageStop": True})

        # Should not have called print_structured_data
        assert not mock_print_structured.called

        # Now enable show_tool_use
        handler.show_tool_use = True
        handler.in_tool_use = False  # Reset state

        # Simulate tool use
        handler(current_tool_use={"name": "test_tool", "input": {"test": "data"}})
        handler(event={"messageStop": True})

        # Should complete without error
        assert mock_print_structured.called

    def test_callback_handler_none_vs_zero_max_line_length(self):
        """Test distinction between None and 0 for max_line_length."""
        # None should default to 90
        handler_none = ConfigurableCallbackHandler(
            show_tool_use=True, max_line_length=None
        )

        # Note: 0 is also falsy, so the 'or' operator treats it like None
        # This is acceptable behavior - both None and 0 get default of 90
        handler_zero = ConfigurableCallbackHandler(
            show_tool_use=True, max_line_length=0
        )

        assert handler_none.max_line_length is None
        assert handler_zero.max_line_length == 0

        # Both should work in formatting and both default to 90
        with patch(
            "strands_agent_factory.handlers.callback.print_structured_data"
        ) as mock_print:
            # Test None case
            handler_none(current_tool_use={"name": "test", "input": {"a": "b"}})
            handler_none(event={"messageStop": True})

            call_args = mock_print.call_args[0]
            assert call_args[2] == 90  # Default applied

            # Reset for next test
            mock_print.reset_mock()
            handler_zero.in_tool_use = False

            # Test 0 case - also defaults to 90 because 0 is falsy
            handler_zero(current_tool_use={"name": "test", "input": {"a": "b"}})
            handler_zero(event={"messageStop": True})

            call_args = mock_print.call_args[0]
            assert call_args[2] == 90  # 0 is falsy, so also defaults to 90

    @patch("strands_agent_factory.handlers.callback.print_structured_data")
    def test_callback_handler_with_complex_tool_input(self, mock_print_structured):
        """Test callback handler with complex nested tool input."""
        handler = ConfigurableCallbackHandler(
            show_tool_use=True, max_line_length=None  # Bug scenario
        )

        # Complex nested tool input (realistic scenario)
        complex_input = {
            "path": "/very/long/path/to/some/file/that/might/be/truncated.txt",
            "options": {
                "recursive": True,
                "pattern": "*.py",
                "exclude": ["__pycache__", ".venv", "node_modules"],
            },
            "config": {"max_depth": 5, "follow_symlinks": False},
        }

        # Should handle complex input without error
        handler(current_tool_use={"name": "file_search", "input": complex_input})
        handler(event={"messageStop": True})

        # Verify formatting was called
        assert mock_print_structured.called
        call_args = mock_print_structured.call_args[0]

        # Verify the data structure was passed
        assert call_args[0] == complex_input
        # Verify max_len defaulted correctly
        assert call_args[2] == 90

    @patch("strands_agent_factory.handlers.callback.print_structured_data")
    def test_multiple_tool_uses_in_sequence(self, mock_print_structured):
        """Test multiple tool uses in sequence with None max_line_length."""
        handler = ConfigurableCallbackHandler(show_tool_use=True, max_line_length=None)

        # First tool use
        handler(current_tool_use={"name": "tool1", "input": {"p1": "v1"}})
        handler(event={"messageStop": True})

        assert mock_print_structured.call_count == 1
        assert handler.tool_count == 1

        # Reset state for second tool
        handler.in_tool_use = False

        # Second tool use
        handler(current_tool_use={"name": "tool2", "input": {"p2": "v2"}})
        handler(event={"messageStop": True})

        assert mock_print_structured.call_count == 2
        assert handler.tool_count == 2

        # All calls should have used default max_len of 90
        for call in mock_print_structured.call_args_list:
            max_len_arg = call[0][2]
            assert max_len_arg == 90

    def test_disable_truncation_attribute_from_env(self):
        """Test that disable_truncation is correctly set from environment variable."""
        # Test with env var set to 'true'
        with patch.dict("os.environ", {"SHOW_FULL_TOOL_INPUT": "true"}):
            handler_true = ConfigurableCallbackHandler()
            assert handler_true.disable_truncation is True

        # Test with env var set to 'false'
        with patch.dict("os.environ", {"SHOW_FULL_TOOL_INPUT": "false"}):
            handler_false = ConfigurableCallbackHandler()
            assert handler_false.disable_truncation is False

        # Test with env var set to other value
        with patch.dict("os.environ", {"SHOW_FULL_TOOL_INPUT": "yes"}):
            handler_other = ConfigurableCallbackHandler()
            assert handler_other.disable_truncation is False  # Only 'true' enables

        # Test without env var (default state)
        # Note: Can't actually remove from os.environ if it exists system-wide
        with patch.dict("os.environ", {"SHOW_FULL_TOOL_INPUT": "false"}):
            handler_none = ConfigurableCallbackHandler()
            assert handler_none.disable_truncation is False  # Default

    @patch("strands_agent_factory.handlers.callback.print_structured_data")
    def test_tool_formatting_not_called_when_show_tool_use_false(
        self, mock_print_structured
    ):
        """Test that tool formatting is not called when show_tool_use is False."""
        handler = ConfigurableCallbackHandler(
            show_tool_use=False, max_line_length=None  # Disabled
        )

        # Simulate tool use
        handler(current_tool_use={"name": "test", "input": {"a": "b"}})
        handler(event={"messageStop": True})

        # Should NOT have called print_structured_data
        assert not mock_print_structured.called


class TestCallbackHandlerFixVerification:
    """Direct verification that the bug fix line is correct."""

    def test_max_line_length_or_operator_logic(self):
        """Test the 'or' operator logic used in the fix."""
        # The fix uses: (self.max_line_length or 90)

        # Test None case
        max_line_length = None
        result = max_line_length or 90
        assert result == 90

        # Test 0 case (falsy, so defaults to 90)
        max_line_length = 0
        result = max_line_length or 90
        assert result == 90  # Note: 0 is falsy, so defaults to 90

        # Test explicit value
        max_line_length = 120
        result = max_line_length or 90
        assert result == 120

        # Test False case (edge case)
        max_line_length = False
        result = max_line_length or 90
        assert result == 90

    @patch("strands_agent_factory.handlers.callback.print_structured_data")
    def test_format_and_print_tool_input_directly(self, mock_print_structured):
        """Test the _format_and_print_tool_input method directly."""
        handler = ConfigurableCallbackHandler(show_tool_use=True, max_line_length=None)

        # Call the method directly
        handler._format_and_print_tool_input(
            tool_name="test_tool", tool_input={"param": "value"}
        )

        # Verify it was called without TypeError
        assert mock_print_structured.called
        call_args = mock_print_structured.call_args[0]

        # Verify parameters
        assert call_args[0] == {"param": "value"}  # tool_input
        assert call_args[1] == 1  # indent level
        assert call_args[2] == 90  # max_len (defaulted from None)

    @patch("strands_agent_factory.handlers.callback.print_structured_data")
    def test_format_and_print_tool_input_with_explicit_length(
        self, mock_print_structured
    ):
        """Test _format_and_print_tool_input with explicit max_line_length."""
        handler = ConfigurableCallbackHandler(show_tool_use=True, max_line_length=150)

        handler._format_and_print_tool_input(
            tool_name="test_tool", tool_input={"param": "value"}
        )

        call_args = mock_print_structured.call_args[0]
        assert call_args[2] == 150

    @patch("strands_agent_factory.handlers.callback.print_structured_data")
    def test_format_and_print_with_disable_truncation_env(self, mock_print_structured):
        """Test _format_and_print_tool_input with disable_truncation env var."""
        with patch.dict("os.environ", {"SHOW_FULL_TOOL_INPUT": "true"}):
            handler = ConfigurableCallbackHandler(
                show_tool_use=True, max_line_length=100  # Should be overridden
            )

            handler._format_and_print_tool_input(
                tool_name="test_tool", tool_input={"param": "value"}
            )

            call_args = mock_print_structured.call_args[0]
            assert call_args[2] == -1  # Disabled by env var

    def test_bug_fix_prevents_type_error(self):
        """
        Direct test that the bug fix prevents TypeError.

        Before fix: (self.max_line_length) could be None → TypeError
        After fix: (self.max_line_length or 90) provides default → No error
        """
        handler = ConfigurableCallbackHandler(show_tool_use=True, max_line_length=None)

        # Mock print_structured_data but let the calculation happen
        with patch(
            "strands_agent_factory.handlers.callback.print_structured_data"
        ) as mock_print:
            # The internal calculation should use the 'or' operator
            # to provide a default value

            # Call the method that contains the fixed line
            try:
                handler._format_and_print_tool_input(
                    tool_name="test", tool_input={"test": "data"}
                )
                success = True
            except TypeError as e:
                if "NoneType" in str(e) and "int" in str(e):
                    # This is the original bug - should not happen
                    pytest.fail(f"Bug not fixed: {e}")
                else:
                    raise

            assert success
            assert mock_print.called

            # Verify the calculation worked
            call_args = mock_print.call_args[0]
            max_len = call_args[2]

            # Should be 90, not None
            assert max_len == 90
            assert isinstance(max_len, int)


class TestCallbackHandlerEdgeCases:
    """Test edge cases for callback handler."""

    @patch("strands_agent_factory.handlers.callback.print_structured_data")
    def test_empty_tool_input(self, mock_print_structured):
        """Test handling of empty tool input."""
        handler = ConfigurableCallbackHandler(show_tool_use=True, max_line_length=None)

        handler(current_tool_use={"name": "test", "input": {}})
        handler(event={"messageStop": True})

        # Should handle empty dict without error
        assert mock_print_structured.called
        call_args = mock_print_structured.call_args[0]
        assert call_args[0] == {}
        assert call_args[2] == 90

    @patch("strands_agent_factory.handlers.callback.print_structured_data")
    def test_none_tool_input(self, mock_print_structured):
        """Test handling of None tool input."""
        handler = ConfigurableCallbackHandler(show_tool_use=True, max_line_length=None)

        handler(current_tool_use={"name": "test", "input": None})
        handler(event={"messageStop": True})

        # Should handle None input without error
        assert mock_print_structured.called
        call_args = mock_print_structured.call_args[0]
        assert call_args[0] is None
        assert call_args[2] == 90

    @patch("strands_agent_factory.handlers.callback.print_structured_data")
    def test_very_large_max_line_length(self, mock_print_structured):
        """Test with very large max_line_length value."""
        handler = ConfigurableCallbackHandler(
            show_tool_use=True, max_line_length=10000  # Very large
        )

        handler._format_and_print_tool_input(
            tool_name="test", tool_input={"data": "x" * 5000}
        )

        call_args = mock_print_structured.call_args[0]
        assert call_args[2] == 10000

    def test_custom_output_printer(self):
        """Test handler with custom output printer."""
        custom_printer = Mock()

        handler = ConfigurableCallbackHandler(
            show_tool_use=True, max_line_length=None, output_printer=custom_printer
        )

        # The custom printer should be used
        assert handler.output_printer == custom_printer

        # Verify it's used for tool formatting
        with patch("strands_agent_factory.handlers.callback.print_structured_data"):
            handler._format_and_print_tool_input("test", {"a": "b"})

            # Custom printer should have been called for the header
            assert custom_printer.called
            # Check it was called with tool name
            call_text = custom_printer.call_args[0][0]
            assert "test" in call_text
