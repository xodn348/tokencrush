"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path
import tempfile
import os


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for config files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_env_keys(monkeypatch):
    """Mock environment variables for API keys."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")


@pytest.fixture
def sample_text():
    """Sample text for compression tests."""
    return "This is a sample text that needs to be compressed. " * 10
