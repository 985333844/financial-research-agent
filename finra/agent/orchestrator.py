"""
Main Orchestrator — LangGraph-based multi-agent pipeline.

This is the entry point for running financial research queries.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, AsyncIterator, Optional

from langgraph.graph import END, StateGraph

from finra.agent.dispatcher import dispatch
from finra.agent.planner import plan_research
from finra.agent.state import (
    AgentState,
    ConvictionScores,
    MarketData,
    NewsSentiment,
    SECFilingAnalysis,
    Verdict,
)
from finra.agents.market_agent import run_market_agent
from finra.agents.news_agent import run_news_agent
from finra.agents.sec_agent import run_sec_agent
from finra.agents.synthesis_agent import run_synthesis_agent
from finra.config import settings


def _state_defaults() -> dict[str, Any]:
    """Create default state values."""
    return {
        "query": "",
        "ticker": "",
        "depth": "standard",
        "research_plan": [],
        "required_sources": [],
        "market_data": None,
        "sec_analysis": None,
        "news_sentiment": None,
        "bull_points": [],
        "bear_points": [],
        "executive_summary": "",
        "conviction": None,
        "verdict": Verdict.HOLD,
        "report_markdown": "",
        "sources": [],
        "started_at": datetime.now().isoformat(),
        "completed_at": "",
        "errors": [],
        "iteration": 0,
    }


async def _plan_node(state: dict[str, Any]) -> dict[str, Any]:
    """Planning node — creates research plan."""
    plan_result = await plan_research(
        query=state["query"],
        ticker=state["ticker"],
        depth=state.get("depth", "standard"),
    )
    return {
        "research_plan": plan_result.get("research_plan", []),
        "required_sources": plan_result.get("required_sources", ["market_data", "news"]),
    }


async def _market_node(state: dict[str, Any]) -> dict[str, Any]:
    """Market data collection node."""
    try:
        market_data = await run_market_agent(state["ticker"])
        return {"market_data": market_data}
    except Exception as e:
        return {"errors": state.get("errors", []) + [f"Market agent error: {e}"]}


async def _sec_node(state: dict[str, Any]) -> dict[str, Any]:
    """SEC filing analysis node."""
    try:
        sec_analysis = await run_sec_agent(state["ticker"])
        return {"sec_analysis": sec_analysis}
    except Exception as e:
        return {"errors": state.get("errors", []) + [f"SEC agent error: {e}"]}


async def _news_node(state: dict[str, Any]) -> dict[str, Any]:
    """News sentiment analysis node."""
    try:
        news_sentiment = await run_news_agent(state["ticker"])
        return {"news_sentiment": news_sentiment}
    except Exception as e:
        return {"errors": state.get("errors", []) + [f"News agent error: {e}"]}


async def _synthesis_node(state: dict[str, Any]) -> dict[str, Any]:
    """Synthesis and report generation node."""
    try:
        result = await run_synthesis_agent(
            query=state["query"],
            ticker=state["ticker"],
            market_data=state.get("market_data"),
            sec_analysis=state.get("sec_analysis"),
            news_sentiment=state.get("news_sentiment"),
        )
        return {
            "executive_summary": result.get("executive_summary", ""),
            "bull_points": result.get("bull_points", []),
            "bear_points": result.get("bear_points", []),
            "conviction": result.get("conviction"),
            "verdict": result.get("verdict", Verdict.HOLD),
            "report_markdown": result.get("report_markdown", ""),
            "sources": result.get("sources", []),
            "completed_at": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "errors": state.get("errors", []) + [f"Synthesis error: {e}"],
            "completed_at": datetime.now().isoformat(),
        }


def _should_run_sec(state: dict[str, Any]) -> str:
    """Conditional edge: should we run the SEC agent?"""
    sources = state.get("required_sources", [])
    return "sec_agent" if "sec_filings" in sources or "earnings" in sources else "skip_sec"


def _should_run_news(state: dict[str, Any]) -> str:
    """Conditional edge: should we run the news agent?"""
    sources = state.get("required_sources", [])
    return "news_agent" if "news" in sources else "skip_news"


def build_graph() -> StateGraph:
    """Build the LangGraph research pipeline."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("planner", _plan_node)
    workflow.add_node("market_agent", _market_node)
    workflow.add_node("sec_agent", _sec_node)
    workflow.add_node("news_agent", _news_node)
    workflow.add_node("synthesis_agent", _synthesis_node)

    # Set entry point
    workflow.set_entry_point("planner")

    # Add edges
    workflow.add_edge("planner", "market_agent")
    workflow.add_conditional_edges("market_agent", _should_run_sec, {
        "sec_agent": "sec_agent",
        "skip_sec": "news_router",
    })
    workflow.add_edge("sec_agent", "news_router")
    workflow.add_conditional_edges("news_router", _should_run_news, {
        "news_agent": "news_agent",
        "skip_news": "synthesis_agent",
    })
    workflow.add_edge("news_agent", "synthesis_agent")
    workflow.add_edge("synthesis_agent", END)

    # Add the news_router as a passthrough
    workflow.add_node("news_router", lambda s: s)

    return workflow.compile()


class ResearchAgent:
    """
    Main entry point for financial research.

    Usage:
        agent = ResearchAgent()
        report = await agent.research(ticker="AAPL", query="Should I invest in Apple?")
        print(report["report_markdown"])
    """

    def __init__(self):
        self._graph = build_graph()

    async def research(
        self,
        ticker: str,
        query: str,
        depth: str = "standard",
    ) -> dict[str, Any]:
        """
        Run a financial research query.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")
            query: Research question or topic
            depth: Research depth — "quick", "standard", or "deep"

        Returns:
            Dict containing the research report and all intermediate results
        """
        state = _state_defaults()
        state["query"] = query
        state["ticker"] = ticker.upper()
        state["depth"] = depth
        state["started_at"] = datetime.now().isoformat()

        # Run the pipeline
        result = await self._graph.ainvoke(state)
        return result

    async def research_stream(
        self,
        ticker: str,
        query: str,
        depth: str = "standard",
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Run research with streaming state updates.

        Yields partial state updates as agents complete their work.
        """
        state = _state_defaults()
        state["query"] = query
        state["ticker"] = ticker.upper()
        state["depth"] = depth
        state["started_at"] = datetime.now().isoformat()

        async for event in self._graph.astream(state):
            # Yield each node's output
            for node_name, node_output in event.items():
                yield {"node": node_name, "data": node_output}
