"""Portfolio construction - Optimization, risk engines, position sizing."""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from pydantic import BaseModel, Field

from scipy.optimize import minimize
from scipy import stats


# ============================================================================
# DATA MODELS
# ============================================================================

class OptimizationMethod(str, Enum):
    """Portfolio optimization methods."""
    MEAN_VARIANCE = "mean_variance"
    MIN_VARIANCE = "min_variance"
    MAX_SHARPE = "max_sharpe"
    RISK_PARITY = "risk_parity"
    MAX_DIVERSIFICATION = "max_diversification"
    EQUAL_WEIGHT = "equal_weight"
    HIERARCHICAL_RISK_PARITY = "hrp"


class Constraint(BaseModel):
    """Portfolio constraint."""
    name: str
    type: str  # min_weight, max_weight, sector_max, etc.
    value: float
    assets: Optional[List[str]] = None


class PortfolioResult(BaseModel):
    """Portfolio optimization result."""
    weights: Dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    diversification_ratio: Optional[float] = None
    risk_contributions: Optional[Dict[str, float]] = None
    method: str


# ============================================================================
# PORTFOLIO OPTIMIZER
# ============================================================================

class PortfolioOptimizer:
    """
    Portfolio optimization with multiple methods.
    Supports constraints, transaction costs, and turnover limits.
    """
    
    def __init__(self, risk_free_rate: float = 0.05):
        self.risk_free_rate = risk_free_rate
    
    def optimize(
        self,
        returns: pd.DataFrame,
        method: OptimizationMethod = OptimizationMethod.MAX_SHARPE,
        constraints: Optional[List[Constraint]] = None,
        min_weight: float = 0.0,
        max_weight: float = 1.0,
        current_weights: Optional[Dict[str, float]] = None,
        max_turnover: Optional[float] = None,
    ) -> PortfolioResult:
        """
        Optimize portfolio using specified method.
        
        Args:
            returns: DataFrame of asset returns (columns = assets)
            method: Optimization method to use
            constraints: List of additional constraints
            min_weight: Minimum weight per asset
            max_weight: Maximum weight per asset
            current_weights: Current portfolio weights (for turnover)
            max_turnover: Maximum allowed turnover
        
        Returns:
            PortfolioResult with optimal weights and metrics
        """
        
        assets = returns.columns.tolist()
        n_assets = len(assets)
        
        # Calculate expected returns and covariance
        expected_returns = returns.mean() * 252  # Annualize
        cov_matrix = returns.cov() * 252  # Annualize
        
        # Dispatch to appropriate method
        if method == OptimizationMethod.MEAN_VARIANCE:
            weights = self._mean_variance(expected_returns, cov_matrix, min_weight, max_weight)
        elif method == OptimizationMethod.MIN_VARIANCE:
            weights = self._min_variance(cov_matrix, min_weight, max_weight)
        elif method == OptimizationMethod.MAX_SHARPE:
            weights = self._max_sharpe(expected_returns, cov_matrix, min_weight, max_weight)
        elif method == OptimizationMethod.RISK_PARITY:
            weights = self._risk_parity(cov_matrix)
        elif method == OptimizationMethod.MAX_DIVERSIFICATION:
            weights = self._max_diversification(cov_matrix, min_weight, max_weight)
        elif method == OptimizationMethod.EQUAL_WEIGHT:
            weights = np.array([1.0 / n_assets] * n_assets)
        elif method == OptimizationMethod.HIERARCHICAL_RISK_PARITY:
            weights = self._hierarchical_risk_parity(returns)
        else:
            weights = np.array([1.0 / n_assets] * n_assets)
        
        # Apply turnover constraint if specified
        if max_turnover and current_weights:
            weights = self._apply_turnover_constraint(
                weights, assets, current_weights, max_turnover
            )
        
        # Calculate portfolio metrics
        port_return = np.dot(weights, expected_returns)
        port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe = (port_return - self.risk_free_rate) / port_vol if port_vol > 0 else 0
        
        # Risk contributions
        risk_contrib = self._calculate_risk_contributions(weights, cov_matrix)
        
        # Diversification ratio
        asset_vols = np.sqrt(np.diag(cov_matrix))
        div_ratio = np.dot(weights, asset_vols) / port_vol if port_vol > 0 else 1
        
        return PortfolioResult(
            weights={assets[i]: float(weights[i]) for i in range(n_assets)},
            expected_return=float(port_return),
            volatility=float(port_vol),
            sharpe_ratio=float(sharpe),
            diversification_ratio=float(div_ratio),
            risk_contributions={assets[i]: float(risk_contrib[i]) for i in range(n_assets)},
            method=method.value,
        )
    
    def _mean_variance(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        min_weight: float,
        max_weight: float,
        target_return: Optional[float] = None,
    ) -> np.ndarray:
        """Mean-variance optimization."""
        
        n = len(expected_returns)
        
        # If no target return, maximize return for given risk level
        if target_return is None:
            target_return = expected_returns.mean()
        
        def objective(w):
            return np.dot(w.T, np.dot(cov_matrix, w))
        
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},  # Weights sum to 1
            {"type": "ineq", "fun": lambda w: np.dot(w, expected_returns) - target_return},
        ]
        
        bounds = [(min_weight, max_weight) for _ in range(n)]
        
        x0 = np.array([1.0 / n] * n)
        result = minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=constraints)
        
        return result.x
    
    def _min_variance(
        self,
        cov_matrix: pd.DataFrame,
        min_weight: float,
        max_weight: float,
    ) -> np.ndarray:
        """Minimum variance portfolio."""
        
        n = len(cov_matrix)
        
        def objective(w):
            return np.dot(w.T, np.dot(cov_matrix, w))
        
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
        bounds = [(min_weight, max_weight) for _ in range(n)]
        
        x0 = np.array([1.0 / n] * n)
        result = minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=constraints)
        
        return result.x
    
    def _max_sharpe(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        min_weight: float,
        max_weight: float,
    ) -> np.ndarray:
        """Maximum Sharpe ratio portfolio."""
        
        n = len(expected_returns)
        
        def neg_sharpe(w):
            port_return = np.dot(w, expected_returns)
            port_vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
            if port_vol == 0:
                return 0
            return -(port_return - self.risk_free_rate) / port_vol
        
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
        bounds = [(min_weight, max_weight) for _ in range(n)]
        
        x0 = np.array([1.0 / n] * n)
        result = minimize(neg_sharpe, x0, method="SLSQP", bounds=bounds, constraints=constraints)
        
        return result.x
    
    def _risk_parity(self, cov_matrix: pd.DataFrame) -> np.ndarray:
        """Risk parity - equal risk contribution."""
        
        n = len(cov_matrix)
        
        def risk_budget_objective(w, cov):
            port_var = np.dot(w.T, np.dot(cov, w))
            marginal_contrib = np.dot(cov, w)
            risk_contrib = w * marginal_contrib / np.sqrt(port_var)
            target_risk = np.sqrt(port_var) / n
            return np.sum((risk_contrib - target_risk) ** 2)
        
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
        bounds = [(0.01, 1.0) for _ in range(n)]
        
        x0 = np.array([1.0 / n] * n)
        result = minimize(
            risk_budget_objective, x0, args=(cov_matrix.values,),
            method="SLSQP", bounds=bounds, constraints=constraints
        )
        
        return result.x
    
    def _max_diversification(
        self,
        cov_matrix: pd.DataFrame,
        min_weight: float,
        max_weight: float,
    ) -> np.ndarray:
        """Maximum diversification ratio."""
        
        n = len(cov_matrix)
        asset_vols = np.sqrt(np.diag(cov_matrix))
        
        def neg_div_ratio(w):
            port_vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
            if port_vol == 0:
                return 0
            return -np.dot(w, asset_vols) / port_vol
        
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
        bounds = [(min_weight, max_weight) for _ in range(n)]
        
        x0 = np.array([1.0 / n] * n)
        result = minimize(neg_div_ratio, x0, method="SLSQP", bounds=bounds, constraints=constraints)
        
        return result.x
    
    def _hierarchical_risk_parity(self, returns: pd.DataFrame) -> np.ndarray:
        """Hierarchical Risk Parity (simplified)."""
        
        from scipy.cluster.hierarchy import linkage, leaves_list
        from scipy.spatial.distance import squareform
        
        # Correlation-based distance
        corr = returns.corr()
        dist = np.sqrt(0.5 * (1 - corr))
        
        # Hierarchical clustering
        try:
            linkage_matrix = linkage(squareform(dist), method="single")
            sorted_idx = leaves_list(linkage_matrix)
        except Exception:
            sorted_idx = list(range(len(returns.columns)))
        
        # Allocate using inverse variance
        cov = returns.cov() * 252
        inv_var = 1 / np.diag(cov)
        weights = inv_var / inv_var.sum()
        
        return weights
    
    def _calculate_risk_contributions(
        self,
        weights: np.ndarray,
        cov_matrix: pd.DataFrame,
    ) -> np.ndarray:
        """Calculate risk contribution of each asset."""
        
        port_var = np.dot(weights.T, np.dot(cov_matrix, weights))
        marginal_contrib = np.dot(cov_matrix, weights)
        risk_contrib = weights * marginal_contrib / np.sqrt(port_var)
        
        # Normalize to sum to 1
        return risk_contrib / risk_contrib.sum()
    
    def _apply_turnover_constraint(
        self,
        new_weights: np.ndarray,
        assets: List[str],
        current_weights: Dict[str, float],
        max_turnover: float,
    ) -> np.ndarray:
        """Apply turnover constraint to weights."""
        
        current = np.array([current_weights.get(a, 0) for a in assets])
        turnover = np.sum(np.abs(new_weights - current))
        
        if turnover <= max_turnover:
            return new_weights
        
        # Scale down changes to meet turnover constraint
        scale = max_turnover / turnover
        adjusted = current + scale * (new_weights - current)
        
        # Ensure sum to 1
        return adjusted / adjusted.sum()
    
    def efficient_frontier(
        self,
        returns: pd.DataFrame,
        n_points: int = 20,
        min_weight: float = 0.0,
        max_weight: float = 1.0,
    ) -> List[Tuple[float, float, Dict[str, float]]]:
        """Generate efficient frontier points."""
        
        expected_returns = returns.mean() * 252
        cov_matrix = returns.cov() * 252
        
        # Find min and max achievable returns
        min_ret_weights = self._min_variance(cov_matrix, min_weight, max_weight)
        max_ret_weights = self._mean_variance(
            expected_returns, cov_matrix, min_weight, max_weight,
            target_return=expected_returns.max()
        )
        
        min_ret = np.dot(min_ret_weights, expected_returns)
        max_ret = np.dot(max_ret_weights, expected_returns)
        
        # Generate frontier
        target_returns = np.linspace(min_ret, max_ret, n_points)
        frontier = []
        
        for target in target_returns:
            try:
                weights = self._mean_variance(
                    expected_returns, cov_matrix, min_weight, max_weight, target
                )
                port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                port_ret = np.dot(weights, expected_returns)
                
                weight_dict = {returns.columns[i]: float(weights[i]) 
                              for i in range(len(weights))}
                
                frontier.append((float(port_vol), float(port_ret), weight_dict))
            except Exception:
                continue
        
        return frontier


# ============================================================================
# POSITION SIZING
# ============================================================================

class PositionSizer:
    """Position sizing methods."""
    
    @staticmethod
    def fixed_dollar(
        capital: float,
        price: float,
        allocation: float,
    ) -> int:
        """Fixed dollar amount per position."""
        dollar_amount = capital * allocation
        return int(dollar_amount // price)
    
    @staticmethod
    def volatility_scaled(
        capital: float,
        price: float,
        volatility: float,
        target_vol: float = 0.02,  # 2% daily vol contribution
    ) -> int:
        """Size position based on volatility."""
        dollar_vol = capital * target_vol
        position_vol = price * volatility
        
        if position_vol == 0:
            return 0
        
        shares = dollar_vol / position_vol
        return int(shares)
    
    @staticmethod
    def kelly_criterion(
        capital: float,
        price: float,
        win_rate: float,
        win_loss_ratio: float,
        fraction: float = 0.25,  # Use fraction of full Kelly
    ) -> int:
        """Kelly criterion position sizing."""
        
        # Kelly formula: f* = (bp - q) / b
        # where b = win/loss ratio, p = win probability, q = 1-p
        b = win_loss_ratio
        p = win_rate
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        
        # Apply fractional Kelly
        position_fraction = max(0, min(fraction * kelly_fraction, 0.25))  # Cap at 25%
        
        dollar_amount = capital * position_fraction
        return int(dollar_amount // price)
    
    @staticmethod
    def atr_based(
        capital: float,
        price: float,
        atr: float,
        risk_per_trade: float = 0.01,  # 1% risk per trade
        atr_multiplier: float = 2.0,
    ) -> Tuple[int, float]:
        """ATR-based position sizing with stop loss."""
        
        stop_distance = atr * atr_multiplier
        risk_amount = capital * risk_per_trade
        
        if stop_distance == 0:
            return 0, 0
        
        shares = int(risk_amount / stop_distance)
        stop_price = price - stop_distance
        
        return shares, stop_price


# ============================================================================
# RISK ENGINE
# ============================================================================

class RiskEngine:
    """Portfolio risk management."""
    
    def __init__(self, max_portfolio_var: float = 0.02):
        """
        Args:
            max_portfolio_var: Maximum daily VaR as fraction of portfolio
        """
        self.max_portfolio_var = max_portfolio_var
    
    def check_position(
        self,
        proposed_weight: float,
        asset_vol: float,
        current_weights: Dict[str, float],
        correlation_with_portfolio: float,
        portfolio_vol: float,
    ) -> Tuple[bool, str]:
        """Check if proposed position meets risk limits."""
        
        # Check individual position limit
        if proposed_weight > 0.25:
            return False, "Position exceeds 25% limit"
        
        # Check volatility contribution
        vol_contribution = proposed_weight * asset_vol * correlation_with_portfolio
        if vol_contribution > self.max_portfolio_var:
            return False, f"Volatility contribution ({vol_contribution:.2%}) exceeds limit"
        
        return True, "Position approved"
    
    def calculate_var(
        self,
        returns: pd.DataFrame,
        weights: Dict[str, float],
        confidence: float = 0.95,
        horizon: int = 1,
    ) -> Dict[str, float]:
        """Calculate portfolio VaR and CVaR."""
        
        # Build portfolio returns
        port_returns = (returns * pd.Series(weights)).sum(axis=1)
        
        # Historical VaR
        var = -np.percentile(port_returns, (1 - confidence) * 100) * np.sqrt(horizon)
        
        # CVaR (Expected Shortfall)
        cvar = -port_returns[port_returns <= -var].mean() * np.sqrt(horizon)
        
        # Parametric VaR (assuming normal)
        mu = port_returns.mean() * horizon
        sigma = port_returns.std() * np.sqrt(horizon)
        parametric_var = -(mu + sigma * stats.norm.ppf(1 - confidence))
        
        return {
            "var_historical": float(var),
            "cvar": float(cvar) if not np.isnan(cvar) else float(var) * 1.2,
            "var_parametric": float(parametric_var),
            "confidence": confidence,
            "horizon_days": horizon,
        }
    
    def stress_test(
        self,
        returns: pd.DataFrame,
        weights: Dict[str, float],
        scenarios: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> Dict[str, float]:
        """Run stress tests on portfolio."""
        
        # Default scenarios
        default_scenarios = {
            "market_crash": {"equity": -0.20, "bonds": 0.05, "gold": 0.10},
            "rate_spike": {"equity": -0.10, "bonds": -0.15, "gold": -0.05},
            "volatility_spike": {"equity": -0.15, "bonds": 0.02, "gold": 0.05},
            "stagflation": {"equity": -0.12, "bonds": -0.08, "gold": 0.15},
        }
        
        scenarios = scenarios or default_scenarios
        
        results = {}
        for scenario_name, shocks in scenarios.items():
            # Apply shocks (simplified - assumes assets match categories)
            portfolio_impact = 0
            for asset, weight in weights.items():
                # Map asset to category (simplified)
                category = "equity"  # Default
                if "TLT" in asset or "BND" in asset:
                    category = "bonds"
                elif "GLD" in asset or "GOLD" in asset:
                    category = "gold"
                
                shock = shocks.get(category, 0)
                portfolio_impact += weight * shock
            
            results[scenario_name] = portfolio_impact
        
        return results
    
    def hedge_suggestions(
        self,
        returns: pd.DataFrame,
        weights: Dict[str, float],
        hedge_universe: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """Suggest hedges for the portfolio."""
        
        hedge_universe = hedge_universe or ["SH", "TLT", "GLD", "VXX"]
        
        # Build portfolio returns
        assets_in_portfolio = [a for a in weights.keys() if a in returns.columns]
        port_returns = (returns[assets_in_portfolio] * pd.Series({
            a: weights[a] for a in assets_in_portfolio
        })).sum(axis=1)
        
        suggestions = []
        
        for hedge in hedge_universe:
            if hedge not in returns.columns:
                continue
            
            hedge_returns = returns[hedge]
            
            # Align data
            aligned = pd.concat([port_returns, hedge_returns], axis=1).dropna()
            if len(aligned) < 30:
                continue
            
            corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
            
            # Good hedges have negative correlation
            if corr < -0.3:
                # Calculate hedge ratio
                cov = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])
                hedge_ratio = -cov[0, 1] / cov[1, 1] if cov[1, 1] != 0 else 0
                
                suggestions.append({
                    "asset": hedge,
                    "correlation": corr,
                    "hedge_ratio": hedge_ratio,
                    "effectiveness": abs(corr),
                })
        
        return sorted(suggestions, key=lambda x: x["effectiveness"], reverse=True)


# ============================================================================
# REBALANCING ENGINE
# ============================================================================

class RebalancingEngine:
    """Portfolio rebalancing logic."""
    
    def __init__(
        self,
        threshold: float = 0.05,  # 5% drift threshold
        min_trade: float = 1000,  # Minimum trade size
        tax_aware: bool = False,
    ):
        self.threshold = threshold
        self.min_trade = min_trade
        self.tax_aware = tax_aware
    
    def check_rebalance_needed(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
    ) -> Tuple[bool, Dict[str, float]]:
        """Check if rebalancing is needed."""
        
        drifts = {}
        max_drift = 0
        
        for asset in set(current_weights.keys()) | set(target_weights.keys()):
            current = current_weights.get(asset, 0)
            target = target_weights.get(asset, 0)
            drift = current - target
            drifts[asset] = drift
            max_drift = max(max_drift, abs(drift))
        
        needs_rebalance = max_drift > self.threshold
        
        return needs_rebalance, drifts
    
    def generate_trades(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        portfolio_value: float,
        prices: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """Generate trades to rebalance portfolio."""
        
        trades = []
        
        for asset in set(current_weights.keys()) | set(target_weights.keys()):
            current = current_weights.get(asset, 0)
            target = target_weights.get(asset, 0)
            
            diff_weight = target - current
            diff_value = diff_weight * portfolio_value
            
            if abs(diff_value) < self.min_trade:
                continue
            
            price = prices.get(asset, 0)
            if price == 0:
                continue
            
            shares = int(diff_value / price)
            
            if shares != 0:
                trades.append({
                    "asset": asset,
                    "action": "buy" if shares > 0 else "sell",
                    "shares": abs(shares),
                    "notional": abs(diff_value),
                    "price": price,
                })
        
        return trades
    
    def calendar_rebalance(
        self,
        frequency: str = "quarterly",
        last_rebalance: Optional[str] = None,
    ) -> bool:
        """Check if calendar-based rebalance is due."""
        
        from datetime import datetime, timedelta
        
        if last_rebalance is None:
            return True
        
        last = datetime.fromisoformat(last_rebalance)
        now = datetime.now()
        
        if frequency == "monthly":
            return (now - last).days >= 28
        elif frequency == "quarterly":
            return (now - last).days >= 90
        elif frequency == "annually":
            return (now - last).days >= 365
        
        return False
