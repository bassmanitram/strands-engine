"""
Comprehensive tests for AWS region resolution in BedrockAdapter.

Tests the complete region resolution hierarchy:
1. Existing region_name in model_config
2. AWS_REGION environment variable
3. AWS_DEFAULT_REGION environment variable
4. AWS_PROFILE configuration with source_profile inheritance
5. None (boto3 defaults)
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from strands_agent_factory.adapters.bedrock import (
    BedrockAdapter,
    _resolve_region_from_profile,
    _resolve_region_name,
)


class TestResolveRegionName:
    """Tests for _resolve_region_name function."""

    def test_existing_region_name_not_overridden(self, monkeypatch):
        """Should preserve existing region_name in config."""
        # Clear all environment variables
        monkeypatch.delenv("AWS_REGION", raising=False)
        monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
        monkeypatch.delenv("AWS_PROFILE", raising=False)

        model_config = {"region_name": "eu-west-1"}
        result = _resolve_region_name(model_config)

        assert result == "eu-west-1"

    def test_aws_region_environment_variable(self, monkeypatch):
        """Should use AWS_REGION if set."""
        monkeypatch.setenv("AWS_REGION", "us-east-1")
        monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
        monkeypatch.delenv("AWS_PROFILE", raising=False)

        result = _resolve_region_name({})

        assert result == "us-east-1"

    def test_aws_default_region_environment_variable(self, monkeypatch):
        """Should use AWS_DEFAULT_REGION if AWS_REGION not set."""
        monkeypatch.delenv("AWS_REGION", raising=False)
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-2")
        monkeypatch.delenv("AWS_PROFILE", raising=False)

        result = _resolve_region_name({})

        assert result == "us-west-2"

    def test_aws_region_takes_precedence_over_default(self, monkeypatch):
        """AWS_REGION should take precedence over AWS_DEFAULT_REGION."""
        monkeypatch.setenv("AWS_REGION", "us-east-1")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-2")
        monkeypatch.delenv("AWS_PROFILE", raising=False)

        result = _resolve_region_name({})

        assert result == "us-east-1"

    def test_no_region_found_returns_none(self, monkeypatch):
        """Should return None if no region source available."""
        monkeypatch.delenv("AWS_REGION", raising=False)
        monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
        monkeypatch.delenv("AWS_PROFILE", raising=False)

        result = _resolve_region_name({})

        assert result is None

    def test_empty_region_name_in_config_treated_as_set(self, monkeypatch):
        """Empty string in region_name should be preserved."""
        monkeypatch.setenv("AWS_REGION", "us-east-1")

        model_config = {"region_name": ""}
        result = _resolve_region_name(model_config)

        assert result == ""

    def test_config_precedence_over_environment(self, monkeypatch):
        """Config region_name should override all environment variables."""
        monkeypatch.setenv("AWS_REGION", "us-east-1")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-2")

        model_config = {"region_name": "ap-southeast-1"}
        result = _resolve_region_name(model_config)

        assert result == "ap-southeast-1"


class TestResolveRegionFromProfile:
    """Tests for _resolve_region_from_profile function."""

    def test_profile_with_region(self, tmp_path, monkeypatch):
        """Should resolve region from profile section."""
        config_dir = tmp_path / ".aws"
        config_dir.mkdir()
        config_file = config_dir / "config"

        config_file.write_text(
            """
[profile dev]
region = us-west-2
output = json
"""
        )

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = _resolve_region_from_profile("dev")

        assert result == "us-west-2"

    def test_default_profile(self, tmp_path, monkeypatch):
        """Should handle default profile (no 'profile' prefix)."""
        config_dir = tmp_path / ".aws"
        config_dir.mkdir()
        config_file = config_dir / "config"

        config_file.write_text(
            """
[default]
region = eu-central-1
"""
        )

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = _resolve_region_from_profile("default")

        assert result == "eu-central-1"

    def test_profile_with_source_profile(self, tmp_path, monkeypatch):
        """Should follow source_profile chain to find region."""
        config_dir = tmp_path / ".aws"
        config_dir.mkdir()
        config_file = config_dir / "config"

        config_file.write_text(
            """
[profile dev]
source_profile = base

[profile base]
region = ap-northeast-1
"""
        )

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = _resolve_region_from_profile("dev")

        assert result == "ap-northeast-1"

    def test_deep_source_profile_chain(self, tmp_path, monkeypatch):
        """Should follow multiple levels of source_profile."""
        config_dir = tmp_path / ".aws"
        config_dir.mkdir()
        config_file = config_dir / "config"

        config_file.write_text(
            """
[profile dev]
source_profile = staging

[profile staging]
source_profile = prod

[profile prod]
region = us-east-1
"""
        )

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = _resolve_region_from_profile("dev")

        assert result == "us-east-1"

    def test_circular_source_profile_reference(self, tmp_path, monkeypatch):
        """Should detect and handle circular profile references."""
        config_dir = tmp_path / ".aws"
        config_dir.mkdir()
        config_file = config_dir / "config"

        config_file.write_text(
            """
[profile dev]
source_profile = staging

[profile staging]
source_profile = dev
"""
        )

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = _resolve_region_from_profile("dev")

        assert result is None

    def test_profile_not_found(self, tmp_path, monkeypatch):
        """Should return None if profile doesn't exist."""
        config_dir = tmp_path / ".aws"
        config_dir.mkdir()
        config_file = config_dir / "config"

        config_file.write_text(
            """
[profile prod]
region = us-east-1
"""
        )

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = _resolve_region_from_profile("nonexistent")

        assert result is None

    def test_config_file_not_found(self, tmp_path, monkeypatch):
        """Should return None if config file doesn't exist."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = _resolve_region_from_profile("dev")

        assert result is None

    def test_malformed_config_file(self, tmp_path, monkeypatch):
        """Should handle malformed config gracefully."""
        config_dir = tmp_path / ".aws"
        config_dir.mkdir()
        config_file = config_dir / "config"

        config_file.write_text("this is not valid INI format [[[")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = _resolve_region_from_profile("dev")

        assert result is None

    def test_profile_without_region_or_source(self, tmp_path, monkeypatch):
        """Should return None if profile has no region or source_profile."""
        config_dir = tmp_path / ".aws"
        config_dir.mkdir()
        config_file = config_dir / "config"

        config_file.write_text(
            """
[profile dev]
output = json
"""
        )

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = _resolve_region_from_profile("dev")

        assert result is None

    def test_source_profile_chain_ending_without_region(self, tmp_path, monkeypatch):
        """Should return None if source_profile chain has no region."""
        config_dir = tmp_path / ".aws"
        config_dir.mkdir()
        config_file = config_dir / "config"

        config_file.write_text(
            """
[profile dev]
source_profile = base

[profile base]
output = json
"""
        )

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = _resolve_region_from_profile("dev")

        assert result is None

    def test_region_in_child_profile_takes_precedence(self, tmp_path, monkeypatch):
        """Child profile region should be used if present."""
        config_dir = tmp_path / ".aws"
        config_dir.mkdir()
        config_file = config_dir / "config"

        config_file.write_text(
            """
[profile dev]
region = us-west-1
source_profile = base

[profile base]
region = us-east-1
"""
        )

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = _resolve_region_from_profile("dev")

        assert result == "us-west-1"


class TestResolveRegionFromProfileIntegration:
    """Integration tests for AWS_PROFILE environment variable."""

    def test_aws_profile_with_region(self, tmp_path, monkeypatch):
        """Should resolve region from AWS_PROFILE."""
        config_dir = tmp_path / ".aws"
        config_dir.mkdir()
        config_file = config_dir / "config"

        config_file.write_text(
            """
[profile production]
region = eu-west-1
"""
        )

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("AWS_REGION", raising=False)
        monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
        monkeypatch.setenv("AWS_PROFILE", "production")

        result = _resolve_region_name({})

        assert result == "eu-west-1"

    def test_environment_precedence_over_profile(self, tmp_path, monkeypatch):
        """AWS_REGION should take precedence over AWS_PROFILE."""
        config_dir = tmp_path / ".aws"
        config_dir.mkdir()
        config_file = config_dir / "config"

        config_file.write_text(
            """
[profile production]
region = eu-west-1
"""
        )

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("AWS_REGION", "us-east-1")
        monkeypatch.setenv("AWS_PROFILE", "production")

        result = _resolve_region_name({})

        assert result == "us-east-1"

    def test_aws_profile_not_set(self, monkeypatch):
        """Should return None if AWS_PROFILE not set and no other source."""
        monkeypatch.delenv("AWS_REGION", raising=False)
        monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
        monkeypatch.delenv("AWS_PROFILE", raising=False)

        result = _resolve_region_name({})

        assert result is None


class TestBedrockAdapterIntegration:
    """Integration tests for BedrockAdapter.load_model with region resolution."""

    @patch("strands_agent_factory.adapters.bedrock.BedrockModel")
    def test_load_model_with_existing_region(self, mock_bedrock_model, monkeypatch):
        """Should not override existing region_name in config."""
        monkeypatch.setenv("AWS_REGION", "us-east-1")

        adapter = BedrockAdapter()
        config = {"model_id": "test-model", "region_name": "eu-west-1"}

        adapter.load_model(model_config=config)

        # Verify BedrockModel was called with the original region
        call_kwargs = mock_bedrock_model.call_args[1]
        assert call_kwargs["region_name"] == "eu-west-1"

    @patch("strands_agent_factory.adapters.bedrock.BedrockModel")
    def test_load_model_resolves_region_from_env(self, mock_bedrock_model, monkeypatch):
        """Should resolve region from AWS_REGION."""
        monkeypatch.setenv("AWS_REGION", "ap-southeast-1")

        adapter = BedrockAdapter()
        config = {"model_id": "test-model"}

        adapter.load_model(model_config=config)

        # Verify BedrockModel was called with resolved region
        call_kwargs = mock_bedrock_model.call_args[1]
        assert call_kwargs["region_name"] == "ap-southeast-1"

    @patch("strands_agent_factory.adapters.bedrock.BedrockModel")
    def test_load_model_resolves_region_from_default_env(
        self, mock_bedrock_model, monkeypatch
    ):
        """Should resolve region from AWS_DEFAULT_REGION."""
        monkeypatch.delenv("AWS_REGION", raising=False)
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-2")

        adapter = BedrockAdapter()
        config = {"model_id": "test-model"}

        adapter.load_model(model_config=config)

        # Verify BedrockModel was called with resolved region
        call_kwargs = mock_bedrock_model.call_args[1]
        assert call_kwargs["region_name"] == "us-west-2"

    @patch("strands_agent_factory.adapters.bedrock.BedrockModel")
    def test_load_model_resolves_region_from_profile(
        self, mock_bedrock_model, tmp_path, monkeypatch
    ):
        """Should resolve region from AWS_PROFILE config."""
        config_dir = tmp_path / ".aws"
        config_dir.mkdir()
        config_file = config_dir / "config"

        config_file.write_text(
            """
[profile dev]
region = eu-central-1
"""
        )

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("AWS_REGION", raising=False)
        monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
        monkeypatch.setenv("AWS_PROFILE", "dev")

        adapter = BedrockAdapter()
        config = {"model_id": "test-model"}

        adapter.load_model(model_config=config)

        # Verify BedrockModel was called with resolved region
        call_kwargs = mock_bedrock_model.call_args[1]
        assert call_kwargs["region_name"] == "eu-central-1"

    @patch("strands_agent_factory.adapters.bedrock.BedrockModel")
    def test_load_model_no_region_specified(self, mock_bedrock_model, monkeypatch):
        """Should not set region_name if not resolvable."""
        monkeypatch.delenv("AWS_REGION", raising=False)
        monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
        monkeypatch.delenv("AWS_PROFILE", raising=False)

        adapter = BedrockAdapter()
        config = {"model_id": "test-model"}

        adapter.load_model(model_config=config)

        # Verify BedrockModel was called without region_name
        call_kwargs = mock_bedrock_model.call_args[1]
        assert "region_name" not in call_kwargs

    @patch("strands_agent_factory.adapters.bedrock.BedrockModel")
    def test_load_model_with_boto_client_config(self, mock_bedrock_model, monkeypatch):
        """Should handle boto_client_config alongside region resolution."""
        monkeypatch.setenv("AWS_REGION", "us-east-1")

        adapter = BedrockAdapter()
        config = {
            "model_id": "test-model",
            "boto_client_config": {"connect_timeout": 60},
        }

        adapter.load_model(model_config=config)

        # Verify both region and boto_client_config are handled
        call_args = mock_bedrock_model.call_args
        assert call_args[1]["region_name"] == "us-east-1"
        assert call_args[1]["boto_client_config"] is not None

    @patch("strands_agent_factory.adapters.bedrock.BedrockModel")
    def test_load_model_with_model_name_parameter(
        self, mock_bedrock_model, monkeypatch
    ):
        """Should handle model_name parameter alongside region resolution."""
        monkeypatch.setenv("AWS_REGION", "us-west-2")

        adapter = BedrockAdapter()

        adapter.load_model(model_name="anthropic.claude-3-sonnet", model_config={})

        # Verify both model_id and region_name are set
        call_kwargs = mock_bedrock_model.call_args[1]
        assert call_kwargs["model_id"] == "anthropic.claude-3-sonnet"
        assert call_kwargs["region_name"] == "us-west-2"


class TestEdgeCases:
    """Edge case and error handling tests."""

    def test_empty_profile_name(self, tmp_path, monkeypatch):
        """Should handle empty profile name gracefully."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = _resolve_region_from_profile("")

        assert result is None

    def test_profile_with_whitespace(self, tmp_path, monkeypatch):
        """Should handle profile names with whitespace."""
        config_dir = tmp_path / ".aws"
        config_dir.mkdir()
        config_file = config_dir / "config"

        config_file.write_text(
            """
[profile my profile]
region = us-east-1
"""
        )

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = _resolve_region_from_profile("my profile")

        assert result == "us-east-1"

    def test_config_with_comments(self, tmp_path, monkeypatch):
        """Should handle config files with comments."""
        config_dir = tmp_path / ".aws"
        config_dir.mkdir()
        config_file = config_dir / "config"

        # AWS config files use # for comments
        config_file.write_text(
            """
# This is a comment
[profile dev]
region = us-west-2
output = json
"""
        )

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = _resolve_region_from_profile("dev")

        assert result == "us-west-2"

    def test_config_with_unicode(self, tmp_path, monkeypatch):
        """Should handle config files with unicode characters."""
        config_dir = tmp_path / ".aws"
        config_dir.mkdir()
        config_file = config_dir / "config"

        # Unicode in comments/values should be handled
        config_file.write_text(
            """
[profile café]
region = eu-west-1
""",
            encoding="utf-8",
        )

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = _resolve_region_from_profile("café")

        assert result == "eu-west-1"

    def test_region_with_special_characters(self, tmp_path, monkeypatch):
        """Should preserve region names with special formats."""
        config_dir = tmp_path / ".aws"
        config_dir.mkdir()
        config_file = config_dir / "config"

        config_file.write_text(
            """
[profile dev]
region = us-gov-west-1
"""
        )

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = _resolve_region_from_profile("dev")

        assert result == "us-gov-west-1"

    def test_config_permissions_error(self, tmp_path, monkeypatch):
        """Should handle permission errors gracefully."""
        config_dir = tmp_path / ".aws"
        config_dir.mkdir()
        config_file = config_dir / "config"
        config_file.write_text("[profile dev]\nregion = us-east-1\n")

        # Make file unreadable
        config_file.chmod(0o000)

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        try:
            result = _resolve_region_from_profile("dev")
            # Should return None or handle gracefully
            assert result is None
        finally:
            # Restore permissions for cleanup
            config_file.chmod(0o644)

    def test_multiple_profiles_same_region(self, tmp_path, monkeypatch):
        """Should correctly resolve when multiple profiles have same region."""
        config_dir = tmp_path / ".aws"
        config_dir.mkdir()
        config_file = config_dir / "config"

        config_file.write_text(
            """
[profile dev]
region = us-east-1

[profile staging]
region = us-east-1

[profile prod]
region = us-east-1
"""
        )

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result1 = _resolve_region_from_profile("dev")
        result2 = _resolve_region_from_profile("staging")
        result3 = _resolve_region_from_profile("prod")

        assert result1 == result2 == result3 == "us-east-1"
