"""Intent parsing and research plan generation for Sigma."""

import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import date

from .models import (
    AssetClass,
    TimeHorizon,
    RiskProfile,
    DeliverableType,
    ResearchPlan,
    Constraint,
    detect_asset_class,
)


# ============================================================================
# INTENT PATTERNS
# ============================================================================

# Deliverable type detection
DELIVERABLE_PATTERNS = {
    DeliverableType.COMPARISON: [
        r"\bcompare\b", r"\bvs\b", r"\bversus\b", r"\bagainst\b",
        r"\bwhich is better\b", r"\bwhich one\b", r"\bdifference between\b",
    ],
    DeliverableType.BACKTEST: [
        r"\bbacktest\b", r"\btest strategy\b", r"\bhistorical performance\b",
        r"\bwould have performed\b", r"\bsimulate\b", r"\bstrategy test\b",
    ],
    DeliverableType.PORTFOLIO: [
        r"\bportfolio\b", r"\ballocation\b", r"\bdiversif\b", r"\brebalance\b",
        r"\bweight\b", r"\brisk parity\b", r"\boptimize\b",
    ],
    DeliverableType.STRATEGY: [
        r"\bstrategy\b", r"\btrading system\b", r"\balgorithm\b", r"\brules?\b",
        r"\bwhen to buy\b", r"\bwhen to sell\b", r"\bsignal\b",
    ],
    DeliverableType.CHART: [
        r"\bchart\b", r"\bgraph\b", r"\bplot\b", r"\bvisualize\b",
        r"\bshow me\b", r"\bdraw\b",
    ],
    DeliverableType.REPORT: [
        r"\breport\b", r"\banalysis report\b", r"\bresearch memo\b",
        r"\bfull analysis\b", r"\bdeep dive\b",
    ],
    DeliverableType.ALERT: [
        r"\balert\b", r"\bnotify\b", r"\bwatch\b", r"\bmonitor\b",
        r"\btell me when\b", r"\bwarn me\b",
    ],
    DeliverableType.ANALYSIS: [
        r"\banalyze\b", r"\banalysis\b", r"\blook at\b", r"\bexamine\b",
        r"\bwhat do you think\b", r"\bopinion on\b", r"\bsentiment\b",
    ],
}

# Time horizon detection
HORIZON_PATTERNS = {
    TimeHorizon.INTRADAY: [r"\bintraday\b", r"\bday trad\b", r"\bscalp\b", r"\bminute\b", r"\bhour\b"],
    TimeHorizon.DAILY: [r"\bdaily\b", r"\bswing\b", r"\bshort.?term\b", r"\bdays?\b"],
    TimeHorizon.WEEKLY: [r"\bweekly\b", r"\bweeks?\b"],
    TimeHorizon.MONTHLY: [r"\bmonthly\b", r"\bmonths?\b", r"\bmedium.?term\b"],
    TimeHorizon.QUARTERLY: [r"\bquarterly\b", r"\bquarters?\b"],
    TimeHorizon.YEARLY: [r"\byearly\b", r"\bannual\b", r"\byears?\b"],
    TimeHorizon.MULTI_YEAR: [r"\blong.?term\b", r"\bmulti.?year\b", r"\bdecade\b", r"\bretirement\b"],
}

# Risk profile detection
RISK_PATTERNS = {
    RiskProfile.CONSERVATIVE: [
        r"\bconservative\b", r"\bsafe\b", r"\blow risk\b", r"\bstable\b",
        r"\bdefensive\b", r"\bcapital preservation\b",
    ],
    RiskProfile.MODERATE: [
        r"\bmoderate\b", r"\bbalanced\b", r"\bmid risk\b",
    ],
    RiskProfile.AGGRESSIVE: [
        r"\baggressive\b", r"\bhigh risk\b", r"\bgrowth\b", r"\bhigh return\b",
    ],
    RiskProfile.VERY_AGGRESSIVE: [
        r"\bspeculative\b", r"\bvery aggressive\b", r"\bmaximum\b", r"\bleverage\b",
    ],
}

# Constraint detection
CONSTRAINT_PATTERNS = [
    (r"max(?:imum)?\s+(?:position\s+)?weight\s*(?:of\s*)?(\d+)%?", "max_weight"),
    (r"max(?:imum)?\s+drawdown\s*(?:of\s*)?(\d+)%?", "max_drawdown"),
    (r"(?:no\s+)?leverage", "leverage"),
    (r"max(?:imum)?\s+leverage\s*(?:of\s*)?([\d.]+)x?", "max_leverage"),
    (r"turnover\s*(?:cap|limit)?\s*(?:of\s*)?(\d+)%?", "max_turnover"),
    (r"sector\s+(?:cap|limit)\s*(?:of\s*)?(\d+)%?", "sector_cap"),
    (r"(?:no\s+)?(?:short|shorting)", "no_shorts"),
    (r"tax.?(?:efficient|aware|sensitive)", "tax_aware"),
    (r"(?:ESG|sustainable|socially responsible)", "esg"),
]

# Account type detection
ACCOUNT_PATTERNS = {
    "taxable": [r"\btaxable\b", r"\bbrokerage\b", r"\bindividual\b"],
    "ira": [r"\bira\b", r"\broth\b", r"\btraditional ira\b"],
    "401k": [r"\b401k\b", r"\b401\(k\)\b", r"\bretirement\b"],
    "margin": [r"\bmargin\b"],
}


# ============================================================================
# TICKER EXTRACTION
# ============================================================================

# Common tickers to help with extraction
COMMON_TICKERS = {
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "BRK.A", "BRK.B",
    "JPM", "V", "JNJ", "WMT", "MA", "PG", "UNH", "HD", "DIS", "BAC",
    "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO", "VEA", "VWO", "BND", "AGG",
    "XLK", "XLF", "XLE", "XLV", "XLI", "XLP", "XLY", "XLB", "XLU", "XLRE",
    "GLD", "SLV", "USO", "UNG", "TLT", "IEF", "SHY", "LQD", "HYG", "JNK",
    "BTC", "ETH", "SOL", "DOGE", "ADA", "XRP", "DOT", "AVAX", "LINK", "MATIC",
}

# Ticker pattern
TICKER_PATTERN = re.compile(r'\b([A-Z]{1,5}(?:\.[A-Z])?)\b')


def extract_tickers(text: str) -> List[str]:
    """Extract stock tickers from text."""
    text_upper = text.upper()
    
    # Find all potential tickers
    matches = TICKER_PATTERN.findall(text_upper)
    
    # Filter out common words
    excluded = {
        "I", "A", "THE", "AND", "OR", "FOR", "TO", "IN", "ON", "AT", "IS", "IT",
        "AS", "BE", "BY", "AN", "IF", "VS", "AM", "PM", "US", "UK", "EU", "OF",
        "MY", "ME", "DO", "SO", "NO", "UP", "HE", "WE", "GO", "CEO", "CFO", "CTO",
        "ETF", "IPO", "EPS", "PE", "PB", "ROE", "ROA", "CAGR", "YOY", "QOQ", "MOM",
        "MAX", "MIN", "AVG", "SMA", "EMA", "RSI", "ATR", "ADX", "MACD", "BB",
        "LEAN", "API", "CSV", "PDF", "PNG", "SVG",
    }
    
    tickers = []
    for match in matches:
        if match not in excluded:
            # Prefer known tickers
            if match in COMMON_TICKERS:
                tickers.append(match)
            elif len(match) >= 2:  # At least 2 chars for unknown tickers
                tickers.append(match)
    
    return list(dict.fromkeys(tickers))  # Remove duplicates, preserve order


# ============================================================================
# INTENT PARSER
# ============================================================================

class IntentParser:
    """Parse user intent into structured research plan."""
    
    def __init__(self):
        self.default_benchmark = "SPY"
        self.default_horizon = TimeHorizon.DAILY
        self.default_risk = RiskProfile.MODERATE
    
    def parse(self, query: str) -> ResearchPlan:
        """Parse user query into a research plan."""
        query_lower = query.lower()
        
        # Extract tickers
        tickers = extract_tickers(query)
        
        # Detect asset classes
        asset_classes = [detect_asset_class(t) for t in tickers]
        asset_classes = list(set(asset_classes))  # Unique classes
        
        # Detect deliverable type
        deliverable = self._detect_deliverable(query_lower)
        
        # Detect time horizon
        horizon = self._detect_horizon(query_lower)
        
        # Detect risk profile
        risk_profile = self._detect_risk_profile(query_lower)
        
        # Detect constraints
        constraints = self._detect_constraints(query_lower)
        
        # Detect account type
        account_type = self._detect_account_type(query_lower)
        
        # Detect leverage
        leverage_allowed = "leverage" in query_lower and "no leverage" not in query_lower
        max_leverage = self._extract_leverage(query_lower) if leverage_allowed else 1.0
        
        # Detect benchmark
        benchmark = self._detect_benchmark(query_lower, tickers)
        
        # Detect date range
        start_date, end_date, lookback = self._detect_dates(query_lower)
        
        # Generate goal summary
        goal = self._generate_goal(query, deliverable)
        
        # Check for clarifications needed
        clarifications = self._check_clarifications(
            query, tickers, deliverable, horizon, constraints
        )
        
        return ResearchPlan(
            goal=goal,
            assets=tickers,
            asset_classes=asset_classes,
            horizon=horizon,
            benchmark=benchmark,
            risk_profile=risk_profile,
            constraints=constraints,
            deliverable=deliverable,
            account_type=account_type,
            leverage_allowed=leverage_allowed,
            max_leverage=max_leverage,
            tax_aware="tax" in query_lower,
            start_date=start_date,
            end_date=end_date,
            lookback_period=lookback,
            clarifications_needed=clarifications,
            context={"original_query": query},
        )
    
    def _detect_deliverable(self, text: str) -> DeliverableType:
        """Detect the type of deliverable requested."""
        for dtype, patterns in DELIVERABLE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return dtype
        return DeliverableType.ANALYSIS
    
    def _detect_horizon(self, text: str) -> TimeHorizon:
        """Detect time horizon from text."""
        for horizon, patterns in HORIZON_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return horizon
        return self.default_horizon
    
    def _detect_risk_profile(self, text: str) -> RiskProfile:
        """Detect risk profile from text."""
        for profile, patterns in RISK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return profile
        return self.default_risk
    
    def _detect_constraints(self, text: str) -> List[Constraint]:
        """Extract constraints from text."""
        constraints = []
        
        for pattern, constraint_type in CONSTRAINT_PATTERNS:
            match = re.search(pattern, text)
            if match:
                value = float(match.group(1)) if match.groups() else 1.0
                
                # Normalize percentage values
                if constraint_type in ["max_weight", "max_drawdown", "max_turnover", "sector_cap"]:
                    if value > 1:  # Assume it's a percentage
                        value = value / 100
                
                constraints.append(Constraint(
                    name=constraint_type,
                    type=constraint_type,
                    value=value,
                ))
        
        return constraints
    
    def _detect_account_type(self, text: str) -> Optional[str]:
        """Detect account type from text."""
        for account, patterns in ACCOUNT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return account
        return None
    
    def _extract_leverage(self, text: str) -> float:
        """Extract leverage multiplier from text."""
        match = re.search(r"(\d+(?:\.\d+)?)\s*x\s*leverage", text)
        if match:
            return float(match.group(1))
        
        match = re.search(r"leverage\s*(?:of\s*)?(\d+(?:\.\d+)?)", text)
        if match:
            return float(match.group(1))
        
        return 2.0  # Default leverage if mentioned but not specified
    
    def _detect_benchmark(self, text: str, tickers: List[str]) -> str:
        """Detect benchmark from text or infer from context."""
        # Explicit benchmark mention
        match = re.search(r"(?:benchmark|vs|against|compared to)\s+([A-Z]{2,5})", text.upper())
        if match:
            return match.group(1)
        
        # Infer from asset classes
        if any(detect_asset_class(t) == AssetClass.CRYPTO for t in tickers):
            return "BTC"
        elif any(detect_asset_class(t) in [AssetClass.RATES, AssetClass.COMMODITY] for t in tickers):
            return "SPY"  # Default
        
        return self.default_benchmark
    
    def _detect_dates(self, text: str) -> Tuple[Optional[date], Optional[date], str]:
        """Detect date range from text."""
        today = date.today()
        
        # Explicit date patterns
        date_match = re.search(
            r"from\s+(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})",
            text
        )
        if date_match:
            return (
                date.fromisoformat(date_match.group(1)),
                date.fromisoformat(date_match.group(2)),
                ""
            )
        
        # Lookback patterns
        lookback_patterns = [
            (r"(\d+)\s*years?", lambda m: f"{m.group(1)}y"),
            (r"(\d+)\s*months?", lambda m: f"{m.group(1)}mo"),
            (r"(\d+)\s*weeks?", lambda m: f"{m.group(1)}w"),
            (r"(\d+)\s*days?", lambda m: f"{m.group(1)}d"),
            (r"\b(ytd|mtd)\b", lambda m: m.group(1)),
        ]
        
        for pattern, extractor in lookback_patterns:
            match = re.search(pattern, text)
            if match:
                return None, None, extractor(match)
        
        # Default lookback
        return None, None, "2y"
    
    def _generate_goal(self, query: str, deliverable: DeliverableType) -> str:
        """Generate a concise goal statement."""
        # Clean and truncate query
        goal = query.strip()
        if len(goal) > 200:
            goal = goal[:197] + "..."
        return goal
    
    def _check_clarifications(
        self,
        query: str,
        tickers: List[str],
        deliverable: DeliverableType,
        horizon: TimeHorizon,
        constraints: List[Constraint],
    ) -> List[str]:
        """Check if clarifications are needed."""
        clarifications = []
        
        # No tickers found
        if not tickers and deliverable in [
            DeliverableType.ANALYSIS,
            DeliverableType.COMPARISON,
            DeliverableType.BACKTEST,
        ]:
            clarifications.append("Which ticker(s) would you like to analyze?")
        
        # Vague comparison
        if deliverable == DeliverableType.COMPARISON and len(tickers) < 2:
            clarifications.append("Please specify at least two assets to compare.")
        
        # Strategy without specifics
        if deliverable == DeliverableType.STRATEGY and "strategy" in query.lower():
            if not any(word in query.lower() for word in ["momentum", "trend", "mean reversion", "value", "carry"]):
                clarifications.append("What type of strategy are you interested in? (momentum, mean reversion, value, trend following, etc.)")
        
        # Backtest without strategy
        if deliverable == DeliverableType.BACKTEST:
            strategy_words = ["sma", "ema", "rsi", "macd", "momentum", "mean reversion", "crossover"]
            if not any(word in query.lower() for word in strategy_words):
                clarifications.append("Which strategy would you like to backtest?")
        
        return clarifications


# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

class PromptPresets:
    """Pre-built prompt templates for common tasks."""
    
    PRESETS = {
        "etf_due_diligence": {
            "name": "ETF Due Diligence",
            "description": "Comprehensive analysis of an ETF",
            "template": "Perform a comprehensive due diligence on {ticker}: holdings analysis, concentration risk, factor tilts, fees, tracking error, liquidity, and how it compares to alternatives.",
        },
        "pairs_trade": {
            "name": "Pairs Trade Analysis",
            "description": "Statistical arbitrage pair analysis",
            "template": "Analyze {ticker1} vs {ticker2} as a pairs trade: cointegration test, spread analysis, optimal hedge ratio, entry/exit signals, and historical performance.",
        },
        "defensive_portfolio": {
            "name": "Defensive Portfolio",
            "description": "Low-volatility, capital preservation focus",
            "template": "Build a defensive portfolio with {tickers}: minimize drawdown, target volatility < 10%, focus on quality and low-beta stocks, suggest hedges.",
        },
        "momentum_rotation": {
            "name": "Momentum Rotation",
            "description": "Sector/asset momentum strategy",
            "template": "Design a momentum rotation strategy for {tickers}: rank by momentum score, rebalance frequency, position sizing, and backtest with transaction costs.",
        },
        "earnings_preview": {
            "name": "Earnings Preview",
            "description": "Pre-earnings analysis",
            "template": "Earnings preview for {ticker}: expected move from options, historical earnings reactions, consensus estimates, key metrics to watch, and trade setup.",
        },
        "risk_assessment": {
            "name": "Risk Assessment",
            "description": "Comprehensive risk analysis",
            "template": "Full risk assessment of {ticker}: factor exposures, tail risk metrics, stress test scenarios, correlation to macro factors, and hedging suggestions.",
        },
        "valuation_deep_dive": {
            "name": "Valuation Deep Dive",
            "description": "Fundamental valuation analysis",
            "template": "Deep dive valuation of {ticker}: DCF model assumptions, comparable analysis, margin of safety, key value drivers, and sensitivity analysis.",
        },
        "sector_rotation": {
            "name": "Sector Rotation",
            "description": "Sector allocation strategy",
            "template": "Sector rotation analysis: current sector momentum, macro environment assessment, recommended tilts, and sector ETF suggestions.",
        },
    }
    
    @classmethod
    def get_preset(cls, name: str, **kwargs) -> Optional[str]:
        """Get a preset template with filled parameters."""
        if name not in cls.PRESETS:
            return None
        
        preset = cls.PRESETS[name]
        template = preset["template"]
        
        # Fill in placeholders
        for key, value in kwargs.items():
            if isinstance(value, list):
                value = ", ".join(value)
            template = template.replace(f"{{{key}}}", str(value))
        
        return template
    
    @classmethod
    def list_presets(cls) -> List[Dict[str, str]]:
        """List all available presets."""
        return [
            {"name": key, **value}
            for key, value in cls.PRESETS.items()
        ]


# ============================================================================
# DECISIVENESS ENGINE
# ============================================================================

class DecisivenessEngine:
    """Convert vague prompts into measurable criteria and score tradeoffs."""
    
    # Mapping of vague terms to measurable criteria
    VAGUE_TO_MEASURABLE = {
        "safer": ["lower volatility", "smaller max drawdown", "higher Sharpe ratio", "lower beta"],
        "better": ["higher Sharpe ratio", "higher total return", "lower max drawdown"],
        "riskier": ["higher volatility", "larger max drawdown", "higher beta"],
        "stable": ["lower volatility", "smaller drawdowns", "consistent returns"],
        "growth": ["higher CAGR", "higher momentum", "higher earnings growth"],
        "value": ["lower P/E", "lower P/B", "higher dividend yield"],
        "defensive": ["lower beta", "lower volatility", "smaller drawdowns"],
        "aggressive": ["higher beta", "higher volatility", "higher returns"],
        "liquid": ["higher average volume", "tighter spreads", "larger market cap"],
        "diversified": ["lower concentration", "more holdings", "lower correlation"],
    }
    
    @classmethod
    def translate_vague_query(cls, query: str) -> Dict[str, Any]:
        """Translate vague query into measurable criteria."""
        query_lower = query.lower()
        
        criteria = []
        weights = {}
        
        for vague_term, measurables in cls.VAGUE_TO_MEASURABLE.items():
            if vague_term in query_lower:
                criteria.extend(measurables)
                for m in measurables:
                    weights[m] = weights.get(m, 0) + 1
        
        # Normalize weights
        total = sum(weights.values()) or 1
        weights = {k: v / total for k, v in weights.items()}
        
        return {
            "criteria": list(set(criteria)),
            "weights": weights,
            "interpretation": cls._generate_interpretation(criteria),
        }
    
    @classmethod
    def _generate_interpretation(cls, criteria: List[str]) -> str:
        """Generate human-readable interpretation."""
        if not criteria:
            return "No specific criteria detected. Using balanced evaluation."
        
        return f"Evaluating based on: {', '.join(criteria[:5])}"
    
    @classmethod
    def score_assets(
        cls,
        assets: List[str],
        metrics: Dict[str, Dict[str, float]],
        weights: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """Score and rank assets based on criteria."""
        scores = []
        
        metric_mapping = {
            "lower volatility": ("volatility", -1),
            "smaller max drawdown": ("max_drawdown", -1),
            "higher Sharpe ratio": ("sharpe_ratio", 1),
            "lower beta": ("beta", -1),
            "higher total return": ("total_return", 1),
            "higher CAGR": ("cagr", 1),
            "higher momentum": ("momentum", 1),
            "lower P/E": ("pe_ratio", -1),
            "higher dividend yield": ("dividend_yield", 1),
        }
        
        for asset in assets:
            asset_metrics = metrics.get(asset, {})
            score = 0
            details = {}
            
            for criterion, weight in weights.items():
                if criterion in metric_mapping:
                    metric_name, direction = metric_mapping[criterion]
                    value = asset_metrics.get(metric_name, 0)
                    contribution = value * direction * weight
                    score += contribution
                    details[criterion] = {
                        "value": value,
                        "contribution": contribution,
                    }
            
            scores.append({
                "asset": asset,
                "total_score": score,
                "details": details,
            })
        
        # Sort by score
        scores.sort(key=lambda x: x["total_score"], reverse=True)
        
        return scores
    
    @classmethod
    def explain_tradeoffs(
        cls,
        scores: List[Dict[str, Any]],
        criteria: List[str],
    ) -> str:
        """Generate tradeoff explanation."""
        if len(scores) < 2:
            return "Not enough assets to compare tradeoffs."
        
        best = scores[0]
        second = scores[1]
        
        explanations = []
        explanations.append(f"{best['asset']} ranks highest overall.")
        
        # Find where second asset is better
        for criterion in criteria:
            if criterion in best["details"] and criterion in second["details"]:
                best_val = best["details"][criterion]["value"]
                second_val = second["details"][criterion]["value"]
                
                if abs(second_val) > abs(best_val):
                    explanations.append(
                        f"However, {second['asset']} has better {criterion} ({second_val:.2f} vs {best_val:.2f})."
                    )
        
        return " ".join(explanations)
