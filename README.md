# TokenCrush

> **One line. Zero config. 100% free LLM caching.**

```python
import tokencrush; tokencrush.enable()
```

That's it. All your OpenAI, Anthropic, Gemini, and LiteLLM calls are now cached.

---

## Install

```bash
pip install tokencrush
```

---

## Usage

### Zero-Config Mode (Recommended)

```python
import tokencrush
tokencrush.enable()

# Your existing code works unchanged
from openai import OpenAI
client = OpenAI()

# First call: hits API (~2-6 seconds)
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is Python?"}]
)

# Second identical call: instant from cache (~0.02 seconds)
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is Python?"}]
)

# Disable when done
tokencrush.disable()
```

**Result**: 251x faster. $0 API cost on cached requests.

### Supported SDKs

| SDK | Status |
|-----|--------|
| OpenAI | ✅ Supported |
| Anthropic | ✅ Supported |
| Google Gemini | ✅ Supported |
| LiteLLM | ✅ Supported |

---

## How It Works

1. **Semantic Caching**: Uses FAISS + sentence-transformers to find similar previous queries
2. **Local Storage**: Cache stored in `~/.cache/tokencrush/` (your machine only)
3. **Transparent**: Your code doesn't change. Just `enable()` at the start.

---

## CLI

```bash
# Interactive chat with caching
tokencrush chat "Hello" --smart

# Configure free API providers
tokencrush config set gemini YOUR_KEY
tokencrush config set groq YOUR_KEY
tokencrush config set deepseek YOUR_KEY

# View cache statistics
tokencrush stats
```

---

## Proxy Server

Route all LLM calls through TokenCrush for automatic caching:

```bash
# Start proxy
tokencrush serve --port 8080

# Point your tools at the proxy
export OPENAI_API_BASE=http://localhost:8080/v1
```

Works with Claude Code, Cursor, OpenCode, and any OpenAI-compatible client.

---

## Free API Providers

| Provider | Rate Limit | Notes |
|----------|------------|-------|
| DeepSeek | Unlimited | Best for volume |
| Groq | 30 RPM | Fast inference |
| Gemini | 15 RPM | Not available in EU/EEA/UK |

Auto-rotates when quota exceeded.

---

## Requirements

- Python 3.10+
- ~500MB disk for embedding model (downloaded on first use)

---

## License

MIT. See [LICENSE](LICENSE).

---

## Links

- [GitHub](https://github.com/xodn348/tokencrush)
- [Issues](https://github.com/xodn348/tokencrush/issues)
- [LEGAL.md](LEGAL.md) - Terms and notices

**Built with**: [FAISS](https://github.com/facebookresearch/faiss), [Sentence Transformers](https://www.sbert.net), [LiteLLM](https://github.com/BerriAI/litellm)
