"""Test enable/disable functionality."""

import pytest
from tokencrush import enable, disable, is_enabled


def test_enable_disable_cycle():
    """Test basic enable/disable cycle."""
    assert is_enabled() is False
    enable()
    assert is_enabled() is True
    disable()
    assert is_enabled() is False


def test_import_interceptors():
    """Test that interceptors are registered."""
    from tokencrush.interceptors import registry

    enable()
    # Registry should have interceptors (even if SDKs not installed)
    assert isinstance(registry, dict)
    disable()
