"""Tests for the market data agent."""

from __future__ import annotations

import pytest

from finra.tools.market_data import (
    _calculate_rsi,
    get_market_data,
    get_technical_indicators,
)


class TestMarketData:
    """Tests for market data functions."""

    def test_get_market_data_valid_ticker(self):
        """Test fetching market data for a valid ticker."""
        data = get_market_data("AAPL")
        assert data.ticker == "AAPL"
        assert data.current_price > 0

    def test_get_market_data_invalid_ticker(self):
        """Test handling of an invalid ticker."""
        data = get_market_data("INVALIDTICKER123")
        assert data.ticker == "INVALIDTICKER123"

    def test_technical_indicators(self):
        """Test technical indicator calculation."""
        indicators = get_technical_indicators("AAPL")
        assert "rsi_14" in indicators
        assert "sma_20" in indicators
        assert 0 <= indicators["rsi_14"] <= 100


class TestRSI:
    """Tests for RSI calculation."""

    def test_rsi_calculation(self):
        """Test RSI calculation with synthetic data."""
        import pandas as pd

        # Create synthetic price data with a clear uptrend
        prices = pd.Series([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24])
        rsi = _calculate_rsi(prices, period=14)
        assert rsi > 50  # Uptrend should have RSI > 50

    def test_rsi_downtrend(self):
        """Test RSI with a downtrend."""
        import pandas as pd

        prices = pd.Series([24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10])
        rsi = _calculate_rsi(prices, period=14)
        assert rsi < 50  # Downtrend should have RSI < 50
