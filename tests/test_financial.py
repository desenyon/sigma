"""Tests for Sigma financial tools."""

import pytest
from sigma.tools.financial import (
    get_stock_quote,
    get_company_info,
    get_stock_history,
    get_analyst_recommendations,
    technical_analysis,
    compare_stocks,
)


class TestFinancialTools:
    """Test financial data tools."""
    
    def test_get_stock_quote(self):
        """Test getting stock quote."""
        result = get_stock_quote("AAPL")
        assert "symbol" in result
        assert result["symbol"] == "AAPL"
        assert "price" in result
        assert result.get("price") is not None
    
    def test_get_company_info(self):
        """Test getting company info."""
        result = get_company_info("MSFT")
        assert "symbol" in result
        assert result["symbol"] == "MSFT"
        assert "name" in result
    
    def test_get_stock_history(self):
        """Test getting stock history."""
        result = get_stock_history("GOOGL", period="1mo")
        assert "symbol" in result
        assert "history" in result
        assert len(result.get("history", [])) > 0
    
    def test_get_analyst_recommendations(self):
        """Test getting analyst recommendations."""
        result = get_analyst_recommendations("NVDA")
        assert "symbol" in result
        assert result["symbol"] == "NVDA"
    
    def test_technical_analysis(self):
        """Test technical analysis."""
        result = technical_analysis("TSLA")
        assert "symbol" in result
        assert "sma_20" in result
        assert "rsi" in result
        assert "signals" in result
    
    def test_compare_stocks(self):
        """Test comparing stocks."""
        result = compare_stocks(["AAPL", "MSFT", "GOOGL"])
        assert "comparison" in result
        assert len(result["comparison"]) == 3
