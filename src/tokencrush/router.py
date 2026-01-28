"""Smart routing system integrating cache, local LLM, and free APIs.

Routes prompts through the most cost-effective path:
Priority: Cache → Local LLM (Ollama) → Free API → (Paid API requires explicit consent)
"""

from dataclasses import dataclass
from typing import Optional, Literal

from tokencrush.cache import SemanticCache
from tokencrush.local import OllamaProvider, OllamaError
from tokencrush.free_api import FreeAPIManager, QuotaExceededError
from tokencrush.compressor import TokenCompressor, CompressResult


RoutingStrategy = Literal["smart", "local", "free-api", "cache-only"]


class RoutingError(Exception):
    """Raised when routing fails across all available providers."""

    pass


@dataclass
class RouterResponse:
    """Response from the smart router.

    Attributes:
        response: The generated text response
        source: Where the response came from ("cache", "local", "free-api")
        cost: Estimated cost in USD (always 0 for free sources)
        tokens_saved: Number of tokens saved through compression
    """

    response: str
    source: str  # "cache", "local", "free-api"
    cost: float  # Estimated cost ($) - always 0 for 100% FREE architecture
    tokens_saved: int  # Compression savings


class SmartRouter:
    """Smart router that integrates caching, compression, and LLM providers.

    Provides intelligent routing to minimize costs while maximizing response quality.
    All integrated providers are 100% FREE:
    - SemanticCache: Local cache with vector similarity
    - OllamaProvider: Local LLM via Ollama
    - FreeAPIManager: Free-tier cloud APIs (Gemini, Groq, DeepSeek)

    Usage:
        router = SmartRouter()
        response = router.chat("Explain quantum computing")
        print(f"Response: {response.response}")
        print(f"Source: {response.source}")
        print(f"Tokens saved: {response.tokens_saved}")
    """

    def __init__(
        self,
        cache: Optional[SemanticCache] = None,
        local: Optional[OllamaProvider] = None,
        free_api: Optional[FreeAPIManager] = None,
        compressor: Optional[TokenCompressor] = None,
        compression_rate: float = 0.5,
    ):
        """Initialize the smart router.

        Args:
            cache: SemanticCache instance (creates new if not provided)
            local: OllamaProvider instance (creates new if not provided)
            free_api: FreeAPIManager instance (creates new if not provided)
            compressor: TokenCompressor instance (creates new if not provided)
            compression_rate: Target compression ratio (0.0-1.0). Default 0.5
        """
        self.cache = cache if cache is not None else SemanticCache()
        self.local = local if local is not None else OllamaProvider()
        self.free_api = free_api if free_api is not None else FreeAPIManager()
        self.compressor = compressor if compressor is not None else TokenCompressor()
        self.compression_rate = compression_rate

    def chat(
        self,
        prompt: str,
        strategy: RoutingStrategy = "smart",
    ) -> RouterResponse:
        """Send a chat request through the smart routing system.

        Args:
            prompt: The prompt text to send
            strategy: Routing strategy to use:
                - "smart" (default): Cache → Local → Free API (automatic fallback)
                - "local": Force local LLM only (Ollama)
                - "free-api": Force free API only (skip local)
                - "cache-only": Return from cache only (error on miss)

        Returns:
            RouterResponse with response text and metadata

        Raises:
            RoutingError: If no provider can handle the request
            ValueError: If strategy is invalid
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        # Validate strategy
        valid_strategies = {"smart", "local", "free-api", "cache-only"}
        if strategy not in valid_strategies:
            raise ValueError(
                f"Invalid strategy: {strategy}. "
                f"Valid options: {', '.join(sorted(valid_strategies))}"
            )

        # 1. Check cache FIRST (highest priority, no compression needed)
        cached_response = self.cache.get(prompt)
        if cached_response is not None:
            return RouterResponse(
                response=cached_response,
                source="cache",
                cost=0.0,
                tokens_saved=0,  # No compression for cache hits
            )

        # For cache-only strategy, error on miss
        if strategy == "cache-only":
            raise RoutingError("Cache miss. No cached response found for this query.")

        # 2. Compress prompt (only on cache miss)
        compress_result = self._compress_prompt(prompt)
        compressed_prompt = compress_result.compressed_text
        tokens_saved = (
            compress_result.original_tokens - compress_result.compressed_tokens
        )

        # 3. Route based on strategy
        if strategy == "local":
            response = self._route_local(compressed_prompt)
        elif strategy == "free-api":
            response = self._route_free_api(compressed_prompt)
        elif strategy == "smart":
            response = self._smart_route(compressed_prompt)
        else:
            # Should never reach here due to validation above
            raise ValueError(f"Unknown strategy: {strategy}")

        # 4. Cache the response (use ORIGINAL prompt for future semantic matches)
        self.cache.set(prompt, response.response)

        # 5. Return response with compression metadata
        return RouterResponse(
            response=response.response,
            source=response.source,
            cost=response.cost,
            tokens_saved=tokens_saved,
        )

    def _compress_prompt(self, prompt: str) -> CompressResult:
        """Compress a prompt using the token compressor.

        Args:
            prompt: Original prompt text

        Returns:
            CompressResult with compression details
        """
        try:
            return self.compressor.compress(prompt, rate=self.compression_rate)
        except Exception:
            # If compression fails, return original prompt with no savings
            return CompressResult(
                original_tokens=len(prompt.split()),  # Rough estimate
                compressed_tokens=len(prompt.split()),
                compressed_text=prompt,
                ratio=1.0,
            )

    def _smart_route(self, prompt: str) -> RouterResponse:
        """Intelligently route prompt to the best available provider.

        Priority order:
        1. Local LLM (Ollama) - completely free, no API calls
        2. Free API (Gemini/Groq/DeepSeek) - free tier limits

        Does NOT automatically fall back to paid APIs without user consent.

        Args:
            prompt: Compressed prompt text

        Returns:
            RouterResponse from the selected provider

        Raises:
            RoutingError: If no provider is available
        """
        errors = []

        # Try local LLM first
        try:
            if self.local.is_available():
                return self._route_local(prompt)
        except OllamaError as e:
            errors.append(f"Local LLM: {e}")

        # Try free APIs
        try:
            return self._route_free_api(prompt)
        except (QuotaExceededError, Exception) as e:
            errors.append(f"Free API: {e}")

        # All providers failed
        raise RoutingError(f"All providers failed. Errors: {'; '.join(errors)}")

    def _route_local(self, prompt: str) -> RouterResponse:
        """Route prompt to local Ollama LLM.

        Args:
            prompt: Prompt text to send

        Returns:
            RouterResponse from Ollama

        Raises:
            OllamaError: If Ollama is not available or fails
        """
        response_text = self.local.chat(prompt)
        return RouterResponse(
            response=response_text,
            source="local",
            cost=0.0,  # Local is always free
            tokens_saved=0,  # Will be overwritten in chat()
        )

    def _route_free_api(self, prompt: str) -> RouterResponse:
        """Route prompt to free API providers.

        Args:
            prompt: Prompt text to send

        Returns:
            RouterResponse from free API

        Raises:
            QuotaExceededError: If all free APIs have exceeded quotas
        """
        response_text = self.free_api.chat(prompt, provider="auto")
        return RouterResponse(
            response=response_text,
            source="free-api",
            cost=0.0,  # Free tier is always free
            tokens_saved=0,  # Will be overwritten in chat()
        )

    def is_local_available(self) -> bool:
        """Check if local LLM (Ollama) is available.

        Returns:
            True if Ollama is running and accessible
        """
        return self.local.is_available()

    def is_free_api_available(self) -> bool:
        """Check if any free API provider is available.

        Returns:
            True if at least one free API has quota remaining
        """
        return self.free_api.get_available_provider() is not None

    def get_provider_status(self) -> dict:
        """Get status of all available providers.

        Returns:
            Dictionary with provider availability and status
        """
        return {
            "cache": {
                "available": True,  # Cache is always available
                "stats": {
                    "total_queries": self.cache._total_queries,
                    "cache_hits": self.cache._cache_hits,
                    "hit_rate": self.cache.stats().hit_rate,
                },
            },
            "local": {
                "available": self.is_local_available(),
                "provider": "ollama",
                "model": self.local.model,
            },
            "free_api": {
                "available": self.is_free_api_available(),
                "usage": self.free_api.get_usage(),
            },
        }
