"""
AWS Bedrock framework adapter for strands_agent_factory.

This module provides the BedrockAdapter class, which enables strands_agent_factory
to work with AWS Bedrock managed AI services. AWS Bedrock provides access to
foundation models from multiple providers (Anthropic, Amazon, Cohere, etc.)
through a unified AWS API with enterprise features.

The Bedrock adapter handles:
- AWS Bedrock model instantiation and configuration
- Content adaptation for Bedrock's specific format requirements
- Tool schema compatibility with Bedrock's function calling
- AWS authentication and configuration management
- Image format validation and binary file handling

This adapter is designed for enterprise applications that need AWS integration,
compliance features, and managed model serving without direct provider APIs.
"""

from typing import List, Optional, Dict, Any
from loguru import logger
from strands.models.bedrock import BedrockModel
from strands.types.content import Messages
from botocore.config import Config as BotocoreConfig

from .base import FrameworkAdapter
from ..core.types import Tool

# Valid image formats supported by AWS Bedrock
VALID_IMAGE_FORMATS = {'gif', 'jpeg', 'png', 'webp'}


class BedrockAdapter(FrameworkAdapter):
    """
    Framework adapter for AWS Bedrock managed AI services.
    
    BedrockAdapter provides integration with AWS Bedrock, which offers access
    to foundation models from multiple providers through AWS's managed platform.
    The adapter handles Bedrock-specific content formatting, authentication,
    and configuration requirements.
    
    Key features:
    - Integration with AWS Bedrock managed models
    - Strict content formatting for Bedrock Converse API compliance
    - Image format validation and binary file handling
    - AWS authentication and configuration management
    - Support for multiple model providers through Bedrock
    
    The adapter is particularly valuable for:
    - Enterprise applications requiring AWS integration
    - Applications needing compliance and governance features
    - Multi-provider model access through a single AWS interface
    - Scenarios requiring AWS security and billing integration
    
    Supported model providers through Bedrock:
    - Anthropic Claude models
    - Amazon Titan models
    - Cohere Command models
    - Meta Llama models
    - Stability AI models
    
    Example:
        Basic usage with Claude on Bedrock::
        
            adapter = BedrockAdapter()
            model = adapter.load_model("anthropic.claude-3-5-sonnet-20241022-v2:0")
            
        With AWS configuration::
        
            config = {
                "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
                "temperature": 0.7,
                "boto_client_config": {
                    "region_name": "us-east-1",
                    "aws_access_key_id": "AKIA...",
                    "aws_secret_access_key": "...",
                }
            }
            model = adapter.load_model(config=config)
    """

    @property
    def framework_name(self) -> str:
        """
        Get the framework name for this adapter.
        
        Returns:
            str: Framework identifier "bedrock" for logging and debugging
        """
        logger.trace("BedrockAdapter.framework_name called")
        return "bedrock"

    def load_model(self, model_name: Optional[str] = None, model_config: Optional[Dict[str, Any]] = None) -> BedrockModel:
        """
        Load a model using AWS Bedrock.
        
        Creates and configures a BedrockModel instance for use with strands-agents.
        Handles AWS-specific configuration including region settings, authentication,
        and Bedrock model identifiers.
        
        Bedrock model identifiers follow AWS naming conventions:
        - "anthropic.claude-3-5-sonnet-20241022-v2:0" (Anthropic Claude)
        - "amazon.titan-text-express-v1" (Amazon Titan)
        - "cohere.command-r-plus-v1:0" (Cohere Command)
        - "meta.llama3-2-90b-instruct-v1:0" (Meta Llama)
        
        Args:
            model_name: Bedrock model identifier (optional if in model_config)
            model_config: Configuration dictionary with model and AWS settings
            
        Returns:
            BedrockModel: Configured model instance ready for agent use
            
        Example:
            Basic model loading::
            
                model = adapter.load_model("anthropic.claude-3-5-sonnet-20241022-v2:0")
                
            With AWS client configuration::
            
                config = {
                    "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
                    "temperature": 0.8,
                    "max_tokens": 4000,
                    "boto_client_config": {
                        "region_name": "us-west-2",
                        "aws_access_key_id": "AKIA...",
                        "aws_secret_access_key": "..."
                    }
                }
                model = adapter.load_model(config=config)
                
        Note:
            The boto_client_config contains AWS-specific settings passed to
            the boto3 client constructor. This includes authentication,
            region, and other AWS SDK configuration options.
        """
        logger.trace(f"BedrockAdapter.load_model called with model_name='{model_name}', model_config={model_config}")
        
        model_config = model_config or {}
        logger.debug(f"Using model_config: {model_config}")
        
        # Set model identifier if provided
        if model_name:
            model_config["model_id"] = model_name
            logger.debug(f"Set model_config['model_id'] to '{model_name}'")
        
        # Extract AWS boto client configuration
        boto_client_config = model_config.pop("boto_client_config", None)
        if boto_client_config:
            boto_client_config = BotocoreConfig(**boto_client_config)

        logger.debug(f"Extracted boto_client_config: {boto_client_config}")
        logger.debug(f"Final model_config after boto_client_config extraction: {model_config}")
        
        # Create and return the Bedrock model
        logger.debug(f"Creating BedrockModel with boto_client_config={boto_client_config}, model_config={model_config}")
        model = BedrockModel(boto_client_config=boto_client_config, **model_config)
        
        logger.debug(f"BedrockModel created successfully: {type(model).__name__}")
        return model

    def adapt_content(self, messages: Messages) -> Messages:
        """
        Transform message content for Bedrock API compliance.
        
        Rigorously transforms message content into the strict format required by
        the Bedrock Converse API. Handles text and image blocks from any source
        (new files or session history) and replaces invalid binary files with
        placeholders.
        
        The transformation ensures:
        - Text blocks are properly formatted for Bedrock
        - Image blocks meet Bedrock's format requirements
        - Unsupported binary files are converted to text placeholders
        - Message structure complies with Bedrock API expectations
        
        Args:
            messages: Message content to adapt for Bedrock
            
        Returns:
            Messages: Content transformed for Bedrock API compliance
            
        Note:
            Bedrock has strict requirements for content formatting, particularly
            for images. Only specific image formats (gif, jpeg, png, webp) are
            supported, and the content structure must match Bedrock's expectations
            exactly. This method ensures full compliance with these requirements.
            
        Example:
            Content transformation::
            
                # Input: Mixed content with various formats
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"text": "Analyze this image"},
                            {"type": "image", "source": {"data": "...", "media_type": "image/png"}}
                        ]
                    }
                ]
                
                # Output: Bedrock-compliant format
                adapted = adapter.adapt_content(messages)
        """
        logger.trace(f"BedrockAdapter.adapt_content called with {len(messages)} messages")
        
        transformed_messages = []

        for message_idx, message in enumerate(messages):
            logger.trace(f"Processing message {message_idx}: {message.get('role', 'unknown')}")
            
            content = message.get("content")
            if not isinstance(content, list):
                # Handle non-list content by converting to text
                if content:
                    logger.trace("Converting non-list content to text block")
                    transformed_messages.append({"text": str(content)})
                continue

            transformed_content = []

            for block_idx, block in enumerate(content):
                logger.trace(f"Processing content block {block_idx}: {type(block)}")
                
                if not isinstance(block, dict):
                    logger.trace("Skipping non-dict block")
                    continue

                # Case 1: Handle text blocks in any format
                if block.get("type") == "text" or "text" in block:
                    text_content = block.get("text", "")
                    transformed_content.append({"text": text_content})
                    logger.trace(f"Added text block with {len(text_content)} characters")
                    continue

                # Case 2: Handle image blocks in the 'strands' format
                if block.get("type") == "image" and "source" in block:
                    source = block.get("source", {})
                    image_format = block.get("format", None)

                    if image_format in VALID_IMAGE_FORMATS and source.get("data"):
                        # Valid image format, pass through
                        transformed_content.append(block)
                        logger.trace(f"Added valid image block with format: {image_format}")
                    else:
                        # Invalid or unsupported format, create placeholder
                        logger.warning(f"File with media type '{image_format}' is not a supported image format for Bedrock. Representing as a text placeholder.")
                        placeholder_text = f"[User uploaded a binary file of type '{image_format}' that cannot be displayed.]"
                        transformed_content.append({"text": placeholder_text})
                        logger.trace(f"Added placeholder for unsupported format: {image_format}")
                    continue
            
            # Update message content if we have transformed blocks
            if transformed_content:
                new_message = message.copy()
                new_message["content"] = transformed_content
                transformed_messages.append(new_message)
                logger.trace(f"Added transformed message with {len(transformed_content)} content blocks")

        logger.trace(f"Content adaptation completed, returning {len(transformed_messages)} messages")
        return transformed_messages

    def adapt_tools(self, tools: List[Tool], model_string: str) -> List[Tool]:
        """
        Adapt tools for Bedrock compatibility.
        
        AWS Bedrock generally supports standard tool schemas with the underlying
        model providers handling the specifics. This method performs minimal
        adaptation but provides an extension point for Bedrock-specific
        tool optimizations if needed.
        
        Args:
            tools: List of tool objects to adapt
            model_string: Model string for potential model-specific adaptations
            
        Returns:
            List[Tool]: Tools adapted for Bedrock (unchanged by default)
            
        Note:
            Bedrock delegates tool handling to the underlying model providers
            (Anthropic, Amazon, etc.), so tool schemas typically don't require
            Bedrock-specific modifications. This method provides a hook for
            future Bedrock-specific tool adaptations if they become necessary.
        """
        logger.trace(f"BedrockAdapter.adapt_tools called with {len(tools) if tools else 0} tools, model_string='{model_string}'")
        
        # Bedrock generally supports standard tool schemas via underlying providers
        if tools:
            logger.debug("Bedrock adapter: Tools passed through without modification")
        else:
            logger.debug("No tools to adapt")
        
        logger.trace(f"Tool adaptation completed, returning {len(tools) if tools else 0} tools")
        return tools