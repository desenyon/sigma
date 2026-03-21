"""Sigma v3.7.0 - Finance Research Agent."""

import asyncio
import time
from pathlib import Path
from typing import Any, List, Dict, Optional
from datetime import datetime

from rich.markdown import Markdown
from rich.text import Text
from rich.console import RenderableType
from rich.style import Style
from rich.syntax import Syntax

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll, Container
from textual.widget import Widget
from textual.widgets import Static, Label, Button, Markdown as TuiMarkdown
from textual.binding import Binding
from textual.reactive import reactive
from textual.message import Message
from textual.events import Click, Key

from .config import (
    AVAILABLE_MODELS,
    LLMProvider,
    detect_lean_installation,
    detect_ollama,
    get_settings,
    list_ollama_model_names,
    needs_llm_setup,
)
from .cli_ui import format_tui_status_markdown
from .llm.router import get_router, LLMRouter
from .tools.registry import TOOL_REGISTRY, filter_args_for_tool
# Import tools to ensure registration
import sigma.tools.local_backtest
import sigma.tools.backtest
import sigma.tools.alpha_vantage
import sigma.tools.exa_search
import sigma.tools.polygon
from .core.engine import AutocompleteEngine, Engine

from .ui.widgets import SigmaInput, SigmaLoader, TickerBadge


def format_setup_instructions() -> str:
    """Human-readable setup steps for the gate panel."""
    settings = get_settings()
    if settings.default_provider != LLMProvider.OLLAMA:
        p = settings.default_provider.value
        return (
            f"Default provider is '{p}' but no API key is set.\n\n"
            f"  sigma --setkey {p} <your-key>\n\n"
            "Or switch to local Ollama:\n\n"
            "  sigma --provider ollama\n"
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

__version__ = "3.7.0"

SYSTEM_PROMPT = """You are Sigma, an elite financial research assistant.
Your goal is to provide accurate, data-driven, and comprehensive financial analysis.

GUIDELINES:
- Be proactive: anticipate follow-up questions and surface risks.
- Be actionable: tie evidence to clear next steps and scenarios.
- Use tools for real market data; stay data-driven in every section.
- You may state a recommendation stance when justified (e.g. STRONG BUY / HOLD / STRONG SELL) and calibrate it to the evidence.
- Be concise. Use Markdown.
"""

WELCOME_BANNER = (
    f"**Sigma** `v{__version__}` · Finance research terminal\n\n"
    "Try natural language, **`/` commands**, or tool-backed questions (quotes, backtests, news)."
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
        t = Text()
        t.append("You ", style="bold #89b4fa")
        t.append(self.content, style="bold #cdd6f4")
        return t

class ToolMessage(ChatMessage):
    """A message representing a tool call."""
    
    status = reactive("Running...")
    result = reactive("")
    
    def __init__(self, tool_name: str, **kwargs):
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.start_time = time.time()
        self.finished = False

    def render(self) -> RenderableType:
        # Minimalist tool output
        if not self.finished:
            return Text(f"  [RUN] {self.tool_name}...", style="dim #565f89")
        
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

    def watch_stream_text(self, _old: str, new: str) -> None:
        """Push markdown into Static via ``update()`` so the TUI actually paints it."""
        if not new:
            self.update(Text("", end=""))
            return
        self.update(Markdown(new))

    def append(self, chunk: str) -> None:
        self.stream_text += chunk

    def set_text(self, text: str) -> None:
        """Replace full content (slash commands, non-streaming replies)."""
        self.stream_text = text

from .utils.formatting import format_tool_result

class SigmaApp(App):
    """The main Sigma TUI application."""

    TITLE = "Sigma"
    SUB_TITLE = "Finance"
    # Default "*" focuses the first focusable node in the tree — often inside Markdown/chat.
    AUTO_FOCUS = "#composer"

    CSS = """
    Screen {
        background: #0d0f18;
        color: #cdd6f4;
    }

    #app-chrome {
        dock: top;
        height: 1;
        layout: horizontal;
        padding: 0 2;
        background: #11111b;
        color: #89b4fa;
        text-style: bold;
        border-bottom: tall #313244;
    }

    #app-chrome-title {
        width: 1fr;
        height: 1;
    }

    #loader {
        width: 4;
        height: 1;
        min-width: 4;
        max-width: 4;
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
        background: #0d0f18;
    }

    #input-area {
        height: auto;
        dock: bottom;
        background: #0c0d14;
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

    #input-bar SigmaInput {
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

    #input-bar SigmaInput:focus {
        background-tint: #ffffff 8%;
    }

    #prompt-char {
        color: #89b4fa;
        margin-right: 1;
        text-style: bold;
    }

    SigmaInput {
        width: 1fr;
        background: transparent;
        border: none;
        color: #cdd6f4;
        scrollbar-size-horizontal: 0;
    }
    SigmaInput:focus {
        border: none;
    }

    .msg-user {
        margin: 1 0;
        padding: 0 1 0 2;
        border-left: outer #89b4fa;
        background: #11111b;
    }

    ToolMessage {
        margin: 0 0 0 2;
        padding: 0 1;
        color: #6c7086;
    }

    .msg-assistant {
        margin: 1 0 2 0;
        padding: 1 2;
        background: #11111b;
        border: round #313244;
        color: #cdd6f4;
    }

    .welcome-message {
        text-align: center;
        color: #6c7086;
        margin: 3 2;
        padding: 2;
        border: round #313244;
        background: #11111b;
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
                f" Sigma  ·  Research  ·  v{__version__} ",
                id="app-chrome-title",
            )
            yield SigmaLoader(id="loader")

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
                yield SigmaInput(
                    id="composer",
                    placeholder="Message Sigma — natural language, or type / for commands…",
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
        parts: List[str] = ["# Sigma export\n"]
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
                text = f"**Active provider:** `{p}`\n\nCLI: `sigma --provider <google|openai|…>`"
            elif cmd == "/model":
                text = f"**Default model:** `{settings.default_model}`"
                if arg:
                    text += f"\n\n*(You typed:* `{arg}`*)*"
                text += "\n\nCLI: `sigma --model <id>`"
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
                out = Path.home() / ".sigma" / "exports"
                out.mkdir(parents=True, exist_ok=True)
                fn = out / f"sigma-chat-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
                fn.write_text(body, encoding="utf-8")
                text = f"Wrote **{fn}** ({len(body)} characters)."
            elif cmd in AutocompleteEngine.COMMANDS:
                tip = AutocompleteEngine.get_command_help(cmd)
                text = f"### {cmd}\n\n{tip}\n\nUse natural language in this chat, or the `sigma` CLI for one-shots (`sigma quote`, `sigma chart`, …)."
            else:
                text = f"Unknown command `{cmd}`. Try `/help`."
        except Exception as e:
            text = f"**Error:** {e}"
        assistant_msg.set_text(text)

    def _focus_input(self) -> None:
        """Keep the composer focused — chat/Markdown must not steal the keyboard."""
        try:
            inp = self.query_one("#composer", SigmaInput)
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
        self.engine = Engine()
        self.router = get_router(get_settings())
        asyncio.create_task(self._bootstrap_chat())
        self.call_after_refresh(self._focus_input)

    async def _bootstrap_chat(self) -> None:
        chat_view = self.query_one("#chat-view")
        settings = get_settings()
        if needs_llm_setup(settings):
            await chat_view.mount(SetupGate())
            self.query_one("#composer", SigmaInput).disabled = True
        else:
            await chat_view.mount(TuiMarkdown(WELCOME_BANNER, classes="welcome-message"))
            self.call_after_refresh(self._focus_input)

    async def _dismiss_setup_gate(self) -> None:
        gate = self.query_one("#setup-gate")
        await gate.remove()
        chat_view = self.query_one("#chat-view")
        await chat_view.mount(TuiMarkdown(WELCOME_BANNER, classes="welcome-message"))
        self.query_one("#composer", SigmaInput).disabled = False
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

    async def on_input_submitted(self, event: SigmaInput.Submitted):
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
        await chat_view.mount(assistant_msg)
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
                plan = await self.engine.intent_parser.parse(query)
                # We don't show the plan explicitly in the new minimalist UI unless debug mode
            except Exception as e:
                pass

            system_prompt = SYSTEM_PROMPT
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            tools = TOOL_REGISTRY.to_llm_format()
            
            response_stream = await self.router.chat(
                messages=messages,
                stream=True,
                tools=tools,
                on_tool_call=on_tool_call
            )
            
            if hasattr(response_stream, "__aiter__"):
                async for chunk in response_stream:
                    message_widget.append(chunk)
                    chat_view.scroll_end()
            else:
                message_widget.append(str(response_stream))

        except Exception as e:
            message_widget.append(f"\n\n**Error:** {str(e)}")

        finally:
            self.query_one("#loader").remove_class("active")
            chat_view.scroll_end()
            self.call_after_refresh(self._focus_input)

    def action_clear_chat(self) -> None:
        self.query_one("#chat-view").remove_children()
        asyncio.create_task(self._after_clear_chat())

    async def _after_clear_chat(self) -> None:
        settings = get_settings()
        chat_view = self.query_one("#chat-view")
        if needs_llm_setup(settings):
            await chat_view.mount(SetupGate())
            self.query_one("#composer", SigmaInput).disabled = True
        else:
            await chat_view.mount(TuiMarkdown(WELCOME_BANNER, classes="welcome-message"))
            self.query_one("#composer", SigmaInput).disabled = False
        self.call_after_refresh(self._focus_input)

def launch():
    app = SigmaApp()
    app.run()

if __name__ == "__main__":
    launch()
