"""Tests for free API manager with quota tracking and rotation."""

import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from tokencrush.free_api import FreeAPIManager, QuotaExceededError, UsageStats


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create a temporary cache directory for tests."""
    cache_dir = tmp_path / "tokencrush_test"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


@pytest.fixture
def manager(temp_cache_dir):
    """Create a FreeAPIManager instance with temporary cache."""
    return FreeAPIManager(cache_dir=temp_cache_dir)


@pytest.fixture
def mock_config():
    """Mock ConfigManager to return test API keys."""
    with patch("tokencrush.free_api.ConfigManager") as mock:
        config_instance = Mock()
        config_instance.get_api_key.side_effect = lambda provider: {
            "gemini": "test-gemini-key",
            "groq": "test-groq-key",
            "deepseek": "test-deepseek-key",
        }.get(provider)
        mock.return_value = config_instance
        yield mock


class TestFreeAPIManager:
    """Test suite for FreeAPIManager."""

    def test_initialization(self, manager, temp_cache_dir):
        """Test manager initializes with correct defaults."""
        assert manager.cache_dir == temp_cache_dir
        assert manager.quota_file == temp_cache_dir / "quotas.json"
        assert len(manager.usage) == 3  # gemini, groq, deepseek
        assert "gemini" in manager.usage
        assert "groq" in manager.usage
        assert "deepseek" in manager.usage

    def test_provider_configuration(self, manager):
        """Test provider configurations are correct."""
        assert manager.PROVIDERS["gemini"]["limit_rpm"] == 15
        assert manager.PROVIDERS["gemini"]["limit_rpd"] == 1000
        assert manager.PROVIDERS["groq"]["limit_rpm"] == 30
        assert manager.PROVIDERS["groq"]["limit_rpd"] is None
        assert manager.PROVIDERS["deepseek"]["limit_rpm"] is None
        assert manager.PROVIDERS["deepseek"]["limit_rpd"] is None

    def test_usage_persistence(self, manager, temp_cache_dir):
        """Test usage statistics are saved and loaded correctly."""
        # Modify usage
        manager.usage["gemini"].requests_today = 50
        manager.usage["gemini"].requests_this_minute = 5
        manager._save_usage()

        # Create new manager instance
        new_manager = FreeAPIManager(cache_dir=temp_cache_dir)

        # Verify usage was loaded
        assert new_manager.usage["gemini"].requests_today == 50
        assert new_manager.usage["gemini"].requests_this_minute == 5

    def test_quota_check_within_limits(self, manager):
        """Test quota check passes when within limits."""
        manager.usage["gemini"].requests_today = 10
        manager.usage["gemini"].requests_this_minute = 5

        assert manager._check_quota("gemini") is True

    def test_quota_check_daily_limit_exceeded(self, manager):
        """Test quota check fails when daily limit exceeded."""
        manager.usage["gemini"].requests_today = 1000
        manager.usage["gemini"].requests_this_minute = 5

        assert manager._check_quota("gemini") is False

    def test_quota_check_minute_limit_exceeded(self, manager):
        """Test quota check fails when per-minute limit exceeded."""
        manager.usage["gemini"].requests_today = 10
        manager.usage["gemini"].requests_this_minute = 15

        assert manager._check_quota("gemini") is False

    def test_quota_check_no_limits(self, manager):
        """Test quota check always passes for providers without limits."""
        manager.usage["deepseek"].requests_today = 10000
        manager.usage["deepseek"].requests_this_minute = 1000

        assert manager._check_quota("deepseek") is True

    def test_reset_daily_counter(self, manager):
        """Test daily counter resets after midnight."""
        # Set usage to yesterday
        manager.usage["gemini"].requests_today = 500
        manager.usage["gemini"].daily_reset_time = time.time() - 86400  # 24 hours ago

        # Check quota (should trigger reset)
        manager._reset_if_needed("gemini")

        assert manager.usage["gemini"].requests_today == 0

    def test_reset_minute_counter(self, manager):
        """Test minute counter resets after 60 seconds."""
        # Set usage to 61 seconds ago
        manager.usage["gemini"].requests_this_minute = 10
        manager.usage["gemini"].minute_window_start = time.time() - 61

        # Check quota (should trigger reset)
        manager._reset_if_needed("gemini")

        assert manager.usage["gemini"].requests_this_minute == 0

    @patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"})
    def test_has_api_key_from_env(self, manager):
        """Test API key detection from environment variable."""
        assert manager._has_api_key("gemini") is True

    def test_has_api_key_missing(self, manager):
        """Test API key detection when key is missing."""
        with patch.object(manager.config, "get_api_key", return_value=None):
            assert manager._has_api_key("gemini") is False

    @patch.dict(
        "os.environ",
        {
            "GOOGLE_API_KEY": "test-gemini",
            "GROQ_API_KEY": "test-groq",
            "DEEPSEEK_API_KEY": "test-deepseek",
        },
    )
    def test_get_available_provider_priority(self, manager):
        """Test provider selection follows priority order (deepseek > groq > gemini)."""
        # All providers available
        provider = manager.get_available_provider()
        assert provider == "deepseek"

        # Exhaust deepseek (shouldn't happen, but test the logic)
        manager.usage["deepseek"].requests_this_minute = 999999
        manager.PROVIDERS["deepseek"]["limit_rpm"] = 1  # Temporarily add limit
        provider = manager.get_available_provider()
        assert provider == "groq"

        # Restore deepseek config
        manager.PROVIDERS["deepseek"]["limit_rpm"] = None

    @patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"})
    def test_get_available_provider_all_exhausted(self, manager):
        """Test returns None when all providers exhausted."""
        # Exhaust all providers
        manager.usage["gemini"].requests_today = 1000
        manager.usage["groq"].requests_this_minute = 30
        manager.usage["deepseek"].requests_this_minute = 999999
        manager.PROVIDERS["deepseek"]["limit_rpm"] = 1  # Temporarily add limit

        provider = manager.get_available_provider()
        assert provider is None

        # Restore config
        manager.PROVIDERS["deepseek"]["limit_rpm"] = None

    @patch("tokencrush.free_api.completion")
    @patch.dict("os.environ", {"DEEPSEEK_API_KEY": "test-key"})
    def test_chat_auto_mode(self, mock_completion, manager):
        """Test chat with automatic provider selection."""
        # Mock API response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response"))]
        mock_completion.return_value = mock_response

        response = manager.chat("Hello, world!", provider="auto")

        assert response == "Test response"
        mock_completion.assert_called_once()

        # Verify usage was incremented
        assert manager.usage["deepseek"].requests_today == 1
        assert manager.usage["deepseek"].requests_this_minute == 1

    @patch("tokencrush.free_api.completion")
    @patch.dict("os.environ", {"GROQ_API_KEY": "test-key"})
    def test_chat_specific_provider(self, mock_completion, manager):
        """Test chat with specific provider selection."""
        # Mock API response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Groq response"))]
        mock_completion.return_value = mock_response

        response = manager.chat("Hello!", provider="groq")

        assert response == "Groq response"

        # Verify correct model was used
        call_args = mock_completion.call_args
        assert call_args[1]["model"] == "groq/llama-3.3-70b-versatile"

    def test_chat_invalid_provider(self, manager):
        """Test chat raises error for invalid provider."""
        with pytest.raises(ValueError, match="Unknown provider"):
            manager.chat("Hello!", provider="invalid")

    def test_chat_no_api_key(self, manager):
        """Test chat raises error when API key is missing."""
        with patch.object(manager, "_has_api_key", return_value=False):
            with pytest.raises(ValueError, match="No API key configured"):
                manager.chat("Hello!", provider="gemini")

    def test_chat_quota_exceeded_specific_provider(self, manager):
        """Test chat raises error when specific provider quota exceeded."""
        with patch.object(manager, "_has_api_key", return_value=True):
            with patch.object(manager, "_check_quota", return_value=False):
                with pytest.raises(QuotaExceededError, match="exceeded its quota"):
                    manager.chat("Hello!", provider="gemini")

    def test_chat_quota_exceeded_all_providers(self, manager):
        """Test chat raises error when all providers exhausted in auto mode."""
        with patch.object(manager, "get_available_provider", return_value=None):
            with pytest.raises(QuotaExceededError, match="All providers have exceeded"):
                manager.chat("Hello!", provider="auto")

    @patch.dict(
        "os.environ", {"GOOGLE_API_KEY": "test-gemini", "GROQ_API_KEY": "test-groq"}
    )
    def test_get_usage(self, manager):
        """Test get_usage returns correct statistics."""
        # Set some usage
        manager.usage["gemini"].requests_today = 100
        manager.usage["gemini"].requests_this_minute = 5
        manager.usage["groq"].requests_today = 50
        manager.usage["groq"].requests_this_minute = 10

        usage = manager.get_usage()

        assert usage["gemini"]["has_api_key"] is True
        assert usage["gemini"]["requests_today"] == 100
        assert usage["gemini"]["requests_this_minute"] == 5
        assert usage["gemini"]["daily_limit"] == 1000
        assert usage["gemini"]["minute_limit"] == 15
        assert usage["gemini"]["model"] == "gemini/gemini-2.0-flash-exp"

        assert usage["groq"]["has_api_key"] is True
        assert usage["groq"]["requests_today"] == 50
        assert usage["groq"]["requests_this_minute"] == 10
        assert usage["groq"]["daily_limit"] is None
        assert usage["groq"]["minute_limit"] == 30

        assert usage["deepseek"]["has_api_key"] is False

    def test_list_providers(self, manager):
        """Test list_providers returns all provider names."""
        providers = manager.list_providers()

        assert len(providers) == 3
        assert "gemini" in providers
        assert "groq" in providers
        assert "deepseek" in providers

    @patch("tokencrush.free_api.completion")
    @patch.dict("os.environ", {"DEEPSEEK_API_KEY": "test-key"})
    def test_increment_usage(self, mock_completion, manager):
        """Test usage counters increment correctly."""
        # Mock API response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_completion.return_value = mock_response

        initial_today = manager.usage["deepseek"].requests_today
        initial_minute = manager.usage["deepseek"].requests_this_minute

        manager.chat("Test", provider="auto")

        assert manager.usage["deepseek"].requests_today == initial_today + 1
        assert manager.usage["deepseek"].requests_this_minute == initial_minute + 1
        assert manager.usage["deepseek"].last_request_time > 0

    @patch("tokencrush.free_api.completion")
    @patch.dict("os.environ", {"DEEPSEEK_API_KEY": "test-key"})
    def test_chat_with_kwargs(self, mock_completion, manager):
        """Test chat passes additional kwargs to completion."""
        # Mock API response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_completion.return_value = mock_response

        manager.chat("Test", provider="auto", temperature=0.7, max_tokens=100)

        # Verify kwargs were passed
        call_args = mock_completion.call_args
        assert call_args[1]["temperature"] == 0.7
        assert call_args[1]["max_tokens"] == 100
