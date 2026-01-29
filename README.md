# TokenCrush v2.0 - 100% Free LLM Cost Optimizer

> Reduce LLM API costs by 95-100% with semantic caching, local LLM, and free API routing.

[![PyPI version](https://img.shields.io/badge/pypi-v2.0.1-blue.svg)](https://pypi.org/project/tokencrush/)
[![Tests](https://img.shields.io/badge/tests-243%20passing-brightgreen.svg)](#)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**TokenCrush v2** combines semantic caching, local LLM, free API routing, and token compression for **95-100% cost reduction** - all without paid services.

---

## Zero-Config Mode (NEW!)

Just import and enable - all LLM SDK calls are automatically cached:

```python
import tokencrush
tokencrush.enable()

# Now all OpenAI/Anthropic/Gemini/LiteLLM calls are cached!
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(...)  # Automatically cached!
```

---

## Quick Start

Copy and paste this to your AI agent (Claude Code, Cursor, AmpCode, etc.):

```bash
pip install tokencrush
tokencrush chat "Hello" --smart
tokencrush config set gemini YOUR_KEY
tokencrush config set groq YOUR_KEY
tokencrush config set deepseek YOUR_KEY
tokencrush stats
```

---

## Proxy Server (Beta)

Route ALL your AI agent LLM calls through TokenCrush for automatic caching and compression.

### Usage

```bash
# Start proxy server
tokencrush serve --port 8080

# Configure your AI agent to use the proxy
export OPENAI_API_BASE=http://localhost:8080/v1
export OPENAI_API_KEY=your-actual-api-key
```

Now all LLM calls from your AI agent (OpenCode, Cursor, Claude Code, etc.) will:
1. Check semantic cache (instant return if hit = FREE)
2. Compress prompts (30-50% token reduction via extractive compression)
3. Forward to your configured LLM API
4. Cache responses for future similar queries

### Legal Notice

- This proxy forwards requests to YOUR configured LLM API using YOUR API keys
- You are responsible for compliance with your LLM provider's Terms of Service
- Cached responses are stored locally on your machine (~/.cache/tokencrush/)
- No data is sent to third parties
- TokenCrush does NOT provide API keys or free LLM access

---

## Free API Limits

| Provider | RPM | Daily | Notes |
|----------|-----|-------|-------|
| DeepSeek | Unlimited | Unlimited | Best for volume |
| Groq | 30 | Unlimited | Fast inference |
| Gemini | 15 | 1,000 | Google |

Auto-rotates when quota exceeded.

---

## Important Notices

- **EU/EEA/UK/CH:** Gemini blocked (GDPR). Use Ollama, Groq, or DeepSeek.
- **Age:** 18+ for third-party APIs.
- **License:** MIT. No warranties. See [LEGAL.md](LEGAL.md).

---

## Support

[GitHub Issues](https://github.com/xodn348/tokencrush/issues) | [Discussions](https://github.com/xodn348/tokencrush/discussions)

**Acknowledgments:** [LLMLingua](https://github.com/microsoft/LLMLingua), [LiteLLM](https://github.com/BerriAI/litellm), [Ollama](https://ollama.ai), [FAISS](https://github.com/facebookresearch/faiss), [Sentence Transformers](https://www.sbert.net), [oh-my-opencode](https://github.com/travisennis/oh-my-opencode)

**100% FREE. 100% Open Source. MIT License.**

---
