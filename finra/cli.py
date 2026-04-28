"""
CLI Interface for Financial Research Agent.

Usage:
    python -m finra.cli --ticker AAPL --query "Should I invest in Apple?"
    python -m finra.cli --ticker MSFT --depth deep --output report.md
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from finra import ResearchAgent, ResearchReport
from finra.config import validate_config

console = Console()


@click.command()
@click.option("--ticker", "-t", required=True, help="Stock ticker symbol (e.g., AAPL)")
@click.option("--query", "-q", required=True, help="Research question or topic")
@click.option("--depth", "-d", default="standard", type=click.Choice(["quick", "standard", "deep"]), help="Research depth")
@click.option("--output", "-o", default=None, help="Output file path (e.g., report.md)")
@click.option("--format", "-f", "fmt", default="markdown", type=click.Choice(["markdown", "json"]), help="Output format")
@click.option("--no-stream", is_flag=True, help="Disable streaming progress updates")
def main(
    ticker: str,
    query: str,
    depth: str,
    output: Optional[str],
    fmt: str,
    no_stream: bool,
) -> None:
    """🔍 Financial Research Agent — AI-powered investment research."""
    # Validate config
    warnings = validate_config()
    for w in warnings:
        console.print(f"[yellow]⚠ {w}[/yellow]")

    if any("API_KEY" in w for w in warnings):
        console.print("[red]Error: OPENAI_API_KEY is required. Set it in .env or environment.[/red]")
        sys.exit(1)

    # Header
    console.print()
    console.print(Panel(
        f"[bold blue]🔍 Financial Research Agent (FinRA)[/bold blue]\n\n"
        f"  Ticker: [bold]{ticker.upper()}[/bold]\n"
        f"  Query:  {query}\n"
        f"  Depth:  {depth}",
        title="FinRA v0.1.0",
        border_style="blue",
    ))
    console.print()

    # Run research
    agent = ResearchAgent()

    if no_stream:
        result = asyncio.run(_run_simple(agent, ticker, query, depth))
    else:
        result = asyncio.run(_run_streaming(agent, ticker, query, depth))

    # Output results
    if fmt == "json":
        _output_json(result, output)
    else:
        _output_markdown(result, ticker, query, output)

    console.print("[green]✅ Research complete![/green]")


async def _run_simple(agent, ticker, query, depth):
    """Run without streaming."""
    with console.status("[bold green]Running research pipeline..."):
        result = await agent.research(ticker=ticker, query=query, depth=depth)
    return result


async def _run_streaming(agent, ticker, query, depth):
    """Run with streaming progress."""
    result = None

    with Live(console=console, refresh_per_second=4) as live:
        status_table = Table(show_header=False, box=None)
        status_table.add_column("Stage", style="cyan", width=20)
        status_table.add_column("Status", width=50)

        node_labels = {
            "planner": "📋 Planning research",
            "market_agent": "📊 Fetching market data",
            "sec_agent": "📄 Analyzing SEC filings",
            "news_agent": "📰 Analyzing news sentiment",
            "synthesis_agent": "📝 Generating report",
        }

        completed = []

        async for event in agent.research_stream(ticker=ticker, query=query, depth=depth):
            node = event.get("node", "")
            data = event.get("data", {})
            label = node_labels.get(node, node)

            if node not in completed:
                completed.append(node)

            # Update status table
            status_table.rows.clear()
            for n in completed:
                l = node_labels.get(n, n)
                status_table.add_row(l, "[green]✅ Complete[/green]")

            live.update(Panel(status_table, title="[bold]Research Progress[/bold]"))

            if node == "synthesis_agent":
                result = data

    # If streaming didn't capture the final state, run without streaming
    if result is None or not result.get("report_markdown"):
        result = await agent.research(ticker=ticker, query=query, depth=depth)

    return result


def _output_markdown(result, ticker, query, output):
    """Output results in Markdown format."""
    report = ResearchReport.from_agent_result(result)
    md = report.markdown()

    if output:
        path = report.save(output)
        console.print(f"\n[green]📄 Report saved to: {path}[/green]")
    else:
        console.print()
        console.print(Markdown(md))


def _output_json(result, output):
    """Output results in JSON format."""
    report = ResearchReport.from_agent_result(result)
    data = report.to_dict()

    json_str = json.dumps(data, indent=2, ensure_ascii=False)

    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json_str, encoding="utf-8")
        console.print(f"\n[green]📄 JSON saved to: {path}[/green]")
    else:
        console.print(json_str)


if __name__ == "__main__":
    main()
