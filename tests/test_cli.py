"""Tests for the CLI module."""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock


runner = CliRunner()


class TestCLI:
    """Tests for CLI commands."""

    def test_compress_command(self):
        """Test compress command."""
        from tokencrush.cli import app
        from tokencrush.compressor import CompressResult
        
        with patch('tokencrush.cli.TokenCompressor') as mock_tc:
            mock_instance = MagicMock()
            mock_instance.compress.return_value = CompressResult(
                original_tokens=100,
                compressed_tokens=50,
                compressed_text="compressed text",
                ratio=0.5,
            )
            mock_tc.return_value = mock_instance
            
            result = runner.invoke(app, ["compress", "test text"])
            
            assert result.exit_code == 0
            assert "compressed" in result.stdout.lower() or "50" in result.stdout

    def test_compress_with_rate(self):
        """Test compress command with rate option."""
        from tokencrush.cli import app
        from tokencrush.compressor import CompressResult
        
        with patch('tokencrush.cli.TokenCompressor') as mock_tc:
            mock_instance = MagicMock()
            mock_instance.compress.return_value = CompressResult(
                original_tokens=100,
                compressed_tokens=30,
                compressed_text="short",
                ratio=0.3,
            )
            mock_tc.return_value = mock_instance
            
            result = runner.invoke(app, ["compress", "test", "--rate", "0.3"])
            
            assert result.exit_code == 0

    def test_chat_command(self, mock_env_keys):
        """Test chat command."""
        from tokencrush.cli import app
        from tokencrush.compressor import CompressResult
        
        with patch('tokencrush.cli.TokenCompressor') as mock_tc, \
             patch('tokencrush.cli.LLMProvider') as mock_provider:
            
            mock_tc_instance = MagicMock()
            mock_tc_instance.compress.return_value = CompressResult(
                original_tokens=100,
                compressed_tokens=50,
                compressed_text="compressed prompt",
                ratio=0.5,
            )
            mock_tc.return_value = mock_tc_instance
            
            mock_provider_instance = MagicMock()
            mock_provider_instance.chat.return_value = "Hello from GPT!"
            mock_provider.return_value = mock_provider_instance
            
            result = runner.invoke(app, ["chat", "Hello", "--model", "gpt-4"])
            
            assert result.exit_code == 0

    def test_config_set(self, temp_config_dir):
        """Test config set command."""
        from tokencrush.cli import app
        
        with patch('tokencrush.cli.ConfigManager') as mock_cm:
            mock_instance = MagicMock()
            mock_cm.return_value = mock_instance
            
            result = runner.invoke(app, ["config", "set", "openai", "sk-test-key"])
            
            assert result.exit_code == 0
            mock_instance.set_api_key.assert_called_once_with("openai", "sk-test-key")

    def test_config_show(self, mock_env_keys):
        """Test config show command."""
        from tokencrush.cli import app
        
        with patch('tokencrush.cli.ConfigManager') as mock_cm:
            mock_instance = MagicMock()
            mock_instance.list_providers.return_value = ["openai", "anthropic"]
            mock_instance.get_api_key.return_value = "sk-test-key"
            mock_cm.return_value = mock_instance
            
            # Mock the static method properly
            with patch.object(mock_cm, 'mask_key', return_value="sk-...key"):
                result = runner.invoke(app, ["config", "show"])
            
            assert result.exit_code == 0

    def test_help(self):
        """Test --help flag."""
        from tokencrush.cli import app
        
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "compress" in result.stdout
        assert "chat" in result.stdout
        assert "config" in result.stdout
