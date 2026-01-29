"""Tests for patching infrastructure."""

import pytest
from tokencrush import patch


class TestPatchInfrastructure:
    def setup_method(self):
        patch._is_enabled = False
        patch._patched_methods = []

    def test_enable_sets_flag(self):
        assert patch.is_enabled() is False
        patch.enable()
        assert patch.is_enabled() is True
        patch.disable()

    def test_disable_clears_flag(self):
        patch.enable()
        assert patch.is_enabled() is True
        patch.disable()
        assert patch.is_enabled() is False

    def test_is_enabled_returns_state(self):
        assert patch.is_enabled() is False
        patch.enable()
        assert patch.is_enabled() is True
        patch.disable()
        assert patch.is_enabled() is False

    def test_double_enable_is_idempotent(self):
        patch.enable()
        patch.enable()
        assert patch.is_enabled() is True
        patch.disable()

    def test_double_disable_is_idempotent(self):
        patch.enable()
        patch.disable()
        patch.disable()
        assert patch.is_enabled() is False
