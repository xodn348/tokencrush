"""Configuration management for API keys and settings."""

import os
from pathlib import Path
from typing import Optional, Dict, List

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
