"""
Technical Analysis Tool — computes technical indicators.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import numpy as np
import yfinance as yf


def compute_all_indicators(ticker: str, period: str = "1y") -> dict[str, Any]:
    """
    Compute a comprehensive set of technical indicators.

    Args:
        ticker: Stock ticker symbol
        period: Historical data period

    Returns:
        Dict with all computed indicators
    """
    stock = yf.Ticker(ticker)
    history = stock.history(period=period)

    if history.empty:
        return {"error": f"No data available for {ticker}"}

    closes = history["Close"].values
    highs = history["High"].values
    lows = history["Low"].values
    volumes = history["Volume"].values

    return {
        "moving_averages": _moving_averages(closes),
        "rsi": _rsi(closes),
        "macd": _macd(closes),
        "bollinger_bands": _bollinger_bands(closes),
        "volume_analysis": _volume_analysis(volumes, closes),
        "support_resistance": _support_resistance(highs, lows),
        "trend": _trend_analysis(closes),
        "momentum": _momentum(closes),
    }


def _moving_averages(closes: np.ndarray) -> dict[str, float]:
    """Compute SMA and EMA."""
    result = {}
    for period in [10, 20, 50, 100, 200]:
        if len(closes) >= period:
            result[f"sma_{period}"] = round(float(closes[-period:].mean()), 2)
            # EMA approximation
            alpha = 2 / (period + 1)
            ema = closes[0]
            for price in closes[1:]:
                ema = alpha * price + (1 - alpha) * ema
            result[f"ema_{period}"] = round(ema, 2)
    return result


def _rsi(closes: np.ndarray, period: int = 14) -> dict[str, Any]:
    """Compute RSI."""
    if len(closes) < period + 1:
        return {"value": 50.0, "signal": "neutral"}

    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])

    if avg_loss == 0:
        rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

    signal = "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral"
    return {"value": round(rsi, 2), "signal": signal}


def _macd(closes: np.ndarray) -> dict[str, float]:
    """Compute MACD."""
    def ema(data, span):
        alpha = 2 / (span + 1)
        result = np.zeros_like(data)
        result[0] = data[0]
        for i in range(1, len(data)):
            result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]
        return result

    if len(closes) < 26:
        return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}

    ema12 = ema(closes, 12)
    ema26 = ema(closes, 26)
    macd_line = ema12 - ema26
    signal_line = ema(macd_line, 9)
    histogram = macd_line - signal_line

    return {
        "macd": round(float(macd_line[-1]), 4),
        "signal": round(float(signal_line[-1]), 4),
        "histogram": round(float(histogram[-1]), 4),
    }


def _bollinger_bands(closes: np.ndarray, period: int = 20, std_dev: float = 2.0) -> dict[str, float]:
    """Compute Bollinger Bands."""
    if len(closes) < period:
        return {"upper": 0.0, "middle": 0.0, "lower": 0.0}

    sma = closes[-period:].mean()
    std = closes[-period:].std()

    return {
        "upper": round(sma + std_dev * std, 2),
        "middle": round(sma, 2),
        "lower": round(sma - std_dev * std, 2),
        "bandwidth": round(2 * std_dev * std / sma * 100, 4) if sma else 0,
    }


def _volume_analysis(volumes: np.ndarray, closes: np.ndarray) -> dict[str, Any]:
    """Analyze volume patterns."""
    avg_volume = float(volumes[-20:].mean()) if len(volumes) >= 20 else float(volumes.mean())
    current_volume = float(volumes[-1])
    volume_ratio = current_volume / avg_volume if avg_volume else 1.0

    # Volume trend
    if len(volumes) >= 5:
        recent_avg = float(volumes[-5:].mean())
        volume_trend = "increasing" if recent_avg > avg_volume * 1.1 else "decreasing" if recent_avg < avg_volume * 0.9 else "stable"
    else:
        volume_trend = "neutral"

    return {
        "current_volume": int(current_volume),
        "avg_volume_20d": int(avg_volume),
        "volume_ratio": round(volume_ratio, 2),
        "trend": volume_trend,
    }


def _support_resistance(highs: np.ndarray, lows: np.ndarray) -> dict[str, float]:
    """Identify approximate support and resistance levels."""
    if len(highs) < 20:
        return {"support": float(lows.min()), "resistance": float(highs.max())}

    recent_highs = highs[-20:]
    recent_lows = lows[-20:]

    return {
        "support_1": round(float(np.percentile(recent_lows, 25)), 2),
        "support_2": round(float(np.percentile(recent_lows, 10)), 2),
        "resistance_1": round(float(np.percentile(recent_highs, 75)), 2),
        "resistance_2": round(float(np.percentile(recent_highs, 90)), 2),
    }


def _trend_analysis(closes: np.ndarray) -> dict[str, Any]:
    """Determine overall trend."""
    if len(closes) < 50:
        return {"trend": "insufficient_data", "strength": 0}

    sma_short = closes[-20:].mean()
    sma_long = closes[-50:].mean()
    current = closes[-1]

    if current > sma_short > sma_long:
        trend = "strong_uptrend"
    elif current > sma_short and sma_short < sma_long:
        trend = "potential_reversal_up"
    elif current < sma_short < sma_long:
        trend = "strong_downtrend"
    elif current < sma_short and sma_short > sma_long:
        trend = "potential_reversal_down"
    else:
        trend = "neutral"

    # Trend strength (R-squared of linear regression)
    x = np.arange(len(closes[-50:]))
    y = closes[-50:]
    slope = np.polyfit(x, y, 1)[0]
    y_pred = np.polyval(np.polyfit(x, y, 1), x)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot else 0

    return {
        "trend": trend,
        "strength": round(r_squared, 3),
        "direction": "up" if slope > 0 else "down",
    }


def _momentum(closes: np.ndarray) -> dict[str, float]:
    """Calculate momentum indicators."""
    if len(closes) < 20:
        return {}

    current = closes[-1]
    return {
        "momentum_10d": round((current / closes[-11] - 1) * 100, 2) if len(closes) >= 11 else 0,
        "momentum_20d": round((current / closes[-21] - 1) * 100, 2) if len(closes) >= 21 else 0,
        "rate_of_change_5d": round((current / closes[-6] - 1) * 100, 2) if len(closes) >= 6 else 0,
    }
