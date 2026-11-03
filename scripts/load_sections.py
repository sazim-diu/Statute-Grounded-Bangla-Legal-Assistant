"""Load a statute JSON file (see data/sections/sample_format.json) into SQLite.

Usage: python scripts/load_sections.py data/sections/labour_act_2006.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.db.database import get_connection, init_db  # noqa: E402


def load(path: str) -> None:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    init_db()
    with get_connection() as conn:
        act = data["act"]
        cur = conn.execute(
            "INSERT INTO act (act_name, act_year, source_url) VALUES (?, ?, ?)",
            (act["act_name"], act.get("act_year"), act.get("source_url")),
        )
        act_id = cur.lastrowid
        cur = conn.execute(
            "INSERT INTO snapshot (snapshot_date, index_version) VALUES (?, ?)",
            (data["snapshot_date"], data.get("index_version", "v1")),
        )
        snapshot_id = cur.lastrowid
        rows = [
            (act_id, snapshot_id, s.get("chapter"), s["section_number"],
             s.get("title"), s["section_text"])
            for s in data["sections"]
        ]
        conn.executemany(
            "INSERT INTO section (act_id, snapshot_id, chapter, section_number, title, section_text)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            rows,
        )
    print(f"Loaded {len(rows)} sections for '{act['act_name']}'")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/load_sections.py <json-file>")
    load(sys.argv[1])
