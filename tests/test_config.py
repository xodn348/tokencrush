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
