# TokenCrush

> LLM token optimization CLI - compress prompts, save costs.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

TokenCrush uses [LLMLingua-2](https://github.com/microsoft/LLMLingua) to compress your prompts before sending them to LLMs, reducing token usage by 50-80% while preserving response quality.

## Features

- **Prompt Compression**: Reduce tokens by 2-5x using Microsoft's LLMLingua-2
- **Multi-Provider Support**: Works with OpenAI, Anthropic (Claude), and Google (Gemini)
- **Simple CLI**: One command to compress and chat
- **Cost Savings**: Significantly reduce API costs

## Installation

```bash
pip install tokencrush
```

Or with uv:

```bash
uv add tokencrush
```

## Quick Start

### 1. Configure API Keys

```bash
# Set API keys (stored in ~/.config/tokencrush/config.toml)
tokencrush config set openai sk-your-openai-key
tokencrush config set anthropic sk-ant-your-anthropic-key
tokencrush config set google your-google-api-key

# Or use environment variables
export OPENAI_API_KEY=sk-your-key
```

### 2. Compress a Prompt

```bash
tokencrush compress "Your very long prompt text here..."
```

Output:
```
┌─────────────────────────────────────┐
│        Compression Result           │
├──────────────────┬──────────────────┤
│ Original Tokens  │ 500              │
│ Compressed Tokens│ 150              │
│ Compression Ratio│ 30.0%            │
│ Tokens Saved     │ 350              │
└──────────────────┴──────────────────┘
```

### 3. Chat with Compression

```bash
# Compress and send to GPT-4
tokencrush chat "Explain quantum computing in detail" --model gpt-4

# Use Claude
tokencrush chat "Write a poem" --model claude-3-sonnet

# Use Gemini
tokencrush chat "Summarize this" --model gemini-1.5-pro
```

## CLI Reference

### `tokencrush compress`

Compress text to reduce tokens.

```bash
tokencrush compress <text> [OPTIONS]

Options:
  -r, --rate FLOAT    Compression rate (0.0-1.0). Default: 0.5
  -g, --gpu           Use GPU for faster compression
```

### `tokencrush chat`

Compress and send to LLM.

```bash
tokencrush chat <prompt> [OPTIONS]

Options:
  -m, --model TEXT    Model to use. Default: gpt-4
  -r, --rate FLOAT    Compression rate. Default: 0.5
  -g, --gpu           Use GPU for compression
  --no-compress       Skip compression
```

### `tokencrush config`

Manage API keys.

```bash
tokencrush config set <provider> <key>   # Save API key
tokencrush config show                    # Show configured keys
```

## Supported Models

| Provider | Models |
|----------|--------|
| OpenAI | gpt-4, gpt-4-turbo, gpt-3.5-turbo |
| Anthropic | claude-3-opus, claude-3-sonnet, claude-3-haiku |
| Google | gemini-1.5-pro, gemini-1.5-flash |

## How It Works

1. **Compression**: TokenCrush uses LLMLingua-2's trained model to identify and remove redundant tokens while preserving meaning.
2. **API Call**: The compressed prompt is sent to your chosen LLM provider.
3. **Response**: You get the same quality response with fewer input tokens = lower cost.

## Development

```bash
# Clone the repository
git clone https://github.com/xodn348/tokencrush.git
cd tokencrush

# Install with dev dependencies
uv sync --all-extras

# Run tests
uv run pytest -v

# Build package
uv build
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [LLMLingua](https://github.com/microsoft/LLMLingua) by Microsoft Research
- [LiteLLM](https://github.com/BerriAI/litellm) for multi-provider support
