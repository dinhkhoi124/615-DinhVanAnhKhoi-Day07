from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot, compute_similarity
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
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb

            # Initialize ephemeral ChromaDB client
            self._client = chromadb.EphemeralClient()
            self._collection = self._client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata) if doc.metadata is not None else {}
        if "doc_id" not in metadata:
            metadata["doc_id"] = doc.id
        embedding = self._embedding_fn(doc.content)
        return {
            "id": doc.id,
            "content": doc.content,
            "embedding": embedding,
            "metadata": metadata,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records:
            return []
        query_emb = self._embedding_fn(query)
        scored_records = []
        for r in records:
            score = compute_similarity(query_emb, r["embedding"])
            scored_records.append({
                "id": r["id"],
                "content": r["content"],
                "metadata": r["metadata"],
                "score": score
            })
        scored_records.sort(key=lambda x: x["score"], reverse=True)
        return scored_records[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        for doc in docs:
            if self._use_chroma and self._collection is not None:
                metadata = dict(doc.metadata) if doc.metadata is not None else {}
                if "doc_id" not in metadata:
                    metadata["doc_id"] = doc.id
                embedding = self._embedding_fn(doc.content)
                compat_metadata = {k: v for k, v in metadata.items() if isinstance(v, (str, int, float, bool))}
                self._collection.add(
                    ids=[f"{doc.id}_{self._next_index}"],
                    documents=[doc.content],
                    embeddings=[embedding],
                    metadatas=[compat_metadata]
                )
                self._next_index += 1
            else:
                record = self._make_record(doc)
                self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma and self._collection is not None:
            query_emb = self._embedding_fn(query)
            results = self._collection.query(
                query_embeddings=[query_emb],
                n_results=top_k,
                include=["documents", "metadatas", "embeddings"]
            )
            output = []
            if results and results.get("ids") and len(results["ids"]) > 0:
                ids = results["ids"][0]
                documents = results["documents"][0]
                metadatas = results["metadatas"][0]
                embeddings = results["embeddings"][0]
                for i in range(len(ids)):
                    score = compute_similarity(query_emb, embeddings[i])
                    output.append({
                        "id": ids[i],
                        "content": documents[i],
                        "metadata": metadatas[i],
                        "score": score
                    })
                output.sort(key=lambda x: x["score"], reverse=True)
            return output
        else:
            return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if self._use_chroma and self._collection is not None:
            query_emb = self._embedding_fn(query)
            where_clause = metadata_filter if metadata_filter else None
            results = self._collection.query(
                query_embeddings=[query_emb],
                n_results=top_k,
                where=where_clause,
                include=["documents", "metadatas", "embeddings"]
            )
            output = []
            if results and results.get("ids") and len(results["ids"]) > 0:
                ids = results["ids"][0]
                documents = results["documents"][0]
                metadatas = results["metadatas"][0]
                embeddings = results["embeddings"][0]
                for i in range(len(ids)):
                    score = compute_similarity(query_emb, embeddings[i])
                    output.append({
                        "id": ids[i],
                        "content": documents[i],
                        "metadata": metadatas[i],
                        "score": score
                    })
                output.sort(key=lambda x: x["score"], reverse=True)
            return output
        else:
            if not metadata_filter:
                filtered_records = self._store
            else:
                filtered_records = []
                for r in self._store:
                    match = True
                    for k, v in metadata_filter.items():
                        if r["metadata"].get(k) != v:
                            match = False
                            break
                    if match:
                        filtered_records.append(r)
            return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            results = self._collection.get(where={"doc_id": doc_id})
            deleted = False
            if results and results.get("ids"):
                self._collection.delete(where={"doc_id": doc_id})
                deleted = True
            
            results_by_id = self._collection.get(ids=[doc_id])
            if results_by_id and results_by_id.get("ids"):
                self._collection.delete(ids=[doc_id])
                deleted = True
            return deleted
        else:
            initial_len = len(self._store)
            self._store = [
                r for r in self._store
                if r["metadata"].get("doc_id") != doc_id and r["id"] != doc_id
            ]
            return len(self._store) < initial_len
