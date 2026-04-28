"""
SEC Filing Tool — retrieves and parses SEC filings from EDGAR.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup

from finra.config import settings

EDGAR_BASE = "https://www.sec.gov"
SEARCH_URL = f"{EDGAR_BASE}/cgi-bin/browse-edgar"
FILING_URL = f"{EDGAR_BASE}/Archives/edgar/data"


async def search_filings(
    ticker: str,
    filing_type: str = "10-K",
    count: int = 5,
) -> list[dict[str, str]]:
    """
    Search for SEC filings for a given ticker.

    Args:
        ticker: Stock ticker symbol
        filing_type: Type of filing (10-K, 10-Q, 8-K, DEF 14A)
        count: Number of results to return

    Returns:
        List of filing metadata dicts
    """
    headers = {
        "User-Agent": settings.data_sources.sec_user_agent,
        "Accept": "application/json",
    }

    params = {
        "action": "getcompany",
        "company": ticker,
        "type": filing_type,
        "dateb": "",
        "owner": "exclude",
        "count": count,
        "search_text": "",
        "output": "atom",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(SEARCH_URL, params=params, headers=headers)
        resp.raise_for_status()

    filings = []
    soup = BeautifulSoup(resp.text, "xml")

    for entry in soup.find_all("entry"):
        title = entry.find("title")
        link = entry.find("link", rel="alternate")
        updated = entry.find("updated")
        summary = entry.find("summary")

        if title and link:
            filings.append({
                "title": title.text.strip(),
                "filing_type": filing_type,
                "link": link.get("href", ""),
                "date": updated.text.strip() if updated else "",
                "summary": summary.text.strip()[:200] if summary else "",
            })

    return filings


async def get_latest_filing(
    ticker: str,
    filing_type: str = "10-K",
) -> Optional[dict[str, Any]]:
    """
    Get the most recent filing of a given type.

    Args:
        ticker: Stock ticker symbol
        filing_type: Type of filing

    Returns:
        Filing content dict or None
    """
    filings = await search_filings(ticker, filing_type, count=1)
    if not filings:
        return None

    filing = filings[0]
    filing_url = filing["link"]

    headers = {"User-Agent": settings.data_sources.sec_user_agent}

    async with httpx.AsyncClient(timeout=30.0) as client:
        # First get the filing index page
        resp = await client.get(filing_url, headers=headers)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Find the document link (usually ends with .htm)
        doc_link = None
        for table in soup.find_all("table", class_="tableFile2"):
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 3:
                    doc_type = cells[0].text.strip()
                    if doc_type in (filing_type, f"{filing_type} (Annual Report)"):
                        href = cells[2].find("a")
                        if href and href.get("href"):
                            doc_link = href["href"]
                            break

        if not doc_link:
            # Fallback: find any .htm file
            for a in soup.find_all("a", href=True):
                if a["href"].endswith(".htm") and "ix?doc=" in a["href"]:
                    doc_link = a["href"]
                    break

        if not doc_link:
            return {"meta": filing, "content": "", "sections": {}}

        # Resolve relative URLs
        if doc_link.startswith("/"):
            doc_link = f"{EDGAR_BASE}{doc_link}"

        # Fetch the actual document
        resp = await client.get(doc_link, headers=headers)
        resp.raise_for_status()

        content = resp.text

        # Parse sections
        sections = _parse_filing_sections(content, filing_type)

        return {
            "meta": filing,
            "content": content,
            "sections": sections,
            "url": doc_link,
        }


def _parse_filing_sections(html_content: str, filing_type: str) -> dict[str, str]:
    """
    Parse a filing HTML into named sections.

    This is a simplified parser — a production system would use
    XBRL or a more sophisticated approach.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator="\n")

    sections = {}

    # Common section headers in SEC filings
    section_patterns = {
        "business": r"(?i)(ITEM\s*1[.)\s]*\s*B[Uu][Ss][Ii][Nn][Ee][Ss][Ss])",
        "risk_factors": r"(?i)(ITEM\s*1[AC][.)\s]*\s*R[Ii][Ss][Kk])",
        "mda": r"(?i)(ITEM\s*7[.)\s]*\s*M[An][Nn][Aa][Gg][Ee])",
        "financial_statements": r"(?i)(ITEM\s*8[.)\s]*\s*F[In][Ii][Nn][Aa])",
        "quantitative_disclosures": r"(?i)(ITEM\s*7A[.)\s])",
    }

    for section_name, pattern in section_patterns.items():
        match = re.search(pattern, text)
        if match:
            start = match.start()
            # Find the next section start
            remaining = text[start + 50:]
            next_section = re.search(r"(?i)ITEM\s*\d+[A-C]?[.)\s]", remaining)
            end = start + 50 + next_section.start() if next_section else start + 5000
            sections[section_name] = text[start:end].strip()[:3000]  # Limit per section

    return sections
