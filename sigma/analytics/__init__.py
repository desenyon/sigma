"""Advanced analytics module for Sigma."""

import asyncio
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform


# ============================================================================
# PERFORMANCE ANALYTICS
# ============================================================================

class PerformanceAnalytics:
    """Comprehensive performance metrics calculation."""
    
    @staticmethod
    def calculate_metrics(
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252,
    ) -> Dict[str, float]:
        """Calculate comprehensive performance metrics."""
        
        # Clean returns
        returns = returns.dropna()
        n = len(returns)
        
        if n < 2:
            return {}
        
        # Basic metrics
        total_return = (1 + returns).prod() - 1
        cagr = (1 + total_return) ** (periods_per_year / n) - 1
        volatility = returns.std() * np.sqrt(periods_per_year)
        
        # Downside metrics
        negative_returns = returns[returns < 0]
        downside_deviation = negative_returns.std() * np.sqrt(periods_per_year) if len(negative_returns) > 0 else 0
        
        # Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Drawdown duration
        in_drawdown = drawdown < 0
        dd_groups = (in_drawdown != in_drawdown.shift()).cumsum()
        dd_durations = in_drawdown.groupby(dd_groups).sum()
        max_dd_duration = dd_durations.max() if len(dd_durations) > 0 else 0
        
        # Risk-adjusted metrics
        excess_return = cagr - risk_free_rate
        sharpe = excess_return / volatility if volatility > 0 else 0
        sortino = excess_return / downside_deviation if downside_deviation > 0 else 0
        calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # VaR and CVaR
        var_95 = returns.quantile(0.05)
        cvar_95 = returns[returns <= var_95].mean() if len(returns[returns <= var_95]) > 0 else var_95
        
        # Win rate
        win_rate = (returns > 0).mean()
        
        # Profit factor
        gains = returns[returns > 0].sum()
        losses = abs(returns[returns < 0].sum())
        profit_factor = gains / losses if losses > 0 else float('inf')
        
        metrics = {
            "total_return": total_return,
            "cagr": cagr,
            "volatility": volatility,
            "downside_deviation": downside_deviation,
            "max_drawdown": max_drawdown,
            "max_dd_duration": int(max_dd_duration),
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "calmar_ratio": calmar,
            "var_95": var_95,
            "cvar_95": cvar_95,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
        }
        
        # Beta and alpha if benchmark provided
        if benchmark_returns is not None:
            aligned = pd.concat([returns, benchmark_returns], axis=1).dropna()
            if len(aligned) > 10:
                cov = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])
                beta = cov[0, 1] / cov[1, 1] if cov[1, 1] != 0 else 0
                alpha = cagr - (risk_free_rate + beta * (aligned.iloc[:, 1].mean() * periods_per_year - risk_free_rate))
                
                # R-squared
                correlation = aligned.corr().iloc[0, 1]
                r_squared = correlation ** 2
                
                # Tracking error
                tracking_diff = aligned.iloc[:, 0] - aligned.iloc[:, 1]
                tracking_error = tracking_diff.std() * np.sqrt(periods_per_year)
                
                # Information ratio
                info_ratio = tracking_diff.mean() * periods_per_year / tracking_error if tracking_error > 0 else 0
                
                # Treynor ratio
                treynor = excess_return / beta if beta != 0 else 0
                
                metrics.update({
                    "beta": beta,
                    "alpha": alpha,
                    "r_squared": r_squared,
                    "tracking_error": tracking_error,
                    "information_ratio": info_ratio,
                    "treynor_ratio": treynor,
                })
        
        return metrics
    
    @staticmethod
    def rolling_metrics(
        returns: pd.Series,
        window: int = 252,
        periods_per_year: int = 252,
    ) -> pd.DataFrame:
        """Calculate rolling performance metrics."""
        
        rolling_return = returns.rolling(window).apply(lambda x: (1 + x).prod() - 1)
        rolling_vol = returns.rolling(window).std() * np.sqrt(periods_per_year)
        rolling_sharpe = (rolling_return - 0) / rolling_vol
        
        # Rolling max drawdown
        def max_dd(x):
            cumulative = (1 + x).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            return drawdown.min()
        
        rolling_dd = returns.rolling(window).apply(max_dd)
        
        return pd.DataFrame({
            "rolling_return": rolling_return,
            "rolling_volatility": rolling_vol,
            "rolling_sharpe": rolling_sharpe,
            "rolling_max_dd": rolling_dd,
        })


# ============================================================================
# REGIME DETECTION
# ============================================================================

class RegimeDetector:
    """Detect market regimes using various methods."""
    
    @staticmethod
    def volatility_regime(
        returns: pd.Series,
        short_window: int = 21,
        long_window: int = 63,
        threshold: float = 1.5,
    ) -> pd.Series:
        """Detect volatility regimes."""
        short_vol = returns.rolling(short_window).std()
        long_vol = returns.rolling(long_window).std()
        
        ratio = short_vol / long_vol
        
        regimes = pd.Series(index=returns.index, data="normal")
        regimes[ratio > threshold] = "high_vol"
        regimes[ratio < 1 / threshold] = "low_vol"
        
        return regimes
    
    @staticmethod
    def trend_regime(
        prices: pd.Series,
        short_window: int = 20,
        long_window: int = 50,
    ) -> pd.Series:
        """Detect trend regimes using moving averages."""
        short_ma = prices.rolling(short_window).mean()
        long_ma = prices.rolling(long_window).mean()
        
        regimes = pd.Series(index=prices.index, data="sideways")
        regimes[(short_ma > long_ma) & (prices > short_ma)] = "bull"
        regimes[(short_ma < long_ma) & (prices < short_ma)] = "bear"
        
        return regimes
    
    @staticmethod
    def correlation_regime(
        returns_matrix: pd.DataFrame,
        window: int = 63,
        high_corr_threshold: float = 0.7,
    ) -> pd.Series:
        """Detect correlation regimes (risk-on/risk-off)."""
        
        rolling_corr = returns_matrix.rolling(window).corr()
        
        # Average pairwise correlation over time
        def avg_corr(df):
            if len(df) < window:
                return np.nan
            corr = df.corr()
            mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
            return corr.where(mask).stack().mean()
        
        avg_correlations = returns_matrix.rolling(window).apply(
            lambda x: returns_matrix.loc[x.index].corr().values[np.triu_indices(len(returns_matrix.columns), k=1)].mean(),
            raw=False
        ).mean(axis=1)
        
        regimes = pd.Series(index=returns_matrix.index, data="normal")
        regimes[avg_correlations > high_corr_threshold] = "high_correlation"
        regimes[avg_correlations < 0.3] = "low_correlation"
        
        return regimes
    
    @staticmethod
    def hidden_markov_regime(
        returns: pd.Series,
        n_regimes: int = 2,
    ) -> Tuple[pd.Series, Dict[str, Any]]:
        """Simple regime detection using return distribution clustering."""
        # Simplified HMM-like approach using rolling statistics
        
        window = 21
        rolling_mean = returns.rolling(window).mean()
        rolling_vol = returns.rolling(window).std()
        
        # Classify based on mean and volatility
        combined = pd.DataFrame({
            'mean': rolling_mean,
            'vol': rolling_vol
        }).dropna()
        
        # Simple k-means-like classification
        mean_threshold = combined['mean'].median()
        vol_threshold = combined['vol'].median()
        
        regimes = pd.Series(index=returns.index, data=0)
        
        bull_mask = (combined['mean'] > mean_threshold) & (combined['vol'] < vol_threshold)
        bear_mask = (combined['mean'] < mean_threshold) & (combined['vol'] > vol_threshold)
        
        regimes.loc[bull_mask.index[bull_mask]] = 1  # Bull
        regimes.loc[bear_mask.index[bear_mask]] = -1  # Bear
        
        regime_labels = {-1: "bear", 0: "neutral", 1: "bull"}
        labeled_regimes = regimes.map(regime_labels)
        
        # Transition matrix
        transitions = {}
        for from_regime in regime_labels.values():
            transitions[from_regime] = {}
            for to_regime in regime_labels.values():
                mask = (labeled_regimes.shift(1) == from_regime) & (labeled_regimes == to_regime)
                from_mask = labeled_regimes.shift(1) == from_regime
                prob = mask.sum() / from_mask.sum() if from_mask.sum() > 0 else 0
                transitions[from_regime][to_regime] = prob
        
        return labeled_regimes, {"transition_matrix": transitions}


# ============================================================================
# SEASONALITY ANALYSIS
# ============================================================================

class SeasonalityAnalyzer:
    """Analyze seasonal patterns in returns."""
    
    @staticmethod
    def monthly_seasonality(returns: pd.Series) -> Dict[int, Dict[str, float]]:
        """Analyze month-of-year seasonality."""
        monthly = returns.groupby(returns.index.month)
        
        result = {}
        for month in range(1, 13):
            if month in monthly.groups:
                month_returns = monthly.get_group(month)
                result[month] = {
                    "mean_return": month_returns.mean(),
                    "median_return": month_returns.median(),
                    "win_rate": (month_returns > 0).mean(),
                    "volatility": month_returns.std(),
                    "count": len(month_returns),
                    "t_stat": stats.ttest_1samp(month_returns, 0)[0] if len(month_returns) > 1 else 0,
                    "p_value": stats.ttest_1samp(month_returns, 0)[1] if len(month_returns) > 1 else 1,
                }
        
        return result
    
    @staticmethod
    def day_of_week_seasonality(returns: pd.Series) -> Dict[int, Dict[str, float]]:
        """Analyze day-of-week seasonality."""
        daily = returns.groupby(returns.index.dayofweek)
        
        day_names = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday"}
        
        result = {}
        for day in range(5):
            if day in daily.groups:
                day_returns = daily.get_group(day)
                result[day_names[day]] = {
                    "mean_return": day_returns.mean(),
                    "median_return": day_returns.median(),
                    "win_rate": (day_returns > 0).mean(),
                    "count": len(day_returns),
                }
        
        return result
    
    @staticmethod
    def pre_post_event_returns(
        returns: pd.Series,
        event_dates: List[date],
        pre_days: int = 5,
        post_days: int = 5,
    ) -> Dict[str, Any]:
        """Analyze returns around events."""
        
        pre_returns = []
        post_returns = []
        
        for event_date in event_dates:
            event_idx = returns.index.get_indexer([event_date], method='nearest')[0]
            
            if event_idx >= pre_days and event_idx < len(returns) - post_days:
                pre_ret = returns.iloc[event_idx - pre_days:event_idx].sum()
                post_ret = returns.iloc[event_idx:event_idx + post_days].sum()
                pre_returns.append(pre_ret)
                post_returns.append(post_ret)
        
        return {
            "pre_event": {
                "mean": np.mean(pre_returns) if pre_returns else 0,
                "median": np.median(pre_returns) if pre_returns else 0,
                "win_rate": np.mean([r > 0 for r in pre_returns]) if pre_returns else 0,
            },
            "post_event": {
                "mean": np.mean(post_returns) if post_returns else 0,
                "median": np.median(post_returns) if post_returns else 0,
                "win_rate": np.mean([r > 0 for r in post_returns]) if post_returns else 0,
            },
            "events_analyzed": len(pre_returns),
        }


# ============================================================================
# FACTOR ANALYSIS
# ============================================================================

class FactorAnalyzer:
    """Factor exposure and attribution analysis."""
    
    # Standard factor definitions
    FACTORS = {
        "market": "SPY",
        "size": "IWM",  # Small cap proxy
        "value": "IVE",  # S&P 500 Value
        "momentum": "MTUM",  # Momentum factor ETF
        "quality": "QUAL",  # Quality factor ETF
        "low_vol": "USMV",  # Low volatility ETF
    }
    
    @staticmethod
    def calculate_factor_exposures(
        returns: pd.Series,
        factor_returns: Dict[str, pd.Series],
        window: Optional[int] = None,
    ) -> Dict[str, float]:
        """Calculate factor exposures using regression."""
        
        # Align all series
        aligned = pd.DataFrame({"asset": returns})
        for name, factor in factor_returns.items():
            aligned[name] = factor
        
        aligned = aligned.dropna()
        
        if len(aligned) < 30:
            return {}
        
        y = aligned["asset"].values
        X = aligned.drop("asset", axis=1).values
        X = np.column_stack([np.ones(len(X)), X])  # Add intercept
        
        # OLS regression
        try:
            coeffs, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
        except:
            return {}
        
        # R-squared
        y_pred = X @ coeffs
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Residual volatility
        residual_vol = np.std(y - y_pred) * np.sqrt(252)
        
        exposures = {
            "alpha": coeffs[0] * 252,  # Annualized
            "r_squared": r_squared,
            "residual_vol": residual_vol,
        }
        
        factor_names = list(factor_returns.keys())
        for i, name in enumerate(factor_names):
            exposures[f"{name}_beta"] = coeffs[i + 1]
        
        return exposures
    
    @staticmethod
    def rolling_factor_exposures(
        returns: pd.Series,
        factor_returns: Dict[str, pd.Series],
        window: int = 252,
    ) -> pd.DataFrame:
        """Calculate rolling factor exposures."""
        
        results = []
        
        aligned = pd.DataFrame({"asset": returns})
        for name, factor in factor_returns.items():
            aligned[name] = factor
        aligned = aligned.dropna()
        
        for i in range(window, len(aligned)):
            subset = aligned.iloc[i - window:i]
            exposures = FactorAnalyzer.calculate_factor_exposures(
                subset["asset"],
                {k: subset[k] for k in factor_returns.keys()}
            )
            exposures["date"] = aligned.index[i]
            results.append(exposures)
        
        return pd.DataFrame(results).set_index("date") if results else pd.DataFrame()
    
    @staticmethod
    def return_attribution(
        returns: pd.Series,
        factor_returns: Dict[str, pd.Series],
        exposures: Dict[str, float],
    ) -> Dict[str, float]:
        """Attribute returns to factors."""
        
        attribution = {"total_return": returns.sum()}
        
        for factor_name, factor_ret in factor_returns.items():
            beta_key = f"{factor_name}_beta"
            if beta_key in exposures:
                contribution = factor_ret.sum() * exposures[beta_key]
                attribution[f"{factor_name}_contribution"] = contribution
        
        # Residual (alpha) contribution
        factor_contributions = sum(
            v for k, v in attribution.items() if k.endswith("_contribution")
        )
        attribution["alpha_contribution"] = attribution["total_return"] - factor_contributions
        
        return attribution


# ============================================================================
# CORRELATION ANALYSIS
# ============================================================================

class CorrelationAnalyzer:
    """Advanced correlation analysis."""
    
    @staticmethod
    def correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
        """Calculate correlation matrix."""
        return returns.corr()
    
    @staticmethod
    def rolling_correlation(
        returns1: pd.Series,
        returns2: pd.Series,
        window: int = 63,
    ) -> pd.Series:
        """Calculate rolling correlation between two series."""
        return returns1.rolling(window).corr(returns2)
    
    @staticmethod
    def clustered_correlation(
        returns: pd.DataFrame,
        n_clusters: int = 3,
    ) -> Tuple[pd.DataFrame, List[List[str]]]:
        """Cluster assets by correlation."""
        
        corr = returns.corr()
        
        # Convert correlation to distance
        distance = 1 - corr.abs()
        
        # Hierarchical clustering
        linkage_matrix = linkage(squareform(distance), method='ward')
        clusters = fcluster(linkage_matrix, n_clusters, criterion='maxclust')
        
        # Group assets by cluster
        cluster_groups = [[] for _ in range(n_clusters)]
        for asset, cluster in zip(corr.columns, clusters):
            cluster_groups[cluster - 1].append(asset)
        
        # Reorder correlation matrix by cluster
        ordered_assets = [asset for group in cluster_groups for asset in group]
        ordered_corr = corr.loc[ordered_assets, ordered_assets]
        
        return ordered_corr, cluster_groups
    
    @staticmethod
    def correlation_breakdown_by_regime(
        returns: pd.DataFrame,
        regimes: pd.Series,
    ) -> Dict[str, pd.DataFrame]:
        """Calculate correlation matrices by regime."""
        
        results = {}
        
        for regime in regimes.unique():
            mask = regimes == regime
            regime_returns = returns.loc[mask]
            
            if len(regime_returns) > 30:
                results[regime] = regime_returns.corr()
        
        return results


# ============================================================================
# MONTE CARLO SIMULATION
# ============================================================================

class MonteCarloSimulator:
    """Monte Carlo portfolio simulations."""
    
    @staticmethod
    def bootstrap_returns(
        returns: pd.Series,
        n_simulations: int = 1000,
        horizon_days: int = 252,
        block_size: int = 21,  # Block bootstrap for autocorrelation
    ) -> np.ndarray:
        """Generate bootstrapped return paths."""
        
        n_blocks = horizon_days // block_size + 1
        simulated_paths = np.zeros((n_simulations, horizon_days))
        
        returns_arr = returns.values
        n_obs = len(returns_arr)
        
        for sim in range(n_simulations):
            path = []
            for _ in range(n_blocks):
                start_idx = np.random.randint(0, n_obs - block_size)
                block = returns_arr[start_idx:start_idx + block_size]
                path.extend(block)
            
            simulated_paths[sim] = path[:horizon_days]
        
        return simulated_paths
    
    @staticmethod
    def simulate_portfolio_value(
        returns_paths: np.ndarray,
        initial_value: float = 100000,
    ) -> Dict[str, Any]:
        """Simulate portfolio values and calculate statistics."""
        
        cumulative_returns = (1 + returns_paths).cumprod(axis=1)
        portfolio_values = initial_value * cumulative_returns
        
        final_values = portfolio_values[:, -1]
        
        return {
            "mean_final_value": final_values.mean(),
            "median_final_value": np.median(final_values),
            "std_final_value": final_values.std(),
            "percentiles": {
                "5th": np.percentile(final_values, 5),
                "25th": np.percentile(final_values, 25),
                "50th": np.percentile(final_values, 50),
                "75th": np.percentile(final_values, 75),
                "95th": np.percentile(final_values, 95),
            },
            "prob_loss": (final_values < initial_value).mean(),
            "prob_double": (final_values > 2 * initial_value).mean(),
            "worst_case": final_values.min(),
            "best_case": final_values.max(),
            "paths": portfolio_values,
        }
    
    @staticmethod
    def scenario_analysis(
        portfolio_returns: pd.Series,
        scenarios: Dict[str, float],
    ) -> Dict[str, Dict[str, float]]:
        """Analyze portfolio under different scenarios."""
        
        current_value = 100000
        results = {}
        
        for scenario_name, shock in scenarios.items():
            # Simple scenario: apply shock to returns
            shocked_return = shock
            new_value = current_value * (1 + shocked_return)
            
            results[scenario_name] = {
                "shock": shock,
                "new_value": new_value,
                "pnl": new_value - current_value,
                "pnl_pct": shocked_return,
            }
        
        return results
    
    # Common scenarios
    SCENARIOS = {
        "rates_up_100bp": -0.05,  # Simplified impact
        "rates_down_100bp": 0.05,
        "market_crash_10pct": -0.10,
        "market_rally_10pct": 0.10,
        "vol_spike_50pct": -0.03,
        "usd_strengthen_5pct": -0.02,
        "oil_up_20pct": 0.01,
        "recession": -0.15,
    }
