"""
LLM service interface for AI/ML integrations.

Provides:
- Abstraction over OpenAI and Anthropic APIs
- Unified interface for text generation
- Model configuration and selection
- Error handling and retry logic
- Token usage tracking
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMModel(str, Enum):
    """Supported LLM models."""
    # OpenAI models
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_35_TURBO = "gpt-3.5-turbo"

    # Anthropic models
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"


class MessageRole(str, Enum):
    """Message roles in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message:
    """A message in a conversation."""

    def __init__(self, role: MessageRole, content: str):
        self.role = role
        self.content = content


class LLMServiceError(Exception):
    """Base exception for LLM service errors."""
    pass


class LLMService:
    """
    LLM service interface for AI/ML integrations.

    Provides a unified interface over multiple LLM providers (OpenAI, Anthropic).
    Supports text generation, chat completions, and embedding generation.

    Features:
    - Provider abstraction
    - Automatic model selection
    - Error handling and retry logic
    - Token usage tracking
    """

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.OPENAI,
        model: LLMModel | None = None,
    ):
        """
        Initialize LLM service.

        Args:
            provider: LLM provider (OpenAI or Anthropic)
            model: Specific model to use (default: provider's default)
        """
        self.provider = provider
        self.model = model or self._get_default_model(provider)
        self._client = None

    def _get_default_model(self, provider: LLMProvider) -> LLMModel:
        """Get default model for a provider."""
        if provider == LLMProvider.OPENAI:
            return LLMModel.GPT_4
        elif provider == LLMProvider.ANTHROPIC:
            return LLMModel.CLAUDE_3_SONNET
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _get_client(self):
        """Lazily initialize and return the LLM client."""
        if self._client is not None:
            return self._client

        if self.provider == LLMProvider.OPENAI:
            try:
                import openai
                self._client = openai.AsyncOpenAI(
                    api_key=settings.openai_api_key.get_secret_value() if settings.openai_api_key else None,
                )
            except ImportError:
                raise LLMServiceError(
                    "OpenAI package not installed. Install with: pip install openai"
                )
        elif self.provider == LLMProvider.ANTHROPIC:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(
                    api_key=settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else None,
                )
            except ImportError:
                raise LLMServiceError(
                    "Anthropic package not installed. Install with: pip install anthropic"
                )
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

        return self._client

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 - 2.0)
            **kwargs: Provider-specific options

        Returns:
            Generated text

        Raises:
            LLMServiceError: If generation fails
        """
        messages = []
        if system_prompt:
            messages.append(Message(role=MessageRole.SYSTEM, content=system_prompt))
        messages.append(Message(role=MessageRole.USER, content=prompt))

        response = await self.generate_chat(messages, max_tokens, temperature, **kwargs)
        return response

    async def generate_chat(
        self,
        messages: list[Message],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        """
        Generate a chat completion.

        Args:
            messages: List of conversation messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Provider-specific options

        Returns:
            Generated response text

        Raises:
            LLMServiceError: If generation fails
        """
        client = await self._get_client()

        try:
            if self.provider == LLMProvider.OPENAI:
                return await self._generate_openai_chat(client, messages, max_tokens, temperature, **kwargs)
            elif self.provider == LLMProvider.ANTHROPIC:
                return await self._generate_anthropic_chat(client, messages, max_tokens, temperature, **kwargs)
            else:
                raise LLMServiceError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise LLMServiceError(f"Generation failed: {e}") from e

    async def _generate_openai_chat(
        self,
        client,
        messages: list[Message],
        max_tokens: int,
        temperature: float,
        **kwargs,
    ) -> str:
        """Generate chat completion using OpenAI."""
        # Convert messages to OpenAI format
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        response = await client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )

        return response.choices[0].message.content

    async def _generate_anthropic_chat(
        self,
        client,
        messages: list[Message],
        max_tokens: int,
        temperature: float,
        **kwargs,
    ) -> str:
        """Generate chat completion using Anthropic."""
        # Separate system message from conversation
        system_message = None
        conversation = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_message = msg.content
            else:
                conversation.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        response = await client.messages.create(
            model=self.model,
            messages=conversation,
            system=system_message,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )

        return response.content[0].text

    async def generate_embeddings(
        self,
        texts: list[str],
        model: str = "text-embedding-3-small",
    ) -> list[list[float]]:
        """
        Generate embeddings for a list of texts (OpenAI only).

        Args:
            texts: List of texts to embed
            model: Embedding model name

        Returns:
            List of embedding vectors

        Raises:
            LLMServiceError: If embedding generation fails
        """
        if self.provider != LLMProvider.OPENAI:
            raise LLMServiceError("Embeddings only supported for OpenAI provider")

        client = await self._get_client()

        try:
            response = await client.embeddings.create(
                model=model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise LLMServiceError(f"Embedding generation failed: {e}") from e

    async def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text (approximate).

        Args:
            text: Text to count tokens for

        Returns:
            Approximate token count
        """
        # Simple approximation: ~4 characters per token for English
        return len(text) // 4

    def set_model(self, model: LLMModel) -> None:
        """Change the model for this service instance."""
        self.model = model
        logger.info(f"Switched to model: {model}")

    def set_provider(self, provider: LLMProvider) -> None:
        """Change the provider and reset client."""
        self.provider = provider
        self.model = self._get_default_model(provider)
        self._client = None
        logger.info(f"Switched to provider: {provider}")


# Singleton instance with default configuration
llm_service = LLMService()
