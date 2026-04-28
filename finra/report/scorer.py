"""
Scoring Module — conviction scoring framework.
"""

from __future__ import annotations

from typing import Optional

from finra.agent.state import ConvictionScores, MarketData, NewsSentiment, Verdict


def score_conviction(
    market: Optional[MarketData] = None,
    news: Optional[NewsSentiment] = None,
) -> ConvictionScores:
    """
    Calculate multi-factor conviction scores from raw data.

    Scoring methodology:
    - Fundamentals (30%): Revenue growth, margins, ROE, FCF
    - Technicals (20%): RSI, trend, momentum
    - Sentiment (20%): News sentiment score
    - Momentum (15%): Price momentum, volume trend
    - Valuation (15%): P/E, P/S relative to sector

    Each factor is scored 0-100 independently.
    Overall score is a weighted average.
    """
    scores = ConvictionScores()

    if market:
        scores.fundamentals = _score_fundamentals(market)
        scores.technicals = _score_technicals(market)
        scores.momentum = _score_momentum(market)
        scores.valuation = _score_valuation(market)

    if news:
        scores.sentiment = _score_sentiment(news)

    # Fill any missing with neutral
    if scores.fundamentals == 0:
        scores.fundamentals = 50
    if scores.technicals == 0:
        scores.technicals = 50
    if scores.sentiment == 0:
        scores.sentiment = 50
    if scores.momentum == 0:
        scores.momentum = 50
    if scores.valuation == 0:
        scores.valuation = 50

    return scores


def conviction_to_verdict(scores: ConvictionScores) -> Verdict:
    """Map overall conviction score to an investment verdict."""
    overall = scores.overall

    if overall >= 82:
        return Verdict.STRONG_BUY
    elif overall >= 70:
        return Verdict.BUY
    elif overall >= 58:
        return Verdict.MODERATE_BUY
    elif overall >= 42:
        return Verdict.HOLD
    elif overall >= 30:
        return Verdict.MODERATE_SELL
    elif overall >= 18:
        return Verdict.SELL
    else:
        return Verdict.STRONG_SELL


def _score_fundamentals(market: MarketData) -> int:
    """Score fundamentals: growth, margins, profitability."""
    score = 50  # Base

    # Revenue growth (0-25 points)
    if market.revenue_growth > 20:
        score += 25
    elif market.revenue_growth > 10:
        score += 20
    elif market.revenue_growth > 5:
        score += 15
    elif market.revenue_growth > 0:
        score += 10
    elif market.revenue_growth > -5:
        score += 5
    else:
        score -= 5

    # Profit margins (0-15 points)
    if market.net_margin and market.net_margin > 0.2:
        score += 15
    elif market.net_margin and market.net_margin > 0.1:
        score += 10
    elif market.net_margin and market.net_margin > 0.05:
        score += 5

    # ROE (0-10 points)
    if market.roe and market.roe > 0.2:
        score += 10
    elif market.roe and market.roe > 0.15:
        score += 7
    elif market.roe and market.roe > 0.1:
        score += 3

    return max(0, min(100, score))


def _score_technicals(market: MarketData) -> int:
    """Score technical indicators."""
    score = 50

    ti = market.technical_indicators
    if not ti:
        return score

    # RSI
    rsi = ti.get("rsi_14", 50)
    if 40 <= rsi <= 60:
        score += 10  # Neutral zone
    elif rsi < 30:
        score += 15  # Oversold = potential bounce
    elif rsi > 70:
        score -= 10  # Overbought

    # Trend
    trend = ti.get("trend", "neutral")
    if trend == "bullish":
        score += 20
    elif trend == "bearish":
        score -= 20

    # Volatility
    vol = ti.get("volatility_annualized", 0.3)
    if vol > 0.5:
        score -= 10  # High volatility = risk
    elif vol < 0.15:
        score += 5  # Low volatility = stable

    return max(0, min(100, score))


def _score_momentum(market: MarketData) -> int:
    """Score price momentum."""
    score = 50

    # Recent price change
    change = market.price_change_pct
    if change > 5:
        score += 25
    elif change > 2:
        score += 15
    elif change > 0:
        score += 5
    elif change > -2:
        score -= 5
    elif change > -5:
        score -= 15
    else:
        score -= 25

    return max(0, min(100, score))


def _score_valuation(market: MarketData) -> int:
    """Score valuation attractiveness."""
    score = 50

    # P/E ratio
    pe = market.pe_ratio
    if pe > 0:
        if pe < 10:
            score += 30
        elif pe < 15:
            score += 20
        elif pe < 25:
            score += 5
        elif pe < 35:
            score -= 10
        else:
            score -= 20
    else:
        # Negative earnings — score based on P/S
        ps = market.ps_ratio
        if ps > 0 and ps < 2:
            score += 10
        elif ps > 5:
            score -= 15

    return max(0, min(100, score))


def _score_sentiment(news: NewsSentiment) -> int:
    """Map sentiment score (-1 to 1) to 0-100."""
    return int((news.overall_sentiment + 1) * 50)
