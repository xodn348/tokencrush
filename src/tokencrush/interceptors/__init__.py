"""SDK interceptors for zero-config patching."""

from abc import ABC, abstractmethod
from typing import Dict


class InterceptorBase(ABC):
    """Base class for SDK interceptors."""

    @abstractmethod
    def patch(self) -> None:
        """Apply patches to the SDK."""
        pass

    @abstractmethod
    def unpatch(self) -> None:
        """Remove patches and restore original behavior."""
        pass


registry: Dict[str, InterceptorBase] = {}


def register(name: str, interceptor: InterceptorBase) -> None:
    """Register an interceptor."""
    registry[name] = interceptor


# Auto-import interceptors to register them
try:
    from tokencrush.interceptors import openai_interceptor
except ImportError:
    pass

try:
    from tokencrush.interceptors import anthropic_interceptor
except ImportError:
    pass

try:
    from tokencrush.interceptors import gemini_interceptor
except ImportError:
    pass

try:
    from tokencrush.interceptors import litellm_interceptor
except ImportError:
    pass
