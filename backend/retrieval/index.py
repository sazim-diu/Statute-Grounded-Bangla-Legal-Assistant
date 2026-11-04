"""Vector indexes. ChromaIndex is used for real; MemoryIndex is a tiny stand-in for tests.

Both expose the same methods so the search service does not care which one it gets.
Embeddings must be normalised, so cosine similarity = dot product.
"""
from pathlib import Path

COLLECTION_NAME = "lexbangla_sections"


class IndexMismatchError(Exception):
    """The index was built with a different embedding model than the one configured."""


class ChromaIndex:
    def __init__(self, path: str | Path, model_name: str):
        import chromadb

        self.model_name = model_name
        self._client = chromadb.PersistentClient(path=str(path))
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine", "embedding_model": model_name},
        )
        built_with = (self._collection.metadata or {}).get("embedding_model")
        if self._collection.count() and built_with and built_with != model_name:
            raise IndexMismatchError(
                f"Index was built with '{built_with}' but EMBEDDING_MODEL is '{model_name}'. "
                "Run backend/scripts/05_build_embedding_index.py again."
            )

    def reset(self) -> None:
        self._client.delete_collection(COLLECTION_NAME)
        self._collection = self._client.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine", "embedding_model": self.model_name},
        )

    def add(self, ids: list[str], embeddings: list[list[float]], metadatas: list[dict]) -> None:
        step = 200
        for i in range(0, len(ids), step):
            self._collection.add(
                ids=ids[i : i + step],
                embeddings=embeddings[i : i + step],
                metadatas=metadatas[i : i + step],
            )

    def count(self) -> int:
        return self._collection.count()

    def query(self, embedding: list[float], k: int, act_id: int | None = None):
        """Return [(section_id, similarity)] best first."""
        where = {"act_id": act_id} if act_id is not None else None
        res = self._collection.query(
            query_embeddings=[embedding],
            n_results=max(1, min(k, self.count() or 1)),
            where=where,
        )
        out = []
        for sid, dist in zip(res["ids"][0], res["distances"][0]):
            out.append((int(sid), round(1.0 - float(dist), 4)))
        return out


class MemoryIndex:
    def __init__(self, model_name: str = "memory"):
        self.model_name = model_name
        self._rows: list[tuple[str, list[float], dict]] = []

    def reset(self) -> None:
        self._rows = []

    def add(self, ids, embeddings, metadatas) -> None:
        self._rows.extend(zip(ids, embeddings, metadatas))

    def count(self) -> int:
        return len(self._rows)

    def query(self, embedding, k, act_id=None):
        scored = []
        for sid, vec, meta in self._rows:
            if act_id is not None and meta.get("act_id") != act_id:
                continue
            scored.append((int(sid), round(sum(a * b for a, b in zip(embedding, vec)), 4)))
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[:k]
