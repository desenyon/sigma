"""CLI entry point for Ephemeral v3.8.0 — Rich UX layer over the TUI and one-shot commands."""

from __future__ import annotations

import argparse
import asyncio
import shutil
import sys
from typing import Optional

from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from .app import launch
from .cli_ui import (
    make_console,
    open_file_cross_platform,
    print_banner,
    print_status_dashboard,
    run_doctor,
)
from .config import (
    AVAILABLE_MODELS,
    detect_lean_installation,
    detect_ollama,
    get_settings,
    is_first_run,
    mark_first_run_complete,
    save_api_key,
    save_setting,
)
from .ink_launcher import launch_ink_ui
from .version import VERSION

__version__ = VERSION


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ephemeral",
        description="Ephemeral — terminal-native finance research (TUI + one-shot commands).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  ephemeral                         # Interactive CLI (Ink by default)\n"
            "  ephemeral --legacy-ui             # Launch the legacy Textual UI\n"
            "  ephemeral ask \"Summarize AAPL risk factors\"\n"
            "  ephemeral quote NVDA AMD\n"
            "  ephemeral chart SPY --period 1y -o /tmp/spy.png\n"
            "  ephemeral doctor                  # Health check\n"
            "  ephemeral news AAPL               # Unified headline digest\n"
            "  ephemeral tools                   # List LLM tool names\n"
            "  ephemeral --status                # Config + services\n"
        ),
    )

    parser.add_argument(
        "--version",
        "-v",
        action="store_true",
        help="Show version and exit",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run the interactive setup wizard",
    )
    parser.add_argument(
        "--setkey",
        nargs=2,
        metavar=("PROVIDER", "KEY"),
        help="Set API key (google, openai, anthropic, groq, xai, polygon, alphavantage, exa)",
    )
    parser.add_argument(
        "--provider",
        choices=["google", "openai", "anthropic", "groq", "xai", "ollama"],
        help="Set default AI provider",
    )
    parser.add_argument(
        "--model",
        help="Set default model id",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List bundled model suggestions by provider",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show configuration, connectivity, and key status",
    )
    parser.add_argument(
        "--no-ui",
        action="store_true",
        help="With --version: print plain text only (no Rich banner)",
    )
    parser.add_argument(
        "--legacy-ui",
        action="store_true",
        help="Launch the legacy Textual interface instead of Ink",
    )
    parser.add_argument(
        "--ink-ui",
        action="store_true",
        help="Force the Ink interface even if Ephemeral would otherwise fall back",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND", help="Subcommands")

    ask_p = subparsers.add_parser("ask", help="Ask the LLM with tools (non-interactive)")
    ask_p.add_argument("query", nargs="+", help="Question / prompt")

    quote_p = subparsers.add_parser("quote", help="Fetch stock quotes")
    quote_p.add_argument("symbols", nargs="+", help="Ticker symbols")

    chart_p = subparsers.add_parser("chart", help="Generate a candlestick chart (saved under ~/.ephemeral/charts)")
    chart_p.add_argument("symbol", help="Ticker symbol")
    chart_p.add_argument("--period", default="6mo", help="yfinance period (default: 6mo)")
    chart_p.add_argument(
        "--output",
        "-o",
        help="Optional path to copy the rendered PNG to",
    )

    bt_p = subparsers.add_parser("backtest", help="Run the built-in yfinance backtest engine")
    bt_p.add_argument("symbol", help="Ticker symbol")
    bt_p.add_argument(
        "--strategy",
        "-s",
        default="sma_crossover",
        help="Strategy id (default: sma_crossover)",
    )
    bt_p.add_argument("--period", default="1y", help="History window (default: 1y)")

    cmp_p = subparsers.add_parser("compare", help="Compare symbols (returns, vol, Sharpe, …)")
    cmp_p.add_argument("symbols", nargs="+", help="Tickers to compare")

    subparsers.add_parser("doctor", help="Verify Python deps, binaries, and API key presence")

    news_p = subparsers.add_parser("news", help="Unified news digest for a ticker (Polygon / AV / Exa / Yahoo)")
    news_p.add_argument("symbol", help="Ticker symbol")
    news_p.add_argument(
        "-n",
        "--limit",
        type=int,
        default=10,
        help="Max headlines (default: 10)",
    )

    subparsers.add_parser("tools", help="List tool names available to the LLM")

    return parser


def _launch_interactive_ui(console, *, force_legacy: bool = False, force_ink: bool = False) -> int:
    if force_legacy:
        launch()
        return 0

    ink_exit = launch_ink_ui()
    if ink_exit == 0:
        return 0

    if force_ink:
        return ink_exit

    console.print(
        "\n[yellow]Ink UI is unavailable right now.[/yellow] Falling back to the legacy Textual interface.\n"
    )
    launch()
    return 0


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    console = make_console()

    if args.version:
        if args.no_ui:
            print(f"ephemeral {__version__}")
            return 0
        print_banner(console, __version__)
        return 0

    if args.setup:
        from .setup_agent import run_setup

        result = run_setup()
        if result:
            mark_first_run_complete()
            from rich.prompt import Confirm

            if Confirm.ask("\n[bold cyan]E[/bold cyan] Launch Ephemeral now?", default=True):
                return _launch_interactive_ui(
                    console,
                    force_legacy=args.legacy_ui,
                    force_ink=args.ink_ui,
                )
        return 0 if result else 1

    if is_first_run():
        console.print("\n[bold cyan]E[/bold cyan] [bold]Welcome to Ephemeral[/bold]")
        console.print("[dim]First run — starting the setup wizard…[/dim]\n")
        from .setup_agent import run_setup

        result = run_setup()
        mark_first_run_complete()

        if result:
            console.print("\n[bold green]Setup complete.[/bold green] [dim]Launching…[/dim]\n")
            import time

            time.sleep(1)
            return _launch_interactive_ui(
                console,
                force_legacy=args.legacy_ui,
                force_ink=args.ink_ui,
            )

        console.print("\n[yellow]Setup skipped.[/yellow] Run [bold]ephemeral --setup[/bold] anytime.\n")
        return _launch_interactive_ui(
            console,
            force_legacy=args.legacy_ui,
            force_ink=args.ink_ui,
        )

    if args.list_models:
        console.print("\n[bold]Models (reference list by provider)[/bold]\n")
        for provider, models in AVAILABLE_MODELS.items():
            console.print(f"  [cyan]{provider}[/cyan]")
            for model in models:
                console.print(f"    • {model}")
        return 0

    if args.status:
        settings = get_settings()
        print_status_dashboard(console, settings, detect_ollama=detect_ollama, detect_lean_installation=detect_lean_installation)
        return 0

    if args.setkey:
        provider, key = args.setkey
        provider = provider.lower()
        if not save_api_key(provider, key):
            console.print(f"[red]Error:[/red] Unknown provider '{provider}'")
            console.print("[dim]Valid: google, openai, anthropic, groq, xai, polygon, alphavantage, exa[/dim]")
            return 1
        console.print(f"[bold cyan]E[/bold cyan] Saved credentials for [bold]{provider}[/bold].")
        return 0

    if args.provider or args.model:
        if args.provider:
            save_setting("default_provider", args.provider)
            console.print(f"[bold cyan]E[/bold cyan] Default provider → [bold]{args.provider}[/bold]")
        if args.model:
            save_setting("default_model", args.model)
            console.print(f"[bold cyan]E[/bold cyan] Default model → [bold]{args.model}[/bold]")
        return 0

    if args.command == "ask":
        return handle_ask(console, " ".join(args.query))

    if args.command == "quote":
        return handle_quotes(console, args.symbols)

    if args.command == "chart":
        return handle_chart(console, args.symbol, args.period, args.output)

    if args.command == "backtest":
        return handle_backtest(console, args.symbol, args.strategy, args.period)

    if args.command == "compare":
        return handle_compare(console, args.symbols)

    if args.command == "doctor":
        settings = get_settings()
        return run_doctor(console, settings)

    if args.command == "news":
        from json import dumps

        from .tools.library import fetch_news_digest

        r = fetch_news_digest(symbol=args.symbol.upper(), limit=args.limit)
        console.print(dumps(r, indent=2))
        if r.get("articles"):
            return 0
        return 1

    if args.command == "tools":
        from .tools.registry import TOOL_REGISTRY

        for name in sorted(TOOL_REGISTRY.get_tool_names()):
            console.print(f"  {name}")
        return 0

    return _launch_interactive_ui(
        console,
        force_legacy=args.legacy_ui,
        force_ink=args.ink_ui,
    )


def handle_ask(console, query: str) -> int:
    from .app import SYSTEM_PROMPT
    from .llm import get_router
    from .llm.tool_guidance import USER_TOOL_NUDGE, build_augmented_system_prompt
    from .tools import execute_tool, get_tools_for_llm
    from .tools.registry import TOOL_REGISTRY

    settings = get_settings()
    console.print(f"\n[dim]Model:[/dim] [bold]{settings.default_model}[/bold]\n")

    try:
        router = get_router(settings)

        async def run_query():
            user_text = query
            if settings.ephemeral_aggressive_tools:
                user_text = query + USER_TOOL_NUDGE
            messages = [
                {
                    "role": "system",
                    "content": build_augmented_system_prompt(SYSTEM_PROMPT, TOOL_REGISTRY),
                },
                {"role": "user", "content": user_text},
            ]

            async def handle_tool(name: str, args: dict):
                console.print(f"[dim]tool[/dim] [bold]{name}[/bold]")
                return execute_tool(name, args)

            return await router.chat(
                messages,
                tools=get_tools_for_llm(),
                on_tool_call=handle_tool,
                stream=False,
            )

        with console.status("[bold blue]Ephemeral analyzing…[/bold blue]"):
            response = asyncio.run(run_query())

        console.print(Panel(Markdown(str(response)), title="[bold cyan]Ephemeral[/bold cyan]", border_style="cyan"))
        return 0

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1


def handle_quotes(console, symbols: list) -> int:
    from .tools import get_stock_quote

    table = Table(title="Quotes", show_lines=True, border_style="cyan")
    table.add_column("Symbol", style="cyan")
    table.add_column("Price", justify="right")
    table.add_column("Change", justify="right")
    table.add_column("Change %", justify="right")
    table.add_column("Volume", justify="right")

    for symbol in symbols:
        quote = get_stock_quote(symbol)

        if "error" in quote:
            table.add_row(symbol, "[red]Error[/red]", "—", "—", "—")
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


def handle_chart(console, symbol: str, period: str, output: Optional[str]) -> int:
    import yfinance as yf

    from .charts import create_candlestick_chart

    with console.status(f"[bold blue]Fetching {symbol} ({period})…[/bold blue]"):
        try:
            ticker = yf.Ticker(symbol.upper())
            hist = ticker.history(period=period)

            if hist.empty:
                console.print(f"[red]Error:[/red] No data for {symbol}")
                return 1

            filepath = create_candlestick_chart(symbol, hist)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            return 1

    dest = filepath
    if output:
        shutil.copy2(filepath, output)
        dest = output

    console.print(f"[bold cyan]E[/bold cyan] Chart written to: [bold]{dest}[/bold]")
    open_file_cross_platform(dest)
    return 0


def handle_backtest(console, symbol: str, strategy: str, period: str) -> int:
    from .backtest import get_available_strategies, run_backtest

    strategies = get_available_strategies()

    if strategy not in strategies:
        console.print(f"[red]Error:[/red] Unknown strategy '{strategy}'")
        console.print(f"Available: {', '.join(strategies.keys())}")
        return 1

    with console.status(f"[bold blue]Backtest {strategy} on {symbol}…[/bold blue]"):
        result = run_backtest(symbol, strategy, period)

    if "error" in result:
        console.print(f"[red]Error:[/red] {result['error']}")
        return 1

    console.print()
    console.print(
        Panel(
            f"[bold]{result.get('strategy', strategy.upper())}[/bold]\n"
            f"[dim]{result.get('strategy_description', '')}[/dim]",
            title=f"[bold cyan]Backtest · {symbol.upper()}[/bold cyan]",
            border_style="cyan",
        )
    )

    perf = result.get("performance", {})
    table = Table(title="Performance", show_header=False, border_style="dim")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Initial Capital", perf.get("initial_capital", "$100,000"))
    table.add_row("Final Equity", perf.get("final_equity", "N/A"))
    table.add_row("Total Return", perf.get("total_return", "N/A"))
    table.add_row("Annual Return", perf.get("annual_return", "N/A"))
    table.add_row("Buy & Hold Return", perf.get("buy_hold_return", "N/A"))
    table.add_row("Alpha", perf.get("alpha", "N/A"))
    console.print(table)

    risk = result.get("risk", {})
    risk_table = Table(title="Risk", show_header=False, border_style="dim")
    risk_table.add_column("Metric", style="bold")
    risk_table.add_column("Value", justify="right")
    risk_table.add_row("Volatility", risk.get("volatility", "N/A"))
    risk_table.add_row("Max Drawdown", risk.get("max_drawdown", "N/A"))
    risk_table.add_row("Sharpe Ratio", risk.get("sharpe_ratio", "N/A"))
    risk_table.add_row("Sortino Ratio", risk.get("sortino_ratio", "N/A"))
    risk_table.add_row("Calmar Ratio", risk.get("calmar_ratio", "N/A"))
    console.print(risk_table)

    trades = result.get("trades", {})
    trade_table = Table(title="Trades", show_header=False, border_style="dim")
    trade_table.add_column("Metric", style="bold")
    trade_table.add_column("Value", justify="right")
    trade_table.add_row("Total Trades", str(trades.get("total_trades", 0)))
    trade_table.add_row("Win Rate", trades.get("win_rate", "N/A"))
    trade_table.add_row("Profit Factor", trades.get("profit_factor", "N/A"))
    trade_table.add_row("Avg Win", trades.get("avg_win", "N/A"))
    trade_table.add_row("Avg Loss", trades.get("avg_loss", "N/A"))
    console.print(trade_table)

    return 0


def handle_compare(console, symbols: list) -> int:
    from .tools import compare_stocks

    with console.status(f"[bold blue]Comparing {', '.join(symbols)}…[/bold blue]"):
        result = compare_stocks(symbols)

    if "error" in result:
        console.print(f"[red]Error:[/red] {result['error']}")
        return 1

    comparison = result.get("comparison", [])

    if not comparison:
        console.print("[yellow]No data for those symbols.[/yellow]")
        return 1

    table = Table(title=f"Comparison · {result.get('period', '1y')}", border_style="cyan")
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
            str(stock.get("name", "N/A"))[:22],
            f"${stock.get('price', 0):,.2f}",
            f"[{return_style}]{return_val:+.2f}%[/{return_style}]",
            f"{stock.get('volatility', 0):.1f}%",
            f"{stock.get('sharpe', 0):.2f}",
            str(stock.get("pe_ratio", "N/A")),
        )

    console.print(table)
    console.print()
    console.print(f"[green]Best:[/green] {result.get('best_performer', 'N/A')}")
    console.print(f"[red]Worst:[/red] {result.get('worst_performer', 'N/A')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
