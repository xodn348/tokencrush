"""Python SDK for TokenCrush - programmatic access to smart routing and compression."""

from dataclasses import dataclass
from typing import Literal, Optional

from tokencrush.router import SmartRouter, RouterResponse, RoutingStrategy
from tokencrush.compressor import TokenCompressor, CompressResult
from tokencrush.cache import SemanticCache, CacheStats


@dataclass
class SDKStats:
    """Statistics about TokenCrush usage and cache performance.

    Attributes:
        cache_hit_rate: Percentage of queries served from cache (0.0-1.0)
        total_queries: Total number of queries processed
        cached: Number of cache hits
        cost_saved: Estimated cost savings (always 0 for 100% FREE architecture)
    """

    cache_hit_rate: float
    total_queries: int
    cached: int
    cost_saved: float


class TokenCrush:
    """Python SDK for TokenCrush - intelligent LLM routing and compression.

    Provides a clean, synchronous interface for:
    - Smart routing through cache → local LLM → free APIs
    - Token compression for prompt optimization
    - Cache statistics and performance tracking

    All providers are 100% FREE:
    - SemanticCache: Local vector similarity search
    - OllamaProvider: Local LLM (if available)
    - FreeAPIManager: Free-tier cloud APIs (Gemini, Groq, DeepSeek)

    Usage:
        from tokencrush import TokenCrush

        tc = TokenCrush()

        # Smart routing (auto-selects best provider)
        response = tc.chat("What is quantum computing?")

        # Force specific provider
        response = tc.chat("Hello", mode="local")

        # Standalone compression
        compressed = tc.compress("Long text to compress...")

        # Get statistics
        stats = tc.stats()
        print(f"Cache hit rate: {stats.cache_hit_rate:.1%}")
    """

    def __init__(
        self,
        cache: Optional[SemanticCache] = None,
        compression_rate: float = 0.5,
    ):
        """Initialize the TokenCrush SDK.

        Args:
            cache: Optional SemanticCache instance. Creates new if not provided.
            compression_rate: Target compression ratio (0.0-1.0). Default 0.5
        """
        self.router = SmartRouter(
            cache=cache,
            compression_rate=compression_rate,
        )
        self.compressor = TokenCompressor()

    def chat(
        self,
        prompt: str,
        mode: Literal["smart", "local", "free", "cache-only"] = "smart",
    ) -> str:
        """Send a chat request through the smart routing system.

        Routes the prompt through the most cost-effective provider based on mode:
        - "smart" (default): Cache → Local LLM → Free API (automatic fallback)
        - "local": Force local LLM only (Ollama)
        - "free": Force free API only (skip local)
        - "cache-only": Return from cache only (error on miss)

        Args:
            prompt: The user query or prompt text
            mode: Routing strategy to use. Default "smart"

        Returns:
            LLM response text

        Raises:
            ValueError: If prompt is empty or mode is invalid
            RoutingError: If no provider can handle the request

        Examples:
            >>> tc = TokenCrush()
            >>> response = tc.chat("Explain machine learning")
            >>> response = tc.chat("Hello", mode="local")  # Force local
            >>> response = tc.chat("Cached query", mode="cache-only")  # Cache only
        """
        # Map SDK mode names to router strategy names
        strategy_map = {
            "smart": "smart",
            "local": "local",
            "free": "free-api",
            "cache-only": "cache-only",
        }

        if mode not in strategy_map:
            raise ValueError(
                f"Invalid mode: {mode}. "
                f"Valid options: {', '.join(sorted(strategy_map.keys()))}"
            )

        strategy = strategy_map[mode]
        response = self.router.chat(prompt, strategy=strategy)
        return response.response

    def compress(self, text: str, rate: float = 0.5) -> str:
        """Compress text without making an LLM call.

        Standalone compression using LLMLingua-2 for token optimization.
        Useful for reducing prompt size before sending to any LLM.

        Args:
            text: Text to compress
            rate: Compression ratio (0.0-1.0). Default 0.5
                - 0.5 = compress to 50% of original tokens
                - 0.3 = compress to 30% of original tokens

        Returns:
            Compressed text

        Raises:
            ValueError: If text is empty or rate is invalid

        Examples:
            >>> tc = TokenCrush()
            >>> long_text = "..." * 1000
            >>> compressed = tc.compress(long_text, rate=0.3)
            >>> print(len(compressed) < len(long_text))
            True
        """
        if not text:
            return ""

        if not (0.0 <= rate <= 1.0):
            raise ValueError(
                f"Compression rate must be between 0.0 and 1.0, got {rate}"
            )

        result = self.compressor.compress(text, rate=rate)
        return result.compressed_text

    def stats(self) -> SDKStats:
        """Get cache statistics and performance metrics.

        Returns cache hit rate, total queries, and cost savings information.

        Returns:
            SDKStats with cache performance metrics

        Examples:
            >>> tc = TokenCrush()
            >>> stats = tc.stats()
            >>> print(f"Hit rate: {stats.cache_hit_rate:.1%}")
            >>> print(f"Queries: {stats.total_queries}")
            >>> print(f"Cached: {stats.cached}")
        """
        cache_stats = self.router.cache.stats()

        return SDKStats(
            cache_hit_rate=cache_stats.hit_rate,
            total_queries=cache_stats.total_queries,
            cached=cache_stats.cache_hits,
            cost_saved=0.0,  # 100% FREE architecture - no costs
        )
