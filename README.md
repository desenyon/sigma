<div align="center">

# Ephemeral

### Terminal-native financial research, rebuilt for `v3.8.0`

[![Version](https://img.shields.io/badge/version-3.8.0-3b82f6?style=for-the-badge&logo=python&logoColor=white)](https://github.com/desenyon/ephemeral)
[![Interface](https://img.shields.io/badge/interface-Ink%20%2B%20Textual-0f172a?style=for-the-badge)](https://github.com/vadimdemedes/ink)
[![Python](https://img.shields.io/badge/python-3.11+-0f172a?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

Ephemeral is a keyboard-first research environment for market analysis, thesis development, and local-or-cloud LLM workflows. It combines a Claude-Code-style Ink shell, a legacy Textual fallback, market-data tools, and provider-aware setup so you can stay inside the terminal for the entire research loop.

</div>

---

## What changed in 3.8

`v3.8.0` is a product-quality pass over the terminal experience:

- The Ink UI was redesigned around a cleaner workspace, compact sidebar, and dedicated prompt dock.
- Input handling is more reliable: typing always returns focus to the prompt, the cursor behaves consistently, and requests no longer make the shell feel frozen.
- The composer is more usable: when it is empty, `↑` and `↓` switch actions directly so the shell no longer feels static.
- The layout falls back earlier on smaller terminals so content stays inside the frame instead of clipping or colliding.
- Ollama onboarding is more accurate: setup can now adopt already-installed local models instead of assuming every machine needs a fresh pull.
- Versioning is centralized and release changes are now logged in [`CHANGELOG.md`](/Users/naitikgupta/Projects/ephemeral/CHANGELOG.md).

---

## Product surfaces

Ephemeral ships with three ways to work:

| Surface | Purpose |
| :--- | :--- |
| `ephemeral` | The default Ink command center for interactive research, setup inspection, and workflow switching. |
| `ephemeral --legacy-ui` | The older Textual experience for teams that still prefer the previous full-screen shell. |
| `ephemeral <command>` | One-shot CLI commands for scripting, automation, and quick checks. |

Configuration, exports, charts, and session artifacts live under `~/.ephemeral/`.

---

## Quick start

```bash
git clone https://github.com/desenyon/ephemeral.git
cd ephemeral
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install --prefix ephemeral/ink_ui
pip install -e ".[dev]"
ephemeral
```

With `uv`:

```bash
git clone https://github.com/desenyon/ephemeral.git
cd ephemeral
uv sync --extra dev
npm install --prefix ephemeral/ink_ui
uv run ephemeral
```

---

## The 3.8 Ink shell

The default interface is now intentionally closer to Claude Code in structure, but customized for Ephemeral research workflows: one navigator, one dominant workspace, and one durable composer.

### Core interaction model

- One dominant **workspace** pane for the selected result.
- One compact **navigator** for actions, session state, and recent runs.
- One always-available **composer** at the bottom.

### Keyboard model

- `Tab`: cycle focus across modes, activity, workspace, and prompt.
- `↑` / `↓` or `j` / `k`: move within the focused rail or scroll the workspace.
- `[` / `]`: page the workspace output.
- `d`: toggle rendered vs raw payloads.
- `Esc`: clear the current prompt and return focus to the dock.
- `Ctrl+C`: quit.

### Prompt behavior

- Typing from any pane returns focus to the prompt immediately.
- The prompt shows a live caret without appending the cursor to placeholder text.
- While a request runs, the shell remains navigable and shows the active job in the chrome.

---

## Setup and providers

Ephemeral supports both cloud providers and local models.

### Cloud providers

Set a key with:

```bash
ephemeral --setkey openai <your-key>
ephemeral --setkey anthropic <your-key>
ephemeral --setkey google <your-key>
```

Then choose a default:

```bash
ephemeral --provider openai
ephemeral --model gpt-5.4
```

### Local Ollama flow

`v3.8.0` improves the local-model path:

- If Ollama is reachable and you already have models installed, setup offers to bind one immediately.
- Selecting a local model persists `DEFAULT_PROVIDER`, `DEFAULT_MODEL`, `OLLAMA_MODEL`, and `OLLAMA_HOST` together.
- Status output now reports whether the active default model is actually available locally.

Common Ollama flow:

```bash
ollama serve
ollama pull qwen3.5:8b
ephemeral --provider ollama
ephemeral --model qwen3.5:8b
ephemeral --status
```

You can also run:

```bash
ephemeral --setup
```

to walk through installation, model binding, and key verification interactively.

---

## Command reference

### Launch and configuration

| Command | Purpose |
| :--- | :--- |
| `ephemeral` | Launch the default Ink shell. |
| `ephemeral --legacy-ui` | Launch the legacy Textual shell. |
| `ephemeral --ink-ui` | Force Ink and fail instead of falling back. |
| `ephemeral --setup` | Run the setup wizard. |
| `ephemeral --status` | Show provider, model, key presence, and dependency health. |
| `ephemeral --list-models` | Print bundled model suggestions by provider. |
| `ephemeral --provider <provider>` | Persist the default provider. |
| `ephemeral --model <id>` | Persist the default model id. |
| `ephemeral --setkey <provider> <key>` | Save an API key in `~/.ephemeral/config.env`. |

### Research workflows

| Command | Purpose |
| :--- | :--- |
| `ephemeral ask QUERY...` | Run a one-shot LLM request with tools. |
| `ephemeral quote AAPL MSFT` | Fetch quote snapshots. |
| `ephemeral news NVDA -n 12` | Produce a news digest. |
| `ephemeral compare META GOOGL AMZN` | Compare returns, vol, and quality metrics. |
| `ephemeral chart SPY --period 6mo` | Save a chart artifact. |
| `ephemeral backtest AAPL -s sma_crossover --period 2y` | Run the built-in backtest engine. |
| `ephemeral doctor` | Run a dependency and environment check. |
| `ephemeral tools` | List registered tool names. |

---

## Architecture

| Layer | Responsibility |
| :--- | :--- |
| `ephemeral/ink_ui` | React + Ink shell for the default interactive experience |
| `ephemeral/ink_bridge.py` | Structured bridge between the Ink UI and Python workflows |
| `ephemeral/cli.py` | CLI entry point and launcher orchestration |
| `ephemeral/setup_agent.py` | Setup wizard for providers, keys, and local models |
| `ephemeral/llm` | Router and provider implementations |
| `ephemeral/tools` | Tool registry and market-data integrations |
| `ephemeral/backtest` | Built-in backtesting engine and related workflows |

The release number is now centralized in [`ephemeral/version.py`](/Users/naitikgupta/Projects/ephemeral/ephemeral/version.py) to keep package metadata, runtime banners, and setup surfaces aligned.

---

## Development

### Quality gates

For the 3.8 UI and setup work, the primary checks are:

```bash
npm --prefix ephemeral/ink_ui run typecheck
npm --prefix ephemeral/ink_ui run smoke
.venv/bin/python -m pytest tests/test_ink_bridge.py tests/test_setup_agent.py -q
```

### Build

```bash
./scripts/build.sh
```

This produces:

- Python distributions under `dist/`
- A macOS app bundle via `scripts/create_app.py`

---

## Release notes

- Human-readable release history lives in [`CHANGELOG.md`](/Users/naitikgupta/Projects/ephemeral/CHANGELOG.md).
- Setup and command examples in this README reflect `v3.8.0`.

---

## License

See [LICENSE](/Users/naitikgupta/Projects/ephemeral/LICENSE).
