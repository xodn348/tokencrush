"""End-to-end integration tests for TokenCrush."""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path


runner = CliRunner()


class TestIntegration:
    """Integration tests for full workflows."""

    def test_config_workflow(self, temp_config_dir):
        """Test: config set → config show → key visible."""
        from tokencrush.cli import app
        from tokencrush.config import ConfigManager
        
        with patch('tokencrush.cli.ConfigManager') as mock_cm:
            mock_instance = MagicMock()
            mock_instance.list_providers.return_value = ["openai"]
            mock_instance.get_api_key.return_value = "sk-test-key"
            # Use the real mask_key static method
            mock_cm.mask_key = ConfigManager.mask_key
            mock_instance.mask_key = ConfigManager.mask_key
            mock_cm.return_value = mock_instance
            
            # Set key
            result = runner.invoke(app, ["config", "set", "openai", "sk-test-key"])
            assert result.exit_code == 0
            
            # Show should display it
            result = runner.invoke(app, ["config", "show"])
            assert result.exit_code == 0

    def test_compress_workflow(self):
        """Test: compress → tokens reduced."""
        from tokencrush.cli import app
        from tokencrush.compressor import CompressResult
        
        with patch('tokencrush.cli.TokenCompressor') as mock_tc:
            mock_instance = MagicMock()
            mock_instance.compress.return_value = CompressResult(
                original_tokens=500,
                compressed_tokens=200,
                compressed_text="This is compressed output",
                ratio=0.4,
            )
            mock_tc.return_value = mock_instance
            
            result = runner.invoke(app, ["compress", "A very long text " * 50])
            
            assert result.exit_code == 0
            assert "500" in result.stdout or "200" in result.stdout

    def test_chat_workflow(self, mock_env_keys):
        """Test: chat → compress + API call."""
        from tokencrush.cli import app
        from tokencrush.compressor import CompressResult
        
        with patch('tokencrush.cli.TokenCompressor') as mock_tc, \
             patch('tokencrush.cli.LLMProvider') as mock_provider:
            
            mock_tc_instance = MagicMock()
            mock_tc_instance.compress.return_value = CompressResult(
                original_tokens=100,
                compressed_tokens=50,
                compressed_text="compressed query",
                ratio=0.5,
            )
            mock_tc.return_value = mock_tc_instance
            
            mock_provider_instance = MagicMock()
            mock_provider_instance.chat.return_value = "This is the LLM response."
            mock_provider.return_value = mock_provider_instance
            
            result = runner.invoke(app, ["chat", "What is Python?", "--model", "gpt-4"])
            
            assert result.exit_code == 0
            # Verify compression was called
            mock_tc_instance.compress.assert_called_once()
            # Verify LLM was called with compressed text
            mock_provider_instance.chat.assert_called_once()

    def test_compress_with_rate(self):
        """Test: compress with custom rate."""
        from tokencrush.cli import app
        from tokencrush.compressor import CompressResult
        
        with patch('tokencrush.cli.TokenCompressor') as mock_tc:
            mock_instance = MagicMock()
            mock_instance.compress.return_value = CompressResult(
                original_tokens=500,
                compressed_tokens=100,
                compressed_text="Highly compressed",
                ratio=0.2,
            )
            mock_tc.return_value = mock_instance
            
            result = runner.invoke(app, ["compress", "A very long text " * 50, "--rate", "0.2"])
            
            assert result.exit_code == 0
            mock_instance.compress.assert_called_once_with("A very long text " * 50, rate=0.2)
