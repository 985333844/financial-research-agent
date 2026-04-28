"""Tests for the RAG system."""

from __future__ import annotations

from finra.rag.retriever import HybridRetriever
from finra.rag.vectorstore import VectorStore


class TestHybridRetriever:
    """Tests for the hybrid retriever."""

    def test_basic_retrieval(self):
        """Test basic document retrieval."""
        retriever = HybridRetriever()
        retriever.add_documents([
            "Apple reported record revenue of $120 billion driven by iPhone sales",
            "Google cloud revenue grew 35% year over year",
            "Microsoft Azure AI services saw strong adoption in enterprise",
        ])

        results = retriever.retrieve("Apple revenue iPhone", top_k=2)
        assert len(results) >= 1
        # Apple document should rank first
        assert results[0][0] == 0

    def test_empty_retriever(self):
        """Test retrieval from empty store."""
        retriever = HybridRetriever()
        results = retriever.retrieve("test query", top_k=5)
        assert results == []

    def test_tokenization(self):
        """Test tokenization."""
        tokens = HybridRetriever._tokenize("Hello World 123! This is a TEST.")
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens


class TestVectorStore:
    """Tests for the local vector store."""

    def test_add_and_search(self):
        """Test adding and searching vectors."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(tmpdir)

            store.add("doc1", [1.0, 0.0, 0.0], {"source": "test"})
            store.add("doc2", [0.0, 1.0, 0.0], {"source": "test"})
            store.add("doc3", [0.9, 0.1, 0.0], {"source": "test"})

            results = store.search([1.0, 0.0, 0.0], top_k=2)
            assert len(results) >= 1
            assert results[0][0] == "doc1"  # Exact match

    def test_delete(self):
        """Test deleting a document."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(tmpdir)
            store.add("doc1", [1.0, 0.0, 0.0])

            assert store.delete("doc1") is True
            assert store.count == 0
            assert store.delete("nonexistent") is False

    def test_persistence(self):
        """Test saving and loading the store."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            store1 = VectorStore(tmpdir)
            store1.add("doc1", [1.0, 0.0, 0.0], {"key": "value"})
            store1.save()

            store2 = VectorStore(tmpdir)
            assert store2.count == 1
            assert store2._ids[0] == "doc1"
