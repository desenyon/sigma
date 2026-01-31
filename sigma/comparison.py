"""Comparison engine - Compare anything finance."""

import asyncio
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from .core.models import (
    AssetClass,
    PerformanceMetrics,
    ComparisonResult,
    detect_asset_class,
)
from .analytics import (
    PerformanceAnalytics,
    FactorAnalyzer,
    CorrelationAnalyzer,
    SeasonalityAnalyzer,
)


class ComparisonEngine:
    """
    Compare anything finance - stocks, ETFs, portfolios with full metrics.
    Translates vague prompts into measurable criteria.
    """
    
    def __init__(self):
        self.performance = PerformanceAnalytics()
        self.factor = FactorAnalyzer()
        self.correlation = CorrelationAnalyzer()
        self.seasonality = SeasonalityAnalyzer()
    
    async def compare(
        self,
        assets: List[str],
        returns_data: Dict[str, pd.Series],
        benchmark: str = "SPY",
        benchmark_returns: Optional[pd.Series] = None,
        fundamentals: Optional[Dict[str, Dict]] = None,
        etf_data: Optional[Dict[str, Dict]] = None,
        criteria: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Comprehensive multi-asset comparison.
        
        Args:
            assets: List of asset symbols to compare
            returns_data: Dictionary of symbol -> returns series
            benchmark: Benchmark symbol
            benchmark_returns: Benchmark returns series
            fundamentals: Optional fundamental data for equities
            etf_data: Optional ETF-specific data (holdings, fees, etc.)
            criteria: Optional weighted criteria for scoring
        
        Returns:
            Comprehensive comparison result
        """
        
        results = {
            "assets": assets,
            "benchmark": benchmark,
            "comparison_date": date.today().isoformat(),
        }
        
        # 1. PERFORMANCE COMPARISON
        performance_comparison = await self._compare_performance(
            assets, returns_data, benchmark_returns
        )
        results["performance"] = performance_comparison
        
        # 2. RISK COMPARISON
        risk_comparison = await self._compare_risk(
            assets, returns_data, benchmark_returns
        )
        results["risk"] = risk_comparison
        
        # 3. BEHAVIOR COMPARISON
        behavior_comparison = await self._compare_behavior(
            assets, returns_data
        )
        results["behavior"] = behavior_comparison
        
        # 4. CORRELATION ANALYSIS
        correlation_analysis = await self._analyze_correlations(
            assets, returns_data
        )
        results["correlations"] = correlation_analysis
        
        # 5. FUNDAMENTAL COMPARISON (if equities)
        if fundamentals:
            fundamental_comparison = self._compare_fundamentals(assets, fundamentals)
            results["fundamentals"] = fundamental_comparison
        
        # 6. ETF-SPECIFIC COMPARISON (if ETFs)
        if etf_data:
            etf_comparison = self._compare_etfs(assets, etf_data)
            results["etf_analysis"] = etf_comparison
        
        # 7. SCORING AND RANKING
        scoring = self._score_and_rank(
            assets,
            performance_comparison,
            risk_comparison,
            behavior_comparison,
            criteria
        )
        results["scoring"] = scoring
        
        # 8. TRADEOFF ANALYSIS
        tradeoffs = self._analyze_tradeoffs(
            assets,
            performance_comparison,
            risk_comparison
        )
        results["tradeoffs"] = tradeoffs
        
        # 9. RECOMMENDATION
        recommendation = self._generate_recommendation(
            assets, scoring, criteria
        )
        results["recommendation"] = recommendation
        
        return results
    
    async def _compare_performance(
        self,
        assets: List[str],
        returns_data: Dict[str, pd.Series],
        benchmark_returns: Optional[pd.Series],
    ) -> Dict[str, Dict]:
        """Compare performance metrics across assets."""
        
        comparison = {}
        
        for asset in assets:
            if asset not in returns_data:
                continue
            
            returns = returns_data[asset]
            metrics = self.performance.calculate_metrics(
                returns,
                benchmark_returns,
                risk_free_rate=0.05  # ~5% risk-free rate
            )
            
            comparison[asset] = {
                "total_return": metrics.get("total_return", 0),
                "cagr": metrics.get("cagr", 0),
                "volatility": metrics.get("volatility", 0),
                "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                "sortino_ratio": metrics.get("sortino_ratio", 0),
                "max_drawdown": metrics.get("max_drawdown", 0),
                "calmar_ratio": metrics.get("calmar_ratio", 0),
                "alpha": metrics.get("alpha", 0),
                "beta": metrics.get("beta", 1),
                "r_squared": metrics.get("r_squared", 0),
            }
        
        return comparison
    
    async def _compare_risk(
        self,
        assets: List[str],
        returns_data: Dict[str, pd.Series],
        benchmark_returns: Optional[pd.Series],
    ) -> Dict[str, Dict]:
        """Compare risk metrics across assets."""
        
        comparison = {}
        
        for asset in assets:
            if asset not in returns_data:
                continue
            
            returns = returns_data[asset]
            metrics = self.performance.calculate_metrics(returns, benchmark_returns)
            
            comparison[asset] = {
                "volatility": metrics.get("volatility", 0),
                "downside_deviation": metrics.get("downside_deviation", 0),
                "max_drawdown": metrics.get("max_drawdown", 0),
                "max_dd_duration": metrics.get("max_dd_duration", 0),
                "var_95": metrics.get("var_95", 0),
                "cvar_95": metrics.get("cvar_95", 0),
                "beta": metrics.get("beta", 1),
            }
            
            # Tail risk metrics
            returns_arr = returns.dropna()
            if len(returns_arr) > 100:
                # Skewness and kurtosis
                comparison[asset]["skewness"] = returns_arr.skew()
                comparison[asset]["kurtosis"] = returns_arr.kurtosis()
                
                # Tail ratio
                upper_tail = returns_arr.quantile(0.95)
                lower_tail = abs(returns_arr.quantile(0.05))
                comparison[asset]["tail_ratio"] = upper_tail / lower_tail if lower_tail != 0 else 1
        
        return comparison
    
    async def _compare_behavior(
        self,
        assets: List[str],
        returns_data: Dict[str, pd.Series],
    ) -> Dict[str, Dict]:
        """Compare behavioral characteristics."""
        
        comparison = {}
        
        for asset in assets:
            if asset not in returns_data:
                continue
            
            returns = returns_data[asset]
            
            # Momentum score (recent performance relative to history)
            if len(returns) > 252:
                recent_return = (1 + returns.iloc[-63:]).prod() - 1  # 3 months
                historical_vol = returns.iloc[:-63].std()
                momentum_score = recent_return / (historical_vol * np.sqrt(63)) if historical_vol > 0 else 0
            else:
                momentum_score = 0
            
            # Mean reversion score (autocorrelation)
            if len(returns) > 21:
                autocorr = returns.autocorr(lag=1)
                mean_reversion_score = -autocorr  # Negative autocorr = mean reverting
            else:
                mean_reversion_score = 0
            
            # Trend persistence
            if len(returns) > 252:
                monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
                if len(monthly_returns) > 2:
                    trend_persistence = monthly_returns.autocorr(lag=1)
                else:
                    trend_persistence = 0
            else:
                trend_persistence = 0
            
            # Seasonality strength
            seasonality = self.seasonality.monthly_seasonality(returns)
            if seasonality:
                returns_by_month = [s["mean_return"] for s in seasonality.values()]
                seasonality_strength = np.std(returns_by_month) if returns_by_month else 0
            else:
                seasonality_strength = 0
            
            comparison[asset] = {
                "momentum_score": momentum_score,
                "mean_reversion_score": mean_reversion_score,
                "trend_persistence": trend_persistence,
                "seasonality_strength": seasonality_strength,
                "win_rate": (returns > 0).mean(),
            }
        
        return comparison
    
    async def _analyze_correlations(
        self,
        assets: List[str],
        returns_data: Dict[str, pd.Series],
    ) -> Dict[str, Any]:
        """Analyze correlations between assets."""
        
        # Build returns DataFrame
        df = pd.DataFrame({a: returns_data[a] for a in assets if a in returns_data})
        df = df.dropna()
        
        if len(df) < 30:
            return {"error": "Insufficient data for correlation analysis"}
        
        # Correlation matrix
        corr_matrix = self.correlation.correlation_matrix(df)
        
        # Average pairwise correlation
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        avg_correlation = corr_matrix.where(mask).stack().mean()
        
        # Clustered correlation
        if len(assets) >= 3:
            n_clusters = min(3, len(assets))
            clustered_corr, clusters = self.correlation.clustered_correlation(df, n_clusters)
        else:
            clustered_corr = corr_matrix
            clusters = [[a] for a in assets]
        
        return {
            "correlation_matrix": corr_matrix.to_dict(),
            "average_correlation": avg_correlation,
            "clusters": clusters,
        }
    
    def _compare_fundamentals(
        self,
        assets: List[str],
        fundamentals: Dict[str, Dict],
    ) -> Dict[str, Dict]:
        """Compare fundamental metrics for equities."""
        
        comparison = {}
        
        for asset in assets:
            if asset not in fundamentals:
                continue
            
            data = fundamentals[asset]
            
            comparison[asset] = {
                # Valuation
                "pe_ratio": data.get("trailingPE", data.get("forwardPE")),
                "pb_ratio": data.get("priceToBook"),
                "ps_ratio": data.get("priceToSalesTrailing12Months"),
                "ev_ebitda": data.get("enterpriseToEbitda"),
                
                # Growth
                "revenue_growth": data.get("revenueGrowth"),
                "earnings_growth": data.get("earningsGrowth"),
                
                # Profitability
                "profit_margin": data.get("profitMargins"),
                "operating_margin": data.get("operatingMargins"),
                "roe": data.get("returnOnEquity"),
                "roa": data.get("returnOnAssets"),
                
                # Financial health
                "debt_to_equity": data.get("debtToEquity"),
                "current_ratio": data.get("currentRatio"),
                "quick_ratio": data.get("quickRatio"),
                
                # Dividends
                "dividend_yield": data.get("dividendYield"),
                "payout_ratio": data.get("payoutRatio"),
                
                # Size
                "market_cap": data.get("marketCap"),
            }
        
        return comparison
    
    def _compare_etfs(
        self,
        assets: List[str],
        etf_data: Dict[str, Dict],
    ) -> Dict[str, Any]:
        """Compare ETF-specific metrics."""
        
        comparison = {}
        
        for asset in assets:
            if asset not in etf_data:
                continue
            
            data = etf_data[asset]
            
            comparison[asset] = {
                "expense_ratio": data.get("expense_ratio"),
                "aum": data.get("aum"),
                "holdings_count": data.get("holdings_count"),
                "top_10_weight": data.get("top_10_weight"),
                "tracking_error": data.get("tracking_error"),
                "premium_discount": data.get("premium_discount"),
            }
        
        # Holdings overlap analysis
        if len(assets) >= 2:
            overlaps = {}
            for i, asset1 in enumerate(assets):
                for asset2 in assets[i+1:]:
                    if asset1 in etf_data and asset2 in etf_data:
                        holdings1 = set(etf_data.get(asset1, {}).get("holdings", []))
                        holdings2 = set(etf_data.get(asset2, {}).get("holdings", []))
                        if holdings1 and holdings2:
                            overlap = len(holdings1 & holdings2) / min(len(holdings1), len(holdings2))
                            overlaps[f"{asset1}_vs_{asset2}"] = overlap
            
            comparison["holdings_overlap"] = overlaps
        
        return comparison
    
    def _score_and_rank(
        self,
        assets: List[str],
        performance: Dict[str, Dict],
        risk: Dict[str, Dict],
        behavior: Dict[str, Dict],
        criteria: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Score and rank assets based on criteria."""
        
        # Default criteria weights
        default_criteria = {
            "sharpe_ratio": 0.25,
            "cagr": 0.20,
            "max_drawdown": -0.20,  # Negative because lower is better
            "volatility": -0.15,   # Negative because lower is better
            "sortino_ratio": 0.10,
            "momentum_score": 0.10,
        }
        
        weights = criteria or default_criteria
        
        # Calculate scores
        scores = {}
        for asset in assets:
            if asset not in performance:
                continue
            
            score = 0
            score_details = {}
            
            for metric, weight in weights.items():
                value = 0
                
                if metric in performance.get(asset, {}):
                    value = performance[asset][metric]
                elif metric in risk.get(asset, {}):
                    value = risk[asset][metric]
                elif metric in behavior.get(asset, {}):
                    value = behavior[asset][metric]
                
                # Handle None values
                if value is None:
                    value = 0
                
                contribution = value * weight
                score += contribution
                score_details[metric] = {
                    "value": value,
                    "weight": weight,
                    "contribution": contribution,
                }
            
            scores[asset] = {
                "total_score": score,
                "details": score_details,
            }
        
        # Rank assets
        ranking = sorted(
            [(asset, data["total_score"]) for asset, data in scores.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            "scores": scores,
            "ranking": [r[0] for r in ranking],
            "criteria_used": weights,
        }
    
    def _analyze_tradeoffs(
        self,
        assets: List[str],
        performance: Dict[str, Dict],
        risk: Dict[str, Dict],
    ) -> List[str]:
        """Analyze tradeoffs between assets."""
        
        tradeoffs = []
        
        if len(assets) < 2:
            return tradeoffs
        
        # Find best and worst in each category
        metrics_to_compare = [
            ("sharpe_ratio", "risk-adjusted returns", True),
            ("cagr", "returns", True),
            ("max_drawdown", "drawdown protection", False),
            ("volatility", "stability", False),
        ]
        
        for metric, description, higher_better in metrics_to_compare:
            values = {}
            for asset in assets:
                if metric in performance.get(asset, {}):
                    values[asset] = performance[asset][metric]
                elif metric in risk.get(asset, {}):
                    values[asset] = risk[asset][metric]
            
            if len(values) >= 2:
                sorted_assets = sorted(values.items(), key=lambda x: x[1], reverse=higher_better)
                best = sorted_assets[0]
                worst = sorted_assets[-1]
                
                if best[0] != worst[0]:
                    tradeoffs.append(
                        f"{best[0]} offers better {description} ({metric}: {best[1]:.2f}) "
                        f"vs {worst[0]} ({worst[1]:.2f})"
                    )
        
        return tradeoffs
    
    def _generate_recommendation(
        self,
        assets: List[str],
        scoring: Dict[str, Any],
        criteria: Optional[Dict[str, float]],
    ) -> Dict[str, Any]:
        """Generate a recommendation based on comparison."""
        
        ranking = scoring.get("ranking", [])
        scores = scoring.get("scores", {})
        
        if not ranking:
            return {"recommendation": "Insufficient data for recommendation"}
        
        top_pick = ranking[0]
        top_score = scores.get(top_pick, {}).get("total_score", 0)
        
        # Check if there's a clear winner
        if len(ranking) >= 2:
            second_score = scores.get(ranking[1], {}).get("total_score", 0)
            margin = (top_score - second_score) / abs(second_score) if second_score != 0 else float('inf')
            
            if margin > 0.2:
                confidence = "high"
                explanation = f"{top_pick} is clearly the best option with a {margin:.0%} advantage."
            elif margin > 0.05:
                confidence = "moderate"
                explanation = f"{top_pick} edges out {ranking[1]}, but the difference is modest."
            else:
                confidence = "low"
                explanation = f"{top_pick} and {ranking[1]} are very close. Consider other factors."
        else:
            confidence = "n/a"
            explanation = "Only one asset to evaluate."
        
        return {
            "top_pick": top_pick,
            "confidence": confidence,
            "explanation": explanation,
            "full_ranking": ranking,
            "key_strengths": self._identify_strengths(top_pick, scores.get(top_pick, {}).get("details", {})),
            "key_weaknesses": self._identify_weaknesses(top_pick, scores.get(top_pick, {}).get("details", {})),
        }
    
    def _identify_strengths(self, asset: str, details: Dict) -> List[str]:
        """Identify key strengths of an asset."""
        strengths = []
        for metric, info in details.items():
            if info.get("contribution", 0) > 0:
                strengths.append(f"Strong {metric}: {info.get('value', 0):.2f}")
        return strengths[:3]  # Top 3
    
    def _identify_weaknesses(self, asset: str, details: Dict) -> List[str]:
        """Identify key weaknesses of an asset."""
        weaknesses = []
        for metric, info in details.items():
            if info.get("contribution", 0) < 0:
                weaknesses.append(f"Weak {metric}: {info.get('value', 0):.2f}")
        return weaknesses[:3]  # Top 3


# ============================================================================
# MACRO SENSITIVITY ANALYSIS
# ============================================================================

class MacroSensitivityAnalyzer:
    """Analyze sensitivity to macro factors."""
    
    MACRO_PROXIES = {
        "rates": "TLT",      # Long-term treasuries (inverse proxy for rates)
        "inflation": "TIP",   # TIPS
        "oil": "USO",        # Oil
        "usd": "UUP",        # US Dollar
        "gold": "GLD",       # Gold
        "credit": "HYG",     # High yield (credit risk)
        "vix": "VIXY",       # Volatility
    }
    
    @staticmethod
    async def analyze_macro_sensitivity(
        asset_returns: pd.Series,
        macro_returns: Dict[str, pd.Series],
    ) -> Dict[str, Dict[str, float]]:
        """Analyze asset sensitivity to macro factors."""
        
        results = {}
        
        for factor_name, factor_returns in macro_returns.items():
            # Align data
            aligned = pd.concat([asset_returns, factor_returns], axis=1).dropna()
            
            if len(aligned) < 30:
                continue
            
            asset_ret = aligned.iloc[:, 0]
            factor_ret = aligned.iloc[:, 1]
            
            # Calculate beta (sensitivity)
            cov = np.cov(asset_ret, factor_ret)
            beta = cov[0, 1] / cov[1, 1] if cov[1, 1] != 0 else 0
            
            # Correlation
            corr = asset_ret.corr(factor_ret)
            
            # R-squared
            r_squared = corr ** 2
            
            results[factor_name] = {
                "beta": beta,
                "correlation": corr,
                "r_squared": r_squared,
            }
        
        return results
