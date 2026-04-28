"""
Shared state definitions for the multi-agent pipeline.

Uses LangGraph's typed state to pass data between agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ResearchDepth(str, Enum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class Verdict(str, Enum):
    STRONG_BUY = "Strong Buy"
    BUY = "Buy"
    MODERATE_BUY = "Moderate Buy"
    HOLD = "Hold"
    MODERATE_SELL = "Moderate Sell"
    SELL = "Sell"
    STRONG_SELL = "Strong Sell"


@dataclass
class MarketData:
    """Market data collected by the market agent."""

    ticker: str = ""
    current_price: float = 0.0
    price_change_pct: float = 0.0
    market_cap: float = 0.0
    pe_ratio: float = 0.0
    ps_ratio: float = 0.0
    pb_ratio: float = 0.0
    dividend_yield: float = 0.0
    revenue: float = 0.0
    revenue_growth: float = 0.0
    net_income: float = 0.0
    free_cash_flow: float = 0.0
    debt_to_equity: float = 0.0
    roe: float = 0.0
    gross_margin: float = 0.0
    operating_margin: float = 0.0
    net_margin: float = 0.0
    technical_indicators: dict[str, Any] = field(default_factory=dict)
    price_history: list[dict[str, Any]] = field(default_factory=list)
    analyst_recommendations: dict[str, Any] = field(default_factory=dict)


@dataclass
class SECFilingAnalysis:
    """Analysis results from SEC filings."""

    filing_type: str = ""
    filing_date: str = ""
    fiscal_year: int = 0
    sections_analyzed: list[str] = field(default_factory=list)
    key_findings: list[str] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)
    segment_data: dict[str, Any] = field(default_factory=dict)
    management_discussion: str = ""
    raw_text_chunks: list[str] = field(default_factory=list)


@dataclass
class NewsSentiment:
    """News sentiment analysis results."""

    articles: list[dict[str, Any]] = field(default_factory=list)
    overall_sentiment: float = 0.0  # -1.0 to 1.0
    sentiment_breakdown: dict[str, int] = field(default_factory=dict)
    key_topics: list[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class ConvictionScores:
    """Multi-factor conviction scoring."""

    fundamentals: int = 0  # 0-100
    technicals: int = 0  # 0-100
    sentiment: int = 0  # 0-100
    momentum: int = 0  # 0-100
    valuation: int = 0  # 0-100

    @property
    def overall(self) -> int:
        return (
            self.fundamentals * 0.30
            + self.technicals * 0.20
            + self.sentiment * 0.20
            + self.momentum * 0.15
            + self.valuation * 0.15
        )


class AgentState(dict):
    """
    LangGraph state that flows through the multi-agent pipeline.
    All keys are typed for clarity; agents read/write to this shared state.
    """

    # Input
    query: str = ""
    ticker: str = ""
    depth: ResearchDepth = ResearchDepth.STANDARD

    # Planning
    research_plan: list[str] = field(default_factory=list)  # type: ignore
    required_sources: list[str] = field(default_factory=list)  # type: ignore

    # Agent outputs
    market_data: Optional[MarketData] = None
    sec_analysis: Optional[SECFilingAnalysis] = None
    news_sentiment: Optional[NewsSentiment] = None

    # Synthesis
    bull_points: list[str] = field(default_factory=list)  # type: ignore
    bear_points: list[str] = field(default_factory=list)  # type: ignore
    executive_summary: str = ""
    conviction: Optional[ConvictionScores] = None
    verdict: Verdict = Verdict.HOLD
    report_markdown: str = ""
    sources: list[str] = field(default_factory=list)  # type: ignore

    # Metadata
    started_at: str = ""
    completed_at: str = ""
    errors: list[str] = field(default_factory=list)  # type: ignore
    iteration: int = 0
