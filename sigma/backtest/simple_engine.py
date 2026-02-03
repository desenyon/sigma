"""Backtesting engine for Sigma."""

import json
from datetime import datetime, timedelta
from typing import Any, Optional

import numpy as np
import pandas as pd
import yfinance as yf


# ============================================================================
# BACKTEST STRATEGIES
# ============================================================================

STRATEGIES = {
    "sma_crossover": {
        "name": "SMA Crossover",
        "description": "Buy when short SMA crosses above long SMA, sell when crosses below",
        "params": {"short_window": 20, "long_window": 50},
    },
    "rsi_mean_reversion": {
        "name": "RSI Mean Reversion",
        "description": "Buy when RSI < 30 (oversold), sell when RSI > 70 (overbought)",
        "params": {"rsi_period": 14, "oversold": 30, "overbought": 70},
    },
    "macd_momentum": {
        "name": "MACD Momentum",
        "description": "Buy on MACD bullish crossover, sell on bearish crossover",
        "params": {"fast": 12, "slow": 26, "signal": 9},
    },
    "bollinger_bands": {
        "name": "Bollinger Bands",
        "description": "Buy when price touches lower band, sell at upper band",
        "params": {"window": 20, "num_std": 2},
    },
    "dual_momentum": {
        "name": "Dual Momentum",
        "description": "Combines absolute and relative momentum",
        "params": {"lookback": 12},
    },
    "breakout": {
        "name": "Breakout",
        "description": "Buy on new highs, sell on new lows",
        "params": {"lookback": 20},
    },
}


def run_backtest(
    symbol: str,
    strategy: str,
    period: str = "2y",
    initial_capital: float = 100000,
    params: Optional[dict] = None,
) -> dict:
    """Run a backtest for a given strategy."""
    
    if strategy not in STRATEGIES:
        return {"error": f"Unknown strategy: {strategy}", "available": list(STRATEGIES.keys())}
    
    try:
        # Get historical data
        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(period=period)
        
        if hist.empty or len(hist) < 50:
            return {"error": "Insufficient data for backtest", "symbol": symbol}
        
        # Get strategy params
        strat_info = STRATEGIES[strategy]
        strat_params = params or strat_info["params"]
        
        # Generate signals based on strategy
        if strategy == "sma_crossover":
            signals = _sma_crossover_signals(hist, **strat_params)
        elif strategy == "rsi_mean_reversion":
            signals = _rsi_signals(hist, **strat_params)
        elif strategy == "macd_momentum":
            signals = _macd_signals(hist, **strat_params)
        elif strategy == "bollinger_bands":
            signals = _bollinger_signals(hist, **strat_params)
        elif strategy == "dual_momentum":
            signals = _momentum_signals(hist, **strat_params)
        elif strategy == "breakout":
            signals = _breakout_signals(hist, **strat_params)
        else:
            signals = pd.Series(0, index=hist.index)
        
        # Run simulation
        results = _simulate_trades(hist, signals, initial_capital)
        
        # Calculate metrics
        metrics = _calculate_metrics(results, hist, initial_capital)
        
        return {
            "symbol": symbol.upper(),
            "strategy": strat_info["name"],
            "strategy_description": strat_info["description"],
            "period": period,
            "initial_capital": initial_capital,
            "parameters": strat_params,
            "performance": metrics["performance"],
            "risk": metrics["risk"],
            "trades": metrics["trades"],
            "monthly_returns": metrics["monthly_returns"],
        }
        
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def _sma_crossover_signals(hist: pd.DataFrame, short_window: int, long_window: int) -> pd.Series:
    """Generate SMA crossover signals."""
    short_sma = hist["Close"].rolling(short_window).mean()
    long_sma = hist["Close"].rolling(long_window).mean()
    
    signals = pd.Series(0, index=hist.index)
    signals[short_sma > long_sma] = 1  # Long
    signals[short_sma < long_sma] = -1  # Exit
    
    return signals


def _rsi_signals(hist: pd.DataFrame, rsi_period: int, oversold: int, overbought: int) -> pd.Series:
    """Generate RSI mean reversion signals."""
    delta = hist["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(rsi_period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    signals = pd.Series(0, index=hist.index)
    signals[rsi < oversold] = 1  # Buy oversold
    signals[rsi > overbought] = -1  # Sell overbought
    
    return signals


def _macd_signals(hist: pd.DataFrame, fast: int, slow: int, signal: int) -> pd.Series:
    """Generate MACD momentum signals."""
    ema_fast = hist["Close"].ewm(span=fast).mean()
    ema_slow = hist["Close"].ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal).mean()
    
    signals = pd.Series(0, index=hist.index)
    signals[macd > macd_signal] = 1  # Bullish
    signals[macd < macd_signal] = -1  # Bearish
    
    return signals


def _bollinger_signals(hist: pd.DataFrame, window: int, num_std: int) -> pd.Series:
    """Generate Bollinger Bands signals."""
    mid = hist["Close"].rolling(window).mean()
    std = hist["Close"].rolling(window).std()
    upper = mid + (std * num_std)
    lower = mid - (std * num_std)
    
    signals = pd.Series(0, index=hist.index)
    signals[hist["Close"] < lower] = 1  # Buy at lower band
    signals[hist["Close"] > upper] = -1  # Sell at upper band
    
    return signals


def _momentum_signals(hist: pd.DataFrame, lookback: int) -> pd.Series:
    """Generate dual momentum signals."""
    returns = hist["Close"].pct_change(lookback * 21)  # Monthly lookback
    
    signals = pd.Series(0, index=hist.index)
    signals[returns > 0] = 1  # Positive momentum
    signals[returns < 0] = -1  # Negative momentum
    
    return signals


def _breakout_signals(hist: pd.DataFrame, lookback: int) -> pd.Series:
    """Generate breakout signals."""
    high_roll = hist["High"].rolling(lookback).max()
    low_roll = hist["Low"].rolling(lookback).min()
    
    signals = pd.Series(0, index=hist.index)
    signals[hist["Close"] >= high_roll] = 1  # New high breakout
    signals[hist["Close"] <= low_roll] = -1  # New low breakdown
    
    return signals


def _simulate_trades(hist: pd.DataFrame, signals: pd.Series, initial_capital: float) -> dict:
    """Simulate trades based on signals."""
    capital = initial_capital
    position = 0
    shares = 0
    trades = []
    equity_curve = [initial_capital]
    
    for i in range(1, len(hist)):
        date = hist.index[i]
        price = hist["Close"].iloc[i]
        signal = signals.iloc[i]
        prev_signal = signals.iloc[i-1]
        
        # Buy signal
        if signal == 1 and prev_signal != 1 and position == 0:
            shares = int(capital * 0.95 / price)  # Use 95% of capital
            if shares > 0:
                cost = shares * price
                capital -= cost
                position = 1
                trades.append({
                    "date": str(date.date()),
                    "action": "BUY",
                    "price": round(price, 2),
                    "shares": shares,
                    "value": round(cost, 2),
                })
        
        # Sell signal
        elif signal == -1 and position == 1:
            proceeds = shares * price
            pnl = proceeds - (trades[-1]["value"] if trades else 0)
            capital += proceeds
            trades.append({
                "date": str(date.date()),
                "action": "SELL",
                "price": round(price, 2),
                "shares": shares,
                "value": round(proceeds, 2),
                "pnl": round(pnl, 2),
            })
            shares = 0
            position = 0
        
        # Track equity
        equity = capital + (shares * price if position == 1 else 0)
        equity_curve.append(equity)
    
    return {
        "trades": trades,
        "equity_curve": equity_curve,
        "final_equity": equity_curve[-1],
        "final_position": position,
        "final_shares": shares,
    }


def _calculate_metrics(results: dict, hist: pd.DataFrame, initial_capital: float) -> dict:
    """Calculate backtest metrics."""
    equity = np.array(results["equity_curve"])
    trades = results["trades"]
    
    # Performance metrics
    total_return = (equity[-1] / initial_capital - 1) * 100
    
    # Calculate daily returns
    daily_returns = np.diff(equity) / equity[:-1]
    
    # Annualized metrics
    trading_days = len(equity) - 1
    years = trading_days / 252
    annual_return = ((equity[-1] / initial_capital) ** (1/years) - 1) * 100 if years > 0 else 0
    
    # Risk metrics
    volatility = np.std(daily_returns) * np.sqrt(252) * 100 if len(daily_returns) > 0 else 0
    
    # Sharpe ratio (assuming 0% risk-free rate)
    sharpe = (np.mean(daily_returns) * 252) / (np.std(daily_returns) * np.sqrt(252)) if np.std(daily_returns) > 0 else 0
    
    # Max drawdown
    peak = np.maximum.accumulate(equity)
    drawdown = (peak - equity) / peak
    max_drawdown = np.max(drawdown) * 100
    
    # Sortino ratio (downside deviation)
    negative_returns = daily_returns[daily_returns < 0]
    downside_std = np.std(negative_returns) * np.sqrt(252) if len(negative_returns) > 0 else 0
    sortino = (np.mean(daily_returns) * 252) / downside_std if downside_std > 0 else 0
    
    # Calmar ratio
    calmar = annual_return / max_drawdown if max_drawdown > 0 else 0
    
    # Trade statistics
    winning_trades = [t for t in trades if t.get("action") == "SELL" and t.get("pnl", 0) > 0]
    losing_trades = [t for t in trades if t.get("action") == "SELL" and t.get("pnl", 0) <= 0]
    
    num_trades = len([t for t in trades if t.get("action") == "SELL"])
    win_rate = len(winning_trades) / num_trades * 100 if num_trades > 0 else 0
    
    avg_win = np.mean([t["pnl"] for t in winning_trades]) if winning_trades else 0
    avg_loss = np.mean([t["pnl"] for t in losing_trades]) if losing_trades else 0
    
    profit_factor = abs(sum(t["pnl"] for t in winning_trades) / sum(t["pnl"] for t in losing_trades)) if losing_trades and sum(t["pnl"] for t in losing_trades) != 0 else 0
    
    # Buy and hold comparison
    buy_hold_return = (hist["Close"].iloc[-1] / hist["Close"].iloc[0] - 1) * 100
    alpha = total_return - buy_hold_return
    
    # Monthly returns
    monthly_returns = []
    if len(equity) > 21:
        for i in range(21, len(equity), 21):
            month_return = (equity[i] / equity[i-21] - 1) * 100
            month_date = hist.index[min(i, len(hist)-1)]
            monthly_returns.append({
                "month": month_date.strftime("%Y-%m"),
                "return": round(month_return, 2),
            })
    
    return {
        "performance": {
            "initial_capital": f"${initial_capital:,.0f}",
            "final_equity": f"${results['final_equity']:,.0f}",
            "total_return": f"{total_return:.2f}%",
            "annual_return": f"{annual_return:.2f}%",
            "buy_hold_return": f"{buy_hold_return:.2f}%",
            "alpha": f"{alpha:.2f}%",
        },
        "risk": {
            "volatility": f"{volatility:.2f}%",
            "max_drawdown": f"{max_drawdown:.2f}%",
            "sharpe_ratio": f"{sharpe:.2f}",
            "sortino_ratio": f"{sortino:.2f}",
            "calmar_ratio": f"{calmar:.2f}",
        },
        "trades": {
            "total_trades": num_trades,
            "win_rate": f"{win_rate:.1f}%",
            "profit_factor": f"{profit_factor:.2f}",
            "avg_win": f"${avg_win:,.0f}",
            "avg_loss": f"${avg_loss:,.0f}",
            "trade_list": trades[-10:],  # Last 10 trades
        },
        "monthly_returns": monthly_returns[-12:],  # Last 12 months
    }


def get_available_strategies() -> dict:
    """Get list of available strategies."""
    return {
        name: {
            "name": info["name"],
            "description": info["description"],
            "default_params": info["params"],
        }
        for name, info in STRATEGIES.items()
    }


# Tool definition for LLM
BACKTEST_TOOL = {
    "type": "function",
    "function": {
        "name": "run_backtest",
        "description": "Run a backtest simulation with a trading strategy",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock ticker symbol"},
                "strategy": {
                    "type": "string",
                    "enum": list(STRATEGIES.keys()),
                    "description": "Trading strategy to test"
                },
                "period": {"type": "string", "description": "Backtest period (e.g., 2y)", "default": "2y"},
                "initial_capital": {"type": "number", "description": "Starting capital", "default": 100000},
            },
            "required": ["symbol", "strategy"]
        }
    }
}
