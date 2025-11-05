"""
Ollama LLM client wrapper.
"""

import ollama
from typing import Optional, Dict, Any
from shared.config.settings import settings
from shared.utils.logging import get_logger

logger = get_logger(__name__)


class OllamaClient:
    """Client for Ollama local LLM."""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.client = None

        try:
            # Test connection
            self.client = ollama.Client(host=self.base_url)
            # Try to list models to verify connection
            models = self.client.list()
            logger.info("ollama_connected", model=self.model, available_models=len(models.get('models', [])))
        except Exception as e:
            logger.warning("ollama_connection_failed", error=str(e))
            logger.info("ollama_fallback_mode", message="Will use fallback classification")

    async def chat(self, messages: list, temperature: float = None, max_tokens: int = None) -> str:
        """
        Send chat completion request to Ollama.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (optional)
            max_tokens: Max tokens to generate (optional)

        Returns:
            Response text from the model
        """
        if not self.client:
            raise ConnectionError("Ollama client not connected")

        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': temperature or settings.llm_temperature,
                    'num_predict': max_tokens or settings.llm_max_tokens,
                }
            )

            return response['message']['content']

        except Exception as e:
            logger.error("ollama_chat_failed", error=str(e))
            raise

    async def generate(self, prompt: str, temperature: float = None, max_tokens: int = None) -> str:
        """
        Generate completion from prompt.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature (optional)
            max_tokens: Max tokens to generate (optional)

        Returns:
            Generated text
        """
        if not self.client:
            raise ConnectionError("Ollama client not connected")

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': temperature or settings.llm_temperature,
                    'num_predict': max_tokens or settings.llm_max_tokens,
                }
            )

            return response['response']

        except Exception as e:
            logger.error("ollama_generate_failed", error=str(e))
            raise

    def is_available(self) -> bool:
        """Check if Ollama is available."""
        return self.client is not None


# Singleton instance
_ollama_client = None


def get_ollama_client() -> OllamaClient:
    """Get or create Ollama client singleton."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client
