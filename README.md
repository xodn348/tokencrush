# TokenCrush v2.0 - 100% Free LLM Cost Optimizer

> Reduce LLM API costs by 95-100% with semantic caching, local LLM, and free API routing.

[![PyPI version](https://img.shields.io/badge/pypi-v2.0.0-blue.svg)](https://pypi.org/project/tokencrush/)
[![Tests](https://img.shields.io/badge/tests-243%20passing-brightgreen.svg)](#)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**TokenCrush v2** is a complete LLM cost optimization toolkit that combines semantic caching, local LLM integration, free API routing, and token compression to deliver **95-100% cost reduction** - all without requiring any paid services.

---

## Quick Start

```bash
pip install tokencrush && tokencrush chat "Hello, how are you?" --smart
```

That's it! TokenCrush works out of the box with zero configuration.

---

## Installation

```bash
pip install tokencrush
```

### Optional: Install Ollama for Local LLM

```bash
# macOS
brew install ollama
ollama serve
ollama pull deepseek-r1:8b

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
ollama pull deepseek-r1:8b

# Windows: Download from ollama.ai/download
```

### Optional: Add Free API Keys

Get free keys from: Gemini (aistudio.google.com/apikey), Groq (console.groq.com), DeepSeek (platform.deepseek.com)

```bash
tokencrush config set gemini your-key
tokencrush config set groq your-key
tokencrush config set deepseek your-key
```

---

## CLI Usage

```bash
# Smart routing (default - recommended)
tokencrush chat "Your question" --smart

# Force local LLM only (offline mode)
tokencrush chat "Your question" --local

# Force free API only
tokencrush chat "Your question" --free-api

# View statistics
tokencrush stats

# Manage cache
tokencrush cache stats
tokencrush cache clear

# Compress text (standalone)
tokencrush compress "Long text here..." --rate 0.5
```

---

## Python SDK

```python
from tokencrush import TokenCrush

# Initialize
tc = TokenCrush()

# Smart routing (default)
response = tc.chat("What is machine learning?")
print(response.response)
print(f"Source: {response.source}")  # "cache", "local", or "free-api"
print(f"Tokens saved: {response.tokens_saved}")

# Force local LLM
response = tc.chat("Explain quantum computing", mode="local")

# Force free API
response = tc.chat("Write a haiku", mode="free")

# Get statistics
stats = tc.stats()
print(f"Cache hit rate: {stats.cache_hit_rate:.1%}")
print(f"Total queries: {stats.total_queries}")
print(f"Cost saved: ${stats.cost_saved:.2f}")

# Clear cache
tc.clear_cache()
```

---

## Configuration

Config file: `~/.config/tokencrush/config.toml`

```toml
[cache]
enabled = true
threshold = 0.85

[local]
model = "deepseek-r1:8b"

[free_api]
gemini_key = "your-key"
groq_key = "your-key"
deepseek_key = "your-key"
```

---

## Ollama Models

Recommended: `deepseek-r1:8b` (4.7GB), `llama3:8b` (4.7GB), `llama-3.3-70b` (40GB)

```bash
ollama pull deepseek-r1:8b
tokencrush config set local.model deepseek-r1:8b
```

---

## Free API Limits

| Provider | RPM | Daily Limit | Notes |
|----------|-----|-------------|-------|
| **DeepSeek** | Unlimited | Unlimited | Best for high volume |
| **Groq** | 30 | Unlimited | Fast inference |
| **Gemini** | 15 | 1,000 | Google's free tier |

TokenCrush automatically rotates providers when quotas are exceeded.

---

## Important Notices

**EU/EEA/UK/Switzerland:** Gemini free tier blocked due to GDPR. Use Ollama, Groq, or DeepSeek instead.

**Age requirement:** 18+ for third-party APIs.

**Legal:** MIT License. No warranties. See [LEGAL.md](LEGAL.md) for details.

---

## Troubleshooting

**Ollama not available:** Run `ollama serve` and `ollama pull deepseek-r1:8b`

**API quota exceeded:** TokenCrush auto-rotates providers. Check usage with `tokencrush stats`

---

## License

MIT License - see [LICENSE](LICENSE)

---

## Acknowledgments

- [LLMLingua](https://github.com/microsoft/LLMLingua) by Microsoft Research - Token compression
- [LiteLLM](https://github.com/BerriAI/litellm) - Multi-provider support
- [Ollama](https://ollama.ai) - Local LLM runtime
- [FAISS](https://github.com/facebookresearch/faiss) - Vector similarity search
- [Sentence Transformers](https://www.sbert.net) - Semantic embeddings
- [oh-my-opencode](https://github.com/travisennis/oh-my-opencode) - Development tooling

---

## Support

- **Issues:** [GitHub Issues](https://github.com/xodn348/tokencrush/issues)
- **Discussions:** [GitHub Discussions](https://github.com/xodn348/tokencrush/discussions)

---

**Made with care by the TokenCrush team. 100% FREE. 100% Open Source.**
