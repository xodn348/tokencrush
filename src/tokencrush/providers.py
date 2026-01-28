"""Multi-provider LLM wrapper using LiteLLM."""

from typing import List, cast, Any
from litellm import completion


class ProviderError(Exception):
    """Exception raised when LLM provider call fails."""

    pass


class LLMProvider:
    """Unified interface for multiple LLM providers via LiteLLM."""

    MODEL_ALIASES = {
        "gpt-4": "gpt-4",
        "gpt-4-turbo": "gpt-4-turbo",
        "gpt-3.5-turbo": "gpt-3.5-turbo",
        "claude-3-sonnet": "anthropic/claude-3-sonnet-20240229",
        "claude-3-opus": "anthropic/claude-3-opus-20240229",
        "claude-3-haiku": "anthropic/claude-3-haiku-20240307",
        "gemini-1.5-pro": "gemini/gemini-1.5-pro",
        "gemini-1.5-flash": "gemini/gemini-1.5-flash",
    }

    def __init__(self):
        """Initialize the LLM provider."""
        pass

    def get_model_name(self, model: str) -> str:
        """Get the full LiteLLM model name from an alias."""
        return self.MODEL_ALIASES.get(model, model)

    def chat(self, prompt: str, model: str = "gpt-4") -> str:
        """Send a chat completion request."""
        full_model = self.get_model_name(model)

        try:
            response: Any = completion(
                model=full_model,
                messages=[{"role": "user", "content": prompt}],
            )
            choices: Any = response.choices  # noqa
            message: Any = choices[0].message  # noqa
            content: str = message.content  # noqa
            return content
        except Exception as e:
            raise ProviderError(f"Failed to get response from {model}: {e}") from e

    @classmethod
    def list_models(cls) -> List[str]:
        """List all supported model aliases."""
        return list(cls.MODEL_ALIASES.keys())


class ProviderManager:
    """Manages LLM provider connections."""

    def get_provider(self, name: str):
        """Get an LLM provider by name."""
        return None
