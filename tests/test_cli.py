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

        with patch("tokencrush.cli.TokenCompressor") as mock_tc:
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

        with patch("tokencrush.cli.TokenCompressor") as mock_tc:
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

    def test_chat_command(self):
        """Test chat command with smart routing."""
        from tokencrush.cli import app
        from tokencrush.sdk import TokenCrush, SDKStats

        with patch("tokencrush.cli.TokenCrush") as mock_tc_class:
            mock_tc = MagicMock()
            mock_tc.chat.return_value = "Hello from smart routing!"
            mock_tc.stats.return_value = SDKStats(
                cache_hit_rate=0.5,
                total_queries=10,
                cached=5,
                cost_saved=0.0,
            )
            mock_tc_class.return_value = mock_tc

            result = runner.invoke(app, ["chat", "Hello"])

            assert result.exit_code == 0
            assert "Hello from smart routing!" in result.stdout
            mock_tc.chat.assert_called_once()

    def test_chat_command_local_mode(self):
        """Test chat command with --local flag."""
        from tokencrush.cli import app
        from tokencrush.sdk import TokenCrush, SDKStats

        with patch("tokencrush.cli.TokenCrush") as mock_tc_class:
            mock_tc = MagicMock()
            mock_tc.chat.return_value = "Response from local LLM"
            mock_tc.stats.return_value = SDKStats(
                cache_hit_rate=0.0,
                total_queries=1,
                cached=0,
                cost_saved=0.0,
            )
            mock_tc_class.return_value = mock_tc

            result = runner.invoke(app, ["chat", "Hello", "--local"])

            assert result.exit_code == 0
            mock_tc.chat.assert_called_once_with("Hello", mode="local")

    def test_chat_command_free_api_mode(self):
        """Test chat command with --free-api flag."""
        from tokencrush.cli import app
        from tokencrush.sdk import TokenCrush, SDKStats

        with patch("tokencrush.cli.TokenCrush") as mock_tc_class:
            mock_tc = MagicMock()
            mock_tc.chat.return_value = "Response from free API"
            mock_tc.stats.return_value = SDKStats(
                cache_hit_rate=0.0,
                total_queries=1,
                cached=0,
                cost_saved=0.0,
            )
            mock_tc_class.return_value = mock_tc

            result = runner.invoke(app, ["chat", "Hello", "--free-api"])

            assert result.exit_code == 0
            mock_tc.chat.assert_called_once_with("Hello", mode="free")

    def test_config_set(self, temp_config_dir):
        """Test config set command."""
        from tokencrush.cli import app

        with patch("tokencrush.cli.ConfigManager") as mock_cm:
            mock_instance = MagicMock()
            mock_cm.return_value = mock_instance

            result = runner.invoke(app, ["config", "set", "openai", "sk-test-key"])

            assert result.exit_code == 0
            mock_instance.set_api_key.assert_called_once_with("openai", "sk-test-key")

    def test_config_show(self, mock_env_keys):
        """Test config show command."""
        from tokencrush.cli import app

        with patch("tokencrush.cli.ConfigManager") as mock_cm:
            mock_instance = MagicMock()
            mock_instance.list_providers.return_value = ["openai", "anthropic"]
            mock_instance.get_api_key.return_value = "sk-test-key"
            mock_cm.return_value = mock_instance

            # Mock the static method properly
            with patch.object(mock_cm, "mask_key", return_value="sk-...key"):
                result = runner.invoke(app, ["config", "show"])

            assert result.exit_code == 0

    def test_stats_command(self):
        """Test stats command."""
        from tokencrush.cli import app
        from tokencrush.sdk import TokenCrush, SDKStats

        with patch("tokencrush.cli.TokenCrush") as mock_tc_class:
            mock_tc = MagicMock()
            mock_tc.stats.return_value = SDKStats(
                cache_hit_rate=0.75,
                total_queries=100,
                cached=75,
                cost_saved=0.0,
            )
            mock_tc_class.return_value = mock_tc

            result = runner.invoke(app, ["stats"])

            assert result.exit_code == 0
            assert "75.0%" in result.stdout or "75%" in result.stdout
            assert "100" in result.stdout

    def test_cache_clear_command(self):
        """Test cache clear command."""
        from tokencrush.cli import app
        from tokencrush.sdk import TokenCrush

        with patch("tokencrush.cli.TokenCrush") as mock_tc_class:
            mock_tc = MagicMock()
            mock_cache = MagicMock()
            mock_tc.router.cache = mock_cache
            mock_tc_class.return_value = mock_tc

            result = runner.invoke(app, ["cache", "clear"])

            assert result.exit_code == 0
            assert "Cache cleared" in result.stdout
            mock_cache.clear.assert_called_once()

    def test_cache_stats_command(self):
        """Test cache stats command."""
        from tokencrush.cli import app
        from tokencrush.sdk import TokenCrush, SDKStats

        with patch("tokencrush.cli.TokenCrush") as mock_tc_class:
            mock_tc = MagicMock()
            mock_tc.stats.return_value = SDKStats(
                cache_hit_rate=0.6,
                total_queries=50,
                cached=30,
                cost_saved=0.0,
            )
            mock_tc_class.return_value = mock_tc

            result = runner.invoke(app, ["cache", "stats"])

            assert result.exit_code == 0
            assert "60.0%" in result.stdout or "60%" in result.stdout
            assert "50" in result.stdout

    def test_help(self):
        """Test --help flag."""
        from tokencrush.cli import app

        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "compress" in result.stdout
        assert "chat" in result.stdout
        assert "config" in result.stdout
        assert "stats" in result.stdout
        assert "cache" in result.stdout
