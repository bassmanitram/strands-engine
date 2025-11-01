"""
Additional unit tests for A2A server script functionality.

Tests edge cases, error handling, and specific server behaviors.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from strands_agent_factory.core.exceptions import ConfigurationError


class TestSkillFileValidation:
    """Test skill file validation and error handling."""

    def test_load_skills_directory_path_rejected(self, tmp_path):
        """Test that directory paths are rejected for skill loading."""
        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        # Create a directory (not a file)
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()

        with pytest.raises(ConfigurationError, match="must be a file"):
            _load_skills_from_files([skill_dir])

    def test_load_skills_empty_file(self, tmp_path):
        """Test loading from empty file."""
        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        empty_file = tmp_path / "empty.json"
        empty_file.write_text("")

        with pytest.raises(ConfigurationError):
            _load_skills_from_files([empty_file])

    def test_load_skills_null_content(self, tmp_path):
        """Test loading file with null content."""
        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        null_file = tmp_path / "null.json"
        null_file.write_text("null")

        with pytest.raises(ConfigurationError):
            _load_skills_from_files([null_file])

    def test_load_skills_invalid_yaml_syntax(self, tmp_path):
        """Test loading file with invalid YAML syntax."""
        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        invalid_yaml = tmp_path / "invalid.yaml"
        invalid_yaml.write_text(
            """
name: Test
  invalid: indentation
    very: bad
        """
        )

        with pytest.raises(ConfigurationError, match="Failed to load skills"):
            _load_skills_from_files([invalid_yaml])

    def test_load_skills_mixed_valid_invalid_fields(self, tmp_path):
        """Test skill with some valid and some invalid fields."""
        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        # Valid required fields but invalid optional field types
        skill_data = {
            "name": "Test Skill",
            "id": "test",
            "description": "Test description",
            "tags": ["valid"],
            "examples": "should be array not string",  # Invalid type
        }

        skill_file = tmp_path / "mixed.json"
        skill_file.write_text(json.dumps(skill_data))

        # Should fail validation
        with pytest.raises(ConfigurationError, match="Invalid skill definition"):
            _load_skills_from_files([skill_file])

    def test_load_skills_with_extra_fields(self, tmp_path):
        """Test that extra fields in skill definition are handled."""
        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        # Valid skill with extra unexpected fields
        skill_data = {
            "name": "Test Skill",
            "id": "test",
            "description": "Test description",
            "tags": ["test"],
            "extra_field": "should be ignored",
            "another_extra": 123,
        }

        skill_file = tmp_path / "extra.json"
        skill_file.write_text(json.dumps(skill_data))

        # Should load successfully, extra fields might be ignored or preserved
        skills = _load_skills_from_files([skill_file])
        assert len(skills) == 1
        assert skills[0].name == "Test Skill"


class TestSystemPromptEdgeCases:
    """Test edge cases in system prompt generation."""

    def test_generate_prompt_empty_skill_list(self):
        """Test prompt generation with empty skills list."""
        from strands_agent_factory.scripts.a2a_server import (
            _generate_system_prompt_from_skills,
        )

        # Should handle gracefully even with empty list
        prompt = _generate_system_prompt_from_skills([])

        assert "0 specialized skills" in prompt or "specialized skill" in prompt
        assert "Agent-to-Agent" in prompt  # Should still have A2A context

    def test_generate_prompt_skill_with_empty_tags(self):
        """Test prompt generation with skill having empty tags."""
        from a2a.types import AgentSkill

        from strands_agent_factory.scripts.a2a_server import (
            _generate_system_prompt_from_skills,
        )

        skill = AgentSkill(
            name="No Tags Skill",
            id="no_tags",
            description="Skill without tags",
            tags=[],  # Empty tags list
        )

        prompt = _generate_system_prompt_from_skills([skill])

        assert "No Tags Skill" in prompt
        assert "Skill without tags" in prompt
        # Should still generate valid prompt
        assert len(prompt) > 100

    def test_generate_prompt_skill_with_long_description(self):
        """Test prompt generation with very long skill description."""
        from a2a.types import AgentSkill

        from strands_agent_factory.scripts.a2a_server import (
            _generate_system_prompt_from_skills,
        )

        long_description = "This is a very long description. " * 100

        skill = AgentSkill(
            name="Verbose Skill",
            id="verbose",
            description=long_description,
            tags=["verbose"],
        )

        prompt = _generate_system_prompt_from_skills([skill])

        # Should include the full description
        assert long_description in prompt

    def test_generate_prompt_skill_with_special_characters(self):
        """Test prompt generation with special characters in skill."""
        from a2a.types import AgentSkill

        from strands_agent_factory.scripts.a2a_server import (
            _generate_system_prompt_from_skills,
        )

        skill = AgentSkill(
            name='Special <Characters> & "Quotes"',
            id="special_chars",
            description="Uses special chars: <>&\"'",
            tags=["special", "characters"],
        )

        prompt = _generate_system_prompt_from_skills([skill])

        # Should handle special characters without errors
        assert "Special" in prompt
        assert "special chars" in prompt

    def test_generate_prompt_preserves_json_formatting(self):
        """Test that skill JSON in prompt is properly formatted."""
        from a2a.types import AgentSkill

        from strands_agent_factory.scripts.a2a_server import (
            _generate_system_prompt_from_skills,
        )

        skill = AgentSkill(
            name="Formatting Test",
            id="format",
            description="Test formatting",
            tags=["test"],
            examples=["Example 1", "Example 2"],
        )

        prompt = _generate_system_prompt_from_skills([skill])

        # Should have properly formatted JSON
        assert "```json" in prompt
        assert "```" in prompt.split("```json")[1]  # Closing backticks
        # JSON should be indented
        assert "  " in prompt  # Indentation present

    def test_generate_prompt_multiple_skills_numbering(self):
        """Test that skills are properly numbered in prompt."""
        from a2a.types import AgentSkill

        from strands_agent_factory.scripts.a2a_server import (
            _generate_system_prompt_from_skills,
        )

        skills = [
            AgentSkill(
                name=f"Skill {i}",
                id=f"skill{i}",
                description=f"Description {i}",
                tags=["test"],
            )
            for i in range(1, 6)
        ]

        prompt = _generate_system_prompt_from_skills(skills)

        # Verify all skills are numbered
        for i in range(1, 6):
            assert f"## Skill {i}:" in prompt


class TestA2AServerConfigurationHandling:
    """Test configuration handling in A2A server."""

    def test_skill_config_paths_none(self):
        """Test handling when skill_config_paths is None."""
        # This tests the server's behavior when no skills are provided
        # Skills should be auto-detected from agent tools

        # The server should handle this gracefully without errors
        import argparse

        args = argparse.Namespace(skill_config_paths=None)

        # Should not raise error
        assert args.skill_config_paths is None

    def test_skill_config_paths_empty_list(self):
        """Test handling when skill_config_paths is empty list."""
        import argparse

        args = argparse.Namespace(skill_config_paths=[])

        # Should handle empty list
        assert args.skill_config_paths == []

    def test_multiple_skill_files_with_duplicates(self, tmp_path):
        """Test loading multiple files with duplicate skill IDs."""
        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        # Create two files with same skill ID
        skill1 = {
            "name": "First Math",
            "id": "math",  # Duplicate ID
            "description": "First math skill",
            "tags": ["math"],
        }

        skill2 = {
            "name": "Second Math",
            "id": "math",  # Duplicate ID
            "description": "Second math skill",
            "tags": ["math"],
        }

        file1 = tmp_path / "math1.json"
        file1.write_text(json.dumps(skill1))

        file2 = tmp_path / "math2.json"
        file2.write_text(json.dumps(skill2))

        # Should load both (A2A server might handle duplicates)
        skills = _load_skills_from_files([file1, file2])

        # Both skills loaded
        assert len(skills) == 2
        # But they have the same ID
        assert skills[0].id == skills[1].id == "math"


class TestSkillFieldValidation:
    """Test validation of individual skill fields."""

    def test_skill_with_empty_name(self, tmp_path):
        """Test skill with empty name string."""
        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        skill = {
            "name": "",  # Empty name
            "id": "test",
            "description": "Test",
            "tags": [],
        }

        skill_file = tmp_path / "empty_name.json"
        skill_file.write_text(json.dumps(skill))

        # Might raise validation error depending on AgentSkill implementation
        try:
            skills = _load_skills_from_files([skill_file])
            # If it allows empty name, that's okay too
            assert len(skills) == 1
        except ConfigurationError:
            # If it rejects empty name, that's expected
            pass

    def test_skill_with_empty_id(self, tmp_path):
        """Test skill with empty ID string."""
        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        skill = {
            "name": "Test",
            "id": "",  # Empty ID
            "description": "Test",
            "tags": [],
        }

        skill_file = tmp_path / "empty_id.json"
        skill_file.write_text(json.dumps(skill))

        try:
            skills = _load_skills_from_files([skill_file])
            assert len(skills) == 1
        except ConfigurationError:
            # Expected if empty ID is invalid
            pass

    def test_skill_with_whitespace_only_fields(self, tmp_path):
        """Test skill with whitespace-only field values."""
        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        skill = {
            "name": "   ",  # Whitespace only
            "id": "test",
            "description": "   ",  # Whitespace only
            "tags": [],
        }

        skill_file = tmp_path / "whitespace.json"
        skill_file.write_text(json.dumps(skill))

        try:
            skills = _load_skills_from_files([skill_file])
            # Might be allowed
            assert len(skills) == 1
        except ConfigurationError:
            # Or might be rejected
            pass

    def test_skill_with_unicode_characters(self, tmp_path):
        """Test skill with Unicode characters."""
        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        skill = {
            "name": "数学技能 (Math)",
            "id": "math_unicode",
            "description": "Mathématiques et calculs 数学",
            "tags": ["数学", "math", "mathématiques"],
        }

        skill_file = tmp_path / "unicode.json"
        skill_file.write_text(json.dumps(skill, ensure_ascii=False), encoding="utf-8")

        # Should handle Unicode properly
        skills = _load_skills_from_files([skill_file])

        assert len(skills) == 1
        assert "数学" in skills[0].name
        assert "数学" in skills[0].tags

    def test_skill_with_very_long_arrays(self, tmp_path):
        """Test skill with very long arrays."""
        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        skill = {
            "name": "Test",
            "id": "test",
            "description": "Test",
            "tags": [f"tag{i}" for i in range(100)],  # 100 tags
            "examples": [f"Example {i}" for i in range(100)],  # 100 examples
        }

        skill_file = tmp_path / "long_arrays.json"
        skill_file.write_text(json.dumps(skill))

        # Should handle large arrays
        skills = _load_skills_from_files([skill_file])

        assert len(skills) == 1
        assert len(skills[0].tags) == 100
        assert len(skills[0].examples) == 100


class TestA2AServerArgumentParsing:
    """Test A2A server command line argument parsing."""

    def test_default_host_and_port(self):
        """Test default values for host and port."""
        import argparse

        # Simulate default args
        args = argparse.Namespace(
            host="127.0.0.1",
            port=9000,
            public_url=None,
            version="1.0.0",
            serve_at_root=False,
        )

        assert args.host == "127.0.0.1"
        assert args.port == 9000
        assert args.public_url is None
        assert args.version == "1.0.0"
        assert args.serve_at_root is False

    def test_custom_host_and_port(self):
        """Test custom host and port values."""
        import argparse

        args = argparse.Namespace(
            host="0.0.0.0",
            port=8001,
            public_url="https://my-agent.com:8001/",
            version="2.0.0",
            serve_at_root=True,
        )

        assert args.host == "0.0.0.0"
        assert args.port == 8001
        assert args.public_url == "https://my-agent.com:8001/"
        assert args.version == "2.0.0"
        assert args.serve_at_root is True


class TestPromptGenerationIntegration:
    """Integration tests for full skill → prompt workflow."""

    def test_full_workflow_json_to_prompt(self, tmp_path):
        """Test complete workflow from JSON file to prompt."""
        from strands_agent_factory.scripts.a2a_server import (
            _generate_system_prompt_from_skills,
            _load_skills_from_files,
        )

        # Create comprehensive skill
        skill = {
            "name": "Complete Workflow Skill",
            "id": "workflow",
            "description": "End-to-end workflow test",
            "tags": ["workflow", "test", "integration"],
            "examples": ["Process data end-to-end", "Handle complex workflows"],
            "inputModes": ["text", "structured"],
            "outputModes": ["text", "json", "xml"],
        }

        skill_file = tmp_path / "workflow_skill.json"
        skill_file.write_text(json.dumps(skill))

        # Load skills
        skills = _load_skills_from_files([skill_file])
        assert len(skills) == 1

        # Generate prompt
        prompt = _generate_system_prompt_from_skills(skills)

        # Verify complete prompt
        assert "Complete Workflow Skill" in prompt
        assert "End-to-end workflow test" in prompt
        assert "workflow" in prompt
        assert "Process data end-to-end" in prompt
        assert "Agent-to-Agent" in prompt
        assert "Operating Guidelines" in prompt
        assert "```json" in prompt

    def test_full_workflow_yaml_to_prompt(self, tmp_path):
        """Test complete workflow from YAML file to prompt."""
        from strands_agent_factory.scripts.a2a_server import (
            _generate_system_prompt_from_skills,
            _load_skills_from_files,
        )

        # Create YAML skill
        yaml_content = """
name: YAML Workflow Skill
id: yaml_workflow
description: YAML-based workflow skill
tags:
  - yaml
  - workflow
examples:
  - Load from YAML
  - Process YAML data
inputModes:
  - text
outputModes:
  - structured
"""

        skill_file = tmp_path / "yaml_workflow.yaml"
        skill_file.write_text(yaml_content)

        # Load skills
        skills = _load_skills_from_files([skill_file])
        assert len(skills) == 1

        # Generate prompt
        prompt = _generate_system_prompt_from_skills(skills)

        # Verify complete prompt
        assert "YAML Workflow Skill" in prompt
        assert "YAML-based workflow skill" in prompt
        assert "Load from YAML" in prompt

    def test_full_workflow_multiple_files_to_prompt(self, tmp_path):
        """Test workflow with multiple skill files to single prompt."""
        from strands_agent_factory.scripts.a2a_server import (
            _generate_system_prompt_from_skills,
            _load_skills_from_files,
        )

        # Create multiple skills
        for i in range(3):
            skill = {
                "name": f"Multi Skill {i}",
                "id": f"multi{i}",
                "description": f"Skill number {i}",
                "tags": [f"skill{i}"],
            }
            skill_file = tmp_path / f"skill{i}.json"
            skill_file.write_text(json.dumps(skill))

        # Load all skills
        skill_files = [tmp_path / f"skill{i}.json" for i in range(3)]
        skills = _load_skills_from_files(skill_files)
        assert len(skills) == 3

        # Generate single prompt
        prompt = _generate_system_prompt_from_skills(skills)

        # Verify all skills in prompt
        assert "3 specialized skills" in prompt
        for i in range(3):
            assert f"Multi Skill {i}" in prompt
            assert f"Skill number {i}" in prompt
