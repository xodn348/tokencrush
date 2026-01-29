"""Token compression module using context-compressor."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CompressResult:
    """Result of prompt compression."""

    original_tokens: int
    compressed_tokens: int
    compressed_text: str
    ratio: float


class TokenCompressor:
    """Compress prompts using context-compressor to reduce token usage."""

    def __init__(self, use_gpu: bool = False, model_name: Optional[str] = None):
        """Initialize the compressor."""
        from context_compressor import ContextCompressor

        self._compressor = ContextCompressor(default_strategy='extractive')

    def compress(self, text: str, rate: float = 0.5) -> CompressResult:
        """Compress the given text."""
        if not text:
            return CompressResult(
                original_tokens=0,
                compressed_tokens=0,
                compressed_text="",
                ratio=1.0,
            )

        if len(text) < 100:
            return CompressResult(
                original_tokens=len(text.split()),
                compressed_tokens=len(text.split()),
                compressed_text=text,
                ratio=1.0,
            )

        result = self._compressor.compress(text, target_ratio=rate)

        return CompressResult(
            original_tokens=result.original_tokens,
            compressed_tokens=result.compressed_tokens,
            compressed_text=result.compressed_text,
            ratio=result.actual_ratio,
        )
