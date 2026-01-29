"""Gemini SDK interceptor."""

import logging
from typing import Optional
import wrapt
from tokencrush.cache import SemanticCache
from tokencrush.interceptors import InterceptorBase, register

logger = logging.getLogger(__name__)


class GeminiInterceptor(InterceptorBase):
    _patched: bool = False

    def patch(self):
        if self._patched:
            return
        try:
            import google.generativeai
        except ImportError:
            raise ImportError("google-generativeai not installed")

        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        wrapt.wrap_function_wrapper(
            "google.generativeai", "GenerativeModel.generate_content", wrapper
        )
        self._patched = True

    def unpatch(self):
        self._patched = False


register("gemini", GeminiInterceptor())
