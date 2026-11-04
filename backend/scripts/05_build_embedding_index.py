"""Embed every searchable section and store the vectors in ChromaDB.

Run after 04_load_chunks_to_sqlite.py. The first run downloads the embedding model
(multilingual-e5-base is about 1 GB) and needs internet.

Usage: python backend/scripts/05_build_embedding_index.py
Use another model:  EMBEDDING_MODEL=BAAI/bge-m3 python backend/scripts/05_build_embedding_index.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend import config  # noqa: E402
from backend.retrieval.embedder import SentenceTransformerEmbedder  # noqa: E402
from backend.retrieval.index import ChromaIndex  # noqa: E402
from backend.retrieval.indexer import build_index  # noqa: E402


def main() -> None:
    embedder = SentenceTransformerEmbedder()
    index = ChromaIndex(config.CHROMA_DIR, embedder.model_name)
    print(f"Model: {embedder.model_name}")
    start = time.time()
    count = build_index(embedder, index)
    print(f"Indexed {count} sections in {time.time() - start:.0f}s -> {config.CHROMA_DIR}")


if __name__ == "__main__":
    main()
