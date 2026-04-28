# Contributing to Financial Research Agent

Thanks for your interest in contributing! 🎉

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/financial-research-agent.git`
3. Install in development mode: `pip install -e ".[dev]"`

## Development Setup

```bash
# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run with coverage
pytest --cov=finra tests/

# Lint and format
ruff check .
ruff format .
```

## Project Structure

- `finra/agent/` — Multi-agent orchestration (LangGraph)
- `finra/tools/` — Data retrieval tools (yfinance, SEC, news)
- `finra/agents/` — Specialized agents
- `finra/rag/` — RAG system
- `finra/report/` — Report generation and scoring

## Adding a New Agent

1. Create `finra/agents/your_agent.py`
2. Implement an async function `run_your_agent(state) -> YourResultType`
3. Add conditional routing in `finra/agent/orchestrator.py`
4. Add tests in `tests/`
5. Update the README

## Code Style

- Follow PEP 8 (enforced by ruff)
- Type hints on all public functions
- Docstrings on all modules and public functions
- Tests for new features

## Pull Request Process

1. Update documentation if needed
2. Add tests for new features
3. Ensure all tests pass: `pytest`
4. Update README.md if you change functionality
