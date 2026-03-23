<div align="center">

# Sigma

### Terminal-native financial research

[![Version](https://img.shields.io/badge/version-3.7.2-3b82f6?style=for-the-badge&logo=python&logoColor=white)](https://github.com/desenyon/sigma)
[![UI](https://img.shields.io/badge/UI-Textual-7c3aed?style=for-the-badge)](https://textual.textualize.io/)
[![Python](https://img.shields.io/badge/python-3.11+-0f172a?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

A keyboard-driven research environment that pairs **multi-provider LLMs** with **market data and tooling** in the terminal. Configure keys locally, choose cloud or local models, and stay in flow without leaving the shell.

</div>

---

## Command reference

Sigma has two surfaces: a **full-screen TUI** (Textual) for interactive research, and a **CLI** for one-shot commands, health checks, and scripting. Configuration and exports live under **`~/.sigma/`** (for example `config.env`, `charts/`, `exports/`).

### Launch

| How | Notes |
| :--- | :--- |
| `sigma` | Default: opens the TUI (splash + quick reference, then chat). |
| `python -m sigma` | Same as above. |
| `sigma-app` | **macOS GUI script** (see `[project.gui-scripts]` in `pyproject.toml`): launches the packaged app entry when installed. |

On **first run**, an interactive setup wizard may run; you can also use `sigma --setup` or `sigma-setup` anytime.

---

### CLI (terminal)

Global options (run before or without a subcommand):

| Option | Purpose |
| :--- | :--- |
| `-h`, `--help` | Full argparse help and examples. |
| `-v`, `--version` | Show version (Rich banner unless `--no-ui`). |
| `--no-ui` | With `--version`: print plain `sigma x.y.z` only. |
| `--setup` | Interactive setup wizard. |
| `--setkey PROVIDER KEY` | Save a key in `~/.sigma/config.env` (`google`, `openai`, `anthropic`, `groq`, `xai`, `polygon`, `alphavantage`, `exa`). |
| `--provider {google,openai,anthropic,groq,xai,ollama}` | Set default AI provider. |
| `--model MODEL` | Set default model id. |
| `--list-models` | Print bundled model suggestions by provider. |
| `--status` | Config summary: provider, model, Ollama, LEAN hints, key presence. |

Subcommands:

| Command | Purpose |
| :--- | :--- |
| `sigma ask QUERY…` | One-shot LLM call **with tools** (non-interactive); uses your default provider/model. |
| `sigma quote SYM [SYM …]` | Table of quotes (price, change, volume). |
| `sigma chart SYM` | Candlestick chart written under `~/.sigma/charts` (yfinance). Use `--period` (default `6mo`), `-o` / `--output` to copy PNG elsewhere. |
| `sigma backtest SYM` | Built-in backtest engine. `-s` / `--strategy` (default `sma_crossover`), `--period` (default `1y`). |
| `sigma compare SYM [SYM …]` | Compare returns, vol, Sharpe, P/E, etc. |
| `sigma news SYM` | Unified headline digest (Polygon / Alpha Vantage / Exa / Yahoo depending on keys). `-n` / `--limit` for max articles. |
| `sigma doctor` | Health check: Python deps, `ollama` / `lean` on `PATH`, API key **presence** (not values). |
| `sigma tools` | Print all registered LLM tool names (same registry the TUI uses). |

**`sigma backtest -s` strategy ids** (implemented in the built-in engine): `sma_crossover`, `rsi_mean_reversion`, `macd_momentum`, `bollinger_bands`, `dual_momentum`, `breakout`, `pairs_trading`. The `/backtest` slash command in the TUI lists additional **example** names for autocomplete; use the ids above (or `sigma backtest SYM` and read the error’s `available` list) for CLI runs.

Run `sigma -h` for the exact option list on your install.

---

### TUI (full-screen terminal UI)

**Layout:** Scrollable conversation, tool calls inline, composer at the bottom. Theme is a dark, low-distraction palette (Tokyo Night–inspired). Tickers such as `AAPL` or `$NVDA` are highlighted; a small badge can show the latest symbol as you type.

**Keyboard**

| Key | Action |
| :--- | :--- |
| **Enter** | Send the current line (natural language, or a `/` command). |
| **Tab** | If the line starts with `/`, insert the **selected** slash command from the menu; otherwise append **ghost text** from Ollama completion when available. |
| **Up** / **Down** | Move the highlight in the **slash command** menu (when `/` menu is open). |
| **Ctrl+L** | Clear the chat transcript (same idea as `/clear`). |
| **Ctrl+C** | Quit the app. |

**Slash commands** (type `/` in the composer; use Tab to complete, `/help` for the full list with descriptions):

| Command | Purpose |
| :--- | :--- |
| `/help` | List all slash commands with short help. |
| `/shortcuts` | Show keyboard reference inside the app. |
| `/status` | Markdown status: provider, model, Ollama, LEAN, keys (like `sigma --status`). |
| `/keys` | Table of which API keys are set (not secret values). |
| `/models` | Reference models by provider (like `sigma --list-models`). |
| `/provider` | Show active provider; points to `sigma --provider`. |
| `/model` | Show default model; optional extra text is echoed; points to `sigma --model`. |
| `/backtest` | List example **strategy ids** (see also `sigma backtest -s`). |
| `/tools` | List registered tools (names only). |
| `/export` | Save the current chat to `~/.sigma/exports/sigma-chat-YYYYMMDD-HHMMSS.md`. |
| `/clear` | Clear transcript (same as **Ctrl+L**). |
| `/reload` | Reload the LLM router after you change keys or env. |
| `/news SYMBOL` or `/digest …` | Headline digest; optional numeric limit, e.g. `/news AAPL 15`. |
| `/quote SYMBOL` | Quick JSON quote for one symbol. |
| `/setup-help` | Setup steps and links (keys, provider, model). |
| `/compare`, `/chart`, `/report`, `/alert`, `/watchlist`, `/portfolio`, `/strategy`, `/preset` | Short tips: prefer natural language in chat or the matching `sigma` CLI (`compare`, `chart`, …). |

**Without a leading `/`**, the input is treated as a **normal prompt** to the model (streaming reply, tools may run). The composer hint line summarizes: Tab complete, `/` for commands, Ctrl+L clear, Ctrl+C quit.

If the LLM is not configured, a **setup gate** may appear with **Retry** (re-check) and **Continue anyway**.

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
# Editable install with dev tools: pip install -e ".[dev]"
```

With **[uv](https://github.com/astral-sh/uv)** (optional):

```bash
cd sigma
uv sync --extra dev
uv run sigma --version
```

Start the app (see **Command reference > Launch** above):

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
