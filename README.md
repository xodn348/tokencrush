# TokenCrush

**LLM API cost optimizer** - Cache responses, compress prompts, save money.

## How It Works

```
Your App → TokenCrush Proxy → LLM API (OpenAI/Anthropic)
              ↓
         1. Check cache → Hit? Return instantly (FREE!)
         2. Miss? Compress prompt → Forward to API
         3. Cache response for next time
```

**Result**: Same request = instant + free. New request = 30-50% fewer tokens.

## Quick Start

```bash
# Install
pip install tokencrush

# Enable system-wide (Cursor, Claude Code, OpenCode, etc.)
tokencrush install

# Done! All LLM calls now go through TokenCrush
```

## Commands

```bash
tokencrush install        # Start proxy + configure shell
tokencrush daemon-status  # Check if running
tokencrush uninstall      # Remove
```

## For Python Code

```python
import tokencrush
tokencrush.enable(compress=True)

# Your code unchanged - caching happens automatically
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(...)
```

## Supported

- OpenAI API
- Anthropic API (Claude)
- Any OpenAI-compatible tool

## How Much Does It Save?

| Scenario | Cost |
|----------|------|
| Cache hit | $0 (instant) |
| Cache miss | 30-50% less tokens |

---

MIT License
