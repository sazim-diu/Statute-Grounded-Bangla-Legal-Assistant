"""SQLite connection helper and tiny schema migration."""
import sqlite3
from pathlib import Path

from backend import config

SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# Columns added after the first schema version. Older database files get them
# automatically, so nobody has to delete lexbangla.db.
_EXTRA_COLUMNS = {
    "section": [
        ("legal_status", "TEXT"),
        ("amendment_note", "TEXT"),
        ("data_flags", "TEXT"),
        ("is_indexed", "INTEGER NOT NULL DEFAULT 1"),
        ("source_chunk_id", "TEXT"),
    ]
}


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create all tables if they do not exist and add any missing columns."""
    with get_connection() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        for table, columns in _EXTRA_COLUMNS.items():
            existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
            for name, decl in columns:
                if name not in existing:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")


if __name__ == "__main__":
    init_db()
    print(f"Database ready at {config.DATABASE_PATH}")
