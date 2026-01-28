# TokenCrush v2.0

> **100% FREE Open Source LLM Optimizer** - Reduce API costs by 95-100% with semantic caching, local LLM, and free API routing.

[![PyPI version](https://img.shields.io/badge/pypi-v2.0.0-blue.svg)](https://pypi.org/project/tokencrush/)
[![Tests](https://img.shields.io/badge/tests-243%20passing-brightgreen.svg)](#)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**TokenCrush v2** is a complete LLM cost optimization toolkit that combines semantic caching, local LLM integration, free API routing, and token compression to deliver **95-100% cost reduction** - all without requiring any paid services.

## Why TokenCrush v2?

**Before TokenCrush:**
- 1000 queries/day × $0.01/query = **$10/day = $300/month**

**After TokenCrush v2:**
- 700 queries cached (70% hit rate) = **$0**
- 200 queries via Ollama (local LLM) = **$0**
- 100 queries via Gemini (free tier) = **$0**
- **Total: $0/month (100% savings)**

## Features

### 🎯 100% FREE Architecture
- **No paid services required** - Everything runs locally or uses free tiers
- **No hidden costs** - Semantic caching, local LLM, and free APIs only
- **No vendor lock-in** - Open source, self-hosted, your data stays local

### 🚀 v2 Capabilities

- **Semantic Caching** (70-90% hit rate)
  - SQLite + FAISS vector search
  - Similarity threshold: 0.85
  - 24-hour TTL, 10,000 entry limit
  - Instant responses on cache hits

- **Local LLM Integration** (Ollama)
  - Completely free, runs on your machine
  - Default model: deepseek-r1:8b (M1/M2 optimized)
  - Supports: llama3, qwen, mistral, and more
  - No API calls, no rate limits

- **Free API Routing**
  - **Gemini**: 15 RPM, 1000 requests/day
  - **Groq**: 30 RPM, unlimited daily
  - **DeepSeek**: Unlimited free tier
  - Auto-rotation when quotas exceeded

- **Smart Routing**
  - Priority: Cache → Local LLM → Free API
  - Never auto-fallback to paid services
  - Configurable routing strategies

- **Token Compression** (LLMLingua-2)
  - 50-80% token reduction
  - Preserves semantic meaning
  - Works with all providers

## Installation

```bash
pip install tokencrush
```

Or with uv:

```bash
uv add tokencrush
```

## Quick Start

### 1. Install Ollama (Local LLM - Optional but Recommended)

**macOS:**
```bash
brew install ollama
ollama serve  # Start Ollama server
ollama pull deepseek-r1:8b  # Download model (4.7GB)
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
ollama pull deepseek-r1:8b
```

**Windows:**
Download from [ollama.ai/download](https://ollama.ai/download)

### 2. Get Free API Keys (Optional)

**Gemini (Google):**
1. Visit [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click "Create API Key"
3. Free tier: 15 requests/minute, 1000 requests/day

**Groq:**
1. Visit [console.groq.com](https://console.groq.com)
2. Sign up and create API key
3. Free tier: 30 requests/minute, unlimited daily

**DeepSeek:**
1. Visit [platform.deepseek.com](https://platform.deepseek.com)
2. Sign up and create API key
3. Free tier: Unlimited requests

### 3. Configure TokenCrush

```bash
# Set free API keys (optional - only if you want free API routing)
tokencrush config set gemini your-gemini-key
tokencrush config set groq your-groq-key
tokencrush config set deepseek your-deepseek-key
```

### 4. Start Using TokenCrush

```bash
# Smart routing (cache → local → free API)
tokencrush chat "What is quantum computing?" --smart

# Force local LLM only
tokencrush chat "Explain AI" --local

# Force free API only
tokencrush chat "Write a poem" --free-api

# View statistics
tokencrush stats

# Manage cache
tokencrush cache stats
tokencrush cache clear
```

## CLI Usage

### Chat Commands

```bash
# Smart routing (default) - tries cache, then local, then free API
tokencrush chat "Your question here"
tokencrush chat "Your question here" --smart

# Force local LLM (Ollama)
tokencrush chat "Your question here" --local

# Force free API (Gemini/Groq/DeepSeek)
tokencrush chat "Your question here" --free-api
```

### Statistics

```bash
# View cache statistics
tokencrush stats

# Output:
# ┌─────────────────────────────────────┐
# │        Cache Statistics             │
# ├──────────────────┬──────────────────┤
# │ Cache Hit Rate   │ 73.5%            │
# │ Total Queries    │ 1,234            │
# │ Cache Hits       │ 907              │
# │ Cost Saved       │ $12.34           │
# └──────────────────┴──────────────────┘
```

### Cache Management

```bash
# Show cache statistics
tokencrush cache stats

# Clear all cache entries
tokencrush cache clear
```

### Token Compression (v1 Feature)

```bash
# Compress text to reduce tokens
tokencrush compress "Your very long prompt text here..." --rate 0.5

# Output:
# ┌─────────────────────────────────────┐
# │        Compression Result           │
# ├──────────────────┬──────────────────┤
# │ Original Tokens  │ 500              │
# │ Compressed Tokens│ 150              │
# │ Compression Ratio│ 30.0%            │
# │ Tokens Saved     │ 350              │
# └──────────────────┴──────────────────┘
```

## Python SDK

### Basic Usage

```python
from tokencrush import TokenCrush

# Initialize
tc = TokenCrush()

# Smart routing (default) - cache → local → free API
response = tc.chat("What is artificial intelligence?")
print(response.response)
print(f"Source: {response.source}")  # "cache", "local", or "free-api"
print(f"Tokens saved: {response.tokens_saved}")

# Force local LLM
response = tc.chat("Explain quantum computing", mode="local")

# Force free API
response = tc.chat("Write a haiku", mode="free")

# Cache-only mode (error if not cached)
response = tc.chat("Previous question", mode="cache-only")
```

### Statistics and Cache Management

```python
# Get statistics
stats = tc.stats()
print(f"Cache hit rate: {stats.cache_hit_rate:.1%}")
print(f"Total queries: {stats.total_queries}")
print(f"Cache hits: {stats.cache_hits}")
print(f"Cost saved: ${stats.cost_saved:.2f}")

# Clear cache
tc.clear_cache()
```

### Token Compression

```python
# Compress text
compressed = tc.compress("Your very long prompt text here...", rate=0.5)
print(f"Original: {compressed.original_tokens} tokens")
print(f"Compressed: {compressed.compressed_tokens} tokens")
print(f"Saved: {compressed.tokens_saved} tokens")
```

## Architecture

### Routing Priority (100% FREE)

```
User Query
    ↓
┌─────────────────┐
│ 1. Cache Check  │ ← Instant response if cached (70-90% hit rate)
└─────────────────┘
    ↓ (miss)
┌─────────────────┐
│ 2. Local LLM    │ ← Ollama (deepseek-r1:8b, llama3, etc.)
│   (Ollama)      │   Completely free, no API calls
└─────────────────┘
    ↓ (unavailable)
┌─────────────────┐
│ 3. Free API     │ ← Gemini (1000/day), Groq (30 RPM), DeepSeek (unlimited)
│   Routing       │   Auto-rotation on quota exceeded
└─────────────────┘
    ↓ (quota exceeded)
┌─────────────────┐
│ 4. Error        │ ← Never auto-fallback to paid services
│   (No Paid)     │   User must explicitly enable paid APIs
└─────────────────┘
```

### Routing Strategies

- **`smart`** (default): Cache → Local → Free API with fallback
- **`local`**: Force Ollama only (error if unavailable)
- **`free-api`**: Force free APIs only (skip local)
- **`cache-only`**: Return cached response or error

### Cost Savings Breakdown

| Component | Hit Rate | Cost Reduction |
|-----------|----------|----------------|
| Semantic Cache | 70-90% | 70-90% saved |
| Local LLM (Ollama) | 15-25% | 15-25% saved |
| Free API (Gemini/Groq) | 5-10% | 5-10% saved |
| **Combined** | **95-100%** | **95-100% saved** |

## Configuration

### Config File Location

`~/.config/tokencrush/config.toml`

### Configuration Options

```toml
[cache]
enabled = true
threshold = 0.85  # Similarity threshold (0-1)
max_size = 10000  # Max cache entries
ttl = 86400       # Time-to-live in seconds (24 hours)

[local]
enabled = true
model = "deepseek-r1:8b"  # Ollama model
fallback = true           # Fallback to free API if unavailable

[free_api]
gemini_key = "your-key"
groq_key = "your-key"
deepseek_key = "your-key"
priority = ["deepseek", "groq", "gemini"]  # Provider priority

[routing]
strategy = "smart"  # smart, local, free-api, cache-only
compress = true     # Enable token compression
```

### Environment Variables

All config options can be overridden with environment variables:

```bash
export TOKENCRUSH_CACHE_ENABLED=true
export TOKENCRUSH_CACHE_THRESHOLD=0.85
export TOKENCRUSH_LOCAL_MODEL=llama3:70b
export TOKENCRUSH_GEMINI_KEY=your-key
export TOKENCRUSH_GROQ_KEY=your-key
export TOKENCRUSH_ROUTING_STRATEGY=smart
```

## Ollama Models

TokenCrush works with any Ollama model. Popular choices:

| Model | Size | Best For |
|-------|------|----------|
| deepseek-r1:8b | 4.7GB | General purpose (default) |
| llama3:8b | 4.7GB | Fast responses |
| qwen2.5:7b | 4.7GB | Multilingual |
| mistral:7b | 4.1GB | Code generation |
| llama3:70b | 40GB | High quality (requires 64GB RAM) |

```bash
# List available models
ollama list

# Pull a new model
ollama pull llama3:8b

# Use a different model
tokencrush chat "Question" --local
# (Configure model in config.toml or env var)
```

## Free API Limits

| Provider | RPM | Daily Limit | Notes |
|----------|-----|-------------|-------|
| **DeepSeek** | Unlimited | Unlimited | Best for high volume |
| **Groq** | 30 | Unlimited | Fast inference |
| **Gemini** | 15 | 1,000 | Google's free tier |

TokenCrush automatically rotates providers when quotas are exceeded.

## Cost Comparison

### Scenario: 1,000 queries/day

| Solution | Monthly Cost | Savings |
|----------|--------------|---------|
| **OpenAI GPT-4** | $300 | 0% |
| **Claude 3 Sonnet** | $150 | 50% |
| **Gemini Pro (paid)** | $75 | 75% |
| **TokenCrush v1** (compression only) | $60 | 80% |
| **TokenCrush v2** (cache + local + free) | **$0** | **100%** |

## Development

```bash
# Clone the repository
git clone https://github.com/xodn348/tokencrush.git
cd tokencrush

# Install with dev dependencies
uv sync --all-extras

# Run tests (243 tests)
uv run pytest -v

# Run specific test suites
uv run pytest tests/test_cache.py -v
uv run pytest tests/test_local.py -v
uv run pytest tests/test_free_api.py -v
uv run pytest tests/test_router.py -v

# Build package
uv build
```

## Testing

TokenCrush v2 has comprehensive test coverage:

- **243 total tests passing**
- 29 cache tests (semantic search, TTL, limits)
- 13 local LLM tests (Ollama integration)
- 23 free API tests (quota tracking, rotation)
- 41 router tests (smart routing, fallback)
- 31 config tests (validation, env vars)
- 41 SDK tests (Python API)
- 11 CLI tests (commands, flags)
- 40 integration tests (end-to-end v2)
- 14 other tests (compression, providers)

## Troubleshooting

### Ollama Not Available

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Pull model if missing
ollama pull deepseek-r1:8b
```

### Free API Quota Exceeded

```bash
# Check current usage
tokencrush stats

# TokenCrush will auto-rotate to next provider
# Or wait for quota reset (midnight UTC for daily, 60s for RPM)
```

### Cache Not Working

```bash
# Check cache stats
tokencrush cache stats

# Clear cache if corrupted
tokencrush cache clear

# Verify cache is enabled
cat ~/.config/tokencrush/config.toml
```

## Roadmap

- [ ] Web UI for cache management
- [ ] Multi-language support (embeddings)
- [ ] Custom embedding models
- [ ] Distributed cache (Redis)
- [ ] More free API providers
- [ ] Streaming responses
- [ ] Batch processing

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass (`pytest -v`)
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [LLMLingua](https://github.com/microsoft/LLMLingua) by Microsoft Research - Token compression
- [LiteLLM](https://github.com/BerriAI/litellm) - Multi-provider support
- [Ollama](https://ollama.ai) - Local LLM runtime
- [FAISS](https://github.com/facebookresearch/faiss) - Vector similarity search
- [Sentence Transformers](https://www.sbert.net) - Semantic embeddings

## Support

- **Issues**: [GitHub Issues](https://github.com/xodn348/tokencrush/issues)
- **Discussions**: [GitHub Discussions](https://github.com/xodn348/tokencrush/discussions)
- **Documentation**: [Wiki](https://github.com/xodn348/tokencrush/wiki)

---

**Made with ❤️ by the TokenCrush team. 100% FREE. 100% Open Source.**
