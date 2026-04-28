# Adding a New Agent

This guide walks through adding a new specialized agent to the pipeline.

## Step 1: Create the Agent Module

Create `finra/agents/your_agent.py`:

```python
from __future__ import annotations
from typing import Any

async def run_your_agent(ticker: str, **kwargs) -> dict[str, Any]:
    \"\"\"
    Your specialized agent.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with analysis results
    \"\"\"
    # 1. Fetch data
    # 2. Process and analyze
    # 3. Return structured results
    return {
        "key_metric": 42,
        "findings": ["Finding 1", "Finding 2"],
    }
```

## Step 2: Add to Orchestrator

In `finra/agent/orchestrator.py`:

### 2a. Add the node function

```python
async def _your_agent_node(state: dict[str, Any]) -> dict[str, Any]:
    try:
        result = await run_your_agent(state["ticker"])
        return {"your_agent_data": result}
    except Exception as e:
        return {"errors": state.get("errors", []) + [f"Your agent error: {e}"]}
```

### 2b. Add to the graph

```python
workflow.add_node("your_agent", _your_agent_node)
```

### 2c. Wire the edges

```python
# Add conditional routing if needed
workflow.add_conditional_edges("news_agent", _should_run_your_agent, {
    "your_agent": "your_agent",
    "skip_your": "synthesis_agent",
})
workflow.add_edge("your_agent", "synthesis_agent")
```

## Step 3: Update the State

In `finra/agent/state.py`, add any new fields you need to `AgentState`.

## Step 4: Update Synthesis

In `finra/agents/synthesis_agent.py`, add your agent's output to the synthesis prompt.

## Step 5: Add Tests

Create `tests/test_your_agent.py`:

```python
import pytest

class TestYourAgent:
    def test_basic(self):
        # Write tests here
        assert True
```

## Step 6: Update Documentation

- Add to README architecture diagram
- Update docs/architecture.md
- Add to CONTRIBUTING.md examples
