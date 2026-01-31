"""Beautiful terminal charts for Sigma."""

import os
from datetime import datetime
from typing import Any, Optional

import plotext as plt
import yfinance as yf


def create_price_chart(
    symbol: str,
    period: str = "3mo",
    chart_type: str = "candle",
    show_volume: bool = True,
    theme: str = "dark",
) -> str:
    """Create a beautiful price chart in the terminal.
    
    Args:
        symbol: Stock ticker symbol
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
        chart_type: Chart type (candle, line, bar, area) - default is candle
        show_volume: Whether to show volume subplot
        theme: Color theme (dark, light, pro)
        
    Returns:
        ASCII chart string
    """
    ticker = yf.Ticker(symbol.upper())
    hist = ticker.history(period=period)
    
    if hist.empty:
        return f"No data available for {symbol}"
    
    # Setup theme
    if theme == "dark":
        plt.theme("dark")
        plt.canvas_color("black")
        plt.axes_color("black")
    elif theme == "pro":
        plt.theme("pro")
    else:
        plt.theme("clear")
    
    # Get data
    dates = list(range(len(hist)))
    closes = hist["Close"].tolist()
    opens = hist["Open"].tolist()
    highs = hist["High"].tolist()
    lows = hist["Low"].tolist()
    volumes = hist["Volume"].tolist()
    
    # Date labels
    date_labels = [d.strftime("%m/%d") for d in hist.index]
    
    # Calculate change
    if len(closes) > 1:
        change = closes[-1] - closes[0]
        change_pct = (change / closes[0]) * 100
        color = "green" if change >= 0 else "red"
        change_str = f"+{change:.2f} (+{change_pct:.1f}%)" if change >= 0 else f"{change:.2f} ({change_pct:.1f}%)"
    else:
        color = "white"
        change_str = ""
    
    plt.clear_figure()
    plt.plotsize(150, 50)  # Higher resolution
    
    if show_volume:
        plt.subplots(2, 1)
        plt.subplot(1, 1)
    
    # Chart title
    info = ticker.info
    name = info.get("shortName", symbol.upper())
    current_price = closes[-1] if closes else 0
    
    title = f"  {name} ({symbol.upper()}) │ ${current_price:.2f} │ {change_str}"
    plt.title(title)
    
    # Plot based on type
    if chart_type == "candle":
        plt.candlestick(dates, {"Open": opens, "Close": closes, "High": highs, "Low": lows})
        plt.xlabel("Date")
    elif chart_type == "bar":
        colors = ["green" if c >= o else "red" for c, o in zip(closes, opens)]
        plt.bar(dates, closes, color=colors)
        plt.xlabel("Date")
    elif chart_type == "area":
        plt.plot(dates, closes, color=color, fillx=True)
        plt.xlabel("Date")
    else:  # line
        plt.plot(dates, closes, color=color, marker="hd")
        
        # Add moving averages
        if len(closes) >= 20:
            sma20 = []
            for i in range(len(closes)):
                if i >= 19:
                    sma20.append(sum(closes[i-19:i+1]) / 20)
                else:
                    sma20.append(None)
            valid_sma = [(i, v) for i, v in enumerate(sma20) if v is not None]
            if valid_sma:
                plt.plot([x[0] for x in valid_sma], [x[1] for x in valid_sma], color="cyan", marker="hd")
    
    plt.ylabel("Price ($)")
    
    # X-axis labels (every 5th date or so)
    step = max(1, len(dates) // 8)
    xticks = dates[::step]
    xlabels = date_labels[::step]
    plt.xticks(xticks, xlabels)
    
    # Volume subplot
    if show_volume:
        plt.subplot(2, 1)
        vol_colors = ["green" if closes[i] >= opens[i] else "red" for i in range(len(volumes))]
        plt.bar(dates, [v / 1_000_000 for v in volumes], color=vol_colors)
        plt.ylabel("Vol (M)")
        plt.xticks(xticks, xlabels)
    
    # Build the chart
    chart_str = plt.build()
    
    return chart_str


def create_comparison_chart(symbols: list[str], period: str = "3mo") -> str:
    """Create a comparison chart for multiple stocks.
    
    Args:
        symbols: List of stock symbols
        period: Time period
        
    Returns:
        ASCII chart string
    """
    plt.clear_figure()
    plt.plotsize(150, 45)  # Higher resolution
    plt.theme("dark")
    plt.canvas_color("black")
    plt.axes_color("black")
    
    colors = ["cyan", "magenta", "yellow", "green", "red", "blue"]
    legend_items = []
    
    for i, symbol in enumerate(symbols[:6]):  # Max 6 symbols
        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(period=period)
        
        if hist.empty:
            continue
        
        # Normalize to percentage change
        closes = hist["Close"].tolist()
        if closes:
            base = closes[0]
            normalized = [(c / base - 1) * 100 for c in closes]
            dates = list(range(len(normalized)))
            
            color = colors[i % len(colors)]
            plt.plot(dates, normalized, color=color, marker="hd", label=symbol.upper())
            legend_items.append(f"{symbol.upper()}")
    
    plt.title("  Stock Comparison (% Change)")
    plt.ylabel("Change (%)")
    plt.xlabel("Days")
    
    chart_str = plt.build()
    return chart_str


def create_sector_chart() -> str:
    """Create a sector performance chart."""
    sectors = {
        "XLK": "Tech",
        "XLF": "Fin",
        "XLV": "Health",
        "XLE": "Energy",
        "XLI": "Indust",
        "XLY": "Discr",
        "XLP": "Staples",
        "XLU": "Util",
        "XLB": "Mater",
        "XLRE": "RE",
    }
    
    plt.clear_figure()
    plt.plotsize(120, 35)  # Higher resolution
    plt.theme("dark")
    plt.canvas_color("black")
    plt.axes_color("black")
    
    names = []
    changes = []
    colors = []
    
    for symbol, name in sectors.items():
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if info:
                price = info.get("regularMarketPrice", 0)
                prev = info.get("previousClose", 0)
                if price and prev:
                    change = ((price - prev) / prev) * 100
                    names.append(name)
                    changes.append(change)
                    colors.append("green" if change >= 0 else "red")
        except:
            continue
    
    if not names:
        return "Could not fetch sector data"
    
    plt.bar(names, changes, color=colors, orientation="horizontal")
    plt.title("  Sector Performance (% Daily Change)")
    plt.xlabel("Change (%)")
    
    chart_str = plt.build()
    return chart_str


def create_rsi_chart(symbol: str, period: str = "3mo") -> str:
    """Create a price chart with RSI indicator."""
    ticker = yf.Ticker(symbol.upper())
    hist = ticker.history(period=period)
    
    if hist.empty:
        return f"No data available for {symbol}"
    
    plt.clear_figure()
    plt.plotsize(150, 50)  # Higher resolution
    plt.theme("dark")
    plt.canvas_color("black")
    plt.axes_color("black")
    
    closes = hist["Close"].tolist()
    dates = list(range(len(closes)))
    
    # Calculate RSI
    deltas = [closes[i] - closes[i-1] if i > 0 else 0 for i in range(len(closes))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    
    # 14-period RSI
    rsi_values = []
    window = 14
    for i in range(len(closes)):
        if i < window:
            rsi_values.append(50)  # Neutral
        else:
            avg_gain = sum(gains[i-window+1:i+1]) / window
            avg_loss = sum(losses[i-window+1:i+1]) / window
            if avg_loss == 0:
                rsi_values.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi_values.append(100 - (100 / (1 + rs)))
    
    plt.subplots(2, 1)
    
    # Price chart
    plt.subplot(1, 1)
    color = "green" if closes[-1] >= closes[0] else "red"
    plt.plot(dates, closes, color=color, marker="hd")
    plt.title(f"  {symbol.upper()} Price & RSI")
    plt.ylabel("Price ($)")
    
    # RSI chart
    plt.subplot(2, 1)
    plt.plot(dates, rsi_values, color="magenta", marker="hd")
    plt.hline(70, color="red")
    plt.hline(30, color="green")
    plt.ylabel("RSI")
    plt.ylim(0, 100)
    
    chart_str = plt.build()
    return chart_str


def create_portfolio_pie(holdings: list[dict]) -> str:
    """Create a portfolio allocation pie chart."""
    plt.clear_figure()
    plt.theme("dark")
    
    labels = []
    values = []
    
    total = 0
    for h in holdings:
        symbol = h.get("symbol", "")
        shares = h.get("shares", 0)
        
        try:
            ticker = yf.Ticker(symbol.upper())
            info = ticker.info
            price = info.get("regularMarketPrice", 0)
            value = price * shares
            if value > 0:
                labels.append(symbol.upper())
                values.append(value)
                total += value
        except:
            continue
    
    if not labels:
        return "Could not calculate portfolio"
    
    # Convert to percentages
    percentages = [v / total * 100 for v in values]
    
    # Bar chart (pie not well supported in terminal)
    colors = ["cyan", "magenta", "yellow", "green", "red", "blue"]
    plt.bar(labels, percentages, color=colors[:len(labels)])
    plt.title(f"  Portfolio Allocation (${total:,.0f} total)")
    plt.ylabel("% of Portfolio")
    
    chart_str = plt.build()
    return chart_str


def save_chart_to_file(
    symbol: str,
    period: str = "6mo",
    filepath: Optional[str] = None,
) -> str:
    """Save a high-quality chart to HTML file using plotly."""
    try:
        import plotly.graph_objects as go  # type: ignore
        from plotly.subplots import make_subplots  # type: ignore
    except ImportError:
        return "plotly not installed. Run: pip install plotly"
    
    ticker = yf.Ticker(symbol.upper())
    hist = ticker.history(period=period)
    
    if hist.empty:
        return f"No data for {symbol}"
    
    # Create candlestick with volume
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3]
    )
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=hist.index,
            open=hist["Open"],
            high=hist["High"],
            low=hist["Low"],
            close=hist["Close"],
            name="OHLC"
        ),
        row=1, col=1
    )
    
    # Volume
    colors = ["green" if c >= o else "red" 
              for c, o in zip(hist["Close"], hist["Open"])]
    fig.add_trace(
        go.Bar(x=hist.index, y=hist["Volume"], marker_color=colors, name="Volume"),
        row=2, col=1
    )
    
    # Add moving averages
    hist["SMA20"] = hist["Close"].rolling(window=20).mean()
    hist["SMA50"] = hist["Close"].rolling(window=50).mean()
    
    fig.add_trace(
        go.Scatter(x=hist.index, y=hist["SMA20"], line=dict(color="cyan", width=1), name="SMA20"),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=hist.index, y=hist["SMA50"], line=dict(color="yellow", width=1), name="SMA50"),
        row=1, col=1
    )
    
    info = ticker.info
    name = info.get("shortName", symbol.upper())
    
    fig.update_layout(
        title=f"{name} ({symbol.upper()}) - {period} Chart",
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        showlegend=True,
    )
    
    # Save
    if filepath is None:
        filepath = f"{symbol.lower()}_chart.html"
    
    fig.write_html(filepath)
    return f"Chart saved to {filepath}"
