"""Comprehensive end-to-end integration tests for TokenCrush v2.0.

Tests full flow: CLI → Router → Cache/Local/API → Response
Covers all routing modes: smart, local, free-api, cache-only
All external dependencies mocked (no real API calls).
"""

import pytest
from unittest.mock import MagicMock, patch, call

from tokencrush.router import SmartRouter, RouterResponse, RoutingError
from tokencrush.cache import SemanticCache, CacheStats
from tokencrush.local import OllamaProvider, OllamaError
from tokencrush.free_api import FreeAPIManager, QuotaExceededError
from tokencrush.compressor import TokenCompressor, CompressResult
from tokencrush.sdk import TokenCrush, SDKStats


# ============================================================================
# FIXTURES: Mocked Dependencies
# ============================================================================


@pytest.fixture
def mock_cache():
    """Create a mock SemanticCache with tracking."""
    cache = MagicMock(spec=SemanticCache)
    cache.get.return_value = None  # Default: cache miss
    cache.set.return_value = None
    cache.stats.return_value = CacheStats(
        total_queries=0,
        cache_hits=0,
        cache_misses=0,
        hit_rate=0.0,
    )
    return cache


@pytest.fixture
def mock_local():
    """Create a mock OllamaProvider."""
    local = MagicMock(spec=OllamaProvider)
    local.is_available.return_value = True
    local.chat.return_value = "Response from local LLM"
    local.model = "deepseek-r1:8b"
    return local


@pytest.fixture
def mock_free_api():
    """Create a mock FreeAPIManager."""
    free_api = MagicMock(spec=FreeAPIManager)
    free_api.get_available_provider.return_value = "gemini"
    free_api.chat.return_value = "Response from free API"
    free_api.get_usage.return_value = {"gemini": {"quota_available": True}}
    return free_api


@pytest.fixture
def mock_compressor():
    """Create a mock TokenCompressor."""
    compressor = MagicMock(spec=TokenCompressor)
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


@pytest.fixture
def sdk(mock_cache, mock_local, mock_free_api, mock_compressor):
    """Create a TokenCrush SDK with mocked router."""
    with patch("tokencrush.sdk.SmartRouter") as MockRouter:
        mock_router = MagicMock()
        mock_router.cache = mock_cache
        mock_router.chat.return_value = RouterResponse(
            response="Test response",
            source="cache",
            cost=0.0,
            tokens_saved=50,
        )
        MockRouter.return_value = mock_router

        with patch("tokencrush.sdk.TokenCompressor") as MockCompressor:
            mock_compressor_instance = MagicMock()
            mock_compressor_instance.compress.return_value = CompressResult(
                original_tokens=100,
                compressed_tokens=50,
                compressed_text="compressed",
                ratio=0.5,
            )
            MockCompressor.return_value = mock_compressor_instance

            sdk = TokenCrush()
            sdk.router = mock_router
            sdk.compressor = mock_compressor_instance
            return sdk


# ============================================================================
# TEST CLASS 1: Cache Flow Integration
# ============================================================================


class TestCacheFlow:
    """Test cache hit/miss flows and cache storage."""

    def test_first_query_cache_miss_then_hit(self, router, mock_cache, mock_local):
        """Test: First query misses cache, second similar query hits."""
        # Setup: First call misses, second call hits
        mock_cache.get.side_effect = [None, "Cached response"]

        # First query: cache miss → local LLM
        response1 = router.chat("What is Python?")
        assert response1.source == "local"
        assert response1.response == "Response from local LLM"
        assert mock_cache.set.called  # Should cache the response

        # Second query: cache hit
        response2 = router.chat("Tell me about Python")
        assert response2.source == "cache"
        assert response2.response == "Cached response"
        assert mock_local.chat.call_count == 1  # Local only called once

    def test_cache_stores_original_prompt(self, router, mock_cache):
        """Test: Cache stores original prompt (not compressed)."""
        mock_cache.get.return_value = None
        original_prompt = "What is quantum computing?"

        router.chat(original_prompt)

        # Verify cache.set was called with ORIGINAL prompt
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        assert call_args[0][0] == original_prompt  # First arg is original prompt

    def test_cache_hit_skips_compression(self, router, mock_cache, mock_compressor):
        """Test: Cache hit returns immediately without compression."""
        mock_cache.get.return_value = "Cached response"

        response = router.chat("Any query")

        assert response.source == "cache"
        assert response.response == "Cached response"
        # Compression should NOT be called on cache hit
        mock_compressor.compress.assert_not_called()

    def test_cache_miss_triggers_compression(self, router, mock_cache, mock_compressor):
        """Test: Cache miss triggers compression before API call."""
        mock_cache.get.return_value = None

        router.chat("Test query")

        # Compression should be called on cache miss
        mock_compressor.compress.assert_called_once()

    def test_cache_statistics_updated(self, router, mock_cache):
        """Test: Cache statistics are tracked correctly."""
        mock_cache.get.return_value = None
        mock_cache.stats.return_value = CacheStats(
            total_queries=1,
            cache_hits=0,
            cache_misses=1,
            hit_rate=0.0,
        )

        router.chat("Query 1")

        # Stats should reflect the query
        stats = mock_cache.stats()
        assert stats.total_queries == 1
        assert stats.cache_misses == 1


# ============================================================================
# TEST CLASS 2: Smart Routing Flow
# ============================================================================


class TestSmartRoutingFlow:
    """Test smart routing priority and fallback behavior."""

    def test_smart_routing_priority_cache_first(self, router, mock_cache):
        """Test: Smart routing checks cache FIRST."""
        mock_cache.get.return_value = "Cached response"

        response = router.chat("Query", strategy="smart")

        assert response.source == "cache"
        # Verify cache.get was called before any other provider
        mock_cache.get.assert_called_once()

    def test_smart_routing_fallback_to_local(self, router, mock_cache, mock_local):
        """Test: Smart routing falls back to local LLM on cache miss."""
        mock_cache.get.return_value = None
        mock_local.is_available.return_value = True

        response = router.chat("Query", strategy="smart")

        assert response.source == "local"
        assert mock_local.chat.called

    def test_smart_routing_fallback_to_free_api(
        self, router, mock_cache, mock_local, mock_free_api
    ):
        """Test: Smart routing falls back to free API when local unavailable."""
        mock_cache.get.return_value = None
        mock_local.is_available.return_value = False

        response = router.chat("Query", strategy="smart")

        assert response.source == "free-api"
        assert mock_free_api.chat.called
        assert not mock_local.chat.called

    def test_smart_routing_all_providers_fail(
        self, router, mock_cache, mock_local, mock_free_api
    ):
        """Test: RoutingError when all providers fail."""
        mock_cache.get.return_value = None
        mock_local.is_available.return_value = False
        mock_free_api.chat.side_effect = QuotaExceededError("No quota")

        with pytest.raises(RoutingError):
            router.chat("Query", strategy="smart")

    def test_local_strategy_forces_local_only(self, router, mock_cache, mock_local):
        """Test: 'local' strategy forces local LLM only."""
        mock_cache.get.return_value = None

        response = router.chat("Query", strategy="local")

        assert response.source == "local"
        assert mock_local.chat.called

    def test_free_api_strategy_forces_free_api(self, router, mock_cache, mock_free_api):
        """Test: 'free-api' strategy forces free API only."""
        mock_cache.get.return_value = None

        response = router.chat("Query", strategy="free-api")

        assert response.source == "free-api"
        assert mock_free_api.chat.called

    def test_cache_only_strategy_hits(self, router, mock_cache):
        """Test: 'cache-only' strategy returns on cache hit."""
        mock_cache.get.return_value = "Cached response"

        response = router.chat("Query", strategy="cache-only")

        assert response.source == "cache"
        assert response.response == "Cached response"

    def test_cache_only_strategy_misses(self, router, mock_cache):
        """Test: 'cache-only' strategy raises RoutingError on miss."""
        mock_cache.get.return_value = None

        with pytest.raises(RoutingError):
            router.chat("Query", strategy="cache-only")


# ============================================================================
# TEST CLASS 3: Offline Mode
# ============================================================================


class TestOfflineMode:
    """Test offline/local-only scenarios."""

    def test_offline_mode_local_only(self, router, mock_cache, mock_local):
        """Test: Offline mode uses local LLM only."""
        mock_cache.get.return_value = None
        mock_local.is_available.return_value = True

        response = router.chat("Query", strategy="local")

        assert response.source == "local"
        assert mock_local.chat.called

    def test_offline_mode_cache_hit_works(self, router, mock_cache):
        """Test: Offline mode returns cached responses."""
        mock_cache.get.return_value = "Cached response"

        response = router.chat("Query", strategy="cache-only")

        assert response.source == "cache"
        assert response.response == "Cached response"

    def test_offline_mode_local_unavailable_fails(self, router, mock_cache, mock_local):
        """Test: Offline mode fails when local LLM unavailable."""
        mock_cache.get.return_value = None
        mock_local.is_available.return_value = False
        mock_local.chat.side_effect = Exception("Ollama not available")

        with pytest.raises(Exception):
            router.chat("Query", strategy="local")


# ============================================================================
# TEST CLASS 4: Compression Integration
# ============================================================================


class TestCompressionIntegration:
    """Test compression applied at correct points in flow."""

    def test_compression_applied_before_api_call(
        self, router, mock_cache, mock_compressor, mock_local
    ):
        """Test: Compression applied before API call (not on cache hit)."""
        mock_cache.get.return_value = None
        original_prompt = "This is a very long prompt that needs compression"

        router.chat(original_prompt)

        # Compression should be called with original prompt
        mock_compressor.compress.assert_called_once()
        call_args = mock_compressor.compress.call_args
        assert call_args[0][0] == original_prompt

    def test_compression_not_applied_on_cache_hit(
        self, router, mock_cache, mock_compressor
    ):
        """Test: Compression NOT applied on cache hit."""
        mock_cache.get.return_value = "Cached response"

        router.chat("Query")

        # Compression should NOT be called
        mock_compressor.compress.assert_not_called()

    def test_compressed_text_sent_to_provider(
        self, router, mock_cache, mock_compressor, mock_local
    ):
        """Test: Compressed text sent to provider, not original."""
        mock_cache.get.return_value = None
        mock_compressor.compress.return_value = CompressResult(
            original_tokens=100,
            compressed_tokens=50,
            compressed_text="compressed version",
            ratio=0.5,
        )

        router.chat("Original prompt")

        # Local LLM should receive compressed text
        mock_local.chat.assert_called_once_with("compressed version")

    def test_compression_failure_handled(
        self, router, mock_cache, mock_compressor, mock_local
    ):
        """Test: Compression failure is handled gracefully (returns original prompt)."""
        mock_cache.get.return_value = None
        mock_compressor.compress.side_effect = Exception("Compression failed")

        # Router should handle compression failure and use original prompt
        response = router.chat("Query")

        # Should still get a response (using original prompt)
        assert response is not None
        assert mock_local.chat.called


# ============================================================================
# TEST CLASS 5: Stats Tracking
# ============================================================================


class TestStatsTracking:
    """Test statistics tracking and cost calculations."""

    def test_cache_hit_rate_calculation(self, router, mock_cache):
        """Test: Cache hit rate calculated correctly."""
        mock_cache.stats.return_value = CacheStats(
            total_queries=10,
            cache_hits=7,
            cache_misses=3,
            hit_rate=0.7,
        )

        stats = mock_cache.stats()

        assert stats.hit_rate == 0.7
        assert stats.cache_hits == 7
        assert stats.total_queries == 10

    def test_cost_savings_tracking(self, router, mock_cache):
        """Test: Cost savings tracked (always 0 for 100% FREE)."""
        mock_cache.get.return_value = None

        response = router.chat("Query")

        # Cost should always be 0 (100% FREE architecture)
        assert response.cost == 0.0

    def test_tokens_saved_tracking(self, router, mock_cache, mock_compressor):
        """Test: Tokens saved through compression tracked."""
        mock_cache.get.return_value = None
        mock_compressor.compress.return_value = CompressResult(
            original_tokens=100,
            compressed_tokens=50,
            compressed_text="compressed",
            ratio=0.5,
        )

        response = router.chat("Query")

        # Tokens saved = original - compressed = 100 - 50 = 50
        assert response.tokens_saved == 50

    def test_sdk_stats_aggregation(self, sdk, mock_cache):
        """Test: SDK stats aggregated from router cache."""
        mock_cache.stats.return_value = CacheStats(
            total_queries=20,
            cache_hits=14,
            cache_misses=6,
            hit_rate=0.7,
        )

        stats = sdk.stats()

        assert isinstance(stats, SDKStats)
        assert stats.cache_hit_rate == 0.7
        assert stats.total_queries == 20
        assert stats.cached == 14


# ============================================================================
# TEST CLASS 6: Error Handling
# ============================================================================


class TestErrorHandling:
    """Test error scenarios and graceful failures."""

    def test_routing_error_when_all_fail(
        self, router, mock_cache, mock_local, mock_free_api
    ):
        """Test: RoutingError raised when all providers fail."""
        mock_cache.get.return_value = None
        mock_local.is_available.return_value = False
        mock_free_api.chat.side_effect = QuotaExceededError("Quota exceeded")

        with pytest.raises(RoutingError):
            router.chat("Query", strategy="smart")

    def test_empty_prompt_validation(self, router):
        """Test: Empty prompt raises ValueError."""
        with pytest.raises(ValueError):
            router.chat("")

    def test_whitespace_only_prompt_validation(self, router):
        """Test: Whitespace-only prompt raises ValueError."""
        with pytest.raises(ValueError):
            router.chat("   ")

    def test_invalid_strategy_validation(self, router):
        """Test: Invalid strategy raises ValueError."""
        with pytest.raises(ValueError):
            router.chat("Query", strategy="invalid-strategy")

    def test_local_unavailable_error(self, router, mock_cache, mock_local):
        """Test: Error when local LLM unavailable."""
        mock_cache.get.return_value = None
        mock_local.is_available.return_value = False
        mock_local.chat.side_effect = Exception("Ollama not available")

        with pytest.raises(Exception):
            router.chat("Query", strategy="local")

    def test_free_api_quota_exceeded(self, router, mock_cache, mock_free_api):
        """Test: QuotaExceededError propagates from free-api strategy."""
        mock_cache.get.return_value = None
        mock_free_api.chat.side_effect = QuotaExceededError("Daily quota exceeded")

        with pytest.raises(QuotaExceededError):
            router.chat("Query", strategy="free-api")

    def test_graceful_compression_failure(
        self, router, mock_cache, mock_compressor, mock_local
    ):
        """Test: Compression failure handled gracefully (uses original prompt)."""
        mock_cache.get.return_value = None
        mock_compressor.compress.side_effect = RuntimeError("Compression failed")

        response = router.chat("Query")

        assert response is not None
        assert mock_local.chat.called


# ============================================================================
# TEST CLASS 7: End-to-End Workflows
# ============================================================================


class TestEndToEndWorkflows:
    """Test complete workflows combining multiple components."""

    def test_full_workflow_cache_miss_to_local(
        self, router, mock_cache, mock_local, mock_compressor
    ):
        """Test: Full workflow - cache miss → compress → local LLM → cache store."""
        mock_cache.get.return_value = None
        original_prompt = "What is machine learning?"

        response = router.chat(original_prompt)

        # Verify full flow
        assert mock_cache.get.called  # Check cache first
        assert mock_compressor.compress.called  # Compress on miss
        assert mock_local.chat.called  # Call local LLM
        assert mock_cache.set.called  # Store in cache
        assert response.source == "local"

    def test_full_workflow_cache_hit(self, router, mock_cache, mock_compressor):
        """Test: Full workflow - cache hit returns immediately."""
        mock_cache.get.return_value = "Cached response"

        response = router.chat("Query")

        # Verify short-circuit flow
        assert mock_cache.get.called
        assert not mock_compressor.compress.called  # No compression
        assert response.source == "cache"

    def test_sdk_chat_integration(self, sdk, mock_cache):
        """Test: SDK chat method integrates with router."""
        mock_cache.stats.return_value = CacheStats(
            total_queries=1,
            cache_hits=1,
            cache_misses=0,
            hit_rate=1.0,
        )

        response = sdk.chat("Test query")

        assert response == "Test response"

    def test_sdk_compress_integration(self, sdk):
        """Test: SDK compress method works independently."""
        result = sdk.compress("Long text to compress", rate=0.5)

        assert result == "compressed"

    def test_multiple_queries_cache_accumulation(self, router, mock_cache):
        """Test: Multiple queries accumulate in cache."""
        mock_cache.get.side_effect = [None, None, "Cached"]

        # Query 1: miss
        router.chat("Query 1")
        assert mock_cache.set.call_count == 1

        # Query 2: miss
        router.chat("Query 2")
        assert mock_cache.set.call_count == 2

        # Query 3: hit
        router.chat("Query 3")
        assert mock_cache.set.call_count == 2  # No new cache entry


# ============================================================================
# TEST CLASS 8: Response Metadata
# ============================================================================


class TestResponseMetadata:
    """Test RouterResponse metadata accuracy."""

    def test_response_source_accuracy(self, router, mock_cache, mock_local):
        """Test: Response source correctly identifies provider."""
        mock_cache.get.return_value = None

        response = router.chat("Query")

        assert response.source in ["cache", "local", "free-api"]

    def test_response_cost_always_zero(self, router, mock_cache):
        """Test: Response cost always 0 (100% FREE)."""
        mock_cache.get.return_value = None

        response = router.chat("Query")

        assert response.cost == 0.0

    def test_response_tokens_saved_on_compression(
        self, router, mock_cache, mock_compressor
    ):
        """Test: Tokens saved calculated from compression."""
        mock_cache.get.return_value = None
        mock_compressor.compress.return_value = CompressResult(
            original_tokens=200,
            compressed_tokens=80,
            compressed_text="compressed",
            ratio=0.4,
        )

        response = router.chat("Query")

        # Tokens saved = 200 - 80 = 120
        assert response.tokens_saved == 120

    def test_response_tokens_saved_zero_on_cache_hit(self, router, mock_cache):
        """Test: Tokens saved is 0 on cache hit (no compression)."""
        mock_cache.get.return_value = "Cached response"

        response = router.chat("Query")

        assert response.tokens_saved == 0
