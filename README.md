<div align="center">

# σ SIGMA

### The Elite Financial Research Terminal

[![Version](https://img.shields.io/badge/version-3.6.1-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://github.com/sigma/terminal) [![UI](https://img.shields.io/badge/UI-Textual-purple.svg?style=for-the-badge&logo=charm&logoColor=white)](https://textual.textualize.io/) [![AI](https://img.shields.io/badge/AI-Multi--Model-green.svg?style=for-the-badge&logo=openai&logoColor=white)](https://ollama.com) [![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg?style=for-the-badge&logo=github-actions&logoColor=white)](https://github.com/sigma/terminal/actions)

<p align="center">
  <em>A high-performance, terminal-based research platform for the modern quantitative analyst.</em>
</p>

</div>

---

## Overview

**Sigma v3.6.1** is not just a chatbot—it is a **comprehensive financial operating system**. Designed for speed, privacy, and precision, Sigma unifies state-of-the-art LLMs with institutional-grade data tools in a minimalist, keyboard-centric interface.

Inspired by the aesthetics of **Claude Code** and the power of **Bloomberg Terminal**, Sigma provides a distraction-free environment where natural language commands translate instantly into rigorous financial analysis.

### Key Features

- **Elite TUI Experience**: A "Tokyonight" themed interface with zero latency, generative autocomplete, and real-time ticker recognition.
- **Multi-Model Intelligence**: Seamlessly route queries to **OpenAI o1**, **Claude 3.5 Sonnet**, **Gemini 1.5 Pro**, or run locally with **Ollama (Qwen 2.5)**.
- **Institutional Data**: Direct integration with **Polygon.io**, **Alpha Vantage**, and **Exa Search** for hallucination-free market data.
- **Quantitative Backtesting**: Built-in **LEAN Engine** support allows you to generate, test, and refine algorithmic strategies in seconds.
- **Privacy by Design**: All API keys and strategies are stored locally. No cloud dependencies. No data logging.

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Ollama** (Recommended for local intelligence)
- **LEAN CLI** (Auto-installed for backtesting)

### Installation

Sigma features an autonomous **Setup Agent** that configures your environment automatically.

```bash
# 1. Clone the repository
git clone https://github.com/sigma/terminal.git
cd sigma

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch Sigma (Triggers Setup Agent)
python -m sigma
```

The Setup Agent will:

1. Detect your hardware acceleration (Metal/CUDA).
2. Install and pull the optimized local model (`qwen2.5:1.5b`).
3. Configure your API keys securely in `.env`.
4. Initialize the LEAN backtesting engine.

---

## Usage

Sigma is controlled via natural language or slash commands. The interface is designed for flow.

### Market Intelligence

> "Analyze the correlation between NVDA and SMCI over the last 6 months."
> "What are the key risk factors in Apple's latest 10-K?"
> "Visualize the volatility surface for SPY options."

### Strategy Development

> "Backtest a mean-reversion strategy on BTC-USD using 15-minute bars."
> "Optimize parameters for a dual-moving average crossover on TSLA."

### System Control

- `/model <name>` - Switch active LLM (e.g., `/model gpt-4o`)
- `/clear` - Reset context window
- `/quit` - Exit session

---

## Architecture

Sigma is built on a modular, event-driven architecture designed for extensibility.

| Layer | Component | Description |
| :--- | :--- | :--- |
| **Interface** | **Textual TUI** | Async, reactive terminal UI with custom widgets and syntax highlighting. |
| **Intelligence** | **LLM Router** | Dynamically routes queries based on complexity and cost (Local vs. Cloud). |
| **Data** | **Tool Registry** | Type-safe bridge connecting LLMs to 30+ financial data endpoints. |
| **Execution** | **LEAN Engine** | Dockerized backtesting environment for institutional-grade strategy validation. |

---

## Configuration

Configuration is managed via the `.env` file in your home directory (`~/.sigma/config.env`) or project root.

```ini
# Example .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
POLYGON_API_KEY=...
DEFAULT_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
```

---

## Contributing

We welcome contributions from the community! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on how to get started.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Contact

For support or inquiries, please open an issue on GitHub or contact the maintainers at [support@sigma.terminal](mailto:support@sigma.terminal).

<div align="center">
  <sub>Built by the Sigma Team</sub>
</div>
