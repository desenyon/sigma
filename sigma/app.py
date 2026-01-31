"""Sigma v3.2.0 - Finance Research Agent."""

import asyncio
import os
from datetime import datetime
from typing import Optional, List

from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.widgets import Footer, Input, RichLog, Static
from textual.suggester import Suggester

from .config import LLMProvider, get_settings, save_api_key, AVAILABLE_MODELS
from .llm import get_llm
from .tools import TOOLS, execute_tool
from .backtest import run_backtest, get_available_strategies, BACKTEST_TOOL


__version__ = "3.2.0"
SIGMA = "σ"

# Animated sigma logo frames for thinking state
THINKING_LOGO_FRAMES = [
    """[bold blue]
    ███████╗██╗ ██████╗ ███╗   ███╗ █████╗ 
    ██╔════╝██║██╔════╝ ████╗ ████║██╔══██╗
    ███████╗██║██║  ███╗██╔████╔██║███████║
    ╚════██║██║██║   ██║██║╚██╔╝██║██╔══██║
    ███████║██║╚██████╔╝██║ ╚═╝ ██║██║  ██║
    ╚══════╝╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝[/bold blue]
              [dim]analyzing[/dim]""",
    """[bold cyan]
    ███████╗██╗ ██████╗ ███╗   ███╗ █████╗ 
    ██╔════╝██║██╔════╝ ████╗ ████║██╔══██╗
    ███████╗██║██║  ███╗██╔████╔██║███████║
    ╚════██║██║██║   ██║██║╚██╔╝██║██╔══██║
    ███████║██║╚██████╔╝██║ ╚═╝ ██║██║  ██║
    ╚══════╝╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝[/bold cyan]
              [dim]analyzing.[/dim]""",
    """[bold white]
    ███████╗██╗ ██████╗ ███╗   ███╗ █████╗ 
    ██╔════╝██║██╔════╝ ████╗ ████║██╔══██╗
    ███████╗██║██║  ███╗██╔████╔██║███████║
    ╚════██║██║██║   ██║██║╚██╔╝██║██╔══██║
    ███████║██║╚██████╔╝██║ ╚═╝ ██║██║  ██║
    ╚══════╝╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝[/bold white]
              [dim]analyzing..[/dim]""",
    """[bold cyan]
    ███████╗██╗ ██████╗ ███╗   ███╗ █████╗ 
    ██╔════╝██║██╔════╝ ████╗ ████║██╔══██╗
    ███████╗██║██║  ███╗██╔████╔██║███████║
    ╚════██║██║██║   ██║██║╚██╔╝██║██╔══██║
    ███████║██║╚██████╔╝██║ ╚═╝ ██║██║  ██║
    ╚══════╝╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝[/bold cyan]
              [dim]analyzing...[/dim]""",
]

# Welcome banner - clean design
WELCOME_BANNER = """
[bold blue]███████╗██╗ ██████╗ ███╗   ███╗ █████╗ [/bold blue]
[bold blue]██╔════╝██║██╔════╝ ████╗ ████║██╔══██╗[/bold blue]
[bold blue]███████╗██║██║  ███╗██╔████╔██║███████║[/bold blue]
[bold blue]╚════██║██║██║   ██║██║╚██╔╝██║██╔══██║[/bold blue]
[bold blue]███████║██║╚██████╔╝██║ ╚═╝ ██║██║  ██║[/bold blue]
[bold blue]╚══════╝╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝[/bold blue]

[bold cyan]Finance Research Agent[/bold cyan]  [dim]v3.2.0 | Native macOS[/dim]
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

# Autocomplete suggestions
SUGGESTIONS = [
    "analyze AAPL",
    "analyze MSFT", 
    "analyze GOOGL",
    "analyze NVDA",
    "analyze TSLA",
    "analyze META",
    "analyze AMZN",
    "compare AAPL MSFT GOOGL",
    "compare NVDA AMD INTC",
    "technical analysis of AAPL",
    "technical analysis of SPY",
    "backtest SMA crossover on AAPL",
    "backtest RSI strategy on SPY",
    "market overview",
    "sector performance",
    "get quote for AAPL",
    "price of NVDA",
    "fundamentals of MSFT",
    "insider trading activity",
    "institutional holders",
    "analyst recommendations",
    "/help",
    "/clear",
    "/keys",
    "/models",
    "/status",
]


class SigmaSuggester(Suggester):
    """Autocomplete suggester for Sigma."""
    
    def __init__(self):
        super().__init__(use_cache=True, case_sensitive=False)
    
    async def get_suggestion(self, value: str) -> Optional[str]:
        """Get autocomplete suggestion."""
        if not value or len(value) < 2:
            return None
        
        value_lower = value.lower()
        for suggestion in SUGGESTIONS:
            if suggestion.lower().startswith(value_lower):
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

#thinking-area {
    height: auto;
    width: 100%;
    content-align: center middle;
    background: #0a0a0f;
    display: none;
    padding: 1;
}

#thinking-area.visible {
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
"""


class ThinkingDisplay(Static):
    """Animated sigma logo during thinking."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame = 0
        self.timer = None
    
    def start(self):
        """Start the animation."""
        self.add_class("visible")
        self.frame = 0
        self.update(Text.from_markup(THINKING_LOGO_FRAMES[0]))
        self.timer = self.set_interval(0.3, self._animate)
    
    def stop(self):
        """Stop the animation."""
        if self.timer:
            self.timer.stop()
            self.timer = None
        self.remove_class("visible")
        self.update("")
    
    def _animate(self):
        """Cycle through animation frames."""
        self.frame = (self.frame + 1) % len(THINKING_LOGO_FRAMES)
        self.update(Text.from_markup(THINKING_LOGO_FRAMES[self.frame]))


class SigmaIndicator(Static):
    """Pulsing sigma indicator."""
    
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
            self.timer = self.set_interval(0.2, self._pulse)
        elif not active and self.timer:
            self.timer.stop()
            self.timer = None
            self.update(Text.from_markup(f"[bold blue]{SIGMA}[/bold blue]"))
    
    def _pulse(self):
        colors = ["#3b82f6", "#60a5fa", "#93c5fd", "#60a5fa"]
        self.frame = (self.frame + 1) % len(colors)
        self.update(Text.from_markup(f"[bold {colors[self.frame]}]{SIGMA}[/bold {colors[self.frame]}]"))


class ChatLog(RichLog):
    """Chat log with rich formatting."""
    
    def write_user(self, message: str):
        self.write(Panel(
            Text(message, style="white"),
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
        self.write(Text.from_markup(f"  [dim]{SIGMA} executing {tool_name}...[/dim]"))
    
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
    
    def compose(self) -> ComposeResult:
        yield Container(
            ScrollableContainer(
                ChatLog(id="chat-log", highlight=True, markup=True),
                id="chat-area",
            ),
            Static(id="thinking-area"),
            Container(
                Horizontal(
                    SigmaIndicator(id="sigma-indicator"),
                    Input(
                        placeholder="Ask about any stock, market, or strategy...",
                        id="prompt-input",
                        suggester=SigmaSuggester(),
                    ),
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
        chat.write_system(f"{SIGMA} Type /help for commands or ask anything about markets")
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
            chat.write_system(f"""
[bold]{SIGMA} Commands[/bold]
  /help              Show commands
  /clear             Clear chat
  /keys              Configure API keys  
  /models            Show models
  /provider <name>   Switch provider
  /model <name>      Switch model
  /status            Show configuration
  /backtest          Show strategies

[bold]{SIGMA} Shortcuts[/bold]
  Ctrl+L  Clear    Ctrl+M  Models    Ctrl+P  Palette
""")
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
        else:
            chat.write_error(f"Unknown command: {command}")
    
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
        thinking = self.query_one("#thinking-area", Static)
        indicator = self.query_one("#sigma-indicator", SigmaIndicator)
        
        # Start animated thinking display
        thinking.add_class("visible")
        frame = [0]
        
        def animate():
            thinking.update(Text.from_markup(THINKING_LOGO_FRAMES[frame[0]]))
            frame[0] = (frame[0] + 1) % len(THINKING_LOGO_FRAMES)
        
        animate()
        timer = self.set_interval(0.3, animate)
        indicator.set_active(True)
        
        try:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(self.conversation)
            messages.append({"role": "user", "content": query})
            
            all_tools = TOOLS + [BACKTEST_TOOL]
            
            async def on_tool(name: str, args: dict):
                chat.write_tool(name)
                if name == "run_backtest":
                    return run_backtest(**args)
                return execute_tool(name, args)
            
            response = await self.llm.generate(messages, tools=all_tools, on_tool_call=on_tool)
            
            if response:
                chat.write_assistant(response)
                self.conversation.append({"role": "user", "content": query})
                self.conversation.append({"role": "assistant", "content": response})
                if len(self.conversation) > 20:
                    self.conversation = self.conversation[-20:]
            else:
                chat.write_error("No response")
        except Exception as e:
            chat.write_error(str(e))
        finally:
            timer.stop()
            thinking.remove_class("visible")
            thinking.update("")
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
    
    def action_cancel(self):
        if self.is_processing:
            self.is_processing = False


def launch():
    """Launch Sigma."""
    SigmaApp().run()


if __name__ == "__main__":
    launch()
