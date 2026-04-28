"""
Streamlit Web UI for Financial Research Agent.

Run with: python -m finra.web
"""

import asyncio
import json
import sys
from pathlib import Path

import streamlit as st

from finra.agent.state import ResearchDepth
from finra.report.generator import ResearchReport

st.set_page_config(
    page_title="Financial Research Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .report-container {
        max-width: 900px;
        margin: 0 auto;
    }
    .verdict-badge {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 1.2em;
    }
    .stScoreBar {
        height: 24px;
        border-radius: 4px;
        background: linear-gradient(90deg, #ef4444 0%, #eab308 50%, #22c55e 100%);
    }
</style>
""", unsafe_allow_html=True)


def run_research_async(ticker: str, query: str, depth: str):
    """Run research asynchronously from Streamlit."""
    from finra import ResearchAgent
    agent = ResearchAgent()
    return asyncio.run(agent.research(ticker=ticker, query=query, depth=depth))


def main():
    st.title("🔍 Financial Research Agent")
    st.caption("AI-powered investment research — Multi-agent analysis pipeline")

    # Sidebar
    with st.sidebar:
        st.header("Settings")

        ticker = st.text_input(
            "Stock Ticker",
            value="AAPL",
            placeholder="e.g., AAPL, MSFT, NVDA",
            max_chars=10,
        ).upper()

        query = st.text_area(
            "Research Question",
            value="Should I invest in this company?",
            placeholder="e.g., Analyze the growth potential and competitive moat...",
            height=100,
        )

        depth = st.selectbox(
            "Research Depth",
            options=["quick", "standard", "deep"],
            index=1,
            help="Quick: market data + news\nStandard: + technical analysis\nDeep: + SEC filings",
        )

        st.divider()

        if st.button("🚀 Run Research", type="primary", use_container_width=True):
            if not ticker:
                st.error("Please enter a ticker symbol")
            elif not query:
                st.error("Please enter a research question")
            else:
                st.session_state["run_research"] = True

        st.divider()
        st.caption("""
        **FinRA v0.1.0**

        Multi-agent pipeline:
        - 📊 Market Data Agent
        - 📄 SEC Filing Agent
        - 📰 News Sentiment Agent
        - 📝 Synthesis Agent

        [GitHub](https://github.com/YOUR_USERNAME/financial-research-agent)
        """)

    # Main content
    if st.session_state.get("run_research"):
        st.session_state["run_research"] = False

        with st.status("Running research pipeline...", expanded=True) as status:
            st.write("📋 Planning research...")
            result = run_research_async(ticker, query, depth)
            st.write("📊 Analyzing market data...")
            st.write("📄 Processing SEC filings...")
            st.write("📰 Analyzing news sentiment...")
            st.write("📝 Generating report...")
            status.update(label="Research complete!", state="complete")

        # Display results
        report = ResearchReport.from_agent_result(result)

        # Verdict badge
        verdict_colors = {
            "Strong Buy": "🟢🟢",
            "Buy": "🟢",
            "Moderate Buy": "🟡🟢",
            "Hold": "🟡",
            "Moderate Sell": "🟡🔴",
            "Sell": "🔴",
            "Strong Sell": "🔴🔴",
        }
        emoji = verdict_colors.get(report.verdict.value, "⚪")
        st.markdown(f"## {emoji} Verdict: {report.verdict.value}")
        st.markdown(f"**Conviction Score: {report.conviction_score}/100**")

        # Executive Summary
        if report.executive_summary:
            st.markdown("## Executive Summary")
            st.markdown(report.executive_summary)

        # Conviction Breakdown
        if report.conviction:
            st.markdown("## Conviction Breakdown")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Fundamentals", f"{report.conviction.fundamentals}/100")
                st.progress(report.conviction.fundamentals / 100)
            with col2:
                st.metric("Technicals", f"{report.conviction.technicals}/100")
                st.progress(report.conviction.technicals / 100)
            with col3:
                st.metric("Sentiment", f"{report.conviction.sentiment}/100")
                st.progress(report.conviction.sentiment / 100)

            col4, col5 = st.columns(2)
            with col4:
                st.metric("Momentum", f"{report.conviction.momentum}/100")
                st.progress(report.conviction.momentum / 100)
            with col5:
                st.metric("Valuation", f"{report.conviction.valuation}/100")
                st.progress(report.conviction.valuation / 100)

        # Bull / Bear
        col_bull, col_bear = st.columns(2)
        with col_bull:
            if report.bull_points:
                st.markdown("### 🐂 Bull Case")
                for point in report.bull_points:
                    st.markdown(f"- {point}")
        with col_bear:
            if report.bear_points:
                st.markdown("### 🐻 Bear Case")
                for point in report.bear_points:
                    st.markdown(f"- {point}")

        # Full report
        with st.expander("📄 Full Report (Markdown)", expanded=False):
            st.markdown(report.markdown())

        # Download buttons
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                "📥 Download Markdown",
                data=report.markdown(),
                file_name=f"{ticker}_research.md",
                mime="text/markdown",
            )
        with col_dl2:
            st.download_button(
                "📥 Download JSON",
                data=json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
                file_name=f"{ticker}_research.json",
                mime="application/json",
            )

    else:
        # Landing page
        st.markdown("""
        ### How It Works

        Enter a stock ticker and research question, then click **Run Research**.

        The multi-agent pipeline will:
        1. **Plan** the research approach
        2. **Fetch** real-time market data (price, fundamentals, technicals)
        3. **Retrieve** and analyze SEC filings (10-K, 10-Q)
        4. **Aggregate** news and compute sentiment scores
        5. **Synthesize** everything into a professional research report

        ### Example Queries
        - "Should I invest in Apple?"
        - "Analyze NVIDIA's data center growth and competitive moat"
        - "Is Tesla overvalued at current prices?"
        - "Evaluate Microsoft's AI strategy and revenue potential"
        """)


if __name__ == "__main__":
    main()
