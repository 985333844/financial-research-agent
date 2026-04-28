"""Tests for the news and sentiment tools."""

from __future__ import annotations

from finra.tools.news import _quick_sentiment, analyze_sentiment


class TestSentiment:
    """Tests for sentiment analysis."""

    def test_bullish_sentiment(self):
        """Test positive sentiment detection."""
        score = _quick_sentiment("Apple stock surges on strong earnings beat and record revenue growth")
        assert score > 0

    def test_bearish_sentiment(self):
        """Test negative sentiment detection."""
        score = _quick_sentiment("Stock falls amid slowdown concerns and investigation into accounting fraud")
        assert score < 0

    def test_neutral_sentiment(self):
        """Test neutral sentiment."""
        score = _quick_sentiment("The meeting is scheduled for next Tuesday")
        assert abs(score) < 0.5

    def test_analyze_sentiment_empty(self):
        """Test sentiment analysis with no articles."""
        result = analyze_sentiment([])
        assert result["overall_sentiment"] == 0.0
        assert result["summary"] == "No news articles found."

    def test_analyze_sentiment_articles(self):
        """Test sentiment analysis with sample articles."""
        articles = [
            {"title": "Stock surges on earnings beat", "sentiment": 0.8},
            {"title": "Revenue growth exceeds expectations", "sentiment": 0.6},
            {"title": "Company faces investigation risk", "sentiment": -0.7},
        ]
        result = analyze_sentiment(articles)
        assert result["overall_sentiment"] > 0  # Net positive
        assert result["sentiment_breakdown"]["bullish"] == 2
        assert result["sentiment_breakdown"]["bearish"] == 1
