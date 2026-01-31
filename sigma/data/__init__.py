"""Data acquisition layer with quality checks and lineage tracking."""

import asyncio
import hashlib
import json
import os
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import yfinance as yf
import requests

from .models import (
    DataSource,
    DataLineage,
    DataQualityReport,
    CorporateAction,
    PriceBar,
    Fundamental,
    AssetClass,
    detect_asset_class,
)


# ============================================================================
# DATA PROVIDER INTERFACE
# ============================================================================

class DataProvider:
    """Base class for data providers."""
    
    def __init__(self, name: str, api_key: Optional[str] = None):
        self.name = name
        self.api_key = api_key
        self.rate_limit = 5  # requests per second
        self.last_request = 0
    
    async def get_price_history(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Get price history for a symbol."""
        raise NotImplementedError
    
    async def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Get fundamental data for a symbol."""
        raise NotImplementedError
    
    async def get_corporate_actions(
        self,
        symbol: str,
        start: date,
        end: date,
    ) -> List[CorporateAction]:
        """Get corporate actions for a symbol."""
        raise NotImplementedError


class YFinanceProvider(DataProvider):
    """Yahoo Finance data provider."""
    
    def __init__(self):
        super().__init__("yfinance")
    
    async def get_price_history(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Get price history from Yahoo Finance."""
        ticker = yf.Ticker(symbol)
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None,
            lambda: ticker.history(start=start, end=end, interval=interval)
        )
        
        return df
    
    async def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Get fundamental data from Yahoo Finance."""
        ticker = yf.Ticker(symbol)
        
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: ticker.info)
        
        return info
    
    async def get_corporate_actions(
        self,
        symbol: str,
        start: date,
        end: date,
    ) -> List[CorporateAction]:
        """Get corporate actions from Yahoo Finance."""
        ticker = yf.Ticker(symbol)
        
        loop = asyncio.get_event_loop()
        
        # Get splits
        splits = await loop.run_in_executor(None, lambda: ticker.splits)
        
        # Get dividends
        dividends = await loop.run_in_executor(None, lambda: ticker.dividends)
        
        actions = []
        
        if not splits.empty:
            for dt, ratio in splits.items():
                try:
                    if hasattr(dt, 'date'):
                        action_date = dt.date()
                    elif hasattr(dt, 'to_pydatetime'):
                        action_date = dt.to_pydatetime().date()
                    else:
                        action_date = date.fromisoformat(str(dt)[:10])
                    if start <= action_date <= end:
                        actions.append(CorporateAction(
                            date=action_date,
                            symbol=symbol,
                            action_type="split",
                            ratio=float(ratio),
                            adjustment_factor=float(ratio),
                            details={"ratio": float(ratio)},
                        ))
                except (TypeError, AttributeError, ValueError):
                    continue
        
        if not dividends.empty:
            for dt, amount in dividends.items():
                try:
                    if hasattr(dt, 'date'):
                        action_date = dt.date()
                    elif hasattr(dt, 'to_pydatetime'):
                        action_date = dt.to_pydatetime().date()
                    else:
                        action_date = date.fromisoformat(str(dt)[:10])
                    if start <= action_date <= end:
                        actions.append(CorporateAction(
                            date=action_date,
                            symbol=symbol,
                            action_type="dividend",
                            amount=float(amount),
                            details={"amount": float(amount)},
                        ))
                except (TypeError, AttributeError, ValueError):
                    continue
        
        return actions
    
    async def get_financial_statements(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """Get financial statements from Yahoo Finance."""
        ticker = yf.Ticker(symbol)
        
        loop = asyncio.get_event_loop()
        
        income = await loop.run_in_executor(None, lambda: ticker.income_stmt)
        balance = await loop.run_in_executor(None, lambda: ticker.balance_sheet)
        cashflow = await loop.run_in_executor(None, lambda: ticker.cashflow)
        
        return {
            "income_statement": income,
            "balance_sheet": balance,
            "cash_flow": cashflow,
        }
    
    async def get_options_data(self, symbol: str) -> Dict[str, Any]:
        """Get options data from Yahoo Finance."""
        ticker = yf.Ticker(symbol)
        
        loop = asyncio.get_event_loop()
        
        try:
            expirations = await loop.run_in_executor(None, lambda: ticker.options)
            
            if not expirations:
                return {"error": "No options data available"}
            
            # Get first expiration's chain
            chain = await loop.run_in_executor(
                None, lambda: ticker.option_chain(expirations[0])
            )
            
            return {
                "expirations": list(expirations),
                "calls": chain.calls.to_dict() if hasattr(chain, 'calls') else {},
                "puts": chain.puts.to_dict() if hasattr(chain, 'puts') else {},
            }
        except Exception as e:
            return {"error": str(e)}


class FREDProvider(DataProvider):
    """FRED (Federal Reserve Economic Data) provider."""
    
    BASE_URL = "https://api.stlouisfed.org/fred"
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("fred", api_key)
    
    async def get_series(
        self,
        series_id: str,
        start: date,
        end: date,
    ) -> pd.DataFrame:
        """Get FRED series data."""
        if not self.api_key:
            raise ValueError("FRED API key required")
        
        url = f"{self.BASE_URL}/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start.isoformat(),
            "observation_end": end.isoformat(),
        }
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: requests.get(url, params=params)
        )
        
        data = response.json()
        
        if "observations" not in data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data["observations"])
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.set_index("date")
        
        return df[["value"]]
    
    # Common FRED series
    SERIES = {
        "treasury_10y": "DGS10",
        "treasury_2y": "DGS2",
        "fed_funds": "FEDFUNDS",
        "inflation_cpi": "CPIAUCSL",
        "unemployment": "UNRATE",
        "gdp": "GDP",
        "credit_spread": "BAMLC0A0CM",
        "vix": "VIXCLS",
    }


# ============================================================================
# DATA QUALITY ENGINE
# ============================================================================

class DataQualityEngine:
    """Perform data quality checks and cleaning."""
    
    @staticmethod
    def check_quality(df: pd.DataFrame, symbol: Optional[str] = None) -> DataQualityReport:
        """Run comprehensive quality checks on data."""
        total = len(df)
        
        # Missing data
        missing = df.isnull().sum().sum()
        missing_pct = (missing / (total * len(df.columns))) * 100 if total > 0 else 0
        
        # Stale ticks (same OHLC for multiple days)
        stale = 0
        if "Close" in df.columns and len(df) > 1:
            stale = (df["Close"].diff() == 0).sum()
        
        # Outliers (returns > 50% in a day)
        outliers = 0
        if "Close" in df.columns and len(df) > 1:
            returns = df["Close"].pct_change().abs()
            outliers = (returns > 0.5).sum()
        
        # Date gaps
        gaps = []
        if isinstance(df.index, pd.DatetimeIndex):
            expected_dates = pd.date_range(df.index.min(), df.index.max(), freq="B")
            actual_dates = set(df.index.date)
            missing_dates = set(expected_dates.date) - actual_dates
            
            # Find consecutive gaps
            if missing_dates:
                sorted_missing = sorted(missing_dates)
                gap_start = sorted_missing[0]
                gap_end = sorted_missing[0]
                
                for d in sorted_missing[1:]:
                    if (d - gap_end).days <= 3:  # Allow weekends
                        gap_end = d
                    else:
                        if gap_start != gap_end:
                            gaps.append((gap_start, gap_end))
                        gap_start = d
                        gap_end = d
                
                if gap_start != gap_end:
                    gaps.append((gap_start, gap_end))
        
        # Timezone issues
        tz_issues = 0
        if isinstance(df.index, pd.DatetimeIndex):
            if df.index.tz is None:
                tz_issues = 1  # Timezone-naive
        
        # Warnings
        warnings = []
        if missing_pct > 5:
            warnings.append(f"High missing data: {missing_pct:.1f}%")
        if stale > len(df) * 0.1:
            warnings.append(f"Many stale ticks: {stale}")
        if outliers > 0:
            warnings.append(f"Potential outliers detected: {outliers}")
        if len(gaps) > 0:
            warnings.append(f"Data gaps detected: {len(gaps)}")
        
        return DataQualityReport(
            total_records=total,
            missing_count=missing,
            missing_pct=missing_pct,
            stale_ticks=stale,
            outliers_detected=outliers,
            timezone_issues=tz_issues,
            date_range=(df.index.min(), df.index.max()) if len(df) > 0 else (None, None),
            gaps=gaps,
            warnings=warnings,
            passed=len(warnings) == 0,
        )
    
    @staticmethod
    def clean_price_data(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and adjust price data."""
        df = df.copy()
        
        # Handle missing values
        for col in ["Open", "High", "Low", "Close"]:
            if col in df.columns:
                df[col] = df[col].ffill()
        
        # Handle volume
        if "Volume" in df.columns:
            df["Volume"] = df["Volume"].fillna(0)
        
        # Remove obvious outliers (returns > 100%)
        if "Close" in df.columns and len(df) > 1:
            returns = df["Close"].pct_change().abs()
            outlier_mask = returns > 1.0
            if outlier_mask.any():
                df.loc[outlier_mask, "Close"] = np.nan
                df["Close"] = df["Close"].interpolate()
        
        return df
    
    @staticmethod
    def adjust_for_splits(df: pd.DataFrame, splits: List[CorporateAction]) -> pd.DataFrame:
        """Adjust historical prices for stock splits."""
        df = df.copy()
        
        for split in sorted(splits, key=lambda x: x.date, reverse=True):
            factor = split.adjustment_factor or split.ratio
            if factor:
                try:
                    mask = pd.to_datetime(df.index).date < split.date
                    for col in ["Open", "High", "Low", "Close"]:
                        if col in df.columns:
                            df.loc[mask, col] = df.loc[mask, col] / factor
                    if "Volume" in df.columns:
                        df.loc[mask, "Volume"] = df.loc[mask, "Volume"] * factor
                except (TypeError, AttributeError):
                    continue
        
        return df


# ============================================================================
# DATA MANAGER
# ============================================================================

class DataManager:
    """Central data manager with caching and lineage tracking."""
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or os.path.expanduser("~/.sigma/data_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.providers = {
            DataSource.YFINANCE: YFinanceProvider(),
        }
        self.lineage_records = []
        self.quality_engine = DataQualityEngine()
    
    def add_provider(self, source: DataSource, provider: DataProvider):
        """Add a data provider."""
        self.providers[source] = provider
    
    async def get_price_data(
        self,
        symbols: Union[str, List[str]],
        start: Optional[date] = None,
        end: Optional[date] = None,
        period: str = "2y",
        source: DataSource = DataSource.YFINANCE,
        clean: bool = True,
        adjust_splits: bool = True,
    ) -> Dict[str, pd.DataFrame]:
        """Get price data for one or more symbols."""
        if isinstance(symbols, str):
            symbols = [symbols]
        
        # Parse period if dates not provided
        if start is None or end is None:
            end = date.today()
            period_days = {
                "1d": 1, "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180,
                "1y": 365, "2y": 730, "5y": 1825, "10y": 3650,
            }
            days = period_days.get(period, 730)
            start = end - timedelta(days=days)
        
        provider = self.providers.get(source)
        if not provider:
            raise ValueError(f"Provider not available: {source}")
        
        results = {}
        transformations = []
        
        for symbol in symbols:
            # Check cache
            cache_key = self._cache_key(symbol, start, end, source)
            cached = self._load_cache(cache_key)
            
            if cached is not None:
                df = cached
                transformations.append("loaded_from_cache")
            else:
                # Fetch from provider
                df = await provider.get_price_history(symbol, start, end)
                
                if df.empty:
                    continue
                
                # Cache the raw data
                self._save_cache(cache_key, df)
                transformations.append("fetched_fresh")
            
            # Clean data
            if clean:
                df = self.quality_engine.clean_price_data(df)
                transformations.append("cleaned")
            
            # Adjust for splits
            if adjust_splits and source == DataSource.YFINANCE:
                splits = await provider.get_corporate_actions(symbol, start, end)
                split_actions = [a for a in splits if a.action_type == "split"]
                if split_actions:
                    df = self.quality_engine.adjust_for_splits(df, split_actions)
                    transformations.append("split_adjusted")
            
            # Quality report
            quality = self.quality_engine.check_quality(df, symbol)
            
            # Record lineage
            lineage = DataLineage(
                source=source,
                fetch_timestamp=datetime.now(),
                symbols=[symbol],
                date_range=(start, end),
                transformations=transformations,
                quality_report=quality,
            )
            self.lineage_records.append(lineage)
            
            results[symbol] = df
        
        return results
    
    async def get_fundamentals(
        self,
        symbol: str,
        source: DataSource = DataSource.YFINANCE,
        point_in_time: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get fundamental data with point-in-time awareness."""
        provider = self.providers.get(source)
        if not provider:
            raise ValueError(f"Provider not available: {source}")
        
        data = await provider.get_fundamentals(symbol)
        
        # Add point-in-time metadata
        data["_as_of_date"] = point_in_time or date.today()
        data["_fetch_timestamp"] = datetime.now().isoformat()
        data["_source"] = source.value
        
        return data
    
    async def get_macro_data(
        self,
        series: List[str],
        start: Optional[date] = None,
        end: Optional[date] = None,
    ) -> Dict[str, pd.DataFrame]:
        """Get macroeconomic data."""
        fred = self.providers.get(DataSource.FRED)
        if not fred:
            # Return empty if FRED not configured
            return {}
        
        end = end or date.today()
        start = start or (end - timedelta(days=365*5))
        
        results = {}
        for series_name in series:
            series_id = FREDProvider.SERIES.get(series_name, series_name)
            try:
                df = await fred.get_series(series_id, start, end)
                results[series_name] = df
            except Exception:
                continue
        
        return results
    
    def get_lineage(self, symbol: str = None) -> List[DataLineage]:
        """Get data lineage records."""
        if symbol:
            return [l for l in self.lineage_records if symbol in l.symbols]
        return self.lineage_records
    
    def _cache_key(self, symbol: str, start: date, end: date, source: DataSource) -> str:
        """Generate cache key."""
        key = f"{symbol}_{start}_{end}_{source.value}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _load_cache(self, key: str) -> Optional[pd.DataFrame]:
        """Load from cache."""
        cache_path = os.path.join(self.cache_dir, f"{key}.pkl")
        if os.path.exists(cache_path):
            # Check if cache is fresh (less than 1 day old)
            mtime = os.path.getmtime(cache_path)
            if datetime.now().timestamp() - mtime < 86400:  # 24 hours
                return pd.read_pickle(cache_path)
        return None
    
    def _save_cache(self, key: str, df: pd.DataFrame):
        """Save to cache."""
        cache_path = os.path.join(self.cache_dir, f"{key}.pkl")
        df.to_pickle(cache_path)
    
    def clear_cache(self, symbol: str = None):
        """Clear cache."""
        if symbol:
            # Clear specific symbol
            for f in os.listdir(self.cache_dir):
                if symbol in f:
                    os.remove(os.path.join(self.cache_dir, f))
        else:
            # Clear all
            for f in os.listdir(self.cache_dir):
                os.remove(os.path.join(self.cache_dir, f))


# ============================================================================
# SURVIVORSHIP BIAS HANDLING
# ============================================================================

class DelistedTracker:
    """Track delisted securities for survivorship-bias-free analysis."""
    
    # Known delisted tickers (simplified - would need database in production)
    KNOWN_DELISTED = {
        "LVLT": {"delisted": "2017-11-01", "reason": "acquired", "successor": "CTL"},
        "TWX": {"delisted": "2018-06-15", "reason": "acquired", "successor": "T"},
        "YHOO": {"delisted": "2017-06-13", "reason": "acquired", "successor": "VZ"},
        "MON": {"delisted": "2018-06-07", "reason": "acquired", "successor": "BAYER.DE"},
    }
    
    @classmethod
    def is_delisted(cls, symbol: str) -> bool:
        """Check if a symbol is delisted."""
        return symbol.upper() in cls.KNOWN_DELISTED
    
    @classmethod
    def get_delisting_info(cls, symbol: str) -> Optional[Dict[str, Any]]:
        """Get delisting information."""
        return cls.KNOWN_DELISTED.get(symbol.upper())
    
    @classmethod
    def warn_survivorship_bias(cls, symbols: List[str], start_date: date) -> List[str]:
        """Warn about potential survivorship bias."""
        warnings = []
        
        for symbol in symbols:
            info = cls.get_delisting_info(symbol)
            if info:
                delisted = date.fromisoformat(info["delisted"])
                if start_date < delisted:
                    warnings.append(
                        f"{symbol} was delisted on {info['delisted']} "
                        f"({info['reason']}). Consider including in analysis for period before delisting."
                    )
        
        # General warning if analyzing only current constituents
        if len(symbols) > 10 and not any(cls.is_delisted(s) for s in symbols):
            warnings.append(
                "Warning: Analyzing only current constituents may introduce survivorship bias. "
                "Consider including delisted securities for historical analysis."
            )
        
        return warnings


# ============================================================================
# CALENDAR DATA
# ============================================================================

class FinancialCalendar:
    """Financial calendar for events."""
    
    @staticmethod
    async def get_earnings_calendar(
        symbols: List[str],
        start: date,
        end: date,
    ) -> List[Dict[str, Any]]:
        """Get earnings calendar."""
        events = []
        
        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            
            loop = asyncio.get_event_loop()
            calendar = await loop.run_in_executor(None, lambda: ticker.calendar)
            
            if calendar is not None and not calendar.empty:
                for col in calendar.columns:
                    event_date = calendar[col].get("Earnings Date")
                    if event_date:
                        events.append({
                            "symbol": symbol,
                            "event_type": "earnings",
                            "date": event_date,
                            "details": calendar[col].to_dict(),
                        })
        
        return events
    
    @staticmethod
    async def get_dividend_calendar(
        symbols: List[str],
        lookback_days: int = 90,
    ) -> List[Dict[str, Any]]:
        """Get upcoming dividends."""
        events = []
        
        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, lambda: ticker.info)
            
            if info.get("dividendDate"):
                events.append({
                    "symbol": symbol,
                    "event_type": "dividend",
                    "date": datetime.fromtimestamp(info["dividendDate"]).date(),
                    "amount": info.get("dividendRate"),
                    "yield": info.get("dividendYield"),
                })
        
        return events
