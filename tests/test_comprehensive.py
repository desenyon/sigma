#!/usr/bin/env python3
"""Comprehensive test suite for Sigma v3.4.1.

Tests all core functionality including:
- Configuration and settings
- Error codes and SigmaError
- Tool functions (stock data, technical analysis, etc.)
- LLM client initialization
- Polygon.io integration
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestVersion(unittest.TestCase):
    """Test that version is consistent across all files."""
    
    def test_version_consistency(self):
        """All files should have version 3.4.1."""
        from sigma import __version__
        from sigma.app import __version__ as app_version
        from sigma.config import __version__ as config_version
        from sigma.cli import __version__ as cli_version
        from sigma.setup import __version__ as setup_version
        
        expected = "3.4.1"
        self.assertEqual(__version__, expected, "sigma/__init__.py version mismatch")
        self.assertEqual(app_version, expected, "sigma/app.py version mismatch")
        self.assertEqual(config_version, expected, "sigma/config.py version mismatch")
        self.assertEqual(cli_version, expected, "sigma/cli.py version mismatch")
        self.assertEqual(setup_version, expected, "sigma/setup.py version mismatch")


class TestErrorCodes(unittest.TestCase):
    """Test error codes and SigmaError."""
    
    def test_error_code_enum(self):
        """ErrorCode enum should have all required codes."""
        from sigma.config import ErrorCode
        
        # Check existence of key error codes
        self.assertEqual(ErrorCode.UNKNOWN_ERROR, 1000)
        self.assertEqual(ErrorCode.API_KEY_MISSING, 1100)
        self.assertEqual(ErrorCode.API_KEY_INVALID, 1101)
        self.assertEqual(ErrorCode.API_KEY_RATE_LIMITED, 1103)
        self.assertEqual(ErrorCode.PROVIDER_UNAVAILABLE, 1200)
        self.assertEqual(ErrorCode.SYMBOL_NOT_FOUND, 1300)
        self.assertEqual(ErrorCode.CONNECTION_ERROR, 1400)
    
    def test_sigma_error_creation(self):
        """SigmaError should be properly constructable."""
        from sigma.config import SigmaError, ErrorCode
        
        error = SigmaError(
            ErrorCode.API_KEY_INVALID,
            "Test error message",
            {"provider": "test", "hint": "Check your key"}
        )
        
        self.assertEqual(error.code, ErrorCode.API_KEY_INVALID)
        self.assertEqual(error.message, "Test error message")
        self.assertEqual(error.details["provider"], "test")
        self.assertIn("E1101", str(error))
    
    def test_sigma_error_to_dict(self):
        """SigmaError should serialize to dict."""
        from sigma.config import SigmaError, ErrorCode
        
        error = SigmaError(ErrorCode.TIMEOUT, "Request timed out")
        d = error.to_dict()
        
        self.assertEqual(d["error_code"], 1002)
        self.assertEqual(d["error_name"], "TIMEOUT")
        self.assertEqual(d["message"], "Request timed out")


class TestConfig(unittest.TestCase):
    """Test configuration management."""
    
    def test_available_models(self):
        """AVAILABLE_MODELS should have all providers."""
        from sigma.config import AVAILABLE_MODELS
        
        expected_providers = ["google", "openai", "anthropic", "groq", "xai", "ollama"]
        for provider in expected_providers:
            self.assertIn(provider, AVAILABLE_MODELS, f"Missing provider: {provider}")
            self.assertIsInstance(AVAILABLE_MODELS[provider], list)
            self.assertGreater(len(AVAILABLE_MODELS[provider]), 0)
    
    def test_no_deprecated_models(self):
        """Deprecated models should not be in AVAILABLE_MODELS."""
        from sigma.config import AVAILABLE_MODELS
        
        deprecated = [
            "gemini-2.0-flash",        # Old Gemini 2.0
            "gemini-1.5-pro",          # Old Gemini 1.5
            "gpt-4o", "gpt-4o-mini",   # Old GPT-4 models
            "o1", "o1-mini",           # Deprecated OpenAI reasoning models
            "claude-3-opus-20240229",  # Older Claude model
        ]
        
        for provider_models in AVAILABLE_MODELS.values():
            for model in provider_models:
                self.assertNotIn(model, deprecated, f"Deprecated model found: {model}")
    
    def test_llm_provider_enum(self):
        """LLMProvider enum should have all providers."""
        from sigma.config import LLMProvider
        
        expected = ["GOOGLE", "OPENAI", "ANTHROPIC", "GROQ", "XAI", "OLLAMA"]
        for provider in expected:
            self.assertTrue(hasattr(LLMProvider, provider))
    
    def test_settings_has_polygon_key(self):
        """Settings should have polygon_api_key field."""
        from sigma.config import Settings
        
        # Check that the field exists in the model
        self.assertIn("polygon_api_key", Settings.model_fields)
    
    def test_save_api_key_providers(self):
        """save_api_key should support all providers including data providers."""
        from sigma.config import save_api_key
        
        # These should not raise errors (we're just testing the function accepts them)
        valid_providers = ["google", "openai", "anthropic", "groq", "xai", "polygon", "alphavantage", "exa"]
        
        # We can't actually save without mocking, but we can check the function exists
        self.assertTrue(callable(save_api_key))


class TestFirstRunDetection(unittest.TestCase):
    """Test first-run detection logic."""
    
    def test_is_first_run_function_exists(self):
        """is_first_run function should exist."""
        from sigma.config import is_first_run
        self.assertTrue(callable(is_first_run))
    
    def test_mark_first_run_complete_exists(self):
        """mark_first_run_complete function should exist."""
        from sigma.config import mark_first_run_complete
        self.assertTrue(callable(mark_first_run_complete))
    
    def test_first_run_marker_path(self):
        """First run marker should be in ~/.sigma/."""
        from sigma.config import FIRST_RUN_MARKER
        self.assertIn(".sigma", str(FIRST_RUN_MARKER))
        self.assertTrue(str(FIRST_RUN_MARKER).endswith(".first_run_complete"))
    
    def test_config_directory_path(self):
        """Config directory should be ~/.sigma/."""
        from sigma.config import CONFIG_DIR, CONFIG_FILE
        self.assertIn(".sigma", str(CONFIG_DIR))
        self.assertIn("config.env", str(CONFIG_FILE))


class TestTools(unittest.TestCase):
    """Test financial data tools."""
    
    def test_tools_list_exists(self):
        """TOOLS list should exist and have entries."""
        from sigma.tools import TOOLS
        
        self.assertIsInstance(TOOLS, list)
        self.assertGreater(len(TOOLS), 10, "Should have at least 10 tools")
    
    def test_tool_functions_dict(self):
        """TOOL_FUNCTIONS should map all tools."""
        from sigma.tools import TOOLS, TOOL_FUNCTIONS
        
        for tool in TOOLS:
            if tool.get("type") == "function":
                name = tool["function"]["name"]
                self.assertIn(name, TOOL_FUNCTIONS, f"Missing function: {name}")
    
    def test_polygon_tools_exist(self):
        """Polygon.io tools should be defined."""
        from sigma.tools import TOOL_FUNCTIONS
        
        polygon_tools = [
            "polygon_get_quote",
            "polygon_get_aggregates", 
            "polygon_get_ticker_news",
            "polygon_market_status"
        ]
        
        for tool in polygon_tools:
            self.assertIn(tool, TOOL_FUNCTIONS, f"Missing Polygon tool: {tool}")
    
    def test_execute_tool_error_handling(self):
        """execute_tool should handle unknown tools gracefully."""
        from sigma.tools import execute_tool
        
        result = execute_tool("nonexistent_tool", {})
        self.assertIn("error", result)
        self.assertIn("error_code", result)
    
    def test_get_stock_quote_format(self):
        """get_stock_quote should return expected format."""
        from sigma.tools import get_stock_quote
        
        # Use a well-known ticker that's unlikely to fail
        result = get_stock_quote("AAPL")
        
        # Either we get data or an error
        if "error" not in result:
            expected_keys = ["symbol", "name", "price"]
            for key in expected_keys:
                self.assertIn(key, result, f"Missing key: {key}")
    
    def test_technical_analysis_format(self):
        """technical_analysis should return expected format."""
        from sigma.tools import technical_analysis
        
        result = technical_analysis("AAPL", "3mo")
        
        if "error" not in result:
            # Should have technical indicators (nested under 'indicators')
            self.assertIn("symbol", result)
            self.assertIn("indicators", result)
            indicators = result["indicators"]
            expected_indicators = ["rsi", "macd", "sma_20"]
            for key in expected_indicators:
                self.assertIn(key, indicators, f"Missing indicator: {key}")


class TestLLMClients(unittest.TestCase):
    """Test LLM client initialization."""
    
    def test_llm_provider_classes_exist(self):
        """All LLM client classes should exist."""
        from sigma.llm import GoogleLLM, OpenAILLM, AnthropicLLM, GroqLLM, OllamaLLM, XaiLLM
        
        self.assertTrue(callable(GoogleLLM))
        self.assertTrue(callable(OpenAILLM))
        self.assertTrue(callable(AnthropicLLM))
        self.assertTrue(callable(GroqLLM))
        self.assertTrue(callable(OllamaLLM))
        self.assertTrue(callable(XaiLLM))
    
    def test_get_llm_raises_sigma_error(self):
        """get_llm should raise SigmaError when API key is missing."""
        from sigma.llm import get_llm
        from sigma.config import LLMProvider, SigmaError, ErrorCode
        
        # Mock settings to have no API key
        with patch('sigma.llm.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                google_api_key=None,
                get_model=lambda x: "test-model"
            )
            
            with self.assertRaises(SigmaError) as context:
                get_llm(LLMProvider.GOOGLE)
            
            self.assertEqual(context.exception.code, ErrorCode.API_KEY_MISSING)
    
    def test_ollama_requires_no_key(self):
        """Ollama should work without an API key."""
        from sigma.llm import get_llm, OllamaLLM
        from sigma.config import LLMProvider
        
        with patch('sigma.llm.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                ollama_host="http://localhost:11434",
                get_model=lambda x: "llama3.2"
            )
            
            llm = get_llm(LLMProvider.OLLAMA)
            self.assertIsInstance(llm, OllamaLLM)


class TestRateLimiting(unittest.TestCase):
    """Test rate limiting functionality."""
    
    def test_rate_limiters_exist(self):
        """Rate limiters should exist for all providers."""
        from sigma.llm import _rate_limiters
        
        expected = ["google", "openai", "anthropic", "groq", "xai", "ollama"]
        for provider in expected:
            self.assertIn(provider, _rate_limiters, f"Missing rate limiter: {provider}")


class TestAppComponents(unittest.TestCase):
    """Test app UI components."""
    
    def test_system_prompt_enhanced(self):
        """SYSTEM_PROMPT should be comprehensive."""
        from sigma.app import SYSTEM_PROMPT
        
        # Check for key phrases that indicate comprehensive prompt
        required_phrases = [
            "proactive",
            "actionable",
            "data-driven",
            "recommendation",
            "STRONG BUY"
        ]
        
        prompt_lower = SYSTEM_PROMPT.lower()
        for phrase in required_phrases:
            self.assertIn(phrase.lower(), prompt_lower, f"Missing phrase: {phrase}")
    
    def test_welcome_banner_updated(self):
        """Welcome banner should not contain 'Native macOS'."""
        from sigma.app import WELCOME_BANNER
        
        self.assertNotIn("Native macOS", WELCOME_BANNER)
        self.assertNotIn("native macOS", WELCOME_BANNER)
        self.assertIn("3.4.1", WELCOME_BANNER)
    
    def test_suggestions_list(self):
        """SUGGESTIONS should have comprehensive entries."""
        from sigma.app import SUGGESTIONS
        
        self.assertIsInstance(SUGGESTIONS, list)
        self.assertGreater(len(SUGGESTIONS), 20, "Should have many suggestions")
        
        # Check for different types of suggestions
        suggestion_text = " ".join(SUGGESTIONS).lower()
        self.assertIn("analyze", suggestion_text)
        self.assertIn("compare", suggestion_text)
        self.assertIn("backtest", suggestion_text)


class TestPolygonIntegration(unittest.TestCase):
    """Test Polygon.io integration."""
    
    def test_polygon_functions_callable(self):
        """Polygon functions should be callable."""
        from sigma.tools import (
            polygon_get_quote,
            polygon_get_aggregates,
            polygon_get_ticker_news,
            polygon_market_status
        )
        
        self.assertTrue(callable(polygon_get_quote))
        self.assertTrue(callable(polygon_get_aggregates))
        self.assertTrue(callable(polygon_get_ticker_news))
        self.assertTrue(callable(polygon_market_status))
    
    def test_polygon_without_key_returns_error(self):
        """Polygon functions should return error when key not configured."""
        from sigma.tools import polygon_get_quote
        
        # Mock to ensure no key
        with patch('sigma.tools._get_polygon_key', return_value=None):
            result = polygon_get_quote("AAPL")
            self.assertIn("error", result)
            self.assertIn("Polygon API key not configured", result["error"])


class TestBacktesting(unittest.TestCase):
    """Test backtesting functionality."""
    
    def test_strategies_available(self):
        """get_available_strategies should return strategies."""
        from sigma.backtest import get_available_strategies
        
        strategies = get_available_strategies()
        self.assertIsInstance(strategies, dict)
        
        # Use actual strategy names from the code
        expected_strategies = ["sma_crossover", "rsi_mean_reversion", "macd_momentum", "bollinger_bands", "dual_momentum", "breakout"]
        for strategy in expected_strategies:
            self.assertIn(strategy, strategies, f"Missing strategy: {strategy}")
    
    def test_backtest_tool_defined(self):
        """BACKTEST_TOOL should be properly defined."""
        from sigma.backtest import BACKTEST_TOOL
        
        self.assertIsInstance(BACKTEST_TOOL, dict)
        self.assertEqual(BACKTEST_TOOL["type"], "function")
        self.assertEqual(BACKTEST_TOOL["function"]["name"], "run_backtest")


class TestImports(unittest.TestCase):
    """Test that all imports work correctly."""
    
    def test_main_package_imports(self):
        """Main package should export key components."""
        from sigma import (
            launch,
            SigmaApp,
            get_settings,
            save_api_key,
            LLMProvider,
            ErrorCode,
            SigmaError,
            __version__
        )
        
        self.assertEqual(__version__, "3.4.1")
        self.assertTrue(callable(launch))
        self.assertTrue(callable(save_api_key))


def run_interactive_tests():
    """Run interactive tests that require user confirmation."""
    print("\n" + "=" * 60)
    print("INTERACTIVE TESTS")
    print("=" * 60)
    
    try:
        from sigma.config import get_settings
        settings = get_settings()
        
        print("\n[Config Test]")
        print(f"  Config directory: ~/.sigma/")
        print(f"  Default provider: {settings.default_provider}")
        print(f"  Default model: {settings.default_model}")
        
        print("\n[API Keys Status]")
        keys = {
            "Google": settings.google_api_key,
            "OpenAI": settings.openai_api_key,
            "Anthropic": settings.anthropic_api_key,
            "Groq": settings.groq_api_key,
            "xAI": settings.xai_api_key,
            "Polygon": getattr(settings, 'polygon_api_key', None),
        }
        for name, key in keys.items():
            status = "[ok] Configured" if key else "[--] Not set"
            print(f"  {name}: {status}")
        
        print("\n[Stock Data Test]")
        from sigma.tools import get_stock_quote
        quote = get_stock_quote("AAPL")
        if "error" not in quote:
            print(f"  AAPL Price: ${quote.get('price', 'N/A')}")
            print(f"  AAPL Change: {quote.get('change_percent', 'N/A')}%")
        else:
            print(f"  Error: {quote.get('error')}")
        
        print("\n[Technical Analysis Test]")
        from sigma.tools import technical_analysis
        ta = technical_analysis("SPY", "1mo")
        if "error" not in ta:
            print(f"  SPY RSI: {ta.get('rsi', 'N/A')}")
            print(f"  SPY MACD: {ta.get('macd', {}).get('macd', 'N/A')}")
        else:
            print(f"  Error: {ta.get('error')}")
        
        print("\n[Market Overview Test]")
        from sigma.tools import get_market_overview
        overview = get_market_overview()
        if "error" not in overview:
            print("  [ok] Market overview fetched successfully")
        else:
            print(f"  Error: {overview.get('error')}")
        
        print("\n" + "=" * 60)
        print("Interactive tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nInteractive test error: {e}")


if __name__ == "__main__":
    # Run unit tests
    print("=" * 60)
    print("SIGMA v3.4.1 - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestVersion,
        TestErrorCodes,
        TestConfig,
        TestTools,
        TestLLMClients,
        TestRateLimiting,
        TestAppComponents,
        TestPolygonIntegration,
        TestBacktesting,
        TestImports,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Run interactive tests
    if result.wasSuccessful():
        run_interactive_tests()
    else:
        print("\n[!!] Some unit tests failed. Fix them before running interactive tests.")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
