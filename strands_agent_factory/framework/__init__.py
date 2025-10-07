"""
Framework adapter modules for strands_agent_factory.

This package provides framework-specific adapters that enable strands_agent_factory
to work with different AI providers and frameworks. Each adapter handles the
unique requirements and capabilities of its target framework while presenting
a consistent interface to the engine.

Supported Frameworks:
    - OpenAI: Direct OpenAI API integration
    - Anthropic: Direct Anthropic API integration  
    - LiteLLM: Universal adapter for multiple providers via LiteLLM
    - Ollama: Local model serving via Ollama
    - AWS Bedrock: AWS managed model services

Common Adapter Responsibilities:
    - Model loading and configuration
    - Tool schema adaptation for provider compatibility
    - Message formatting and system prompt handling
    - Provider-specific authentication and connection management
    - Error handling and logging specific to each provider

The adapter system allows strands_agent_factory to remain provider-agnostic while
supporting the full capabilities of each framework through specialized
implementations.

Usage:
    Adapters are typically loaded automatically based on model strings,
    but can also be imported directly for advanced use cases.
    
Example:
    >>> from strands_agent_factory.framework import LiteLLMAdapter
    >>> adapter = LiteLLMAdapter()
    >>> model = adapter.load_model("gpt-4o")
"""