-- LexBangla schema (based on SRS Section 7.4 ERD, plus USERS for authentication)

CREATE TABLE IF NOT EXISTS users (
    user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    username       TEXT NOT NULL UNIQUE,
    password_hash  TEXT NOT NULL,
    role           TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS snapshot (
    snapshot_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date  TEXT NOT NULL,
    index_version  TEXT
);

CREATE TABLE IF NOT EXISTS act (
    act_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    act_name   TEXT NOT NULL,
    act_year   INTEGER,
    source_url TEXT
);

CREATE TABLE IF NOT EXISTS section (
    section_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    act_id          INTEGER NOT NULL REFERENCES act(act_id),
    snapshot_id     INTEGER NOT NULL REFERENCES snapshot(snapshot_id),
    chapter         TEXT,
    section_number  TEXT NOT NULL,
    title           TEXT,
    section_text    TEXT NOT NULL,
    -- added for the real data pipeline (see backend/retrieval/loader.py)
    legal_status    TEXT,
    amendment_note  TEXT,
    data_flags      TEXT,
    is_indexed      INTEGER NOT NULL DEFAULT 1,
    source_chunk_id TEXT
);

CREATE TABLE IF NOT EXISTS query_log (
    log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    input_type      TEXT,
    query_text      TEXT NOT NULL,
    issue_category  TEXT,
    retrieval_score REAL,
    evidence_status TEXT CHECK (evidence_status IN ('supported', 'partly_supported', 'not_supported')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS retrieval_result (
    log_id     INTEGER NOT NULL REFERENCES query_log(log_id),
    section_id INTEGER NOT NULL REFERENCES section(section_id),
    rank       INTEGER NOT NULL,
    score      REAL,
    PRIMARY KEY (log_id, section_id)
);

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_id      INTEGER NOT NULL REFERENCES query_log(log_id),
    rating      TEXT NOT NULL CHECK (rating IN ('helpful', 'not_helpful')),
    comment     TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_section_act ON section(act_id);
CREATE INDEX IF NOT EXISTS idx_retrieval_log ON retrieval_result(log_id);
CREATE INDEX IF NOT EXISTS idx_feedback_log ON feedback(log_id);
