"""Example test to verify pytest setup."""

import pytest
from tokencrush import __version__


def test_version():
    """Test that version is defined correctly."""
    assert __version__ == "2.0.1"


def test_sample_fixture(sample_text):
    """Test that sample fixture works."""
    assert len(sample_text) > 100
    assert "compressed" in sample_text
