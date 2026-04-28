"""
Embedding generation — wraps multiple embedding providers.
"""

from __future__ import annotations

from typing import Any, List, Optional

from langchain_openai import OpenAIEmbeddings

from finra.config import settings


def get_embeddings(model: str = "text-embedding-3-small") -> OpenAIEmbeddings:
    """
    Get an embeddings instance.

    Args:
        model: Embedding model name

    Returns:
        LangChain OpenAIEmbeddings instance
    """
    return OpenAIEmbeddings(
        model=model,
        openai_api_key=settings.llm.openai_api_key,
    )
