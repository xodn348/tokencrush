"""Anthropic SDK interceptor."""

import json, logging
from typing import Optional
import wrapt
from tokencrush.cache import SemanticCache
from tokencrush.interceptors import InterceptorBase, register

logger = logging.getLogger(__name__)


class AnthropicInterceptor(InterceptorBase):
    _cache: Optional[SemanticCache] = None
    _patched: bool = False

    def _get_cache(self):
        if self._cache is None:
            self._cache = SemanticCache()
        return self._cache

    def patch(self):
        if self._patched:
            return
        try:
            import anthropic.resources.messages
        except ImportError:
            raise ImportError("anthropic not installed")

        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        wrapt.wrap_function_wrapper(
            "anthropic.resources.messages", "Messages.create", wrapper
        )
        self._patched = True

    def unpatch(self):
        self._patched = False


register("anthropic", AnthropicInterceptor())
