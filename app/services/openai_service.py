"""
Gemini service wrapper for text generation using LiteLLM proxy.
"""
from typing import Optional, Dict
import os
from litellm import acompletion

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIService:
    """Service for interacting with Gemini via LiteLLM proxy."""

    def __init__(self):
        """Initialize LiteLLM with custom endpoint and API key."""
        # Validate required configuration
        if not settings.endpoint:
            logger.warning(
                "ENDPOINT is not set. Please set ENDPOINT in your .env file."
            )
        if not settings.api_key:
            logger.warning(
                "API_KEY is not set. Please set API_KEY in your .env file."
            )
        
        # Set LiteLLM environment variables for custom endpoint
        if settings.endpoint:
            os.environ["OPENAI_API_BASE"] = settings.endpoint
        if settings.api_key:
            os.environ["OPENAI_API_KEY"] = settings.api_key
        
        # Use the deployment name as the model
        self.completion_model = settings.deployment_name
        
        logger.info(f"Initialized Gemini service with model: {self.completion_model}")
        if settings.endpoint:
            logger.info(f"Using endpoint: {settings.endpoint}")
        if settings.api_key:
            logger.info("API key is configured")

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text (approximate for Gemini).
        Note: Gemini uses a different tokenizer than OpenAI, so this is an approximation.

        Args:
            text: Text to count tokens for

        Returns:
            Approximate number of tokens (using character-based estimation)
        """
        # Rough approximation: ~4 characters per token for Gemini
        return len(text) // 4

    async def generate_completion(
        self,
        prompt: str = None,
        system_message: Optional[str] = None,
        messages: Optional[list] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Generate text completion using Gemini via LiteLLM proxy.

        Args:
            prompt: User prompt (if messages not provided)
            system_message: Optional system message
            messages: Optional list of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            response_format: Optional response format (e.g., {"type": "json_object"})

        Returns:
            Generated text
        """
        try:
            logger.info(f"Generating completion with model: {self.completion_model}")

            # Prepare model kwargs
            model_kwargs = {
                "temperature": temperature or settings.temperature,
            }
            
            # Add max_tokens if specified
            if max_tokens:
                model_kwargs["max_tokens"] = max_tokens
            elif settings.max_tokens:
                model_kwargs["max_tokens"] = settings.max_tokens
            
            # Add response format if specified
            if response_format:
                model_kwargs["response_format"] = response_format

            # Build messages
            if messages:
                # Use provided messages directly
                message_list = messages
            else:
                # Build from prompt and system_message
                message_list = []
                if system_message:
                    message_list.append({"role": "system", "content": system_message})
                if prompt:
                    message_list.append({"role": "user", "content": prompt})
            
            if not message_list:
                raise ValueError("Either messages or prompt must be provided")
            
            response = await acompletion(
                model=self.completion_model,
                messages=message_list,
                **model_kwargs
            )
            
            # Handle response
            if hasattr(response, 'choices') and len(response.choices) > 0:
                if hasattr(response.choices[0], 'message') and hasattr(response.choices[0].message, 'content'):
                    generated_text = response.choices[0].message.content or ""
                else:
                    generated_text = str(response.choices[0])
            else:
                generated_text = ""

            logger.info(f"Generated {len(generated_text)} characters")

            return generated_text

        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            raise
