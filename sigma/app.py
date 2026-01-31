"""Sigma v3.3.0 - Finance Research Agent."""

import asyncio
import os
import re
from datetime import datetime
from typing import Optional, List

from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Footer, Input, RichLog, Static
from textual.suggester import Suggester

from .config import LLMProvider, get_settings, save_api_key, AVAILABLE_MODELS
from .llm import get_llm
from .tools import TOOLS, execute_tool
from .backtest import run_backtest, get_available_strategies, BACKTEST_TOOL


__version__ = "3.3.0"
SIGMA = "σ"

# Common stock tickers for recognition
COMMON_TICKERS = {
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "BRK.A", "BRK.B",
    "JPM", "JNJ", "V", "PG", "UNH", "HD", "MA", "DIS", "PYPL", "BAC", "ADBE", "NFLX",
    "CRM", "INTC", "AMD", "CSCO", "PEP", "KO", "ABT", "NKE", "MRK", "PFE", "TMO",
    "COST", "AVGO", "WMT", "ACN", "LLY", "MCD", "DHR", "TXN", "NEE", "PM", "HON",
    "UPS", "BMY", "QCOM", "LOW", "MS", "RTX", "UNP", "ORCL", "IBM", "GE", "CAT",
    "SBUX", "AMAT", "GS", "BLK", "DE", "AMT", "NOW", "ISRG", "LMT", "MDLZ", "AXP",
    "SYK", "BKNG", "PLD", "GILD", "ADI", "TMUS", "CVS", "MMC", "ZTS", "CB", "C",
    "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO", "VXX", "ARKK", "XLF", "XLK", "XLE",
}

# Small sigma animation frames (minimal footprint)
SMALL_SIGMA_FRAMES = [
    "[bold blue]σ[/bold blue]",
    "[bold cyan]σ[/bold cyan]",
    "[bold white]σ[/bold white]",
    "[bold #60a5fa]σ[/bold #60a5fa]",
]

# Tool call animation frames
TOOL_CALL_FRAMES = [
    "⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"
]

# Welcome banner - clean design
WELCOME_BANNER = """
[bold blue]███████╗██╗ ██████╗ ███╗   ███╗ █████╗ [/bold blue]
[bold blue]██╔════╝██║██╔════╝ ████╗ ████║██╔══██╗[/bold blue]
[bold blue]███████╗██║██║  ███╗██╔████╔██║███████║[/bold blue]
[bold blue]╚════██║██║██║   ██║██║╚██╔╝██║██╔══██║[/bold blue]
[bold blue]███████║██║╚██████╔╝██║ ╚═╝ ██║██║  ██║[/bold blue]
[bold blue]╚══════╝╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝[/bold blue]

[bold cyan]Finance Research Agent[/bold cyan]  [dim]v3.3.0 | Native macOS[/dim]
"""

SYSTEM_PROMPT = """You are Sigma, a Finance Research Agent. You provide comprehensive market analysis, trading strategies, and investment insights.

CORE CAPABILITIES:
- Real-time market data analysis (quotes, charts, technicals)
- Fundamental analysis (financials, ratios, earnings)
- Technical analysis (RSI, MACD, Bollinger Bands, moving averages)
- Backtesting strategies (SMA crossover, RSI, MACD, Bollinger, momentum, breakout)
- Portfolio analysis and optimization
- Sector and market overview
- Insider and fund activity tracking

RESPONSE STYLE:
- Be concise and data-driven
- Lead with key insights, then supporting data
- Use tables for comparative data when appropriate
- Always cite specific numbers and metrics
- Provide actionable recommendations when asked
- Format currency and percentages properly
- Use STRONG BUY, BUY, HOLD, SELL, STRONG SELL ratings when appropriate

When users ask about stocks, always gather current data using your tools before responding."""

# Enhanced autocomplete suggestions with more variety
SUGGESTIONS = [
    # Analysis commands
    "analyze AAPL",
    "analyze MSFT", 
    "analyze GOOGL",
    "analyze NVDA",
    "analyze TSLA",
    "analyze META",
    "analyze AMZN",
    "analyze AMD",
    "analyze SPY",
    # Comparisons
    "compare AAPL MSFT GOOGL",
    "compare NVDA AMD INTC",
    "compare META GOOGL AMZN",
    "compare TSLA RIVN LCID",
    # Technical
    "technical analysis of AAPL",
    "technical analysis of SPY",
    "technical analysis of NVDA",
    "technical analysis of QQQ",
    # Backtesting
    "backtest SMA crossover on AAPL",
    "backtest RSI strategy on SPY",
    "backtest MACD on NVDA",
    "backtest momentum on QQQ",
    # Market
    "market overview",
    "sector performance",
    "what sectors are hot today",
    # Quotes
    "get quote for AAPL",
    "price of NVDA",
    "how is TSLA doing",
    # Fundamentals
    "fundamentals of MSFT",
    "financials for AAPL",
    "earnings of NVDA",
    # Activity
    "insider trading for AAPL",
    "institutional holders of NVDA",
    "analyst recommendations for TSLA",
    # Natural language queries
    "what should I know about AAPL",
    "is NVDA overvalued",
    "best tech stocks right now",
    "should I buy TSLA",
    # Commands
    "/help",
    "/clear",
    "/keys",
    "/models",
    "/status",
    "/backtest",
]


def extract_tickers(text: str) -> List[str]:
    """Extract stock tickers from text."""
    # Look for common patterns: $AAPL, or standalone uppercase words
    # Only match if it's a known ticker or starts with $
    words = text.upper().split()
    tickers = []
    
    for word in words:
        # Clean the word
        clean = word.strip('.,!?()[]{}":;')
        
        # Check for $TICKER format
        if clean.startswith('$'):
            ticker = clean[1:]
            if ticker and ticker.isalpha() and len(ticker) <= 5:
                tickers.append(ticker)
        # Check if it's a known ticker
        elif clean in COMMON_TICKERS:
            tickers.append(clean)
    
    return list(dict.fromkeys(tickers))  # Dedupe while preserving order


class SigmaSuggester(Suggester):
    """Enhanced autocomplete suggester with ticker recognition."""
    
    def __init__(self):
        super().__init__(use_cache=True, case_sensitive=False)
    
    async def get_suggestion(self, value: str) -> Optional[str]:
        """Get autocomplete suggestion."""
        if not value or len(value) < 2:
            return None
        
        value_lower = value.lower()
        
        # Check for ticker pattern (all caps or starts with $)
        if value.startswith("$") or value.isupper():
            ticker = value.lstrip("$").upper()
            for common in COMMON_TICKERS:
                if common.startswith(ticker) and common != ticker:
                    return f"analyze {common}"
        
        # Standard suggestions
        for suggestion in SUGGESTIONS:
            if suggestion.lower().startswith(value_lower):
                return suggestion
        
        # Try partial match in middle of suggestion
        for suggestion in SUGGESTIONS:
            if value_lower in suggestion.lower():
                return suggestion
        
        return None


CSS = """
Screen {
    background: #0a0a0f;
}

* {
    scrollbar-size: 1 1;
    scrollbar-color: #3b82f6 30%;
    scrollbar-color-hover: #60a5fa 50%;
    scrollbar-color-active: #93c5fd 70%;
}

#main-container {
    width: 100%;
    height: 100%;
    background: #0a0a0f;
}

#chat-area {
    height: 1fr;
    margin: 1 2;
    background: #0a0a0f;
}

#chat-log {
    background: #0a0a0f;
    padding: 1 0;
}

#status-bar {
    height: 3;
    background: #0d1117;
    border-top: solid #1a1a2e;
    padding: 0 2;
    dock: bottom;
}

#status-content {
    width: 100%;
    height: 100%;
    content-align: left middle;
}

#thinking-indicator {
    width: auto;
    height: 1;
    content-align: center middle;
    display: none;
}

#thinking-indicator.visible {
    display: block;
}

#tool-calls-display {
    width: 100%;
    height: auto;
    max-height: 6;
    background: #0d1117;
    border: solid #1a1a2e;
    margin: 0 2;
    padding: 0 1;
    display: none;
}

#tool-calls-display.visible {
    display: block;
}

#input-area {
    height: 5;
    padding: 1 2;
    background: #0d1117;
}

#input-row {
    height: 3;
    width: 100%;
}

#sigma-indicator {
    width: 4;
    height: 3;
    content-align: center middle;
}

#prompt-input {
    width: 1fr;
    background: #1a1a2e;
    border: solid #3b82f6;
    color: #ffffff;
    padding: 0 1;
}

#prompt-input:focus {
    border: solid #60a5fa;
}

#prompt-input.-autocomplete {
    border: solid #22c55e;
}

#ticker-highlight {
    width: auto;
    height: 1;
    padding: 0 1;
    background: transparent;
}

Footer {
    background: #0d1117;
    height: 1;
    dock: bottom;
}

Footer > .footer--highlight {
    background: transparent;
}

Footer > .footer--key {
    background: #1a1a2e;
    color: #f59e0b;
    text-style: bold;
}

Footer > .footer--description {
    color: #6b7280;
}

#help-panel {
    width: 100%;
    height: auto;
    padding: 1;
    background: #0d1117;
    border: solid #3b82f6;
    margin: 1 2;
    display: none;
}

#help-panel.visible {
    display: block;
}
"""


class ToolCallDisplay(Static):
    """Animated display for tool calls."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tool_calls: List[dict] = []
        self.frame = 0
        self.timer = None
    
    def add_tool_call(self, name: str, status: str = "running"):
        """Add a tool call to the display."""
        self.tool_calls.append({"name": name, "status": status, "frame": 0})
        self.add_class("visible")
        self._render()
        if not self.timer:
            self.timer = self.set_interval(0.1, self._animate)
    
    def complete_tool_call(self, name: str):
        """Mark a tool call as complete."""
        for tc in self.tool_calls:
            if tc["name"] == name and tc["status"] == "running":
                tc["status"] = "complete"
                break
        self._render()
    
    def clear(self):
        """Clear all tool calls."""
        self.tool_calls = []
        if self.timer:
            self.timer.stop()
            self.timer = None
        self.remove_class("visible")
        self.update("")
    
    def _animate(self):
        """Animate the spinner."""
        self.frame = (self.frame + 1) % len(TOOL_CALL_FRAMES)
        for tc in self.tool_calls:
            if tc["status"] == "running":
                tc["frame"] = self.frame
        self._render()
    
    def _render(self):
        """Render the tool calls display."""
        if not self.tool_calls:
            return
        
        lines = []
        for tc in self.tool_calls:
            if tc["status"] == "running":
                spinner = TOOL_CALL_FRAMES[tc["frame"]]
                lines.append(f"  [cyan]{spinner}[/cyan] [bold]{tc['name']}[/bold] [dim]executing...[/dim]")
            else:
                lines.append(f"  [green]✓[/green] [bold]{tc['name']}[/bold] [green]complete[/green]")
        
        self.update(Text.from_markup("\n".join(lines)))


class SigmaIndicator(Static):
    """Pulsing sigma indicator with minimal footprint."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = False
        self.frame = 0
        self.timer = None
    
    def on_mount(self):
        self.update(Text.from_markup(f"[bold blue]{SIGMA}[/bold blue]"))
    
    def set_active(self, active: bool):
        self.active = active
        if active and not self.timer:
            self.timer = self.set_interval(0.15, self._pulse)
        elif not active and self.timer:
            self.timer.stop()
            self.timer = None
            self.update(Text.from_markup(f"[bold blue]{SIGMA}[/bold blue]"))
    
    def _pulse(self):
        self.frame = (self.frame + 1) % len(SMALL_SIGMA_FRAMES)
        self.update(Text.from_markup(SMALL_SIGMA_FRAMES[self.frame]))


class TickerHighlight(Static):
    """Display detected tickers in real-time."""
    
    def update_tickers(self, text: str):
        """Update displayed tickers based on input."""
        tickers = extract_tickers(text)
        if tickers:
            ticker_text = " ".join([f"[cyan]${t}[/cyan]" for t in tickers[:3]])
            self.update(Text.from_markup(ticker_text))
        else:
            self.update("")


class ChatLog(RichLog):
    """Chat log with rich formatting."""
    
    def write_user(self, message: str):
        # Highlight any tickers in user message
        highlighted = message
        for ticker in extract_tickers(message):
            highlighted = re.sub(
                rf'\b{ticker}\b',
                f'[cyan]{ticker}[/cyan]',
                highlighted,
                flags=re.IGNORECASE
            )
        
        self.write(Panel(
            Text.from_markup(highlighted) if '[cyan]' in highlighted else Text(message, style="white"),
            title="[bold blue]You[/bold blue]",
            border_style="blue",
            padding=(0, 1),
        ))
    
    def write_assistant(self, message: str):
        self.write(Panel(
            Markdown(message),
            title=f"[bold cyan]{SIGMA} Sigma[/bold cyan]",
            border_style="cyan",
            padding=(0, 1),
        ))
    
    def write_tool(self, tool_name: str):
        # This is now handled by ToolCallDisplay
        pass
    
    def write_error(self, message: str):
        self.write(Panel(Text(message, style="red"), title="[red]Error[/red]", border_style="red"))
    
    def write_system(self, message: str):
        self.write(Text.from_markup(f"[dim]{message}[/dim]"))
    
    def write_welcome(self):
        self.write(Text.from_markup(WELCOME_BANNER))


class SigmaApp(App):
    """Sigma Finance Research Agent."""
    
    TITLE = "Sigma"
    CSS = CSS
    
    BINDINGS = [
        Binding("ctrl+l", "clear", "Clear"),
        Binding("ctrl+m", "models", "Models"),
        Binding("ctrl+h", "help_toggle", "Help"),
        Binding("ctrl+p", "palette", "palette", show=True),
        Binding("escape", "cancel", show=False),
    ]
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.llm = None
        self.conversation = []
        self.is_processing = False
        self.history: List[str] = []
        self.history_idx = -1
        self.show_help = False
    
    def compose(self) -> ComposeResult:
        yield Container(
            ScrollableContainer(
                ChatLog(id="chat-log", highlight=True, markup=True),
                id="chat-area",
            ),
            ToolCallDisplay(id="tool-calls-display"),
            Static(id="help-panel"),
            Container(
                Horizontal(
                    SigmaIndicator(id="sigma-indicator"),
                    Input(
                        placeholder="Ask about any stock, market, or strategy... (Tab to autocomplete)",
                        id="prompt-input",
                        suggester=SigmaSuggester(),
                    ),
                    TickerHighlight(id="ticker-highlight"),
                    id="input-row",
                ),
                id="input-area",
            ),
            id="main-container",
        )
        yield Footer()
    
    def on_mount(self):
        chat = self.query_one("#chat-log", ChatLog)
        chat.write_welcome()
        
        provider = getattr(self.settings.default_provider, 'value', str(self.settings.default_provider))
        chat.write_system(f"{SIGMA} Provider: {provider} | Model: {self.settings.default_model}")
        chat.write_system(f"{SIGMA} Type /help for commands • Ctrl+H for quick help • Tab to autocomplete")
        chat.write_system("")
        
        self._init_llm()
        self.query_one("#prompt-input", Input).focus()
    
    def _init_llm(self):
        try:
            self.llm = get_llm(self.settings.default_provider, self.settings.default_model)
        except Exception as e:
            chat = self.query_one("#chat-log", ChatLog)
            chat.write_error(f"LLM init failed: {e}")
            chat.write_system("Use /keys to configure API keys")
    
    @on(Input.Changed)
    def on_input_change(self, event: Input.Changed):
        """Update ticker highlight as user types."""
        ticker_display = self.query_one("#ticker-highlight", TickerHighlight)
        ticker_display.update_tickers(event.value)
    
    @on(Input.Submitted)
    def handle_input(self, event: Input.Submitted):
        if self.is_processing:
            return
        
        text = event.value.strip()
        if not text:
            return
        
        self.query_one("#prompt-input", Input).value = ""
        self.history.append(text)
        self.history_idx = len(self.history)
        
        chat = self.query_one("#chat-log", ChatLog)
        
        if text.startswith("/"):
            self._handle_command(text, chat)
        else:
            chat.write_user(text)
            self._process_query(text, chat)
    
    def _handle_command(self, cmd: str, chat: ChatLog):
        parts = cmd.lower().split()
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        if command == "/help":
            self._show_comprehensive_help(chat)
        elif command == "/clear":
            chat.clear()
            self.conversation = []
            chat.write_system("Chat cleared")
        elif command == "/keys":
            self._show_keys(chat)
        elif command == "/models":
            self._show_models(chat)
        elif command == "/status":
            self._show_status(chat)
        elif command == "/backtest":
            self._show_strategies(chat)
        elif command == "/provider" and args:
            self._switch_provider(args[0], chat)
        elif command == "/model" and args:
            self._switch_model(args[0], chat)
        elif command.startswith("/setkey") and len(parts) >= 3:
            self._set_key(parts[1], parts[2], chat)
        elif command == "/tickers":
            self._show_popular_tickers(chat)
        else:
            chat.write_error(f"Unknown command: {command}. Type /help for available commands.")
    
    def _show_comprehensive_help(self, chat: ChatLog):
        """Show comprehensive help with examples."""
        help_text = f"""
[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]
[bold]                    {SIGMA} SIGMA HELP CENTER                      [/bold]
[bold cyan]═══════════════════════════════════════════════════════════════[/bold cyan]

[bold yellow]QUICK START[/bold yellow]
  Just type naturally! Examples:
  • "analyze AAPL"           - Full analysis of Apple
  • "compare NVDA AMD INTC"  - Compare multiple stocks
  • "is TSLA overvalued?"    - Get AI insights
  • "market overview"        - See major indices

[bold yellow]COMMANDS[/bold yellow]
  [cyan]/help[/cyan]              This help screen
  [cyan]/clear[/cyan]             Clear chat history
  [cyan]/keys[/cyan]              Configure API keys
  [cyan]/models[/cyan]            Show available models
  [cyan]/status[/cyan]            Current configuration
  [cyan]/backtest[/cyan]          Show backtest strategies
  [cyan]/provider <name>[/cyan]   Switch AI provider
  [cyan]/model <name>[/cyan]      Switch model
  [cyan]/setkey <p> <k>[/cyan]    Set API key
  [cyan]/tickers[/cyan]           Popular tickers list

[bold yellow]ANALYSIS EXAMPLES[/bold yellow]
  • "technical analysis of SPY"
  • "fundamentals of MSFT"
  • "insider trading for AAPL"
  • "analyst recommendations for NVDA"
  • "sector performance"

[bold yellow]BACKTESTING[/bold yellow]
  • "backtest SMA crossover on AAPL"
  • "backtest RSI strategy on SPY"
  • "backtest MACD on NVDA"
  Strategies: sma_crossover, rsi, macd, bollinger, momentum, breakout

[bold yellow]KEYBOARD SHORTCUTS[/bold yellow]
  [bold]Tab[/bold]      Autocomplete suggestion
  [bold]Ctrl+L[/bold]   Clear chat
  [bold]Ctrl+M[/bold]   Show models
  [bold]Ctrl+H[/bold]   Toggle quick help
  [bold]Ctrl+P[/bold]   Command palette
  [bold]Esc[/bold]      Cancel operation

[bold yellow]TIPS[/bold yellow]
  • Type [cyan]$AAPL[/cyan] or [cyan]AAPL[/cyan] - tickers auto-detected
  • Use Tab for smart autocomplete
  • Detected tickers shown next to input
"""
        chat.write(Panel(
            Text.from_markup(help_text),
            title=f"[bold cyan]{SIGMA} Help[/bold cyan]",
            border_style="cyan",
            padding=(0, 1),
        ))
    
    def _show_popular_tickers(self, chat: ChatLog):
        """Show popular tickers organized by category."""
        tickers_text = """
[bold]Tech Giants[/bold]: AAPL, MSFT, GOOGL, AMZN, META, NVDA
[bold]Semiconductors[/bold]: NVDA, AMD, INTC, AVGO, QCOM, TSM
[bold]EVs & Auto[/bold]: TSLA, RIVN, LCID, F, GM
[bold]Finance[/bold]: JPM, BAC, GS, MS, V, MA
[bold]Healthcare[/bold]: JNJ, PFE, UNH, MRK, ABBV
[bold]ETFs[/bold]: SPY, QQQ, IWM, DIA, VTI, VOO
[bold]Sector ETFs[/bold]: XLK, XLF, XLE, XLV, XLI
"""
        chat.write(Panel(
            Text.from_markup(tickers_text),
            title=f"[cyan]{SIGMA} Popular Tickers[/cyan]",
            border_style="dim",
        ))
    
    def _show_keys(self, chat: ChatLog):
        chat.write_system(f"""
[bold]{SIGMA} API Keys[/bold]
Set key: /setkey <provider> <key>

Providers: google, openai, anthropic, groq, xai
Example: /setkey google AIzaSy...
""")
        self._show_status(chat)
    
    def _show_status(self, chat: ChatLog):
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("", style="bold")
        table.add_column("")
        
        provider = getattr(self.settings.default_provider, 'value', str(self.settings.default_provider))
        table.add_row("Provider", provider)
        table.add_row("Model", self.settings.default_model)
        table.add_row("", "")
        
        keys = [
            ("Google", self.settings.google_api_key),
            ("OpenAI", self.settings.openai_api_key),
            ("Anthropic", self.settings.anthropic_api_key),
            ("Groq", self.settings.groq_api_key),
            ("xAI", self.settings.xai_api_key),
        ]
        for name, key in keys:
            status = "[green]OK[/green]" if key else "[dim]--[/dim]"
            table.add_row(f"  {name}", Text.from_markup(status))
        
        chat.write(Panel(table, title=f"[cyan]{SIGMA} Config[/cyan]", border_style="dim"))
    
    def _show_models(self, chat: ChatLog):
        table = Table(title=f"{SIGMA} Models", show_header=True, border_style="dim")
        table.add_column("Provider", style="cyan")
        table.add_column("Models")
        for p, m in AVAILABLE_MODELS.items():
            table.add_row(p, ", ".join(m))
        chat.write(table)
    
    def _show_strategies(self, chat: ChatLog):
        strategies = get_available_strategies()
        table = Table(title=f"{SIGMA} Strategies", show_header=True, border_style="dim")
        table.add_column("Name", style="cyan")
        table.add_column("Description")
        for k, v in strategies.items():
            table.add_row(k, v.get('description', ''))
        chat.write(table)
    
    def _switch_provider(self, provider: str, chat: ChatLog):
        valid = ["google", "openai", "anthropic", "groq", "xai", "ollama"]
        if provider not in valid:
            chat.write_error(f"Invalid. Use: {', '.join(valid)}")
            return
        try:
            self.settings.default_provider = LLMProvider(provider)
            if provider in AVAILABLE_MODELS:
                self.settings.default_model = AVAILABLE_MODELS[provider][0]
            self._init_llm()
            chat.write_system(f"Switched to {provider}")
        except Exception as e:
            chat.write_error(str(e))
    
    def _switch_model(self, model: str, chat: ChatLog):
        self.settings.default_model = model
        self._init_llm()
        chat.write_system(f"Model: {model}")
    
    def _set_key(self, provider: str, key: str, chat: ChatLog):
        try:
            save_api_key(LLMProvider(provider), key)
            chat.write_system(f"{SIGMA} Key saved for {provider}")
            if provider == getattr(self.settings.default_provider, 'value', ''):
                self._init_llm()
        except Exception as e:
            chat.write_error(str(e))
    
    @work(exclusive=True)
    async def _process_query(self, query: str, chat: ChatLog):
        if not self.llm:
            chat.write_error("No LLM. Use /keys to configure.")
            return
        
        self.is_processing = True
        indicator = self.query_one("#sigma-indicator", SigmaIndicator)
        tool_display = self.query_one("#tool-calls-display", ToolCallDisplay)
        ticker_highlight = self.query_one("#ticker-highlight", TickerHighlight)
        
        # Clear ticker highlight and start sigma animation
        ticker_highlight.update("")
        indicator.set_active(True)
        
        try:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(self.conversation)
            messages.append({"role": "user", "content": query})
            
            all_tools = TOOLS + [BACKTEST_TOOL]
            
            async def on_tool(name: str, args: dict):
                tool_display.add_tool_call(name)
                if name == "run_backtest":
                    result = run_backtest(**args)
                else:
                    result = execute_tool(name, args)
                tool_display.complete_tool_call(name)
                return result
            
            response = await self.llm.generate(messages, tools=all_tools, on_tool_call=on_tool)
            
            # Clear tool display after getting response
            await asyncio.sleep(0.5)  # Brief pause to show completion
            tool_display.clear()
            
            if response:
                chat.write_assistant(response)
                self.conversation.append({"role": "user", "content": query})
                self.conversation.append({"role": "assistant", "content": response})
                if len(self.conversation) > 20:
                    self.conversation = self.conversation[-20:]
            else:
                chat.write_error("No response")
        except Exception as e:
            tool_display.clear()
            chat.write_error(str(e))
        finally:
            indicator.set_active(False)
            self.is_processing = False
            self.query_one("#prompt-input", Input).focus()
    
    def action_clear(self):
        chat = self.query_one("#chat-log", ChatLog)
        chat.clear()
        self.conversation = []
        chat.write_system("Cleared")
    
    def action_models(self):
        self._show_models(self.query_one("#chat-log", ChatLog))
    
    def action_help_toggle(self):
        """Toggle quick help panel."""
        help_panel = self.query_one("#help-panel", Static)
        if self.show_help:
            help_panel.remove_class("visible")
            help_panel.update("")
        else:
            help_panel.add_class("visible")
            help_panel.update(Text.from_markup(
                "[bold]Quick Commands:[/bold] /help /clear /keys /models /status /backtest  "
                "[bold]Shortcuts:[/bold] Tab=autocomplete Ctrl+L=clear Ctrl+M=models"
            ))
        self.show_help = not self.show_help
    
    def action_cancel(self):
        if self.is_processing:
            self.is_processing = False
            tool_display = self.query_one("#tool-calls-display", ToolCallDisplay)
            tool_display.clear()


def launch():
    """Launch Sigma."""
    SigmaApp().run()


if __name__ == "__main__":
    launch()
