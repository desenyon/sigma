"""Data models for Sigma."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Message roles."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCall(BaseModel):
    """Tool call."""
    id: str
    name: str
    arguments: dict[str, Any]


class Message(BaseModel):
    """Chat message."""
    role: MessageRole
    content: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ToolResult(BaseModel):
    """Tool execution result."""
    tool_name: str
    tool_call_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    duration_ms: float = 0.0
    
    @property
    def display_result(self) -> str:
        """Get result for display."""
        if self.error:
            return f"Error: {self.error}"
        if isinstance(self.result, dict):
            return str(self.result)
        return str(self.result) if self.result else "No result"


class AgentStep(BaseModel):
    """Agent execution step."""
    step_number: int
    action: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_results: list[ToolResult] = Field(default_factory=list)
    reasoning: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class FinancialMetric(BaseModel):
    """Financial metric."""
    name: str
    value: float | str | None
    unit: Optional[str] = None
    period: Optional[str] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None


class StockSnapshot(BaseModel):
    """Stock market snapshot."""
    symbol: str
    company_name: str
    price: float
    change: float
    change_pct: float
    volume: int
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    avg_volume: Optional[int] = None
    beta: Optional[float] = None
    eps: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class FinancialStatement(BaseModel):
    """Financial statement data."""
    symbol: str
    statement_type: str  # income, balance, cash_flow
    period: str  # annual, quarterly
    date: str
    metrics: dict[str, float | None]


class EarningsData(BaseModel):
    """Earnings data."""
    symbol: str
    date: str
    eps_estimate: Optional[float] = None
    eps_actual: Optional[float] = None
    revenue_estimate: Optional[float] = None
    revenue_actual: Optional[float] = None
    surprise_pct: Optional[float] = None


class InsiderTrade(BaseModel):
    """Insider trading data."""
    symbol: str
    insider_name: str
    title: str
    transaction_type: str
    shares: int
    price: Optional[float] = None
    value: Optional[float] = None
    date: str


class AnalystRating(BaseModel):
    """Analyst rating."""
    symbol: str
    firm: str
    analyst: Optional[str] = None
    rating: str
    price_target: Optional[float] = None
    date: str


class NewsItem(BaseModel):
    """News item."""
    title: str
    source: str
    url: str
    published: datetime
    summary: Optional[str] = None
    sentiment: Optional[str] = None


class ResearchReport(BaseModel):
    """Research report."""
    title: str
    summary: str
    sections: list[dict[str, Any]]
    data_sources: list[str]
    symbols_analyzed: list[str]
    generated_at: datetime = Field(default_factory=datetime.now)
    confidence: float = 0.0
