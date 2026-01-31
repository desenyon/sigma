"""Main research engine orchestrating all Sigma capabilities."""

import asyncio
import json
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    ResearchPlan,
    DeliverableType,
    DataLineage,
    DataQualityReport,
    PerformanceMetrics,
    ComparisonResult,
    BacktestResult,
    ResearchMemo,
    Alert,
    RegimeAnalysis,
    Regime,
)
from .intent import IntentParser, DecisivenessEngine, PromptPresets


class SigmaEngine:
    """Main research engine for Sigma."""
    
    def __init__(self):
        self.intent_parser = IntentParser()
        self.decisiveness = DecisivenessEngine()
        self.presets = PromptPresets()
        self.data_cache = {}
        self.lineage_tracker = []
    
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a user query end-to-end."""
        # Parse intent
        plan = self.intent_parser.parse(query)
        
        # Check if clarifications needed
        if plan.clarifications_needed:
            return {
                "type": "clarification",
                "questions": plan.clarifications_needed,
                "partial_plan": plan.model_dump(),
            }
        
        # Handle vague queries with decisiveness engine
        vague_translation = self.decisiveness.translate_vague_query(query)
        if vague_translation["criteria"]:
            plan.context["measurable_criteria"] = vague_translation
        
        # Route to appropriate handler
        result = await self._route_deliverable(plan)
        
        return {
            "type": "result",
            "plan": plan.model_dump(),
            "result": result,
        }
    
    async def _route_deliverable(self, plan: ResearchPlan) -> Dict[str, Any]:
        """Route to appropriate handler based on deliverable type."""
        handlers = {
            DeliverableType.ANALYSIS: self._handle_analysis,
            DeliverableType.COMPARISON: self._handle_comparison,
            DeliverableType.BACKTEST: self._handle_backtest,
            DeliverableType.PORTFOLIO: self._handle_portfolio,
            DeliverableType.STRATEGY: self._handle_strategy,
            DeliverableType.CHART: self._handle_chart,
            DeliverableType.REPORT: self._handle_report,
            DeliverableType.ALERT: self._handle_alert,
        }
        
        handler = handlers.get(plan.deliverable, self._handle_analysis)
        return await handler(plan)
    
    async def _handle_analysis(self, plan: ResearchPlan) -> Dict[str, Any]:
        """Handle general analysis request."""
        results = {}
        
        for symbol in plan.assets:
            # This will be implemented with actual data fetching
            results[symbol] = {
                "symbol": symbol,
                "analysis_type": "comprehensive",
                "metrics": {},
                "insights": [],
            }
        
        return {"analyses": results}
    
    async def _handle_comparison(self, plan: ResearchPlan) -> Dict[str, Any]:
        """Handle comparison request."""
        # Get measurable criteria from vague query
        criteria = plan.context.get("measurable_criteria", {})
        
        return {
            "comparison_type": "multi_asset",
            "assets": plan.assets,
            "criteria": criteria.get("criteria", []),
            "interpretation": criteria.get("interpretation", ""),
        }
    
    async def _handle_backtest(self, plan: ResearchPlan) -> Dict[str, Any]:
        """Handle backtest request."""
        return {
            "backtest_type": "strategy",
            "assets": plan.assets,
            "period": plan.lookback_period,
            "constraints": [c.model_dump() for c in plan.constraints],
        }
    
    async def _handle_portfolio(self, plan: ResearchPlan) -> Dict[str, Any]:
        """Handle portfolio construction request."""
        return {
            "portfolio_type": "optimization",
            "assets": plan.assets,
            "risk_profile": plan.risk_profile,
            "constraints": [c.model_dump() for c in plan.constraints],
        }
    
    async def _handle_strategy(self, plan: ResearchPlan) -> Dict[str, Any]:
        """Handle strategy discovery request."""
        return {
            "strategy_type": "discovery",
            "assets": plan.assets,
            "horizon": plan.horizon,
        }
    
    async def _handle_chart(self, plan: ResearchPlan) -> Dict[str, Any]:
        """Handle chart generation request."""
        return {
            "chart_type": "price",
            "assets": plan.assets,
            "period": plan.lookback_period,
        }
    
    async def _handle_report(self, plan: ResearchPlan) -> Dict[str, Any]:
        """Handle report generation request."""
        return {
            "report_type": "research_memo",
            "assets": plan.assets,
        }
    
    async def _handle_alert(self, plan: ResearchPlan) -> Dict[str, Any]:
        """Handle alert setup request."""
        return {
            "alert_type": "watchlist",
            "assets": plan.assets,
        }
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_presets(self) -> List[Dict[str, str]]:
        """Get available prompt presets."""
        return self.presets.list_presets()
    
    def apply_preset(self, preset_name: str, **kwargs) -> Optional[str]:
        """Apply a prompt preset."""
        return self.presets.get_preset(preset_name, **kwargs)
    
    def get_show_work_mode(self) -> bool:
        """Check if show work mode is enabled."""
        return getattr(self, "_show_work", False)
    
    def set_show_work_mode(self, enabled: bool):
        """Enable/disable show work mode."""
        self._show_work = enabled
    
    def explain_technical(self, concept: str) -> str:
        """Explain a concept with formulas and definitions."""
        explanations = {
            "sharpe_ratio": """
**Sharpe Ratio**
Formula: (Rp - Rf) / σp
Where:
- Rp = Portfolio return
- Rf = Risk-free rate
- σp = Portfolio standard deviation

Interpretation: Risk-adjusted return per unit of volatility. Higher is better.
Typical values: <1 = poor, 1-2 = good, >2 = excellent
            """,
            "sortino_ratio": """
**Sortino Ratio**
Formula: (Rp - Rf) / σd
Where:
- Rp = Portfolio return
- Rf = Risk-free rate (or target return)
- σd = Downside deviation (only negative returns)

Interpretation: Like Sharpe but only penalizes downside volatility.
Better for asymmetric return distributions.
            """,
            "max_drawdown": """
**Maximum Drawdown**
Formula: (Peak - Trough) / Peak
Measures the largest peak-to-trough decline.

Interpretation: Worst-case loss from a peak.
Context: A 50% drawdown requires 100% gain to recover.
            """,
            "beta": """
**Beta (β)**
Formula: Cov(Ri, Rm) / Var(Rm)
Where:
- Ri = Asset return
- Rm = Market return

Interpretation: Sensitivity to market movements.
β = 1: Moves with market
β > 1: More volatile than market
β < 1: Less volatile than market
            """,
            "var": """
**Value at Risk (VaR)**
Formula: Quantile of return distribution at confidence level
Example: 95% VaR = 5th percentile of returns

Interpretation: Maximum expected loss at given confidence level.
95% VaR of -3% means 95% of the time, loss won't exceed 3%.
            """,
            "cvar": """
**Conditional VaR (CVaR) / Expected Shortfall**
Formula: E[Loss | Loss > VaR]
Average loss in the worst cases beyond VaR.

Interpretation: Expected loss when VaR is breached.
Better captures tail risk than VaR alone.
            """,
        }
        
        return explanations.get(concept.lower(), f"No detailed explanation available for: {concept}")


# ============================================================================
# AUTOCOMPLETE ENGINE
# ============================================================================

class AutocompleteEngine:
    """Provide intelligent autocomplete suggestions."""
    
    # Common commands
    COMMANDS = [
        "/help", "/keys", "/models", "/provider", "/model", "/backtest",
        "/status", "/export", "/clear", "/compare", "/chart", "/report",
        "/alert", "/watchlist", "/portfolio", "/strategy", "/preset",
    ]
    
    # Common phrases
    PHRASES = [
        "analyze {ticker}",
        "compare {ticker1} vs {ticker2}",
        "backtest {strategy} on {ticker}",
        "show me a chart of {ticker}",
        "what's the sentiment on {ticker}",
        "build a portfolio with {tickers}",
        "run technical analysis on {ticker}",
        "how does {ticker} compare to {benchmark}",
        "what's the Sharpe ratio of {ticker}",
        "show factor exposures for {ticker}",
        "detect regime for {ticker}",
        "run stress test on {portfolio}",
        "generate research memo for {ticker}",
        "set alert when {ticker} drops below {price}",
    ]
    
    # Strategy names
    STRATEGIES = [
        "sma_crossover", "rsi_mean_reversion", "macd_momentum",
        "bollinger_bands", "dual_momentum", "breakout",
        "trend_following", "mean_reversion", "carry",
        "value", "quality", "momentum", "low_volatility",
    ]
    
    # Common tickers
    TICKERS = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
        "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO",
        "XLK", "XLF", "XLE", "XLV", "XLI",
        "GLD", "SLV", "TLT", "BND",
        "BTC", "ETH",
    ]
    
    @classmethod
    def get_suggestions(cls, text: str, max_results: int = 10) -> List[str]:
        """Get autocomplete suggestions for partial input."""
        text = text.lower().strip()
        suggestions = []
        
        # Command completion
        if text.startswith("/"):
            suggestions.extend([
                cmd for cmd in cls.COMMANDS
                if cmd.lower().startswith(text)
            ])
        
        # Ticker completion
        words = text.split()
        if words:
            last_word = words[-1].upper()
            if len(last_word) >= 1:
                matching_tickers = [
                    t for t in cls.TICKERS
                    if t.startswith(last_word)
                ]
                suggestions.extend([
                    " ".join(words[:-1] + [t]) for t in matching_tickers
                ])
        
        # Strategy completion
        if "backtest" in text or "strategy" in text:
            for strategy in cls.STRATEGIES:
                if strategy not in text:
                    suggestions.append(text + " " + strategy)
        
        # Phrase completion
        for phrase in cls.PHRASES:
            phrase_lower = phrase.lower()
            if text in phrase_lower:
                suggestions.append(phrase)
        
        return suggestions[:max_results]
    
    @classmethod
    def get_ticker_suggestions(cls, partial: str) -> List[str]:
        """Get ticker suggestions for partial input."""
        partial = partial.upper()
        return [t for t in cls.TICKERS if t.startswith(partial)][:10]
    
    @classmethod
    def get_command_help(cls, command: str) -> str:
        """Get help text for a command."""
        help_texts = {
            "/help": "Show all available commands",
            "/keys": "Configure API keys for providers",
            "/models": "List available AI models",
            "/provider": "Switch AI provider (google, openai, anthropic, groq, ollama)",
            "/model": "Switch to a specific model",
            "/backtest": "Show available backtest strategies",
            "/status": "Show current configuration",
            "/export": "Export conversation to file",
            "/clear": "Clear chat history",
            "/compare": "Compare multiple assets",
            "/chart": "Generate a chart",
            "/report": "Generate a research report",
            "/alert": "Set up price or signal alerts",
            "/watchlist": "Manage your watchlist",
            "/portfolio": "Portfolio analysis and optimization",
            "/strategy": "Discover and test strategies",
            "/preset": "Use a prompt preset template",
        }
        return help_texts.get(command, "No help available for this command")


# ============================================================================
# SHOW WORK MODE
# ============================================================================

class ShowWorkLogger:
    """Log and display the agent's reasoning process."""
    
    def __init__(self):
        self.steps = []
        self.assumptions = []
        self.scoring_rubric = {}
    
    def log_step(self, step: str, details: Optional[Dict[str, Any]] = None):
        """Log a reasoning step."""
        self.steps.append({
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "details": details or {},
        })
    
    def log_assumption(self, assumption: str):
        """Log an assumption being made."""
        self.assumptions.append(assumption)
    
    def set_scoring_rubric(self, rubric: Dict[str, float]):
        """Set the scoring rubric being used."""
        self.scoring_rubric = rubric
    
    def get_work_log(self) -> str:
        """Get formatted work log."""
        lines = []
        lines.append("## Reasoning Process\n")
        
        if self.assumptions:
            lines.append("### Assumptions")
            for a in self.assumptions:
                lines.append(f"- {a}")
            lines.append("")
        
        if self.scoring_rubric:
            lines.append("### Scoring Rubric")
            for criterion, weight in self.scoring_rubric.items():
                lines.append(f"- {criterion}: {weight:.1%}")
            lines.append("")
        
        if self.steps:
            lines.append("### Steps Taken")
            for i, step in enumerate(self.steps, 1):
                lines.append(f"{i}. {step['step']}")
                if step.get("details"):
                    for k, v in step["details"].items():
                        lines.append(f"   - {k}: {v}")
            lines.append("")
        
        return "\n".join(lines)
    
    def clear(self):
        """Clear the work log."""
        self.steps = []
        self.assumptions = []
        self.scoring_rubric = {}


# ============================================================================
# SAFETY GUARDRAILS
# ============================================================================

class SafetyGuardrails:
    """Enforce safety and correctness checks."""
    
    @staticmethod
    def check_lookahead_bias(code: str) -> List[str]:
        """Check for potential lookahead bias in code."""
        warnings = []
        
        # Common lookahead patterns
        patterns = [
            (r"shift\(-", "Negative shift may cause lookahead bias"),
            (r"\.future", "Future reference detected"),
            (r"iloc\[-\d+\]", "Negative indexing without proper offset"),
            (r"fillna\(method='bfill'\)", "Backward fill can cause lookahead"),
        ]
        
        import re
        for pattern, message in patterns:
            if re.search(pattern, code):
                warnings.append(message)
        
        return warnings
    
    @staticmethod
    def check_sample_size(n_samples: int, n_parameters: int) -> Dict[str, Any]:
        """Check if sample size is sufficient."""
        min_recommended = n_parameters * 50  # Rule of thumb
        
        return {
            "sample_size": n_samples,
            "parameters": n_parameters,
            "min_recommended": min_recommended,
            "sufficient": n_samples >= min_recommended,
            "warning": f"Sample size ({n_samples}) may be too small for {n_parameters} parameters. Recommend at least {min_recommended}." if n_samples < min_recommended else None,
        }
    
    @staticmethod
    def validate_indicator_timing(indicator_name: str, window: int, data_length: int) -> Dict[str, Any]:
        """Validate that indicator uses only past data."""
        warmup_needed = window
        valid_start = warmup_needed
        
        return {
            "indicator": indicator_name,
            "window": window,
            "data_length": data_length,
            "warmup_needed": warmup_needed,
            "valid_start_index": valid_start,
            "warning": f"First {warmup_needed} observations are warmup period" if warmup_needed > 0 else None,
        }
    
    @staticmethod
    def disclaimer() -> str:
        """Get standard disclaimer."""
        return """
**Disclaimer**: This analysis is for informational and educational purposes only. 
It does not constitute financial advice, investment recommendations, or a solicitation 
to buy or sell securities. Past performance does not guarantee future results. 
Always consult with a qualified financial advisor before making investment decisions.
        """.strip()
    
    @staticmethod
    def separate_research_from_advice(content: str) -> Dict[str, str]:
        """Explicitly separate research findings from advice."""
        return {
            "research_findings": content,
            "advice_section": "For personalized advice, please consult a licensed financial advisor.",
            "disclaimer": SafetyGuardrails.disclaimer(),
        }
