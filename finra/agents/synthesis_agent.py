"""
Synthesis Agent — merges findings and generates the final research report.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from finra.agent.state import (
    ConvictionScores,
    MarketData,
    NewsSentiment,
    SECFilingAnalysis,
    Verdict,
)
from finra.config import settings

SYNTHESIS_PROMPT = """You are a senior financial analyst writing an investment research report. \
Synthesize the following research data into a comprehensive, well-structured report.

## Research Query
{query}

## Ticker
{ticker}

## Market Data
{market_data}

## SEC Filing Analysis
{sec_analysis}

## News & Sentiment
{news_sentiment}

## Instructions
1. Write a compelling executive summary (3-5 sentences)
2. List 3-5 strong bull points
3. List 3-5 strong bear points
4. Assign conviction scores (0-100) for each factor
5. Provide an overall verdict (Strong Buy / Buy / Moderate Buy / Hold / Moderate Sell / Sell / Strong Sell)
6. Cite all sources

Output a JSON object with:
- "executive_summary": string
- "bull_points": array of strings
- "bear_points": array of strings
- "conviction": {{"fundamentals": N, "technicals": N, "sentiment": N, "momentum": N, "valuation": N}}
- "verdict": one of [Strong Buy, Buy, Moderate Buy, Hold, Moderate Sell, Sell, Strong Sell]
- "report_markdown": full markdown report as string
- "sources": array of source strings"""


def _format_market_for_prompt(market: MarketData) -> str:
    """Format market data for the LLM prompt."""
    if not market:
        return "No market data available."
    return (
        f"Price: ${market.current_price:.2f} ({market.price_change_pct:+.2f}%)\n"
        f"Market Cap: ${market.market_cap / 1e9:.2f}B\n"
        f"P/E: {market.pe_ratio:.1f} | P/S: {market.ps_ratio:.2f} | P/B: {market.pb_ratio:.2f}\n"
        f"Revenue: ${market.revenue / 1e9:.2f}B (YoY: {market.revenue_growth:+.1f}%)\n"
        f"FCF: ${market.free_cash_flow / 1e9:.2f}B\n"
        f"Margins — Gross: {market.gross_margin * 100:.1f}% | Op: {market.operating_margin * 100:.1f}% | Net: {market.net_margin * 100:.1f}%\n"
        f"ROE: {market.roe * 100:.1f}% | D/E: {market.debt_to_equity:.1f}\n"
        f"Technicals: {json.dumps(market.technical_indicators, default=str)}"
    )


def _format_sec_for_prompt(sec: Optional[SECFilingAnalysis]) -> str:
    """Format SEC analysis for the LLM prompt."""
    if not sec:
        return "No SEC filing data available."
    parts = [f"Filing: {sec.filing_type} ({sec.filing_date})"]
    if sec.key_findings:
        parts.append("Key Findings:\n" + "\n".join(f"- {f}" for f in sec.key_findings))
    if sec.risk_factors:
        parts.append("Risk Factors:\n" + "\n".join(f"- {r[:200]}" for r in sec.risk_factors[:3]))
    if sec.management_discussion:
        parts.append(f"MD&A Excerpt: {sec.management_discussion[:1000]}...")
    return "\n".join(parts)


def _format_news_for_prompt(news: Optional[NewsSentiment]) -> str:
    """Format news sentiment for the LLM prompt."""
    if not news:
        return "No news data available."
    parts = [
        f"Overall Sentiment: {news.overall_sentiment:+.3f}",
        f"Breakdown: {news.sentiment_breakdown}",
        news.summary,
        "Top Headlines:",
    ]
    for article in news.articles[:5]:
        parts.append(f"- [{article.get('sentiment', 0):+.2f}] {article.get('title', '')}")
    return "\n".join(parts)


async def run_synthesis_agent(
    query: str,
    ticker: str,
    market_data: Optional[MarketData],
    sec_analysis: Optional[SECFilingAnalysis],
    news_sentiment: Optional[NewsSentiment],
) -> dict[str, Any]:
    """
    Run the synthesis agent to generate the final research report.

    Args:
        query: Original research query
        ticker: Stock ticker
        market_data: Market data from market agent
        sec_analysis: SEC filing analysis
        news_sentiment: News sentiment analysis

    Returns:
        Dict with report content and conviction scores
    """
    llm = ChatOpenAI(
        model=settings.llm.model,
        temperature=0.2,
        max_tokens=4096,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYNTHESIS_PROMPT),
        ("human", "Generate the investment research report."),
    ])

    chain = prompt | llm

    response = await chain.ainvoke({
        "query": query,
        "ticker": ticker,
        "market_data": _format_market_for_prompt(market_data) if market_data else "N/A",
        "sec_analysis": _format_sec_for_prompt(sec_analysis),
        "news_sentiment": _format_news_for_prompt(news_sentiment),
    })

    try:
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        result = json.loads(content)
    except (json.JSONDecodeError, IndexError):
        # Fallback: use the raw LLM output as the report
        result = {
            "executive_summary": "Report generated. See full report below.",
            "bull_points": [],
            "bear_points": [],
            "conviction": None,
            "verdict": Verdict.HOLD,
            "report_markdown": response.content,
            "sources": [],
        }

    # Parse conviction scores
    conviction = None
    if result.get("conviction"):
        c = result["conviction"]
        conviction = ConvictionScores(
            fundamentals=int(c.get("fundamentals", 50)),
            technicals=int(c.get("technicals", 50)),
            sentiment=int(c.get("sentiment", 50)),
            momentum=int(c.get("momentum", 50)),
            valuation=int(c.get("valuation", 50)),
        )
    else:
        # Compute basic conviction from available data
        conviction = _compute_basic_conviction(market_data, news_sentiment)

    # Parse verdict
    verdict = Verdict.HOLD
    if result.get("verdict"):
        try:
            verdict = Verdict(result["verdict"])
        except ValueError:
            pass
    else:
        verdict = _conviction_to_verdict(conviction)

    # Collect sources
    sources = result.get("sources", [])
    if market_data:
        sources.append(f"Yahoo Finance — {ticker} market data")
    if sec_analysis and sec_analysis.filing_date:
        sources.append(f"SEC EDGAR — {sec_analysis.filing_type} filed {sec_analysis.filing_date}")
    if news_sentiment and news_sentiment.articles:
        sources.extend([f"News: {a.get('title', '')}" for a in news_sentiment.articles[:3]])

    return {
        "executive_summary": result.get("executive_summary", ""),
        "bull_points": result.get("bull_points", []),
        "bear_points": result.get("bear_points", []),
        "conviction": conviction,
        "verdict": verdict,
        "report_markdown": result.get("report_markdown", ""),
        "sources": list(set(sources)),
    }


def _compute_basic_conviction(
    market: Optional[MarketData],
    news: Optional[NewsSentiment],
) -> ConvictionScores:
    """Compute basic conviction scores from raw data without LLM."""
    scores = ConvictionScores()

    if market:
        # Fundamentals based on margins and growth
        scores.fundamentals = min(100, max(
            50,
            50 + (market.roe * 100 if market.roe else 0) * 0.3
            + (market.revenue_growth * 0.5 if market.revenue_growth else 0)
            - (abs(market.debt_to_equity) * 0.1 if market.debt_to_equity else 0)
        ))

        # Valuation based on P/E
        scores.valuation = min(100, max(
            0, 100 - max(0, (market.pe_ratio - 15) * 2) if market.pe_ratio else 50
        ))

        # Technicals based on indicators
        ti = market.technical_indicators
        if ti:
            rsi = ti.get("rsi_14", 50)
            if 30 <= rsi <= 70:
                scores.technicals = 60
            elif rsi < 30:
                scores.technicals = 75  # Oversold = opportunity
            else:
                scores.technicals = 35  # Overbought
            trend = ti.get("trend", "neutral")
            if trend == "bullish":
                scores.technicals = min(100, scores.technicals + 15)
            elif trend == "bearish":
                scores.technicals = max(0, scores.technicals - 15)

        # Momentum from price change
        scores.momentum = min(100, max(
            0, 50 + market.price_change_pct * 2
        ))

    if news:
        # Sentiment score mapped to 0-100
        scores.sentiment = int((news.overall_sentiment + 1) * 50)

    # Clamp all values
    scores.fundamentals = max(0, min(100, scores.fundamentals))
    scores.technicals = max(0, min(100, scores.technicals))
    scores.sentiment = max(0, min(100, scores.sentiment))
    scores.momentum = max(0, min(100, scores.momentum))
    scores.valuation = max(0, min(100, scores.valuation))

    return scores


def _conviction_to_verdict(conviction: ConvictionScores) -> Verdict:
    """Convert overall conviction score to a verdict."""
    overall = conviction.overall
    if overall >= 80:
        return Verdict.STRONG_BUY
    elif overall >= 68:
        return Verdict.BUY
    elif overall >= 55:
        return Verdict.MODERATE_BUY
    elif overall >= 45:
        return Verdict.HOLD
    elif overall >= 35:
        return Verdict.MODERATE_SELL
    elif overall >= 22:
        return Verdict.SELL
    else:
        return Verdict.STRONG_SELL
