"""Embedding model wrapper (sentence-transformers). Loaded lazily because it is slow."""
from backend import config


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str | None = None, max_seq_length: int = 512):
        self.model_name = model_name or config.EMBEDDING_MODEL
        self.max_seq_length = max_seq_length
        self._model = None
        # e5 models were trained with these prefixes; other models (e.g. BGE-M3) use none.
        is_e5 = "e5" in self.model_name.lower()
        self._query_prefix = "query: " if is_e5 else ""
        self._passage_prefix = "passage: " if is_e5 else ""

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            self._model.max_seq_length = self.max_seq_length
        return self._model

    def embed_passages(self, texts: list[str], batch_size: int = 16) -> list[list[float]]:
        model = self._load()
        vectors = model.encode(
            [self._passage_prefix + t for t in texts],
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        model = self._load()
        vector = model.encode([self._query_prefix + text], normalize_embeddings=True)[0]
        return vector.tolist()
