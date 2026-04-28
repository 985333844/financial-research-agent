"""
News Tool — fetches financial news and analyzes sentiment.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup

from finra.config import settings


async def search_news(
    ticker: str,
    query: Optional[str] = None,
    max_articles: int = 10,
) -> list[dict[str, Any]]:
    """
    Search for recent news about a company.

    Uses multiple sources:
    1. Tavily API (if key available)
    2. Yahoo Finance RSS (fallback)

    Args:
        ticker: Stock ticker symbol
        query: Optional search query override
        max_articles: Maximum number of articles to return

    Returns:
        List of article dicts with title, content, sentiment, etc.
    """
    articles = []

    # Try Tavily first
    if settings.data_sources.tavily_api_key:
        try:
            tavily_articles = await _search_tavily(ticker, query, max_articles)
            articles.extend(tavily_articles)
        except Exception:
            pass

    # Fallback to Yahoo Finance RSS
    if len(articles) < max_articles:
        try:
            yahoo_articles = await _search_yahoo_finance(ticker, max_articles - len(articles))
            articles.extend(yahoo_articles)
        except Exception:
            pass

    # Add sentiment to each article
    for article in articles:
        article["sentiment"] = _quick_sentiment(article.get("title", "") + " " + article.get("snippet", ""))

    return articles[:max_articles]


async def _search_tavily(
    ticker: str,
    query: Optional[str],
    max_articles: int,
) -> list[dict[str, Any]]:
    """Search using the Tavily API."""
    search_query = query or f"{ticker} stock news analysis"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.data_sources.tavily_api_key}",
    }

    payload = {
        "query": search_query,
        "max_results": max_articles,
        "include_answer": False,
        "topic": "finance",
        "days": 7,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.tavily.com/search",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()

    data = resp.json()
    articles = []
    for result in data.get("results", []):
        articles.append({
            "title": result.get("title", ""),
            "url": result.get("url", ""),
            "snippet": result.get("content", "")[:500],
            "source": result.get("source", ""),
            "published_date": result.get("published_date", ""),
        })

    return articles


async def _search_yahoo_finance(
    ticker: str,
    max_articles: int,
) -> list[dict[str, Any]]:
    """Scrape news from Yahoo Finance."""
    url = f"https://finance.yahoo.com/quote/{ticker}/news/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    articles = []

    for item in soup.find_all("li", class_="js-stream-content")[:max_articles]:
        title_el = item.find("h3")
        link_el = item.find("a")
        source_el = item.find("span", attrs={"data-test-locator": "publisher"})

        if title_el:
            articles.append({
                "title": title_el.text.strip(),
                "url": link_el.get("href", "") if link_el else "",
                "snippet": title_el.text.strip()[:300],
                "source": source_el.text.strip() if source_el else "Yahoo Finance",
                "published_date": "",
            })

    return articles


def _quick_sentiment(text: str) -> float:
    """
    Quick rule-based sentiment scoring.
    Returns a score between -1.0 (bearish) and 1.0 (bullish).
    """
    bullish_words = {
        "surge", "jump", "soar", "rally", "beat", "exceed", "growth", "profit",
        "upgrade", "outperform", "bullish", "strong", "record", "gain", "rise",
        "revenue", "innovation", "breakthrough", "positive", "optimistic",
    }
    bearish_words = {
        "drop", "fall", "decline", "miss", "cut", "loss", "downgrade", "weak",
        "bearish", "risk", "concern", "warning", "slowdown", "negative",
        "pessimistic", "debt", "lawsuit", "investigation", "crash", "plunge",
    }

    words = set(text.lower().split())
    bull_count = len(words & bullish_words)
    bear_count = len(words & bearish_words)
    total = bull_count + bear_count

    if total == 0:
        return 0.0
    return (bull_count - bear_count) / total


def analyze_sentiment(articles: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Analyze overall sentiment across multiple articles.

    Args:
        articles: List of article dicts with 'sentiment' field

    Returns:
        Sentiment analysis summary
    """
    if not articles:
        return {
            "overall_sentiment": 0.0,
            "sentiment_breakdown": {"bullish": 0, "neutral": 0, "bearish": 0},
            "key_topics": [],
            "summary": "No news articles found.",
        }

    sentiments = [a.get("sentiment", 0.0) for a in articles]
    avg_sentiment = sum(sentiments) / len(sentiments)

    bullish = sum(1 for s in sentiments if s > 0.1)
    bearish = sum(1 for s in sentiments if s < -0.1)
    neutral = len(sentiments) - bullish - bearish

    # Extract key topics from titles
    all_titles = " ".join(a.get("title", "") for a in articles)
    topics = list(set(w for w in bullish_words | bearish_words if w.lower() in all_titles.lower()))[:5]

    # Generate summary
    if avg_sentiment > 0.3:
        tone = "predominantly positive"
    elif avg_sentiment > 0.1:
        tone = "slightly positive"
    elif avg_sentiment < -0.3:
        tone = "predominantly negative"
    elif avg_sentiment < -0.1:
        tone = "slightly negative"
    else:
        tone = "neutral"

    return {
        "overall_sentiment": round(avg_sentiment, 3),
        "sentiment_breakdown": {
            "bullish": bullish,
            "neutral": neutral,
            "bearish": bearish,
        },
        "key_topics": topics,
        "summary": (
            f"Analyzed {len(articles)} articles. Overall sentiment is {tone} "
            f"({bullish} positive, {neutral} neutral, {bearish} negative)."
        ),
    }


# Need to re-import for analyze_sentiment
bullish_words = {
    "surge", "jump", "soar", "rally", "beat", "exceed", "growth", "profit",
    "upgrade", "outperform", "bullish", "strong", "record", "gain", "rise",
    "revenue", "innovation", "breakthrough", "positive", "optimistic",
}
bearish_words = {
    "drop", "fall", "decline", "miss", "cut", "loss", "downgrade", "weak",
    "bearish", "risk", "concern", "warning", "slowdown", "negative",
    "pessimistic", "debt", "lawsuit", "investigation", "crash", "plunge",
}
