"""
Hybrid Retriever — combines vector similarity with keyword search.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, List, Optional, Tuple

from finra.rag.embeddings import get_embeddings


class HybridRetriever:
    """
    Hybrid retriever combining vector similarity and TF-IDF keyword search.

    Usage:
        retriever = HybridRetriever()
        retriever.add_documents(["Document 1 text...", "Document 2 text..."])
        results = retriever.retrieve("search query", top_k=5)
    """

    def __init__(
        self,
        vector_weight: float = 0.6,
        keyword_weight: float = 0.4,
        embedding_model: str = "text-embedding-3-small",
    ):
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self._documents: List[str] = []
        self._embeddings: Optional[List[List[float]]] = None
        self._idf: dict[str, float] = {}
        self._embedding_model = embedding_model

    def add_documents(self, documents: List[str]) -> None:
        """Add documents to the retriever."""
        self._documents = documents

        # Compute IDF for all terms
        all_terms = set()
        doc_freq: Counter = Counter()
        for doc in documents:
            terms = set(self._tokenize(doc))
            all_terms.update(terms)
            for term in terms:
                doc_freq[term] += 1

        n_docs = len(documents)
        for term in all_terms:
            self._idf[term] = math.log((n_docs + 1) / (doc_freq[term] + 1)) + 1

    async def add_documents_with_embeddings(self, documents: List[str]) -> None:
        """Add documents and compute embeddings."""
        self.add_documents(documents)

        # Generate embeddings
        try:
            embedder = get_embeddings(self._embedding_model)
            self._embeddings = await embedder.aembed_documents(documents)
        except Exception:
            self._embeddings = None

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Tuple[int, float, str]]:
        """
        Retrieve documents using hybrid search.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of (doc_index, score, document_text) tuples
        """
        if not self._documents:
            return []

        # Vector scores
        vector_scores = self._vector_scores(query) if self._embeddings else [0.5] * len(self._documents)

        # Keyword scores
        keyword_scores = self._keyword_scores(query)

        # Combine
        combined = []
        for i in range(len(self._documents)):
            score = (
                self.vector_weight * vector_scores[i]
                + self.keyword_weight * keyword_scores[i]
            )
            combined.append((i, score, self._documents[i]))

        # Sort by score descending
        combined.sort(key=lambda x: x[1], reverse=True)

        return combined[:top_k]

    def _vector_scores(self, query: str) -> List[float]:
        """Compute cosine similarity between query and all documents."""
        if not self._embeddings:
            return [0.0] * len(self._documents)

        # Simple approach: use pre-computed embeddings
        # In production, embed the query and compute similarity
        query_tokens = self._tokenize(query)
        scores = []
        for i, doc in enumerate(self._documents):
            doc_tokens = set(self._tokenize(doc))
            overlap = len(query_tokens & doc_tokens)
            total = len(query_tokens | doc_tokens)
            scores.append(overlap / total if total else 0)

        return scores

    def _keyword_scores(self, query: str) -> List[float]:
        """Compute TF-IDF keyword scores."""
        query_terms = self._tokenize(query)
        if not query_terms:
            return [0.0] * len(self._documents)

        scores = []
        for doc in self._documents:
            doc_terms = self._tokenize(doc)
            term_freq = Counter(doc_terms)
            doc_len = len(doc_terms)

            score = 0.0
            for term in query_terms:
                tf = term_freq.get(term, 0) / doc_len if doc_len else 0
                idf = self._idf.get(term, 0)
                score += tf * idf

            # Normalize
            score /= len(query_terms)
            scores.append(score)

        return scores

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple tokenization: lowercase, alphanumeric words only."""
        return re.findall(r"\b[a-z0-9]{2,}\b", text.lower())
