"""Sigma v3.5.0 - Finance Research Agent."""

import asyncio
from datetime import datetime
from typing import Any, Optional

import re  # Added top-level import

from rich.markdown import Markdown
from rich.markup import escape
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.align import Align

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal, Container
from textual.screen import Screen
from textual.widgets import Input, RichLog, Label, Static, LoadingIndicator
from textual.reactive import reactive
from textual.suggester import SuggestFromList

from .config import get_settings
from .core.command_router import CommandRouter, Request
from .llm.router import get_router
from .tools.registry import TOOL_REGISTRY

__version__ = "3.5.0"

# -----------------------------------------------------------------------------
# CONSTANTS & ASSETS
# -----------------------------------------------------------------------------

SIGMA_ASCII = """
[#d97757]  ██████  ██[/]  [#e08e79]██████  ███    ███  █████ [/]
[#d97757]  ██      ██[/] [#e08e79]██       ████  ████ ██   ██[/]
[#d97757]  ███████ ██[/] [#e08e79]██   ███ ██ ████ ██ ███████[/]
[#d97757]       ██ ██[/] [#e08e79]██    ██ ██  ██  ██ ██   ██[/]
[#d97757]  ██████  ██[/] [#e08e79] ██████  ██      ██ ██   ██[/]
"""

SUGGESTIONS = [
    "analyze", "backtest", "compare", "chart", "quote",
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META",
    "strategy", "momentum", "mean_reversion"
]


# -----------------------------------------------------------------------------
# SCREENS
# -----------------------------------------------------------------------------

class ThinkingStatus(Static):
    """Animated thinking indicator like Claude Code."""
    
    DEFAULT_CSS = """
    ThinkingStatus {
        height: 1;
        width: 100%;
        color: #a1a1aa;
        display: none;
        padding-left: 2;
    }
    ThinkingStatus.visible {
        display: block;
    }
    """
    
    def on_mount(self):
        self.loading = False
        self.frame = 0
        self.frames = ["σ", "o", "O", "0", "O", "o"]
        self.set_interval(0.1, self.animate)
        
    def animate(self):
        if self.loading:
            self.frame = (self.frame + 1) % len(self.frames)
            # symbol = self.frames[self.frame]
            # Just pulse the sigma
            if self.frame < 3:
                self.update(Text("σ", style="bold #d97757") + " Analysis in progress...")
            else:
                self.update(Text("σ", style="dim #d97757") + " Analysis in progress...")
                
    def start(self):
        self.loading = True
        self.add_class("visible")
        
    def stop(self):
        self.loading = False
        self.remove_class("visible")


class SplashScreen(Screen):

    BINDINGS = [("enter", "start_app", "Start")]

    def compose(self) -> ComposeResult:
        yield Container(
            Static(Panel(Align.center("[#e4e4e7]Welcome to Sigma[/]"), border_style="#d97757", padding=(0, 2)), id="welcome-badge"),
            Static(Align.center(SIGMA_ASCII), id="ascii-art"),
            Label("Press Enter to continue", id="press-enter"),
            id="splash-container"
        )

    def action_start_app(self):
        self.app.switch_screen("main")


class MainScreen(Screen):
    """Main chat interface."""
    
    BINDINGS = [
        Binding("ctrl+l", "clear_chat", "Clear"),
        Binding("ctrl+b", "toggle_sidebar", "Sidebar"),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal():
            # Main Chat Area
            with Vertical(id="chat-area"):
                # Use a specific class or check if can_focus can be disabled here for RichLog
                # In Textual, RichLog is focusable by default. We disable it to prevent it stealing focus from Input.
                log = RichLog(id="chat-log", wrap=True, highlight=True, markup=True)
                log.can_focus = False
                yield log
                yield ThinkingStatus(id="thinking")
                yield Input(
                    placeholder="Ask Sigma...", 
                    id="prompt",
                    suggester=SuggestFromList(SUGGESTIONS, case_sensitive=False)
                )
            
            # Sidebar (Hidden by default)
            with Vertical(id="sidebar"):
                yield Label("TRACE", classes="sidebar-header")
                tracelog = RichLog(id="trace-log", wrap=True, highlight=True, markup=True)
                tracelog.can_focus = False
                yield tracelog

    def on_mount(self):
        self.query_one("#prompt").focus()
        # Initial greeting
        self.query_one("#chat-log", RichLog).write(
            Text.assemble(
                ("σ ", "bold #d97757"),
                ("Sigma initialized. ", "bold #e4e4e7"),
                ("Ready for research.", "dim #a1a1aa")
            )
        )


# -----------------------------------------------------------------------------
# MAIN APPLICATION
# -----------------------------------------------------------------------------

class SigmaApp(App):
    CSS = """
    /* --- COLOR PALETTE (Claude Code Dark) --- */
    $bg: #0f0f0f;       /* Very dark grey/black */
    $surface: #1a1a1a;  /* Slightly lighter surface */
    $text: #e4e4e7;     /* Off-white */
    $dim: #a1a1aa;      /* Muted text */
    $accent: #d97757;   /* Claude-like Orange/Peach */
    $blue: #3b82f6;     /* Link/Action Blue */

    Screen {
        background: $bg;
        color: $text;
    }

    /* --- SPLASH SCREEN --- */
    #splash-container {
        align: center middle;
        height: 100%;
    }

    #welcome-badge {
        width: auto;
        margin-bottom: 2;
        background: $bg;
    }
    
    #ascii-art {
        margin-bottom: 4;
        color: $accent;
    }

    #press-enter {
        color: $dim;
        text-style: bold;
    }

    /* --- MAIN CHAT LAYOUT --- */
    #chat-area {
        width: 1fr;
        height: 100%;
        padding: 1 2;
    }

    #chat-log {
        width: 100%;
        height: 1fr;
        background: $bg;
        border: none;
        margin-bottom: 1;
    }

    Input {
        width: 100%;
        height: 3;
        background: $surface;
        border: solid $dim;
        color: $text;
        padding: 0 1; 
    }
    
    Input:focus {
        border: solid $accent;
        background: $surface;
    }
    
    Input .suggestion {
        color: $dim;
    }

    /* --- SIDEBAR --- */
    #sidebar {
        width: 40;
        dock: right;
        background: $surface;
        border-left: solid $dim 20%;
        display: none;
    }

    #sidebar.visible {
        display: block;
    }

    .sidebar-header {
        background: $surface;
        color: $dim;
        text-align: center;
        text-style: bold;
        padding: 1;
        border-bottom: solid $dim 20%;
    }
    
    #trace-log {
        background: $surface;
        padding: 1;
    }
    """

    SCREENS = {
        "splash": SplashScreen,
        "main": MainScreen
    }

    def on_mount(self):
        # Initialize Core Logic
        self.router = CommandRouter()
        try:
            self.llm_router = get_router(get_settings())
        except Exception:
            self.llm_router = None
            
        self.push_screen("splash")

    @on(Input.Submitted)
    async def on_input(self, event: Input.Submitted):
        query = event.value
        if not query.strip(): return
        
        # Clear input
        event.input.value = ""
        
        # Get chat log - relative to the screen containing the input
        # This fixes the issue where self.query_one fails on App or wrong screen
        try:
            chat_log = event.control.screen.query_one("#chat-log", RichLog)
        except Exception as e:
            self.notify(f"UI Error: Could not find chat log on active screen. {e}", severity="error")
            return

        # Prepare display text
        display_query = escape(query)
        
        # Highlight tickers
        try:
            req = self.router.parse(query)
            for ticker in req.tickers:
                escaped_ticker = re.escape(ticker)
                # Apply green highlight
                display_query = re.sub(
                    f"(?i)\\b{escaped_ticker}\\b", 
                    f"[bold #22c55e]{ticker.upper()}[/]", 
                    display_query
                )
        except Exception:
            pass

        # Write to log
        try:
            chat_log.write(
                Text.assemble(
                    ("❯ ", "bold #d97757"),
                    Text.from_markup(display_query)
                )
            )
            chat_log.write("") # Add spacing
        except Exception as e:
            self.notify(f"Display Error: {e}", severity="error")
            chat_log.write(f"❯ {query}")
        
        # Pass the specific chat_log instance to the worker to avoid re-querying failure
        self.run_query(query, chat_log)

    @work
    async def run_query(self, query: str, chat_log: RichLog):
        # Trace log logic simplified
        trace_log = None
        try:
             # Try to find trace log on the same screen as chat_log
             trace_log = chat_log.screen.query_one("#trace-log", RichLog)
        except:
             pass
        
        # UI Animation: Thinking
        try:
            thinker = chat_log.screen.query_one(ThinkingStatus)
            thinker.start()
        except:
            thinker = None
        
        try:
            req = self.router.parse(query)
            if trace_log:
                trace_log.write(f"[dim]Action:[/dim] {req.action}")

            if req.is_command:
                await self.handle_command(req, chat_log, trace_log)
            else:
                await self.handle_chat(req, chat_log, trace_log)

        except Exception as e:
            chat_log.write(f"[red]Error: {e}[/red]")
            
        finally:
            if thinker:
                thinker.stop()

    async def handle_command(self, req: Request, chat_log: RichLog, trace_log: Optional[RichLog]):
        if req.action == "backtest":
            chat_log.write("[dim]Running backtest...[/dim]")
            try:
                 symbol = req.tickers[0] if req.tickers else "SPY"
                 strategy = req.details.get("strategy") or "momentum"
                 from .backtest import run_backtest
                 
                 result = await asyncio.to_thread(run_backtest, symbol, strategy, "1y")
                 
                 if "error" in result:
                     chat_log.write(f"[red]Failed: {result['error']}[/red]")
                 else:
                     perf = result.get("performance", {})
                     # Minimalist Table
                     table = Table(box=None, show_header=False, padding=(0, 2))
                     table.add_row("[bold]Return[/]", f"[green]{perf.get('total_return')}[/]")
                     table.add_row("[bold]Sharpe[/]", f"{result.get('risk', {}).get('sharpe_ratio')}")
                     table.add_row("[bold]Equity[/]", f"{perf.get('final_equity')}")
                     
                     chat_log.write(Panel(table, title=f"Backtest: {symbol}", border_style="#d97757"))
            except Exception as e:
                chat_log.write(f"[red]{e}[/red]")

    async def handle_chat(self, req: Request, chat_log: RichLog, trace_log: Optional[RichLog]):
        if not self.llm_router:
            chat_log.write("[red]Setup required.[/red]")
            return

        chat_log.write("") # break
        
        # System prompt to enforce thought signatures for Hack Club/Gemini compatibility
        system_prompt = (
            "You are Sigma, an advanced financial research assistant. "
            "You are powered by various LLMs and have access to real-time financial tools. "
            "You MUST use available tools for any question regarding stock prices, financials, market news, or analysis. "
            "Never hallucinate financial data. Always fetch it using the provided tools. "
            "CRITICAL INSTRUCTION: When calling any tool, you MUST provide the 'thought_signature' parameter. "
            "This parameter should contain your internal reasoning for why you are calling that specific tool. "
            "Do not output the thought signature in your final response, only use it in the tool call. "
            "Format your final response in clean Markdown."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": req.original_query}
        ]
        
        try:
            stream = await self.llm_router.chat(
                messages,
                tools=TOOL_REGISTRY.to_llm_format(),
                on_tool_call=self.mk_tool_callback(trace_log)
            )
            
            if isinstance(stream, str):
                chat_log.write(Markdown(stream))
            else:
                acc = ""
                async for chunk in stream:
                    acc += chunk
                chat_log.write(Markdown(acc))
                
        except Exception as e:
            chat_log.write(f"[red]LLM Error: {e}[/red]")

    def mk_tool_callback(self, trace_log: Optional[RichLog]):
        async def callback(name: str, args: dict):
            if trace_log:
                trace_log.write(f"[yellow]➜ {name}[/yellow]")
            try:
                res = await TOOL_REGISTRY.execute(name, args)
                if trace_log:
                    trace_log.write(f"[green]✔[/green]")
                return res
            except Exception as e:
                if trace_log:
                    trace_log.write(f"[red]✖ {e}[/red]")
                raise
        return callback

    def action_toggle_sidebar(self):
        try:
            sidebar = self.query_one("#sidebar")
            sidebar.set_class(not sidebar.has_class("visible"), "visible")
        except:
            pass

def launch():
    app = SigmaApp()
    app.run()
