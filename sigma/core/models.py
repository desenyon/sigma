"""Data models for Sigma Financial Intelligence Platform."""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
import json


# ============================================================================
# ENUMS
# ============================================================================

class AssetClass(str, Enum):
    """Asset class types."""
    EQUITY = "equity"
    ETF = "etf"
    OPTION = "option"
    FUTURE = "future"
    FOREX = "forex"
    CRYPTO = "crypto"
    RATES = "rates"
    COMMODITY = "commodity"
    INDEX = "index"
    FUND = "fund"
    UNKNOWN = "unknown"


class TimeHorizon(str, Enum):
    """Investment time horizons."""
    INTRADAY = "intraday"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    MULTI_YEAR = "multi_year"


class RiskProfile(str, Enum):
    """Risk tolerance levels."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    VERY_AGGRESSIVE = "very_aggressive"


class DeliverableType(str, Enum):
    """Types of research deliverables."""
    QUICK_ANSWER = "quick_answer"
    ANALYSIS = "analysis"
    COMPARISON = "comparison"
    BACKTEST = "backtest"
    PORTFOLIO = "portfolio"
    STRATEGY = "strategy"
    REPORT = "report"
    ALERT = "alert"
    CHART = "chart"


class Regime(str, Enum):
    """Market regime types."""
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    HIGH_VOL = "high_volatility"
    LOW_VOL = "low_volatility"
    CRISIS = "crisis"
    RECOVERY = "recovery"


class SignalType(str, Enum):
    """Signal types for strategies."""
    TREND = "trend"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    CARRY = "carry"
    VALUE = "value"
    QUALITY = "quality"
    LOW_VOL = "low_volatility"
    SIZE = "size"
    DEFENSIVE = "defensive"
    GROWTH = "growth"


class DataSource(str, Enum):
    """Data source providers."""
    YFINANCE = "yfinance"
    ALPHA_VANTAGE = "alpha_vantage"
    POLYGON = "polygon"
    TIINGO = "tiingo"
    FRED = "fred"
    QUANDL = "quandl"
    LEAN = "lean"
    CUSTOM = "custom"


# ============================================================================
# RESEARCH PLAN MODELS
# ============================================================================

class Constraint(BaseModel):
    """Investment constraint."""
    name: str
    type: str  # max_weight, sector_cap, leverage_cap, turnover_cap, etc.
    value: float
    description: Optional[str] = None


class ResearchPlan(BaseModel):
    """Structured research plan from user intent."""
    goal: str = Field(..., description="Primary research goal")
    assets: List[str] = Field(default_factory=list, description="Tickers/assets to analyze")
    asset_classes: List[AssetClass] = Field(default_factory=list)
    horizon: TimeHorizon = Field(default=TimeHorizon.DAILY)
    benchmark: Optional[str] = Field(default="SPY", description="Benchmark for comparison")
    risk_profile: RiskProfile = Field(default=RiskProfile.MODERATE)
    constraints: List[Constraint] = Field(default_factory=list)
    deliverable: DeliverableType = Field(default=DeliverableType.ANALYSIS)
    
    # Account and tax settings
    account_type: Optional[str] = Field(default=None)  # taxable, ira, 401k
    leverage_allowed: bool = Field(default=False)
    max_leverage: float = Field(default=1.0)
    tax_aware: bool = Field(default=False)
    
    # Date ranges
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    lookback_period: Optional[str] = Field(default="2y")
    
    # Additional context
    context: Dict[str, Any] = Field(default_factory=dict)
    clarifications_needed: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


# ============================================================================
# DATA MODELS
# ============================================================================

class DataQualityReport(BaseModel):
    """Data quality assessment."""
    total_records: int
    missing_count: int
    missing_pct: float
    stale_ticks: int
    outliers_detected: int
    timezone_issues: int
    date_range: tuple
    gaps: List[tuple]
    warnings: List[str]
    passed: bool


class DataLineage(BaseModel):
    """Track data provenance."""
    source: DataSource
    fetch_timestamp: datetime
    symbols: List[str]
    date_range: tuple
    transformations: List[str] = Field(default_factory=list)
    quality_report: Optional[DataQualityReport] = None
    version: str = "1.0"
    config: Dict[str, Any] = Field(default_factory=dict)


class CorporateAction(BaseModel):
    """Corporate action event."""
    date: date
    symbol: str
    action_type: str  # split, dividend, merger, symbol_change, spinoff
    details: Dict[str, Any]
    adjustment_factor: Optional[float] = None


class PriceBar(BaseModel):
    """OHLCV price bar."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    adjusted_close: Optional[float] = None
    vwap: Optional[float] = None


class Fundamental(BaseModel):
    """Point-in-time fundamental data."""
    as_of_date: date  # When data was known (avoids lookahead)
    report_date: date  # When the report period ends
    symbol: str
    metrics: Dict[str, float]  # revenue, earnings, etc.
    source: str


# ============================================================================
# ANALYTICS MODELS
# ============================================================================

class PerformanceMetrics(BaseModel):
    """Comprehensive performance metrics."""
    # Returns
    total_return: float
    cagr: float
    mtd_return: Optional[float] = None
    ytd_return: Optional[float] = None
    
    # Risk
    volatility: float
    downside_deviation: float
    max_drawdown: float
    drawdown_duration_days: Optional[int] = None
    var_95: Optional[float] = None
    cvar_95: Optional[float] = None
    
    # Risk-adjusted
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    information_ratio: Optional[float] = None
    treynor_ratio: Optional[float] = None
    
    # Other
    beta: Optional[float] = None
    alpha: Optional[float] = None
    r_squared: Optional[float] = None
    tracking_error: Optional[float] = None
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None


class FactorExposure(BaseModel):
    """Factor exposure analysis."""
    symbol: str
    as_of_date: date
    market_beta: float
    size_exposure: Optional[float] = None
    value_exposure: Optional[float] = None
    momentum_exposure: Optional[float] = None
    quality_exposure: Optional[float] = None
    low_vol_exposure: Optional[float] = None
    growth_exposure: Optional[float] = None
    r_squared: float
    residual_vol: float


class RegimeAnalysis(BaseModel):
    """Regime detection results."""
    current_regime: Regime
    regime_probability: float
    regime_history: List[tuple]  # (start_date, end_date, regime)
    transition_matrix: Optional[Dict[str, Dict[str, float]]] = None
    indicators: Dict[str, float]


class SeasonalityAnalysis(BaseModel):
    """Seasonality patterns."""
    symbol: str
    monthly_returns: Dict[int, float]  # month -> avg return
    day_of_week_returns: Dict[int, float]  # day -> avg return
    pre_earnings_drift: Optional[float] = None
    post_earnings_drift: Optional[float] = None
    strongest_month: int
    weakest_month: int
    statistical_significance: Dict[str, float]


class EventStudy(BaseModel):
    """Event study results."""
    event_type: str  # earnings, fomc, cpi, etc.
    symbol: str
    events_analyzed: int
    avg_move: float
    std_move: float
    positive_rate: float
    pre_event_drift: float
    post_event_drift: float
    distribution: Dict[str, float]  # percentiles
    conditional_outcomes: Dict[str, float]


# ============================================================================
# STRATEGY MODELS
# ============================================================================

class TradingRule(BaseModel):
    """Explicit trading rule."""
    name: str
    entry_condition: str  # Human-readable condition
    exit_condition: str
    position_size: str  # Sizing rule description
    stop_loss: Optional[str] = None
    take_profit: Optional[str] = None
    rebalance_frequency: str
    assumptions: List[str] = Field(default_factory=list)
    failure_modes: List[str] = Field(default_factory=list)


class StrategyHypothesis(BaseModel):
    """Trading strategy hypothesis."""
    name: str
    description: str
    signal_type: SignalType
    asset_classes: List[AssetClass]
    timeframe: TimeHorizon
    expected_sharpe: float
    expected_turnover: float
    rules: List[TradingRule]
    data_requirements: List[str]
    assumptions: List[str]
    risks: List[str]


class BacktestResult(BaseModel):
    """Comprehensive backtest results."""
    strategy_name: str
    symbol: str
    period: str
    
    # Performance
    metrics: PerformanceMetrics
    
    # Equity curve data
    equity_curve: List[float]
    drawdown_curve: List[float]
    
    # Trade analysis
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    avg_holding_period: float
    
    # Factor analysis
    factor_exposures: Optional[FactorExposure] = None
    
    # Diagnostics
    warnings: List[str] = Field(default_factory=list)
    issues_detected: List[str] = Field(default_factory=list)
    
    # Reproducibility
    parameters: Dict[str, Any] = Field(default_factory=dict)
    data_lineage: Optional[DataLineage] = None


class ParameterSweepResult(BaseModel):
    """Parameter optimization results."""
    strategy_name: str
    best_params: Dict[str, Any]
    best_metric: float
    optimization_metric: str
    all_results: List[Dict[str, Any]]
    stability_score: float
    overfitting_warning: bool
    train_sharpe: float
    test_sharpe: float


# ============================================================================
# PORTFOLIO MODELS
# ============================================================================

class Position(BaseModel):
    """Portfolio position."""
    symbol: str
    shares: float
    entry_price: float
    current_price: float
    market_value: float
    weight: float
    pnl: float
    pnl_pct: float


class PortfolioAllocation(BaseModel):
    """Portfolio allocation."""
    positions: Dict[str, float]  # symbol -> weight
    method: str  # mean_variance, risk_parity, min_variance, etc.
    expected_return: float
    expected_volatility: float
    expected_sharpe: float
    constraints_applied: List[str]


class RiskBudget(BaseModel):
    """Risk budget allocation."""
    total_risk: float  # Portfolio volatility target
    position_risks: Dict[str, float]  # symbol -> risk contribution
    marginal_risks: Dict[str, float]  # symbol -> marginal risk
    diversification_ratio: float


class HedgeSuggestion(BaseModel):
    """Hedge recommendation."""
    hedge_type: str  # index, sector, duration, volatility
    instrument: str
    hedge_ratio: float
    expected_beta_reduction: float
    cost_estimate: float
    rationale: str


# ============================================================================
# REPORTING MODELS
# ============================================================================

class ResearchMemo(BaseModel):
    """Research memo output."""
    title: str
    date: datetime
    executive_summary: str
    key_findings: List[str]
    methodology: str
    risks: List[str]
    conclusion: str
    what_would_change: List[str]  # Factors that would change the conclusion
    charts: List[str]  # Paths to chart files
    data_sources: List[DataLineage]
    reproducibility_config: Dict[str, Any]


class Alert(BaseModel):
    """Monitoring alert."""
    timestamp: datetime
    alert_type: str  # signal, regime_shift, volume, drawdown, drift
    symbol: str
    message: str
    severity: str  # info, warning, critical
    current_value: float
    threshold: float
    action_suggested: Optional[str] = None


# ============================================================================
# COMPARISON MODELS
# ============================================================================

class ComparisonResult(BaseModel):
    """Multi-asset comparison result."""
    assets: List[str]
    period: str
    
    # Performance comparison
    performance_metrics: Dict[str, PerformanceMetrics]
    
    # Risk comparison
    correlation_matrix: Dict[str, Dict[str, float]]
    beta_to_benchmark: Dict[str, float]
    
    # Behavioral comparison
    momentum_scores: Dict[str, float]
    mean_reversion_scores: Dict[str, float]
    regime_sensitivity: Dict[str, Dict[str, float]]
    
    # Fundamental comparison (if applicable)
    fundamental_comparison: Optional[Dict[str, Dict[str, float]]] = None
    
    # Ranking
    overall_ranking: List[str]
    ranking_rationale: str
    tradeoffs: List[str]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def detect_asset_class(symbol: str) -> AssetClass:
    """Auto-detect asset class from symbol."""
    symbol = symbol.upper()
    
    # Crypto patterns
    if symbol.endswith(("USD", "USDT", "BTC", "ETH")) or symbol in ["BTC", "ETH", "SOL", "DOGE"]:
        return AssetClass.CRYPTO
    
    # Forex patterns
    if len(symbol) == 6 and symbol[:3] in ["USD", "EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD"]:
        return AssetClass.FOREX
    
    # Futures patterns
    if symbol.startswith(("/", "@")) or symbol.endswith(("F", "Z", "H", "M", "U")) and len(symbol) <= 5:
        return AssetClass.FUTURE
    
    # Options (simplified detection)
    if len(symbol) > 10 and any(c.isdigit() for c in symbol):
        return AssetClass.OPTION
    
    # Index patterns
    if symbol.startswith("^") or symbol in ["SPX", "NDX", "DJI", "VIX", "RUT"]:
        return AssetClass.INDEX
    
    # Common ETFs
    etf_patterns = ["SPY", "QQQ", "IWM", "DIA", "VTI", "VOO", "XL", "IY", "VB", "VG"]
    if any(symbol.startswith(p) for p in etf_patterns):
        return AssetClass.ETF
    
    # Default to equity
    return AssetClass.EQUITY


def parse_time_period(period: str) -> tuple:
    """Parse period string to start/end dates."""
    from datetime import timedelta
    
    today = date.today()
    period = period.lower().strip()
    
    period_map = {
        "1d": timedelta(days=1),
        "5d": timedelta(days=5),
        "1w": timedelta(weeks=1),
        "1mo": timedelta(days=30),
        "3mo": timedelta(days=90),
        "6mo": timedelta(days=180),
        "1y": timedelta(days=365),
        "2y": timedelta(days=730),
        "5y": timedelta(days=1825),
        "10y": timedelta(days=3650),
        "ytd": None,  # Special case
        "mtd": None,  # Special case
    }
    
    if period == "ytd":
        return date(today.year, 1, 1), today
    elif period == "mtd":
        return date(today.year, today.month, 1), today
    elif period in period_map:
        return today - period_map[period], today
    else:
        # Try parsing as date range
        if " to " in period:
            parts = period.split(" to ")
            return date.fromisoformat(parts[0]), date.fromisoformat(parts[1])
    
    # Default to 2 years
    return today - timedelta(days=730), today
