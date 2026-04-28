"""
Configuration management for Financial Research Agent.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env file
load_dotenv()


@dataclass(frozen=True)
class LLMConfig:
    """LLM provider configuration."""

    model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o"))
    temperature: float = field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.1")))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "4096")))
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    anthropic_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY")
    )


@dataclass(frozen=True)
class DataSourceConfig:
    """Data source configuration."""

    tavily_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("TAVILY_API_KEY")
    )
    sec_user_agent: str = field(
        default_factory=lambda: os.getenv(
            "SEC_USER_AGENT", "Financial Research Agent/1.0 (research@example.com)"
        )
    )
    alpha_vantage_key: Optional[str] = field(
        default_factory=lambda: os.getenv("ALPHA_VANTAGE_KEY")
    )


@dataclass(frozen=True)
class StorageConfig:
    """Storage configuration."""

    vector_db_path: Path = field(
        default_factory=lambda: Path(os.getenv("VECTOR_DB_PATH", "./data/vectorstore"))
    )
    cache_dir: Path = field(
        default_factory=lambda: Path(os.getenv("CACHE_DIR", "./data/cache"))
    )
    cache_ttl: int = field(default_factory=lambda: int(os.getenv("CACHE_TTL", "3600")))
    output_dir: Path = field(
        default_factory=lambda: Path(os.getenv("OUTPUT_DIR", "./data/reports"))
    )


@dataclass(frozen=True)
class ResearchConfig:
    """Research pipeline configuration."""

    depth: str = field(default_factory=lambda: os.getenv("RESEARCH_DEPTH", "standard"))
    report_format: str = field(
        default_factory=lambda: os.getenv("REPORT_FORMAT", "markdown")
    )
    news_max_articles: int = field(
        default_factory=lambda: int(os.getenv("NEWS_MAX_ARTICLES", "10"))
    )
    technical_lookback_days: int = field(
        default_factory=lambda: int(os.getenv("TECHNICAL_LOOKBACK_DAYS", "180"))
    )
    max_research_iterations: int = 3


class Settings:
    """Global settings container."""

    llm: LLMConfig = field(default_factory=LLMConfig)  # type: ignore
    data_sources: DataSourceConfig = field(default_factory=DataSourceConfig)  # type: ignore
    storage: StorageConfig = field(default_factory=StorageConfig)  # type: ignore
    research: ResearchConfig = field(default_factory=ResearchConfig)  # type: ignore

    def __post_init__(self):
        # Ensure directories exist
        self.storage.vector_db_path.mkdir(parents=True, exist_ok=True)
        self.storage.cache_dir.mkdir(parents=True, exist_ok=True)
        self.storage.output_dir.mkdir(parents=True, exist_ok=True)


# Global singleton
settings = Settings()


def validate_config() -> list[str]:
    """Validate configuration and return list of warnings."""
    warnings = []
    if not settings.llm.openai_api_key:
        warnings.append("OPENAI_API_KEY not set — most features require an LLM key")
    if settings.research.depth not in ("quick", "standard", "deep"):
        warnings.append(
            f"Invalid RESEARCH_DEPTH '{settings.research.depth}', using 'standard'"
        )
    return warnings
