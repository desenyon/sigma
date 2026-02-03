# Copilot Instructions for Sigma

This guide helps AI agents explore, understand, and contribute to the Sigma codebase efficiently.

## 🏗 Global Architecture & Core Components

Sigma is a terminal-based financial research agent built with Python, Textual, and multiple AI providers.

### Key Components

- **Core Engine (`sigma/core/engine.py`)**: The brain of the application. It orchestrates the entire lifecycle of a user query:
    - **Intent Parsing**: Determines what the user wants (via `IntentParser`).
    - **Decisiveness**: Handles vague queries (via `DecisivenessEngine`).
    - **Execution**: Coordinates tool usage and LLM responses.
- **UI & Interaction (`sigma/app.py`)**: A Textual application (`App`) that manages the TUI.
    - Handles user input, markdown rendering (`rich`), and command loop.
    - Includes custom widgets like `RichLog`, `Input`, and `Footer`.
- **Tool System (`sigma/tools.py`)**: Collection of financial data functions.
    - Wraps `yfinance` for stock data (quotes, history, financials).
    - Functions return simple dicts or pandas objects, processed for the generic LLM context.
- **LLM Abstraction (`sigma/llm.py`)**: Unified interface for providers like OpenAI, Anthropic, Gemini, Groq, and Ollama.
- **Data Models (`sigma/core/models.py`)**: Pydantic models used for structured data exchange (e.g., `ResearchPlan`, `Alert`, `BacktestResult`).

### Data Flow

1.  **User Input**: Captured in `sigma/app.py` via Textual `Input` widget.
2.  **Engine Processing**: `SigmaEngine.process_query()` receives the input string.
3.  **Intent Analysis**: The intent is parsed into a `ResearchPlan`.
4.  **Execution**: The engine calls necessary tools defined in `sigma/tools.py`.
5.  **LLM Generation**: Context + tool outputs are sent to the LLM via `sigma/llm.py`.
6.  **Rendering**: The response is streamed back to the UI log in `sigma/app.py`.

## 🛠 Developer Workflows

### Running & Building

- **Run Locally**:
    ```bash
    # Run as module
    python -m sigma
    ```
- **Build Distribution**:
    - Use the helper script: `scripts/build.sh`
    - This cleans `dist/`, installs build tools, and runs `python -m build`.

### Dependencies

- **Management**: Defined in `pyproject.toml`.
- **Key Libraries**: `textual` (UI), `rich` (formatting), `yfinance` (data), `openai`/`anthropic`/etc (AI).

### Testing

*(Verify specific test runner, likely `pytest` based on standard python structure)*
- Run tests: `pytest tests/`

## 🧩 Project Conventions & Patterns

### Asynchronous Design
- **Core Logic**: The engine and UI event handlers are heavily asynchronous (`async def`).
- **Pattern**: Use `await` for LLM calls and potentially long-running data fetches to keep the TUI responsive.

### Type Safety
- **Strict Typing**: Use Python type hints everywhere (`typing.List`, `typing.Dict`, `typing.Optional`).
- **Models**: Prefer passing Pydantic objects over raw dictionaries within the `core` logic.

### UI Rendering
- **Rich Integration**: Use `rich` for formatting text, tables, and markdown before displaying in Textual widgets.
- **Animation**: See `SIGMA_FRAMES` in `sigma/app.py` for branding animations.
- **Color Coding**: Helper functions like `format_return` and `format_price_change` in `app.py` strictly define color semantics (Green `#22c55e` for positive, Red `#ef4444` for negative).

### Error Handling
- **Custom Errors**: Use `SigmaError` and `ErrorCode` (from `sigma/config.py`) for specific application failures.
- **Graceful Degradation**: Tools catch exceptions and return error dictionaries `{"error": "message"}` rather than crashing the app.

## 🔌 Integration Points

### AI Providers
- **Adding a Provider**: Update `sigma/config.py` to add to `AVAILABLE_MODELS` and implementing the wrapper in `sigma/llm.py`.
- **API Keys**: Stored in `~/.sigma/` (via `save_api_key`).

### Financial Data
- **Source**: Primarily `yfinance`.
- **Extension**: Add new data functions in `sigma/tools.py` and register them in `sigma/tools.py`'s `TOOLS` list or equivalent registry so the LLM knows about them.
