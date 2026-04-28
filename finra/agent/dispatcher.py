"""
Query Dispatcher — routes sub-tasks to specialized agents.
"""

from __future__ import annotations

from typing import Any

from finra.agent.state import AgentState


def dispatch(state: AgentState) -> dict[str, list[str]]:
    """
    Determine which agents should run based on the research plan.

    Returns:
        Dict with 'next_agents' — list of agent names to invoke.
    """
    required_sources = state.get("required_sources", [])

    source_to_agent = {
        "market_data": "market_agent",
        "sec_filings": "sec_agent",
        "news": "news_agent",
        "earnings": "sec_agent",  # Earnings calls handled by SEC agent
    }

    next_agents = []
    for source in required_sources:
        agent = source_to_agent.get(source)
        if agent and agent not in next_agents:
            next_agents.append(agent)

    # Always run synthesis after data collection
    if next_agents:
        next_agents.append("synthesis_agent")

    return {"next_agents": next_agents}
