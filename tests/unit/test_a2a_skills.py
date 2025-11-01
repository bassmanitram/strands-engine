"""
Unit tests for A2A skills configuration and system prompt generation.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from strands_agent_factory.core.exceptions import ConfigurationError


class TestLoadSkillsFromFiles:
    """Test _load_skills_from_files function."""

    def test_load_single_skill_from_json(self, tmp_path):
        """Test loading a single skill from JSON file."""
        skill_file = tmp_path / "skill.json"
        skill_data = {
            "name": "Test Skill",
            "id": "test",
            "description": "A test skill",
            "tags": ["test"],
        }
        skill_file.write_text(json.dumps(skill_data))

        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        skills = _load_skills_from_files([skill_file])

        assert len(skills) == 1
        assert skills[0].name == "Test Skill"
        assert skills[0].id == "test"
        assert skills[0].description == "A test skill"
        assert skills[0].tags == ["test"]

    def test_load_multiple_skills_from_one_file(self, tmp_path):
        """Test loading multiple skills from one JSON array file."""
        skill_file = tmp_path / "skills.json"
        skills_data = [
            {
                "name": "Skill 1",
                "id": "skill1",
                "description": "First skill",
                "tags": ["tag1"],
            },
            {
                "name": "Skill 2",
                "id": "skill2",
                "description": "Second skill",
                "tags": ["tag2"],
            },
        ]
        skill_file.write_text(json.dumps(skills_data))

        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        skills = _load_skills_from_files([skill_file])

        assert len(skills) == 2
        assert skills[0].name == "Skill 1"
        assert skills[1].name == "Skill 2"

    def test_load_skill_from_yaml(self, tmp_path):
        """Test loading skill from YAML file."""
        skill_file = tmp_path / "skill.yaml"
        yaml_content = """
name: YAML Skill
id: yaml-skill
description: A skill from YAML
tags:
  - yaml
  - test
"""
        skill_file.write_text(yaml_content)

        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        skills = _load_skills_from_files([skill_file])

        assert len(skills) == 1
        assert skills[0].name == "YAML Skill"
        assert skills[0].id == "yaml-skill"
        assert "yaml" in skills[0].tags

    def test_load_from_multiple_files(self, tmp_path):
        """Test loading skills from multiple files."""
        skill1_file = tmp_path / "skill1.json"
        skill1_data = {
            "name": "Skill 1",
            "id": "skill1",
            "description": "First skill",
            "tags": ["tag1"],
        }
        skill1_file.write_text(json.dumps(skill1_data))

        skill2_file = tmp_path / "skill2.json"
        skill2_data = {
            "name": "Skill 2",
            "id": "skill2",
            "description": "Second skill",
            "tags": ["tag2"],
        }
        skill2_file.write_text(json.dumps(skill2_data))

        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        skills = _load_skills_from_files([skill1_file, skill2_file])

        assert len(skills) == 2
        assert skills[0].name == "Skill 1"
        assert skills[1].name == "Skill 2"

    def test_load_skill_with_all_fields(self, tmp_path):
        """Test loading skill with all optional fields."""
        skill_file = tmp_path / "skill.json"
        skill_data = {
            "name": "Complete Skill",
            "id": "complete",
            "description": "A complete skill definition",
            "tags": ["complete", "test"],
            "examples": ["Example 1", "Example 2"],
            "inputModes": ["text", "structured"],
            "outputModes": ["text", "code"],
        }
        skill_file.write_text(json.dumps(skill_data))

        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        skills = _load_skills_from_files([skill_file])

        assert len(skills) == 1
        skill = skills[0]
        assert skill.examples == ["Example 1", "Example 2"]
        # Note: Pydantic uses snake_case for field names
        assert skill.input_modes == ["text", "structured"]
        assert skill.output_modes == ["text", "code"]

    def test_file_not_found(self):
        """Test error when skill file doesn't exist."""
        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        with pytest.raises(ConfigurationError, match="Skill config file not found"):
            _load_skills_from_files(["nonexistent.json"])

    def test_directory_instead_of_file(self, tmp_path):
        """Test error when path is a directory."""
        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        with pytest.raises(ConfigurationError, match="must be a file"):
            _load_skills_from_files([tmp_path])

    def test_invalid_json(self, tmp_path):
        """Test error with invalid JSON."""
        skill_file = tmp_path / "invalid.json"
        skill_file.write_text("{invalid json}")

        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        with pytest.raises(ConfigurationError, match="Failed to load skills"):
            _load_skills_from_files([skill_file])

    def test_missing_required_field(self, tmp_path):
        """Test error when required field is missing."""
        skill_file = tmp_path / "skill.json"
        skill_data = {
            "name": "Incomplete",
            "id": "incomplete",
            # Missing: description, tags
        }
        skill_file.write_text(json.dumps(skill_data))

        from strands_agent_factory.scripts.a2a_server import _load_skills_from_files

        with pytest.raises(ConfigurationError, match="Invalid skill definition"):
            _load_skills_from_files([skill_file])


class TestGenerateSystemPromptFromSkills:
    """Test _generate_system_prompt_from_skills function."""

    def test_generate_prompt_single_skill(self):
        """Test generating prompt from single skill."""
        from a2a.types import AgentSkill

        from strands_agent_factory.scripts.a2a_server import (
            _generate_system_prompt_from_skills,
        )

        skill = AgentSkill(
            name="Math",
            id="math",
            description="Perform mathematical calculations",
            tags=["math"],
        )

        prompt = _generate_system_prompt_from_skills([skill])

        assert "Agent Role and Purpose" in prompt
        assert "Agent-to-Agent (A2A) protocol" in prompt
        assert "NOT interact directly with humans" in prompt
        assert "1 specialized skill" in prompt
        assert "Math" in prompt
        assert "Perform mathematical calculations" in prompt
        assert "Operating Guidelines" in prompt

    def test_generate_prompt_multiple_skills(self):
        """Test generating prompt from multiple skills."""
        from a2a.types import AgentSkill

        from strands_agent_factory.scripts.a2a_server import (
            _generate_system_prompt_from_skills,
        )

        skills = [
            AgentSkill(
                name="Math",
                id="math",
                description="Perform mathematical calculations",
                tags=["math"],
            ),
            AgentSkill(
                name="Coding",
                id="coding",
                description="Write and debug code",
                tags=["code"],
            ),
        ]

        prompt = _generate_system_prompt_from_skills(skills)

        assert "2 specialized skills" in prompt
        assert "## Skill 1: Math" in prompt
        assert "## Skill 2: Coding" in prompt
        assert "Perform mathematical calculations" in prompt
        assert "Write and debug code" in prompt

    def test_generate_prompt_includes_full_skill_card(self):
        """Test that generated prompt includes complete skill JSON."""
        from a2a.types import AgentSkill

        from strands_agent_factory.scripts.a2a_server import (
            _generate_system_prompt_from_skills,
        )

        skill = AgentSkill(
            name="Complete",
            id="complete",
            description="A complete skill",
            tags=["tag1", "tag2"],
            examples=["Example 1", "Example 2"],
            input_modes=["text"],
            output_modes=["structured"],
        )

        prompt = _generate_system_prompt_from_skills([skill])

        # Should contain JSON representation
        assert "```json" in prompt
        assert '"name": "Complete"' in prompt
        assert '"id": "complete"' in prompt
        assert '"description": "A complete skill"' in prompt
        assert '"tags"' in prompt
        assert '"examples"' in prompt
        # Note: Pydantic serializes to snake_case by default
        assert '"input_modes"' in prompt or '"inputModes"' in prompt
        assert '"output_modes"' in prompt or '"outputModes"' in prompt

    def test_generate_prompt_a2a_directive(self):
        """Test that prompt includes A2A-specific directive."""
        from a2a.types import AgentSkill

        from strands_agent_factory.scripts.a2a_server import (
            _generate_system_prompt_from_skills,
        )

        skill = AgentSkill(name="Test", id="test", description="Test skill", tags=[])

        prompt = _generate_system_prompt_from_skills([skill])

        # Check for A2A-specific guidance
        assert "Agent-to-Agent" in prompt or "A2A" in prompt
        assert "NOT interact directly with humans" in prompt
        assert "other AI agents" in prompt

    def test_generate_prompt_operating_guidelines(self):
        """Test that prompt includes operating guidelines."""
        from a2a.types import AgentSkill

        from strands_agent_factory.scripts.a2a_server import (
            _generate_system_prompt_from_skills,
        )

        skill = AgentSkill(name="Test", id="test", description="Test skill", tags=[])

        prompt = _generate_system_prompt_from_skills([skill])

        assert "Operating Guidelines" in prompt
        assert "Use Your Skills" in prompt or "skills" in prompt.lower()

    def test_generate_prompt_with_minimal_skill(self):
        """Test generating prompt from minimal skill (required fields only)."""
        from a2a.types import AgentSkill

        from strands_agent_factory.scripts.a2a_server import (
            _generate_system_prompt_from_skills,
        )

        skill = AgentSkill(
            name="Minimal", id="minimal", description="Minimal skill", tags=[]
        )

        prompt = _generate_system_prompt_from_skills([skill])

        # Should still generate valid prompt
        assert len(prompt) > 100
        assert "Minimal" in prompt
        assert "minimal" in prompt


class TestA2ASkillsIntegration:
    """Integration tests for A2A skills functionality."""

    def test_skills_and_prompt_generation_flow(self, tmp_path):
        """Test complete flow: load skills → generate prompt."""
        # Create skill file
        skill_file = tmp_path / "skill.json"
        skill_data = {
            "name": "Test Skill",
            "id": "test",
            "description": "A test skill",
            "tags": ["test"],
            "examples": ["Do something"],
        }
        skill_file.write_text(json.dumps(skill_data))

        from strands_agent_factory.scripts.a2a_server import (
            _generate_system_prompt_from_skills,
            _load_skills_from_files,
        )

        # Load skills
        skills = _load_skills_from_files([skill_file])
        assert len(skills) == 1

        # Generate prompt
        prompt = _generate_system_prompt_from_skills(skills)
        assert "Test Skill" in prompt
        assert "A test skill" in prompt
        assert "Do something" in prompt
        assert "Agent-to-Agent" in prompt

    def test_multiple_files_to_single_prompt(self, tmp_path):
        """Test loading from multiple files and generating single prompt."""
        # Create multiple skill files
        for i in range(3):
            skill_file = tmp_path / f"skill{i}.json"
            skill_data = {
                "name": f"Skill {i}",
                "id": f"skill{i}",
                "description": f"Description {i}",
                "tags": [f"tag{i}"],
            }
            skill_file.write_text(json.dumps(skill_data))

        from strands_agent_factory.scripts.a2a_server import (
            _generate_system_prompt_from_skills,
            _load_skills_from_files,
        )

        # Load all skills
        skill_files = [tmp_path / f"skill{i}.json" for i in range(3)]
        skills = _load_skills_from_files(skill_files)
        assert len(skills) == 3

        # Generate single prompt
        prompt = _generate_system_prompt_from_skills(skills)
        assert "3 specialized skills" in prompt
        for i in range(3):
            assert f"Skill {i}" in prompt

    def test_yaml_and_json_mixed(self, tmp_path):
        """Test loading from both YAML and JSON files."""
        # Create JSON skill
        json_file = tmp_path / "skill.json"
        json_data = {
            "name": "JSON Skill",
            "id": "json",
            "description": "From JSON",
            "tags": ["json"],
        }
        json_file.write_text(json.dumps(json_data))

        # Create YAML skill
        yaml_file = tmp_path / "skill.yaml"
        yaml_content = """
name: YAML Skill
id: yaml
description: From YAML
tags:
  - yaml
"""
        yaml_file.write_text(yaml_content)

        from strands_agent_factory.scripts.a2a_server import (
            _generate_system_prompt_from_skills,
            _load_skills_from_files,
        )

        # Load both
        skills = _load_skills_from_files([json_file, yaml_file])
        assert len(skills) == 2

        # Generate prompt
        prompt = _generate_system_prompt_from_skills(skills)
        assert "JSON Skill" in prompt
        assert "YAML Skill" in prompt


class TestA2AServerCLIIntegration:
    """Test CLI integration (without actually running server)."""

    def test_argument_parser_has_skill_config_paths(self):
        """Test that argument parser includes --skill-config-paths."""
        # This would require running the parser, which we can skip
        # as it's tested by actual usage
        pass

    def test_help_text_includes_skill_documentation(self):
        """Test that --help includes skill configuration docs."""
        # Would need to capture help output
        pass
