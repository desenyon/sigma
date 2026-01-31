"""Sigma CLI - Professional financial research interface."""

import asyncio
import sys
import re
from typing import Any, Optional
import time

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.markdown import Markdown
from rich.padding import Padding
from rich.box import ROUNDED, SIMPLE, HEAVY, DOUBLE
from rich.columns import Columns
from rich import box

from sigma.core.agent import SigmaAgent
from sigma.core.config import LLMProvider, get_settings


console = Console()

# Version
VERSION = "2.0.2"

# ASCII Art Banner
BANNER = """[bold bright_blue]
 ███████╗██╗ ██████╗ ███╗   ███╗ █████╗ 
 ██╔════╝██║██╔════╝ ████╗ ████║██╔══██╗
 ███████╗██║██║  ███╗██╔████╔██║███████║
 ╚════██║██║██║   ██║██║╚██╔╝██║██╔══██║
 ███████║██║╚██████╔╝██║ ╚═╝ ██║██║  ██║
 ╚══════╝╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝[/bold bright_blue]
"""

SUB_BANNER = """[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]
[bold white]        Institutional-Grade Financial Research Agent[/bold white]
[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]"""


def print_banner(model: str):
    """Print the startup banner."""
    console.print()
    console.print(BANNER)
    console.print(SUB_BANNER)
    console.print()
    
    # Status line
    console.print(f"  [dim]Version:[/dim] [bright_cyan]{VERSION}[/bright_cyan]    [dim]Model:[/dim] [bright_cyan]{model}[/bright_cyan]")
    console.print()
    console.print("  [dim]Type[/dim] [bold bright_yellow]/help[/bold bright_yellow] [dim]for commands[/dim]    [dim]Type[/dim] [bold bright_yellow]/quit[/bold bright_yellow] [dim]to exit[/dim]")
    console.print()


def print_help():
    """Print comprehensive help."""
    console.print()
    
    # Commands table
    commands = Table(title="[bold bright_cyan]Commands[/bold bright_cyan]", box=ROUNDED, show_header=True, header_style="bold")
    commands.add_column("Command", style="bright_yellow")
    commands.add_column("Description", style="white")
    
    commands.add_row("/help, /h, /?", "Show this help message")
    commands.add_row("/model <provider>", "Switch LLM provider (openai, anthropic, google, groq, ollama)")
    commands.add_row("/mode <mode>", "Switch analysis mode (default, technical, fundamental, quant)")
    commands.add_row("/clear", "Clear conversation history")
    commands.add_row("/status", "Show current configuration")
    commands.add_row("/chart <symbol>", "Quick price chart for a symbol")
    commands.add_row("/compare <sym1> <sym2>...", "Quick comparison chart")
    commands.add_row("/backtest <symbol> <strategy>", "Generate backtest algorithm")
    commands.add_row("/lean setup", "Setup LEAN Engine for backtesting")
    commands.add_row("/lean run <symbol> <strategy>", "Run backtest with LEAN Engine")
    commands.add_row("/quit, /exit, /q", "Exit Sigma")
    
    console.print(commands)
    console.print()
    
    # Analysis modes
    modes = Table(title="[bold bright_cyan]Analysis Modes[/bold bright_cyan]", box=ROUNDED, show_header=True, header_style="bold")
    modes.add_column("Mode", style="bright_yellow")
    modes.add_column("Description", style="white")
    
    modes.add_row("default", "Comprehensive analysis using all available tools")
    modes.add_row("technical", "Focus on technical indicators, charts, and price action")
    modes.add_row("fundamental", "Focus on financial statements, ratios, and valuations")
    modes.add_row("quant", "Quantitative analysis with predictions and backtesting")
    
    console.print(modes)
    console.print()
    
    # Examples
    examples = Table(title="[bold bright_cyan]Example Queries[/bold bright_cyan]", box=ROUNDED, show_header=False)
    examples.add_column("Query", style="white")
    
    examples.add_row("[dim]── Stock Analysis ──[/dim]")
    examples.add_row("  Analyze NVDA stock")
    examples.add_row("  Is AAPL a good investment?")
    examples.add_row("  Give me a deep dive on Tesla")
    examples.add_row("")
    examples.add_row("[dim]── Charts & Visualization ──[/dim]")
    examples.add_row("  Show me a chart of MSFT for the past 6 months")
    examples.add_row("  Compare NVDA, AMD, and INTC")
    examples.add_row("  Show RSI chart for SPY")
    examples.add_row("")
    examples.add_row("[dim]── Technical Analysis ──[/dim]")
    examples.add_row("  Technical analysis on QQQ")
    examples.add_row("  What are the support levels for META?")
    examples.add_row("  Is GOOGL overbought?")
    examples.add_row("")
    examples.add_row("[dim]── Predictions & Sentiment ──[/dim]")
    examples.add_row("  Predict AMZN price for next month")
    examples.add_row("  What's the sentiment on TSLA?")
    examples.add_row("  Price forecast for Bitcoin")
    examples.add_row("")
    examples.add_row("[dim]── Backtesting & Strategy ──[/dim]")
    examples.add_row("  Create a MACD strategy backtest for AAPL")
    examples.add_row("  Generate RSI mean reversion backtest for SPY")
    examples.add_row("  List available backtest strategies")
    examples.add_row("")
    examples.add_row("[dim]── Market Overview ──[/dim]")
    examples.add_row("  What are today's market movers?")
    examples.add_row("  Show sector performance")
    examples.add_row("  How are the major indices doing?")
    
    console.print(examples)
    console.print()
    
    # Strategies
    strategies = Table(title="[bold bright_cyan]Backtest Strategies[/bold bright_cyan]", box=ROUNDED, show_header=True, header_style="bold")
    strategies.add_column("Strategy", style="bright_yellow")
    strategies.add_column("Description", style="white")
    
    strategies.add_row("sma_crossover", "Classic moving average crossover (fast/slow SMA)")
    strategies.add_row("rsi_mean_reversion", "Buy oversold, sell overbought using RSI")
    strategies.add_row("macd_momentum", "MACD histogram momentum strategy")
    strategies.add_row("bollinger_bands", "Mean reversion at Bollinger Band extremes")
    strategies.add_row("dual_momentum", "Absolute + relative momentum")
    strategies.add_row("breakout", "Donchian channel breakout strategy")
    
    console.print(strategies)
    console.print()


# Tool name mappings for cleaner display
TOOL_DISPLAY_NAMES = {
    "get_stock_quote": "Stock Quote",
    "get_stock_history": "Price History",
    "get_company_info": "Company Info",
    "get_financial_statements": "Financials",
    "get_analyst_recommendations": "Analyst Ratings",
    "get_insider_trades": "Insider Trades",
    "get_institutional_holders": "Institutions",
    "get_earnings_calendar": "Earnings",
    "get_options_chain": "Options Chain",
    "get_dividends": "Dividends",
    "compare_stocks": "Compare Stocks",
    "get_market_movers": "Market Movers",
    "get_sector_performance": "Sectors",
    "get_market_indices": "Market Indices",
    "calculate_portfolio_metrics": "Portfolio",
    "search_stocks": "Stock Search",
    "get_stock_news": "News",
    "technical_analysis": "Technicals",
    "generate_price_chart": "Price Chart",
    "generate_comparison_chart": "Comparison",
    "generate_rsi_chart": "RSI Chart",
    "generate_sector_chart": "Sectors",
    "list_backtest_strategies": "Strategies",
    "generate_backtest": "Backtest",
    "generate_custom_backtest": "Custom Backtest",
    "price_forecast": "Forecast",
    "sentiment_analysis": "Sentiment",
}

TOOL_ICONS = {
    "get_stock_quote": ">",
    "get_stock_history": ">",
    "get_company_info": ">",
    "get_financial_statements": ">",
    "get_analyst_recommendations": ">",
    "get_insider_trades": ">",
    "get_institutional_holders": ">",
    "get_earnings_calendar": ">",
    "get_options_chain": ">",
    "get_dividends": ">",
    "compare_stocks": ">",
    "get_market_movers": ">",
    "get_sector_performance": ">",
    "get_market_indices": ">",
    "calculate_portfolio_metrics": ">",
    "search_stocks": ">",
    "get_stock_news": ">",
    "technical_analysis": ">",
    "generate_price_chart": ">",
    "generate_comparison_chart": ">",
    "generate_rsi_chart": ">",
    "generate_sector_chart": ">",
    "list_backtest_strategies": ">",
    "generate_backtest": ">",
    "generate_custom_backtest": ">",
    "price_forecast": ">",
    "sentiment_analysis": ">",
}


def format_tool_description(name: str, args: dict) -> tuple[str, Optional[str]]:
    """Format tool call with description. Returns (display_name, detail)."""
    display_name = TOOL_DISPLAY_NAMES.get(name, name.replace('_', ' ').title())
    icon = TOOL_ICONS.get(name, "●")
    
    symbol = args.get('symbol', '')
    symbols = args.get('symbols', [])
    query = args.get('query', '')
    strategy = args.get('strategy', '')
    
    if symbol and strategy:
        return f"{icon} {display_name}", f"{symbol.upper()} - {strategy}"
    elif symbol:
        return f"{icon} {display_name}", symbol.upper()
    elif symbols:
        return f"{icon} {display_name}", ', '.join(s.upper() for s in symbols[:3])
    elif query:
        return f"{icon} {display_name}", query[:30]
    else:
        return f"{icon} {display_name}", None


class SigmaUI:
    """Professional terminal UI for Sigma."""
    
    def __init__(self):
        self.settings = get_settings()
        self.agent: Optional[SigmaAgent] = None
        self.provider = self.settings.default_provider
        self.tool_calls: list[tuple[str, float]] = []
        self.start_time = 0.0
        self.custom_model: Optional[str] = None
        self.mode = "default"  # default, technical, fundamental, quant
        self.chart_output: Optional[str] = None  # Store chart for display
    
    def _init_agent(self):
        """Initialize agent."""
        self.agent = SigmaAgent(provider=self.provider, model=self.custom_model)
    
    def _get_model_display(self) -> str:
        """Get model name for display."""
        if self.custom_model:
            return self.custom_model
        return self.settings.get_model(self.provider)
    
    def on_tool_start(self, name: str, args: dict):
        """Called when tool starts."""
        display_name, detail = format_tool_description(name, args)
        if detail:
            console.print(f"    [bright_cyan]{display_name}[/bright_cyan] [dim]({detail})[/dim]")
        else:
            console.print(f"    [bright_cyan]{display_name}[/bright_cyan]")
    
    def on_tool_end(self, name: str, result: Any, duration_ms: float):
        """Called when tool ends."""
        self.tool_calls.append((name, duration_ms))
        
        # Check for chart output
        if isinstance(result, dict) and result.get("display_as_chart"):
            self.chart_output = result.get("chart", "")
    
    def on_thinking(self, content: str):
        """Called when agent is thinking."""
        pass
    
    def on_response(self, content: str):
        """Called with final response."""
        pass
    
    async def process_query(self, query: str):
        """Process a query."""
        if self.agent is None:
            self._init_agent()
        
        assert self.agent is not None
        
        self.tool_calls = []
        self.start_time = time.time()
        self.chart_output = None
        
        console.print()
        console.print("  [dim]╭─ Researching...[/dim]")
        
        # Run agent
        response = await self.agent.run(
            query,
            on_tool_start=self.on_tool_start,
            on_tool_end=self.on_tool_end,
            on_thinking=self.on_thinking,
            on_response=self.on_response,
        )
        
        elapsed = time.time() - self.start_time
        
        # Print data sources summary
        if self.tool_calls:
            console.print(f"  [dim]╰─[/dim] [bright_green]Called {len(self.tool_calls)} data sources[/bright_green] [dim]in {elapsed:.1f}s[/dim]")
        
        console.print()
        
        # Print chart if generated
        if self.chart_output:
            console.print(self.chart_output)
            console.print()
        
        # Print response
        self._display_response(response)
        
        console.print()
    
    def _display_response(self, response: str):
        """Display the response with professional formatting."""
        lines = response.split('\n')
        in_table = False
        table_lines: list[str] = []
        
        for line in lines:
            # Check if this is a table line
            if '|' in line and ('---' in line or line.strip().startswith('|')):
                if not in_table:
                    in_table = True
                    table_lines = []
                table_lines.append(line)
                continue
            elif in_table and line.strip():
                if '|' in line:
                    table_lines.append(line)
                    continue
                else:
                    self._print_table(table_lines)
                    in_table = False
                    table_lines = []
            elif in_table and not line.strip():
                self._print_table(table_lines)
                in_table = False
                table_lines = []
            
            # Format and print the line
            formatted = self._format_line(line)
            if formatted is not None:
                console.print(formatted)
        
        # Print any remaining table
        if table_lines:
            self._print_table(table_lines)
    
    def _format_line(self, line: str) -> Optional[str]:
        """Format a single line with proper markdown rendering."""
        stripped = line.strip()
        
        # Empty line
        if not stripped:
            return ""
        
        # Headers
        if stripped.startswith('#'):
            header_match = re.match(r'^(#+)\s*(.+)$', stripped)
            if header_match:
                level = len(header_match.group(1))
                text = header_match.group(2)
                if level == 1:
                    return f"\n[bold bright_white]{text}[/bold bright_white]"
                elif level == 2:
                    return f"\n[bold bright_cyan]▸ {text}[/bold bright_cyan]"
                else:
                    return f"\n[bold]{text}[/bold]"
        
        # Bold-only lines
        if stripped.startswith('**') and stripped.endswith('**') and stripped.count('**') == 2:
            text = stripped[2:-2]
            return f"\n[bold bright_yellow]▸ {text}[/bold bright_yellow]"
        
        # Lines starting with bold
        bold_start = re.match(r'^\*\*(.+?)\*\*(.*)$', stripped)
        if bold_start:
            bold_part = bold_start.group(1)
            rest = bold_start.group(2)
            rest = re.sub(r'\*\*(.+?)\*\*', r'[bold]\1[/bold]', rest)
            rest = re.sub(r'`([^`]+)`', r'[bright_cyan]\1[/bright_cyan]', rest)
            return f"[bold bright_green]{bold_part}[/bold bright_green]{rest}"
        
        # Bullet points
        if stripped.startswith('- ') or stripped.startswith('* '):
            bullet_text = stripped[2:]
            bullet_text = re.sub(r'\*\*(.+?)\*\*', r'[bold]\1[/bold]', bullet_text)
            bullet_text = re.sub(r'`([^`]+)`', r'[bright_cyan]\1[/bright_cyan]', bullet_text)
            return f"  [dim]•[/dim] {bullet_text}"
        
        # Numbered lists
        numbered = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if numbered:
            num = numbered.group(1)
            text = numbered.group(2)
            text = re.sub(r'\*\*(.+?)\*\*', r'[bold]\1[/bold]', text)
            text = re.sub(r'`([^`]+)`', r'[bright_cyan]\1[/bright_cyan]', text)
            return f"  [bright_cyan]{num}.[/bright_cyan] {text}"
        
        # Regular line - handle inline formatting
        formatted = stripped
        formatted = re.sub(r'\*\*(.+?)\*\*', r'[bold]\1[/bold]', formatted)
        formatted = re.sub(r'`([^`]+)`', r'[bright_cyan]\1[/bright_cyan]', formatted)
        
        return formatted
    
    def _print_table(self, lines: list[str]):
        """Print a markdown table as a Rich table."""
        if len(lines) < 2:
            return
        
        header_line = lines[0]
        headers = [h.strip() for h in header_line.split('|') if h.strip()]
        
        table = Table(box=ROUNDED, show_header=True, header_style="bold bright_cyan")
        for h in headers:
            table.add_column(h)
        
        for line in lines[2:]:
            if '---' in line:
                continue
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if cells:
                # Color code values
                colored_cells = []
                for cell in cells:
                    if cell.startswith('+') or cell.lower() in ['buy', 'bullish', 'strong buy']:
                        colored_cells.append(f"[green]{cell}[/green]")
                    elif cell.startswith('-') or cell.lower() in ['sell', 'bearish']:
                        colored_cells.append(f"[red]{cell}[/red]")
                    else:
                        colored_cells.append(cell)
                table.add_row(*colored_cells)
        
        console.print()
        console.print(Padding(table, (0, 2)))
    
    async def quick_chart(self, symbol: str, period: str = "3mo"):
        """Generate a quick chart."""
        from sigma.tools.charts import create_price_chart
        chart = create_price_chart(symbol, period)
        console.print()
        console.print(chart)
        console.print()
    
    async def quick_compare(self, symbols: list[str], period: str = "3mo"):
        """Generate a quick comparison chart."""
        from sigma.tools.charts import create_comparison_chart
        chart = create_comparison_chart(symbols, period)
        console.print()
        console.print(chart)
        console.print()
    
    def _handle_lean_command(self, args: list[str]):
        """Handle /lean commands for LEAN Engine backtesting."""
        from sigma.tools.backtest import setup_lean_engine, run_lean_backtest, check_lean_status, get_available_strategies
        
        if not args:
            # Show help menu
            strategies = get_available_strategies()
            console.print()
            console.print(Panel(
                "\n".join([
                    "[bold cyan]LEAN Engine Backtesting[/bold cyan]",
                    "",
                    "[bold]Commands:[/bold]",
                    "  /lean setup              - Setup LEAN Engine (one-time)",
                    "  /lean run <SYM> <STRAT>  - Run comprehensive backtest",
                    "  /lean status             - Check LEAN setup status",
                    "  /lean strategies         - List available strategies",
                    "",
                    "[bold]Quick Start:[/bold]",
                    "  /lean run AAPL sma_crossover",
                    "  /lean run TSLA macd_momentum",
                    "  /lean run NVDA rsi_mean_reversion",
                    "",
                    "[bold]Available Strategies:[/bold]",
                    *[f"  [cyan]{name}[/cyan] - {s['description'][:50]}..." for name, s in list(strategies.items())[:3]],
                    "  [dim]...use /lean strategies for full list[/dim]"
                ]),
                title="[bold bright_cyan]LEAN Backtest Engine[/bold bright_cyan]",
                border_style="bright_blue"
            ))
            console.print()
            return
        
        subcmd = args[0].lower()
        
        if subcmd == "help":
            self._handle_lean_command([])
            return
        
        if subcmd == "strategies":
            strategies = get_available_strategies()
            console.print()
            from rich.table import Table
            table = Table(title="Available Backtest Strategies", border_style="bright_blue")
            table.add_column("Strategy", style="cyan")
            table.add_column("Description", style="dim")
            table.add_column("Parameters", style="yellow")
            
            for name, s in strategies.items():
                params = ", ".join([f"{k}={v}" for k, v in s.get("default_params", {}).items()])
                table.add_row(name, s["description"][:60], params[:40])
            
            console.print(table)
            console.print()
            return
        
        if subcmd == "status":
            status = check_lean_status()
            console.print()
            console.print(Panel(
                "\n".join([
                    f"[dim]Docker Installed:[/dim] {'[green]Yes[/green]' if status['docker_installed'] else '[red]No[/red]'}",
                    f"[dim]Docker Running:[/dim] {'[green]Yes[/green]' if status['docker_running'] else '[red]No[/red]'}",
                    f"[dim]LEAN Image:[/dim] {'[green]Pulled[/green]' if status['lean_image_pulled'] else '[yellow]Not pulled[/yellow]'}",
                    f"[dim]Workspace:[/dim] {'[green]Ready[/green]' if status['workspace_initialized'] else '[yellow]Not initialized[/yellow]'}",
                    "",
                    *status['instructions']
                ]),
                title="[bold bright_cyan]LEAN Engine Status[/bold bright_cyan]",
                border_style="bright_blue"
            ))
            console.print()
            return
        
        if subcmd == "setup":
            console.print()
            console.print("[bright_cyan]Setting up LEAN Engine...[/bright_cyan]")
            console.print()
            
            result = setup_lean_engine()
            
            for step in result["steps_completed"]:
                console.print(f"  [green]✓[/green] {step}")
            
            for error in result.get("errors", []):
                console.print(f"  [red]✗[/red] {error}")
            
            console.print()
            if result["success"]:
                console.print(Panel(
                    "\n".join(result["next_steps"]),
                    title="[bold bright_green]Setup Complete[/bold bright_green]",
                    border_style="green"
                ))
            else:
                console.print(Panel(
                    "\n".join(result.get("next_steps", ["Setup failed. Check errors above."])),
                    title="[bold red]Setup Incomplete[/bold red]",
                    border_style="red"
                ))
            console.print()
        
        elif subcmd == "run":
            if len(args) < 3:
                console.print("\n  [red]Usage:[/red] /lean run <symbol> <strategy>\n")
                console.print("  [dim]Strategies:[/dim] sma_crossover, rsi_mean_reversion, macd_momentum, bollinger_bands, dual_momentum, breakout\n")
                return
            
            symbol = args[1].upper()
            strategy = args[2].lower()
            
            console.print()
            console.print(f"[bright_cyan]Running Comprehensive Backtest: {symbol} - {strategy}[/bright_cyan]")
            console.print()
            
            result = run_lean_backtest(symbol, strategy)
            
            for step in result["steps"]:
                console.print(f"  [dim]>[/dim] {step}")
            
            console.print()
            
            if result["status"] == "success":
                metrics = result.get("metrics", {})
                
                # Performance metrics panel
                perf = metrics.get("performance", {})
                console.print(Panel(
                    "\n".join([
                        f"  [bold cyan]Initial Capital:[/bold cyan]    {perf.get('initial_capital', 'N/A')}",
                        f"  [bold cyan]Final Equity:[/bold cyan]       {perf.get('final_equity', 'N/A')}",
                        f"  [bold cyan]Total Return:[/bold cyan]       {perf.get('total_return', 'N/A')}",
                        f"  [bold cyan]Annual Return:[/bold cyan]      {perf.get('annual_return', 'N/A')}",
                        f"  [bold cyan]Buy & Hold:[/bold cyan]         {perf.get('buy_hold_return', 'N/A')}",
                        f"  [bold cyan]Alpha:[/bold cyan]              {perf.get('alpha', 'N/A')}",
                    ]),
                    title=f"[bold bright_green]Performance - {symbol} {strategy}[/bold bright_green]",
                    border_style="green"
                ))
                
                # Risk metrics panel
                risk = metrics.get("risk", {})
                console.print(Panel(
                    "\n".join([
                        f"  [bold yellow]Max Drawdown:[/bold yellow]      {risk.get('max_drawdown', 'N/A')}",
                        f"  [bold yellow]Volatility:[/bold yellow]        {risk.get('volatility', 'N/A')}",
                        f"  [bold yellow]Sharpe Ratio:[/bold yellow]      {risk.get('sharpe_ratio', 'N/A')}",
                        f"  [bold yellow]Sortino Ratio:[/bold yellow]     {risk.get('sortino_ratio', 'N/A')}",
                        f"  [bold yellow]Calmar Ratio:[/bold yellow]      {risk.get('calmar_ratio', 'N/A')}",
                    ]),
                    title="[bold bright_yellow]Risk Metrics[/bold bright_yellow]",
                    border_style="yellow"
                ))
                
                # Trade statistics panel
                trades = metrics.get("trades", {})
                console.print(Panel(
                    "\n".join([
                        f"  [bold magenta]Total Trades:[/bold magenta]       {trades.get('total_trades', 'N/A')}",
                        f"  [bold magenta]Win Rate:[/bold magenta]           {trades.get('win_rate', 'N/A')}",
                        f"  [bold magenta]Profit Factor:[/bold magenta]      {trades.get('profit_factor', 'N/A')}",
                        f"  [bold magenta]Avg Win:[/bold magenta]            {trades.get('avg_win', 'N/A')}",
                        f"  [bold magenta]Avg Loss:[/bold magenta]           {trades.get('avg_loss', 'N/A')}",
                        f"  [bold magenta]Avg Holding:[/bold magenta]        {trades.get('avg_holding_days', 'N/A')} days",
                    ]),
                    title="[bold bright_magenta]Trade Statistics[/bold bright_magenta]",
                    border_style="magenta"
                ))
                
                # Display charts
                charts = result.get("charts", {})
                
                if charts.get("equity_curve"):
                    console.print()
                    console.print(charts["equity_curve"])
                
                if charts.get("drawdown"):
                    console.print()
                    console.print(charts["drawdown"])
                
                if charts.get("trade_pnl"):
                    console.print()
                    console.print(charts["trade_pnl"])
                
                if charts.get("monthly_returns"):
                    console.print()
                    console.print(charts["monthly_returns"])
                
                # Recent trades table
                trade_list = result.get("trades", [])
                if trade_list:
                    console.print()
                    from rich.table import Table
                    table = Table(title="Recent Trades", border_style="dim")
                    table.add_column("Date", style="dim")
                    table.add_column("Action", style="bold")
                    table.add_column("Price", justify="right")
                    table.add_column("Shares", justify="right")
                    table.add_column("P&L", justify="right")
                    
                    for trade in trade_list[-10:]:
                        action_style = "green" if trade.get("action") == "BUY" else "red"
                        pnl = trade.get("pnl")
                        pnl_str = f"${pnl:+,.2f}" if pnl else "-"
                        pnl_style = "green" if pnl and pnl > 0 else "red" if pnl else "dim"
                        table.add_row(
                            trade.get("date", ""),
                            f"[{action_style}]{trade.get('action', '')}[/{action_style}]",
                            f"${trade.get('price', 0):,.2f}",
                            str(trade.get("shares", "")),
                            f"[{pnl_style}]{pnl_str}[/{pnl_style}]"
                        )
                    console.print(table)
                
                # Monthly returns
                monthly = result.get("monthly_returns", [])
                if monthly:
                    console.print()
                    from rich.table import Table
                    mtable = Table(title="Monthly Returns", border_style="dim")
                    mtable.add_column("Month", style="dim")
                    mtable.add_column("Return", justify="right")
                    
                    for m in monthly[-12:]:
                        ret = m.get("return", 0)
                        ret_style = "green" if ret > 0 else "red"
                        mtable.add_row(m.get("month", ""), f"[{ret_style}]{ret:+.2f}%[/{ret_style}]")
                    console.print(mtable)
                
                # QuantConnect instructions
                console.print()
                console.print(Panel(
                    "\n".join(result.get("quantconnect_instructions", [])),
                    title="[bold bright_blue]QuantConnect Cloud (Institutional Data)[/bold bright_blue]",
                    border_style="blue"
                ))
                
            else:
                console.print(Panel(
                    f"[red]Error:[/red] {result.get('error', 'Unknown error')[:200]}",
                    title="[bold red]Backtest Failed[/bold red]",
                    border_style="red"
                ))
            
            # Always show the algorithm file location
            if result.get("algorithm_file"):
                console.print()
                console.print(f"  [dim]LEAN Algorithm saved:[/dim] {result['algorithm_file']}")
            console.print()
        
        elif subcmd == "status":
            self._handle_lean_command([])  # Same as no args
        
        else:
            console.print(f"\n  [red]Unknown lean command:[/red] {subcmd}")
            console.print("  [dim]Available:[/dim] /lean setup, /lean run <symbol> <strategy>, /lean status\n")

    def handle_command(self, cmd: str) -> bool:
        """Handle slash command. Returns True to continue, False to quit."""
        parts = cmd.strip().split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if command in ["/quit", "/exit", "/q"]:
            return False
        
        elif command in ["/help", "/h", "/?"]:
            print_help()
        
        elif command == "/model":
            if not args:
                available = self.settings.get_available_providers()
                console.print()
                console.print(f"  [dim]Current model:[/dim] [bright_cyan]{self._get_model_display()}[/bright_cyan]")
                console.print(f"  [dim]Available:[/dim] {', '.join(p.value for p in available)}")
                console.print()
            else:
                try:
                    self.provider = LLMProvider(args[0].lower())
                    self.agent = None
                    console.print(f"\n  [bright_green]✓[/bright_green] Switched to [bright_cyan]{self._get_model_display()}[/bright_cyan]\n")
                except ValueError:
                    console.print(f"\n  [red]✗[/red] Unknown provider: {args[0]}\n")
        
        elif command == "/mode":
            if not args:
                console.print()
                console.print(f"  [dim]Current mode:[/dim] [bright_cyan]{self.mode}[/bright_cyan]")
                console.print(f"  [dim]Available:[/dim] default, technical, fundamental, quant")
                console.print()
            else:
                mode = args[0].lower()
                if mode in ["default", "technical", "fundamental", "quant"]:
                    self.mode = mode
                    console.print(f"\n  [bright_green]✓[/bright_green] Switched to [bright_cyan]{mode}[/bright_cyan] mode\n")
                else:
                    console.print(f"\n  [red]✗[/red] Unknown mode: {mode}\n")
        
        elif command == "/clear":
            if self.agent:
                self.agent.clear()
            console.print("\n  [bright_green]✓[/bright_green] Conversation cleared\n")
        
        elif command == "/status":
            console.print()
            console.print(f"  [dim]Provider:[/dim] [bright_cyan]{self.provider.value}[/bright_cyan]")
            console.print(f"  [dim]Model:[/dim] [bright_cyan]{self._get_model_display()}[/bright_cyan]")
            console.print(f"  [dim]Mode:[/dim] [bright_cyan]{self.mode}[/bright_cyan]")
            available = self.settings.get_available_providers()
            console.print(f"  [dim]Available providers:[/dim] {', '.join(p.value for p in available)}")
            if self.agent:
                stats = self.agent.get_stats()
                console.print(f"  [dim]Tools called this session:[/dim] {stats['tools_called']}")
            console.print()
        
        elif command == "/chart":
            if not args:
                console.print("\n  [red]Usage:[/red] /chart <symbol> [period]\n")
            else:
                symbol = args[0].upper()
                period = args[1] if len(args) > 1 else "3mo"
                try:
                    asyncio.get_event_loop().run_until_complete(self.quick_chart(symbol, period))
                except RuntimeError:
                    asyncio.run(self.quick_chart(symbol, period))
        
        elif command == "/compare":
            if len(args) < 2:
                console.print("\n  [red]Usage:[/red] /compare <symbol1> <symbol2> ...\n")
            else:
                symbols = [s.upper() for s in args[:5]]
                try:
                    asyncio.get_event_loop().run_until_complete(self.quick_compare(symbols))
                except RuntimeError:
                    asyncio.run(self.quick_compare(symbols))
        
        elif command == "/backtest":
            if len(args) < 2:
                console.print("\n  [red]Usage:[/red] /backtest <symbol> <strategy>\n")
                console.print("  [dim]Strategies:[/dim] sma_crossover, rsi_mean_reversion, macd_momentum, bollinger_bands, dual_momentum, breakout\n")
            else:
                symbol = args[0]
                strategy = args[1]
                try:
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(
                        self.process_query(f"Generate a {strategy} backtest for {symbol}")
                    )
                except RuntimeError:
                    asyncio.run(
                        self.process_query(f"Generate a {strategy} backtest for {symbol}")
                    )
        
        elif command == "/lean":
            self._handle_lean_command(args)
        
        else:
            console.print(f"\n  [red]Unknown command:[/red] {command}. Type /help for commands.\n")
        
        return True
    
    async def run(self):
        """Run the interactive loop."""
        print_banner(self._get_model_display())
        
        while True:
            try:
                # Professional prompt
                prompt_line = f"[bold bright_yellow]σ[/bold bright_yellow] [dim]›[/dim] "
                query = console.input(prompt_line).strip()
                
                if not query:
                    continue
                
                # Handle commands
                if query.startswith("/"):
                    if not self.handle_command(query):
                        console.print("\n  [dim]Goodbye! May your trades be ever profitable.[/dim] 📈\n")
                        break
                    continue
                
                # Process query
                await self.process_query(query)
                
            except KeyboardInterrupt:
                console.print("\n")
                continue
            except EOFError:
                console.print("\n  [dim]Goodbye! May your trades be ever profitable.[/dim] 📈\n")
                break
            except Exception as e:
                console.print(f"\n  [red]Error:[/red] {str(e)}\n")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        prog="sigma",
        description="Sigma - Institutional-Grade Financial Research Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sigma                    Start interactive mode
  sigma --setup            Run setup wizard
  sigma "Analyze AAPL"     Direct query mode
  sigma --version          Show version

Inside Sigma:
  /help                    Show all commands
  /model openai            Switch to OpenAI
  /lean run TSLA macd      Run backtest
        """
    )
    
    parser.add_argument(
        "query",
        nargs="?",
        help="Direct query to analyze (optional)"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run the setup wizard"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset configuration and run setup"
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"Sigma {VERSION}"
    )
    parser.add_argument(
        "--model", "-m",
        choices=["openai", "anthropic", "google", "groq", "xai", "ollama"],
        help="Override default AI model"
    )
    
    args = parser.parse_args()
    
    # Handle setup
    from sigma.setup import ensure_setup, run_setup, is_setup_complete, CONFIG_DIR
    import shutil
    
    if args.reset:
        if CONFIG_DIR.exists():
            shutil.rmtree(CONFIG_DIR)
        run_setup(force=True)
    elif args.setup:
        run_setup(force=True)
    else:
        # Ensure setup is done
        ensure_setup()
    
    # Create UI with optional model override
    ui = SigmaUI()
    if args.model:
        try:
            ui.provider = LLMProvider(args.model)
            ui.agent = None  # Force agent reload
        except ValueError:
            pass
    
    # Handle direct query or interactive mode
    if args.query:
        # Direct query mode
        async def run_query():
            print_banner(ui._get_model_display())
            await ui.process_query(args.query)
        
        try:
            asyncio.run(run_query())
        except KeyboardInterrupt:
            console.print("\n")
    else:
        # Interactive mode
        try:
            asyncio.run(ui.run())
        except KeyboardInterrupt:
            console.print("\n  [dim]Goodbye! May your trades be ever profitable.[/dim]\n")


if __name__ == "__main__":
    main()
