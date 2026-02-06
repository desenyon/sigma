"""Sigma v3.5.5 - Finance Research Agent."""

import asyncio
from typing import Any, Optional, List, Dict
import re
import time

from rich.markdown import Markdown
from rich.markup import escape
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from rich.console import Group

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal, Container
from textual.screen import Screen
from textual.widgets import Input, RichLog, Static, Footer
from textual.reactive import reactive
from textual.suggester import SuggestFromList

from .config import get_settings
from .core.command_router import CommandRouter, Request
from .llm.router import get_router
from .tools.registry import TOOL_REGISTRY

__version__ = "3.5.5"


SIGMA_ASCII = """
[bold #d97757]  ███████ ██  ██████  ███    ███  █████ [/]
[bold #d97757]  ██      ██ ██       ████  ████ ██   ██[/]
[bold #d97757]  ███████ ██ ██   ███ ██ ████ ██ ███████[/]
[bold #d97757]       ██ ██ ██    ██ ██  ██  ██ ██   ██[/]
[bold #d97757]  ███████ ██  ██████  ██      ██ ██   ██[/]
"""

SIGMA_FRAMES = [
    "[bold #d97757]σ[/]",
    "[bold #e08e79]σ[/]",
    "[bold #f59e0b]σ[/]",
    "[bold #e08e79]σ[/]",
    "[bold #d97757]σ[/]",
    "[#a16145]σ[/]",
]

SUGGESTIONS = [
    "analyze AAPL",
    "analyze NVDA", 
    "quote TSLA",
    "quote AAPL",
    "compare AAPL MSFT GOOGL",
    "technical analysis SPY",
    "market overview",
    "NVDA fundamentals",
]


class SigmaStatus(Static):
    """Animated sigma loading indicator with tool call display."""
    
    DEFAULT_CSS = """
    SigmaStatus {
        height: auto;
        min-height: 2;
        width: 100%;
        background: #111111;
        border-left: tall #d97757;
        padding: 0 1;
        margin: 0 0 1 0;
        display: none;
    }
    SigmaStatus.active {
        display: block;
    }
    """
    
    is_active = reactive(False)
    
    def on_mount(self):
        self.frame = 0
        self.elapsed = 0.0
        self.phase = "Thinking"
        self.tools: List[Dict] = []
        self.set_interval(0.1, self._tick)
        
    def _tick(self):
        if not self.is_active:
            return
            
        self.frame = (self.frame + 1) % len(SIGMA_FRAMES)
        self.elapsed += 0.1
        
        sigma = SIGMA_FRAMES[self.frame]
        secs = f"{self.elapsed:.1f}s"
        
        lines = []
        
        main = Text()
        main.append_text(Text.from_markup(f" {sigma} "))
        main.append(self.phase, "#e4e4e7")
        main.append(f"  [{secs}]", "#52525b")
        lines.append(main)
        
        for tc in self.tools[-3:]:
            line = Text()
            if tc.get("done"):
                line.append("   ", "")
                line.append("done ", "#22c55e")
                line.append(tc["name"], "#a1a1aa")
                if tc.get("result"):
                    line.append(f" = {tc['result']}", "#71717a")
                if tc.get("ms"):
                    line.append(f" ({tc['ms']}ms)", "#3f3f46")
            else:
                line.append("   ", "")
                line.append("running ", "#f59e0b")
                line.append(tc["name"], "#e4e4e7")
            lines.append(line)
        
        self.update(Group(*lines))
                
    def start(self, phase: str = "Thinking"):
        self.is_active = True
        self.elapsed = 0.0
        self.phase = phase
        self.tools = []
        self.add_class("active")
        
    def stop(self):
        self.is_active = False
        self.remove_class("active")
        
    def set_phase(self, phase: str):
        self.phase = phase
        
    def add_tool(self, name: str) -> int:
        idx = len(self.tools)
        self.tools.append({"name": name, "done": False, "start": time.time()})
        self.phase = f"Calling {name}"
        return idx
        
    def finish_tool(self, idx: int, result: Any):
        if idx < len(self.tools):
            tc = self.tools[idx]
            tc["done"] = True
            tc["ms"] = int((time.time() - tc["start"]) * 1000)
            
            if isinstance(result, dict):
                if "price" in result:
                    tc["result"] = f"${result['price']}"
                elif "current_price" in result:
                    tc["result"] = f"${result['current_price']}"
                elif "error" in result:
                    tc["result"] = f"error"
                elif "symbol" in result:
                    tc["result"] = result["symbol"]
            
            self.phase = "Processing"


class ActionBtn(Static):
    """Action button without emojis."""
    
    DEFAULT_CSS = """
    ActionBtn {
        width: auto;
        min-width: 12;
        height: 3;
        background: #1a1a1a;
        color: #a1a1aa;
        border: round #2a2a2a;
        padding: 0 2;
        margin-right: 1;
        content-align: center middle;
    }
    ActionBtn:hover {
        background: #252525;
        color: #e4e4e7;
        border: round #d97757;
    }
    ActionBtn:focus {
        border: round #d97757;
    }
    """
    
    def __init__(self, label: str, cmd: str, **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self.cmd = cmd
        self.can_focus = True
        
    def on_mount(self):
        self.update(f"[bold]{self.label}[/]")
        
    def on_click(self):
        self.post_message(ActionBtn.Clicked(self))
        
    class Clicked:
        def __init__(self, btn): self.btn = btn


class SplashScreen(Screen):
    BINDINGS = [("enter", "go", "Start"), ("space", "go", "Start")]
    DEFAULT_CSS = """
    SplashScreen { background: #0a0a0a; }
    #splash { align: center middle; height: 100%; }
    #tag { color: #71717a; margin: 2; }
    #hint { color: #52525b; }
    """

    def compose(self) -> ComposeResult:
        yield Container(
            Static(Align.center(SIGMA_ASCII), id="art"),
            Static(Align.center(f"v{__version__} | Finance Research Agent"), id="tag"),
            Static(Align.center("Press Enter"), id="hint"),
            id="splash"
        )

    def action_go(self):
        self.app.switch_screen("main")


class MainScreen(Screen):
    BINDINGS = [
        Binding("ctrl+l", "clear", "Clear", show=True),
        Binding("ctrl+b", "trace", "Trace", show=True),
        Binding("ctrl+h", "help", "Help", show=True),
    ]

    DEFAULT_CSS = """
    MainScreen { background: #0a0a0a; }
    
    #main { height: 100%; width: 100%; }
    #chat-area { width: 1fr; height: 100%; padding: 1 2; }
    
    #log {
        width: 100%;
        height: 1fr;
        background: #0a0a0a;
        border: none;
        scrollbar-size: 1 1;
        scrollbar-background: #0a0a0a;
        scrollbar-color: #252525;
    }
    
    #btns { height: 3; width: 100%; margin-bottom: 1; }
    
    #input {
        width: 100%;
        height: 3;
        background: #151515;
        border: round #3a3a3a;
        color: #e4e4e7;
    }
    #input:focus { border: round #d97757; background: #1a1a1a; }
    
    Input > .input--placeholder { color: #52525b; }
    Input > .input--suggestion { color: #6b7280; }
    
    #sidebar {
        width: 50;
        dock: right;
        background: #0f0f0f;
        border-left: tall #1a1a1a;
        display: none;
        padding: 1;
    }
    #sidebar.show { display: block; }
    
    #trace { background: #0f0f0f; height: 1fr; }
    .hdr { color: #52525b; text-align: center; margin-bottom: 1; }
    """

    def compose(self) -> ComposeResult:
        with Horizontal(id="main"):
            with Vertical(id="chat-area"):
                log = RichLog(id="log", wrap=True, markup=True)
                log.can_focus = False
                yield log
                
                yield SigmaStatus(id="status")
                
                with Horizontal(id="btns"):
                    yield ActionBtn("Analyze", "analyze ", id="b1")
                    yield ActionBtn("Quote", "quote ", id="b2")
                    yield ActionBtn("Compare", "compare ", id="b3")
                    yield ActionBtn("Market", "market overview", id="b4")
                
                yield Input(
                    placeholder="Ask Sigma... (try 'quote AAPL')", 
                    id="input",
                    suggester=SuggestFromList(SUGGESTIONS, case_sensitive=False)
                )
            
            with Vertical(id="sidebar"):
                yield Static("Trace", classes="hdr")
                trace = RichLog(id="trace", wrap=True, markup=True)
                trace.can_focus = False
                yield trace
        
        yield Footer()

    def on_mount(self):
        self.query_one("#input").focus()
        self._welcome()
        
    def _welcome(self):
        log = self.query_one("#log", RichLog)
        msg = Text()
        msg.append("σ ", "bold #d97757")
        msg.append("Sigma v3.5.5", "bold")
        msg.append(" ready\n\n", "#71717a")
        msg.append("  Try: ", "#52525b")
        msg.append("quote AAPL", "#22c55e")
        msg.append("   ", "")
        msg.append("analyze NVDA", "#22c55e")
        msg.append("   ", "")
        msg.append("compare AAPL MSFT\n", "#22c55e")
        log.write(Panel(msg, border_style="#2a2a2a"))
        
    @on(ActionBtn.Clicked)
    def on_btn(self, event):
        inp = self.query_one("#input", Input)
        inp.value = event.btn.cmd
        inp.focus()
        
    def action_help(self):
        log = self.query_one("#log", RichLog)
        txt = Text()
        txt.append("Commands\n", "bold")
        txt.append("  quote <SYM>     ", "#d97757")
        txt.append("Current price\n", "#71717a")
        txt.append("  analyze <SYM>   ", "#d97757")
        txt.append("Full analysis\n", "#71717a")
        txt.append("  compare A B     ", "#d97757")
        txt.append("Compare stocks\n", "#71717a")
        log.write(Panel(txt, title="[#d97757]Help[/]", border_style="#2a2a2a"))


class SigmaApp(App):
    CSS = """
    Screen { background: #0a0a0a; color: #e4e4e7; }
    RichLog { scrollbar-background: #0a0a0a; scrollbar-color: #2a2a2a; }
    Footer { background: #0f0f0f; }
    Footer > .footer--key { background: #1a1a1a; color: #d97757; }
    Footer > .footer--description { color: #71717a; }
    """

    SCREENS = {"splash": SplashScreen, "main": MainScreen}

    def on_mount(self):
        self.router = CommandRouter()
        try:
            self.llm = get_router(get_settings())
        except Exception:
            self.llm = None
        self.push_screen("splash")

    @on(Input.Submitted)
    async def on_submit(self, event: Input.Submitted):
        query = event.value.strip()
        if not query:
            return
        
        event.input.value = ""
        
        try:
            log = event.control.screen.query_one("#log", RichLog)
        except:
            return

        display = escape(query)
        try:
            req = self.router.parse(query)
            for t in req.tickers:
                display = re.sub(f"(?i)\\b{re.escape(t)}\\b", f"[bold #22c55e]{t.upper()}[/]", display)
        except:
            pass

        log.write(Text.assemble(("[#d97757]>[/] ", ""), Text.from_markup(display)))
        log.write("")
        
        self._process(query, log)

    @work
    async def _process(self, query: str, log: RichLog):
        trace = None
        try:
            trace = log.screen.query_one("#trace", RichLog)
        except:
            pass
        
        status = None
        try:
            status = log.screen.query_one(SigmaStatus)
            status.start("Parsing query")
        except:
            pass
        
        try:
            req = self.router.parse(query)
            
            if trace:
                trace.write(f"[#52525b]intent:[/] [#3b82f6]{req.action}[/]")
                if req.tickers:
                    trace.write(f"[#52525b]tickers:[/] [#22c55e]{', '.join(req.tickers)}[/]")

            if req.is_command:
                await self._cmd(req, log, trace, status)
            else:
                await self._chat(req, log, trace, status)

        except Exception as e:
            log.write(f"[#ef4444]Error: {e}[/]")
        finally:
            if status:
                status.stop()

    async def _cmd(self, req, log, trace, status):
        if req.action == "backtest":
            if status:
                status.set_phase("Running backtest")
            try:
                sym = req.tickers[0] if req.tickers else "SPY"
                from .backtest import run_backtest
                result = await asyncio.to_thread(run_backtest, sym, "momentum", "1y")
                
                if "error" in result:
                    log.write(f"[#ef4444]{result['error']}[/]")
                else:
                    perf = result.get("performance", {})
                    table = Table(box=None, show_header=False)
                    table.add_column("", style="#71717a")
                    table.add_column("", justify="right")
                    
                    ret = perf.get('total_return', 0)
                    color = "#22c55e" if ret > 0 else "#ef4444"
                    table.add_row("Return", f"[{color}]{ret}[/]")
                    
                    log.write(Panel(table, title=f"[#d97757]{sym}[/]", border_style="#2a2a2a"))
            except Exception as e:
                log.write(f"[#ef4444]{e}[/]")

    async def _chat(self, req, log, trace, status):
        if not self.llm:
            log.write(Panel(
                "[#f59e0b]LLM not configured.[/] Run: sigma --setup",
                border_style="#2a2a2a"
            ))
            return

        if status:
            status.set_phase("Connecting to AI")

        system = """You are Sigma, a financial research assistant.

CRITICAL RULES:
1. ALWAYS use the get_stock_quote tool to get current stock prices - NEVER make up prices
2. Use technical_analysis for RSI, moving averages, etc.
3. Use get_company_info for fundamentals like P/E ratio, market cap
4. Be concise and direct with your answers
5. Include thought_signature parameter in every tool call

When asked about a stock price, ALWAYS call get_stock_quote first."""
        
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": req.original_query}
        ]
        
        tool_idx = {}
        
        async def on_tool(name: str, args: dict):
            if status:
                idx = status.add_tool(name)
                tool_idx[id(args)] = idx
                
            if trace:
                trace.write(f"[#f59e0b]call[/] [#3b82f6]{name}[/]")
            
            start = time.time()
            try:
                result = await TOOL_REGISTRY.execute(name, args)
                ms = int((time.time() - start) * 1000)
                
                if status and id(args) in tool_idx:
                    status.finish_tool(tool_idx[id(args)], result)
                    
                if trace:
                    if isinstance(result, dict) and "price" in result:
                        trace.write(f"  [#22c55e]ok[/] ${result['price']} ({ms}ms)")
                    else:
                        trace.write(f"  [#22c55e]ok[/] ({ms}ms)")
                    
                return result
            except Exception as e:
                if trace:
                    trace.write(f"  [#ef4444]err[/] {str(e)[:25]}")
                raise
        
        try:
            if status:
                status.set_phase("Waiting for response")
                
            stream = await self.llm.chat(
                messages,
                tools=TOOL_REGISTRY.to_llm_format(),
                on_tool_call=on_tool
            )
            
            if isinstance(stream, str):
                log.write(Panel(Markdown(stream), border_style="#2a2a2a"))
            else:
                acc = ""
                async for chunk in stream:
                    acc += chunk
                if acc:
                    log.write(Panel(Markdown(acc), border_style="#2a2a2a"))
                    
        except Exception as e:
            log.write(f"[#ef4444]LLM Error: {e}[/]")

    def action_trace(self):
        try:
            sb = self.query_one("#sidebar")
            sb.set_class(not sb.has_class("show"), "show")
        except:
            pass
            
    def action_clear(self):
        try:
            log = self.screen.query_one("#log", RichLog)
            log.clear()
            log.write("[#d97757]σ[/] Cleared.")
        except:
            pass


def launch():
    SigmaApp().run()
