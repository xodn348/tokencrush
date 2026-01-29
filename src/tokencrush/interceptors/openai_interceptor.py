"""OpenAI SDK interceptor."""

import json, logging
from typing import Optional
import wrapt
from tokencrush.cache import SemanticCache
from tokencrush.interceptors import InterceptorBase, register

logger = logging.getLogger(__name__)


class OpenAIInterceptor(InterceptorBase):
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

    def _cache_key(self, model, messages):
        return json.dumps({"model": model, "messages": messages}, sort_keys=True)

    def patch(self):
        if self._patched:
            return
        try:
            import openai.resources.chat.completions
        except ImportError:
            raise ImportError("openai not installed")
        interceptor = self

        def wrapper(wrapped, instance, args, kwargs):
            try:
                if kwargs.get("stream"):
                    return wrapped(*args, **kwargs)

                messages = kwargs.get("messages", [])
                model = kwargs.get("model", "gpt-3.5-turbo")

                # Cache key uses original (uncompressed) messages
                key = interceptor._cache_key(model, messages)
                cached = interceptor._get_cache().get(key)
                if cached:
                    import openai.types.chat

                    return openai.types.chat.ChatCompletion.model_validate(
                        json.loads(cached)
                    )

                # Compress messages for API call (if enabled)
                compressed_messages = interceptor._compress_messages(messages)
                kwargs["messages"] = compressed_messages

                response = wrapped(*args, **kwargs)
                try:
                    interceptor._get_cache().set(key, response.model_dump_json())
                except:
                    pass
                return response
            except:
                return wrapped(*args, **kwargs)

        wrapt.wrap_function_wrapper(
            "openai.resources.chat.completions", "Completions.create", wrapper
        )
        self._patched = True

    def unpatch(self):
        self._patched = False


register("openai", OpenAIInterceptor())
