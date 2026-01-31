"""Monitoring system - Watchlists, alerts, drift detection."""

import asyncio
import json
import os
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


# ============================================================================
# DATA MODELS
# ============================================================================

class AlertType(str, Enum):
    """Types of alerts."""
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PERCENT_CHANGE = "percent_change"
    VOLUME_SPIKE = "volume_spike"
    VOLATILITY_SPIKE = "volatility_spike"
    MOVING_AVERAGE_CROSS = "ma_cross"
    RSI_OVERSOLD = "rsi_oversold"
    RSI_OVERBOUGHT = "rsi_overbought"
    DRAWDOWN = "drawdown"
    NEW_HIGH = "new_high"
    NEW_LOW = "new_low"
    CORRELATION_BREAK = "correlation_break"
    DRIFT_DETECTED = "drift_detected"


class AlertPriority(str, Enum):
    """Alert priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Alert(BaseModel):
    """Alert configuration."""
    
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S%f"))
    symbol: str
    alert_type: AlertType
    threshold: float
    priority: AlertPriority = AlertPriority.MEDIUM
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    cooldown_minutes: int = 60  # Don't re-trigger within this period
    message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AlertNotification(BaseModel):
    """Alert notification event."""
    
    alert_id: str
    symbol: str
    alert_type: AlertType
    priority: AlertPriority
    message: str
    current_value: float
    threshold: float
    triggered_at: datetime = Field(default_factory=datetime.now)


class WatchlistItem(BaseModel):
    """Item in a watchlist."""
    
    symbol: str
    added_at: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None
    target_price: Optional[float] = None
    stop_price: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    alerts: List[str] = Field(default_factory=list)  # Alert IDs


class Watchlist(BaseModel):
    """A watchlist of securities."""
    
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S"))
    name: str
    description: Optional[str] = None
    items: List[WatchlistItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# ============================================================================
# ALERT ENGINE
# ============================================================================

class AlertEngine:
    """
    Monitor markets and trigger alerts.
    Supports price alerts, technical alerts, and custom conditions.
    """
    
    def __init__(self, storage_dir: str = None):
        self.storage_dir = Path(storage_dir or os.path.expanduser("~/.sigma/alerts"))
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.alerts: Dict[str, Alert] = {}
        self.notification_handlers: List[Callable[[AlertNotification], None]] = []
        self._load_alerts()
    
    def _load_alerts(self):
        """Load alerts from storage."""
        
        alerts_file = self.storage_dir / "alerts.json"
        if alerts_file.exists():
            data = json.loads(alerts_file.read_text())
            for alert_data in data:
                alert = Alert(**alert_data)
                self.alerts[alert.id] = alert
    
    def _save_alerts(self):
        """Save alerts to storage."""
        
        alerts_file = self.storage_dir / "alerts.json"
        data = [alert.model_dump() for alert in self.alerts.values()]
        alerts_file.write_text(json.dumps(data, indent=2, default=str))
    
    def add_alert(self, alert: Alert) -> str:
        """Add a new alert."""
        
        self.alerts[alert.id] = alert
        self._save_alerts()
        return alert.id
    
    def remove_alert(self, alert_id: str) -> bool:
        """Remove an alert."""
        
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            self._save_alerts()
            return True
        return False
    
    def enable_alert(self, alert_id: str, enabled: bool = True):
        """Enable or disable an alert."""
        
        if alert_id in self.alerts:
            self.alerts[alert_id].enabled = enabled
            self._save_alerts()
    
    def add_notification_handler(self, handler: Callable[[AlertNotification], None]):
        """Add a notification handler."""
        
        self.notification_handlers.append(handler)
    
    async def check_alerts(self, market_data: Dict[str, Dict[str, Any]]) -> List[AlertNotification]:
        """
        Check all alerts against current market data.
        
        Args:
            market_data: Dict of symbol -> current data
        
        Returns:
            List of triggered notifications
        """
        
        notifications = []
        now = datetime.now()
        
        for alert_id, alert in self.alerts.items():
            if not alert.enabled:
                continue
            
            # Check cooldown
            if alert.last_triggered:
                cooldown_end = alert.last_triggered + timedelta(minutes=alert.cooldown_minutes)
                if now < cooldown_end:
                    continue
            
            # Get market data for symbol
            data = market_data.get(alert.symbol)
            if not data:
                continue
            
            # Check alert condition
            triggered, current_value, message = self._check_alert_condition(alert, data)
            
            if triggered:
                # Create notification
                notification = AlertNotification(
                    alert_id=alert.id,
                    symbol=alert.symbol,
                    alert_type=alert.alert_type,
                    priority=alert.priority,
                    message=message or alert.message or f"{alert.alert_type.value} triggered",
                    current_value=current_value,
                    threshold=alert.threshold,
                )
                
                notifications.append(notification)
                
                # Update alert
                alert.last_triggered = now
                alert.trigger_count += 1
                
                # Notify handlers
                for handler in self.notification_handlers:
                    try:
                        handler(notification)
                    except Exception as e:
                        print(f"Notification handler error: {e}")
        
        self._save_alerts()
        return notifications
    
    def _check_alert_condition(
        self,
        alert: Alert,
        data: Dict[str, Any],
    ) -> tuple[bool, float, str]:
        """Check if alert condition is met."""
        
        current_price = data.get("price", data.get("close", 0))
        
        if alert.alert_type == AlertType.PRICE_ABOVE:
            if current_price > alert.threshold:
                return True, current_price, f"{alert.symbol} above ${alert.threshold:.2f} (${current_price:.2f})"
        
        elif alert.alert_type == AlertType.PRICE_BELOW:
            if current_price < alert.threshold:
                return True, current_price, f"{alert.symbol} below ${alert.threshold:.2f} (${current_price:.2f})"
        
        elif alert.alert_type == AlertType.PERCENT_CHANGE:
            change = data.get("change_percent", 0)
            if abs(change) > alert.threshold:
                direction = "up" if change > 0 else "down"
                return True, change, f"{alert.symbol} {direction} {abs(change):.1f}%"
        
        elif alert.alert_type == AlertType.VOLUME_SPIKE:
            volume = data.get("volume", 0)
            avg_volume = data.get("avg_volume", volume)
            if avg_volume > 0 and volume / avg_volume > alert.threshold:
                multiple = volume / avg_volume
                return True, multiple, f"{alert.symbol} volume {multiple:.1f}x average"
        
        elif alert.alert_type == AlertType.VOLATILITY_SPIKE:
            volatility = data.get("volatility", 0)
            if volatility > alert.threshold:
                return True, volatility, f"{alert.symbol} volatility at {volatility:.1%}"
        
        elif alert.alert_type == AlertType.RSI_OVERSOLD:
            rsi = data.get("rsi", 50)
            if rsi < alert.threshold:
                return True, rsi, f"{alert.symbol} RSI oversold at {rsi:.1f}"
        
        elif alert.alert_type == AlertType.RSI_OVERBOUGHT:
            rsi = data.get("rsi", 50)
            if rsi > alert.threshold:
                return True, rsi, f"{alert.symbol} RSI overbought at {rsi:.1f}"
        
        elif alert.alert_type == AlertType.DRAWDOWN:
            drawdown = data.get("drawdown", 0)
            if abs(drawdown) > alert.threshold:
                return True, drawdown, f"{alert.symbol} drawdown at {abs(drawdown):.1%}"
        
        elif alert.alert_type == AlertType.NEW_HIGH:
            high_52w = data.get("52w_high", float('inf'))
            if current_price >= high_52w * (1 - alert.threshold / 100):
                return True, current_price, f"{alert.symbol} near 52-week high"
        
        elif alert.alert_type == AlertType.NEW_LOW:
            low_52w = data.get("52w_low", 0)
            if current_price <= low_52w * (1 + alert.threshold / 100):
                return True, current_price, f"{alert.symbol} near 52-week low"
        
        return False, 0, ""
    
    def get_alerts_for_symbol(self, symbol: str) -> List[Alert]:
        """Get all alerts for a symbol."""
        
        return [a for a in self.alerts.values() if a.symbol == symbol]
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        
        return [a for a in self.alerts.values() if a.enabled]


# ============================================================================
# WATCHLIST MANAGER
# ============================================================================

class WatchlistManager:
    """Manage watchlists."""
    
    def __init__(self, storage_dir: str = None):
        self.storage_dir = Path(storage_dir or os.path.expanduser("~/.sigma/watchlists"))
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.watchlists: Dict[str, Watchlist] = {}
        self._load_watchlists()
    
    def _load_watchlists(self):
        """Load watchlists from storage."""
        
        for file in self.storage_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text())
                watchlist = Watchlist(**data)
                self.watchlists[watchlist.id] = watchlist
            except Exception as e:
                print(f"Error loading watchlist {file}: {e}")
    
    def _save_watchlist(self, watchlist: Watchlist):
        """Save a watchlist to storage."""
        
        filepath = self.storage_dir / f"{watchlist.id}.json"
        filepath.write_text(watchlist.model_dump_json(indent=2))
    
    def create_watchlist(self, name: str, description: str = None) -> Watchlist:
        """Create a new watchlist."""
        
        watchlist = Watchlist(name=name, description=description)
        self.watchlists[watchlist.id] = watchlist
        self._save_watchlist(watchlist)
        return watchlist
    
    def delete_watchlist(self, watchlist_id: str) -> bool:
        """Delete a watchlist."""
        
        if watchlist_id in self.watchlists:
            del self.watchlists[watchlist_id]
            filepath = self.storage_dir / f"{watchlist_id}.json"
            if filepath.exists():
                filepath.unlink()
            return True
        return False
    
    def add_to_watchlist(
        self,
        watchlist_id: str,
        symbol: str,
        notes: str = None,
        target_price: float = None,
        stop_price: float = None,
        tags: List[str] = None,
    ) -> bool:
        """Add a symbol to a watchlist."""
        
        if watchlist_id not in self.watchlists:
            return False
        
        watchlist = self.watchlists[watchlist_id]
        
        # Check if already in watchlist
        if any(item.symbol == symbol for item in watchlist.items):
            return False
        
        item = WatchlistItem(
            symbol=symbol,
            notes=notes,
            target_price=target_price,
            stop_price=stop_price,
            tags=tags or [],
        )
        
        watchlist.items.append(item)
        watchlist.updated_at = datetime.now()
        self._save_watchlist(watchlist)
        
        return True
    
    def remove_from_watchlist(self, watchlist_id: str, symbol: str) -> bool:
        """Remove a symbol from a watchlist."""
        
        if watchlist_id not in self.watchlists:
            return False
        
        watchlist = self.watchlists[watchlist_id]
        original_length = len(watchlist.items)
        watchlist.items = [item for item in watchlist.items if item.symbol != symbol]
        
        if len(watchlist.items) < original_length:
            watchlist.updated_at = datetime.now()
            self._save_watchlist(watchlist)
            return True
        
        return False
    
    def get_watchlist(self, watchlist_id: str) -> Optional[Watchlist]:
        """Get a watchlist by ID."""
        
        return self.watchlists.get(watchlist_id)
    
    def get_all_watchlists(self) -> List[Watchlist]:
        """Get all watchlists."""
        
        return list(self.watchlists.values())
    
    def get_all_symbols(self) -> List[str]:
        """Get all unique symbols across all watchlists."""
        
        symbols = set()
        for watchlist in self.watchlists.values():
            for item in watchlist.items:
                symbols.add(item.symbol)
        return list(symbols)


# ============================================================================
# DRIFT DETECTOR
# ============================================================================

class DriftDetector:
    """
    Detect drift in portfolios and strategies.
    Monitors for changes in:
    - Portfolio weights
    - Risk characteristics
    - Return patterns
    - Correlations
    """
    
    def __init__(
        self,
        weight_threshold: float = 0.05,
        volatility_threshold: float = 0.5,
        correlation_threshold: float = 0.3,
    ):
        self.weight_threshold = weight_threshold
        self.volatility_threshold = volatility_threshold
        self.correlation_threshold = correlation_threshold
    
    def check_weight_drift(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
    ) -> Dict[str, Any]:
        """Check for portfolio weight drift."""
        
        drifts = {}
        max_drift = 0
        
        all_assets = set(current_weights.keys()) | set(target_weights.keys())
        
        for asset in all_assets:
            current = current_weights.get(asset, 0)
            target = target_weights.get(asset, 0)
            drift = current - target
            drifts[asset] = drift
            max_drift = max(max_drift, abs(drift))
        
        needs_rebalance = max_drift > self.weight_threshold
        
        return {
            "drifts": drifts,
            "max_drift": max_drift,
            "needs_rebalance": needs_rebalance,
            "threshold": self.weight_threshold,
        }
    
    def check_volatility_drift(
        self,
        current_vol: float,
        historical_vol: float,
    ) -> Dict[str, Any]:
        """Check for volatility regime change."""
        
        if historical_vol == 0:
            return {"drift_detected": False, "reason": "No historical data"}
        
        vol_change = (current_vol - historical_vol) / historical_vol
        drift_detected = abs(vol_change) > self.volatility_threshold
        
        return {
            "current_vol": current_vol,
            "historical_vol": historical_vol,
            "change": vol_change,
            "drift_detected": drift_detected,
            "direction": "up" if vol_change > 0 else "down",
            "threshold": self.volatility_threshold,
        }
    
    def check_correlation_drift(
        self,
        current_corr: pd.DataFrame,
        historical_corr: pd.DataFrame,
    ) -> Dict[str, Any]:
        """Check for correlation breakdown."""
        
        # Calculate correlation changes
        corr_diff = current_corr - historical_corr
        
        # Find significant changes
        significant_changes = []
        
        for i in range(len(corr_diff.columns)):
            for j in range(i + 1, len(corr_diff.columns)):
                asset1 = corr_diff.columns[i]
                asset2 = corr_diff.columns[j]
                change = corr_diff.iloc[i, j]
                
                if abs(change) > self.correlation_threshold:
                    significant_changes.append({
                        "asset1": asset1,
                        "asset2": asset2,
                        "change": change,
                        "current": current_corr.iloc[i, j],
                        "historical": historical_corr.iloc[i, j],
                    })
        
        return {
            "drift_detected": len(significant_changes) > 0,
            "significant_changes": significant_changes,
            "threshold": self.correlation_threshold,
        }
    
    def check_strategy_drift(
        self,
        recent_returns: pd.Series,
        historical_returns: pd.Series,
    ) -> Dict[str, Any]:
        """Check for strategy performance drift."""
        
        # Calculate rolling stats
        recent_mean = recent_returns.mean() * 252
        recent_vol = recent_returns.std() * np.sqrt(252)
        recent_sharpe = recent_mean / recent_vol if recent_vol > 0 else 0
        
        historical_mean = historical_returns.mean() * 252
        historical_vol = historical_returns.std() * np.sqrt(252)
        historical_sharpe = historical_mean / historical_vol if historical_vol > 0 else 0
        
        # Detect drift
        return_drift = recent_mean - historical_mean
        vol_drift = recent_vol - historical_vol
        sharpe_drift = recent_sharpe - historical_sharpe
        
        # Significant if Sharpe dropped by more than 0.5
        drift_detected = sharpe_drift < -0.5
        
        return {
            "drift_detected": drift_detected,
            "metrics": {
                "recent_return": recent_mean,
                "historical_return": historical_mean,
                "return_drift": return_drift,
                "recent_vol": recent_vol,
                "historical_vol": historical_vol,
                "vol_drift": vol_drift,
                "recent_sharpe": recent_sharpe,
                "historical_sharpe": historical_sharpe,
                "sharpe_drift": sharpe_drift,
            },
        }


# ============================================================================
# SCHEDULED RUNNER
# ============================================================================

class ScheduledRunner:
    """Run scheduled analysis tasks."""
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.running = False
    
    def add_task(
        self,
        task_id: str,
        func: Callable,
        schedule: str,  # daily, weekly, monthly
        time: str = "09:00",  # HH:MM
        args: tuple = None,
        kwargs: dict = None,
    ):
        """Add a scheduled task."""
        
        self.tasks[task_id] = {
            "func": func,
            "schedule": schedule,
            "time": time,
            "args": args or (),
            "kwargs": kwargs or {},
            "last_run": None,
            "enabled": True,
        }
    
    def remove_task(self, task_id: str):
        """Remove a scheduled task."""
        
        if task_id in self.tasks:
            del self.tasks[task_id]
    
    def enable_task(self, task_id: str, enabled: bool = True):
        """Enable or disable a task."""
        
        if task_id in self.tasks:
            self.tasks[task_id]["enabled"] = enabled
    
    async def run_once(self):
        """Check and run due tasks once."""
        
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        for task_id, task in self.tasks.items():
            if not task["enabled"]:
                continue
            
            # Check if task is due
            if self._is_task_due(task, now):
                try:
                    result = task["func"](*task["args"], **task["kwargs"])
                    if asyncio.iscoroutine(result):
                        await result
                    task["last_run"] = now
                except Exception as e:
                    print(f"Task {task_id} failed: {e}")
    
    def _is_task_due(self, task: Dict[str, Any], now: datetime) -> bool:
        """Check if a task is due to run."""
        
        schedule = task["schedule"]
        scheduled_time = task["time"]
        last_run = task["last_run"]
        
        current_time = now.strftime("%H:%M")
        
        # Check if time matches (within 1 minute)
        if current_time != scheduled_time:
            return False
        
        # Check if already run today
        if last_run and last_run.date() == now.date():
            return False
        
        # Check schedule
        if schedule == "daily":
            return True
        elif schedule == "weekly":
            # Run on Monday
            return now.weekday() == 0
        elif schedule == "monthly":
            # Run on 1st of month
            return now.day == 1
        
        return False
    
    async def run_continuous(self, check_interval: int = 60):
        """Run continuously, checking for due tasks."""
        
        self.running = True
        
        while self.running:
            await self.run_once()
            await asyncio.sleep(check_interval)
    
    def stop(self):
        """Stop the continuous runner."""
        
        self.running = False
