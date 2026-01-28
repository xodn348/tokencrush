"""Free API manager for rotating between free-tier LLM providers.

Supports Gemini (15 RPM, 1000 RPD), Groq (30 RPM), and DeepSeek (unlimited free models).
Tracks usage quotas and auto-rotates when limits are hit.
"""

import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, List
from litellm import completion

from tokencrush.config import ConfigManager


@dataclass
class UsageStats:
    """Usage statistics for a provider."""

    requests_today: int
    requests_this_minute: int
    last_request_time: float
    daily_reset_time: float
    minute_window_start: float


class QuotaExceededError(Exception):
    """Raised when all providers have exceeded their quotas."""

    pass


class FreeAPIManager:
    """Manages free-tier API providers with automatic rotation and quota tracking."""

    # Provider configurations with rate limits
    PROVIDERS = {
        "gemini": {
            "limit_rpm": 15,  # requests per minute
            "limit_rpd": 1000,  # requests per day
            "model": "gemini/gemini-1.5-flash",
            "api_key_env": "GOOGLE_API_KEY",
        },
        "groq": {
            "limit_rpm": 30,
            "limit_rpd": None,  # No daily limit
            "model": "groq/llama-3.1-70b-versatile",
            "api_key_env": "GROQ_API_KEY",
        },
        "deepseek": {
            "limit_rpm": None,  # No rate limit on free models
            "limit_rpd": None,
            "model": "deepseek/deepseek-chat",
            "api_key_env": "DEEPSEEK_API_KEY",
        },
    }

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the free API manager.

        Args:
            cache_dir: Directory for storing usage data. Defaults to ~/.cache/tokencrush.
        """
        self.config = ConfigManager()
        self.cache_dir = cache_dir or (Path.home() / ".cache" / "tokencrush")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.quota_file = self.cache_dir / "quotas.json"
        self.usage = self._load_usage()

    def _load_usage(self) -> Dict[str, UsageStats]:
        """Load usage statistics from cache file."""
        if not self.quota_file.exists():
            return self._init_usage()

        try:
            with open(self.quota_file, "r") as f:
                data = json.load(f)

            # Convert dict back to UsageStats objects
            usage = {}
            for provider, stats in data.items():
                usage[provider] = UsageStats(**stats)

            return usage
        except (json.JSONDecodeError, TypeError):
            # If file is corrupted, reinitialize
            return self._init_usage()

    def _init_usage(self) -> Dict[str, UsageStats]:
        """Initialize usage statistics for all providers."""
        now = time.time()
        midnight_today = (
            datetime.now(timezone.utc)
            .replace(hour=0, minute=0, second=0, microsecond=0)
            .timestamp()
        )

        return {
            provider: UsageStats(
                requests_today=0,
                requests_this_minute=0,
                last_request_time=0,
                daily_reset_time=midnight_today,
                minute_window_start=now,
            )
            for provider in self.PROVIDERS
        }

    def _save_usage(self) -> None:
        """Save usage statistics to cache file."""
        data = {provider: asdict(stats) for provider, stats in self.usage.items()}

        with open(self.quota_file, "w") as f:
            json.dump(data, f, indent=2)

    def _reset_if_needed(self, provider: str) -> None:
        """Reset counters if time windows have passed."""
        now = time.time()
        stats = self.usage[provider]

        # Reset daily counter if it's a new day (midnight UTC)
        midnight_today = (
            datetime.now(timezone.utc)
            .replace(hour=0, minute=0, second=0, microsecond=0)
            .timestamp()
        )

        if midnight_today > stats.daily_reset_time:
            stats.requests_today = 0
            stats.daily_reset_time = midnight_today

        # Reset minute counter if 60 seconds have passed
        if now - stats.minute_window_start >= 60:
            stats.requests_this_minute = 0
            stats.minute_window_start = now

    def _check_quota(self, provider: str) -> bool:
        """
        Check if provider has available quota.

        Args:
            provider: Provider name to check.

        Returns:
            True if quota is available, False otherwise.
        """
        config = self.PROVIDERS[provider]
        stats = self.usage[provider]

        self._reset_if_needed(provider)

        # Check daily limit
        if config["limit_rpd"] is not None:
            if stats.requests_today >= config["limit_rpd"]:
                return False

        # Check per-minute limit
        if config["limit_rpm"] is not None:
            if stats.requests_this_minute >= config["limit_rpm"]:
                return False

        return True

    def _has_api_key(self, provider: str) -> bool:
        """Check if API key is configured for provider."""
        config = self.PROVIDERS[provider]
        env_var = config["api_key_env"]

        # Check if key exists in config or environment
        key = self.config.get_api_key(provider)
        if key:
            return True

        # For backward compatibility, also check the exact env var name
        import os

        return bool(os.environ.get(env_var))

    def get_available_provider(self) -> Optional[str]:
        """
        Get the first available provider with quota remaining.

        Returns:
            Provider name or None if all providers are exhausted.
        """
        # Priority order: deepseek (unlimited) -> groq (30 RPM) -> gemini (15 RPM, 1000 RPD)
        priority_order = ["deepseek", "groq", "gemini"]

        for provider in priority_order:
            if self._has_api_key(provider) and self._check_quota(provider):
                return provider

        return None

    def _increment_usage(self, provider: str) -> None:
        """Increment usage counters for a provider."""
        stats = self.usage[provider]
        stats.requests_today += 1
        stats.requests_this_minute += 1
        stats.last_request_time = time.time()
        self._save_usage()

    def chat(self, prompt: str, provider: str = "auto", **kwargs) -> str:
        """
        Send a chat completion request with automatic provider rotation.

        Args:
            prompt: The prompt to send.
            provider: Provider to use ("auto" for automatic selection, or specific provider name).
            **kwargs: Additional arguments to pass to litellm.completion().

        Returns:
            Response text from the LLM.

        Raises:
            QuotaExceededError: If all providers have exceeded their quotas.
            ValueError: If specified provider is invalid or has no API key.
        """
        # Determine which provider to use
        if provider == "auto":
            selected_provider = self.get_available_provider()
            if selected_provider is None:
                raise QuotaExceededError(
                    "All providers have exceeded their quotas. "
                    "Please wait for quota reset or configure additional API keys."
                )
        else:
            if provider not in self.PROVIDERS:
                raise ValueError(f"Unknown provider: {provider}")

            if not self._has_api_key(provider):
                raise ValueError(f"No API key configured for provider: {provider}")

            if not self._check_quota(provider):
                raise QuotaExceededError(
                    f"Provider {provider} has exceeded its quota. "
                    f"Try 'auto' mode to use alternative providers."
                )

            selected_provider = provider

        # Get model name for the provider
        config = self.PROVIDERS[selected_provider]
        model = config["model"]

        # Make the API call
        try:
            response = completion(
                model=model, messages=[{"role": "user", "content": prompt}], **kwargs
            )

            # Increment usage counter
            self._increment_usage(selected_provider)

            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"API call to {selected_provider} failed: {e}") from e

    def get_usage(self) -> Dict[str, Dict]:
        """
        Get current usage statistics for all providers.

        Returns:
            Dictionary mapping provider names to their usage stats.
        """
        result = {}

        for provider, stats in self.usage.items():
            self._reset_if_needed(provider)

            config = self.PROVIDERS[provider]
            has_key = self._has_api_key(provider)

            result[provider] = {
                "has_api_key": has_key,
                "requests_today": stats.requests_today,
                "requests_this_minute": stats.requests_this_minute,
                "daily_limit": config["limit_rpd"],
                "minute_limit": config["limit_rpm"],
                "quota_available": self._check_quota(provider) if has_key else False,
                "model": config["model"],
            }

        return result

    def list_providers(self) -> List[str]:
        """
        List all supported provider names.

        Returns:
            List of provider names.
        """
        return list(self.PROVIDERS.keys())
