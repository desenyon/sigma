"""Strategy discovery - Hypothesis generation and rule conversion."""

import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from .analytics import PerformanceAnalytics


# ============================================================================
# DATA MODELS
# ============================================================================

class TradingRule(BaseModel):
    """A trading rule specification."""
    name: str
    description: str
    entry_condition: str
    exit_condition: Optional[str] = None
    position_sizing: str = "fixed"  # fixed, volatility_scaled, kelly
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    max_holding_period: Optional[int] = None  # days
    required_data: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class HypothesisResult(BaseModel):
    """Result of hypothesis testing."""
    hypothesis: str
    supported: bool
    confidence: float
    evidence: List[str]
    metrics: Dict[str, float]
    sample_size: int
    caveats: List[str] = Field(default_factory=list)


class StrategyIdea(BaseModel):
    """A strategy idea with rationale."""
    name: str
    thesis: str
    rules: List[TradingRule]
    expected_edge: str
    risk_factors: List[str]
    data_requirements: List[str]


# ============================================================================
# HYPOTHESIS GENERATOR
# ============================================================================

class HypothesisGenerator:
    """Generate testable hypotheses from observations or queries."""
    
    # Common hypothesis templates
    HYPOTHESIS_TEMPLATES = {
        "momentum": [
            "Assets with positive {period}-period momentum outperform",
            "Strong recent performance predicts continued strength",
            "Winners keep winning over {period} periods",
        ],
        "mean_reversion": [
            "Extreme {direction} moves tend to reverse",
            "Oversold conditions predict bounces",
            "Overbought conditions predict pullbacks",
        ],
        "seasonality": [
            "{month} shows consistent {direction} bias",
            "Day-of-week effects exist in this asset",
            "Year-end rally effect is statistically significant",
        ],
        "volatility": [
            "Low volatility periods precede high volatility",
            "Volatility clustering is exploitable",
            "Implied volatility overestimates realized volatility",
        ],
        "correlation": [
            "Correlation breaks down during crises",
            "Cross-asset momentum signals are predictive",
            "Sector rotation patterns are persistent",
        ],
        "fundamental": [
            "Value outperforms over long horizons",
            "Quality metrics predict outperformance",
            "Earnings surprises have momentum",
        ],
    }
    
    def generate_hypotheses(
        self,
        context: str,
        category: Optional[str] = None,
    ) -> List[str]:
        """Generate relevant hypotheses based on context."""
        
        hypotheses = []
        
        if category and category in self.HYPOTHESIS_TEMPLATES:
            hypotheses.extend(self.HYPOTHESIS_TEMPLATES[category])
        else:
            # Auto-detect relevant categories from context
            context_lower = context.lower()
            
            if any(w in context_lower for w in ["momentum", "trend", "winning"]):
                hypotheses.extend(self.HYPOTHESIS_TEMPLATES["momentum"])
            
            if any(w in context_lower for w in ["revert", "bounce", "oversold", "overbought"]):
                hypotheses.extend(self.HYPOTHESIS_TEMPLATES["mean_reversion"])
            
            if any(w in context_lower for w in ["january", "month", "day", "seasonal"]):
                hypotheses.extend(self.HYPOTHESIS_TEMPLATES["seasonality"])
            
            if any(w in context_lower for w in ["volatility", "vol", "vix"]):
                hypotheses.extend(self.HYPOTHESIS_TEMPLATES["volatility"])
            
            if any(w in context_lower for w in ["correlation", "hedge", "diversif"]):
                hypotheses.extend(self.HYPOTHESIS_TEMPLATES["correlation"])
            
            if any(w in context_lower for w in ["value", "quality", "earnings", "fundamental"]):
                hypotheses.extend(self.HYPOTHESIS_TEMPLATES["fundamental"])
        
        return hypotheses if hypotheses else list(self.HYPOTHESIS_TEMPLATES["momentum"])
    
    def parse_hypothesis_from_query(self, query: str) -> str:
        """Extract a testable hypothesis from a natural language query."""
        
        # Common patterns
        patterns = [
            (r"(does|do)\s+(.+)\s+(outperform|beat|predict)", r"\2 predicts outperformance"),
            (r"(is|are)\s+(.+)\s+(better|worse)", r"\2 is a significant factor"),
            (r"(can|could)\s+(.+)\s+(work|predict)", r"\2 has predictive power"),
            (r"what if\s+(.+)", r"\1 is exploitable"),
        ]
        
        for pattern, replacement in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return re.sub(pattern, replacement, query, flags=re.IGNORECASE)
        
        # Default: convert to testable statement
        return f"The pattern described in '{query}' is statistically significant"


# ============================================================================
# HYPOTHESIS TESTER
# ============================================================================

class HypothesisTester:
    """Test hypotheses with statistical rigor."""
    
    def __init__(self):
        self.performance = PerformanceAnalytics()
    
    def test_momentum_hypothesis(
        self,
        returns: pd.Series,
        lookback: int = 252,
        holding: int = 21,
    ) -> HypothesisResult:
        """Test if momentum is predictive."""
        
        # Calculate rolling momentum
        momentum = returns.rolling(lookback).apply(lambda x: (1 + x).prod() - 1)
        
        # Create forward returns
        forward_returns = returns.rolling(holding).apply(lambda x: (1 + x).prod() - 1).shift(-holding)
        
        # Align and clean
        df = pd.concat([momentum, forward_returns], axis=1).dropna()
        df.columns = ["momentum", "forward_return"]
        
        if len(df) < 100:
            return HypothesisResult(
                hypothesis=f"{lookback}-period momentum predicts {holding}-period forward returns",
                supported=False,
                confidence=0.0,
                evidence=["Insufficient data"],
                metrics={},
                sample_size=len(df),
                caveats=["Need at least 100 observations"],
            )
        
        # Split into quintiles
        df["quintile"] = pd.qcut(df["momentum"], 5, labels=[1, 2, 3, 4, 5])
        
        # Calculate returns by quintile
        quintile_returns = df.groupby("quintile")["forward_return"].mean()
        
        # Long-short spread
        long_short = quintile_returns.iloc[-1] - quintile_returns.iloc[0]
        
        # Calculate t-statistic
        q5_returns = df[df["quintile"] == 5]["forward_return"]
        q1_returns = df[df["quintile"] == 1]["forward_return"]
        
        from scipy import stats
        t_stat, p_value = stats.ttest_ind(q5_returns, q1_returns)
        
        supported = p_value < 0.05 and long_short > 0
        confidence = 1 - p_value
        
        return HypothesisResult(
            hypothesis=f"{lookback}-period momentum predicts {holding}-period forward returns",
            supported=supported,
            confidence=confidence,
            evidence=[
                f"Long-short spread: {long_short:.2%} per period",
                f"t-statistic: {t_stat:.2f}",
                f"p-value: {p_value:.4f}",
                f"Top quintile avg: {quintile_returns.iloc[-1]:.2%}",
                f"Bottom quintile avg: {quintile_returns.iloc[0]:.2%}",
            ],
            metrics={
                "long_short_spread": long_short,
                "t_statistic": t_stat,
                "p_value": p_value,
            },
            sample_size=len(df),
            caveats=[
                "Past performance may not predict future results",
                "Transaction costs not included",
                "May be period-specific",
            ],
        )
    
    def test_mean_reversion_hypothesis(
        self,
        returns: pd.Series,
        threshold: float = 2.0,  # Standard deviations
        holding: int = 5,
    ) -> HypothesisResult:
        """Test if extreme moves tend to reverse."""
        
        # Calculate z-scores of returns
        mean_return = returns.mean()
        std_return = returns.std()
        z_scores = (returns - mean_return) / std_return
        
        # Identify extreme moves
        extreme_down = z_scores < -threshold
        extreme_up = z_scores > threshold
        
        # Forward returns after extremes
        forward_returns = returns.rolling(holding).apply(lambda x: (1 + x).prod() - 1).shift(-holding)
        
        df = pd.concat([z_scores, forward_returns, extreme_down, extreme_up], axis=1).dropna()
        df.columns = ["z_score", "forward_return", "extreme_down", "extreme_up"]
        
        # Calculate results
        after_down = df[df["extreme_down"]]["forward_return"].mean()
        after_up = df[df["extreme_up"]]["forward_return"].mean()
        n_down = df["extreme_down"].sum()
        n_up = df["extreme_up"].sum()
        
        # Reversion detected if:
        # - Extreme down is followed by positive returns
        # - Extreme up is followed by negative returns
        supported = after_down > 0 and after_up < 0
        
        # Confidence based on sample size and magnitude
        if n_down >= 30 and n_up >= 30:
            confidence = 0.8
        elif n_down >= 10 and n_up >= 10:
            confidence = 0.5
        else:
            confidence = 0.2
        
        return HypothesisResult(
            hypothesis=f"Extreme moves ({threshold}σ) tend to reverse over {holding} days",
            supported=supported,
            confidence=confidence,
            evidence=[
                f"Return after extreme down: {after_down:.2%} (n={n_down:.0f})",
                f"Return after extreme up: {after_up:.2%} (n={n_up:.0f})",
            ],
            metrics={
                "return_after_extreme_down": after_down,
                "return_after_extreme_up": after_up,
                "n_extreme_down": float(n_down),
                "n_extreme_up": float(n_up),
            },
            sample_size=len(df),
            caveats=[
                "Threshold choice affects results",
                "May not account for regime changes",
                "Sample size may be small for extreme events",
            ],
        )
    
    def test_seasonality_hypothesis(
        self,
        returns: pd.Series,
        period: str = "month",  # month, dayofweek
    ) -> HypothesisResult:
        """Test if seasonality is statistically significant."""
        
        if period == "month":
            groups = returns.groupby(returns.index.month)
            labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        else:
            groups = returns.groupby(returns.index.dayofweek)
            labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        # Calculate mean and std for each period
        period_stats = groups.agg(["mean", "std", "count"])
        
        # ANOVA test
        from scipy import stats
        group_data = [group.values for name, group in groups]
        f_stat, p_value = stats.f_oneway(*group_data)
        
        supported = p_value < 0.05
        confidence = 1 - p_value
        
        # Find best and worst periods
        means = groups.mean()
        best_idx = means.idxmax()
        worst_idx = means.idxmin()
        
        if period == "month":
            best_label = labels[int(best_idx) - 1]
            worst_label = labels[int(worst_idx) - 1]
        else:
            best_label = labels[int(best_idx)]
            worst_label = labels[int(worst_idx)]
        
        return HypothesisResult(
            hypothesis=f"There are significant {period}ly patterns in returns",
            supported=supported,
            confidence=confidence,
            evidence=[
                f"F-statistic: {f_stat:.2f}",
                f"p-value: {p_value:.4f}",
                f"Best {period}: {best_label} ({means[best_idx]:.4%})",
                f"Worst {period}: {worst_label} ({means[worst_idx]:.4%})",
            ],
            metrics={
                "f_statistic": f_stat,
                "p_value": p_value,
                "best_period_return": means[best_idx],
                "worst_period_return": means[worst_idx],
            },
            sample_size=len(returns),
            caveats=[
                "Seasonality may change over time",
                "Sample period affects results",
                "May be coincidental",
            ],
        )


# ============================================================================
# RULE CONVERTER
# ============================================================================

class RuleConverter:
    """Convert natural language rules to algorithmic specifications."""
    
    # Signal definitions
    SIGNAL_PATTERNS = {
        "ma_cross": {
            "patterns": [r"(\d+)\s*(?:day|d)\s*(?:ma|moving average)\s*cross(?:es|ing)?\s*(?:above|below)?\s*(\d+)\s*(?:day|d)"],
            "template": "MA({fast}) crosses MA({slow})",
        },
        "rsi": {
            "patterns": [r"rsi\s*(?:below|under|<)\s*(\d+)", r"rsi\s*(?:above|over|>)\s*(\d+)"],
            "template": "RSI {condition} {threshold}",
        },
        "price_breakout": {
            "patterns": [r"(?:price|close)\s*(?:breaks?|crosses?)\s*(?:above|below)\s*(\d+)\s*(?:day|d)\s*(?:high|low)"],
            "template": "Price breaks {period}-day {level}",
        },
        "volatility": {
            "patterns": [r"(?:vol|volatility)\s*(?:below|under|<)\s*(\d+)%?", r"low\s*(?:vol|volatility)"],
            "template": "Volatility condition",
        },
    }
    
    def parse_rule(self, text: str) -> Optional[TradingRule]:
        """Parse a natural language rule into a TradingRule."""
        
        text_lower = text.lower()
        
        # Detect signal type
        for signal_type, config in self.SIGNAL_PATTERNS.items():
            for pattern in config["patterns"]:
                match = re.search(pattern, text_lower)
                if match:
                    return self._create_rule(signal_type, match, text)
        
        # Generic rule if no specific pattern matched
        return TradingRule(
            name="custom_rule",
            description=text,
            entry_condition=text,
            required_data=["price"],
            parameters={},
        )
    
    def _create_rule(
        self,
        signal_type: str,
        match: re.Match,
        original_text: str,
    ) -> TradingRule:
        """Create a TradingRule from a matched pattern."""
        
        if signal_type == "ma_cross":
            fast = int(match.group(1))
            slow = int(match.group(2))
            return TradingRule(
                name="ma_crossover",
                description=f"{fast}/{slow} Moving Average Crossover",
                entry_condition=f"SMA({fast}) > SMA({slow})",
                exit_condition=f"SMA({fast}) < SMA({slow})",
                required_data=["close"],
                parameters={"fast_period": fast, "slow_period": slow},
            )
        
        elif signal_type == "rsi":
            threshold = int(match.group(1))
            is_oversold = "below" in original_text.lower() or "<" in original_text
            return TradingRule(
                name="rsi_signal",
                description=f"RSI {'Oversold' if is_oversold else 'Overbought'} Signal",
                entry_condition=f"RSI < {threshold}" if is_oversold else f"RSI > {threshold}",
                exit_condition=f"RSI > {100 - threshold}" if is_oversold else f"RSI < {threshold}",
                required_data=["close"],
                parameters={"threshold": threshold, "period": 14},
            )
        
        elif signal_type == "price_breakout":
            period = int(match.group(1))
            is_high = "high" in original_text.lower()
            return TradingRule(
                name="price_breakout",
                description=f"{period}-Day {'High' if is_high else 'Low'} Breakout",
                entry_condition=f"Close > {period}-day high" if is_high else f"Close < {period}-day low",
                required_data=["close", "high" if is_high else "low"],
                parameters={"period": period, "breakout_type": "high" if is_high else "low"},
            )
        
        # Default
        return TradingRule(
            name=signal_type,
            description=original_text,
            entry_condition=original_text,
            required_data=["close"],
            parameters={},
        )
    
    def rule_to_python(self, rule: TradingRule) -> str:
        """Convert a TradingRule to Python code."""
        
        if rule.name == "ma_crossover":
            fast = rule.parameters.get("fast_period", 10)
            slow = rule.parameters.get("slow_period", 50)
            return f'''
def generate_signals(prices: pd.Series) -> pd.Series:
    """MA Crossover: {rule.description}"""
    fast_ma = prices.rolling({fast}).mean()
    slow_ma = prices.rolling({slow}).mean()
    
    signal = pd.Series(0, index=prices.index)
    signal[fast_ma > slow_ma] = 1   # Long
    signal[fast_ma < slow_ma] = -1  # Short or flat
    
    return signal
'''
        
        elif rule.name == "rsi_signal":
            threshold = rule.parameters.get("threshold", 30)
            period = rule.parameters.get("period", 14)
            return f'''
def generate_signals(prices: pd.Series) -> pd.Series:
    """RSI Signal: {rule.description}"""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling({period}).mean()
    loss = (-delta.where(delta < 0, 0)).rolling({period}).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    signal = pd.Series(0, index=prices.index)
    signal[rsi < {threshold}] = 1   # Buy on oversold
    signal[rsi > {100 - threshold}] = -1  # Sell on overbought
    
    return signal
'''
        
        elif rule.name == "price_breakout":
            period = rule.parameters.get("period", 20)
            breakout_type = rule.parameters.get("breakout_type", "high")
            return f'''
def generate_signals(prices: pd.DataFrame) -> pd.Series:
    """Breakout Signal: {rule.description}"""
    close = prices['close']
    
    {'high_n = prices["high"].rolling('+str(period)+').max()' if breakout_type == 'high' else 'low_n = prices["low"].rolling('+str(period)+').min()'}
    
    signal = pd.Series(0, index=close.index)
    {'signal[close > high_n.shift(1)] = 1' if breakout_type == 'high' else 'signal[close < low_n.shift(1)] = -1'}
    
    return signal
'''
        
        # Generic template
        return f'''
def generate_signals(prices: pd.Series) -> pd.Series:
    """Custom Signal: {rule.description}
    
    Entry: {rule.entry_condition}
    Exit: {rule.exit_condition or "Reverse signal"}
    """
    # TODO: Implement custom logic
    signal = pd.Series(0, index=prices.index)
    return signal
'''


# ============================================================================
# FAILURE MODE DETECTOR
# ============================================================================

class FailureModeDetector:
    """Detect potential failure modes in strategies."""
    
    FAILURE_MODES = {
        "overfitting": {
            "description": "Strategy may be overfitted to historical data",
            "checks": ["parameter_sensitivity", "out_of_sample"],
        },
        "regime_dependency": {
            "description": "Strategy may only work in specific market regimes",
            "checks": ["regime_breakdown"],
        },
        "capacity_limit": {
            "description": "Strategy may have limited capacity",
            "checks": ["market_impact", "liquidity"],
        },
        "crowding": {
            "description": "Strategy may be crowded by similar traders",
            "checks": ["signal_correlation"],
        },
        "data_mining": {
            "description": "Results may be due to data mining bias",
            "checks": ["multiple_testing"],
        },
    }
    
    def detect_failure_modes(
        self,
        strategy_results: Dict[str, Any],
        returns: pd.Series,
    ) -> List[Dict[str, Any]]:
        """Detect potential failure modes in a strategy."""
        
        failures = []
        
        # Check for overfitting signals
        if self._check_overfitting(strategy_results):
            failures.append({
                "mode": "overfitting",
                "severity": "high",
                "description": self.FAILURE_MODES["overfitting"]["description"],
                "evidence": self._get_overfitting_evidence(strategy_results),
                "mitigation": "Use walk-forward optimization, reduce parameters",
            })
        
        # Check for regime dependency
        if self._check_regime_dependency(strategy_results, returns):
            failures.append({
                "mode": "regime_dependency",
                "severity": "medium",
                "description": self.FAILURE_MODES["regime_dependency"]["description"],
                "evidence": ["Performance varies significantly across market regimes"],
                "mitigation": "Add regime filters or diversify strategies",
            })
        
        # Check for data mining
        if self._check_data_mining(strategy_results):
            failures.append({
                "mode": "data_mining",
                "severity": "medium",
                "description": self.FAILURE_MODES["data_mining"]["description"],
                "evidence": ["Multiple parameters tested without correction"],
                "mitigation": "Apply multiple testing correction, use holdout data",
            })
        
        return failures
    
    def _check_overfitting(self, results: Dict[str, Any]) -> bool:
        """Check for signs of overfitting."""
        
        # High in-sample performance but not robust
        sharpe = results.get("sharpe_ratio", 0)
        n_params = results.get("num_parameters", 0)
        n_trades = results.get("num_trades", 100)
        
        # Too good to be true Sharpe
        if sharpe > 3:
            return True
        
        # Too many parameters relative to trades
        if n_params > 0 and n_trades / n_params < 20:
            return True
        
        return False
    
    def _check_regime_dependency(
        self,
        results: Dict[str, Any],
        returns: pd.Series,
    ) -> bool:
        """Check if strategy is regime-dependent."""
        
        # Calculate volatility regimes
        vol = returns.rolling(63).std() * np.sqrt(252)
        high_vol_threshold = vol.quantile(0.75)
        
        # Check if performance differs significantly by regime
        strategy_returns = results.get("strategy_returns", returns)
        
        if isinstance(strategy_returns, pd.Series):
            high_vol_perf = strategy_returns[vol > high_vol_threshold].mean()
            low_vol_perf = strategy_returns[vol <= high_vol_threshold].mean()
            
            # Significant difference suggests regime dependency
            if abs(high_vol_perf - low_vol_perf) > 0.1 * abs(strategy_returns.mean()):
                return True
        
        return False
    
    def _check_data_mining(self, results: Dict[str, Any]) -> bool:
        """Check for data mining bias."""
        
        # Simple heuristics
        n_params = results.get("num_parameters", 0)
        
        # Many parameters suggest potential data mining
        if n_params > 5:
            return True
        
        return False
    
    def _get_overfitting_evidence(self, results: Dict[str, Any]) -> List[str]:
        """Get evidence of overfitting."""
        
        evidence = []
        
        sharpe = results.get("sharpe_ratio", 0)
        if sharpe > 3:
            evidence.append(f"Unusually high Sharpe ratio: {sharpe:.2f}")
        
        n_params = results.get("num_parameters", 0)
        n_trades = results.get("num_trades", 100)
        if n_params > 0 and n_trades / n_params < 20:
            evidence.append(f"Low trade/parameter ratio: {n_trades/n_params:.1f}")
        
        return evidence


# ============================================================================
# STRATEGY GENERATOR
# ============================================================================

class StrategyGenerator:
    """Generate strategy ideas from hypotheses and rules."""
    
    STRATEGY_TEMPLATES = {
        "momentum": StrategyIdea(
            name="Trend Following",
            thesis="Trends persist due to behavioral biases and institutional flows",
            rules=[
                TradingRule(
                    name="price_above_ma",
                    description="Price above 200-day MA",
                    entry_condition="Close > SMA(200)",
                    exit_condition="Close < SMA(200)",
                    required_data=["close"],
                    parameters={"period": 200},
                ),
            ],
            expected_edge="2-4% annualized alpha in trending markets",
            risk_factors=["Choppy markets", "Regime changes", "Crowding"],
            data_requirements=["Daily prices", "Volume"],
        ),
        "mean_reversion": StrategyIdea(
            name="Mean Reversion",
            thesis="Prices revert to fair value after overreaction",
            rules=[
                TradingRule(
                    name="oversold_bounce",
                    description="Buy when RSI oversold",
                    entry_condition="RSI(14) < 30",
                    exit_condition="RSI(14) > 70",
                    required_data=["close"],
                    parameters={"rsi_period": 14, "oversold": 30, "overbought": 70},
                ),
            ],
            expected_edge="1-3% annualized alpha",
            risk_factors=["Trending markets", "Extended drawdowns", "Value traps"],
            data_requirements=["Daily prices"],
        ),
        "quality": StrategyIdea(
            name="Quality Factor",
            thesis="High-quality companies outperform over long horizons",
            rules=[
                TradingRule(
                    name="quality_screen",
                    description="Screen for quality metrics",
                    entry_condition="ROE > 15% AND Debt/Equity < 0.5 AND Margin Trend > 0",
                    exit_condition="Quality score deteriorates",
                    required_data=["fundamentals"],
                    parameters={"roe_threshold": 0.15, "de_threshold": 0.5},
                ),
            ],
            expected_edge="2-5% annualized alpha over market cycles",
            risk_factors=["Valuation multiples", "Factor crowding", "Sector concentration"],
            data_requirements=["Quarterly fundamentals", "Daily prices"],
        ),
    }
    
    def suggest_strategies(
        self,
        hypothesis_results: List[HypothesisResult],
        market_context: Optional[Dict[str, Any]] = None,
    ) -> List[StrategyIdea]:
        """Suggest strategies based on hypothesis testing results."""
        
        suggestions = []
        
        for result in hypothesis_results:
            if result.supported and result.confidence > 0.8:
                # Map hypothesis to strategy template
                hypothesis_lower = result.hypothesis.lower()
                
                if "momentum" in hypothesis_lower or "trend" in hypothesis_lower:
                    suggestions.append(self.STRATEGY_TEMPLATES["momentum"])
                
                elif "revert" in hypothesis_lower or "extreme" in hypothesis_lower:
                    suggestions.append(self.STRATEGY_TEMPLATES["mean_reversion"])
                
                elif "quality" in hypothesis_lower or "fundamental" in hypothesis_lower:
                    suggestions.append(self.STRATEGY_TEMPLATES["quality"])
        
        return suggestions
