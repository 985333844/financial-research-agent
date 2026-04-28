# Architecture

## System Overview

Financial Research Agent uses a **multi-agent pipeline** orchestrated by LangGraph:

```
User Query → Planner → Dispatcher → [Market Agent | SEC Agent | News Agent] → Synthesis Agent → Report
```

## Agent Descriptions

### 1. Planning Agent
Analyzes the research query and creates an execution plan:
- Identifies required data sources
- Generates sub-tasks for specialized agents
- Estimates research complexity

### 2. Market Data Agent
Fetches comprehensive financial data:
- Real-time and historical prices (yfinance)
- Fundamental metrics (P/E, margins, ROE, revenue growth)
- Technical indicators (RSI, MACD, Bollinger Bands, SMA/EMA)
- Analyst recommendations

### 3. SEC Filing Agent
Retrieves and analyzes SEC filings:
- Downloads from EDGAR
- Parses 10-K, 10-Q, 8-K filings
- Extracts key sections (business, risk factors, MD&A)
- Identifies risk factors and key findings

### 4. News Sentiment Agent
Aggregates and analyzes news:
- Searches via Tavily API and Yahoo Finance
- Computes per-article sentiment scores
- Aggregates overall sentiment
- Identifies key topics

### 5. Synthesis Agent
Generates the final research report:
- Merges findings from all agents
- Creates bull/bear case analysis
- Calculates multi-factor conviction scores
- Produces structured Markdown report with citations

## Scoring Framework

| Factor | Weight | Data Sources |
|--------|--------|-------------|
| Fundamentals | 30% | Revenue growth, margins, ROE, FCF |
| Technicals | 20% | RSI, trend, momentum, volatility |
| Sentiment | 20% | News sentiment analysis |
| Momentum | 15% | Price change, volume |
| Valuation | 15% | P/E, P/S, P/B ratios |

## Verdict Scale

| Score Range | Verdict |
|-------------|---------|
| 82-100 | Strong Buy |
| 70-81 | Buy |
| 58-69 | Moderate Buy |
| 42-57 | Hold |
| 30-41 | Moderate Sell |
| 18-29 | Sell |
| 0-17 | Strong Sell |
