"""Zero-config patching for LLM SDKs."""

from typing import List, Tuple, Any
import logging
import os

logger = logging.getLogger(__name__)

if os.environ.get("TOKENCRUSH_DEBUG"):
    logging.basicConfig(level=logging.DEBUG)

_is_enabled: bool = False
_compress_enabled: bool = False
_compression_rate: float = 0.5
_patched_methods: List[Tuple[Any, str, Any]] = []


def enable(compress: bool = False, compression_rate: float = 0.5, **kwargs) -> None:
    """Enable TokenCrush caching and compression for all LLM SDKs."""
    global _is_enabled, _compress_enabled, _compression_rate
    if _is_enabled:
        logger.debug("TokenCrush already enabled")
        return

    _compress_enabled = compress
    _compression_rate = compression_rate
    _is_enabled = True

    from tokencrush.interceptors import registry

    for name, interceptor in registry.items():
        try:
            interceptor.patch()
            logger.debug(f"Patched {name}")
        except ImportError:
            logger.debug(f"SDK {name} not installed, skipping")
        except Exception as e:
            logger.warning(f"Failed to patch {name}: {e}")


def disable() -> None:
    """Disable TokenCrush and restore original SDK behavior."""
    global _is_enabled
    if not _is_enabled:
        return

    from tokencrush.interceptors import registry

    for name, interceptor in registry.items():
        try:
            interceptor.unpatch()
            logger.debug(f"Unpatched {name}")
        except Exception as e:
            logger.warning(f"Failed to unpatch {name}: {e}")

    _is_enabled = False


def is_enabled() -> bool:
    """Check if TokenCrush patching is currently enabled."""
    return _is_enabled


def get_compression_settings() -> tuple[bool, float]:
    """Get current compression settings."""
    return _compress_enabled, _compression_rate
