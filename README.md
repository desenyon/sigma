<div align="center">

# Sigma

### Terminal-native financial research

[![Version](https://img.shields.io/badge/version-3.7.1-3b82f6?style=for-the-badge&logo=python&logoColor=white)](https://github.com/desenyon/sigma)
[![UI](https://img.shields.io/badge/UI-Textual-7c3aed?style=for-the-badge)](https://textual.textualize.io/)
[![Python](https://img.shields.io/badge/python-3.11+-0f172a?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

A keyboard-driven research environment that pairs **multi-provider LLMs** with **market data and tooling** in the terminal. Configure keys locally, choose cloud or local models, and stay in flow without leaving the shell.

</div>

---

## The interface

Sigma is built around two surfaces: a **full-screen terminal UI (TUI)** for interactive work, and a **CLI** for quick commands, health checks, and scripting.

### Full-screen terminal (Textual)

| | |
| :--- | :--- |
| **Launch** | `sigma` or `python -m sigma` |
| **Layout** | Scrollable conversation, tool activity inline, fixed input row at the bottom |
| **Theme** | Dark, low-distraction palette (Tokyo Night–inspired) |
| **Input** | Type natural-language prompts; optional Tab behavior for inline suggestions when Ollama is available |

**Keyboard**

| Shortcut | Action |
| :--- | :--- |
| `Ctrl+C` | Quit |
| `Ctrl+L` | Clear the chat view |

On first launch, the setup wizard can walk through optional local (Ollama) and API configuration.

### Command-line interface

| Command | Purpose |
| :--- | :--- |
| `sigma` | Open the TUI (after an optional splash and quick-reference panel) |
| `sigma doctor` | Check Python imports, `ollama` / `lean` on `PATH`, and which API keys are present |
| `sigma --status` | Show active provider, model, Ollama reachability, LEAN hints, and key status |
| `sigma ask "…"` | Single-shot LLM query with tools (non-interactive) |
| `sigma quote SYM …` | Tabular quotes |
| `sigma chart SYM --period 1y` | Render a chart under `~/.sigma/charts` (optional `-o` copy path) |
| `sigma backtest SYM -s STRATEGY` | Built-in yfinance strategy backtests |
| `sigma compare SYM …` | Side-by-side comparison metrics |
| `sigma --list-models` | Reference list of suggested models by provider |
| `sigma --setkey PROVIDER KEY` | Store a key in `~/.sigma/config.env` |
| `sigma --setup` | Run the setup wizard |

Use `sigma -h` for the full option list (including `--version`, `--provider`, `--model`).

---

## Capabilities

- **Models**: Route requests through supported providers (e.g. OpenAI, Anthropic, Google Gemini, Groq, xAI) or **Ollama** locally, via the LLM router and your config.
- **Data & tools**: Stock quotes, history, comparisons, technicals, and integrations such as **Polygon.io**, **Alpha Vantage**, and **Exa** when keys are set.
- **Backtesting**: Built-in strategies over historical data (yfinance-backed engine); optional **QuantConnect LEAN** CLI for advanced workflows when installed.
- **Privacy posture**: API keys and config live under your user account (e.g. `~/.sigma/config.env`); choose what you enable.

---

## Requirements

- **Python 3.11+**
- **Ollama** (optional, recommended for local models)
- **LEAN CLI** (optional, for LEAN-based backtests)

---

## Installation

Use a virtual environment (recommended):

```bash
git clone https://github.com/desenyon/sigma.git
cd sigma
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# or: pip install -e ".[dev]"
```

Start the app:

```bash
sigma
# or
python -m sigma
```

---

## Configuration

Environment variables and `~/.sigma/config.env` control providers and models. See `.env.example` for variable names (e.g. `OPENAI_API_KEY`, `POLYGON_API_KEY`, `DEFAULT_MODEL`, `OLLAMA_HOST`).

### Model IDs (2026 reference)

Defaults in code target current-tier APIs. Override with `DEFAULT_MODEL` or `sigma --model <id>`.

| Provider | Default id | Notes |
| :--- | :--- | :--- |
| Google | `gemini-3.1-pro` | Flash: `gemini-3-flash` |
| OpenAI | `gpt-5.4` | Also: `gpt-5.2`, `gpt-5`, `o3-preview`, … |
| Anthropic | `claude-sonnet-4-6` | Opus: `claude-opus-4-6` |
| Groq | `llama-3.3-70b-versatile` | Hosted Llama / Mixtral on Groq |
| xAI | `grok-4` | Fast: `grok-4-mini` |
| Ollama | `qwen3.5:8b` | Local; run `sigma --list-models` for the full suggestion list |

Exact API names change with providers; if a call fails, switch to another id from `sigma --list-models` or your provider’s docs.

---

## Architecture (overview)

| Layer | Role |
| :--- | :--- |
| **TUI** | Textual application: chat, tool messages, input widgets |
| **CLI** | `argparse` + Rich: doctor, status, one-shot commands |
| **LLM** | Router and provider clients; tool calls from the model |
| **Tools** | Registry exposing data and analysis functions to the model |
| **Backtest** | Python engine and optional LEAN integration |

---

## Contributing

Contributions are welcome. Open an issue or pull request on the [repository](https://github.com/desenyon/sigma).

---

## License

See [LICENSE](LICENSE).

---

## Links

- [Repository](https://github.com/desenyon/sigma)
- [Documentation (wiki)](https://github.com/desenyon/sigma/wiki)
