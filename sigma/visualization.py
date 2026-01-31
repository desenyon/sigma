"""Advanced charting engine - Publication-grade visualizations."""

import json
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ============================================================================
# CHART THEMES
# ============================================================================

SIGMA_THEME = {
    "dark": {
        "bg": "#0d1117",
        "paper_bg": "#0d1117",
        "grid": "#21262d",
        "text": "#c9d1d9",
        "primary": "#58a6ff",
        "secondary": "#8b949e",
        "positive": "#3fb950",
        "negative": "#f85149",
        "accent1": "#a371f7",
        "accent2": "#f0883e",
        "accent3": "#56d4dd",
    },
    "light": {
        "bg": "#ffffff",
        "paper_bg": "#ffffff",
        "grid": "#d0d7de",
        "text": "#1f2328",
        "primary": "#0969da",
        "secondary": "#57606a",
        "positive": "#1a7f37",
        "negative": "#cf222e",
        "accent1": "#8250df",
        "accent2": "#bf8700",
        "accent3": "#0550ae",
    }
}


# ============================================================================
# CHART RECIPES
# ============================================================================

class ChartRecipes:
    """Pre-built chart configurations for common use cases."""
    
    @staticmethod
    def equity_curve() -> Dict[str, Any]:
        """Equity curve with drawdown overlay."""
        return {
            "type": "equity_drawdown",
            "rows": 2,
            "row_heights": [0.7, 0.3],
            "components": ["equity_line", "drawdown_fill"],
        }
    
    @staticmethod
    def returns_analysis() -> Dict[str, Any]:
        """Returns distribution and time series."""
        return {
            "type": "returns_analysis",
            "rows": 2,
            "cols": 2,
            "components": ["returns_bar", "distribution", "rolling_stats", "calendar"],
        }
    
    @staticmethod
    def comparison_dashboard() -> Dict[str, Any]:
        """Multi-asset comparison."""
        return {
            "type": "comparison",
            "rows": 2,
            "cols": 2,
            "components": ["normalized_prices", "rolling_correlation", "risk_return_scatter", "metrics_table"],
        }
    
    @staticmethod
    def strategy_tearsheet() -> Dict[str, Any]:
        """Full strategy analysis."""
        return {
            "type": "tearsheet",
            "rows": 3,
            "cols": 2,
            "components": [
                "equity_curve", "monthly_returns_heatmap",
                "drawdown", "rolling_metrics",
                "returns_distribution", "trade_analysis"
            ],
        }
    
    @staticmethod
    def market_regime() -> Dict[str, Any]:
        """Market regime analysis."""
        return {
            "type": "regime",
            "rows": 2,
            "components": ["price_with_regime_shading", "regime_statistics"],
        }


# ============================================================================
# CHART BUILDER
# ============================================================================

class ChartBuilder:
    """
    Build publication-grade financial charts with Plotly.
    Features:
    - Regime shading
    - Event markers
    - Drawdown overlays
    - Multi-axis layouts
    - Auto-captions
    """
    
    def __init__(self, theme: str = "dark"):
        self.colors = SIGMA_THEME.get(theme, SIGMA_THEME["dark"])
        self.theme = theme
    
    def _get_base_layout(
        self,
        title: str = "",
        height: int = 600,
        width: int = 1000,
        showlegend: bool = True,
    ) -> Dict[str, Any]:
        """Get base layout configuration."""
        
        return {
            "title": {
                "text": title,
                "font": {"size": 18, "color": self.colors["text"]},
                "x": 0.5,
            },
            "paper_bgcolor": self.colors["paper_bg"],
            "plot_bgcolor": self.colors["bg"],
            "font": {"color": self.colors["text"], "family": "SF Pro Display, -apple-system, sans-serif"},
            "height": height,
            "width": width,
            "showlegend": showlegend,
            "legend": {
                "bgcolor": "rgba(0,0,0,0)",
                "font": {"color": self.colors["text"]},
            },
            "margin": {"l": 60, "r": 40, "t": 60, "b": 60},
            "xaxis": {
                "gridcolor": self.colors["grid"],
                "zerolinecolor": self.colors["grid"],
            },
            "yaxis": {
                "gridcolor": self.colors["grid"],
                "zerolinecolor": self.colors["grid"],
            },
        }
    
    # ==========================================================================
    # CORE CHART TYPES
    # ==========================================================================
    
    def price_chart(
        self,
        df: pd.DataFrame,
        title: str = "Price Chart",
        ohlc: bool = False,
        volume: bool = True,
        ma_periods: Optional[List[int]] = None,
        events: Optional[List[Dict[str, Any]]] = None,
        regimes: Optional[pd.Series] = None,
    ) -> go.Figure:
        """
        Create price chart with optional overlays.
        
        Args:
            df: DataFrame with OHLCV data
            title: Chart title
            ohlc: Use candlestick (True) or line (False)
            volume: Include volume subplot
            ma_periods: Moving average periods to overlay
            events: List of event markers
            regimes: Series of regime labels for shading
        """
        
        n_rows = 2 if volume else 1
        row_heights = [0.75, 0.25] if volume else [1.0]
        
        fig = make_subplots(
            rows=n_rows,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=row_heights,
        )
        
        # Main price trace
        if ohlc and all(col in df.columns for col in ["open", "high", "low", "close"]):
            fig.add_trace(
                go.Candlestick(
                    x=df.index,
                    open=df["open"],
                    high=df["high"],
                    low=df["low"],
                    close=df["close"],
                    name="Price",
                    increasing_line_color=self.colors["positive"],
                    decreasing_line_color=self.colors["negative"],
                ),
                row=1, col=1
            )
        else:
            price_col = "close" if "close" in df.columns else df.columns[0]
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[price_col],
                    name="Price",
                    line={"color": self.colors["primary"], "width": 2},
                ),
                row=1, col=1
            )
        
        # Moving averages
        if ma_periods:
            colors = [self.colors["accent1"], self.colors["accent2"], self.colors["accent3"]]
            price_col = "close" if "close" in df.columns else df.columns[0]
            
            for i, period in enumerate(ma_periods):
                ma = df[price_col].rolling(period).mean()
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=ma,
                        name=f"MA{period}",
                        line={"color": colors[i % len(colors)], "width": 1, "dash": "dot"},
                    ),
                    row=1, col=1
                )
        
        # Volume
        if volume and "volume" in df.columns:
            colors = [
                self.colors["positive"] if c >= o else self.colors["negative"]
                for c, o in zip(df.get("close", df.iloc[:, 0]), df.get("open", df.iloc[:, 0].shift(1)))
            ]
            
            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df["volume"],
                    name="Volume",
                    marker_color=colors,
                    opacity=0.5,
                ),
                row=2, col=1
            )
        
        # Event markers
        if events:
            for event in events:
                fig.add_vline(
                    x=event.get("date"),
                    line={"color": event.get("color", self.colors["accent1"]), "dash": "dash"},
                    annotation_text=event.get("label", ""),
                    annotation_position="top",
                )
        
        # Regime shading
        if regimes is not None:
            self._add_regime_shading(fig, regimes)
        
        # Layout
        layout = self._get_base_layout(title)
        layout["xaxis_rangeslider_visible"] = False
        fig.update_layout(**layout)
        
        return fig
    
    def equity_curve(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
        title: str = "Equity Curve",
        show_drawdown: bool = True,
        regimes: Optional[pd.Series] = None,
    ) -> go.Figure:
        """
        Create equity curve with drawdown overlay.
        """
        
        n_rows = 2 if show_drawdown else 1
        row_heights = [0.7, 0.3] if show_drawdown else [1.0]
        
        fig = make_subplots(
            rows=n_rows,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=row_heights,
        )
        
        # Calculate cumulative returns
        equity = (1 + returns).cumprod()
        
        fig.add_trace(
            go.Scatter(
                x=equity.index,
                y=equity.values,
                name="Strategy",
                line={"color": self.colors["primary"], "width": 2},
                fill="tozeroy" if not benchmark_returns else None,
                fillcolor=f"rgba({int(self.colors['primary'][1:3], 16)}, {int(self.colors['primary'][3:5], 16)}, {int(self.colors['primary'][5:7], 16)}, 0.1)",
            ),
            row=1, col=1
        )
        
        # Benchmark
        if benchmark_returns is not None:
            benchmark_equity = (1 + benchmark_returns).cumprod()
            fig.add_trace(
                go.Scatter(
                    x=benchmark_equity.index,
                    y=benchmark_equity.values,
                    name="Benchmark",
                    line={"color": self.colors["secondary"], "width": 1.5, "dash": "dash"},
                ),
                row=1, col=1
            )
        
        # Drawdown
        if show_drawdown:
            running_max = equity.expanding().max()
            drawdown = (equity - running_max) / running_max
            
            fig.add_trace(
                go.Scatter(
                    x=drawdown.index,
                    y=drawdown.values * 100,
                    name="Drawdown",
                    line={"color": self.colors["negative"], "width": 1},
                    fill="tozeroy",
                    fillcolor=f"rgba({int(self.colors['negative'][1:3], 16)}, {int(self.colors['negative'][3:5], 16)}, {int(self.colors['negative'][5:7], 16)}, 0.3)",
                ),
                row=2, col=1
            )
            
            fig.update_yaxes(title_text="Drawdown %", row=2, col=1)
        
        # Regime shading
        if regimes is not None:
            self._add_regime_shading(fig, regimes)
        
        layout = self._get_base_layout(title)
        fig.update_layout(**layout)
        fig.update_yaxes(title_text="Growth of $1", row=1, col=1)
        
        return fig
    
    def returns_distribution(
        self,
        returns: pd.Series,
        title: str = "Returns Distribution",
        benchmark_returns: Optional[pd.Series] = None,
    ) -> go.Figure:
        """Create returns distribution histogram with statistics."""
        
        fig = go.Figure()
        
        # Main histogram
        fig.add_trace(
            go.Histogram(
                x=returns.values * 100,
                name="Strategy",
                marker_color=self.colors["primary"],
                opacity=0.7,
                nbinsx=50,
            )
        )
        
        # Benchmark histogram
        if benchmark_returns is not None:
            fig.add_trace(
                go.Histogram(
                    x=benchmark_returns.values * 100,
                    name="Benchmark",
                    marker_color=self.colors["secondary"],
                    opacity=0.5,
                    nbinsx=50,
                )
            )
        
        # Add mean line
        mean_ret = returns.mean() * 100
        fig.add_vline(
            x=mean_ret,
            line={"color": self.colors["accent1"], "dash": "dash", "width": 2},
            annotation_text=f"Mean: {mean_ret:.2f}%",
        )
        
        # Add VaR lines
        var_95 = returns.quantile(0.05) * 100
        fig.add_vline(
            x=var_95,
            line={"color": self.colors["negative"], "dash": "dot", "width": 1},
            annotation_text=f"5% VaR: {var_95:.2f}%",
        )
        
        layout = self._get_base_layout(title)
        layout["barmode"] = "overlay"
        layout["xaxis_title"] = "Daily Returns (%)"
        layout["yaxis_title"] = "Frequency"
        
        fig.update_layout(**layout)
        
        return fig
    
    def rolling_metrics(
        self,
        returns: pd.Series,
        window: int = 63,
        title: str = "Rolling Metrics",
        metrics: Optional[List[str]] = None,
    ) -> go.Figure:
        """Create rolling metrics chart."""
        
        metrics = metrics or ["volatility", "sharpe", "beta"]
        n_metrics = len(metrics)
        
        fig = make_subplots(
            rows=n_metrics,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=[m.replace("_", " ").title() for m in metrics],
        )
        
        colors = [self.colors["primary"], self.colors["accent1"], self.colors["accent2"]]
        
        for i, metric in enumerate(metrics, 1):
            if metric == "volatility":
                values = returns.rolling(window).std() * np.sqrt(252) * 100
                ylabel = "Volatility (%)"
            elif metric == "sharpe":
                rolling_ret = returns.rolling(window).mean() * 252
                rolling_vol = returns.rolling(window).std() * np.sqrt(252)
                values = rolling_ret / rolling_vol
                ylabel = "Sharpe Ratio"
            elif metric == "returns":
                values = returns.rolling(window).apply(lambda x: (1 + x).prod() - 1) * 100
                ylabel = "Return (%)"
            else:
                values = returns.rolling(window).mean() * 252 * 100
                ylabel = metric.title()
            
            fig.add_trace(
                go.Scatter(
                    x=values.index,
                    y=values.values,
                    name=metric.title(),
                    line={"color": colors[i-1 % len(colors)], "width": 1.5},
                ),
                row=i, col=1
            )
            
            fig.update_yaxes(title_text=ylabel, row=i, col=1)
        
        layout = self._get_base_layout(title, height=400 * n_metrics)
        fig.update_layout(**layout)
        
        return fig
    
    def monthly_returns_heatmap(
        self,
        returns: pd.Series,
        title: str = "Monthly Returns",
    ) -> go.Figure:
        """Create monthly returns heatmap."""
        
        # Resample to monthly
        monthly = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
        
        # Pivot to year x month
        monthly_df = pd.DataFrame({
            'year': monthly.index.year,
            'month': monthly.index.month,
            'return': monthly.values * 100
        })
        
        pivot = monthly_df.pivot(index='year', columns='month', values='return')
        pivot.columns = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Custom colorscale
        colorscale = [
            [0, self.colors["negative"]],
            [0.5, self.colors["bg"]],
            [1, self.colors["positive"]]
        ]
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale=colorscale,
            zmid=0,
            text=np.round(pivot.values, 1),
            texttemplate="%{text}%",
            textfont={"size": 10},
            hovertemplate="Year: %{y}<br>Month: %{x}<br>Return: %{z:.2f}%<extra></extra>",
        ))
        
        layout = self._get_base_layout(title, height=max(400, len(pivot) * 30))
        fig.update_layout(**layout)
        
        return fig
    
    def correlation_matrix(
        self,
        returns_df: pd.DataFrame,
        title: str = "Correlation Matrix",
    ) -> go.Figure:
        """Create correlation matrix heatmap."""
        
        corr = returns_df.corr()
        
        # Custom colorscale
        colorscale = [
            [0, self.colors["negative"]],
            [0.5, self.colors["bg"]],
            [1, self.colors["positive"]]
        ]
        
        fig = go.Figure(data=go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.index,
            colorscale=colorscale,
            zmid=0,
            text=np.round(corr.values, 2),
            texttemplate="%{text}",
            textfont={"size": 10},
            hovertemplate="%{x} vs %{y}: %{z:.3f}<extra></extra>",
        ))
        
        layout = self._get_base_layout(title, height=max(400, len(corr) * 40))
        fig.update_layout(**layout)
        
        return fig
    
    def risk_return_scatter(
        self,
        returns_dict: Dict[str, pd.Series],
        title: str = "Risk-Return",
        annualize: bool = True,
    ) -> go.Figure:
        """Create risk-return scatter plot."""
        
        fig = go.Figure()
        
        points = []
        for name, returns in returns_dict.items():
            if annualize:
                ret = returns.mean() * 252 * 100
                vol = returns.std() * np.sqrt(252) * 100
            else:
                ret = returns.mean() * 100
                vol = returns.std() * 100
            
            sharpe = ret / vol if vol > 0 else 0
            points.append((name, vol, ret, sharpe))
        
        # Create scatter
        for name, vol, ret, sharpe in points:
            color = self.colors["positive"] if ret > 0 else self.colors["negative"]
            
            fig.add_trace(
                go.Scatter(
                    x=[vol],
                    y=[ret],
                    mode="markers+text",
                    name=name,
                    text=[name],
                    textposition="top center",
                    marker={
                        "size": 15 + sharpe * 5,
                        "color": color,
                        "line": {"width": 1, "color": self.colors["text"]},
                    },
                    hovertemplate=f"{name}<br>Return: {ret:.2f}%<br>Vol: {vol:.2f}%<br>Sharpe: {sharpe:.2f}<extra></extra>",
                )
            )
        
        # Add efficient frontier reference line
        if len(points) > 1:
            vols = [p[1] for p in points]
            rets = [p[2] for p in points]
            
            max_sharpe_point = max(points, key=lambda p: p[3])
            
            fig.add_shape(
                type="line",
                x0=0, y0=0,
                x1=max_sharpe_point[1], y1=max_sharpe_point[2],
                line={"color": self.colors["secondary"], "dash": "dash"},
            )
        
        layout = self._get_base_layout(title)
        layout["xaxis_title"] = "Volatility (%)"
        layout["yaxis_title"] = "Return (%)"
        fig.update_layout(**layout)
        
        return fig
    
    def comparison_chart(
        self,
        returns_dict: Dict[str, pd.Series],
        title: str = "Performance Comparison",
        normalize: bool = True,
    ) -> go.Figure:
        """Create multi-asset comparison chart."""
        
        fig = go.Figure()
        
        colors = [
            self.colors["primary"],
            self.colors["accent1"],
            self.colors["accent2"],
            self.colors["accent3"],
            self.colors["positive"],
            self.colors["secondary"],
        ]
        
        for i, (name, returns) in enumerate(returns_dict.items()):
            if normalize:
                values = (1 + returns).cumprod()
            else:
                values = returns.cumsum()
            
            fig.add_trace(
                go.Scatter(
                    x=values.index,
                    y=values.values,
                    name=name,
                    line={"color": colors[i % len(colors)], "width": 2},
                )
            )
        
        layout = self._get_base_layout(title)
        layout["yaxis_title"] = "Growth of $1" if normalize else "Cumulative Return"
        layout["hovermode"] = "x unified"
        fig.update_layout(**layout)
        
        return fig
    
    def _add_regime_shading(
        self,
        fig: go.Figure,
        regimes: pd.Series,
        row: int = 1,
    ) -> None:
        """Add regime shading to a figure."""
        
        regime_colors = {
            "expansion": "rgba(59, 185, 80, 0.1)",
            "contraction": "rgba(248, 81, 73, 0.1)",
            "high_vol": "rgba(248, 81, 73, 0.15)",
            "low_vol": "rgba(59, 185, 80, 0.08)",
            "bull": "rgba(59, 185, 80, 0.1)",
            "bear": "rgba(248, 81, 73, 0.1)",
            "neutral": "rgba(139, 148, 158, 0.05)",
        }
        
        # Find regime changes
        regime_changes = regimes != regimes.shift(1)
        change_points = regimes.index[regime_changes].tolist()
        
        if not change_points:
            return
        
        change_points.append(regimes.index[-1])
        
        for i in range(len(change_points) - 1):
            start = change_points[i]
            end = change_points[i + 1]
            regime = regimes.loc[start]
            
            color = regime_colors.get(str(regime).lower(), "rgba(139, 148, 158, 0.05)")
            
            fig.add_vrect(
                x0=start,
                x1=end,
                fillcolor=color,
                layer="below",
                line_width=0,
                row=row,
                col=1,
            )
    
    def save_chart(
        self,
        fig: go.Figure,
        filepath: str,
        format: str = "png",
        scale: int = 2,
    ) -> str:
        """Save chart to file."""
        
        if format == "html":
            fig.write_html(filepath)
        else:
            fig.write_image(filepath, format=format, scale=scale)
        
        return filepath


# ============================================================================
# AUTO CAPTION GENERATOR
# ============================================================================

class AutoCaptionGenerator:
    """Generate captions for charts automatically."""
    
    @staticmethod
    def equity_curve_caption(
        total_return: float,
        max_drawdown: float,
        sharpe: float,
        benchmark_return: Optional[float] = None,
    ) -> str:
        """Generate caption for equity curve."""
        
        caption = f"Total return of {total_return:.1%}"
        
        if benchmark_return is not None:
            excess = total_return - benchmark_return
            caption += f" ({'+' if excess >= 0 else ''}{excess:.1%} vs benchmark)"
        
        caption += f" with {abs(max_drawdown):.1%} maximum drawdown"
        caption += f" and {sharpe:.2f} Sharpe ratio."
        
        return caption
    
    @staticmethod
    def comparison_caption(
        winner: str,
        margin: float,
        metric: str,
    ) -> str:
        """Generate caption for comparison chart."""
        
        return f"{winner} outperformed by {margin:.1%} in {metric} over the period."
    
    @staticmethod
    def regime_caption(
        current_regime: str,
        duration: int,
        historical_context: str,
    ) -> str:
        """Generate caption for regime chart."""
        
        return f"Currently in {current_regime} regime for {duration} days. {historical_context}"
