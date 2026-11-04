"""Build the vector index from the sections stored in SQLite."""
from backend.db.database import get_connection

EMBED_BODY_CHARS = 1500  # the model reads at most ~512 tokens, so the start of the text matters most


def passage_text(title: str | None, chapter: str | None, text: str) -> str:
    """Text that is embedded. Only real statute content: title, chapter, start of the body."""
    parts = []
    if title and not title.startswith("("):
        parts.append(title)
    if chapter:
        parts.append(chapter)
    parts.append(text[:EMBED_BODY_CHARS])
    return "\n".join(parts)


def build_index(embedder, index) -> int:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT section_id, act_id, section_number, title, chapter, section_text "
            "FROM section WHERE is_indexed = 1 ORDER BY section_id"
        ).fetchall()
    if not rows:
        raise RuntimeError("No sections in the database. Run 04_load_chunks_to_sqlite.py first.")

    texts = [passage_text(r["title"], r["chapter"], r["section_text"]) for r in rows]
    vectors = embedder.embed_passages(texts)
    index.reset()
    index.add(
        ids=[str(r["section_id"]) for r in rows],
        embeddings=vectors,
        metadatas=[
            {"act_id": r["act_id"], "section_number": r["section_number"]} for r in rows
        ],
    )
    return len(rows)
