"""Configuration management for API keys and settings."""

import os
from pathlib import Path
from typing import Optional, Dict, List, Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib


class ConfigManager:
    """Manage API keys and configuration settings."""

    ENV_KEY_MAP = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
    }

    # Default configuration values
    DEFAULTS = {
        "cache": {
            "enabled": True,
            "threshold": 0.85,
            "max_size": 10000,
            "ttl": 86400,  # 24 hours
        },
        "local": {
            "enabled": True,
            "model": "deepseek-r1:8b",
            "fallback": True,
        },
        "free_api": {
            "gemini_key": "",
            "groq_key": "",
            "priority": ["deepseek", "groq", "gemini"],
        },
        "routing": {
            "strategy": "smart",
            "compress": True,
        },
    }

    # Environment variable mappings for new settings
    ENV_CONFIG_MAP = {
        "cache.enabled": "TOKENCRUSH_CACHE_ENABLED",
        "cache.threshold": "TOKENCRUSH_CACHE_THRESHOLD",
        "cache.max_size": "TOKENCRUSH_CACHE_MAX_SIZE",
        "cache.ttl": "TOKENCRUSH_CACHE_TTL",
        "local.enabled": "TOKENCRUSH_LOCAL_ENABLED",
        "local.model": "TOKENCRUSH_LOCAL_MODEL",
        "local.fallback": "TOKENCRUSH_LOCAL_FALLBACK",
        "free_api.gemini_key": "TOKENCRUSH_GEMINI_KEY",
        "free_api.groq_key": "TOKENCRUSH_GROQ_KEY",
        "free_api.priority": "TOKENCRUSH_FREE_API_PRIORITY",
        "routing.strategy": "TOKENCRUSH_ROUTING_STRATEGY",
        "routing.compress": "TOKENCRUSH_ROUTING_COMPRESS",
    }

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the config manager.

        Args:
            config_dir: Directory for config files. Defaults to ~/.config/tokencrush.
        """
        self.config_dir = config_dir or (Path.home() / ".config" / "tokencrush")
        self.config_file = self.config_dir / "config.toml"

    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a provider. Environment variables take priority.

        Args:
            provider: Provider name (openai, anthropic, google).

        Returns:
            API key string or None if not found.
        """
        # Check environment variable first
        env_var = self.ENV_KEY_MAP.get(provider.lower())
        if env_var:
            key = os.environ.get(env_var)
            if key:
                return key

        # Fall back to config file
        return self._get_key_from_file(provider)

    def _get_key_from_file(self, provider: str) -> Optional[str]:
        """Read API key from config file."""
        if not self.config_file.exists():
            return None

        with open(self.config_file, "rb") as f:
            config = tomllib.load(f)

        return config.get("api_keys", {}).get(provider.lower())

    def set_api_key(self, provider: str, key: str) -> None:
        """
        Save API key to config file.

        Args:
            provider: Provider name.
            key: API key to save.
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load existing config
        config: Dict = {}
        if self.config_file.exists():
            with open(self.config_file, "rb") as f:
                config = tomllib.load(f)

        # Update api_keys section
        if "api_keys" not in config:
            config["api_keys"] = {}
        config["api_keys"][provider.lower()] = key

        # Write back - use simple format for now
        with open(self.config_file, "w") as f:
            f.write("[api_keys]\n")
            for p, k in config["api_keys"].items():
                f.write(f'{p} = "{k}"\n')

    def get_config(self, section: str, key: Optional[str] = None) -> Any:
        """
        Get configuration value with environment variable override support.

        Args:
            section: Config section (cache, local, free_api, routing).
            key: Optional key within section. If None, returns entire section.

        Returns:
            Configuration value or None if not found.

        Raises:
            ValueError: If configuration value is invalid.
        """
        # Build the full key path for env var lookup
        if key:
            config_path = f"{section}.{key}"
            env_var = self.ENV_CONFIG_MAP.get(config_path)

            # Check environment variable first
            if env_var:
                env_value = os.environ.get(env_var)
                if env_value is not None:
                    return self._parse_config_value(config_path, env_value)

            # Fall back to config file
            file_value = self._get_from_file(section, key)
            if file_value is not None:
                return file_value

            # Fall back to defaults
            return self.DEFAULTS.get(section, {}).get(key)
        else:
            # Return entire section
            file_config = self._get_from_file(section)
            if file_config:
                return file_config
            return self.DEFAULTS.get(section, {})

    def _get_from_file(self, section: str, key: Optional[str] = None) -> Any:
        """Read configuration from file."""
        if not self.config_file.exists():
            return None

        with open(self.config_file, "rb") as f:
            config = tomllib.load(f)

        if key:
            return config.get(section, {}).get(key)
        else:
            return config.get(section)

    def _parse_config_value(self, config_path: str, value: str) -> Any:
        """
        Parse configuration value from environment variable.

        Args:
            config_path: Path like "cache.enabled" or "cache.threshold".
            value: String value from environment variable.

        Returns:
            Parsed value with appropriate type.

        Raises:
            ValueError: If value cannot be parsed or is invalid.
        """
        section, key = config_path.split(".")

        # Type conversions based on key
        if key in ("enabled", "fallback", "compress"):
            # Boolean values
            if value.lower() in ("true", "1", "yes"):
                return True
            elif value.lower() in ("false", "0", "no"):
                return False
            else:
                raise ValueError(f"Invalid boolean value for {config_path}: {value}")

        elif key in ("threshold",):
            # Float values (0-1 range)
            try:
                float_val = float(value)
                if not 0 <= float_val <= 1:
                    raise ValueError(
                        f"Threshold must be between 0 and 1, got {float_val}"
                    )
                return float_val
            except ValueError as e:
                raise ValueError(
                    f"Invalid float value for {config_path}: {value}"
                ) from e

        elif key in ("max_size", "ttl"):
            # Integer values (must be positive)
            try:
                int_val = int(value)
                if int_val <= 0:
                    raise ValueError(f"{key} must be positive, got {int_val}")
                return int_val
            except ValueError as e:
                raise ValueError(
                    f"Invalid integer value for {config_path}: {value}"
                ) from e

        elif key == "priority":
            # List values (comma-separated)
            return [item.strip() for item in value.split(",")]

        else:
            # String values
            return value

    def validate_config(self) -> List[str]:
        """
        Validate all configuration values.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        # Validate cache section - check each key individually to trigger env var parsing
        for key in ["enabled", "threshold", "max_size", "ttl"]:
            try:
                value = self.get_config("cache", key)
                if key == "enabled" and value not in (True, False):
                    errors.append("cache.enabled must be boolean")
                elif key == "threshold":
                    if not isinstance(value, (int, float)):
                        errors.append("cache.threshold must be numeric")
                    elif not 0 <= value <= 1:
                        errors.append("cache.threshold must be between 0 and 1")
                elif key == "max_size":
                    if not isinstance(value, int) or value <= 0:
                        errors.append("cache.max_size must be positive integer")
                elif key == "ttl":
                    if not isinstance(value, int) or value <= 0:
                        errors.append("cache.ttl must be positive integer")
            except ValueError as e:
                errors.append(f"cache.{key}: {str(e)}")

        # Validate local section
        for key in ["enabled", "model", "fallback"]:
            try:
                value = self.get_config("local", key)
                if key == "enabled" and value not in (True, False):
                    errors.append("local.enabled must be boolean")
                elif key == "model":
                    if not isinstance(value, str) or not value:
                        errors.append("local.model must be non-empty string")
                elif key == "fallback" and value not in (True, False):
                    errors.append("local.fallback must be boolean")
            except ValueError as e:
                errors.append(f"local.{key}: {str(e)}")

        # Validate free_api section
        for key in ["gemini_key", "groq_key", "priority"]:
            try:
                value = self.get_config("free_api", key)
                if key in ("gemini_key", "groq_key"):
                    if not isinstance(value, str):
                        errors.append(f"free_api.{key} must be string")
                elif key == "priority":
                    if not isinstance(value, list) or not all(
                        isinstance(p, str) for p in value
                    ):
                        errors.append("free_api.priority must be list of strings")
            except ValueError as e:
                errors.append(f"free_api.{key}: {str(e)}")

        # Validate routing section
        for key in ["strategy", "compress"]:
            try:
                value = self.get_config("routing", key)
                if key == "strategy":
                    valid_strategies = ["smart", "local", "free-api", "cache-only"]
                    if value not in valid_strategies:
                        errors.append(
                            f"routing.strategy must be one of {valid_strategies}"
                        )
                elif key == "compress" and value not in (True, False):
                    errors.append("routing.compress must be boolean")
            except ValueError as e:
                errors.append(f"routing.{key}: {str(e)}")

        return errors

    @staticmethod
    def mask_key(key: str) -> str:
        """
        Mask API key for safe display.

        Args:
            key: Full API key.

        Returns:
            Masked key like "sk-1234...cdef".
        """
        if not key or len(key) < 8:
            return "***"
        return f"{key[:7]}...{key[-4:]}"

    def list_providers(self) -> List[str]:
        """
        List all providers with configured API keys.

        Returns:
            List of provider names.
        """
        providers = []
        for provider in self.ENV_KEY_MAP:
            if self.get_api_key(provider):
                providers.append(provider)
        return providers


class Config:
    """Application configuration."""

    def __init__(self):
        """Initialize configuration."""
        self.settings = {}
