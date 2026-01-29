"""LiteLLM interceptor."""

import json, logging
from typing import Optional
import wrapt
from tokencrush.cache import SemanticCache
from tokencrush.interceptors import InterceptorBase, register

logger = logging.getLogger(__name__)


class LiteLLMInterceptor(InterceptorBase):
    _cache: Optional[SemanticCache] = None
    _compressor = None
    _patched: bool = False

    def _get_cache(self):
        if self._cache is None:
            self._cache = SemanticCache()
        return self._cache

    def _get_compressor(self):
        if self._compressor is None:
            from tokencrush.compressor import TokenCompressor

            self._compressor = TokenCompressor()
        return self._compressor

    def _compress_messages(self, messages):
        """Compress user messages if compression is enabled."""
        from tokencrush.patch import get_compression_settings

        compress, rate = get_compression_settings()
        if not compress:
            return messages

        compressed = []
        for msg in messages:
            if msg.get("role") == "user" and len(msg.get("content", "")) > 100:
                try:
                    result = self._get_compressor().compress(msg["content"], rate=rate)
                    compressed.append({**msg, "content": result.compressed_text})
                except Exception:
                    compressed.append(msg)
            else:
                compressed.append(msg)
        return compressed

    def patch(self):
        if self._patched:
            return
        try:
            import litellm
        except ImportError:
            raise ImportError("litellm not installed")

        interceptor = self

        def wrapper(wrapped, instance, args, kwargs):
            try:
                messages = kwargs.get("messages", [])

                # Compress messages for API call (if enabled)
                compressed_messages = interceptor._compress_messages(messages)
                kwargs["messages"] = compressed_messages

                return wrapped(*args, **kwargs)
            except:
                return wrapped(*args, **kwargs)

        wrapt.wrap_function_wrapper("litellm", "completion", wrapper)
        self._patched = True

    def unpatch(self):
        self._patched = False


register("litellm", LiteLLMInterceptor())
