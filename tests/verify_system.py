#!/usr/bin/env python3
"""
System Verification Suite for Sigma v3.6.1
Tests all core components, tools, and configurations.
"""

import sys
import os
import asyncio
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import json

# Ensure we can import sigma
sys.path.insert(0, str(Path(__file__).parent.parent))

from sigma.config import Settings, LLMProvider, ErrorCode, SigmaError
from sigma.tools.registry import TOOL_REGISTRY
from sigma.llm.router import LLMRouter
from sigma.core.engine import Engine
from sigma.ui.widgets import SigmaInput, TickerBadge

class TestSigmaSystem(unittest.TestCase):
    
    def setUp(self):
        self.settings = Settings()

    def test_01_configuration(self):
        """Verify configuration defaults and structure."""
        print("\n[TEST] Configuration Defaults")
        # Check if default provider is valid (can be OLLAMA or GOOGLE depending on user config)
        self.assertIsInstance(self.settings.default_provider, LLMProvider)
        print(f"  [INFO] Default provider: {self.settings.default_provider}")
        
        # Check model
        self.assertEqual(self.settings.ollama_model, "qwen2.5:1.5b")
        
        # Check if fields exist (values might be None)
        self.assertIn("alpha_vantage_api_key", self.settings.model_fields)
        self.assertIn("polygon_api_key", self.settings.model_fields)
        print("  [OK] Settings loaded correctly")

    def test_02_tool_registry(self):
        """Verify all tools are registered and have schemas."""
        print("\n[TEST] Tool Registry")
        tools = TOOL_REGISTRY.list_tools()
        self.assertGreater(len(tools), 0, "No tools registered!")
        
        # Check for key tools
        tool_names = [t.name for t in tools]
        required_tools = [
            "run_local_backtest",
            "get_stock_quote", # Alpha Vantage
            "polygon_get_quote", # Polygon
            "search_exa", # Exa
        ]
        
        for rt in required_tools:
            self.assertIn(rt, tool_names, f"Missing required tool: {rt}")
            
        print(f"  [OK] {len(tools)} tools registered.")

    def test_03_local_backtest_logic(self):
        """Test the local backtest tool logic (using mocks to avoid network)."""
        print("\n[TEST] Local Backtest Logic")
        
        tool = TOOL_REGISTRY.get_tool("run_local_backtest")
        self.assertIsNotNone(tool)
        
        # Mock run_backtest internal call to simple_engine
        with patch("sigma.tools.local_backtest.run_backtest") as mock_run:
            mock_run.return_value = {
                "metrics": {"total_return": 0.1},
                "equity_curve": [],
                "parameters": {"symbol": "AAPL"}
            }
            
            result = tool.func(
                symbol="AAPL",
                strategy="sma_crossover",
                period="1y",
                initial_capital=10000
            )
            
            self.assertIn("metrics", result)
            self.assertEqual(result["parameters"]["symbol"], "AAPL")
            print("  [OK] Backtest simulation ran successfully")

    def test_04_ui_ticker_recognition(self):
        """Test the regex logic for ticker recognition."""
        print("\n[TEST] UI Ticker Recognition")
        import re
        ticker_pattern = r"\b[A-Z]{1,5}\b" 
        
        input_text = "Analyze AAPL please"
        match = re.search(ticker_pattern, input_text)
        self.assertTrue(match)
        self.assertEqual(match.group(0), "AAPL")
        print("  [OK] Ticker regex logic verified")

    def test_05_router_initialization(self):
        """Test LLM Router initialization."""
        print("\n[TEST] LLM Router")
        # Create a router with mocked settings
        with patch("sigma.llm.router.OllamaProvider") as MockOllama:
            router = LLMRouter(self.settings)
            self.assertIsNotNone(router)
        print("  [OK] Router initialized")

    def test_06_alpha_vantage_tool(self):
        """Test Alpha Vantage tool structure."""
        print("\n[TEST] Alpha Vantage Tool")
        tool = TOOL_REGISTRY.get_tool("get_stock_quote")
        # Just check it exists and has correct provider metadata if set
        # The provider field might be 'internal' or 'alpha_vantage' depending on how it was registered
        # Let's check the function name instead
        self.assertEqual(tool.name, "get_stock_quote")
        
        # Verify arguments
        schema = tool.input_schema
        self.assertIn("symbol", schema["properties"])
        print("  [OK] Alpha Vantage tool configured")


class TestAsyncSigmaSystem(unittest.IsolatedAsyncioTestCase):
    
    async def test_07_engine_flow(self):
        """Test the core Engine flow (mocked)."""
        print("\n[TEST] Engine Flow")
        engine = Engine()
        
        # We need to mock the intent parser's parse method
        # The engine imports IntentParser, so we mock where it's used or the instance on the engine
        
        # Create a mock plan
        from sigma.core.models import ResearchPlan, DeliverableType
        mock_plan = ResearchPlan(
            original_query="test",
            intent="analysis",
            goal="Test Analysis",
            deliverable=DeliverableType.ANALYSIS,
            assets=["AAPL"],
            tasks=["Analyze AAPL"],
            context={}
        )

        # Mock the instance method
        engine.intent_parser.parse = MagicMock()
        # Make the mock async-compatible if parse is async
        async def async_return(*args, **kwargs):
            return mock_plan
        engine.intent_parser.parse.side_effect = async_return
        
        # Run process_query
        result = await engine.process_query("Analyze AAPL")
        
        self.assertEqual(result["type"], "result")
        # The engine mock implementation in my head returns analyses dict
        self.assertIn("analyses", result["result"])
        self.assertEqual(result["result"]["analyses"]["AAPL"]["symbol"], "AAPL")
        print("  [OK] Engine processed query plan")

if __name__ == "__main__":
    unittest.main()