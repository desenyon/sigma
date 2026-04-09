"""Ephemeral v3.8.0 - Finance Research Agent."""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from rich.console import RenderableType
from rich.markdown import Markdown
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.events import Click
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Label, Static
from textual.widgets import Markdown as TuiMarkdown

# Import tools to ensure registration
from .cli_ui import format_tui_status_markdown
from .config import (
    AVAILABLE_MODELS,
    LLMProvider,
    detect_lean_installation,
    detect_ollama,
    get_settings,
    list_ollama_model_names,
    needs_llm_setup,
)
from .core.engine import AutocompleteEngine, Engine
from .llm.router import get_router
from .llm.tool_guidance import USER_TOOL_NUDGE, build_augmented_system_prompt
from .tools.registry import TOOL_REGISTRY, filter_args_for_tool
from .ui.motion import SPINNER_BRAILE
from .ui.widgets import EphemeralInput, EphemeralLoader, TickerBadge
from .utils.formatting import format_tool_result
from .utils.ticker_highlight import enhance_markdown_tickers, rich_text_user_line
from .version import VERSION


def format_setup_instructions() -> str:
    """Human-readable setup steps for the gate panel."""
    settings = get_settings()
    if settings.default_provider != LLMProvider.OLLAMA:
        p = settings.default_provider.value
        return (
            f"Default provider is '{p}' but no API key is set.\n\n"
            f"  ephemeral --setkey {p} <your-key>\n\n"
            "Or switch to local Ollama:\n\n"
            "  ephemeral --provider ollama\n"
            "  ollama pull qwen3.5:8b"
        )
    ok, host = detect_ollama()
    if not ok:
        return (
            "Ollama is not reachable (is it running?).\n\n"
            "  ollama serve\n\n"
            "Then press Retry."
        )
    model = (settings.default_model or "").strip()
    names = list_ollama_model_names(host or "")
    if not names:
        return (
            "Ollama is up but no models are installed.\n\n"
            f"  ollama pull {model or 'qwen3.5:8b'}\n\n"
            "Then press Retry."
        )
    return (
        f"Your default model is '{model}' but it is not installed locally.\n\n"
        f"Installed: {', '.join(names[:10])}"
        + (" …" if len(names) > 10 else "")
        + "\n\n"
        f"  ollama pull {model}\n\n"
        "Or set DEFAULT_MODEL to an installed name, then Retry."
    )


class SetupGate(Vertical):
    """Shown first when the default LLM cannot run."""

    def __init__(self) -> None:
        super().__init__(id="setup-gate")

    DEFAULT_CSS = """
    SetupGate {
        height: auto;
        margin: 1 0;
        padding: 1 2;
        background: #16161e;
        border: tall #7aa2f7;
    }
    #setup-title {
        text-style: bold;
        color: #7aa2f7;
        margin-bottom: 1;
    }
    #setup-body-text {
        color: #a9b1d6;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("Setup required", id="setup-title")
        yield Static("", id="setup-body-text")
        with Horizontal():
            yield Button("Retry", id="btn-setup-retry", variant="primary")
            yield Button("Continue anyway", id="btn-setup-dismiss")

    def on_mount(self) -> None:
        self.query_one("#setup-body-text", Static).update(format_setup_instructions())

__version__ = VERSION

SYSTEM_PROMPT = """You are Ephemeral, a senior financial research copilot (terminal UI). Your job is to
reduce confusion: always ground claims in tools, cite what you fetched, and explain *why* something
matters to a portfolio or thesis.

## Behavior
- Lead with the answer, then evidence. Use Markdown: short sections, bullets, tables when comparing.
- When the user names tickers, call tools early (quotes, `fetch_news_digest`, fundamentals) before
  long prose. Prefer `fetch_news_digest` for “why is X moving”, headlines, and catalyst context.
- After tool results: synthesize (do not dump raw JSON). Quote numbers with units and timestamps.
- If data is missing or APIs error, say so once and suggest what key or action fixes it.
- Multi-step reasoning: note assumptions, risks, and what would change your view.
- Stay professional; no fabricated prices, filings, or URLs. If unsure, verify with tools or say you cannot.

## Output shape (flexible)
1) **Take** — one tight paragraph.
2) **Evidence** — facts from tools (with source implied by tool name).
3) **Risks / second-order** — what could invalidate the view.
4) **Next** — concrete follow-ups (metrics, charts, scenarios).

## Tools
Use the registered tools liberally. For news and narrative context, prefer **fetch_news_digest**
(symbol + optional query). Use price/quote tools for levels; use fundamentals/risk tools when the user
asks valuation, quality, or drawdowns.

## Parallel tool use (critical)
- You may issue **multiple tool calls in a single turn**. APIs support parallel calls—use them.
- For a single ticker “what’s going on / thesis”: combine **quote + news digest + (fundamentals or risk)**
  when relevant—do not stop after one tool unless the user asked a single narrow fact.
- For **comparisons** (A vs B): use **compare_stocks** and/or separate quotes for each name, plus news or
  valuation tools as needed—cover every symbol mentioned.
- For **macro + names**: use `get_market_overview` / `get_sector_performance` / `get_economic_indicators`
  alongside ticker-level tools when the prompt mixes both.
- Prefer **breadth over speed**: an extra tool that contradicts or refines the thesis is worth calling.

Tone: precise, institutional, but readable. Avoid filler. Use headings sparingly."""

WELCOME_BANNER = (
    f"### Ephemeral `v{__version__}`\n\n"
    "**Research terminal** — type a question, **`/` commands**, or ask for quotes, news, and backtests.\n\n"
    "_Tip: tickers like **AAPL** or **$NVDA** highlight in chat. Tab completes `/` commands._"
)

SUGGESTIONS = [
    "Analyze AAPL fundamentals vs peers",
    "Compare MSFT and GOOGL revenue growth over 5 years",
    "Backtest a dual momentum strategy on SPY",
    "Summarize key risks from the latest NVDA 10-K",
    "Plot realized volatility for QQQ over the last year",
    "What is the sector rotation picture this quarter?",
    "Run technical_analysis on TSLA for 6mo",
    "Get polygon news flow for AMD limit 15",
    "Explain the yield curve and implications for banks",
    "Stress-test a 60/40 portfolio for a 20% equity drawdown",
    "Compare Sharpe ratios for MAG7 vs equal-weight S&P",
    "Screen for high short interest large-caps",
    "Draft a trade thesis for uranium miners",
    "Summarize Fed communications impact on duration risk",
    "Fetch market overview and highlight breadth",
    "Analyze correlation between gold and real yields",
    "Backtest RSI mean reversion on ETH-USD",
    "Compare dividend safety for KO vs PEP",
    "What are catalysts for SMCI next earnings?",
    "Build a pairs-trading hypothesis for XLK vs XLF",
    "Audit data quality for a backtest on IWM",
    "Generate a memo outline for a long/short consumer book",
    "List macro indicators to watch for recession risk",
    "Compare credit spreads vs VIX regime",
    "Explain options skew for SPY weeklies",
    "Summarize insider activity for a mid-cap name",
]

class ChatMessage(Static):
    """Base class for chat messages."""
    pass

class UserMessage(ChatMessage):
    """A message from the user."""

    def __init__(self, content: str, **kwargs):
        cls = kwargs.pop("classes", "")
        merged = f"msg-user {cls}".strip()
        super().__init__(classes=merged, **kwargs)
        self.content = content

    def render(self) -> RenderableType:
        head = Text("You ", style="bold #89dceb")
        return head + rich_text_user_line(self.content)

class ToolMessage(ChatMessage):
    """A message representing a tool call."""

    status = reactive("Running...")
    result = reactive("")

    def __init__(self, tool_name: str, **kwargs):
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.start_time = time.time()
        self.finished = False
        self._spin_timer = None
        self._spin_i = 0

    def on_mount(self) -> None:
        self._spin_timer = self.set_interval(0.1, self._advance_spin)

    def _advance_spin(self) -> None:
        if self.finished:
            if self._spin_timer is not None:
                self._spin_timer.stop()
                self._spin_timer = None
            return
        self._spin_i = (self._spin_i + 1) % len(SPINNER_BRAILE)
        self.refresh()

    def render(self) -> RenderableType:
        if not self.finished:
            fr = SPINNER_BRAILE[self._spin_i % len(SPINNER_BRAILE)]
            t = Text()
            t.append(f"  {fr} ", style="bold #89dceb")
            t.append(self.tool_name, style="bold #cba6f7")
            t.append("  ·  running…", style="dim #6c7086")
            return t

        status_color = "#9ece6a" if "Error" not in self.status else "#f7768e"
        status_text = "[OK]" if "Error" not in self.status else "[ERR]"

        text = Text()
        text.append(f"  {status_text} ", style=status_color)
        text.append(f"{self.tool_name} ", style="bold #7aa2f7")

        duration = time.time() - self.start_time
        text.append(f"({duration:.2f}s)", style="dim")

        if self.result is not None and str(self.result).strip():
            display_result = str(self.result).strip()
            # Clean up newlines for compact display
            display_result = display_result.replace("\n", " ")
            if len(display_result) > 100:
                display_result = display_result[:100] + "..."
            text.append(f" -> {display_result}", style="italic #565f89")

        return text

    def complete(self, result: Any, error: bool = False):
        self.finished = True
        if self._spin_timer is not None:
            self._spin_timer.stop()
            self._spin_timer = None
        self.result = result
        self.status = "Error" if error else "Completed"
        if error:
            self.add_class("error")
        else:
            self.add_class("completed")
        self.refresh()

class AssistantMessage(ChatMessage):
    """A message from the assistant.

    Do not use ``content`` as a reactive name — it shadows ``Static.content`` and breaks rendering.
    """

    stream_text = reactive("")

    def __init__(self, **kwargs):
        cls = kwargs.pop("classes", "")
        merged = f"msg-assistant {cls}".strip()
        super().__init__("", classes=merged, **kwargs)
        self._replace_on_first_chunk = False

    def watch_stream_text(self, _old: str, new: str) -> None:
        """Push markdown into Static via ``update()`` so the TUI actually paints it."""
        if not new:
            self.update(Text("", end=""))
            return
        self.update(Markdown(enhance_markdown_tickers(new)))

    def append(self, chunk: str) -> None:
        if self._replace_on_first_chunk:
            if not chunk:
                return
            self._replace_on_first_chunk = False
            self.stream_text = chunk
            return
        self.stream_text += chunk

    def set_text(self, text: str) -> None:
        """Replace full content (slash commands, non-streaming replies)."""
        self._replace_on_first_chunk = False
        self.stream_text = text

class EphemeralApp(App):
    """The main Ephemeral TUI application."""

    TITLE = "Ephemeral"
    SUB_TITLE = "Finance"
    # Default "*" focuses the first focusable node in the tree — often inside Markdown/chat.
    AUTO_FOCUS = "#composer"

    CSS = """
    Screen {
        background: #0b0d12;
        color: #cdd6f4;
    }

    #app-chrome {
        dock: top;
        height: 1;
        layout: horizontal;
        padding: 0 2;
        background: #0f111a;
        color: #89dceb;
        text-style: bold;
        border-bottom: tall #313244;
    }

    #app-chrome-title {
        width: 1fr;
        height: 1;
    }

    #loader {
        width: 18;
        height: 1;
        min-width: 18;
        max-width: 22;
        overflow: hidden;
        background: transparent;
        border: none;
        padding: 0 1;
        color: #7aa2f7;
        text-align: right;
        content-align: right middle;
    }

    #chat-view {
        height: 1fr;
        overflow-y: auto;
        padding: 1 3;
        scrollbar-gutter: stable;
        background: #0b0d12;
    }

    #input-area {
        height: auto;
        dock: bottom;
        background: #08090e;
        padding: 0 2 1 2;
        border-top: tall #313244;
        layout: vertical;
    }

    #slash-completions {
        display: none;
        height: auto;
        max-height: 14;
        margin-bottom: 1;
        padding: 1 2;
        background: #11111b;
        border: round #45475a;
        color: #bac2de;
    }

    #input-hints {
        color: #45475a;
        height: 1;
        margin-top: 0;
        margin-bottom: 1;
        text-style: italic;
    }

    #input-bar {
        /* Do not pin height: 1 — ScrollView-based Input clips/glitches when squeezed */
        height: auto;
        min-height: 1;
        layout: horizontal;
        align: center middle;
        padding: 0 1;
        background: #181825;
        border: round #45475a;
    }

    #input-bar EphemeralInput {
        background: #181825;
        border: none;
        min-height: 1;
        height: auto;
        min-width: 10;
        width: 1fr;
        scrollbar-size-horizontal: 0;
        color: #cdd6f4;
        overflow: hidden;
    }

    #input-bar EphemeralInput:focus {
        background-tint: #ffffff 8%;
    }

    #prompt-char {
        color: #89b4fa;
        margin-right: 1;
        text-style: bold;
    }

    EphemeralInput {
        width: 1fr;
        background: transparent;
        border: none;
        color: #cdd6f4;
        scrollbar-size-horizontal: 0;
    }
    EphemeralInput:focus {
        border: none;
    }

    .msg-user {
        margin: 1 0;
        padding: 0 1 0 2;
        border-left: outer #89dceb;
        background: #101018;
    }

    ToolMessage {
        margin: 0 0 0 2;
        padding: 0 1;
        color: #7f849c;
        background: #0f1018;
        border-left: outer #45475a;
    }

    ToolMessage.completed {
        border-left: outer #94e2d5;
    }

    ToolMessage.error {
        border-left: outer #f38ba8;
    }

    .msg-assistant {
        margin: 1 0 2 0;
        padding: 1 2;
        background: #12121c;
        border: round #45475a;
        color: #cdd6f4;
    }

    .welcome-message {
        text-align: center;
        color: #7f849c;
        margin: 2 2;
        padding: 2;
        border: round #45475a;
        background: #101018;
    }

    #suggestion-label {
        color: #6c7086;
        padding: 0 2;
        margin-bottom: 0;
        text-style: italic;
        display: none;
    }

    SetupGate {
        background: #11111b;
        border: round #89b4fa;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear_chat", "Clear"),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal(id="app-chrome"):
            yield Static(
                f" Ephemeral  ·  Research  ·  v{__version__} ",
                id="app-chrome-title",
            )
            yield EphemeralLoader(id="loader")

        # Scroll area must not take keyboard focus (typing goes to #composer). See AUTO_FOCUS.
        yield VerticalScroll(id="chat-view", can_focus=False)

        with Container(id="input-area"):
            yield Static("", id="slash-completions")
            yield Label("", id="suggestion-label")
            yield Label(
                " Tab complete · / for commands · Ctrl+L clear · Ctrl+C quit ",
                id="input-hints",
            )
            with Horizontal(id="input-bar"):
                yield Label(">", id="prompt-char")
                yield EphemeralInput(
                    id="composer",
                    placeholder="Message Ephemeral — natural language, or type / for commands…",
                )
                yield TickerBadge(id="ticker-badge")

    @staticmethod
    def _parse_slash_query(query: str) -> tuple[str, str]:
        rest = query.strip()
        if not rest.startswith("/"):
            return "", ""
        i = rest.find(" ")
        if i == -1:
            return rest.lower(), ""
        return rest[:i].lower(), rest[i + 1 :].strip()

    def _gather_chat_markdown(self) -> str:
        chat_view = self.query_one("#chat-view")
        parts: List[str] = ["# Ephemeral export\n"]
        for w in chat_view.children:
            if isinstance(w, UserMessage):
                parts.append(f"\n## You\n\n{w.content}\n")
            elif isinstance(w, AssistantMessage):
                c = (w.stream_text or "").strip()
                if c:
                    parts.append(f"\n## Assistant\n\n{c}\n")
            elif isinstance(w, ToolMessage):
                r = str(w.result).strip() if w.result is not None else ""
                if r and len(r) < 8000:
                    parts.append(f"\n### Tool `{w.tool_name}`\n\n```\n{r}\n```\n")
                elif r:
                    parts.append(f"\n### Tool `{w.tool_name}`\n\n```\n{r[:8000]}…\n```\n")
        return "".join(parts)

    async def run_slash_response(self, query: str, assistant_msg: AssistantMessage) -> None:
        cmd, arg = self._parse_slash_query(query)
        settings = get_settings()
        text = ""
        try:
            if cmd in ("/", ""):
                text = (
                    "Type a command after `/` — for example `/help` or `/status`. "
                    "Use **Up** / **Down** to move the menu and **Tab** to insert."
                )
            elif cmd == "/help":
                lines = ["## Commands", ""]
                for c in sorted(AutocompleteEngine.COMMANDS):
                    lines.append(f"- `{c}` — {AutocompleteEngine.get_command_help(c)}")
                text = "\n".join(lines)
            elif cmd == "/status":
                text = format_tui_status_markdown(
                    settings,
                    detect_ollama=detect_ollama,
                    detect_lean_installation=detect_lean_installation,
                )
            elif cmd == "/keys":
                key_rows = [
                    ("Google", settings.google_api_key),
                    ("OpenAI", settings.openai_api_key),
                    ("Anthropic", settings.anthropic_api_key),
                    ("Groq", settings.groq_api_key),
                    ("xAI", settings.xai_api_key),
                    ("Polygon", getattr(settings, "polygon_api_key", None)),
                    ("Alpha Vantage", getattr(settings, "alpha_vantage_api_key", None)),
                    ("Exa", getattr(settings, "exa_api_key", None)),
                ]
                lines = ["## API keys", "", "| Provider | Status |", "| --- | --- |"]
                for label, val in key_rows:
                    lines.append(f"| {label} | {'set' if val else '—'} |")
                text = "\n".join(lines)
            elif cmd == "/models":
                lines: List[str] = ["## Reference models", ""]
                for prov, models in AVAILABLE_MODELS.items():
                    lines.append(f"### {prov}")
                    for m in models:
                        lines.append(f"- `{m}`")
                    lines.append("")
                text = "\n".join(lines)
            elif cmd == "/provider":
                p = (
                    settings.default_provider.value
                    if hasattr(settings.default_provider, "value")
                    else str(settings.default_provider)
                )
                text = f"**Active provider:** `{p}`\n\nCLI: `ephemeral --provider <google|openai|…>`"
            elif cmd == "/model":
                text = f"**Default model:** `{settings.default_model}`"
                if arg:
                    text += f"\n\n*(You typed:* `{arg}`*)*"
                text += "\n\nCLI: `ephemeral --model <id>`"
            elif cmd == "/backtest":
                lines = ["## Strategy ids (examples)", ""]
                for s in AutocompleteEngine.STRATEGIES:
                    lines.append(f"- `{s}`")
                text = "\n".join(lines)
            elif cmd == "/tools":
                names = sorted(TOOL_REGISTRY.get_tool_names())
                lines = [f"## Registered tools ({len(names)})", ""]
                for n in names:
                    lines.append(f"- `{n}`")
                text = "\n".join(lines)
            elif cmd == "/export":
                body = self._gather_chat_markdown()
                out = Path.home() / ".ephemeral" / "exports"
                out.mkdir(parents=True, exist_ok=True)
                fn = out / f"ephemeral-chat-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
                fn.write_text(body, encoding="utf-8")
                text = f"Wrote **{fn}** ({len(body)} characters)."
            elif cmd == "/shortcuts":
                text = (
                    "## Keyboard shortcuts\n\n"
                    "| Key | Action |\n"
                    "| --- | --- |\n"
                    "| **Tab** | Accept ghost text or insert selected `/` command |\n"
                    "| **↑ / ↓** | Move in the slash menu |\n"
                    "| **Enter** | Send message or run `/` command |\n"
                    "| **Ctrl+L** | Clear chat transcript |\n"
                    "| **Ctrl+C** | Quit |\n\n"
                    "Tickers like `AAPL` or `$NVDA` are highlighted. The badge by the input shows "
                    "the latest symbol while you type.\n"
                )
            elif cmd == "/setup-help":
                text = (
                    "## Setup\n\n"
                    "1. Copy `.env.example` to `~/.ephemeral/config.env` and fill keys.\n"
                    "2. `ephemeral --setkey openai <key>` (or `google`, `anthropic`, `polygon`, …).\n"
                    "3. `ephemeral --provider openai` and `ephemeral --model <id>`.\n"
                    "4. Run `/status` or `ephemeral --status` to verify.\n\n"
                    "Docs: https://github.com/desenyon/ephemeral#readme\n"
                )
            elif cmd == "/reload":
                self.router = get_router(get_settings(), force=True)
                text = "Reloaded the LLM router from environment and `~/.ephemeral/config.env`."
            elif cmd in ("/news", "/digest"):
                parts = arg.split()
                sym = ""
                lim = 10
                for p in parts:
                    if p.isdigit():
                        lim = max(1, min(25, int(p)))
                    elif not sym:
                        sym = p.upper().strip(".,;:")
                if not sym:
                    text = (
                        "**Usage:** `/news AAPL` or `/news NVDA 15` (headline limit).\n\n"
                        "Feeds try **Polygon**, **Alpha Vantage**, **Exa**, then **Yahoo** — "
                        "configure keys for the best coverage."
                    )
                else:
                    from ephemeral.tools.library import fetch_news_digest

                    r = fetch_news_digest(symbol=sym, limit=lim)
                    if r.get("error"):
                        text = f"## News `{sym}`\n\n{r.get('error')}\n\n{r.get('setup_hint', '')}"
                    else:
                        lines = [
                            f"## Headlines — `{sym}`",
                            f"_Source: {r.get('source_used', '?')}_",
                            "",
                        ]
                        for article in (r.get("articles") or [])[:20]:
                            title = (article.get("title") or "")[:220]
                            summ = (article.get("summary") or article.get("description") or "")[:320]
                            lines.append(f"- **{title}**")
                            if summ:
                                lines.append(f"  _{summ}_")
                        text = "\n".join(lines)
            elif cmd == "/quote":
                parts = arg.split()
                sym = parts[0].upper().strip(".,;:") if parts else ""
                if not sym:
                    text = "**Usage:** `/quote MSFT`"
                else:
                    from ephemeral.tools.library import get_stock_quote

                    q = get_stock_quote(sym)
                    text = f"## Quote `{sym}`\n\n```json\n{json.dumps(q, indent=2)[:8000]}\n```"
            elif cmd in AutocompleteEngine.COMMANDS:
                tip = AutocompleteEngine.get_command_help(cmd)
                text = f"### {cmd}\n\n{tip}\n\nUse natural language in this chat, or the `ephemeral` CLI for one-shots (`ephemeral quote`, `ephemeral chart`, `ephemeral news`, …)."
            else:
                text = f"Unknown command `{cmd}`. Try `/help`."
        except Exception as e:
            text = f"**Error:** {e}"
        assistant_msg.set_text(text)

    def _focus_input(self) -> None:
        """Keep the composer focused — chat/Markdown must not steal the keyboard."""
        try:
            inp = self.query_one("#composer", EphemeralInput)
            if not inp.disabled:
                inp.focus()
        except Exception:
            pass

    @staticmethod
    def _widget_has_ancestor_button(widget: Widget | None) -> bool:
        w: Widget | None = widget
        while isinstance(w, Widget):
            if isinstance(w, Button):
                return True
            w = w.parent
        return False

    def on_mount(self) -> None:
        self._conversation_history: List[Dict[str, str]] = []
        self.engine = Engine()
        self.router = get_router(get_settings())
        asyncio.create_task(self._bootstrap_chat())
        self.call_after_refresh(self._focus_input)

    async def _bootstrap_chat(self) -> None:
        chat_view = self.query_one("#chat-view")
        settings = get_settings()
        if needs_llm_setup(settings):
            await chat_view.mount(SetupGate())
            self.query_one("#composer", EphemeralInput).disabled = True
        else:
            await chat_view.mount(TuiMarkdown(WELCOME_BANNER, classes="welcome-message"))
            self.call_after_refresh(self._focus_input)

    async def _dismiss_setup_gate(self) -> None:
        gate = self.query_one("#setup-gate")
        await gate.remove()
        chat_view = self.query_one("#chat-view")
        await chat_view.mount(TuiMarkdown(WELCOME_BANNER, classes="welcome-message"))
        self.query_one("#composer", EphemeralInput).disabled = False
        self.router = get_router(get_settings(), force=True)
        self.call_after_refresh(self._focus_input)

    @on(Click, "#input-area")
    def on_click_input_area(self, event: Click) -> None:
        self._focus_input()

    @on(Click, "#chat-view")
    def on_click_chat_view(self, event: Click) -> None:
        """Markdown / links can take focus on click; return the keyboard to the composer."""
        if self._widget_has_ancestor_button(event.control):
            return
        self._focus_input()

    @on(Button.Pressed, "#btn-setup-retry")
    async def on_setup_retry(self, event: Button.Pressed) -> None:
        try:
            body = self.query_one("#setup-body-text", Static)
            body.update(format_setup_instructions())
        except Exception:
            pass
        if not needs_llm_setup(get_settings()):
            await self._dismiss_setup_gate()

    @on(Button.Pressed, "#btn-setup-dismiss")
    async def on_setup_dismiss(self, event: Button.Pressed) -> None:
        await self._dismiss_setup_gate()

    async def on_input_submitted(self, event: EphemeralInput.Submitted):
        query = event.value.strip()
        if not query:
            return

        event.input.value = ""
        chat_view = self.query_one("#chat-view")

        first = query.split(maxsplit=1)[0].lower()
        if first == "/clear":
            self.action_clear_chat()
            return

        await chat_view.mount(UserMessage(query))

        if query.startswith("/"):
            assistant_msg = AssistantMessage()
            await chat_view.mount(assistant_msg)
            self.query_one("#loader").add_class("active")
            try:
                await self.run_slash_response(query, assistant_msg)
            finally:
                self.query_one("#loader").remove_class("active")
                chat_view.scroll_end()
                self.call_after_refresh(self._focus_input)
            return

        assistant_msg = AssistantMessage()
        assistant_msg._replace_on_first_chunk = True
        await chat_view.mount(assistant_msg)
        assistant_msg.stream_text = "> _Ephemeral is reasoning (tools may run above)..._\n\n"
        self.query_one("#loader").add_class("active")
        self.process_query(query, assistant_msg)

    @work
    async def process_query(self, query: str, message_widget: AssistantMessage):
        chat_view = self.query_one("#chat-view")

        try:
            # Tool Execution Callback
            async def on_tool_call(name: str, args: dict):
                # 1. Mount Tool Message (@work runs on the app asyncio loop — do not use call_from_thread)
                tool_msg = ToolMessage(name)
                await chat_view.mount(tool_msg)
                chat_view.scroll_end()

                # 2. Execute Tool
                try:
                    tool_def = TOOL_REGISTRY.get_tool(name)
                    if not tool_def:
                        result = {"error": f"Tool {name} not found"}
                    else:
                        clean = filter_args_for_tool(tool_def.func, args or {})
                        if asyncio.iscoroutinefunction(tool_def.func):
                            result = await tool_def.func(**clean)
                        else:
                            result = await asyncio.to_thread(tool_def.func, **clean)

                except Exception as e:
                    result = {"error": str(e)}

                # 3. Update UI
                formatted = format_tool_result(result)
                tool_err = isinstance(result, dict) and "error" in result
                tool_msg.complete(formatted, error=tool_err)

                return result

            # Parse Intent
            try:
                await self.engine.intent_parser.parse(query)
                # We don't show the plan explicitly in the new minimalist UI unless debug mode
            except Exception:
                pass

            settings = get_settings()
            system_prompt = build_augmented_system_prompt(SYSTEM_PROMPT, TOOL_REGISTRY)
            user_content = query
            if getattr(settings, "ephemeral_aggressive_tools", True):
                user_content = query + USER_TOOL_NUDGE
            messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
            messages.extend(self._conversation_history)
            messages.append({"role": "user", "content": user_content})
            tools = TOOL_REGISTRY.to_llm_format()

            response_stream = await self.router.chat(
                messages=messages,
                stream=True,
                tools=tools,
                on_tool_call=on_tool_call
            )

            collected: List[str] = []
            if hasattr(response_stream, "__aiter__"):
                async for chunk in response_stream:
                    message_widget.append(chunk)
                    collected.append(chunk)
                    chat_view.scroll_end()
            else:
                text = str(response_stream)
                message_widget.append(text)
                collected.append(text)

            assistant_body = "".join(collected).strip()
            if assistant_body:
                self._conversation_history.append({"role": "user", "content": query})
                self._conversation_history.append({"role": "assistant", "content": assistant_body})
                while len(self._conversation_history) > 24:
                    self._conversation_history.pop(0)

        except Exception as e:
            message_widget.append(f"\n\n**Error:** {str(e)}")

        finally:
            self.query_one("#loader").remove_class("active")
            chat_view.scroll_end()
            self.call_after_refresh(self._focus_input)

    def action_clear_chat(self) -> None:
        self._conversation_history = []
        self.query_one("#chat-view").remove_children()
        asyncio.create_task(self._after_clear_chat())

    async def _after_clear_chat(self) -> None:
        settings = get_settings()
        chat_view = self.query_one("#chat-view")
        if needs_llm_setup(settings):
            await chat_view.mount(SetupGate())
            self.query_one("#composer", EphemeralInput).disabled = True
        else:
            await chat_view.mount(TuiMarkdown(WELCOME_BANNER, classes="welcome-message"))
            self.query_one("#composer", EphemeralInput).disabled = False
        self.call_after_refresh(self._focus_input)

def launch():
    app = EphemeralApp()
    app.run()

if __name__ == "__main__":
    launch()
