"""Tests for TokenCrush SDK module."""

import pytest
from unittest.mock import MagicMock, patch

from tokencrush.sdk import TokenCrush, SDKStats
from tokencrush.router import RouterResponse
from tokencrush.compressor import CompressResult
from tokencrush.cache import CacheStats


@pytest.fixture
def mock_cache():
    """Create a mock SemanticCache."""
    cache = MagicMock()
    cache.get.return_value = None  # Default: cache miss
    cache.stats.return_value = CacheStats(
        total_queries=10,
        cache_hits=3,
        cache_misses=7,
        hit_rate=0.3,
    )
    return cache


@pytest.fixture
def mock_router():
    """Create a mock SmartRouter."""
    router = MagicMock()
    router.cache = MagicMock()
    router.cache.stats.return_value = CacheStats(
        total_queries=10,
        cache_hits=3,
        cache_misses=7,
        hit_rate=0.3,
    )
    router.chat.return_value = RouterResponse(
        response="Test response",
        source="local",
        cost=0.0,
        tokens_saved=50,
    )
    return router


@pytest.fixture
def mock_compressor():
    """Create a mock TokenCompressor."""
    compressor = MagicMock()
    compressor.compress.return_value = CompressResult(
        original_tokens=100,
        compressed_tokens=50,
        compressed_text="compressed text",
        ratio=0.5,
    )
    return compressor


@pytest.fixture
def sdk(mock_router, mock_compressor):
    """Create a TokenCrush SDK instance with mocked dependencies."""
    with patch("tokencrush.sdk.SmartRouter", return_value=mock_router):
        with patch("tokencrush.sdk.TokenCompressor", return_value=mock_compressor):
            sdk = TokenCrush()
            sdk.router = mock_router
            sdk.compressor = mock_compressor
            return sdk


class TestSDKStats:
    """Tests for SDKStats dataclass."""

    def test_create_sdk_stats(self):
        """Test creating SDKStats."""
        stats = SDKStats(
            cache_hit_rate=0.5,
            total_queries=100,
            cached=50,
            cost_saved=0.0,
        )
        assert stats.cache_hit_rate == 0.5
        assert stats.total_queries == 100
        assert stats.cached == 50
        assert stats.cost_saved == 0.0

    def test_sdk_stats_zero_values(self):
        """Test SDKStats with zero values."""
        stats = SDKStats(
            cache_hit_rate=0.0,
            total_queries=0,
            cached=0,
            cost_saved=0.0,
        )
        assert stats.cache_hit_rate == 0.0
        assert stats.total_queries == 0
        assert stats.cached == 0


class TestTokenCrushInit:
    """Tests for TokenCrush initialization."""

    def test_init_default(self):
        """Test TokenCrush initialization with defaults."""
        with patch("tokencrush.sdk.SmartRouter"):
            with patch("tokencrush.sdk.TokenCompressor"):
                sdk = TokenCrush()
                assert sdk.router is not None
                assert sdk.compressor is not None

    def test_init_with_cache(self, mock_cache):
        """Test TokenCrush initialization with custom cache."""
        with patch("tokencrush.sdk.SmartRouter") as mock_router_class:
            with patch("tokencrush.sdk.TokenCompressor"):
                sdk = TokenCrush(cache=mock_cache)
                # Verify SmartRouter was called with the cache
                mock_router_class.assert_called_once()
                call_kwargs = mock_router_class.call_args[1]
                assert call_kwargs["cache"] == mock_cache

    def test_init_with_compression_rate(self):
        """Test TokenCrush initialization with custom compression rate."""
        with patch("tokencrush.sdk.SmartRouter") as mock_router_class:
            with patch("tokencrush.sdk.TokenCompressor"):
                sdk = TokenCrush(compression_rate=0.3)
                # Verify SmartRouter was called with compression_rate
                mock_router_class.assert_called_once()
                call_kwargs = mock_router_class.call_args[1]
                assert call_kwargs["compression_rate"] == 0.3


class TestTokenCrushChat:
    """Tests for TokenCrush.chat() method."""

    def test_chat_default_mode(self, sdk):
        """Test chat with default smart mode."""
        response = sdk.chat("What is AI?")
        assert response == "Test response"
        sdk.router.chat.assert_called_once_with("What is AI?", strategy="smart")

    def test_chat_local_mode(self, sdk):
        """Test chat with local mode."""
        response = sdk.chat("Hello", mode="local")
        assert response == "Test response"
        sdk.router.chat.assert_called_once_with("Hello", strategy="local")

    def test_chat_free_mode(self, sdk):
        """Test chat with free API mode."""
        response = sdk.chat("Test", mode="free")
        assert response == "Test response"
        sdk.router.chat.assert_called_once_with("Test", strategy="free-api")

    def test_chat_cache_only_mode(self, sdk):
        """Test chat with cache-only mode."""
        response = sdk.chat("Cached", mode="cache-only")
        assert response == "Test response"
        sdk.router.chat.assert_called_once_with("Cached", strategy="cache-only")

    def test_chat_invalid_mode(self, sdk):
        """Test chat with invalid mode raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            sdk.chat("Test", mode="invalid")
        assert "Invalid mode" in str(exc_info.value)
        assert "invalid" in str(exc_info.value)

    def test_chat_empty_prompt(self, sdk):
        """Test chat with empty prompt."""
        # The router should handle empty prompt validation
        sdk.chat("")
        sdk.router.chat.assert_called_once_with("", strategy="smart")

    def test_chat_long_prompt(self, sdk):
        """Test chat with long prompt."""
        long_prompt = "Test " * 1000
        response = sdk.chat(long_prompt)
        assert response == "Test response"
        sdk.router.chat.assert_called_once_with(long_prompt, strategy="smart")

    def test_chat_special_characters(self, sdk):
        """Test chat with special characters."""
        prompt = "What is 2+2? @#$%^&*()"
        response = sdk.chat(prompt)
        assert response == "Test response"
        sdk.router.chat.assert_called_once_with(prompt, strategy="smart")

    def test_chat_mode_case_sensitive(self, sdk):
        """Test that mode parameter is case-sensitive."""
        with pytest.raises(ValueError):
            sdk.chat("Test", mode="SMART")

    def test_chat_all_valid_modes(self, sdk):
        """Test all valid mode values."""
        modes = ["smart", "local", "free", "cache-only"]
        for mode in modes:
            sdk.router.reset_mock()
            response = sdk.chat("Test", mode=mode)
            assert response == "Test response"
            assert sdk.router.chat.called


class TestTokenCrushCompress:
    """Tests for TokenCrush.compress() method."""

    def test_compress_default_rate(self, sdk):
        """Test compress with default rate."""
        result = sdk.compress("Long text to compress")
        assert result == "compressed text"
        sdk.compressor.compress.assert_called_once_with(
            "Long text to compress", rate=0.5
        )

    def test_compress_custom_rate(self, sdk):
        """Test compress with custom rate."""
        result = sdk.compress("Text", rate=0.3)
        assert result == "compressed text"
        sdk.compressor.compress.assert_called_once_with("Text", rate=0.3)

    def test_compress_empty_text(self, sdk):
        """Test compress with empty text returns empty string."""
        result = sdk.compress("")
        assert result == ""
        sdk.compressor.compress.assert_not_called()

    def test_compress_rate_zero(self, sdk):
        """Test compress with rate 0.0."""
        result = sdk.compress("Text", rate=0.0)
        assert result == "compressed text"
        sdk.compressor.compress.assert_called_once_with("Text", rate=0.0)

    def test_compress_rate_one(self, sdk):
        """Test compress with rate 1.0."""
        result = sdk.compress("Text", rate=1.0)
        assert result == "compressed text"
        sdk.compressor.compress.assert_called_once_with("Text", rate=1.0)

    def test_compress_rate_invalid_negative(self, sdk):
        """Test compress with negative rate raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            sdk.compress("Text", rate=-0.1)
        assert "between 0.0 and 1.0" in str(exc_info.value)

    def test_compress_rate_invalid_over_one(self, sdk):
        """Test compress with rate > 1.0 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            sdk.compress("Text", rate=1.5)
        assert "between 0.0 and 1.0" in str(exc_info.value)

    def test_compress_long_text(self, sdk):
        """Test compress with very long text."""
        long_text = "Word " * 10000
        result = sdk.compress(long_text)
        assert result == "compressed text"
        sdk.compressor.compress.assert_called_once_with(long_text, rate=0.5)

    def test_compress_special_characters(self, sdk):
        """Test compress with special characters."""
        text = "Special chars: @#$%^&*()_+-=[]{}|;:',.<>?/~`"
        result = sdk.compress(text)
        assert result == "compressed text"
        sdk.compressor.compress.assert_called_once_with(text, rate=0.5)

    def test_compress_unicode(self, sdk):
        """Test compress with unicode characters."""
        text = "Unicode: 你好世界 🌍 مرحبا"
        result = sdk.compress(text)
        assert result == "compressed text"
        sdk.compressor.compress.assert_called_once_with(text, rate=0.5)


class TestTokenCrushStats:
    """Tests for TokenCrush.stats() method."""

    def test_stats_basic(self, sdk):
        """Test getting basic statistics."""
        stats = sdk.stats()
        assert isinstance(stats, SDKStats)
        assert stats.cache_hit_rate == 0.3
        assert stats.total_queries == 10
        assert stats.cached == 3
        assert stats.cost_saved == 0.0

    def test_stats_zero_queries(self, sdk):
        """Test stats with zero queries."""
        sdk.router.cache.stats.return_value = CacheStats(
            total_queries=0,
            cache_hits=0,
            cache_misses=0,
            hit_rate=0.0,
        )
        stats = sdk.stats()
        assert stats.total_queries == 0
        assert stats.cached == 0
        assert stats.cache_hit_rate == 0.0

    def test_stats_perfect_hit_rate(self, sdk):
        """Test stats with perfect cache hit rate."""
        sdk.router.cache.stats.return_value = CacheStats(
            total_queries=100,
            cache_hits=100,
            cache_misses=0,
            hit_rate=1.0,
        )
        stats = sdk.stats()
        assert stats.cache_hit_rate == 1.0
        assert stats.total_queries == 100
        assert stats.cached == 100

    def test_stats_cost_always_zero(self, sdk):
        """Test that cost_saved is always 0 (100% FREE architecture)."""
        stats = sdk.stats()
        assert stats.cost_saved == 0.0

    def test_stats_multiple_calls(self, sdk):
        """Test calling stats multiple times."""
        stats1 = sdk.stats()
        stats2 = sdk.stats()
        assert stats1.cache_hit_rate == stats2.cache_hit_rate
        assert stats1.total_queries == stats2.total_queries
        assert sdk.router.cache.stats.call_count == 2


class TestTokenCrushIntegration:
    """Integration tests for TokenCrush SDK."""

    def test_chat_then_stats(self, sdk):
        """Test chat followed by stats."""
        response = sdk.chat("Question?")
        assert response == "Test response"

        stats = sdk.stats()
        assert isinstance(stats, SDKStats)
        assert stats.total_queries == 10

    def test_compress_then_chat(self, sdk):
        """Test compress followed by chat."""
        compressed = sdk.compress("Long text")
        assert compressed == "compressed text"

        response = sdk.chat("Question?")
        assert response == "Test response"

    def test_multiple_chats_different_modes(self, sdk):
        """Test multiple chats with different modes."""
        modes = ["smart", "local", "free", "cache-only"]
        for mode in modes:
            sdk.router.reset_mock()
            response = sdk.chat("Test", mode=mode)
            assert response == "Test response"

    def test_compress_multiple_rates(self, sdk):
        """Test compress with multiple rates."""
        rates = [0.1, 0.3, 0.5, 0.7, 0.9]
        for rate in rates:
            sdk.compressor.reset_mock()
            result = sdk.compress("Text", rate=rate)
            assert result == "compressed text"
            sdk.compressor.compress.assert_called_once_with("Text", rate=rate)

    def test_workflow_cache_hit_then_miss(self, sdk):
        """Test workflow with cache hit then miss."""
        # First call - cache miss
        sdk.router.cache.stats.return_value = CacheStats(
            total_queries=1,
            cache_hits=0,
            cache_misses=1,
            hit_rate=0.0,
        )
        response1 = sdk.chat("Question 1")
        stats1 = sdk.stats()
        assert stats1.cache_hit_rate == 0.0

        # Second call - cache hit
        sdk.router.cache.stats.return_value = CacheStats(
            total_queries=2,
            cache_hits=1,
            cache_misses=1,
            hit_rate=0.5,
        )
        response2 = sdk.chat("Question 2")
        stats2 = sdk.stats()
        assert stats2.cache_hit_rate == 0.5


class TestTokenCrushEdgeCases:
    """Edge case tests for TokenCrush SDK."""

    def test_chat_whitespace_only_prompt(self, sdk):
        """Test chat with whitespace-only prompt."""
        response = sdk.chat("   \n\t  ")
        assert response == "Test response"

    def test_compress_whitespace_only(self, sdk):
        """Test compress with whitespace-only text."""
        result = sdk.compress("   \n\t  ")
        assert result == "compressed text"

    def test_compress_single_character(self, sdk):
        """Test compress with single character."""
        result = sdk.compress("A")
        assert result == "compressed text"

    def test_chat_very_long_prompt(self, sdk):
        """Test chat with extremely long prompt."""
        long_prompt = "A" * 100000
        response = sdk.chat(long_prompt)
        assert response == "Test response"

    def test_compress_very_long_text(self, sdk):
        """Test compress with extremely long text."""
        long_text = "Word " * 100000
        result = sdk.compress(long_text)
        assert result == "compressed text"

    def test_stats_after_no_queries(self, sdk):
        """Test stats when no queries have been made."""
        sdk.router.cache.stats.return_value = CacheStats(
            total_queries=0,
            cache_hits=0,
            cache_misses=0,
            hit_rate=0.0,
        )
        stats = sdk.stats()
        assert stats.total_queries == 0
        assert stats.cached == 0
