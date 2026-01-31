"""Chart generation for Sigma using Plotly."""

import os
import tempfile
from datetime import datetime
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Chart theme
SIGMA_THEME = {
    "bg_color": "#0a0a0f",
    "paper_color": "#0a0a0f",
    "grid_color": "#1a1a2e",
    "text_color": "#e4e4e7",
    "accent": "#3b82f6",
    "positive": "#22c55e",
    "negative": "#ef4444",
    "neutral": "#6b7280",
}


def create_candlestick_chart(
    symbol: str,
    data: pd.DataFrame,
    title: Optional[str] = None,
    show_volume: bool = True,
    show_sma: bool = True,
    sma_periods: list = [20, 50],
) -> str:
    """Create a candlestick chart with optional indicators."""
    
    if show_volume:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=[None, None],
        )
    else:
        fig = make_subplots(rows=1, cols=1)
    
    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name=symbol.upper(),
            increasing_line_color=SIGMA_THEME["positive"],
            decreasing_line_color=SIGMA_THEME["negative"],
        ),
        row=1, col=1
    )
    
    # Add SMAs
    if show_sma:
        colors = ["#f59e0b", "#8b5cf6", "#06b6d4"]
        for i, period in enumerate(sma_periods):
            if len(data) >= period:
                sma = data["Close"].rolling(period).mean()
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=sma,
                        name=f"SMA {period}",
                        line=dict(color=colors[i % len(colors)], width=1),
                    ),
                    row=1, col=1
                )
    
    # Volume
    if show_volume and "Volume" in data.columns:
        colors = [SIGMA_THEME["positive"] if data["Close"].iloc[i] >= data["Open"].iloc[i] 
                  else SIGMA_THEME["negative"] for i in range(len(data))]
        
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data["Volume"],
                name="Volume",
                marker_color=colors,
                opacity=0.7,
            ),
            row=2, col=1
        )
    
    # Layout
    chart_title = title or f"{symbol.upper()} Price Chart"
    _apply_layout(fig, chart_title, show_volume)
    
    return _save_chart(fig, f"{symbol}_candlestick")


def create_line_chart(
    symbol: str,
    data: pd.DataFrame,
    title: Optional[str] = None,
    show_volume: bool = False,
) -> str:
    """Create a line chart."""
    
    if show_volume:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
        )
    else:
        fig = make_subplots(rows=1, cols=1)
    
    # Price line
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["Close"],
            name=symbol.upper(),
            line=dict(color=SIGMA_THEME["accent"], width=2),
            fill="tozeroy",
            fillcolor="rgba(59, 130, 246, 0.1)",
        ),
        row=1, col=1
    )
    
    # Volume
    if show_volume and "Volume" in data.columns:
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data["Volume"],
                name="Volume",
                marker_color=SIGMA_THEME["neutral"],
                opacity=0.5,
            ),
            row=2, col=1
        )
    
    chart_title = title or f"{symbol.upper()} Price"
    _apply_layout(fig, chart_title, show_volume)
    
    return _save_chart(fig, f"{symbol}_line")


def create_comparison_chart(
    symbols: list,
    data_dict: dict,
    title: Optional[str] = None,
    normalize: bool = True,
) -> str:
    """Create a comparison chart for multiple symbols."""
    
    fig = go.Figure()
    
    colors = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"]
    
    for i, symbol in enumerate(symbols):
        if symbol not in data_dict:
            continue
        
        data = data_dict[symbol]
        
        if normalize:
            values = (data["Close"] / data["Close"].iloc[0] - 1) * 100
            y_label = "Return (%)"
        else:
            values = data["Close"]
            y_label = "Price ($)"
        
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=values,
                name=symbol.upper(),
                line=dict(color=colors[i % len(colors)], width=2),
            )
        )
    
    chart_title = title or "Stock Comparison"
    _apply_layout(fig, chart_title, False)
    fig.update_yaxes(title_text=y_label if normalize else "Price ($)")
    
    return _save_chart(fig, "comparison")


def create_technical_chart(
    symbol: str,
    data: pd.DataFrame,
    indicators: list = ["rsi", "macd"],
    title: Optional[str] = None,
) -> str:
    """Create a chart with technical indicators."""
    
    num_indicators = len(indicators)
    heights = [0.5] + [0.25 / max(1, num_indicators)] * num_indicators + [0.25]
    
    fig = make_subplots(
        rows=num_indicators + 2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=heights,
    )
    
    row = 1
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name=symbol.upper(),
            increasing_line_color=SIGMA_THEME["positive"],
            decreasing_line_color=SIGMA_THEME["negative"],
        ),
        row=row, col=1
    )
    row += 1
    
    # Add indicators
    for indicator in indicators:
        if indicator.lower() == "rsi":
            rsi = _calculate_rsi(data["Close"])
            fig.add_trace(
                go.Scatter(x=data.index, y=rsi, name="RSI", line=dict(color=SIGMA_THEME["accent"])),
                row=row, col=1
            )
            fig.add_hline(y=70, line_dash="dash", line_color=SIGMA_THEME["negative"], row=row, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color=SIGMA_THEME["positive"], row=row, col=1)
            fig.update_yaxes(range=[0, 100], row=row, col=1)
            row += 1
        
        elif indicator.lower() == "macd":
            macd, signal, hist = _calculate_macd(data["Close"])
            colors = [SIGMA_THEME["positive"] if h >= 0 else SIGMA_THEME["negative"] for h in hist]
            
            fig.add_trace(
                go.Bar(x=data.index, y=hist, name="MACD Hist", marker_color=colors, opacity=0.5),
                row=row, col=1
            )
            fig.add_trace(
                go.Scatter(x=data.index, y=macd, name="MACD", line=dict(color=SIGMA_THEME["accent"])),
                row=row, col=1
            )
            fig.add_trace(
                go.Scatter(x=data.index, y=signal, name="Signal", line=dict(color="#f59e0b")),
                row=row, col=1
            )
            row += 1
    
    # Volume
    if "Volume" in data.columns:
        colors = [SIGMA_THEME["positive"] if data["Close"].iloc[i] >= data["Open"].iloc[i] 
                  else SIGMA_THEME["negative"] for i in range(len(data))]
        fig.add_trace(
            go.Bar(x=data.index, y=data["Volume"], name="Volume", marker_color=colors, opacity=0.7),
            row=row, col=1
        )
    
    chart_title = title or f"{symbol.upper()} Technical Analysis"
    _apply_layout(fig, chart_title, True)
    
    return _save_chart(fig, f"{symbol}_technical")


def create_performance_chart(
    equity_curve: list,
    title: str = "Portfolio Performance",
) -> str:
    """Create a performance/equity curve chart."""
    
    fig = go.Figure()
    
    x = list(range(len(equity_curve)))
    
    # Equity curve
    fig.add_trace(
        go.Scatter(
            x=x,
            y=equity_curve,
            name="Portfolio Value",
            line=dict(color=SIGMA_THEME["accent"], width=2),
            fill="tozeroy",
            fillcolor="rgba(59, 130, 246, 0.1)",
        )
    )
    
    # Starting value reference line
    fig.add_hline(
        y=equity_curve[0],
        line_dash="dash",
        line_color=SIGMA_THEME["neutral"],
        annotation_text=f"Start: ${equity_curve[0]:,.0f}",
    )
    
    _apply_layout(fig, title, False)
    fig.update_xaxes(title_text="Trading Days")
    fig.update_yaxes(title_text="Portfolio Value ($)")
    
    return _save_chart(fig, "performance")


def create_sector_chart(sector_data: dict) -> str:
    """Create a sector performance chart."""
    
    sectors = list(sector_data.keys())
    values = list(sector_data.values())
    
    colors = [SIGMA_THEME["positive"] if v >= 0 else SIGMA_THEME["negative"] for v in values]
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(
            x=sectors,
            y=values,
            marker_color=colors,
            text=[f"{v:+.2f}%" for v in values],
            textposition="outside",
        )
    )
    
    _apply_layout(fig, "Sector Performance", False)
    fig.update_yaxes(title_text="Return (%)")
    
    return _save_chart(fig, "sectors")


def _calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def _calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Calculate MACD indicator."""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal).mean()
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist


def _apply_layout(fig: go.Figure, title: str, has_volume: bool):
    """Apply Sigma theme to chart."""
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=18, color=SIGMA_THEME["text_color"]),
            x=0.5,
        ),
        paper_bgcolor=SIGMA_THEME["paper_color"],
        plot_bgcolor=SIGMA_THEME["bg_color"],
        font=dict(color=SIGMA_THEME["text_color"], family="SF Mono, Menlo, monospace"),
        xaxis=dict(
            gridcolor=SIGMA_THEME["grid_color"],
            showgrid=True,
            zeroline=False,
        ),
        yaxis=dict(
            gridcolor=SIGMA_THEME["grid_color"],
            showgrid=True,
            zeroline=False,
            title_text="Price ($)",
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=SIGMA_THEME["text_color"]),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=60, r=40, t=80, b=40),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
    )


def _save_chart(fig: go.Figure, name: str) -> str:
    """Save chart to file and return path."""
    
    # Create charts directory
    charts_dir = os.path.expanduser("~/.sigma/charts")
    os.makedirs(charts_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.png"
    filepath = os.path.join(charts_dir, filename)
    
    fig.write_image(filepath, width=1200, height=800, scale=2)
    
    return filepath
