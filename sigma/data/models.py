"""Data models for the data module."""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class AssetClass(Enum):
    """Asset class types."""
    EQUITY = "equity"
    ETF = "etf"
    CRYPTO = "crypto"
    FOREX = "forex"
    INDEX = "index"
    COMMODITY = "commodity"
    BOND = "bond"
    OPTION = "option"
    FUTURE = "future"
    UNKNOWN = "unknown"


class DataSource(Enum):
    """Data source providers."""
    YFINANCE = "yfinance"
    ALPHA_VANTAGE = "alpha_vantage"
    POLYGON = "polygon"
    QUANDL = "quandl"
    FRED = "fred"
    CACHE = "cache"
    COMPUTED = "computed"


@dataclass
class DataLineage:
    """Track data provenance."""
    source: DataSource
    symbol: str
    timestamp: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    transformations: List[str] = field(default_factory=list)
    quality_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataQualityReport:
    """Quality assessment for data."""
    completeness: float = 1.0  # % of non-null values
    accuracy: float = 1.0  # estimated accuracy
    timeliness: float = 1.0  # freshness score
    consistency: float = 1.0  # internal consistency
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    total_records: int = 0
    missing_count: int = 0
    missing_pct: float = 0.0
    stale_ticks: int = 0
    outliers_detected: int = 0
    timezone_issues: int = 0
    date_range: Optional[Tuple[Any, Any]] = None
    gaps: List[Any] = field(default_factory=list)
    passed: bool = True
    
    @property
    def overall_score(self) -> float:
        """Calculate overall quality score."""
        return (self.completeness + self.accuracy + self.timeliness + self.consistency) / 4


@dataclass
class CorporateAction:
    """Corporate action event."""
    action_type: str  # split, dividend, merger, spinoff
    date: date
    symbol: str
    ratio: Optional[float] = None  # for splits
    amount: Optional[float] = None  # for dividends
    adjustment_factor: Optional[float] = None  # adjustment multiplier
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PriceBar:
    """Single price bar."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None


@dataclass
class Fundamental:
    """Fundamental data point."""
    symbol: str
    period: str  # quarterly, annual
    date: date
    metrics: Dict[str, Any] = field(default_factory=dict)


def detect_asset_class(symbol: str) -> AssetClass:
    """Detect asset class from symbol."""
    symbol = symbol.upper()
    
    # Crypto patterns
    if symbol.endswith("-USD") or symbol.endswith("USD"):
        return AssetClass.CRYPTO
    if symbol in ["BTC", "ETH", "DOGE", "SOL", "ADA"]:
        return AssetClass.CRYPTO
    
    # Forex patterns
    if len(symbol) == 6 and symbol.isalpha():
        major_currencies = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]
        if symbol[:3] in major_currencies and symbol[3:] in major_currencies:
            return AssetClass.FOREX
    
    # Index patterns
    if symbol.startswith("^") or symbol in ["SPY", "QQQ", "DIA", "IWM", "VTI"]:
        return AssetClass.INDEX if symbol.startswith("^") else AssetClass.ETF
    
    # Common ETFs
    etfs = ["SPY", "QQQ", "IWM", "VTI", "VOO", "VEA", "VWO", "BND", "GLD", "SLV", "USO"]
    if symbol in etfs:
        return AssetClass.ETF
    
    # Default to equity
    return AssetClass.EQUITY
