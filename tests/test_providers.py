"""Tests for the LLMProvider module."""

import pytest
from unittest.mock import patch, MagicMock


class TestLLMProvider:
    """Tests for LLMProvider class."""

    def test_chat_basic(self, mock_env_keys):
        """Test basic chat completion."""
        from tokencrush.providers import LLMProvider
        
        with patch('tokencrush.providers.completion') as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hello!"
            mock_completion.return_value = mock_response
            
            provider = LLMProvider()
            result = provider.chat("Hello", model="gpt-4")
            
            assert result == "Hello!"

    def test_model_mapping(self):
        """Test model name to LiteLLM format mapping."""
        from tokencrush.providers import LLMProvider
        
        provider = LLMProvider()
        assert provider.get_model_name("gpt-4") == "gpt-4"
        assert "claude" in provider.get_model_name("claude-3-sonnet")
        assert "gemini" in provider.get_model_name("gemini-1.5-pro")

    def test_list_models(self):
        """Test listing supported models."""
        from tokencrush.providers import LLMProvider
        
        models = LLMProvider.list_models()
        assert len(models) > 0
        assert "gpt-4" in models

    def test_error_handling(self, mock_env_keys):
        """Test error handling when API fails."""
        from tokencrush.providers import LLMProvider, ProviderError
        
        with patch('tokencrush.providers.completion') as mock_completion:
            mock_completion.side_effect = Exception("API Error")
            
            provider = LLMProvider()
            with pytest.raises(ProviderError):
                provider.chat("Hello", model="gpt-4")
