"""Sigma v3.4.0 - Finance Research Agent."""

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

from .config import LLMProvider, get_settings, save_api_key, AVAILABLE_MODELS, SigmaError, ErrorCode
from .llm import get_llm
from .tools import TOOLS, execute_tool
from .backtest import run_backtest, get_available_strategies, BACKTEST_TOOL


__version__ = "3.4.0"
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

# Sigma animation frames - color cycling for thinking/processing state
SIGMA_FRAMES = [
    "[bold #3b82f6]s[/bold #3b82f6]",
    "[bold #60a5fa]si[/bold #60a5fa]",
    "[bold #93c5fd]sig[/bold #93c5fd]",
    "[bold #bfdbfe]sigm[/bold #bfdbfe]",
    "[bold white]sigma[/bold white]",
    "[bold #bfdbfe]sigm[/bold #bfdbfe]",
    "[bold #93c5fd]sig[/bold #93c5fd]",
    "[bold #60a5fa]si[/bold #60a5fa]",
    "[bold #3b82f6]s[/bold #3b82f6]",
    "[bold cyan].[/bold cyan]",
]

# Sigma pulse animation (color breathing)
SIGMA_PULSE_FRAMES = [
    "[bold #1e40af]o[/bold #1e40af]",
    "[bold #2563eb]o[/bold #2563eb]",
    "[bold #3b82f6]o[/bold #3b82f6]",
    "[bold #60a5fa]o[/bold #60a5fa]",
    "[bold #93c5fd]o[/bold #93c5fd]",
    "[bold #bfdbfe]o[/bold #bfdbfe]",
    "[bold #93c5fd]o[/bold #93c5fd]",
    "[bold #60a5fa]o[/bold #60a5fa]",
    "[bold #3b82f6]o[/bold #3b82f6]",
    "[bold #2563eb]o[/bold #2563eb]",
]

# Tool call spinner frames - ASCII based
TOOL_SPINNER_FRAMES = [
    "|", "/", "-", "\\"
]

# Welcome banner - clean design
WELCOME_BANNER = """
[bold #3b82f6]███████╗██╗ ██████╗ ███╗   ███╗ █████╗ [/bold #3b82f6]
[bold #60a5fa]██╔════╝██║██╔════╝ ████╗ ████║██╔══██╗[/bold #60a5fa]
[bold #93c5fd]███████╗██║██║  ███╗██╔████╔██║███████║[/bold #93c5fd]
[bold #60a5fa]╚════██║██║██║   ██║██║╚██╔╝██║██╔══██║[/bold #60a5fa]
[bold #3b82f6]███████║██║╚██████╔╝██║ ╚═╝ ██║██║  ██║[/bold #3b82f6]
[bold #1d4ed8]╚══════╝╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝[/bold #1d4ed8]

[bold cyan]Finance Research Agent[/bold cyan]  [dim]v3.4.0[/dim]
"""

SYSTEM_PROMPT = """You are Sigma (σ), an elite AI-powered Finance Research Agent. You combine the analytical rigor of a quantitative analyst, the market intuition of a seasoned portfolio manager, and the communication clarity of a top financial advisor.

CORE CAPABILITIES:
- Real-time market data analysis (quotes, charts, technicals) via yfinance and Polygon.io
- Fundamental analysis (financials, ratios, earnings, valuations)
- Technical analysis (RSI, MACD, Bollinger Bands, moving averages, support/resistance)
- Backtesting strategies (SMA crossover, RSI, MACD, Bollinger, momentum, breakout)
- Portfolio analysis and optimization
- Sector and market overview with economic indicators
- Insider trading and institutional activity tracking
- Financial news search and SEC filings analysis

RESPONSE PHILOSOPHY:
1. BE PROACTIVE: Anticipate follow-up questions and address them
2. BE THOROUGH: When analyzing, cover fundamentals + technicals + sentiment
3. BE ACTIONABLE: Always end with clear recommendations or next steps
4. BE DATA-DRIVEN: Cite specific numbers, dates, and percentages
5. BE HONEST: Acknowledge uncertainty and risks

RESPONSE FORMAT:
- Start with a 1-2 sentence executive summary (the key takeaway)
- Use structured sections with clear headers (## format)
- Present comparative data in markdown tables
- Highlight key metrics: **bold** for critical numbers
- Use bullet points for easy scanning
- End with "**Bottom Line:**" or "**Recommendation:**"

RATING SYSTEM (when asked for recommendations):
- STRONG BUY [A+]: Exceptional opportunity, high conviction
- BUY [A]: Favorable outlook, solid fundamentals
- HOLD [B]: Fair value, wait for better entry
- SELL [C]: Concerns outweigh positives
- STRONG SELL [D]: Significant risks, avoid

DATA GATHERING RULES:
- ALWAYS use tools to fetch current data before answering stock questions
- Use multiple tools for comprehensive analysis (quote + technicals + fundamentals)
- Cross-reference data points for accuracy
- If a tool fails, try alternative approaches or acknowledge the limitation

PROACTIVE INSIGHTS:
When analyzing any stock, proactively mention:
- Recent earnings surprises or upcoming earnings dates
- Major analyst rating changes
- Unusual volume or price movements
- Relevant sector trends
- Key support/resistance levels
- Comparison to peers when relevant

FORBIDDEN:
- Never fabricate data or prices
- Never provide data without fetching it first
- Never give buy/sell advice without disclosure of risks
- Never claim certainty about future performance

Remember: Users trust you for professional-grade financial research. Exceed their expectations with every response."""

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

# Extended action verbs for smart completion
ACTION_VERBS = [
    "analyze", "compare", "show", "get", "what is", "tell me about",
    "technical analysis", "fundamentals", "price", "quote", "chart",
    "backtest", "insider trading", "institutional", "analyst", "earnings",
    "financials", "valuation", "news", "sector", "market", "portfolio"
]

# Ticker categories for smart suggestions
TICKER_CATEGORIES = {
    "tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "AMD", "INTC", "CRM", "ADBE"],
    "finance": ["JPM", "BAC", "GS", "MS", "V", "MA", "BRK.B", "C", "WFC", "AXP"],
    "healthcare": ["JNJ", "UNH", "PFE", "MRK", "ABBV", "LLY", "TMO", "ABT", "BMY", "GILD"],
    "consumer": ["AMZN", "TSLA", "HD", "NKE", "MCD", "SBUX", "COST", "WMT", "TGT", "LOW"],
    "energy": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL"],
    "etf": ["SPY", "QQQ", "IWM", "DIA", "VTI", "VOO", "VXX", "ARKK", "XLF", "XLK"],
    "crypto": ["COIN", "MSTR", "RIOT", "MARA", "HUT"],
    "ev": ["TSLA", "RIVN", "LCID", "NIO", "XPEV", "LI"],
    "ai": ["NVDA", "AMD", "MSFT", "GOOGL", "META", "PLTR", "AI", "PATH", "SNOW"],
    "semiconductor": ["NVDA", "AMD", "INTC", "AVGO", "QCOM", "TXN", "MU", "AMAT", "LRCX", "ASML"],
}


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
    """Smart autocomplete with fuzzy matching and context awareness."""
    
    def __init__(self):
        super().__init__(use_cache=False, case_sensitive=False)
        self._build_suggestion_index()
    
    def _build_suggestion_index(self):
        """Build an index of all possible suggestions for fast lookup."""
        self.all_suggestions = []
        
        # Add static suggestions
        self.all_suggestions.extend(SUGGESTIONS)
        
        # Generate dynamic suggestions for all tickers
        for ticker in COMMON_TICKERS:
            self.all_suggestions.extend([
                f"analyze {ticker}",
                f"technical analysis of {ticker}",
                f"fundamentals of {ticker}",
                f"price of {ticker}",
                f"quote {ticker}",
                f"insider trading {ticker}",
                f"earnings {ticker}",
                f"news {ticker}",
            ])
        
        # Add category-based suggestions
        for category, tickers in TICKER_CATEGORIES.items():
            self.all_suggestions.append(f"best {category} stocks")
            self.all_suggestions.append(f"{category} sector performance")
            if len(tickers) >= 3:
                self.all_suggestions.append(f"compare {' '.join(tickers[:3])}")
    
    def _fuzzy_match(self, query: str, target: str) -> float:
        """Calculate fuzzy match score (0-1). Higher is better."""
        query = query.lower()
        target = target.lower()
        
        # Exact prefix match is best
        if target.startswith(query):
            return 1.0 + len(query) / len(target)
        
        # Check if all query chars appear in order
        q_idx = 0
        matches = 0
        consecutive = 0
        max_consecutive = 0
        last_match = -1
        
        for t_idx, char in enumerate(target):
            if q_idx < len(query) and char == query[q_idx]:
                matches += 1
                if last_match == t_idx - 1:
                    consecutive += 1
                    max_consecutive = max(max_consecutive, consecutive)
                else:
                    consecutive = 1
                last_match = t_idx
                q_idx += 1
        
        if q_idx < len(query):
            # Not all chars matched
            # Try substring match
            if query in target:
                return 0.5
            return 0
        
        # Score based on match quality
        score = (matches / len(query)) * 0.5 + (max_consecutive / len(query)) * 0.3
        # Bonus for shorter targets (more relevant)
        score += (1 - len(target) / 100) * 0.2
        
        return score
    
    def _get_context_suggestions(self, value: str) -> List[str]:
        """Get context-aware suggestions based on partial input."""
        suggestions = []
        value_lower = value.lower().strip()
        
        # Command shortcuts
        if value.startswith("/"):
            cmd = value_lower[1:]
            commands = ["/help", "/clear", "/keys", "/models", "/status", "/backtest", 
                       "/provider", "/model", "/setkey", "/tickers"]
            for c in commands:
                if c[1:].startswith(cmd):
                    suggestions.append(c)
            return suggestions
        
        # Detect if user is typing a ticker
        words = value.split()
        last_word = words[-1] if words else ""
        
        if last_word.startswith("$") or (last_word.isupper() and len(last_word) >= 1):
            ticker_prefix = last_word.lstrip("$").upper()
            matching_tickers = [t for t in COMMON_TICKERS if t.startswith(ticker_prefix)]
            
            # If we have an action verb, complete with ticker
            action_words = ["analyze", "compare", "technical", "price", "quote", 
                           "fundamentals", "insider", "earnings", "news"]
            prefix = " ".join(words[:-1]).lower() if len(words) > 1 else ""
            
            for ticker in matching_tickers[:5]:
                if prefix:
                    suggestions.append(f"{prefix} {ticker}")
                else:
                    suggestions.append(f"analyze {ticker}")
            return suggestions
        
        # Natural language patterns
        patterns = [
            ("ana", "analyze"),
            ("tech", "technical analysis of"),
            ("fun", "fundamentals of"),
            ("comp", "compare"),
            ("back", "backtest"),
            ("mark", "market overview"),
            ("sect", "sector performance"),
            ("pri", "price of"),
            ("quo", "quote"),
            ("ins", "insider trading"),
            ("ear", "earnings"),
            ("wha", "what should I know about"),
            ("sho", "should I buy"),
            ("is ", "is NVDA overvalued"),
            ("how", "how is"),
            ("bes", "best tech stocks"),
        ]
        
        for prefix, expansion in patterns:
            if value_lower.startswith(prefix):
                if expansion.endswith("of") or expansion.endswith("about"):
                    # Add popular tickers
                    for ticker in ["AAPL", "NVDA", "MSFT", "TSLA", "GOOGL"]:
                        suggestions.append(f"{expansion} {ticker}")
                else:
                    suggestions.append(expansion)
        
        return suggestions
    
    async def get_suggestion(self, value: str) -> Optional[str]:
        """Get the best autocomplete suggestion."""
        if not value or len(value) < 1:
            return None
        
        value_lower = value.lower().strip()
        
        # Get context-aware suggestions first
        context_suggestions = self._get_context_suggestions(value)
        if context_suggestions:
            return context_suggestions[0]
        
        # Fuzzy match against all suggestions
        scored = []
        for suggestion in self.all_suggestions:
            score = self._fuzzy_match(value_lower, suggestion)
            if score > 0:
                scored.append((score, suggestion))
        
        # Sort by score and return best
        scored.sort(key=lambda x: x[0], reverse=True)
        
        if scored:
            return scored[0][1]
        
        # Last resort: if looks like a ticker, suggest analyze
        if value.isupper() and len(value) <= 5 and value.isalpha():
            return f"analyze {value}"
        
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
    background: #0f1419;
    border-top: solid #1e293b;
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
    max-height: 8;
    background: #0f1419;
    border: round #1e293b;
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
    background: #0f1419;
}

#input-row {
    height: 3;
    width: 100%;
}

#sigma-indicator {
    width: 4;
    height: 3;
    content-align: center middle;
    background: transparent;
}

#prompt-input {
    width: 1fr;
    background: #1e293b;
    border: tall #3b82f6;
    color: #f8fafc;
    padding: 0 1;
}

#prompt-input:focus {
    border: tall #60a5fa;
    background: #1e3a5f;
}

#prompt-input.-autocomplete {
    border: tall #22c55e;
}

#ticker-highlight {
    width: auto;
    height: 1;
    padding: 0 1;
    background: transparent;
    color: #22d3ee;
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
        self.frame = (self.frame + 1) % len(TOOL_SPINNER_FRAMES)
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
                spinner = TOOL_SPINNER_FRAMES[tc["frame"] % len(TOOL_SPINNER_FRAMES)]
                lines.append(f"  [cyan]{spinner}[/cyan] [bold]{tc['name']}[/bold] [dim]executing...[/dim]")
            else:
                lines.append(f"  [green][ok][/green] [bold]{tc['name']}[/bold] [green]done[/green]")
        
        self.update(Text.from_markup("\n".join(lines)))


class SigmaIndicator(Static):
    """Animated sigma indicator - typewriter style when active."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = False
        self.mode = "idle"  # idle, thinking, tool
        self.frame = 0
        self.timer = None
    
    def on_mount(self):
        self.update(Text.from_markup(f"[bold blue]{SIGMA}[/bold blue]"))
    
    def set_active(self, active: bool, mode: str = "thinking"):
        self.active = active
        self.mode = mode if active else "idle"
        if active and not self.timer:
            self.frame = 0
            interval = 0.08 if mode == "thinking" else 0.12
            self.timer = self.set_interval(interval, self._animate)
        elif not active and self.timer:
            self.timer.stop()
            self.timer = None
            self.update(Text.from_markup(f"[bold blue]{SIGMA}[/bold blue]"))
    
    def _animate(self):
        if self.mode == "thinking":
            # Typewriter effect: s -> si -> sig -> sigm -> sigma -> sigm -> ...
            self.frame = (self.frame + 1) % len(SIGMA_FRAMES)
            self.update(Text.from_markup(SIGMA_FRAMES[self.frame]))
        else:
            # Pulse effect for tool calls
            self.frame = (self.frame + 1) % len(SIGMA_PULSE_FRAMES)
            self.update(Text.from_markup(SIGMA_PULSE_FRAMES[self.frame]))


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
        chat.write_system(f"{SIGMA} Provider: [bold]{provider}[/bold] | Model: [bold]{self.settings.default_model}[/bold]")
        chat.write_system(f"{SIGMA} Type [cyan]/help[/cyan] for commands • [cyan]/keys[/cyan] to set up API keys")
        chat.write_system("")
        
        self._init_llm()
        self.query_one("#prompt-input", Input).focus()
    
    def _init_llm(self):
        """Initialize the LLM client with proper error handling."""
        try:
            self.llm = get_llm(self.settings.default_provider, self.settings.default_model)
        except SigmaError as e:
            chat = self.query_one("#chat-log", ChatLog)
            chat.write_error(f"[E{e.code}] {e.message}")
            if e.details.get("hint"):
                chat.write_system(f"[dim]Hint: {e.details['hint']}[/dim]")
            self.llm = None
        except Exception as e:
            chat = self.query_one("#chat-log", ChatLog)
            chat.write_error(f"[E{ErrorCode.PROVIDER_ERROR}] Failed to initialize: {str(e)[:100]}")
            chat.write_system("[dim]Use /keys to configure API keys[/dim]")
            self.llm = None
    
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
        """Show comprehensive API key management interface."""
        keys_help = f"""
[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]
[bold]                    {SIGMA} API KEY MANAGER                     [/bold]
[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]

[bold yellow]QUICK SETUP[/bold yellow]
  Set a key:  [cyan]/setkey <provider> <your-api-key>[/cyan]
  
[bold yellow]LLM PROVIDERS[/bold yellow]
  [bold]google[/bold]      → https://aistudio.google.com/apikey
  [bold]openai[/bold]      → https://platform.openai.com/api-keys
  [bold]anthropic[/bold]   → https://console.anthropic.com/settings/keys
  [bold]groq[/bold]        → https://console.groq.com/keys [dim](free!)[/dim]
  [bold]xai[/bold]         → https://console.x.ai

[bold yellow]DATA PROVIDERS[/bold yellow] [dim](optional - enhances data quality)[/dim]
  [bold]polygon[/bold]     → https://polygon.io/dashboard/api-keys

[bold yellow]EXAMPLES[/bold yellow]
  /setkey google AIzaSyB...
  /setkey openai sk-proj-...
  /setkey polygon abc123...
  /provider groq          [dim]← switch to groq[/dim]

[bold yellow]TIPS[/bold yellow]
  • [green]Groq[/green] is free and fast - great for starting out
  • [green]Ollama[/green] runs locally - no key needed (/provider ollama)
  • Keys are stored in [dim]~/.sigma/config.env[/dim]
"""
        chat.write(Panel(
            Text.from_markup(keys_help),
            title=f"[bold cyan]{SIGMA} API Keys[/bold cyan]",
            border_style="cyan",
            padding=(0, 1),
        ))
        self._show_status(chat)
    
    def _show_status(self, chat: ChatLog):
        """Show current configuration status."""
        table = Table(show_header=True, box=None, padding=(0, 2), title=f"{SIGMA} Current Status")
        table.add_column("Setting", style="bold")
        table.add_column("Value")
        table.add_column("Status")
        
        provider = getattr(self.settings.default_provider, 'value', str(self.settings.default_provider))
        table.add_row("Provider", provider, "[green][*][/green] Active")
        table.add_row("Model", self.settings.default_model, "")
        table.add_row("", "", "")
        
        # LLM Keys
        llm_keys = [
            ("Google", self.settings.google_api_key, "google"),
            ("OpenAI", self.settings.openai_api_key, "openai"),
            ("Anthropic", self.settings.anthropic_api_key, "anthropic"),
            ("Groq", self.settings.groq_api_key, "groq"),
            ("xAI", self.settings.xai_api_key, "xai"),
        ]
        for name, key, prov in llm_keys:
            if key:
                masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
                status = "[green][ok][/green]"
            else:
                masked = "[dim]not set[/dim]"
                status = "[dim]--[/dim]"
            
            # Highlight active provider
            if prov == provider:
                name = f"[bold cyan]{name}[/bold cyan]"
            table.add_row(f"  {name}", Text.from_markup(masked), Text.from_markup(status))
        
        table.add_row("", "", "")
        
        # Data Keys
        polygon_key = getattr(self.settings, 'polygon_api_key', None)
        if polygon_key:
            table.add_row("  Polygon", polygon_key[:8] + "...", Text.from_markup("[green][ok][/green]"))
        else:
            table.add_row("  Polygon", Text.from_markup("[dim]not set[/dim]"), Text.from_markup("[dim]optional[/dim]"))
        
        chat.write(Panel(table, border_style="dim"))
    
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
        """Save an API key for a provider."""
        # Normalize provider name
        provider = provider.lower().strip()
        valid_providers = ["google", "openai", "anthropic", "groq", "xai", "polygon", "alphavantage", "exa"]
        
        if provider not in valid_providers:
            chat.write_error(f"[E{ErrorCode.INVALID_INPUT}] Unknown provider: {provider}")
            chat.write_system(f"Valid providers: {', '.join(valid_providers)}")
            return
        
        # Basic key validation
        key = key.strip()
        if len(key) < 10:
            chat.write_error(f"[E{ErrorCode.INVALID_INPUT}] API key seems too short")
            return
        
        try:
            success = save_api_key(provider, key)
            if success:
                # Reload settings
                self.settings = get_settings()
                
                # Show success with masked key
                masked = key[:6] + "..." + key[-4:] if len(key) > 10 else "***"
                chat.write_system(f"[green][ok][/green] {SIGMA} Key saved for [bold]{provider}[/bold]: {masked}")
                
                # Auto-switch to this provider if it's an LLM provider and we don't have an LLM
                llm_providers = ["google", "openai", "anthropic", "groq", "xai"]
                if provider in llm_providers:
                    if not self.llm or provider == getattr(self.settings.default_provider, 'value', ''):
                        self._switch_provider(provider, chat)
            else:
                chat.write_error(f"[E{ErrorCode.UNKNOWN_ERROR}] Failed to save key")
        except Exception as e:
            chat.write_error(f"[E{ErrorCode.UNKNOWN_ERROR}] {str(e)}")
    
    @work(exclusive=True)
    async def _process_query(self, query: str, chat: ChatLog):
        if not self.llm:
            chat.write_error(f"[E{ErrorCode.API_KEY_MISSING}] No LLM configured. Use /keys to set up.")
            return
        
        self.is_processing = True
        indicator = self.query_one("#sigma-indicator", SigmaIndicator)
        tool_display = self.query_one("#tool-calls-display", ToolCallDisplay)
        ticker_highlight = self.query_one("#ticker-highlight", TickerHighlight)
        
        # Clear ticker highlight and start sigma animation
        ticker_highlight.update("")
        indicator.set_active(True, mode="thinking")
        
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
                chat.write_error(f"[E{ErrorCode.RESPONSE_INVALID}] No response received")
                
        except SigmaError as e:
            tool_display.clear()
            # Format SigmaError nicely
            chat.write_error(f"[E{e.code}] {e.message}")
            if e.details.get("hint"):
                chat.write_system(f"[dim]Hint: {e.details['hint']}[/dim]")
        except Exception as e:
            tool_display.clear()
            # Try to parse common API errors
            error_str = str(e)
            if "401" in error_str or "invalid" in error_str.lower() and "key" in error_str.lower():
                chat.write_error(f"[E{ErrorCode.API_KEY_INVALID}] API key is invalid. Use /keys to update.")
            elif "429" in error_str or "rate" in error_str.lower():
                chat.write_error(f"[E{ErrorCode.API_KEY_RATE_LIMITED}] Rate limit hit. Wait a moment and try again.")
            else:
                chat.write_error(f"[E{ErrorCode.PROVIDER_ERROR}] {error_str[:200]}")
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
