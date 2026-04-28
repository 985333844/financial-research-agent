"""
Market Data Tool — fetches stock data via yfinance.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

import yfinance as yf

from finra.agent.state import MarketData


def get_market_data(ticker: str, period: str = "1y") -> MarketData:
    """
    Fetch comprehensive market data for a ticker.

    Args:
        ticker: Stock ticker symbol
        period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)

    Returns:
        MarketData with price, fundamentals, and technicals
    """
    stock = yf.Ticker(ticker)

    # Get current price info
    info = stock.info or {}

    # Get price history
    history = stock.history(period=period)

    # Get financials
    financials = stock.financials
    balance_sheet = stock.balance_sheet
    cashflow = stock.cashflow

    # Calculate price change
    current_price = info.get("currentPrice", info.get("regularMarketPrice", 0))
    prev_close = info.get("previousClose", 0)
    price_change_pct = (
        ((current_price - prev_close) / prev_close * 100) if prev_close else 0
    )

    # Revenue growth
    revenue_growth = 0
    if financials is not None and len(financials.columns) >= 2:
        rev_current = financials.iloc[financials.index.get_loc("Total Revenue")].iloc[0] if "Total Revenue" in financials.index else 0
        rev_prev = financials.iloc[financials.index.get_loc("Total Revenue")].iloc[1] if "Total Revenue" in financials.index else 0
        if rev_prev:
            revenue_growth = (rev_current - rev_prev) / abs(rev_prev) * 100

    data = MarketData(
        ticker=ticker.upper(),
        current_price=current_price,
        price_change_pct=round(price_change_pct, 2),
        market_cap=info.get("marketCap", 0),
        pe_ratio=info.get("trailingPE", 0),
        ps_ratio=info.get("priceToSalesTrailing12Months", 0),
        pb_ratio=info.get("priceToBook", 0),
        dividend_yield=info.get("dividendYield", 0),
        revenue=info.get("totalRevenue", 0),
        revenue_growth=round(revenue_growth, 2),
        net_income=info.get("netIncomeToCommon", 0),
        free_cash_flow=info.get("freeCashflow", 0),
        debt_to_equity=info.get("debtToEquity", 0),
        roe=info.get("returnOnEquity", 0),
        gross_margin=info.get("grossMargins", 0),
        operating_margin=info.get("operatingMargins", 0),
        net_margin=info.get("profitMargins", 0),
    )

    # Add analyst recommendations
    recs = stock.recommendations
    if recs is not None and not recs.empty:
        # Get the most recent recommendation
        latest = recs.iloc[-1] if len(recs) > 0 else {}
        data.analyst_recommendations = {
            "strong_buy": int(latest.get("strongBuy", 0)),
            "buy": int(latest.get("buy", 0)),
            "hold": int(latest.get("hold", 0)),
            "sell": int(latest.get("sell", 0)),
            "strong_sell": int(latest.get("strongSell", 0)),
        }

    return data


def get_technical_indicators(ticker: str, period: int = 180) -> dict[str, Any]:
    """
    Calculate technical indicators for a ticker.

    Args:
        ticker: Stock ticker symbol
        period: Lookback period in days

    Returns:
        Dict with technical indicator values
    """
    stock = yf.Ticker(ticker)
    end = datetime.now()
    start = end - timedelta(days=period)
    history = stock.history(start=start, end=end)

    if history.empty:
        return {}

    closes = history["Close"].values

    # Simple Moving Averages
    sma_20 = closes[-20:].mean() if len(closes) >= 20 else closes.mean()
    sma_50 = closes[-50:].mean() if len(closes) >= 50 else closes.mean()
    sma_200 = closes[-200:].mean() if len(closes) >= 200 else closes.mean()

    # RSI (14-period)
    rsi = _calculate_rsi(history["Close"], period=14)

    # Volatility (standard deviation of daily returns)
    returns = history["Close"].pct_change().dropna()
    volatility = returns.std() * (252**0.5)  # Annualized

    # 52-week high/low
    high_52w = history["High"].max()
    low_52w = history["Low"].min()
    current = closes[-1]

    return {
        "sma_20": round(sma_20, 2),
        "sma_50": round(sma_50, 2),
        "sma_200": round(sma_200, 2),
        "rsi_14": round(rsi, 2),
        "volatility_annualized": round(volatility, 4),
        "high_52w": round(high_52w, 2),
        "low_52w": round(low_52w, 2),
        "pct_off_52w_high": round((current - high_52w) / high_52w * 100, 2) if high_52w else 0,
        "pct_above_52w_low": round((current - low_52w) / low_52w * 100, 2) if low_52w else 0,
        "trend": "bullish" if current > sma_50 > sma_200 else "bearish" if current < sma_50 < sma_200 else "neutral",
        "volume_avg": round(history["Volume"].mean(), 0),
    }


def _calculate_rsi(prices, period: int = 14) -> float:
    """Calculate Relative Strength Index."""
    delta = prices.diff().dropna()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0, float("inf"))
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1] if not rsi.empty else 50.0
