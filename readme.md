# Financial Research Agent 🔍📈

<p align="center">
  <img src="docs/architecture.png" alt="Architecture" width="700"/>
</p>

<p align="center">
  <strong>An open-source autonomous AI agent for deep financial research</strong><br/>
  Multi-agent RAG pipeline • SEC filings • Earnings calls • News synthesis • Report generation
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python"/>
  <img src="https://img.shields.io/badge/LangGraph-0.3+-green.svg" alt="LangGraph"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License"/>
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen.svg" alt="PRs Welcome"/>
</p>

---

## 🌟 Overview

**Financial Research Agent (FinRA)** is a multi-agent autonomous system that performs institutional-grade financial research. Given a company ticker or research topic, it orchestrates a team of specialized AI agents to:

- 📊 **Fetch & analyze** real-time market data (via yfinance)
- 📄 **Read & interpret** SEC filings (10-K, 10-Q, 8-K)
- 🎙️ **Summarize** earnings call transcripts
- 📰 **Synthesize** news sentiment from multiple sources
- 📝 **Generate** professional investment research reports
- ⚖️ **Evaluate** with a multi-criteria scoring framework

### How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│                      FINANCIAL RESEARCH AGENT                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐     ┌──────────────────┐     ┌───────────────┐ │
│  │   Research   │────►│   Planning       │────►│  Dispatcher   │ │
│  │   Query      │     │   Agent          │     │  (Router)     │ │
│  └─────────────┘     └──────────────────┘     └───────┬───────┘ │
│                                                        │         │
│              ┌─────────────────┬─────────────────┬─────┘         │
│              ▼                 ▼                 ▼               │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │ Market Data   │ │ SEC Filing    │ │ News &       │         │
│  │ Agent         │ │ Agent         │ │ Sentiment    │         │
│  │ (yfinance)    │ │ (EDGAR/10-K)  │ │ Agent        │         │
│  └───────┬───────┘ └───────┬───────┘ └───────┬───────┘         │
│          │                 │                 │                  │
│          ▼                 ▼                 ▼                  │
│  ┌──────────────────────────────────────────────────┐           │
│  │           SYNTHESIS & REPORT GENERATOR           │           │
│  │  • Merge findings  • Score conviction            │           │
│  │  • Generate report • Cite sources                │           │
│  └──────────────────────────────────────────────────┘           │
│                        │                                         │
│                        ▼                                         │
│  ┌──────────────────────────────────────────────────┐           │
│  │        📄 Investment Research Report             │           │
│  │        • Executive Summary  • Risk Analysis      │           │
│  │        • Valuation Metrics  • Bull/Bear Case     │           │
│  │        • Conviction Rating   • Sources           │           │
│  └──────────────────────────────────────────────────┘           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## ✨ Features

### Core Capabilities
- **🔍 Multi-Source Data Retrieval** — Aggregates data from SEC EDGAR, Yahoo Finance, and news APIs
- **🧠 Semantic Routing** — Intelligently routes queries to the right specialized agent
- **📄 SEC Filing Analysis** — Parses 10-K/10-Q/8-K filings with section-level retrieval
- **📊 Technical & Fundamental Analysis** — Computes key financial metrics and technicals
- **📰 Sentiment Analysis** — Aggregates and scores news sentiment in real-time
- **📝 Report Generation** — Produces structured Markdown research reports
- **⚖️ Conviction Scoring** — Multi-factor scoring (fundamentals, technicals, sentiment, momentum)

### Technical Highlights
- **LangGraph** orchestration with stateful multi-agent workflow
- **RAG** (Retrieval-Augmented Generation) with hybrid vector + keyword search
- **Iterative self-reflection** — Agent evaluates and improves its own output
- **Streaming responses** — Real-time progress updates during research
- **Extensible architecture** — Plug in new data sources and analysis modules
- **BYOK** (Bring Your Own Key) — Works with OpenAI, Anthropic, or local LLMs via LiteLLM

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- An LLM API key (OpenAI, Anthropic, or compatible)

### Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/financial-research-agent.git
cd financial-research-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Run a Research Query

```bash
# Command line
python -m finra.cli --ticker AAPL --query "Should I invest in Apple?"

# With options
python -m finra.cli \
  --ticker MSFT \
  --query "Analyze Microsoft's AI strategy and revenue growth potential" \
  --output report.md \
  --format markdown \
  --depth deep
```

### Use as a Python Library

```python
from finra import ResearchAgent

agent = ResearchAgent()

# Run a research query
report = await agent.research(
    ticker="NVDA",
    query="Analyze NVIDIA's data center growth and competitive moat",
    depth="deep"
)

# Print the report
print(report.markdown())

# Access structured data
print(f"Conviction: {report.conviction_score}/100")
print(f"Bull/Bear: {report.verdict}")
print(f"Key Metrics: {report.key_metrics}")
```

### Run the Web UI

```bash
python -m finra.web
# Open http://localhost:8501
```

## 🏗️ Architecture

### Project Structure

```
financial-research-agent/
├── finra/                      # Core package
│   ├── __init__.py
│   ├── cli.py                  # Command-line interface
│   ├── web.py                  # Streamlit web UI
│   ├── agent/                  # Agent system
│   │   ├── __init__.py
│   │   ├── orchestrator.py     # Main LangGraph orchestrator
│   │   ├── state.py            # Shared state definitions
│   │   ├── planner.py          # Research planning agent
│   │   └── dispatcher.py       # Query routing agent
│   ├── tools/                  # Data retrieval tools
│   │   ├── __init__.py
│   │   ├── market_data.py      # yfinance integration
│   │   ├── sec_filings.py      # SEC EDGAR scraper
│   │   ├── news.py             # News aggregation
│   │   └── technical.py        # Technical analysis
│   ├── agents/                 # Specialized agents
│   │   ├── __init__.py
│   │   ├── market_agent.py     # Market data analysis
│   │   ├── sec_agent.py        # SEC filing analysis
│   │   ├── news_agent.py       # News & sentiment
│   │   └── synthesis_agent.py  # Report synthesis
│   ├── rag/                    # RAG system
│   │   ├── __init__.py
│   │   ├── embeddings.py       # Embedding generation
│   │   ├── retriever.py        # Hybrid retrieval
│   │   └── vectorstore.py      # Vector storage
│   ├── report/                 # Report generation
│   │   ├── __init__.py
│   │   ├── generator.py        # Report builder
│   │   ├── templates.py        # Report templates
│   │   └── scorer.py           # Conviction scoring
│   └── config.py               # Configuration
├── data/                       # Data storage
│   ├── filings/                # Cached SEC filings
│   ├── reports/                # Generated reports
│   └── cache/                  # General cache
├── tests/                      # Test suite
│   ├── test_agents.py
│   ├── test_tools.py
│   └── test_rag.py
├── docs/                       # Documentation
│   ├── architecture.md
│   ├── adding-agents.md
│   └── api-reference.md
├── .env.example                # Environment template
├── pyproject.toml              # Package config
├── requirements.txt            # Dependencies
├── Dockerfile                  # Container
├── docker-compose.yml          # Full stack
└── README.md                   # This file
```

### Agent Pipeline

1. **Planner** — Analyzes the query, identifies required data sources, creates a research plan
2. **Dispatcher** — Routes sub-tasks to specialized agents in parallel
3. **Market Data Agent** — Fetches price data, financials, and technical indicators
4. **SEC Filing Agent** — Retrieves and analyzes SEC filings with RAG
5. **News Agent** — Aggregates news, performs sentiment analysis
6. **Synthesis Agent** — Merges all findings, generates scored report with citations

## ⚙️ Configuration

Create a `.env` file from the template:

```bash
cp .env.example .env
```

### Required Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | — |
| `LLM_MODEL` | Model to use | `gpt-4o` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key | — |
| `TAVILY_API_KEY` | Tavily search API key | — |
| `SEC_USER_AGENT` | EDGAR user agent (required by SEC) | `FinRA/1.0` |
| `VECTOR_DB_PATH` | Local vector DB path | `./data/vectorstore` |
| `CACHE_TTL` | Cache TTL in seconds | `3600` |
| `RESEARCH_DEPTH` | Default research depth | `standard` |
| `REPORT_FORMAT` | Default output format | `markdown` |

## 📊 Output Example

A generated research report includes:

```markdown
# Investment Research Report: AAPL

## Executive Summary
Apple Inc. shows strong fundamentals with [summary]...

## Key Metrics
| Metric | Value | Rating |
|--------|-------|--------|
| P/E Ratio | 28.5 | Fair |
| Revenue Growth | 8.2% YoY | Strong |
| Free Cash Flow | $111.4B | Excellent |

## Bull Case
- Services revenue growing at 15%+ YoY...
- Vision Pro ecosystem expansion...

## Bear Case
- China market headwinds...
- Regulatory risks in EU...

## Conviction Score: 72/100 (Moderate Buy)
- Fundamentals: 80/100
- Technicals: 65/100
- Sentiment: 70/100
- Momentum: 72/100

## Sources
1. SEC 10-K Filing (FY2025) — [link]
2. Q1 2026 Earnings Call Transcript — [link]
3. Yahoo Finance — [link]
```

## 🧪 Development

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=finra tests/

# Specific module
pytest tests/test_agents.py -v
```

### Code Quality

```bash
# Format
ruff format .

# Lint
ruff check .

# Type check
mypy finra/
```

### Adding a New Agent

1. Create `finra/agents/your_agent.py`
2. Implement the `BaseAgent` protocol
3. Register in `finra/agent/dispatcher.py`
4. Add tests in `tests/`

See [docs/adding-agents.md](docs/adding-agents.md) for the full guide.

## 🐳 Docker

```bash
# Build
docker build -t financial-research-agent .

# Run CLI
docker run -it --env-file .env financial-research-agent --ticker AAPL

# Run Web UI
docker-compose up
```

## 🗺️ Roadmap

- [x] Core multi-agent pipeline
- [x] SEC filing retrieval & analysis
- [x] Market data integration (yfinance)
- [x] News sentiment analysis
- [x] Report generation with scoring
- [x] CLI interface
- [x] Streamlit Web UI
- [ ] Vector DB integration (ChromaDB)
- [ ] Earnings call transcript analysis
- [ ] Multi-ticker comparison reports
- [ ] Export to PDF/Word
- [ ] API server (FastAPI)
- [ ] Scheduled research alerts
- [ ] Portfolio analysis mode

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) — Agent orchestration
- [yfinance](https://github.com/ranaroussi/yfinance) — Market data
- [SEC EDGAR](https://www.sec.gov/edgar) — Financial filings
- [Tavily](https://tavily.com/) — AI-powered search

---

<p align="center">
  Built with 🧠 by <a href="https://github.com/YOUR_USERNAME">Your Name</a><br/>
  If you find this useful, please consider giving it a ⭐!
</p>
