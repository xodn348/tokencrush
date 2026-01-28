"""Tests for the OllamaProvider module."""

import pytest
from unittest.mock import patch, MagicMock
import httpx


class TestOllamaProvider:
    """Tests for OllamaProvider class."""

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        from tokencrush.local import OllamaProvider

        provider = OllamaProvider()
        assert provider.model == "deepseek-r1:8b"
        assert provider.base_url == "http://localhost:11434"
        assert provider.timeout == 30.0

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        from tokencrush.local import OllamaProvider

        provider = OllamaProvider(
            model="llama3", base_url="http://custom:8080", timeout=60.0
        )
        assert provider.model == "llama3"
        assert provider.base_url == "http://custom:8080"
        assert provider.timeout == 60.0

    def test_is_available_success(self):
        """Test is_available when Ollama is running."""
        from tokencrush.local import OllamaProvider

        provider = OllamaProvider()

        with patch.object(provider._client, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            assert provider.is_available() is True
            mock_get.assert_called_once_with("http://localhost:11434/api/tags")

    def test_is_available_connection_error(self):
        """Test is_available when Ollama is not running."""
        from tokencrush.local import OllamaProvider

        provider = OllamaProvider()

        with patch.object(provider._client, "get") as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")

            assert provider.is_available() is False

    def test_is_available_timeout(self):
        """Test is_available when request times out."""
        from tokencrush.local import OllamaProvider

        provider = OllamaProvider()

        with patch.object(provider._client, "get") as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Timeout")

            assert provider.is_available() is False

    def test_chat_success(self):
        """Test successful chat completion."""
        from tokencrush.local import OllamaProvider

        provider = OllamaProvider()

        with (
            patch.object(provider._client, "get") as mock_get,
            patch.object(provider._client, "post") as mock_post,
        ):
            # Mock is_available check
            mock_get_response = MagicMock()
            mock_get_response.status_code = 200
            mock_get.return_value = mock_get_response

            # Mock chat response
            mock_post_response = MagicMock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {
                "response": "Hello! How can I help you?"
            }
            mock_post.return_value = mock_post_response

            result = provider.chat("Hello")

            assert result == "Hello! How can I help you?"
            mock_post.assert_called_once_with(
                "http://localhost:11434/api/generate",
                json={"model": "deepseek-r1:8b", "prompt": "Hello", "stream": False},
            )

    def test_chat_with_custom_model(self):
        """Test chat with custom model override."""
        from tokencrush.local import OllamaProvider

        provider = OllamaProvider()

        with (
            patch.object(provider._client, "get") as mock_get,
            patch.object(provider._client, "post") as mock_post,
        ):
            # Mock is_available check
            mock_get_response = MagicMock()
            mock_get_response.status_code = 200
            mock_get.return_value = mock_get_response

            # Mock chat response
            mock_post_response = MagicMock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {"response": "Response"}
            mock_post.return_value = mock_post_response

            provider.chat("Test", model="llama3")

            call_args = mock_post.call_args
            assert call_args[1]["json"]["model"] == "llama3"

    def test_chat_ollama_not_available(self):
        """Test chat when Ollama is not available."""
        from tokencrush.local import OllamaProvider, OllamaError

        provider = OllamaProvider()

        with patch.object(provider._client, "get") as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")

            with pytest.raises(OllamaError) as exc_info:
                provider.chat("Hello")

            assert "not available" in str(exc_info.value)
            assert "ollama.ai/download" in str(exc_info.value)

    def test_chat_model_not_found(self):
        """Test chat when model is not installed."""
        from tokencrush.local import OllamaProvider, OllamaError

        provider = OllamaProvider()

        with (
            patch.object(provider._client, "get") as mock_get,
            patch.object(provider._client, "post") as mock_post,
        ):
            # Mock is_available check
            mock_get_response = MagicMock()
            mock_get_response.status_code = 200
            mock_get.return_value = mock_get_response

            # Mock 404 error
            mock_post_response = MagicMock()
            mock_post_response.status_code = 404
            mock_post.return_value = mock_post_response
            mock_post_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not found", request=MagicMock(), response=mock_post_response
            )

            with pytest.raises(OllamaError) as exc_info:
                provider.chat("Hello")

            assert "not found" in str(exc_info.value)
            assert "ollama pull" in str(exc_info.value)

    def test_list_models_success(self):
        """Test listing installed models."""
        from tokencrush.local import OllamaProvider

        provider = OllamaProvider()

        with patch.object(provider._client, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "deepseek-r1:8b"},
                    {"name": "llama3"},
                    {"name": "qwen"},
                ]
            }
            mock_get.return_value = mock_response

            models = provider.list_models()

            assert len(models) == 3
            assert "deepseek-r1:8b" in models
            assert "llama3" in models
            assert "qwen" in models

    def test_list_models_empty(self):
        """Test listing models when none are installed."""
        from tokencrush.local import OllamaProvider

        provider = OllamaProvider()

        with patch.object(provider._client, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"models": []}
            mock_get.return_value = mock_response

            models = provider.list_models()

            assert models == []

    def test_list_models_ollama_not_available(self):
        """Test list_models when Ollama is not available."""
        from tokencrush.local import OllamaProvider, OllamaError

        provider = OllamaProvider()

        with patch.object(provider._client, "get") as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")

            with pytest.raises(OllamaError) as exc_info:
                provider.list_models()

            assert "not available" in str(exc_info.value)

    def test_base_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from base_url."""
        from tokencrush.local import OllamaProvider

        provider = OllamaProvider(base_url="http://localhost:11434/")
        assert provider.base_url == "http://localhost:11434"
