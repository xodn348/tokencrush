"""Tests for smart router module."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from tokencrush.router import SmartRouter, RouterResponse, RoutingError
from tokencrush.compressor import CompressResult
from tokencrush.local import OllamaError
from tokencrush.free_api import QuotaExceededError


@pytest.fixture
def mock_cache():
    """Create a mock SemanticCache."""
    cache = MagicMock()
    cache.get.return_value = None  # Default: cache miss
    cache._total_queries = 0
    cache._cache_hits = 0
    cache.stats.return_value = MagicMock(hit_rate=0.0)
    return cache


@pytest.fixture
def mock_local():
    """Create a mock OllamaProvider."""
    local = MagicMock()
    local.is_available.return_value = True
    local.chat.return_value = "Local LLM response"
    local.model = "deepseek-r1:8b"
    return local


@pytest.fixture
def mock_free_api():
    """Create a mock FreeAPIManager."""
    free_api = MagicMock()
    free_api.get_available_provider.return_value = "gemini"
    free_api.chat.return_value = "Free API response"
    free_api.get_usage.return_value = {"gemini": {"quota_available": True}}
    return free_api


@pytest.fixture
def mock_compressor():
    """Create a mock TokenCompressor."""
    compressor = MagicMock()
    compressor.compress.return_value = CompressResult(
        original_tokens=100,
        compressed_tokens=50,
        compressed_text="compressed prompt",
        ratio=0.5,
    )
    return compressor


@pytest.fixture
def router(mock_cache, mock_local, mock_free_api, mock_compressor):
    """Create a SmartRouter with mocked dependencies."""
    return SmartRouter(
        cache=mock_cache,
        local=mock_local,
        free_api=mock_free_api,
        compressor=mock_compressor,
    )


class TestRouterResponse:
    """Tests for RouterResponse dataclass."""

    def test_create_router_response(self):
        """Test creating a RouterResponse."""
        response = RouterResponse(
            response="Hello world",
            source="cache",
            cost=0.0,
            tokens_saved=50,
        )
        assert response.response == "Hello world"
        assert response.source == "cache"
        assert response.cost == 0.0
        assert response.tokens_saved == 50

    def test_router_response_equality(self):
        """Test RouterResponse equality."""
        r1 = RouterResponse("test", "cache", 0.0, 10)
        r2 = RouterResponse("test", "cache", 0.0, 10)
        assert r1 == r2


class TestSmartRouterInit:
    """Tests for SmartRouter initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default components."""
        with (
            patch("tokencrush.router.SemanticCache") as MockCache,
            patch("tokencrush.router.OllamaProvider") as MockLocal,
            patch("tokencrush.router.FreeAPIManager") as MockFreeAPI,
            patch("tokencrush.router.TokenCompressor") as MockCompressor,
        ):
            router = SmartRouter()

            MockCache.assert_called_once()
            MockLocal.assert_called_once()
            MockFreeAPI.assert_called_once()
            MockCompressor.assert_called_once()

    def test_init_with_custom_components(
        self, mock_cache, mock_local, mock_free_api, mock_compressor
    ):
        """Test initialization with provided components."""
        router = SmartRouter(
            cache=mock_cache,
            local=mock_local,
            free_api=mock_free_api,
            compressor=mock_compressor,
        )

        assert router.cache is mock_cache
        assert router.local is mock_local
        assert router.free_api is mock_free_api
        assert router.compressor is mock_compressor

    def test_init_with_custom_compression_rate(
        self, mock_cache, mock_local, mock_free_api, mock_compressor
    ):
        """Test initialization with custom compression rate."""
        router = SmartRouter(
            cache=mock_cache,
            local=mock_local,
            free_api=mock_free_api,
            compressor=mock_compressor,
            compression_rate=0.3,
        )
        assert router.compression_rate == 0.3


class TestCacheHit:
    """Tests for cache hit scenarios."""

    def test_cache_hit_returns_cached_response(self, router, mock_cache):
        """Test that cache hit returns cached response immediately."""
        mock_cache.get.return_value = "Cached response"

        result = router.chat("test prompt")

        assert result.response == "Cached response"
        assert result.source == "cache"
        assert result.cost == 0.0
        assert result.tokens_saved == 0  # No compression for cache hits

    def test_cache_hit_does_not_call_compression(
        self, router, mock_cache, mock_compressor
    ):
        """Test that cache hit skips compression."""
        mock_cache.get.return_value = "Cached response"

        router.chat("test prompt")

        mock_compressor.compress.assert_not_called()

    def test_cache_hit_does_not_call_providers(
        self, router, mock_cache, mock_local, mock_free_api
    ):
        """Test that cache hit skips all providers."""
        mock_cache.get.return_value = "Cached response"

        router.chat("test prompt")

        mock_local.chat.assert_not_called()
        mock_free_api.chat.assert_not_called()


class TestCacheMiss:
    """Tests for cache miss scenarios."""

    def test_cache_miss_triggers_compression(self, router, mock_cache, mock_compressor):
        """Test that cache miss triggers prompt compression."""
        mock_cache.get.return_value = None

        router.chat("test prompt")

        mock_compressor.compress.assert_called_once()

    def test_cache_miss_stores_response(self, router, mock_cache):
        """Test that cache miss stores the response."""
        mock_cache.get.return_value = None

        router.chat("test prompt")

        # Should store with original prompt (not compressed)
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args[0]
        assert call_args[0] == "test prompt"  # Original prompt

    def test_tokens_saved_calculated_correctly(
        self, router, mock_cache, mock_compressor
    ):
        """Test tokens saved calculation from compression."""
        mock_cache.get.return_value = None
        mock_compressor.compress.return_value = CompressResult(
            original_tokens=200,
            compressed_tokens=75,
            compressed_text="compressed",
            ratio=0.375,
        )

        result = router.chat("test prompt")

        assert result.tokens_saved == 125  # 200 - 75


class TestSmartRouting:
    """Tests for smart routing strategy."""

    def test_smart_route_prefers_local(self, router, mock_local, mock_free_api):
        """Test smart routing prefers local LLM when available."""
        result = router.chat("test prompt", strategy="smart")

        assert result.source == "local"
        mock_local.chat.assert_called_once()
        mock_free_api.chat.assert_not_called()

    def test_smart_route_fallback_to_free_api(self, router, mock_local, mock_free_api):
        """Test smart routing falls back to free API when local unavailable."""
        mock_local.is_available.return_value = False

        result = router.chat("test prompt", strategy="smart")

        assert result.source == "free-api"
        mock_free_api.chat.assert_called_once()

    def test_smart_route_handles_local_error(self, router, mock_local, mock_free_api):
        """Test smart routing handles local LLM errors gracefully."""
        mock_local.is_available.return_value = True
        mock_local.chat.side_effect = OllamaError("Connection failed")

        result = router.chat("test prompt", strategy="smart")

        assert result.source == "free-api"
        mock_free_api.chat.assert_called_once()

    def test_smart_route_all_providers_fail(self, router, mock_local, mock_free_api):
        """Test smart routing raises error when all providers fail."""
        mock_local.is_available.return_value = False
        mock_free_api.chat.side_effect = QuotaExceededError("All quotas exceeded")

        with pytest.raises(RoutingError) as exc_info:
            router.chat("test prompt", strategy="smart")

        assert "All providers failed" in str(exc_info.value)


class TestLocalStrategy:
    """Tests for local-only routing strategy."""

    def test_local_strategy_uses_ollama(self, router, mock_local, mock_free_api):
        """Test local strategy uses Ollama directly."""
        result = router.chat("test prompt", strategy="local")

        assert result.source == "local"
        mock_local.chat.assert_called_once()
        mock_free_api.chat.assert_not_called()

    def test_local_strategy_raises_on_unavailable(self, router, mock_local):
        """Test local strategy raises when Ollama unavailable."""
        mock_local.is_available.return_value = False
        mock_local.chat.side_effect = OllamaError("Ollama not running")

        with pytest.raises(OllamaError):
            router.chat("test prompt", strategy="local")

    def test_local_strategy_uses_compressed_prompt(
        self, router, mock_local, mock_compressor
    ):
        """Test local strategy sends compressed prompt."""
        mock_compressor.compress.return_value = CompressResult(
            original_tokens=100,
            compressed_tokens=50,
            compressed_text="compressed prompt text",
            ratio=0.5,
        )

        router.chat("original prompt", strategy="local")

        mock_local.chat.assert_called_with("compressed prompt text")


class TestFreeAPIStrategy:
    """Tests for free-api-only routing strategy."""

    def test_free_api_strategy_skips_local(self, router, mock_local, mock_free_api):
        """Test free-api strategy skips local LLM."""
        mock_local.is_available.return_value = True

        result = router.chat("test prompt", strategy="free-api")

        assert result.source == "free-api"
        mock_local.chat.assert_not_called()
        mock_free_api.chat.assert_called_once()

    def test_free_api_strategy_raises_on_quota_exceeded(self, router, mock_free_api):
        """Test free-api strategy raises when quota exceeded."""
        mock_free_api.chat.side_effect = QuotaExceededError("No quota")

        with pytest.raises(QuotaExceededError):
            router.chat("test prompt", strategy="free-api")

    def test_free_api_uses_auto_provider(self, router, mock_free_api):
        """Test free-api strategy uses auto provider selection."""
        router.chat("test prompt", strategy="free-api")

        mock_free_api.chat.assert_called_with("compressed prompt", provider="auto")


class TestCacheOnlyStrategy:
    """Tests for cache-only routing strategy."""

    def test_cache_only_returns_on_hit(self, router, mock_cache):
        """Test cache-only strategy returns cached response."""
        mock_cache.get.return_value = "Cached response"

        result = router.chat("test prompt", strategy="cache-only")

        assert result.response == "Cached response"
        assert result.source == "cache"

    def test_cache_only_raises_on_miss(self, router, mock_cache):
        """Test cache-only strategy raises error on cache miss."""
        mock_cache.get.return_value = None

        with pytest.raises(RoutingError) as exc_info:
            router.chat("test prompt", strategy="cache-only")

        assert "Cache miss" in str(exc_info.value)

    def test_cache_only_does_not_call_providers(
        self, router, mock_cache, mock_local, mock_free_api
    ):
        """Test cache-only does not call any providers on miss."""
        mock_cache.get.return_value = None

        with pytest.raises(RoutingError):
            router.chat("test prompt", strategy="cache-only")

        mock_local.chat.assert_not_called()
        mock_free_api.chat.assert_not_called()


class TestInputValidation:
    """Tests for input validation."""

    def test_empty_prompt_raises_error(self, router):
        """Test empty prompt raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            router.chat("")

        assert "empty" in str(exc_info.value).lower()

    def test_whitespace_prompt_raises_error(self, router):
        """Test whitespace-only prompt raises ValueError."""
        with pytest.raises(ValueError):
            router.chat("   ")

    def test_invalid_strategy_raises_error(self, router):
        """Test invalid strategy raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            router.chat("test", strategy="invalid")

        assert "Invalid strategy" in str(exc_info.value)

    def test_error_message_lists_valid_strategies(self, router):
        """Test error message includes valid strategy options."""
        with pytest.raises(ValueError) as exc_info:
            router.chat("test", strategy="wrong")

        error_msg = str(exc_info.value)
        assert "cache-only" in error_msg
        assert "free-api" in error_msg
        assert "local" in error_msg
        assert "smart" in error_msg


class TestCompressionHandling:
    """Tests for compression error handling."""

    def test_compression_failure_uses_original_prompt(
        self, router, mock_cache, mock_compressor, mock_local
    ):
        """Test compression failure falls back to original prompt."""
        mock_cache.get.return_value = None
        mock_compressor.compress.side_effect = Exception("Compression failed")

        # Should not raise - falls back to original prompt
        result = router.chat("original prompt")

        # Should still work
        assert result is not None

    def test_compression_failure_reports_zero_savings(
        self, router, mock_cache, mock_compressor
    ):
        """Test compression failure reports zero tokens saved."""
        mock_cache.get.return_value = None
        mock_compressor.compress.side_effect = Exception("Compression failed")

        result = router.chat("original prompt")

        assert result.tokens_saved == 0


class TestProviderStatus:
    """Tests for provider status methods."""

    def test_is_local_available(self, router, mock_local):
        """Test is_local_available returns correct status."""
        mock_local.is_available.return_value = True
        assert router.is_local_available() is True

        mock_local.is_available.return_value = False
        assert router.is_local_available() is False

    def test_is_free_api_available(self, router, mock_free_api):
        """Test is_free_api_available returns correct status."""
        mock_free_api.get_available_provider.return_value = "gemini"
        assert router.is_free_api_available() is True

        mock_free_api.get_available_provider.return_value = None
        assert router.is_free_api_available() is False

    def test_get_provider_status_returns_dict(
        self, router, mock_cache, mock_local, mock_free_api
    ):
        """Test get_provider_status returns complete status dict."""
        mock_local.is_available.return_value = True
        mock_free_api.get_available_provider.return_value = "gemini"

        status = router.get_provider_status()

        assert "cache" in status
        assert "local" in status
        assert "free_api" in status
        assert status["cache"]["available"] is True
        assert status["local"]["available"] is True
        assert status["free_api"]["available"] is True


class TestCostTracking:
    """Tests for cost tracking (always $0 for 100% FREE architecture)."""

    def test_cache_hit_cost_is_zero(self, router, mock_cache):
        """Test cache hit cost is always zero."""
        mock_cache.get.return_value = "Cached"
        result = router.chat("test")
        assert result.cost == 0.0

    def test_local_cost_is_zero(self, router, mock_local):
        """Test local LLM cost is always zero."""
        result = router.chat("test", strategy="local")
        assert result.cost == 0.0

    def test_free_api_cost_is_zero(self, router, mock_free_api, mock_local):
        """Test free API cost is always zero."""
        mock_local.is_available.return_value = False
        result = router.chat("test", strategy="free-api")
        assert result.cost == 0.0


class TestCacheStorage:
    """Tests for cache storage behavior."""

    def test_response_cached_after_local_generation(
        self, router, mock_cache, mock_local
    ):
        """Test response is cached after local LLM generation."""
        mock_cache.get.return_value = None
        mock_local.chat.return_value = "Generated response"

        router.chat("test prompt")

        mock_cache.set.assert_called_once_with("test prompt", "Generated response")

    def test_response_cached_after_free_api_generation(
        self, router, mock_cache, mock_free_api, mock_local
    ):
        """Test response is cached after free API generation."""
        mock_cache.get.return_value = None
        mock_local.is_available.return_value = False
        mock_free_api.chat.return_value = "API response"

        router.chat("test prompt")

        mock_cache.set.assert_called_once_with("test prompt", "API response")

    def test_original_prompt_used_for_cache_key(
        self, router, mock_cache, mock_compressor
    ):
        """Test original (not compressed) prompt is used for cache key."""
        mock_cache.get.return_value = None
        mock_compressor.compress.return_value = CompressResult(
            original_tokens=100,
            compressed_tokens=50,
            compressed_text="completely different compressed text",
            ratio=0.5,
        )

        router.chat("original prompt text")

        # Cache should be set with original prompt, not compressed
        call_args = mock_cache.set.call_args[0]
        assert call_args[0] == "original prompt text"


class TestCompressionRate:
    """Tests for compression rate configuration."""

    def test_default_compression_rate(
        self, mock_cache, mock_local, mock_free_api, mock_compressor
    ):
        """Test default compression rate is 0.5."""
        router = SmartRouter(
            cache=mock_cache,
            local=mock_local,
            free_api=mock_free_api,
            compressor=mock_compressor,
        )
        assert router.compression_rate == 0.5

    def test_custom_compression_rate_used(
        self, mock_cache, mock_local, mock_free_api, mock_compressor
    ):
        """Test custom compression rate is passed to compressor."""
        router = SmartRouter(
            cache=mock_cache,
            local=mock_local,
            free_api=mock_free_api,
            compressor=mock_compressor,
            compression_rate=0.3,
        )
        mock_cache.get.return_value = None

        router.chat("test prompt")

        mock_compressor.compress.assert_called_with("test prompt", rate=0.3)
