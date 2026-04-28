"""
Vector Store — simple local vector storage using NumPy.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional, Tuple

import numpy as np


class VectorStore:
    """
    Simple local vector store using NumPy for nearest-neighbor search.

    For production use, consider ChromaDB, FAISS, or pgvector.

    Usage:
        store = VectorStore("./data/vectorstore")
        store.add("doc1", [0.1, 0.2, ...], {"source": "sec_filing"})
        results = store.search([0.1, 0.2, ...], top_k=5)
    """

    def __init__(self, persist_dir: str = "./data/vectorstore"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._vectors: Optional[np.ndarray] = None
        self._ids: List[str] = []
        self._metadata: List[dict] = []
        self._load()

    def add(
        self,
        doc_id: str,
        vector: List[float],
        metadata: Optional[dict] = None,
    ) -> None:
        """Add a document to the store."""
        vec = np.array(vector, dtype=np.float32)
        if vec.ndim != 1:
            raise ValueError("Vector must be 1-dimensional")

        if self._vectors is None:
            self._vectors = vec.reshape(1, -1)
        else:
            if vec.shape[0] != self._vectors.shape[1]:
                raise ValueError(
                    f"Vector dimension mismatch: expected {self._vectors.shape[1]}, got {vec.shape[0]}"
                )
            self._vectors = np.vstack([self._vectors, vec])

        self._ids.append(doc_id)
        self._metadata.append(metadata or {})

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> List[Tuple[str, float, dict]]:
        """
        Search for similar vectors.

        Args:
            query_vector: Query embedding
            top_k: Number of results
            threshold: Minimum similarity score

        Returns:
            List of (doc_id, score, metadata) tuples
        """
        if self._vectors is None or len(self._ids) == 0:
            return []

        query = np.array(query_vector, dtype=np.float32)

        # Cosine similarity
        norms = np.linalg.norm(self._vectors, axis=1)
        query_norm = np.linalg.norm(query)
        if query_norm == 0:
            return []

        similarities = self._vectors @ query / (norms * query_norm)

        # Filter and sort
        results = []
        for idx in np.argsort(-similarities):
            score = float(similarities[idx])
            if score < threshold:
                continue
            results.append((self._ids[idx], score, self._metadata[idx]))
            if len(results) >= top_k:
                break

        return results

    def delete(self, doc_id: str) -> bool:
        """Delete a document by ID."""
        if doc_id not in self._ids:
            return False

        idx = self._ids.index(doc_id)
        self._ids.pop(idx)
        self._metadata.pop(idx)
        if self._vectors is not None:
            self._vectors = np.delete(self._vectors, idx, axis=0)
        return True

    def save(self) -> None:
        """Persist the store to disk."""
        if self._vectors is not None:
            np.save(self.persist_dir / "vectors.npy", self._vectors)
        with open(self.persist_dir / "metadata.json", "w") as f:
            json.dump({"ids": self._ids, "metadata": self._metadata}, f)

    def _load(self) -> None:
        """Load the store from disk."""
        vec_path = self.persist_dir / "vectors.npy"
        meta_path = self.persist_dir / "metadata.json"

        if vec_path.exists():
            self._vectors = np.load(vec_path)
        if meta_path.exists():
            with open(meta_path) as f:
                data = json.load(f)
                self._ids = data["ids"]
                self._metadata = data["metadata"]

    @property
    def count(self) -> int:
        return len(self._ids)

    def __len__(self) -> int:
        return self.count
