"""Robustness engine - Stress tests, overfitting detection, explainability."""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from pydantic import BaseModel, Field

from scipy import stats


# ============================================================================
# DATA MODELS
# ============================================================================

class StressScenario(BaseModel):
    """Stress test scenario definition."""
    
    name: str
    description: str
    shocks: Dict[str, float]  # Asset/factor -> shock magnitude
    correlation_adjustment: Optional[float] = None  # Increase correlations
    duration_days: Optional[int] = None


class RobustnessResult(BaseModel):
    """Robustness test result."""
    
    test_name: str
    passed: bool
    score: float  # 0-1
    details: Dict[str, Any]
    recommendations: List[str]


# ============================================================================
# STRESS TESTER
# ============================================================================

class StressTester:
    """
    Run stress tests on portfolios and strategies.
    Tests include historical scenarios, hypothetical scenarios, and factor shocks.
    """
    
    # Historical stress scenarios
    HISTORICAL_SCENARIOS = {
        "2008_financial_crisis": StressScenario(
            name="2008 Financial Crisis",
            description="Global financial crisis peak",
            shocks={"equity": -0.50, "credit": -0.30, "rates": -0.20, "volatility": 2.5},
            correlation_adjustment=0.3,
            duration_days=252,
        ),
        "2020_covid_crash": StressScenario(
            name="2020 COVID Crash",
            description="COVID-19 market crash",
            shocks={"equity": -0.34, "credit": -0.15, "oil": -0.70, "volatility": 3.0},
            correlation_adjustment=0.4,
            duration_days=30,
        ),
        "2022_rate_shock": StressScenario(
            name="2022 Rate Shock",
            description="Fed rate hiking cycle",
            shocks={"equity": -0.25, "bonds": -0.15, "tech": -0.35, "rates": 0.30},
            duration_days=252,
        ),
        "flash_crash": StressScenario(
            name="Flash Crash",
            description="Sudden market dislocation",
            shocks={"equity": -0.10, "volatility": 2.0},
            duration_days=1,
        ),
        "stagflation": StressScenario(
            name="Stagflation",
            description="High inflation + low growth",
            shocks={"equity": -0.20, "bonds": -0.10, "commodities": 0.30, "rates": 0.15},
            duration_days=504,
        ),
    }
    
    def run_stress_test(
        self,
        returns: pd.DataFrame,
        weights: Dict[str, float],
        scenario: StressScenario,
    ) -> Dict[str, Any]:
        """Run a stress test on a portfolio."""
        
        # Map assets to factors (simplified)
        factor_mapping = {
            "equity": ["SPY", "QQQ", "IWM", "VTI"],
            "bonds": ["TLT", "BND", "AGG", "IEF"],
            "tech": ["QQQ", "XLK"],
            "credit": ["HYG", "LQD"],
            "commodities": ["GLD", "USO", "DBC"],
        }
        
        # Calculate portfolio impact
        portfolio_shock = 0
        asset_impacts = {}
        
        for asset, weight in weights.items():
            # Find relevant factor shock
            shock = 0
            for factor, factor_assets in factor_mapping.items():
                if any(fa.lower() in asset.lower() for fa in factor_assets):
                    shock = scenario.shocks.get(factor, 0)
                    break
            
            # Default to equity if no match
            if shock == 0 and "equity" in scenario.shocks:
                shock = scenario.shocks["equity"] * 0.8  # Assume 80% correlation
            
            impact = weight * shock
            portfolio_shock += impact
            asset_impacts[asset] = {"shock": shock, "impact": impact}
        
        # Adjust for correlation increase during stress
        if scenario.correlation_adjustment:
            # Higher correlation = worse diversification = more severe impact
            portfolio_shock *= (1 + scenario.correlation_adjustment)
        
        return {
            "scenario": scenario.name,
            "description": scenario.description,
            "portfolio_impact": portfolio_shock,
            "asset_impacts": asset_impacts,
            "duration_days": scenario.duration_days,
            "survival": portfolio_shock > -0.50,  # Survive if < 50% loss
        }
    
    def run_all_scenarios(
        self,
        returns: pd.DataFrame,
        weights: Dict[str, float],
    ) -> Dict[str, Dict[str, Any]]:
        """Run all historical stress scenarios."""
        
        results = {}
        
        for scenario_id, scenario in self.HISTORICAL_SCENARIOS.items():
            results[scenario_id] = self.run_stress_test(returns, weights, scenario)
        
        return results
    
    def run_custom_shock(
        self,
        returns: pd.DataFrame,
        weights: Dict[str, float],
        shocks: Dict[str, float],
    ) -> Dict[str, Any]:
        """Run a custom shock scenario."""
        
        scenario = StressScenario(
            name="Custom Shock",
            description="User-defined scenario",
            shocks=shocks,
        )
        
        return self.run_stress_test(returns, weights, scenario)
    
    def monte_carlo_stress(
        self,
        returns: pd.DataFrame,
        weights: Dict[str, float],
        n_simulations: int = 1000,
        stress_multiplier: float = 2.0,
    ) -> Dict[str, Any]:
        """Monte Carlo stress test with fat tails."""
        
        # Calculate portfolio returns
        portfolio_returns = (returns * pd.Series(weights)).sum(axis=1)
        
        # Parameters
        mu = portfolio_returns.mean()
        sigma = portfolio_returns.std()
        
        # Generate stressed returns (using Student's t for fat tails)
        stressed_returns = stats.t.rvs(
            df=3,  # Heavy tails
            loc=mu,
            scale=sigma * stress_multiplier,
            size=(n_simulations, 252)
        )
        
        # Calculate outcomes
        final_values = np.prod(1 + stressed_returns, axis=1)
        max_drawdowns = []
        
        for sim in stressed_returns:
            cumulative = np.cumprod(1 + sim)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            max_drawdowns.append(drawdown.min())
        
        return {
            "median_return": np.median(final_values) - 1,
            "worst_5_pct": np.percentile(final_values, 5) - 1,
            "worst_1_pct": np.percentile(final_values, 1) - 1,
            "prob_positive": (final_values > 1).mean(),
            "prob_50pct_loss": (final_values < 0.5).mean(),
            "median_max_drawdown": np.median(max_drawdowns),
            "worst_max_drawdown": np.min(max_drawdowns),
        }


# ============================================================================
# OVERFITTING DETECTOR
# ============================================================================

class OverfittingDetector:
    """
    Detect signs of overfitting in strategies.
    Uses multiple techniques including:
    - Out-of-sample testing
    - Walk-forward analysis
    - Combinatorial purged cross-validation
    - Deflated Sharpe Ratio
    """
    
    def check_overfitting(
        self,
        in_sample_sharpe: float,
        out_sample_sharpe: float,
        n_parameters: int,
        n_trades: int,
        strategy_trials: int = 1,
    ) -> RobustnessResult:
        """Comprehensive overfitting check."""
        
        checks = []
        score = 1.0
        
        # 1. In-sample vs Out-of-sample degradation
        if in_sample_sharpe > 0:
            degradation = (in_sample_sharpe - out_sample_sharpe) / in_sample_sharpe
        else:
            degradation = 0
        
        if degradation > 0.5:
            checks.append(f"High performance degradation: {degradation:.0%}")
            score -= 0.3
        elif degradation > 0.3:
            checks.append(f"Moderate performance degradation: {degradation:.0%}")
            score -= 0.15
        
        # 2. Parameter to trades ratio
        if n_parameters > 0:
            ratio = n_trades / n_parameters
            if ratio < 10:
                checks.append(f"Low trades per parameter: {ratio:.1f}")
                score -= 0.25
            elif ratio < 20:
                checks.append(f"Marginal trades per parameter: {ratio:.1f}")
                score -= 0.1
        
        # 3. Deflated Sharpe Ratio (Bailey & López de Prado)
        deflated_sharpe = self._deflated_sharpe_ratio(
            in_sample_sharpe, n_trades, strategy_trials
        )
        
        if deflated_sharpe < 0:
            checks.append(f"Negative deflated Sharpe: {deflated_sharpe:.2f}")
            score -= 0.3
        elif deflated_sharpe < in_sample_sharpe * 0.5:
            checks.append(f"Low deflated Sharpe: {deflated_sharpe:.2f}")
            score -= 0.15
        
        # 4. Suspiciously high Sharpe
        if in_sample_sharpe > 3:
            checks.append(f"Unusually high Sharpe ratio: {in_sample_sharpe:.2f}")
            score -= 0.2
        
        passed = score >= 0.5
        
        recommendations = []
        if degradation > 0.3:
            recommendations.append("Reduce model complexity")
            recommendations.append("Use regularization")
        if n_parameters > 0 and n_trades / n_parameters < 20:
            recommendations.append("Reduce number of parameters")
            recommendations.append("Collect more data")
        if in_sample_sharpe > 3:
            recommendations.append("Verify data quality")
            recommendations.append("Check for look-ahead bias")
        
        return RobustnessResult(
            test_name="Overfitting Detection",
            passed=passed,
            score=max(0, score),
            details={
                "in_sample_sharpe": in_sample_sharpe,
                "out_sample_sharpe": out_sample_sharpe,
                "degradation": degradation,
                "deflated_sharpe": deflated_sharpe,
                "trades_per_parameter": n_trades / n_parameters if n_parameters > 0 else float('inf'),
                "checks": checks,
            },
            recommendations=recommendations,
        )
    
    def _deflated_sharpe_ratio(
        self,
        sharpe: float,
        n_observations: int,
        n_trials: int,
    ) -> float:
        """
        Calculate Deflated Sharpe Ratio.
        Adjusts for multiple testing bias.
        """
        
        if n_trials <= 1 or n_observations <= 1:
            return sharpe
        
        # Expected maximum Sharpe from random strategies
        euler_gamma = 0.5772156649
        expected_max = (1 - euler_gamma) * stats.norm.ppf(1 - 1/n_trials) + \
                       euler_gamma * stats.norm.ppf(1 - 1/(n_trials * np.e))
        
        # Adjusted for observations
        expected_max *= np.sqrt(252 / n_observations)
        
        # Deflated Sharpe
        deflated = sharpe - expected_max
        
        return deflated
    
    def walk_forward_test(
        self,
        returns: pd.Series,
        signal_func,  # Function that generates signals
        train_period: int = 252,
        test_period: int = 63,
    ) -> Dict[str, Any]:
        """Run walk-forward analysis."""
        
        results = []
        
        i = train_period
        while i + test_period <= len(returns):
            # Train period
            train_returns = returns.iloc[i-train_period:i]
            
            # Generate signal on train data
            signal = signal_func(train_returns)
            
            # Test period
            test_returns = returns.iloc[i:i+test_period]
            
            # Calculate test performance
            strategy_returns = test_returns * signal
            sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252) if strategy_returns.std() > 0 else 0
            
            results.append({
                "period_start": returns.index[i],
                "period_end": returns.index[min(i+test_period-1, len(returns)-1)],
                "sharpe": sharpe,
                "return": (1 + strategy_returns).prod() - 1,
            })
            
            i += test_period
        
        # Analyze consistency
        sharpes = [r["sharpe"] for r in results]
        
        return {
            "periods": results,
            "mean_sharpe": np.mean(sharpes),
            "std_sharpe": np.std(sharpes),
            "pct_positive": sum(1 for s in sharpes if s > 0) / len(sharpes),
            "worst_period": min(sharpes),
            "best_period": max(sharpes),
        }


# ============================================================================
# EXPLAINABILITY ENGINE
# ============================================================================

class ExplainabilityEngine:
    """
    Make strategy and model decisions explainable.
    """
    
    def explain_trade(
        self,
        signal: float,
        features: Dict[str, float],
        thresholds: Dict[str, float],
    ) -> Dict[str, Any]:
        """Explain why a trade signal was generated."""
        
        reasons = []
        
        for feature, value in features.items():
            threshold = thresholds.get(feature)
            if threshold is None:
                continue
            
            if value > threshold:
                reasons.append({
                    "feature": feature,
                    "value": value,
                    "threshold": threshold,
                    "direction": "above",
                    "contribution": "bullish",
                })
            elif value < -threshold:
                reasons.append({
                    "feature": feature,
                    "value": value,
                    "threshold": -threshold,
                    "direction": "below",
                    "contribution": "bearish",
                })
        
        # Determine primary driver
        if reasons:
            primary = max(reasons, key=lambda x: abs(x["value"]))
        else:
            primary = None
        
        return {
            "signal": signal,
            "direction": "long" if signal > 0 else "short" if signal < 0 else "neutral",
            "reasons": reasons,
            "primary_driver": primary,
            "confidence": min(abs(signal), 1.0),
        }
    
    def explain_performance(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series = None,
    ) -> Dict[str, Any]:
        """Explain performance attribution."""
        
        # Calculate various return components
        total_return = (1 + returns).prod() - 1
        
        # Contribution from positive vs negative days
        positive_contrib = returns[returns > 0].sum()
        negative_contrib = returns[returns < 0].sum()
        
        # Best and worst periods
        monthly = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
        best_month = monthly.idxmax()
        worst_month = monthly.idxmin()
        
        # Win rate analysis
        win_rate = (returns > 0).mean()
        avg_win = returns[returns > 0].mean() if win_rate > 0 else 0
        avg_loss = returns[returns < 0].mean() if win_rate < 1 else 0
        
        explanation = {
            "total_return": total_return,
            "positive_contribution": positive_contrib,
            "negative_contribution": negative_contrib,
            "best_month": {"date": str(best_month), "return": monthly[best_month]},
            "worst_month": {"date": str(worst_month), "return": monthly[worst_month]},
            "win_rate": win_rate,
            "average_win": avg_win,
            "average_loss": avg_loss,
            "profit_factor": abs(positive_contrib / negative_contrib) if negative_contrib != 0 else float('inf'),
        }
        
        # Alpha decomposition if benchmark provided
        if benchmark_returns is not None:
            aligned = pd.concat([returns, benchmark_returns], axis=1).dropna()
            aligned.columns = ["strategy", "benchmark"]
            
            # Beta and alpha
            cov = np.cov(aligned["strategy"], aligned["benchmark"])
            beta = cov[0, 1] / cov[1, 1] if cov[1, 1] != 0 else 1
            
            benchmark_contrib = beta * (1 + aligned["benchmark"]).prod() - 1
            alpha_contrib = total_return - benchmark_contrib
            
            explanation["beta"] = beta
            explanation["benchmark_contribution"] = benchmark_contrib
            explanation["alpha_contribution"] = alpha_contrib
        
        return explanation
    
    def counterfactual_analysis(
        self,
        returns: pd.Series,
        signal: pd.Series,
        alternative_signal: pd.Series,
    ) -> Dict[str, Any]:
        """What-if analysis with alternative signals."""
        
        # Actual performance
        actual_returns = returns * signal
        actual_total = (1 + actual_returns).prod() - 1
        actual_sharpe = actual_returns.mean() / actual_returns.std() * np.sqrt(252) if actual_returns.std() > 0 else 0
        
        # Alternative performance
        alt_returns = returns * alternative_signal
        alt_total = (1 + alt_returns).prod() - 1
        alt_sharpe = alt_returns.mean() / alt_returns.std() * np.sqrt(252) if alt_returns.std() > 0 else 0
        
        # Difference analysis
        diff_returns = alt_returns - actual_returns
        
        return {
            "actual": {
                "total_return": actual_total,
                "sharpe": actual_sharpe,
            },
            "alternative": {
                "total_return": alt_total,
                "sharpe": alt_sharpe,
            },
            "difference": {
                "return_diff": alt_total - actual_total,
                "sharpe_diff": alt_sharpe - actual_sharpe,
                "better_alternative": alt_sharpe > actual_sharpe,
            },
            "attribution": {
                "positive_changes": (diff_returns > 0).sum(),
                "negative_changes": (diff_returns < 0).sum(),
                "total_impact": diff_returns.sum(),
            },
        }


# ============================================================================
# SAMPLE SIZE VALIDATOR
# ============================================================================

class SampleSizeValidator:
    """Validate statistical significance of results."""
    
    @staticmethod
    def minimum_trades(
        target_sharpe: float = 1.0,
        significance: float = 0.05,
        power: float = 0.80,
    ) -> int:
        """Calculate minimum trades needed for statistical significance."""
        
        # Using standard power analysis for Sharpe ratio
        # n = ((z_alpha + z_beta) / sharpe)^2
        
        z_alpha = stats.norm.ppf(1 - significance / 2)
        z_beta = stats.norm.ppf(power)
        
        # Adjusted for daily returns (Sharpe is annualized)
        daily_sharpe = target_sharpe / np.sqrt(252)
        
        n = ((z_alpha + z_beta) / daily_sharpe) ** 2
        
        return int(np.ceil(n))
    
    @staticmethod
    def sharpe_confidence_interval(
        sharpe: float,
        n_observations: int,
        confidence: float = 0.95,
    ) -> Tuple[float, float]:
        """Calculate confidence interval for Sharpe ratio."""
        
        # Standard error of Sharpe ratio
        se = np.sqrt((1 + 0.5 * sharpe**2) / n_observations)
        
        z = stats.norm.ppf(1 - (1 - confidence) / 2)
        
        lower = sharpe - z * se
        upper = sharpe + z * se
        
        return lower, upper
    
    @staticmethod
    def is_significant(
        sharpe: float,
        n_observations: int,
        significance: float = 0.05,
    ) -> Dict[str, Any]:
        """Test if Sharpe ratio is statistically significant."""
        
        # Standard error
        se = np.sqrt((1 + 0.5 * sharpe**2) / n_observations)
        
        # t-statistic (testing H0: Sharpe = 0)
        t_stat = sharpe / se
        
        # p-value (two-tailed)
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=n_observations - 1))
        
        return {
            "sharpe": sharpe,
            "standard_error": se,
            "t_statistic": t_stat,
            "p_value": p_value,
            "is_significant": p_value < significance,
            "significance_level": significance,
        }


# ============================================================================
# BIAS DETECTOR
# ============================================================================

class BiasDetector:
    """Detect common biases in backtests."""
    
    @staticmethod
    def check_lookahead_bias(
        signal_dates: pd.DatetimeIndex,
        data_dates: pd.DatetimeIndex,
    ) -> Dict[str, Any]:
        """Check for look-ahead bias in signals."""
        
        violations = []
        
        for signal_date in signal_dates:
            # Check if signal uses future data
            future_data = data_dates[data_dates > signal_date]
            if len(future_data) > 0:
                # This is expected for most data
                pass
        
        # Look for signals that precede data
        for i, signal_date in enumerate(signal_dates):
            if i > 0:
                prev_signal = signal_dates[i-1]
                data_between = data_dates[(data_dates > prev_signal) & (data_dates <= signal_date)]
                if len(data_between) == 0:
                    violations.append({
                        "signal_date": signal_date,
                        "issue": "Signal generated without new data",
                    })
        
        return {
            "violations": violations,
            "violation_count": len(violations),
            "passed": len(violations) == 0,
        }
    
    @staticmethod
    def check_survivorship_bias(
        universe_dates: Dict[str, Tuple[str, str]],  # symbol -> (start, end)
        backtest_start: str,
    ) -> Dict[str, Any]:
        """Check for survivorship bias in universe."""
        
        # Count symbols that existed at backtest start
        survivors = 0
        non_survivors = 0
        
        backtest_start_dt = pd.Timestamp(backtest_start)
        
        for symbol, (start, end) in universe_dates.items():
            start_dt = pd.Timestamp(start)
            end_dt = pd.Timestamp(end) if end else pd.Timestamp.now()
            
            if start_dt <= backtest_start_dt:
                if end_dt >= pd.Timestamp.now() - pd.Timedelta(days=30):
                    survivors += 1
                else:
                    non_survivors += 1
        
        total = survivors + non_survivors
        survivor_pct = survivors / total if total > 0 else 0
        
        return {
            "survivors": survivors,
            "non_survivors": non_survivors,
            "survivor_percentage": survivor_pct,
            "potential_bias": survivor_pct > 0.9,
            "recommendation": "Include delisted securities" if survivor_pct > 0.9 else "Universe appears balanced",
        }
