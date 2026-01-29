"""TokenCrush - LLM token optimization CLI."""

from tokencrush.sdk import TokenCrush
from tokencrush.patch import enable, disable, is_enabled

__version__ = "2.0.1"

__all__ = ["TokenCrush", "enable", "disable", "is_enabled"]
