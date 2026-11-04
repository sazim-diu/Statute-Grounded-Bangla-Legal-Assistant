"""Load the cleaned statute sections into SQLite (tables: snapshot, act, section)."""
import json
from pathlib import Path

from backend.db.database import get_connection, init_db
from backend.retrieval.data_cleaning import clean_chunks

DEFAULT_ACT = {
    "act_name": "বাংলাদেশ শ্রম আইন, ২০০৬",
    "act_year": 2006,
    "source_url": "https://bdlaws.minlaw.gov.bd/act-details-952.html",
}


class SectionsAlreadyLoadedError(Exception):
    pass


def load_chunks(
    chunks: list[dict],
    snapshot_date: str,
    act: dict | None = None,
    rebuild: bool = False,
    index_version: str = "chunks-v1",
) -> dict:
    """Clean `chunks` and store them. Returns the data-quality report."""
    act = act or DEFAULT_ACT
    records, report = clean_chunks(chunks)
    init_db()
    with get_connection() as conn:
        existing = conn.execute("SELECT COUNT(*) FROM section").fetchone()[0]
        if existing and not rebuild:
            raise SectionsAlreadyLoadedError(
                f"{existing} sections are already loaded. Use --rebuild to replace them."
            )
        if existing:
            conn.execute("DELETE FROM retrieval_result")
            conn.execute("DELETE FROM section")
            conn.execute("DELETE FROM act")
            conn.execute("DELETE FROM snapshot")

        act_id = conn.execute(
            "INSERT INTO act (act_name, act_year, source_url) VALUES (?, ?, ?)",
            (act["act_name"], act.get("act_year"), act.get("source_url")),
        ).lastrowid
        snapshot_id = conn.execute(
            "INSERT INTO snapshot (snapshot_date, index_version) VALUES (?, ?)",
            (snapshot_date, index_version),
        ).lastrowid
        conn.executemany(
            "INSERT INTO section (act_id, snapshot_id, chapter, section_number, title, "
            "section_text, legal_status, amendment_note, data_flags, is_indexed, source_chunk_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    act_id, snapshot_id, r["chapter"], r["section_number"], r["title"],
                    r["text"], r["legal_status"], r["amendment_note"],
                    ",".join(r["flags"]), 1 if r["is_indexed"] else 0, r["source_chunk_id"],
                )
                for r in records
            ],
        )
    report["act_id"] = act_id
    report["snapshot_date"] = snapshot_date
    return report


def load_chunks_file(path: str | Path, snapshot_date: str, rebuild: bool = False) -> dict:
    chunks = json.loads(Path(path).read_text(encoding="utf-8"))
    return load_chunks(chunks, snapshot_date, rebuild=rebuild)
