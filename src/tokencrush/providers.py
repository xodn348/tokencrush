"""Multi-provider LLM wrapper using LiteLLM."""

from typing import List, cast, Any
from litellm import completion


class ProviderError(Exception):
    """Exception raised when LLM provider call fails."""

    pass


class LLMProvider:
    """Unified interface for multiple LLM providers via LiteLLM."""

    MODEL_ALIASES = {
        # OpenAI GPT-5 family (2025)
        "gpt-5.2": "gpt-5.2",
        "gpt-5.2-pro": "gpt-5.2-pro",
        "gpt-5.2-codex": "gpt-5.2-codex",
        "gpt-5-mini": "gpt-5-mini",
        "gpt-5-nano": "gpt-5-nano",
        # OpenAI legacy
        "gpt-4.1": "gpt-4.1",
        "gpt-4-turbo": "gpt-4-turbo",
        "gpt-4": "gpt-4",
        "gpt-3.5-turbo": "gpt-3.5-turbo",
        # Anthropic Claude 4.5 family (2025)
        "claude-sonnet-4-5": "anthropic/claude-sonnet-4-5-20250929",
        "claude-opus-4-5": "anthropic/claude-opus-4-5-20251101",
        "claude-haiku-4-5": "anthropic/claude-haiku-4-5-20251001",
        # Anthropic Claude 4 legacy
        "claude-opus-4-1": "anthropic/claude-opus-4-1-20250805",
        "claude-sonnet-4": "anthropic/claude-sonnet-4-20250514",
        "claude-opus-4": "anthropic/claude-opus-4-20250514",
        # Anthropic Claude 3 legacy
        "claude-3-sonnet": "anthropic/claude-3-sonnet-20240229",
        "claude-3-opus": "anthropic/claude-3-opus-20240229",
        "claude-3-haiku": "anthropic/claude-3-haiku-20240307",
        # Google Gemini 3 family (2025)
        "gemini-3-pro": "gemini/gemini-3-pro-preview",
        "gemini-3-pro-image": "gemini/gemini-3-pro-image-preview",
        # Google Gemini 2.x
        "gemini-2.5-flash": "gemini/gemini-2.5-flash",
        "gemini-2.0-flash": "gemini/gemini-2.0-flash-exp",
        # Google Gemini legacy
        "gemini-1.5-pro": "gemini/gemini-1.5-pro",
        "gemini-1.5-flash": "gemini/gemini-1.5-flash",
        # DeepSeek (2025)
        "deepseek-v3.2": "deepseek/deepseek-chat",
        "deepseek-reasoner": "deepseek/deepseek-reasoner",
        # Groq (2025) - fast inference
        "groq-llama-3.3": "groq/llama-3.3-70b-versatile",
        "groq-llama-3.1": "groq/llama-3.1-8b-instant",
        "groq-gpt-oss": "groq/openai/gpt-oss-120b",
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
