#!/usr/bin/env python3
"""
A2A Server Script for strands-agent-factory

Runs an agent created by AgentFactory as an Agent-to-Agent server.
The agent's tools (Python, MCP, A2A client tools) become available to other agents.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import List

# Add the package root to sys.path so we can import strands_agent_factory
script_dir = Path(__file__).parent
package_root = script_dir.parent.parent
sys.path.insert(0, str(package_root))

from dataclass_args import GenericConfigBuilder
from loguru import logger

from strands_agent_factory import AgentFactory
from strands_agent_factory.core.config import AgentFactoryConfig
from strands_agent_factory.core.exceptions import (
    ConfigurationError,
    InitializationError,
    ModelLoadError,
)
from strands_agent_factory.core.types import PathLike


def _load_skills_from_files(file_paths: List[PathLike]) -> List:
    """
    Load AgentSkill objects from configuration files.

    Supports both single skill objects and arrays of skills per file.
    Files can be in JSON or YAML format.

    Args:
        file_paths: List of paths to skill definition files (JSON or YAML)

    Returns:
        List[AgentSkill]: Loaded and validated skill objects

    Raises:
        ConfigurationError: If files are invalid or skills are malformed
        ImportError: If A2A dependencies not available
    """
    try:
        from a2a.types import AgentSkill
    except ImportError as e:
        raise ImportError(
            "A2A dependencies not available. Install with: "
            "pip install 'strands-agents[a2a]'"
        ) from e

    from strands_agent_factory.messaging.content import load_structured_file

    skills = []

    for file_path in file_paths:
        try:
            path_obj = Path(file_path)

            # Validate file exists
            if not path_obj.exists():
                raise ConfigurationError(f"Skill config file not found: {file_path}")

            if not path_obj.is_file():
                raise ConfigurationError(
                    f"Skill config path must be a file: {file_path}"
                )

            # Load JSON/YAML
            logger.debug(f"Loading skill config from {file_path}")
            data = load_structured_file(path_obj)

            # Handle single skill or list of skills
            skill_dicts = data if isinstance(data, list) else [data]

            # Convert to AgentSkill objects
            for i, skill_dict in enumerate(skill_dicts):
                try:
                    skill = AgentSkill(**skill_dict)
                    skills.append(skill)
                    logger.info(
                        f"Loaded skill '{skill.name}' (id: {skill.id}) from {file_path}"
                    )
                except Exception as e:
                    logger.error(f"Invalid skill at index {i} in {file_path}: {e}")
                    raise ConfigurationError(
                        f"Invalid skill definition in {file_path} at index {i}: {e}"
                    ) from e

        except ConfigurationError:
            raise
        except Exception as e:
            logger.error(f"Failed to load skills from {file_path}: {e}")
            raise ConfigurationError(
                f"Failed to load skills from {file_path}: {e}"
            ) from e

    logger.info(
        f"Successfully loaded {len(skills)} skill(s) from {len(file_paths)} file(s)"
    )
    return skills


def _generate_system_prompt_from_skills(skills: List) -> str:
    """
    Generate a system prompt from AgentSkill objects.

    Creates a comprehensive prompt that includes full skill cards and
    specifies that the agent is designed for agent-to-agent communication.

    Args:
        skills: List of AgentSkill objects

    Returns:
        str: Generated system prompt
    """
    prompt_parts = [
        "# Agent Role and Purpose",
        "",
        "You are an AI agent designed to be accessed exclusively by other AI agents through the Agent-to-Agent (A2A) protocol.",
        "You will NOT interact directly with humans. All requests come from other AI agents acting on behalf of users.",
        "",
        "# Your Capabilities",
        "",
        f"You provide {len(skills)} specialized skill{'s' if len(skills) != 1 else ''}:",
        "",
    ]

    # Add each skill card in full
    for i, skill in enumerate(skills, 1):
        # Convert skill to dict for display
        skill_dict = skill.model_dump()

        prompt_parts.extend(
            [
                f"## Skill {i}: {skill.name}",
                "",
                "```json",
                json.dumps(skill_dict, indent=2),
                "```",
                "",
            ]
        )

    prompt_parts.extend(
        [
            "# Operating Guidelines",
            "",
            "1. **Agent-to-Agent Context**: All requests come from other AI agents, not humans directly",
            "2. **Use Your Skills**: Apply the appropriate skill(s) based on the incoming request",
            "3. **Be Precise**: Other agents expect structured, accurate responses",
            "4. **Honor Skill Boundaries**: Only perform operations within your defined skill set",
            "5. **Provide Context**: Include relevant details from skill examples and tags when appropriate",
            "",
            "Focus on delivering high-quality results using your skills as defined above.",
        ]
    )

    return "\n".join(prompt_parts)


async def run_a2a_server(
    config_builder: GenericConfigBuilder, args: argparse.Namespace
) -> None:
    """
    Run agent as A2A server.

    Args:
        config_builder: GenericConfigBuilder instance
        args: Parsed command-line arguments

    Raises:
        InitializationError: If agent initialization fails
        ImportError: If A2A dependencies are not available
    """
    # Check if A2A dependencies are available
    try:
        from strands.multiagent.a2a import A2AServer
    except ImportError as e:
        raise ImportError(
            "A2A dependencies not available. Install with: "
            "pip install 'strands-agents[a2a]'"
        ) from e

    print("Building agent configuration...")
    try:
        config = config_builder.build_config(args, "agent_config")
    except Exception as e:
        raise ConfigurationError(f"Failed to build configuration: {e}") from e

    # Load skills from config files if provided
    skills = None
    if args.skill_config_paths:
        try:
            skills = _load_skills_from_files(args.skill_config_paths)
            print(f"   Skills: Loaded {len(skills)} custom skill(s) from config files")
            for skill in skills:
                print(f"      - {skill.name} ({skill.id}): {skill.description}")

            # Generate system prompt from skills if not explicitly provided
            if not config.system_prompt:
                config.system_prompt = _generate_system_prompt_from_skills(skills)
                print(
                    f"   System Prompt: Auto-generated from {len(skills)} skill card(s)"
                )
                logger.info("Generated system prompt from skill definitions")
            else:
                print("   System Prompt: Using explicitly provided prompt")
                logger.info(
                    "Using explicit system prompt (skills not used for prompt generation)"
                )

        except ConfigurationError as e:
            logger.error(f"Failed to load skills: {e}")
            raise
    else:
        print("   Skills: Auto-detecting from agent tools")
        print("   System Prompt: Using config or default (no auto-generation)")

    print("Initializing agent factory...")
    logger.info(f"Loading configuration with model: {config.model}")

    try:
        factory = AgentFactory(config)
        await factory.initialize()
    except Exception as e:
        raise InitializationError(f"Failed to initialize agent factory: {e}") from e

    print("Creating agent with tools...")
    agent_proxy = factory.create_agent()

    # A2A server parameters
    host = args.host
    port = args.port
    public_url = args.public_url or f"http://{host}:{port}/"
    version = args.version
    serve_at_root = args.serve_at_root

    print("Starting A2A server...")
    print(f"   Bind address: {host}:{port}")
    print(f"   Public URL: {public_url}")
    print(f"   Version: {version}")

    logger.info(
        f"A2A server configuration: host={host}, port={port}, public_url={public_url}"
    )

    with agent_proxy as agent:
        try:
            a2a_server = A2AServer(
                agent=agent,
                host=host,
                port=port,
                http_url=public_url,
                serve_at_root=serve_at_root,
                version=version,
                skills=skills,
            )

            print(f"\nA2A server running! Other agents can connect to: {public_url}")
            print("Press Ctrl+C to stop...")
            logger.info("A2A server started successfully")

            # Start the server (this blocks)
            a2a_server.serve(host=host, port=port)

        except KeyboardInterrupt:
            print("\nReceived shutdown signal...")
            logger.info("A2A server shutdown requested")
        except Exception as e:
            logger.error(f"A2A server error: {e}")
            raise
        finally:
            print("A2A server stopped.")
            logger.info("A2A server stopped")


def main():
    """Command line entry point."""
    parser = argparse.ArgumentParser(
        description="Run strands-agent-factory agent as A2A server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Minimal usage (all defaults, auto-detect skills from tools)
  strands-a2a-server --model gpt-4o
  
  # With base config file
  strands-a2a-server --agent-config agent.yaml --host 0.0.0.0 --port 8001
  
  # Override config with CLI parameters
  strands-a2a-server --agent-config base.yaml --model gpt-4o --tool-config-paths tools/math.json
  
  # Complex configuration with model config overrides
  strands-a2a-server --model-config ~/model.json --mc temperature:0.7 --mc max_tokens:2000
  
  # Custom skill definitions (auto-generates system prompt)
  strands-a2a-server --model gpt-4o --skill-config-paths skills/public-api.json
  
  # Multiple skill files (system prompt includes all skills)
  strands-a2a-server --model gpt-4o \\
    --skill-config-paths skills/math.json skills/coding.json skills/research.json
  
  # Override both skills and system prompt
  strands-a2a-server --model gpt-4o \\
    --skill-config-paths skills/math.json \\
    --system-prompt "Custom prompt that overrides auto-generation"

Skill Configuration:
  Skills define how your agent is presented to other A2A agents.
  
  By default, skills are auto-detected from your agent's tools, using tool
  names and descriptions to create AgentSkill objects automatically.
  
  Use --skill-config-paths to provide custom skill definitions when you want:
    - Custom skill names/descriptions different from tool names
    - Additional metadata (tags, examples, inputModes, outputModes)
    - Skills that aggregate multiple tools
    - Skills that represent higher-level capabilities
    - Control which capabilities are exposed to other agents
    - Auto-generate a system prompt from skill definitions
  
  Skill files are JSON or YAML files containing AgentSkill definitions.
  Each file can contain either a single skill object or an array of skills.
  
  Required fields:
    - name (str): Display name of the skill
    - id (str): Unique identifier for the skill
    - description (str): Description of what the skill does
    - tags (list[str]): Categorization tags (can be empty list)
  
  Optional fields:
    - examples (list[str]): Example use cases
    - inputModes (list[str]): Supported input modes (e.g., ["text", "url"])
    - outputModes (list[str]): Supported output modes (e.g., ["text", "structured"])
    - security (list[dict]): Security requirements
  
  Skill File Format Examples:
    
    Single skill (skills/math.json):
      {
        "name": "Mathematical Analysis",
        "id": "math",
        "description": "Perform complex mathematical calculations",
        "tags": ["math", "calculation", "analysis"],
        "examples": ["Calculate derivatives", "Solve equations"]
      }
    
    Multiple skills (skills/all.json):
      [
        {
          "name": "Math",
          "id": "math",
          "description": "Perform calculations",
          "tags": ["math"]
        },
        {
          "name": "Coding",
          "id": "coding",
          "description": "Write and debug code",
          "tags": ["code"]
        }
      ]
    
    YAML format (skills/research.yaml):
      name: Research Assistant
      id: research
      description: Search for information and summarize documents
      tags:
        - research
        - search
      examples:
        - Summarize research papers
        - Find recent developments

System Prompt Auto-Generation:
  When you provide --skill-config-paths WITHOUT an explicit --system-prompt,
  the system prompt is automatically generated from the skill definitions.
  
  The generated prompt includes:
    - A directive that the agent is for A2A use (not direct human interaction)
    - Complete skill cards in JSON format for full context
    - Operating guidelines for agent-to-agent communication
  
  To disable auto-generation, explicitly provide --system-prompt (or --agent-config
  with a system_prompt field).

Agent Configuration:
  All AgentFactoryConfig parameters are available as CLI options:
  - Single parameters override base config values
  - List parameters (--tool-config-paths, --skill-config-paths) accept multiple values
  - Object parameters (--model-config) load from files and support property overrides
  
  Property Override Format:
    --mc temperature:0.7           # Set model_config.temperature = 0.7
    --mc client.timeout:30         # Set model_config.client.timeout = 30
    --cc window_size:50            # Set conversation_config.window_size = 50

A2A Server Parameters:
  These control how the agent is exposed as an A2A server and are separate
  from the agent configuration itself.
        """,
    )

    # A2A server-specific parameters (not part of AgentFactoryConfig)
    server_group = parser.add_argument_group("A2A Server Options")
    server_group.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind server to (default: 127.0.0.1)",
    )
    server_group.add_argument(
        "--port", type=int, default=9000, help="Port to bind server to (default: 9000)"
    )
    server_group.add_argument(
        "--public-url",
        help="Public URL where this agent will be accessible (auto-generated if not provided)",
    )
    server_group.add_argument(
        "--version", default="1.0.0", help="Agent version (default: 1.0.0)"
    )
    server_group.add_argument(
        "--skill-config-paths",
        nargs="*",
        help="Path to skill definition file (JSON or YAML) containing AgentSkill objects",
    )
    server_group.add_argument(
        "--serve-at-root",
        action="store_true",
        help="Serve at root path (useful with load balancers that strip paths)",
    )
    server_group.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    # Add all AgentFactoryConfig parameters using the generic builder
    config_builder = GenericConfigBuilder(AgentFactoryConfig)
    config_builder.add_arguments(
        parser,
        base_config_name="agent-config",
        base_config_help="Base agent configuration file (JSON or YAML)",
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")

    try:
        asyncio.run(run_a2a_server(config_builder, args))

    except ConfigurationError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
    except InitializationError as e:
        print(f"Initialization Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ModelLoadError as e:
        print(f"Model Load Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ImportError as e:
        print(f"Import Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nGoodbye!", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        logger.exception("Unexpected error in A2A server")
        sys.exit(1)


if __name__ == "__main__":
    main()
