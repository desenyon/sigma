"""Sigma Research Agent."""

import asyncio
import time
from datetime import datetime
from typing import Any, Callable, Optional

from sigma.core.config import LLMProvider, get_settings
from sigma.core.llm import get_llm, BaseLLM
from sigma.core.models import Message, MessageRole, ToolCall, ToolResult
from sigma.tools.financial import get_all_tools, execute_tool


SYSTEM_PROMPT = """You are Sigma, an elite quantitative financial research analyst and AI-powered trading strategist. You have institutional-grade expertise in markets, securities analysis, algorithmic trading, and investment research.

CRITICAL CONSTRAINT: You ONLY respond to finance, investing, trading, and market-related queries.
- If a user asks about non-financial topics, politely redirect them to financial topics
- Example: "I specialize in financial analysis. I can help you with stock analysis, market research, portfolio optimization, or trading strategies. What financial topic would you like to explore?"

Your capabilities include:

MARKET DATA & ANALYSIS
- Real-time stock quotes and market data
- Historical price analysis and charting
- Sector performance and market indices
- Options chain analysis

TECHNICAL ANALYSIS
- Price charts (line, candle, area)
- Moving averages (SMA, EMA)
- RSI, MACD, Bollinger Bands
- Support/resistance levels
- Technical signals and patterns

FUNDAMENTAL ANALYSIS
- Financial statements (income, balance sheet, cash flow)
- Valuation metrics (P/E, P/B, PEG, EV/EBITDA)
- Earnings and revenue analysis
- Profitability ratios (ROE, ROA, margins)

PREDICTIONS & FORECASTING
- Price predictions using multiple models
- Sentiment analysis
- Risk assessment
- Monte Carlo simulations

INSTITUTIONAL FEATURES
- Analyst recommendations and price targets
- Insider trading activity
- Institutional holdings
- Short interest data

ALGORITHMIC TRADING
- Generate LEAN engine backtests
- Strategy templates (SMA crossover, RSI mean reversion, MACD momentum, etc.)
- Custom strategy builder
- Backtest parameter optimization

When answering:
1. ALWAYS use tools to get real, current data - never make up numbers
2. Provide specific metrics and data points
3. Present analysis in clear, structured formats
4. Include risk factors and caveats
5. Give actionable insights with reasoning
6. Use charts when visualizing would help
7. Compare to benchmarks and peers when relevant

For comprehensive analysis, use multiple tools:
1. get_stock_quote → Current price and key metrics
2. get_company_info → Business context and fundamentals
3. get_analyst_recommendations → Wall Street sentiment
4. technical_analysis → Price action and signals
5. get_financial_statements → Deep fundamental analysis
6. sentiment_analysis → Multi-factor sentiment
7. price_forecast → Forward-looking projections

For charts and visualization:
- generate_price_chart → Beautiful terminal price charts
- generate_comparison_chart → Compare multiple stocks
- generate_rsi_chart → Price with RSI indicator
- generate_sector_chart → Sector performance overview

For backtesting and strategy:
- list_backtest_strategies → Available strategies
- generate_backtest → Create LEAN algorithm
- generate_custom_backtest → Custom strategy builder

Your analysis should match the quality of Goldman Sachs, Morgan Stanley, and Citadel research."""


class SigmaAgent:
    """Financial research agent."""
    
    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
    ):
        self.settings = get_settings()
        self.provider = provider or self.settings.default_provider
        self.llm: BaseLLM = get_llm(self.provider, model)
        self.messages: list[Message] = []
        self.tools = get_all_tools()
        self.tool_results: list[ToolResult] = []
        self._reset()
    
    def _reset(self):
        """Reset conversation."""
        self.messages = [
            Message(role=MessageRole.SYSTEM, content=SYSTEM_PROMPT)
        ]
        self.tool_results = []
    
    async def run(
        self,
        query: str,
        on_tool_start: Optional[Callable[[str, dict], None]] = None,
        on_tool_end: Optional[Callable[[str, Any, float], None]] = None,
        on_thinking: Optional[Callable[[str], None]] = None,
        on_response: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Run the agent on a query."""
        self.messages.append(Message(role=MessageRole.USER, content=query))
        self.tool_results = []
        
        iteration = 0
        start_time = time.time()
        
        while iteration < self.settings.max_iterations:
            iteration += 1
            
            # Get LLM response
            try:
                content, tool_calls = await self.llm.generate(
                    messages=self.messages,
                    tools=self.tools,
                )
            except Exception as e:
                return f"Error: {str(e)}"
            
            # If no tool calls, we're done
            if not tool_calls:
                if content:
                    self.messages.append(Message(role=MessageRole.ASSISTANT, content=content))
                    if on_response:
                        on_response(content)
                    return content
                continue
            
            # Record assistant message with tool calls
            self.messages.append(Message(
                role=MessageRole.ASSISTANT,
                content=content,
                tool_calls=tool_calls,
            ))
            
            if on_thinking and content:
                on_thinking(content)
            
            # Execute tools
            for tc in tool_calls:
                tool_start = time.time()
                
                if on_tool_start:
                    on_tool_start(tc.name, tc.arguments)
                
                result = await execute_tool(tc.name, tc.arguments)
                
                duration_ms = (time.time() - tool_start) * 1000
                
                tool_result = ToolResult(
                    tool_name=tc.name,
                    tool_call_id=tc.id,
                    success="error" not in str(result).lower(),
                    result=result,
                    duration_ms=duration_ms,
                )
                self.tool_results.append(tool_result)
                
                if on_tool_end:
                    on_tool_end(tc.name, result, duration_ms)
                
                # Add tool result message
                self.messages.append(Message(
                    role=MessageRole.TOOL,
                    content=str(result),
                    tool_call_id=tc.id,
                    name=tc.name,
                ))
        
        return "Max iterations reached. Please try a simpler query."
    
    def get_stats(self) -> dict[str, Any]:
        """Get execution statistics."""
        total_time = sum(r.duration_ms for r in self.tool_results)
        return {
            "tools_called": len(self.tool_results),
            "total_time_ms": total_time,
            "successful": sum(1 for r in self.tool_results if r.success),
            "failed": sum(1 for r in self.tool_results if not r.success),
        }
    
    def clear(self):
        """Clear conversation history."""
        self._reset()
