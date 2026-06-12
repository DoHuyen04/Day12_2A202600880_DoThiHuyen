from __future__ import annotations

from typing import Any, Callable

from .chunking import FixedSizeChunker, compute_similarity
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
        chunker: Any | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        # Split each document into chunks before embedding so retrieval works on
        # focused passages instead of whole files. Any object exposing
        # ``chunk(text) -> list[str]`` is accepted; default is fixed-size chunking.
        self._chunker = chunker or FixedSizeChunker()
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        # This lab uses a simple, deterministic in-memory store so results are
        # reproducible in class and tests. ChromaDB detection is kept for
        # reference, but all operations below run against self._store.
        try:
            import chromadb  # noqa: F401
        except Exception:
            pass
        self._use_chroma = False
        self._collection = None

    def _make_records(self, doc: Document) -> list[dict[str, Any]]:
        """Chunk one document and build a stored record (with embedding) per chunk."""
        chunks = self._chunker.chunk(doc.content) or [doc.content]
        records: list[dict[str, Any]] = []
        for chunk_index, chunk in enumerate(chunks):
            metadata = dict(doc.metadata) if doc.metadata else {}
            metadata.setdefault("doc_id", doc.id)
            metadata["chunk_id"] = chunk_index
            records.append(
                {
                    "doc_id": doc.id,
                    "content": chunk,
                    "embedding": self._embedding_fn(chunk),
                    "metadata": metadata,
                }
            )
            self._next_index += 1
        return records

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Rank the given records by similarity to query and return the top_k."""
        query_embedding = self._embedding_fn(query)
        scored: list[dict[str, Any]] = []
        for record in records:
            score = compute_similarity(query_embedding, record["embedding"])
            scored.append(
                {
                    "doc_id": record["doc_id"],
                    "content": record["content"],
                    "metadata": record["metadata"],
                    "score": score,
                }
            )
        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For in-memory: append normalized records to self._store.
        """
        for doc in docs:
            self._store.extend(self._make_records(doc))

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Find the top_k most similar documents to query."""
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self._search_records(query, self._store, top_k)

        candidates = [
            record
            for record in self._store
            if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
        ]
        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        before = len(self._store)
        self._store = [record for record in self._store if record["doc_id"] != doc_id]
        return len(self._store) < before
