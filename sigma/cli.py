"""CLI entry point for Sigma v3.2.0."""

import argparse
import json
import sys
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .app import launch
from .config import get_settings, save_api_key, save_setting, AVAILABLE_MODELS, LLMProvider


__version__ = "3.2.0"

console = Console()


def show_banner():
    """Show the Sigma banner."""
    banner = """
[bold white]███████╗██╗ ██████╗ ███╗   ███╗ █████╗ [/bold white]
[bold white]██╔════╝██║██╔════╝ ████╗ ████║██╔══██╗[/bold white]
[bold white]███████╗██║██║  ███╗██╔████╔██║███████║[/bold white]
[bold white]╚════██║██║██║   ██║██║╚██╔╝██║██╔══██║[/bold white]
[bold white]███████║██║╚██████╔╝██║ ╚═╝ ██║██║  ██║[/bold white]
[bold white]╚══════╝╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝[/bold white]

[dim]v3.2.0[/dim] [bold cyan]σ[/bold cyan] [bold]Finance Research Agent[/bold]
"""
    console.print(banner)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="sigma",
        description="Sigma v3.2.0 - Finance Research Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sigma                          # Launch interactive app
  sigma ask "analyze AAPL"       # Quick query
  sigma quote AAPL GOOGL MSFT    # Get quotes
  sigma --setup                  # Run setup wizard
        """
    )
    
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Show version and exit"
    )
    
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run the setup wizard"
    )
    
    parser.add_argument(
        "--setkey",
        nargs=2,
        metavar=("PROVIDER", "KEY"),
        help="Set API key for provider (google, openai, anthropic, groq, xai)"
    )
    
    parser.add_argument(
        "--provider",
        choices=["google", "openai", "anthropic", "groq", "xai", "ollama"],
        help="Set default AI provider"
    )
    
    parser.add_argument(
        "--model",
        help="Set default model"
    )
    
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current configuration"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Ask command
    ask_parser = subparsers.add_parser("ask", help="Ask a question")
    ask_parser.add_argument("query", nargs="+", help="Your question")
    
    # Quote command
    quote_parser = subparsers.add_parser("quote", help="Get stock quotes")
    quote_parser.add_argument("symbols", nargs="+", help="Stock symbols")
    
    # Chart command
    chart_parser = subparsers.add_parser("chart", help="Generate a chart")
    chart_parser.add_argument("symbol", help="Stock symbol")
    chart_parser.add_argument("--period", default="6mo", help="Time period (default: 6mo)")
    chart_parser.add_argument("--output", "-o", help="Output file path")
    
    # Backtest command
    backtest_parser = subparsers.add_parser("backtest", help="Run a backtest")
    backtest_parser.add_argument("symbol", help="Stock symbol")
    backtest_parser.add_argument("--strategy", "-s", default="sma_crossover", 
                                 help="Strategy name (default: sma_crossover)")
    backtest_parser.add_argument("--period", default="1y", help="Time period (default: 1y)")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare stocks")
    compare_parser.add_argument("symbols", nargs="+", help="Stock symbols to compare")
    
    args = parser.parse_args()
    
    if args.version:
        show_banner()
        return 0
    
    if args.setup:
        from .setup import run_setup
        return 0 if run_setup() else 1
    
    if args.list_models:
        console.print("\n[bold]Available Models by Provider:[/bold]\n")
        for provider, models in AVAILABLE_MODELS.items():
            console.print(f"  [cyan]{provider}:[/cyan]")
            for model in models:
                console.print(f"    • {model}")
        return 0
    
    if args.status:
        settings = get_settings()
        
        table = Table(title="Sigma Configuration", show_header=False)
        table.add_column("Setting", style="bold")
        table.add_column("Value")
        
        table.add_row("Provider", settings.default_provider.value if hasattr(settings.default_provider, 'value') else str(settings.default_provider))
        table.add_row("Model", settings.default_model)
        table.add_row("", "")
        table.add_row("API Keys", "")
        table.add_row("  Google", "[green]OK[/green]" if settings.google_api_key else "[red]--[/red]")
        table.add_row("  OpenAI", "[green]OK[/green]" if settings.openai_api_key else "[red]--[/red]")
        table.add_row("  Anthropic", "[green]OK[/green]" if settings.anthropic_api_key else "[red]--[/red]")
        table.add_row("  Groq", "[green]OK[/green]" if settings.groq_api_key else "[red]--[/red]")
        table.add_row("  xAI", "[green]OK[/green]" if settings.xai_api_key else "[red]--[/red]")
        
        console.print(table)
        return 0
    
    if args.setkey:
        provider, key = args.setkey
        provider = provider.lower()
        
        try:
            provider_enum = LLMProvider(provider)
            save_api_key(provider_enum, key)
            console.print(f"[bold cyan]σ[/bold cyan] API key for {provider} saved.")
            return 0
        except ValueError:
            console.print(f"[red]Error:[/red] Unknown provider '{provider}'")
            console.print(f"Valid providers: google, openai, anthropic, groq, xai")
            return 1
    
    if args.provider or args.model:
        if args.provider:
            save_setting("default_provider", args.provider)
            console.print(f"[bold cyan]σ[/bold cyan] Default provider: {args.provider}")
        
        if args.model:
            save_setting("default_model", args.model)
            console.print(f"[bold cyan]σ[/bold cyan] Default model: {args.model}")
        
        return 0
    
    # Handle subcommands
    if args.command == "ask":
        query = " ".join(args.query)
        return handle_ask(query)
    
    elif args.command == "quote":
        return handle_quotes(args.symbols)
    
    elif args.command == "chart":
        return handle_chart(args.symbol, args.period, args.output)
    
    elif args.command == "backtest":
        return handle_backtest(args.symbol, args.strategy, args.period)
    
    elif args.command == "compare":
        return handle_compare(args.symbols)
    
    # Default: Launch the app
    launch()
    return 0


def handle_ask(query: str) -> int:
    """Handle ask command."""
    import asyncio
    from .llm import get_llm
    from .tools import TOOLS, execute_tool
    
    settings = get_settings()
    
    console.print(f"\n[dim]Using {settings.default_provider.value} / {settings.default_model}[/dim]\n")
    
    try:
        llm = get_llm(settings.default_provider, settings.default_model)
        
        async def run_query():
            """Run the query asynchronously."""
            messages = [
                {"role": "system", "content": "You are Sigma, a helpful financial intelligence assistant. Use the tools available to provide accurate, data-driven insights."},
                {"role": "user", "content": query}
            ]
            
            async def handle_tool(name: str, args: dict):
                """Handle tool calls."""
                console.print(f"[dim]Executing: {name}[/dim]")
                return execute_tool(name, args)
            
            response = await llm.generate(messages, TOOLS, handle_tool)
            return response
        
        with console.status("[bold blue]σ analyzing...[/bold blue]"):
            response = asyncio.run(run_query())
        
        console.print(Panel(response, title="[bold cyan]σ Sigma[/bold cyan]"))
        return 0
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1


def handle_quotes(symbols: list) -> int:
    """Handle quote command."""
    from .tools import get_stock_quote
    
    table = Table(title="Stock Quotes")
    table.add_column("Symbol", style="cyan")
    table.add_column("Price", justify="right")
    table.add_column("Change", justify="right")
    table.add_column("Change %", justify="right")
    table.add_column("Volume", justify="right")
    
    for symbol in symbols:
        quote = get_stock_quote(symbol)
        
        if "error" in quote:
            table.add_row(symbol, "[red]Error[/red]", "-", "-", "-")
            continue
        
        change = quote.get("change", 0)
        change_pct = quote.get("change_percent", 0)
        change_style = "green" if change >= 0 else "red"
        
        table.add_row(
            quote.get("symbol", symbol),
            f"${quote.get('price', 0):,.2f}",
            f"[{change_style}]{change:+.2f}[/{change_style}]",
            f"[{change_style}]{change_pct:+.2f}%[/{change_style}]",
            f"{quote.get('volume', 0):,}",
        )
    
    console.print(table)
    return 0


def handle_chart(symbol: str, period: str, output: Optional[str] = None) -> int:
    """Handle chart command."""
    from .charts import create_candlestick_chart
    import yfinance as yf
    
    with console.status(f"[bold blue]Generating chart for {symbol}...[/bold blue]"):
        try:
            ticker = yf.Ticker(symbol.upper())
            hist = ticker.history(period=period)
            
            if hist.empty:
                console.print(f"[red]Error:[/red] No data found for {symbol}")
                return 1
            
            filepath = create_candlestick_chart(symbol, hist)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            return 1
    
    console.print(f"[bold cyan]σ[/bold cyan] Chart saved to: {filepath}")
    
    # Try to open the chart
    import subprocess
    try:
        subprocess.run(["open", filepath], check=True)
    except Exception:
        pass
    
    return 0


def handle_backtest(symbol: str, strategy: str, period: str) -> int:
    """Handle backtest command."""
    from .backtest import run_backtest, get_available_strategies
    
    strategies = get_available_strategies()
    
    if strategy not in strategies:
        console.print(f"[red]Error:[/red] Unknown strategy '{strategy}'")
        console.print(f"Available: {', '.join(strategies.keys())}")
        return 1
    
    with console.status(f"[bold blue]Running backtest: {strategy} on {symbol}...[/bold blue]"):
        result = run_backtest(symbol, strategy, period)
    
    if "error" in result:
        console.print(f"[red]Error:[/red] {result['error']}")
        return 1
    
    # Display results
    console.print()
    console.print(Panel(
        f"[bold]{result.get('strategy', strategy.upper())}[/bold]\n"
        f"[dim]{result.get('strategy_description', '')}[/dim]",
        title=f"[bold cyan]Backtest: {symbol.upper()}[/bold cyan]",
    ))
    
    # Performance table
    perf = result.get("performance", {})
    table = Table(title="Performance", show_header=False)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    
    table.add_row("Initial Capital", perf.get("initial_capital", "$100,000"))
    table.add_row("Final Equity", perf.get("final_equity", "N/A"))
    table.add_row("Total Return", perf.get("total_return", "N/A"))
    table.add_row("Annual Return", perf.get("annual_return", "N/A"))
    table.add_row("Buy & Hold Return", perf.get("buy_hold_return", "N/A"))
    table.add_row("Alpha", perf.get("alpha", "N/A"))
    
    console.print(table)
    
    # Risk table
    risk = result.get("risk", {})
    risk_table = Table(title="Risk Metrics", show_header=False)
    risk_table.add_column("Metric", style="bold")
    risk_table.add_column("Value", justify="right")
    
    risk_table.add_row("Volatility", risk.get("volatility", "N/A"))
    risk_table.add_row("Max Drawdown", risk.get("max_drawdown", "N/A"))
    risk_table.add_row("Sharpe Ratio", risk.get("sharpe_ratio", "N/A"))
    risk_table.add_row("Sortino Ratio", risk.get("sortino_ratio", "N/A"))
    risk_table.add_row("Calmar Ratio", risk.get("calmar_ratio", "N/A"))
    
    console.print(risk_table)
    
    # Trade stats
    trades = result.get("trades", {})
    trade_table = Table(title="Trade Statistics", show_header=False)
    trade_table.add_column("Metric", style="bold")
    trade_table.add_column("Value", justify="right")
    
    trade_table.add_row("Total Trades", str(trades.get("total_trades", 0)))
    trade_table.add_row("Win Rate", trades.get("win_rate", "N/A"))
    trade_table.add_row("Profit Factor", trades.get("profit_factor", "N/A"))
    trade_table.add_row("Avg Win", trades.get("avg_win", "N/A"))
    trade_table.add_row("Avg Loss", trades.get("avg_loss", "N/A"))
    
    console.print(trade_table)
    
    return 0


def handle_compare(symbols: list) -> int:
    """Handle compare command."""
    from .tools import compare_stocks
    
    with console.status(f"[bold blue]Comparing {', '.join(symbols)}...[/bold blue]"):
        result = compare_stocks(symbols)
    
    if "error" in result:
        console.print(f"[red]Error:[/red] {result['error']}")
        return 1
    
    comparison = result.get("comparison", [])
    
    if not comparison:
        console.print("[yellow]No data found for the specified symbols[/yellow]")
        return 1
    
    # Display comparison table
    table = Table(title=f"Stock Comparison ({result.get('period', '1y')})")
    table.add_column("Symbol", style="cyan")
    table.add_column("Name", style="dim")
    table.add_column("Price", justify="right")
    table.add_column("Return", justify="right")
    table.add_column("Volatility", justify="right")
    table.add_column("Sharpe", justify="right")
    table.add_column("P/E", justify="right")
    
    for stock in comparison:
        return_val = stock.get("total_return", 0)
        return_style = "green" if return_val >= 0 else "red"
        
        table.add_row(
            stock.get("symbol", ""),
            stock.get("name", "N/A")[:20],
            f"${stock.get('price', 0):,.2f}",
            f"[{return_style}]{return_val:+.2f}%[/{return_style}]",
            f"{stock.get('volatility', 0):.1f}%",
            f"{stock.get('sharpe', 0):.2f}",
            str(stock.get("pe_ratio", "N/A")),
        )
    
    console.print(table)
    
    # Summary
    console.print()
    console.print(f"[green]Best:[/green] {result.get('best_performer', 'N/A')}")
    console.print(f"[red]Worst:[/red] {result.get('worst_performer', 'N/A')}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
