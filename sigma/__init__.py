"""
Sigma v3.2.0 - Finance Research Agent

An elite finance research agent combining:
- Multi-provider AI (Google Gemini, OpenAI, Anthropic, Groq, xAI, Ollama)
- Real-time market data and analytics
- Advanced charting and visualization
- Strategy discovery and backtesting
- Portfolio optimization and risk management
- Robustness testing and stress analysis
- Research memo generation and export
- Monitoring, alerts, and watchlists
"""

__version__ = "3.2.0"
__author__ = "Sigma Team"

# Core functionality
from .app import launch, SigmaApp
from .cli import main

# Configuration
from .config import get_settings, save_api_key, LLMProvider

# Data tools
from .tools import (
    get_stock_quote,
    get_stock_history,
    get_company_info,
    get_financial_statements,
    get_analyst_recommendations,
    technical_analysis,
    compare_stocks,
    get_market_overview,
    get_sector_performance,
    TOOLS,
    execute_tool,
)

# Backtesting
from .backtest import run_backtest, get_available_strategies

# Analytics
from .analytics import (
    PerformanceAnalytics,
    RegimeDetector,
    SeasonalityAnalyzer,
    FactorAnalyzer,
    CorrelationAnalyzer,
    MonteCarloSimulator,
)

# Comparison
from .comparison import ComparisonEngine, MacroSensitivityAnalyzer

# Strategy
from .strategy import (
    HypothesisGenerator,
    HypothesisTester,
    RuleConverter,
    StrategyGenerator,
)

# Portfolio
from .portfolio import (
    PortfolioOptimizer,
    OptimizationMethod,
    PositionSizer,
    RiskEngine,
    RebalancingEngine,
)

# Visualization
from .visualization import ChartBuilder, ChartRecipes, AutoCaptionGenerator

# Reporting
from .reporting import (
    MemoGenerator,
    ExportEngine,
    ReproducibilityEngine,
    SessionLogger,
)

# Monitoring
from .monitoring import (
    AlertEngine,
    WatchlistManager,
    DriftDetector,
    ScheduledRunner,
    Alert,
    AlertType,
)

# Robustness
from .robustness import (
    StressTester,
    OverfittingDetector,
    ExplainabilityEngine,
    SampleSizeValidator,
    BiasDetector,
)

# Setup
from .setup import run_setup, quick_setup

__all__ = [
    # Version
    "__version__",
    
    # Core
    "launch",
    "main",
    "SigmaApp",
    
    # Config
    "get_settings",
    "save_api_key",
    "LLMProvider",
    
    # Tools
    "get_stock_quote",
    "get_stock_history",
    "get_company_info",
    "technical_analysis",
    "compare_stocks",
    "TOOLS",
    "execute_tool",
    
    # Backtesting
    "run_backtest",
    "get_available_strategies",
    
    # Analytics
    "PerformanceAnalytics",
    "RegimeDetector",
    "SeasonalityAnalyzer",
    "FactorAnalyzer",
    "CorrelationAnalyzer",
    "MonteCarloSimulator",
    
    # Comparison
    "ComparisonEngine",
    "MacroSensitivityAnalyzer",
    
    # Strategy
    "HypothesisGenerator",
    "HypothesisTester",
    "RuleConverter",
    "StrategyGenerator",
    
    # Portfolio
    "PortfolioOptimizer",
    "OptimizationMethod",
    "PositionSizer",
    "RiskEngine",
    "RebalancingEngine",
    
    # Visualization
    "ChartBuilder",
    "ChartRecipes",
    "AutoCaptionGenerator",
    
    # Reporting
    "MemoGenerator",
    "ExportEngine",
    "ReproducibilityEngine",
    "SessionLogger",
    
    # Monitoring
    "AlertEngine",
    "WatchlistManager",
    "DriftDetector",
    "Alert",
    "AlertType",
    
    # Robustness
    "StressTester",
    "OverfittingDetector",
    "ExplainabilityEngine",
    "SampleSizeValidator",
    
    # Setup
    "run_setup",
    "quick_setup",
]
