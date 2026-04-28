"""Tests for the scoring module."""

from __future__ import annotations

from finra.agent.state import ConvictionScores, MarketData, NewsSentiment, Verdict
from finra.report.scorer import conviction_to_verdict, score_conviction


class TestScoring:
    """Tests for conviction scoring."""

    def test_score_fundamentals_strong(self):
        """Test fundamentals scoring for a strong company."""
        market = MarketData(
            revenue_growth=20.0,
            net_margin=0.25,
            roe=0.30,
        )
        scores = score_conviction(market=market)
        assert scores.fundamentals >= 70

    def test_score_fundamentals_weak(self):
        """Test fundamentals scoring for a weak company."""
        market = MarketData(
            revenue_growth=-10.0,
            net_margin=0.02,
            roe=0.05,
        )
        scores = score_conviction(market=market)
        assert scores.fundamentals <= 60

    def test_score_sentiment(self):
        """Test sentiment scoring."""
        news = NewsSentiment(overall_sentiment=0.8)
        scores = score_conviction(news=news)
        assert scores.sentiment >= 80

    def test_conviction_to_verdict(self):
        """Test verdict mapping."""
        # Strong conviction
        scores = ConvictionScores(fundamentals=85, technicals=80, sentiment=90, momentum=85, valuation=80)
        assert conviction_to_verdict(scores) in (Verdict.STRONG_BUY, Verdict.BUY)

        # Weak conviction
        scores = ConvictionScores(fundamentals=20, technicals=15, sentiment=10, momentum=25, valuation=20)
        assert conviction_to_verdict(scores) in (Verdict.SELL, Verdict.STRONG_SELL)

        # Neutral
        scores = ConvictionScores(fundamentals=50, technicals=50, sentiment=50, momentum=50, valuation=50)
        assert conviction_to_verdict(scores) == Verdict.HOLD

    def test_overall_score(self):
        """Test overall score calculation."""
        scores = ConvictionScores(fundamentals=100, technicals=100, sentiment=100, momentum=100, valuation=100)
        assert scores.overall == 100

        scores = ConvictionScores(fundamentals=0, technicals=0, sentiment=0, momentum=0, valuation=0)
        assert scores.overall == 0
