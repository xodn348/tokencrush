"""Tests for the ConfigManager module."""

import pytest
import os
from pathlib import Path


class TestConfigManager:
    """Tests for ConfigManager class."""

    def test_get_api_key_from_env(self, mock_env_keys):
        """Test reading API key from environment variable."""
        from tokencrush.config import ConfigManager

        config = ConfigManager()
        key = config.get_api_key("openai")

        assert key == "sk-test-openai-key"

    def test_get_api_key_env_priority(self, temp_config_dir, mock_env_keys):
        """Test that environment variables take priority over config file."""
        from tokencrush.config import ConfigManager

        # Write different key to config file
        config_file = temp_config_dir / "config.toml"
        config_file.write_text('[api_keys]\nopenai = "file-key"')

        config = ConfigManager(config_dir=temp_config_dir)
        key = config.get_api_key("openai")

        # Env should take priority
        assert key == "sk-test-openai-key"

    def test_set_api_key(self, temp_config_dir):
        """Test saving API key to config file."""
        from tokencrush.config import ConfigManager

        config = ConfigManager(config_dir=temp_config_dir)
        config.set_api_key("openai", "sk-new-key")

        # Read back
        config2 = ConfigManager(config_dir=temp_config_dir)
        # Clear env to test file reading
        key = config2._get_key_from_file("openai")
        assert key == "sk-new-key"

    def test_mask_api_key(self):
        """Test API key masking for display."""
        from tokencrush.config import ConfigManager

        masked = ConfigManager.mask_key("sk-1234567890abcdef")

        assert masked.startswith("sk-")
        assert "..." in masked
        assert len(masked) < len("sk-1234567890abcdef")

    def test_get_api_key_not_found(self, temp_config_dir, monkeypatch):
        """Test behavior when API key is not found."""
        from tokencrush.config import ConfigManager

        # Clear env vars
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        config = ConfigManager(config_dir=temp_config_dir)
        key = config.get_api_key("openai")

        assert key is None

    def test_list_configured_providers(self, mock_env_keys, temp_config_dir):
        """Test listing all configured providers."""
        from tokencrush.config import ConfigManager

        config = ConfigManager(config_dir=temp_config_dir)
        providers = config.list_providers()

        assert "openai" in providers
        assert "anthropic" in providers
        assert "google" in providers

    def test_default_config_dir(self):
        """Test default config directory is ~/.config/tokencrush."""
        from tokencrush.config import ConfigManager

        config = ConfigManager()
        expected = Path.home() / ".config" / "tokencrush"

        assert config.config_dir == expected


class TestConfigSections:
    """Tests for new configuration sections."""

    def test_get_cache_config_defaults(self, temp_config_dir):
        """Test getting cache config with defaults."""
        from tokencrush.config import ConfigManager

        config = ConfigManager(config_dir=temp_config_dir)
        cache = config.get_config("cache")

        assert cache["enabled"] is True
        assert cache["threshold"] == 0.85
        assert cache["max_size"] == 10000
        assert cache["ttl"] == 86400

    def test_get_cache_config_from_file(self, temp_config_dir):
        """Test reading cache config from file."""
        from tokencrush.config import ConfigManager

        config_file = temp_config_dir / "config.toml"
        config_file.write_text("""
[cache]
enabled = false
threshold = 0.75
max_size = 5000
ttl = 3600
""")

        config = ConfigManager(config_dir=temp_config_dir)
        cache = config.get_config("cache")

        assert cache["enabled"] is False
        assert cache["threshold"] == 0.75
        assert cache["max_size"] == 5000
        assert cache["ttl"] == 3600

    def test_get_cache_config_env_override(self, temp_config_dir, monkeypatch):
        """Test environment variable override for cache config."""
        from tokencrush.config import ConfigManager

        monkeypatch.setenv("TOKENCRUSH_CACHE_ENABLED", "false")
        monkeypatch.setenv("TOKENCRUSH_CACHE_THRESHOLD", "0.5")

        config = ConfigManager(config_dir=temp_config_dir)

        assert config.get_config("cache", "enabled") is False
        assert config.get_config("cache", "threshold") == 0.5

    def test_get_local_config_defaults(self, temp_config_dir):
        """Test getting local config with defaults."""
        from tokencrush.config import ConfigManager

        config = ConfigManager(config_dir=temp_config_dir)
        local = config.get_config("local")

        assert local["enabled"] is True
        assert local["model"] == "deepseek-r1:8b"
        assert local["fallback"] is True

    def test_get_local_config_from_file(self, temp_config_dir):
        """Test reading local config from file."""
        from tokencrush.config import ConfigManager

        config_file = temp_config_dir / "config.toml"
        config_file.write_text("""
[local]
enabled = true
model = "llama3:70b"
fallback = false
""")

        config = ConfigManager(config_dir=temp_config_dir)
        local = config.get_config("local")

        assert local["enabled"] is True
        assert local["model"] == "llama3:70b"
        assert local["fallback"] is False

    def test_get_local_config_env_override(self, temp_config_dir, monkeypatch):
        """Test environment variable override for local config."""
        from tokencrush.config import ConfigManager

        monkeypatch.setenv("TOKENCRUSH_LOCAL_MODEL", "mistral:7b")
        monkeypatch.setenv("TOKENCRUSH_LOCAL_FALLBACK", "false")

        config = ConfigManager(config_dir=temp_config_dir)

        assert config.get_config("local", "model") == "mistral:7b"
        assert config.get_config("local", "fallback") is False

    def test_get_free_api_config_defaults(self, temp_config_dir):
        """Test getting free_api config with defaults."""
        from tokencrush.config import ConfigManager

        config = ConfigManager(config_dir=temp_config_dir)
        free_api = config.get_config("free_api")

        assert free_api["gemini_key"] == ""
        assert free_api["groq_key"] == ""
        assert free_api["priority"] == ["deepseek", "groq", "gemini"]

    def test_get_free_api_config_from_file(self, temp_config_dir):
        """Test reading free_api config from file."""
        from tokencrush.config import ConfigManager

        config_file = temp_config_dir / "config.toml"
        config_file.write_text("""
[free_api]
gemini_key = "test-gemini-key"
groq_key = "test-groq-key"
priority = ["groq", "gemini"]
""")

        config = ConfigManager(config_dir=temp_config_dir)
        free_api = config.get_config("free_api")

        assert free_api["gemini_key"] == "test-gemini-key"
        assert free_api["groq_key"] == "test-groq-key"
        assert free_api["priority"] == ["groq", "gemini"]

    def test_get_free_api_config_env_override(self, temp_config_dir, monkeypatch):
        """Test environment variable override for free_api config."""
        from tokencrush.config import ConfigManager

        monkeypatch.setenv("TOKENCRUSH_GEMINI_KEY", "env-gemini-key")
        monkeypatch.setenv("TOKENCRUSH_FREE_API_PRIORITY", "groq, gemini, deepseek")

        config = ConfigManager(config_dir=temp_config_dir)

        assert config.get_config("free_api", "gemini_key") == "env-gemini-key"
        priority = config.get_config("free_api", "priority")
        assert priority == ["groq", "gemini", "deepseek"]

    def test_get_routing_config_defaults(self, temp_config_dir):
        """Test getting routing config with defaults."""
        from tokencrush.config import ConfigManager

        config = ConfigManager(config_dir=temp_config_dir)
        routing = config.get_config("routing")

        assert routing["strategy"] == "smart"
        assert routing["compress"] is True

    def test_get_routing_config_from_file(self, temp_config_dir):
        """Test reading routing config from file."""
        from tokencrush.config import ConfigManager

        config_file = temp_config_dir / "config.toml"
        config_file.write_text("""
[routing]
strategy = "local"
compress = false
""")

        config = ConfigManager(config_dir=temp_config_dir)
        routing = config.get_config("routing")

        assert routing["strategy"] == "local"
        assert routing["compress"] is False

    def test_get_routing_config_env_override(self, temp_config_dir, monkeypatch):
        """Test environment variable override for routing config."""
        from tokencrush.config import ConfigManager

        monkeypatch.setenv("TOKENCRUSH_ROUTING_STRATEGY", "free-api")
        monkeypatch.setenv("TOKENCRUSH_ROUTING_COMPRESS", "false")

        config = ConfigManager(config_dir=temp_config_dir)

        assert config.get_config("routing", "strategy") == "free-api"
        assert config.get_config("routing", "compress") is False


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_validate_config_valid(self, temp_config_dir):
        """Test validation passes with valid config."""
        from tokencrush.config import ConfigManager

        config = ConfigManager(config_dir=temp_config_dir)
        errors = config.validate_config()

        assert errors == []

    def test_validate_cache_threshold_range(self, temp_config_dir, monkeypatch):
        """Test cache threshold validation."""
        from tokencrush.config import ConfigManager

        monkeypatch.setenv("TOKENCRUSH_CACHE_THRESHOLD", "1.5")

        config = ConfigManager(config_dir=temp_config_dir)
        errors = config.validate_config()

        # Should have error about threshold being out of range
        assert len(errors) > 0
        assert any(
            "threshold" in error.lower() or "cache" in error.lower() for error in errors
        )

    def test_validate_cache_max_size_positive(self, temp_config_dir, monkeypatch):
        """Test cache max_size must be positive."""
        from tokencrush.config import ConfigManager

        monkeypatch.setenv("TOKENCRUSH_CACHE_MAX_SIZE", "0")

        config = ConfigManager(config_dir=temp_config_dir)
        errors = config.validate_config()

        # Should have error about max_size being non-positive
        assert len(errors) > 0
        assert any(
            "max_size" in error.lower() or "cache" in error.lower() for error in errors
        )

    def test_validate_routing_strategy(self, temp_config_dir, monkeypatch):
        """Test routing strategy validation."""
        from tokencrush.config import ConfigManager

        monkeypatch.setenv("TOKENCRUSH_ROUTING_STRATEGY", "invalid-strategy")

        config = ConfigManager(config_dir=temp_config_dir)
        errors = config.validate_config()

        # Should have error about invalid strategy
        assert len(errors) > 0
        assert any(
            "strategy" in error.lower() or "routing" in error.lower()
            for error in errors
        )


class TestConfigParsing:
    """Tests for configuration value parsing."""

    def test_parse_boolean_true_values(self, temp_config_dir):
        """Test parsing boolean true values."""
        from tokencrush.config import ConfigManager

        config = ConfigManager(config_dir=temp_config_dir)

        for value in ["true", "True", "TRUE", "1", "yes", "YES"]:
            result = config._parse_config_value("cache.enabled", value)
            assert result is True, f"Failed for value: {value}"

    def test_parse_boolean_false_values(self, temp_config_dir):
        """Test parsing boolean false values."""
        from tokencrush.config import ConfigManager

        config = ConfigManager(config_dir=temp_config_dir)

        for value in ["false", "False", "FALSE", "0", "no", "NO"]:
            result = config._parse_config_value("cache.enabled", value)
            assert result is False, f"Failed for value: {value}"

    def test_parse_boolean_invalid(self, temp_config_dir):
        """Test parsing invalid boolean values."""
        from tokencrush.config import ConfigManager

        config = ConfigManager(config_dir=temp_config_dir)

        with pytest.raises(ValueError):
            config._parse_config_value("cache.enabled", "maybe")

    def test_parse_float_threshold(self, temp_config_dir):
        """Test parsing float threshold values."""
        from tokencrush.config import ConfigManager

        config = ConfigManager(config_dir=temp_config_dir)

        result = config._parse_config_value("cache.threshold", "0.75")
        assert result == 0.75

    def test_parse_float_out_of_range(self, temp_config_dir):
        """Test parsing float out of range."""
        from tokencrush.config import ConfigManager

        config = ConfigManager(config_dir=temp_config_dir)

        with pytest.raises(ValueError):
            config._parse_config_value("cache.threshold", "1.5")

    def test_parse_integer_max_size(self, temp_config_dir):
        """Test parsing integer max_size values."""
        from tokencrush.config import ConfigManager

        config = ConfigManager(config_dir=temp_config_dir)

        result = config._parse_config_value("cache.max_size", "5000")
        assert result == 5000

    def test_parse_integer_negative(self, temp_config_dir):
        """Test parsing negative integer values."""
        from tokencrush.config import ConfigManager

        config = ConfigManager(config_dir=temp_config_dir)

        with pytest.raises(ValueError):
            config._parse_config_value("cache.max_size", "-100")

    def test_parse_list_priority(self, temp_config_dir):
        """Test parsing list priority values."""
        from tokencrush.config import ConfigManager

        config = ConfigManager(config_dir=temp_config_dir)

        result = config._parse_config_value(
            "free_api.priority", "groq, gemini, deepseek"
        )
        assert result == ["groq", "gemini", "deepseek"]
