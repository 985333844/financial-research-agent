"""
Research Planning Agent.
Analyzes the query and creates a structured research plan.
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from finra.config import settings

PLANNER_PROMPT = """You are a financial research planner. Given a research query and ticker, \
create a structured research plan.

Research Query: {query}
Ticker: {ticker}
Depth: {depth}

Your plan should identify:
1. What data sources are needed (market data, SEC filings, news, earnings calls)
2. What specific analyses to perform
3. What questions the research should answer

Output a JSON object with:
- "research_plan": list of specific research steps
- "required_sources": list of data sources needed ["market_data", "sec_filings", "news", "earnings"]
- "key_questions": list of questions to answer

Be specific and actionable. For "quick" depth, focus on market data and recent news. \
For "deep" depth, include SEC filings, earnings analysis, and comprehensive news review."""


def create_planner() -> ChatPromptTemplate:
    """Create the planner prompt template."""
    return ChatPromptTemplate.from_messages([
        ("system", PLANNER_PROMPT),
        ("human", "Create a research plan for this query."),
    ])


async def plan_research(query: str, ticker: str, depth: str) -> dict:
    """
    Generate a research plan using the LLM.

    Args:
        query: The research query
        ticker: The stock ticker
        depth: Research depth (quick, standard, deep)

    Returns:
        Dict with research_plan, required_sources, and key_questions
    """
    llm = ChatOpenAI(
        model=settings.llm.model,
        temperature=settings.llm.temperature,
        max_tokens=1024,
    )

    prompt = create_planner()
    chain = prompt | llm

    response = await chain.ainvoke({
        "query": query,
        "ticker": ticker.upper(),
        "depth": depth,
    })

    import json

    try:
        # Try to parse JSON from the response
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content)
    except (json.JSONDecodeError, IndexError):
        # Fallback plan
        return {
            "research_plan": [
                f"Fetch current market data for {ticker}",
                f"Retrieve recent news about {ticker}",
                f"Analyze {query}",
                "Generate research report",
            ],
            "required_sources": ["market_data", "news"],
            "key_questions": [query],
        }
