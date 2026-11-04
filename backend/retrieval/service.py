"""Search service for FR-2 (semantic retrieval) and FR-4 (exact citation).

The vector index only returns section ids and scores. The text shown to the user is
always read from SQLite, so the citation is the stored statute text and nothing else.
"""
import re
import uuid

from backend import config
from backend.db.database import get_connection

DISCLAIMER = (
    "এটি শুধুমাত্র আইনি তথ্য, আইনি পরামর্শ নয়। প্রয়োজনে যোগ্য আইনজীবী বা আইনি সহায়তা সংস্থার "
    "সঙ্গে যোগাযোগ করুন।"
)
AMENDMENT_NOTICE = (
    "এই পাঠ একটি নির্দিষ্ট তারিখের সংগৃহীত কপি; পরবর্তী সংশোধনী থাকতে পারে। "
    "সর্বশেষ পাঠের জন্য সরকারি পোর্টাল bdlaws.minlaw.gov.bd দেখুন।"
)
MAX_K = 10


class IndexNotBuiltError(Exception):
    pass


class IndexStaleError(Exception):
    pass


class SearchEngine:
    def __init__(self, embedder, index):
        self.embedder = embedder
        self.index = index

    def query(self, question: str, k: int, act_id: int | None):
        if self.index.count() == 0:
            raise IndexNotBuiltError(
                "The search index is empty. Run backend/scripts/05_build_embedding_index.py."
            )
        return self.index.query(self.embedder.embed_query(question), k, act_id)


_engine: SearchEngine | None = None


def get_engine() -> SearchEngine:
    global _engine
    if _engine is None:
        from backend.retrieval.embedder import SentenceTransformerEmbedder
        from backend.retrieval.index import ChromaIndex

        embedder = SentenceTransformerEmbedder()
        _engine = SearchEngine(embedder, ChromaIndex(config.CHROMA_DIR, embedder.model_name))
    return _engine


def set_engine(engine: SearchEngine | None) -> None:
    """Used by tests (and scripts) to plug in another embedder/index."""
    global _engine
    _engine = engine


def clean_session_id(value: str | None) -> str:
    if value and re.fullmatch(r"[A-Za-z0-9-]{8,64}", value):
        return value
    return uuid.uuid4().hex  # random, not linked to a person (SRS 7.4)


def _fetch_sections(ids: list[int]) -> dict[int, dict]:
    marks = ",".join("?" * len(ids))
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT s.section_id, s.section_number, s.title, s.chapter, s.section_text, "
            "a.act_id, a.act_name, a.act_year, a.source_url, sn.snapshot_date "
            "FROM section s JOIN act a ON a.act_id = s.act_id "
            "JOIN snapshot sn ON sn.snapshot_id = s.snapshot_id "
            f"WHERE s.section_id IN ({marks})",
            ids,
        ).fetchall()
    return {r["section_id"]: dict(r) for r in rows}


def search(
    question: str,
    k: int | None = None,
    act_id: int | None = None,
    session_id: str | None = None,
    log: bool = True,
    engine: SearchEngine | None = None,
) -> dict:
    k = max(1, min(k or config.TOP_K_DEFAULT, MAX_K))
    hits = (engine or get_engine()).query(question, k, act_id)
    sections = _fetch_sections([sid for sid, _ in hits]) if hits else {}

    results = []
    for sid, score in hits:
        row = sections.get(sid)
        if row is None:
            continue  # index and database are out of sync for this id
        results.append(
            {
                "rank": len(results) + 1,
                "score": score,
                "section_id": sid,
                "act_id": row["act_id"],
                "act_name": row["act_name"],
                "act_year": row["act_year"],
                "chapter": row["chapter"],
                "section_number": row["section_number"],
                "title": row["title"],
                "text": row["section_text"],
                "source_url": row["source_url"],
            }
        )
    if hits and not results:
        raise IndexStaleError("The index does not match the database. Rebuild the index.")

    best = results[0]["score"] if results else None
    snapshot_date = sections[hits[0][0]]["snapshot_date"] if results else None

    query_id = None
    if log:
        with get_connection() as conn:
            query_id = conn.execute(
                "INSERT INTO query_log (session_id, input_type, query_text, retrieval_score) "
                "VALUES (?, 'question', ?, ?)",
                (clean_session_id(session_id), question, best),
            ).lastrowid
            conn.executemany(
                "INSERT INTO retrieval_result (log_id, section_id, rank, score) VALUES (?, ?, ?, ?)",
                [(query_id, r["section_id"], r["rank"], r["score"]) for r in results],
            )

    return {
        "query_id": query_id,
        "question": question,
        "best_score": best,
        "snapshot_date": snapshot_date,
        "results": results,
        "disclaimer": DISCLAIMER,
        "amendment_notice": AMENDMENT_NOTICE,
    }
