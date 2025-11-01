"""
Unit tests for AgentProxy bug fix - no MCP clients scenario.

Tests that AgentProxy works correctly when no MCP clients are configured,
addressing the bug where start_time was undefined leading to TypeError.
"""

from unittest.mock import Mock, patch

import pytest

from strands_agent_factory.core.agent import AgentProxy


class TestAgentProxyNoMCPClients:
    """Test AgentProxy behavior when no MCP clients are configured."""

    def test_agent_proxy_no_mcp_clients_success(self):
        """Test that AgentProxy works without MCP clients (bug fix verification)."""
        # Mock the adapter
        mock_adapter = Mock()
        mock_adapter.adapt_content = Mock(return_value=[])

        # Create tool specs with NO MCP clients (empty list)
        tool_specs = []

        # Mock Agent constructor
        with patch("strands_agent_factory.core.agent.Agent") as mock_agent_class:
            mock_agent_instance = Mock()
            mock_agent_class.return_value = mock_agent_instance

            # Create proxy with NO MCP clients
            proxy = AgentProxy(
                adapter=mock_adapter,
                tool_specs=tool_specs,  # Empty - no MCP clients
                system_prompt="Test prompt",
                messages=[],
            )

            # Should complete without TypeError
            with proxy as agent:
                assert agent._agent is not None
                assert agent._context_entered is True
                assert len(agent._active_mcp_clients) == 0
                assert len(agent._mcp_tools) == 0

        # Verify Agent was created with correct parameters
        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]
        assert "system_prompt" in call_kwargs
        assert call_kwargs["system_prompt"] == "Test prompt"

    def test_agent_proxy_only_python_tools_no_mcp(self):
        """Test AgentProxy with Python tools but no MCP clients."""
        # Mock the adapter
        mock_adapter = Mock()
        mock_adapter.adapt_content = Mock(return_value=[])

        # Create tool specs with Python tools but NO MCP clients
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.__name__ = "test_tool"

        tool_specs = [
            {
                "id": "python_tools",
                "type": "python",
                "tools": [mock_tool],
                "tool_names": ["test_tool"],
                # No "client" key - not an MCP tool
            }
        ]

        # Mock Agent constructor
        with patch("strands_agent_factory.core.agent.Agent") as mock_agent_class:
            mock_agent_instance = Mock()
            mock_agent_class.return_value = mock_agent_instance

            # Create proxy
            proxy = AgentProxy(
                adapter=mock_adapter,
                tool_specs=tool_specs,
                system_prompt="Test prompt",
                messages=[],
            )

            # Should complete without TypeError
            with proxy as agent:
                assert agent._agent is not None
                assert agent._context_entered is True
                assert len(agent._active_mcp_clients) == 0  # No MCP clients
                assert len(agent._tools) == 1  # Has Python tool
                assert agent._tools[0] == mock_tool

    def test_agent_proxy_empty_mcp_specs_list(self):
        """Test AgentProxy with explicitly empty MCP client specs list."""
        # Mock the adapter
        mock_adapter = Mock()
        mock_adapter.adapt_content = Mock(return_value=[])

        # Empty tool specs
        tool_specs = []

        # Mock Agent constructor
        with patch("strands_agent_factory.core.agent.Agent") as mock_agent_class:
            mock_agent_instance = Mock()
            mock_agent_class.return_value = mock_agent_instance

            # Create proxy
            proxy = AgentProxy(
                adapter=mock_adapter, tool_specs=tool_specs, system_prompt="Test prompt"
            )

            # Verify initial state
            assert len(proxy._mcp_client_specs) == 0
            assert len(proxy._local_tool_specs) == 0

            # Should complete without TypeError
            with proxy as agent:
                assert agent._agent is not None
                assert agent._exit_stack is None  # No exit stack created
                assert len(agent._active_mcp_clients) == 0

    def test_agent_proxy_context_manager_lifecycle_no_mcp(self):
        """Test complete lifecycle of AgentProxy context manager without MCP."""
        # Mock the adapter
        mock_adapter = Mock()

        tool_specs = []

        # Mock Agent
        with patch("strands_agent_factory.core.agent.Agent") as mock_agent_class:
            mock_agent_instance = Mock()
            mock_agent_class.return_value = mock_agent_instance

            proxy = AgentProxy(
                adapter=mock_adapter, tool_specs=tool_specs, system_prompt="Test"
            )

            # Before context
            assert proxy._context_entered is False
            assert proxy._agent is None

            # Enter context
            with proxy as agent:
                # Inside context
                assert agent._context_entered is True
                assert agent._agent is not None
                assert agent._exit_stack is None  # No MCP, so no exit stack

            # After context
            assert proxy._context_entered is False
            assert proxy._agent is None

    def test_agent_proxy_mixed_tools_and_errors_no_mcp(self):
        """Test AgentProxy with tools that have errors but no MCP clients."""
        mock_adapter = Mock()

        # Tool specs with errors
        tool_specs = [
            {
                "id": "failed_tool",
                "type": "python",
                "error": "Failed to load",
                # Has error, should be filtered out
            },
            {
                "id": "working_tool",
                "type": "python",
                "tools": [Mock(name="good_tool", __name__="good_tool")],
                "tool_names": ["good_tool"],
                # No error, should be included
            },
        ]

        with patch("strands_agent_factory.core.agent.Agent") as mock_agent_class:
            mock_agent_instance = Mock()
            mock_agent_class.return_value = mock_agent_instance

            proxy = AgentProxy(
                adapter=mock_adapter, tool_specs=tool_specs, system_prompt="Test"
            )

            # Should have filtered out the error tool
            assert len(proxy._local_tool_specs) == 1
            assert len(proxy._mcp_client_specs) == 0

            # Should work without TypeError
            with proxy as agent:
                assert agent._agent is not None
                assert len(agent._tools) == 1

    def test_original_bug_scenario(self):
        """
        Test the exact scenario from the bug report:
        - No MCP clients configured
        - Agent initialization should not crash with TypeError

        This reproduces the original bug where start_time was undefined.
        """
        mock_adapter = Mock()
        mock_adapter.adapt_content = Mock(return_value=[])

        # Simulate the bug scenario: no MCP tools, only regular tools
        tool_specs = []  # No tools at all, similar to bug report

        with patch("strands_agent_factory.core.agent.Agent") as mock_agent_class:
            mock_agent_instance = Mock()
            mock_agent_class.return_value = mock_agent_instance

            proxy = AgentProxy(
                adapter=mock_adapter,
                tool_specs=tool_specs,
                system_prompt="You are a helpful assistant",
                messages=[],
            )

            # This should NOT raise:
            # TypeError: unsupported operand type(s) for -: 'NoneType' and 'int'
            try:
                with proxy as agent:
                    # Successful initialization
                    assert agent is not None
                    assert agent._agent is not None
                    success = True
            except TypeError as e:
                if "NoneType" in str(e) and "int" in str(e):
                    pytest.fail(f"Bug not fixed: {e}")
                else:
                    raise

            assert success

    def test_agent_proxy_properties_no_mcp(self):
        """Test AgentProxy properties work correctly without MCP clients."""
        mock_adapter = Mock()

        tool_specs = []

        with patch("strands_agent_factory.core.agent.Agent") as mock_agent_class:
            mock_agent_instance = Mock()
            mock_agent_class.return_value = mock_agent_instance

            proxy = AgentProxy(
                adapter=mock_adapter,
                tool_specs=tool_specs,
                system_prompt="Test",
                messages=[],
            )

            # Test has_initial_messages property
            assert proxy.has_initial_messages is False

            # Test tool_specs property
            assert proxy.tool_specs == tool_specs

            # Should work in context
            with proxy as agent:
                assert agent.has_initial_messages is False
                assert agent.tool_specs == tool_specs
