
import asyncio
import unittest
import os
from typing import Dict, Any
from unittest.mock import patch, MagicMock
from sigma.core.engine import Engine
from sigma.core.models import ResearchPlan, DeliverableType
from sigma.tools.registry import TOOL_REGISTRY

# Ensure required API keys are present (or mocked)
# For this test scenario, we'll mock the actual API calls to avoid cost/flakiness,
# but verify the logic flow and tool selection.

class TestRealWorldScenarios(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self):
        self.engine = Engine()
        # Mock settings to ensure providers are available
        with patch("sigma.config.get_settings") as mock_settings:
            mock_settings.return_value.default_provider = "ollama"
            mock_settings.return_value.alpha_vantage_api_key = "test"
            
    async def test_scenario_1_simple_analysis(self):
        """
        Scenario 1: User asks for a simple analysis of a single stock.
        Query: "Analyze AAPL's recent performance"
        Expected: 
        - Intent: Analysis
        - Assets: ['AAPL']
        - Tools Triggered: get_stock_quote, maybe get_stock_history
        """
        print("\n[SCENARIO] 1: Simple Analysis (AAPL)")
        
        # 1. Simulate Intent Parsing (Mocking the LLM parser for determinism)
        mock_plan = ResearchPlan(
            original_query="Analyze AAPL's recent performance",
            intent="analysis",
            goal="Analyze AAPL performance",
            deliverable=DeliverableType.ANALYSIS,
            assets=["AAPL"],
            tasks=["Fetch AAPL quote", "Fetch AAPL history", "Summarize"],
            context={}
        )
        
        # 2. Mock the _route_deliverable part or the tools directly
        # We want to see if the engine calls the right tools if we were to execute it.
        # Since Engine._handle_analysis is currently a stub in the codebase (returning mock results),
        # we will verify the structure it returns.
        
        result = await self.engine._handle_analysis(mock_plan)
        
        # 3. Assertions
        self.assertIn("analyses", result)
        self.assertIn("AAPL", result["analyses"])
        self.assertEqual(result["analyses"]["AAPL"]["symbol"], "AAPL")
        print("  [PASS] Analysis structure correct")

    async def test_scenario_2_comparison(self):
        """
        Scenario 2: User compares two competitors.
        Query: "Compare NVDA and AMD"
        Expected:
        - Intent: Comparison
        - Assets: ['NVDA', 'AMD']
        - Result: Comparison structure
        """
        print("\n[SCENARIO] 2: Comparison (NVDA vs AMD)")
        
        mock_plan = ResearchPlan(
            original_query="Compare NVDA and AMD",
            intent="comparison",
            goal="Compare NVDA and AMD",
            deliverable=DeliverableType.COMPARISON,
            assets=["NVDA", "AMD"],
            tasks=["Fetch NVDA data", "Fetch AMD data", "Compare metrics"],
            context={}
        )
        
        result = await self.engine._handle_comparison(mock_plan)
        
        self.assertEqual(result["comparison_type"], "multi_asset")
        self.assertEqual(len(result["assets"]), 2)
        self.assertIn("NVDA", result["assets"])
        self.assertIn("AMD", result["assets"])
        print("  [PASS] Comparison structure correct")

    async def test_scenario_3_tool_execution(self):
        """
        Scenario 3: Execute a real tool via the registry (Mocked Network).
        Query: Implicitly testing 'get_stock_quote'
        """
        print("\n[SCENARIO] 3: Tool Execution (get_stock_quote)")
        
        tool = TOOL_REGISTRY.get_tool("get_stock_quote")
        self.assertIsNotNone(tool, "Tool 'get_stock_quote' not found")
        
        # Mock yfinance inside the tool
        with patch("yfinance.Ticker") as mock_ticker:
            mock_instance = mock_ticker.return_value
            mock_instance.info = {
                "shortName": "Apple Inc.",
                "regularMarketPrice": 150.0,
                "regularMarketChangePercent": 0.01
            }
            
            result = tool.func(symbol="AAPL")
            
            self.assertEqual(result["symbol"], "AAPL")
            self.assertEqual(result["price"], 150.0)
            self.assertEqual(result["name"], "Apple Inc.")
            print("  [PASS] Tool execution (Mocked) successful")

    async def test_scenario_4_search_tool(self):
        """
        Scenario 4: Research using Exa search.
        """
        print("\n[SCENARIO] 4: Search Tool (Exa)")
        
        tool = TOOL_REGISTRY.get_tool("search_exa")
        self.assertIsNotNone(tool, "Tool 'search_exa' not found")
        
        # Mock httpx for Exa
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [
                    {"title": "Market News 1", "url": "http://example.com/1"},
                    {"title": "Market News 2", "url": "http://example.com/2"}
                ]
            }
            mock_post.return_value = mock_response
            
            # Since the tool is async, we await it
            # Note: The tool registry might wrap it, but let's call the func directly if it's the raw func
            # Check if tool.func is a coroutine
            if asyncio.iscoroutinefunction(tool.func):
                result = await tool.func(query="latest tech news")
            else:
                result = tool.func(query="latest tech news")
            
            self.assertIn("results", result)
            self.assertEqual(len(result["results"]), 2)
            print("  [PASS] Search tool execution (Mocked) successful")

if __name__ == "__main__":
    unittest.main()
