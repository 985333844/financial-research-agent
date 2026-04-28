"""
Financial Research Agent (FinRA)
An open-source autonomous AI agent for deep financial research.
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from finra.agent.orchestrator import ResearchAgent
from finra.report.generator import ResearchReport

__all__ = ["ResearchAgent", "ResearchReport"]
