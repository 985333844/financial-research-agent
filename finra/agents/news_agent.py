"""
News & Sentiment Agent — fetches news and analyzes sentiment.
"""

from __future__ import annotations

from typing import Any, Optional

from finra.agent.state import NewsSentiment
from finra.tools.news import analyze_sentiment, search_news


async def run_news_agent(ticker: str) -> NewsSentiment:
    """
    Run the news sentiment agent.

    Fetches recent news and analyzes overall sentiment for the given ticker.

    Args:
        ticker: Stock ticker symbol

    Returns:
        NewsSentiment object with articles and analysis
    """
    # Search for news
    articles = await search_news(ticker, max_articles=10)

    # Analyze sentiment
    sentiment_analysis = analyze_sentiment(articles)

    return NewsSentiment(
        articles=articles,
        overall_sentiment=sentiment_analysis["overall_sentiment"],
        sentiment_breakdown=sentiment_analysis["sentiment_breakdown"],
        key_topics=sentiment_analysis["key_topics"],
        summary=sentiment_analysis["summary"],
    )


def _format_news_summary(sentiment: NewsSentiment) -> str:
    """Format news sentiment into a readable summary."""
    lines = [
        "## News & Sentiment Analysis",
        "",
        f"Overall Sentiment: {sentiment.overall_sentiment:+.3f}",
        f"Breakdown: {sentiment.sentiment_breakdown}",
        "",
        sentiment.summary,
        "",
    ]

    if sentiment.key_topics:
        lines.append("### Key Topics")
        lines.append(", ".join(sentiment.key_topics))
        lines.append("")

    if sentiment.articles:
        lines.append("### Recent Headlines")
        for i, article in enumerate(sentiment.articles[:5], 1):
            sent_emoji = "🟢" if article.get("sentiment", 0) > 0.1 else "🔴" if article.get("sentiment", 0) < -0.1 else "⚪"
            lines.append(f"{i}. {sent_emoji} {article.get('title', 'Untitled')}")
            lines.append(f"   Source: {article.get('source', 'Unknown')} | Sentiment: {article.get('sentiment', 0):+.2f}")
            if article.get("url"):
                lines.append(f"   {article['url']}")

    return "\n".join(lines)
