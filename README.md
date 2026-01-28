# TokenCrush v2.0 - 100% Free LLM Cost Optimizer

> Reduce LLM API costs by 95-100% with semantic caching, local LLM, and free API routing.

[![PyPI version](https://img.shields.io/badge/pypi-v2.0.1-blue.svg)](https://pypi.org/project/tokencrush/)
[![Tests](https://img.shields.io/badge/tests-243%20passing-brightgreen.svg)](#)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**TokenCrush v2** combines semantic caching, local LLM, free API routing, and token compression for **95-100% cost reduction** - all without paid services.

---

## For AI Agents

```bash
pip install tokencrush
tokencrush chat "Hello" --smart
tokencrush config set gemini YOUR_KEY
tokencrush config set groq YOUR_KEY
tokencrush config set deepseek YOUR_KEY
tokencrush stats
```

```python
from tokencrush import TokenCrush
tc = TokenCrush()
response = tc.chat("Your question")
print(response.response)
```

---

## Quick Start

```bash
pip install tokencrush
brew install ollama && ollama serve && ollama pull deepseek-r1:8b  # optional
tokencrush chat "Your question" --smart
```

Free API keys: [Gemini](https://aistudio.google.com/apikey) | [Groq](https://console.groq.com) | [DeepSeek](https://platform.deepseek.com)

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
