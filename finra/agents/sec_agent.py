"""
SEC Filing Agent — retrieves and analyzes SEC filings.
"""

from __future__ import annotations

from typing import Any, Optional

from finra.agent.state import SECFilingAnalysis
from finra.tools.sec_filings import get_latest_filing, search_filings


async def run_sec_agent(ticker: str) -> Optional[SECFilingAnalysis]:
    """
    Run the SEC filing agent.

    Retrieves and analyzes the latest 10-K filing for the given ticker.

    Args:
        ticker: Stock ticker symbol

    Returns:
        SECFilingAnalysis object with findings
    """
    # Get latest 10-K
    filing = await get_latest_filing(ticker, "10-K")

    if not filing:
        # Try 10-Q as fallback
        filing = await get_latest_filing(ticker, "10-Q")

    if not filing:
        return None

    meta = filing.get("meta", {})
    sections = filing.get("sections", {})
    content = filing.get("content", "")

    analysis = SECFilingAnalysis(
        filing_type=meta.get("filing_type", "10-K"),
        filing_date=meta.get("date", ""),
        sections_analyzed=list(sections.keys()),
        raw_text_chunks=[sections[k] for k in sections if sections[k]],
    )

    # Extract key findings from available sections
    if "risk_factors" in sections:
        risk_text = sections["risk_factors"]
        # Extract top risk sentences (simplified)
        risk_sentences = [s.strip() for s in risk_text.split(".") if len(s.strip()) > 50]
        analysis.risk_factors = risk_sentences[:5]

    if "business" in sections:
        analysis.management_discussion = sections["business"][:2000]

    if "mda" in sections:
        analysis.management_discussion = sections["mda"][:2000]

    # Extract key findings from filing metadata
    analysis.key_findings = [
        f"Filed {analysis.filing_type} on {analysis.filing_date}",
        f"Sections analyzed: {', '.join(analysis.sections_analyzed) or 'full document'}",
    ]

    if analysis.risk_factors:
        analysis.key_findings.append(f"Identified {len(analysis.risk_factors)} key risk factors")

    if analysis.management_discussion:
        analysis.key_findings.append("Management discussion & analysis available")

    return analysis


def _format_sec_summary(analysis: SECFilingAnalysis) -> str:
    """Format SEC analysis into a readable summary."""
    lines = [
        f"## SEC Filing Analysis: {analysis.filing_type}",
        f"Filing Date: {analysis.filing_date}",
        "",
        "### Sections Analyzed",
        ", ".join(analysis.sections_analyzed) if analysis.sections_analyzed else "Full document",
        "",
    ]

    if analysis.key_findings:
        lines.append("### Key Findings")
        for finding in analysis.key_findings:
            lines.append(f"- {finding}")
        lines.append("")

    if analysis.risk_factors:
        lines.append("### Risk Factors (Top 5)")
        for i, risk in enumerate(analysis.risk_factors, 1):
            lines.append(f"{i}. {risk[:200]}...")
        lines.append("")

    if analysis.management_discussion:
        lines.append("### Management Discussion")
        lines.append(analysis.management_discussion[:1000] + "...")

    return "\n".join(lines)
