"""
Report Generator — builds structured research reports.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from finra.agent.state import (
    ConvictionScores,
    MarketData,
    NewsSentiment,
    SECFilingAnalysis,
    Verdict,
)
from finra.report.templates import REPORT_TEMPLATE, format_metrics_table


class ResearchReport:
    """
    Represents a generated investment research report.

    Usage:
        report = ResearchReport.from_agent_result(agent_output)
        print(report.markdown())
        report.save("reports/aapl.md")
    """

    def __init__(
        self,
        ticker: str,
        query: str,
        executive_summary: str = "",
        bull_points: Optional[list[str]] = None,
        bear_points: Optional[list[str]] = None,
        conviction: Optional[ConvictionScores] = None,
        verdict: Verdict = Verdict.HOLD,
        market_data: Optional[MarketData] = None,
        sec_analysis: Optional[SECFilingAnalysis] = None,
        news_sentiment: Optional[NewsSentiment] = None,
        sources: Optional[list[str]] = None,
    ):
        self.ticker = ticker
        self.query = query
        self.executive_summary = executive_summary
        self.bull_points = bull_points or []
        self.bear_points = bear_points or []
        self.conviction = conviction
        self.verdict = verdict
        self.market_data = market_data
        self.sec_analysis = sec_analysis
        self.news_sentiment = news_sentiment
        self.sources = sources or []
        self.generated_at = datetime.now().isoformat()

    @classmethod
    def from_agent_result(cls, result: dict[str, Any]) -> "ResearchReport":
        """Create a report from the agent pipeline output."""
        return cls(
            ticker=result.get("ticker", ""),
            query=result.get("query", ""),
            executive_summary=result.get("executive_summary", ""),
            bull_points=result.get("bull_points", []),
            bear_points=result.get("bear_points", []),
            conviction=result.get("conviction"),
            verdict=result.get("verdict", Verdict.HOLD),
            market_data=result.get("market_data"),
            sec_analysis=result.get("sec_analysis"),
            news_sentiment=result.get("news_sentiment"),
            sources=result.get("sources", []),
        )

    @property
    def conviction_score(self) -> int:
        """Overall conviction score (0-100)."""
        if self.conviction:
            return int(self.conviction.overall)
        return 50

    def markdown(self) -> str:
        """Generate the full Markdown report."""
        report_md = result.get("report_markdown", "") if hasattr(self, "report_markdown") else ""
        if report_md:
            return report_md

        # Build the report from components
        sections = []

        # Header
        sections.append(f"# Investment Research Report: {self.ticker}\n")
        sections.append(f"**Query:** {self.query}")
        sections.append(f"**Generated:** {self.generated_at}\n")

        # Verdict banner
        emoji = {
            Verdict.STRONG_BUY: "🟢🟢",
            Verdict.BUY: "🟢",
            Verdict.MODERATE_BUY: "🟡🟢",
            Verdict.HOLD: "🟡",
            Verdict.MODERATE_SELL: "🟡🔴",
            Verdict.SELL: "🔴",
            Verdict.STRONG_SELL: "🔴🔴",
        }.get(self.verdict, "⚪")

        sections.append(f"## Verdict: {emoji} {self.verdict.value}")
        sections.append(f"**Conviction Score: {self.conviction_score}/100**\n")

        # Executive Summary
        if self.executive_summary:
            sections.append("## Executive Summary\n")
            sections.append(self.executive_summary)
            sections.append("")

        # Conviction Breakdown
        if self.conviction:
            sections.append("## Conviction Breakdown\n")
            sections.append("| Factor | Score | Weight | Contribution |")
            sections.append("|--------|-------|--------|-------------|")
            factors = [
                ("Fundamentals", self.conviction.fundamentals, "30%"),
                ("Technicals", self.conviction.technicals, "20%"),
                ("Sentiment", self.conviction.sentiment, "20%"),
                ("Momentum", self.conviction.momentum, "15%"),
                ("Valuation", self.conviction.valuation, "15%"),
            ]
            for name, score, weight in factors:
                bar = "█" * (score // 5) + "░" * (20 - score // 5)
                sections.append(f"| {name} | {score}/100 ({bar}) | {weight} | {score * float(weight.strip('%')) / 100:.0f} |")
            sections.append(f"| **Overall** | **{self.conviction_score}/100** | **100%** | **—** |")
            sections.append("")

        # Key Metrics
        if self.market_data:
            sections.append("## Key Metrics\n")
            sections.append(format_metrics_table(self.market_data))
            sections.append("")

        # Technical Indicators
        if self.market_data and self.market_data.technical_indicators:
            ti = self.market_data.technical_indicators
            sections.append("## Technical Analysis\n")
            sections.append(f"- **RSI (14):** {ti.get('rsi_14', 'N/A')} ({ti.get('trend', 'neutral')})")
            sections.append(f"- **SMA 20/50/200:** ${ti.get('sma_20', 0):.2f} / ${ti.get('sma_50', 0):.2f} / ${ti.get('sma_200', 0):.2f}")
            sections.append(f"- **Volatility:** {ti.get('volatility_annualized', 0) * 100:.1f}% annualized")
            sections.append(f"- **52-Week Range:** ${ti.get('low_52w', 0):.2f} – ${ti.get('high_52w', 0):.2f}")
            sections.append("")

        # Bull Case
        if self.bull_points:
            sections.append("## 🐂 Bull Case\n")
            for point in self.bull_points:
                sections.append(f"- {point}")
            sections.append("")

        # Bear Case
        if self.bear_points:
            sections.append("## 🐻 Bear Case\n")
            for point in self.bear_points:
                sections.append(f"- {point}")
            sections.append("")

        # News Sentiment
        if self.news_sentiment:
            sections.append("## News & Sentiment\n")
            sections.append(f"Overall Sentiment: **{self.news_sentiment.overall_sentiment:+.3f}**")
            sections.append(f"{self.news_sentiment.sentiment_breakdown}")
            sections.append("")
            sections.append(self.news_sentiment.summary)
            sections.append("")

        # Sources
        if self.sources:
            sections.append("## Sources\n")
            for i, source in enumerate(self.sources, 1):
                sections.append(f"{i}. {source}")
            sections.append("")

        # Footer
        sections.append("---")
        sections.append("*This report was generated by Financial Research Agent (FinRA). Not financial advice.*")

        return "\n".join(sections)

    def save(self, filepath: str) -> str:
        """Save the report to a file."""
        from pathlib import Path

        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.markdown(), encoding="utf-8")
        return str(path)

    def to_dict(self) -> dict[str, Any]:
        """Convert report to a dictionary."""
        return {
            "ticker": self.ticker,
            "query": self.query,
            "verdict": self.verdict.value if self.verdict else "N/A",
            "conviction_score": self.conviction_score,
            "conviction_breakdown": {
                "fundamentals": self.conviction.fundamentals if self.conviction else None,
                "technicals": self.conviction.technicals if self.conviction else None,
                "sentiment": self.conviction.sentiment if self.conviction else None,
                "momentum": self.conviction.momentum if self.conviction else None,
                "valuation": self.conviction.valuation if self.conviction else None,
            },
            "executive_summary": self.executive_summary,
            "bull_points": self.bull_points,
            "bear_points": self.bear_points,
            "sources": self.sources,
            "generated_at": self.generated_at,
            "markdown": self.markdown(),
        }
