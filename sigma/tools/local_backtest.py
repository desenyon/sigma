
"""Local backtesting tool using simple engine."""

from ..backtest.simple_engine import run_backtest, STRATEGIES
from .registry import TOOL_REGISTRY

@TOOL_REGISTRY.register(
    name="run_local_backtest",
    description="Run a local backtest using yfinance data. Supports: sma_crossover, rsi_mean_reversion, macd_momentum, bollinger_bands, pairs_trading.",
)
def run_local_backtest(
    symbol: str,
    strategy: str,
    period: str = "2y",
    initial_capital: float = 100000,
    params: dict = None,
    transaction_cost_pct: float = 0.001
) -> dict:
    """
    Run a simulation backtest locally.
    
    Args:
        symbol: Ticker symbol (e.g. "AAPL", "BTC-USD")
        strategy: Strategy name (sma_crossover, rsi_mean_reversion, macd_momentum, bollinger_bands, pairs_trading)
        period: Time period (1y, 2y, 5y, max)
        initial_capital: Starting cash
        params: Strategy parameters (optional)
        transaction_cost_pct: Transaction cost as decimal (0.001 = 0.1%)
    """
    return run_backtest(
        symbol=symbol,
        strategy=strategy,
        period=period,
        initial_capital=initial_capital,
        params=params,
        transaction_cost_pct=transaction_cost_pct
    )

@TOOL_REGISTRY.register(
    name="list_backtest_strategies",
    description="List available local backtest strategies and their parameters."
)
def list_backtest_strategies() -> dict:
    """List available strategies."""
    return STRATEGIES
