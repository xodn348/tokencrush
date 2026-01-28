"""Local LLM provider using Ollama."""

import httpx
from typing import List, Optional, Dict, Any


class OllamaError(Exception):
    """Exception raised when Ollama operations fail."""

    pass


class OllamaProvider:
    """Local LLM provider using Ollama.

    Provides free, local LLM inference using Ollama.
    Requires Ollama to be installed and running on localhost:11434.

    Supported models:
    - deepseek-r1:8b (default)
    - llama3
    - qwen
    - Any other model installed in Ollama
    """

    def __init__(
        self,
        model: str = "deepseek-r1:8b",
        base_url: str = "http://localhost:11434",
        timeout: float = 30.0,
    ):
        """Initialize Ollama provider.

        Args:
            model: Model name to use (default: deepseek-r1:8b)
            base_url: Ollama API base URL (default: http://localhost:11434)
            timeout: Request timeout in seconds (default: 30.0)
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def __del__(self):
        """Clean up HTTP client."""
        if hasattr(self, "_client"):
            self._client.close()

    def is_available(self) -> bool:
        """Check if Ollama is installed and running.

        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            response = self._client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError):
            return False

    def chat(self, prompt: str, model: Optional[str] = None) -> str:
        """Send a chat completion request to Ollama.

        Args:
            prompt: The prompt text to send
            model: Optional model override (uses instance model if not provided)

        Returns:
            Generated response text

        Raises:
            OllamaError: If Ollama is not available or request fails
        """
        if not self.is_available():
            raise OllamaError(
                "Ollama is not available. Please ensure Ollama is installed and running.\n"
                "Install: https://ollama.ai/download\n"
                "Start: Run 'ollama serve' in terminal"
            )

        target_model = model or self.model

        try:
            response = self._client.post(
                f"{self.base_url}/api/generate",
                json={"model": target_model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()

            data = response.json()
            return data.get("response", "")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise OllamaError(
                    f"Model '{target_model}' not found. "
                    f"Install it with: ollama pull {target_model}"
                ) from e
            raise OllamaError(f"Ollama API error: {e}") from e
        except httpx.RequestError as e:
            raise OllamaError(f"Failed to connect to Ollama: {e}") from e
        except Exception as e:
            raise OllamaError(f"Unexpected error: {e}") from e

    def list_models(self) -> List[str]:
        """List all models installed in Ollama.

        Returns:
            List of model names

        Raises:
            OllamaError: If Ollama is not available or request fails
        """
        if not self.is_available():
            raise OllamaError(
                "Ollama is not available. Please ensure Ollama is installed and running.\n"
                "Install: https://ollama.ai/download\n"
                "Start: Run 'ollama serve' in terminal"
            )

        try:
            response = self._client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()

            data = response.json()
            models = data.get("models", [])
            return [model.get("name", "") for model in models if model.get("name")]

        except httpx.RequestError as e:
            raise OllamaError(f"Failed to list models: {e}") from e
        except Exception as e:
            raise OllamaError(f"Unexpected error: {e}") from e
