"""
Market Data Agent — fetches and analyzes market data using yfinance.
"""

from __future__ import annotations

from typing import Any, Optional

from finra.agent.state import MarketData
from finra.tools.market_data import get_market_data, get_technical_indicators


async def run_market_agent(ticker: str) -> MarketData:
    """
    Run the market data agent.

    Fetches comprehensive market data and technical indicators for the given ticker.

    Args:
        ticker: Stock ticker symbol

    Returns:
        MarketData object with all collected data
    """
    # Fetch market data
    market = get_market_data(ticker)

    # Fetch technical indicators
    technicals = get_technical_indicators(ticker)
    market.technical_indicators = technicals

    return market


def _format_market_summary(market_data: MarketData) -> str:
    """Format market data into a readable summary."""
    lines = [
        f"## Market Data: {market_data.ticker}",
        f"Current Price: ${market_data.current_price:.2f} ({market_data.price_change_pct:+.2f}%)",
        f"Market Cap: ${market_data.market_cap / 1e12:.2f}T" if market_data.market_cap > 1e12 else f"Market Cap: ${market_data.market_cap / 1e9:.2f}B",
        "",
        "### Valuation",
        f"P/E Ratio: {market_data.pe_ratio:.1f}",
        f"P/S Ratio: {market_data.ps_ratio:.2f}",
        f"P/B Ratio: {market_data.pb_ratio:.2f}",
        f"Dividend Yield: {market_data.dividend_yield * 100:.2f}%" if market_data.dividend_yield else "Dividend Yield: N/A",
        "",
        "### Financials",
        f"Revenue: ${market_data.revenue / 1e9:.2f}B ({market_data.revenue_growth:+.1f}% YoY)" if market_data.revenue else "Revenue: N/A",
        f"Net Income: ${market_data.net_income / 1e9:.2f}B" if market_data.net_income else "Net Income: N/A",
        f"Free Cash Flow: ${market_data.free_cash_flow / 1e9:.2f}B" if market_data.free_cash_flow else "Free Cash Flow: N/A",
        "",
        "### Profitability",
        f"Gross Margin: {market_data.gross_margin * 100:.1f}%" if market_data.gross_margin else "Gross Margin: N/A",
        f"Operating Margin: {market_data.operating_margin * 100:.1f}%" if market_data.operating_margin else "Operating Margin: N/A",
        f"Net Margin: {market_data.net_margin * 100:.1f}%" if market_data.net_margin else "Net Margin: N/A",
        f"ROE: {market_data.roe * 100:.1f}%" if market_data.roe else "ROE: N/A",
    ]

    if market_data.technical_indicators:
        ti = market_data.technical_indicators
        lines.extend([
            "",
            "### Technical Indicators",
            f"SMA 20/50/200: ${ti.get('sma_20', 0):.2f} / ${ti.get('sma_50', 0):.2f} / ${ti.get('sma_200', 0):.2f}",
            f"RSI (14): {ti.get('rsi_14', 50):.1f} ({ti.get('trend', 'neutral')})",
            f"Annualized Volatility: {ti.get('volatility_annualized', 0) * 100:.1f}%",
            f"52-Week Range: ${ti.get('low_52w', 0):.2f} - ${ti.get('high_52w', 0):.2f}",
        ])

    return "\n".join(lines)
