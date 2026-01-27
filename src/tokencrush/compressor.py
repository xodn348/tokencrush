"""Token compression module using LLMLingua-2."""

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
    """Compress prompts using LLMLingua-2 to reduce token usage."""
    
    DEFAULT_MODEL = "microsoft/llmlingua-2-xlm-roberta-large-meetingbank"
    
    def __init__(self, use_gpu: bool = False, model_name: Optional[str] = None):
        """Initialize the compressor."""
        from llmlingua import PromptCompressor
        
        device_map = "cuda" if use_gpu else "cpu"
        self._compressor = PromptCompressor(
            model_name=model_name or self.DEFAULT_MODEL,
            use_llmlingua2=True,
            device_map=device_map,
        )
    
    def compress(self, text: str, rate: float = 0.5) -> CompressResult:
        """Compress the given text."""
        if not text:
            return CompressResult(
                original_tokens=0,
                compressed_tokens=0,
                compressed_text="",
                ratio=1.0,
            )
        
        result = self._compressor.compress_prompt(text, rate=rate)
        original = result.get('origin_tokens', 0)
        compressed = result.get('compressed_tokens', 0)
        
        return CompressResult(
            original_tokens=original,
            compressed_tokens=compressed,
            compressed_text=result.get('compressed_prompt', ''),
            ratio=compressed / original if original > 0 else 1.0,
        )
