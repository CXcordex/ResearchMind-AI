import sqlite3, os
from contextlib import contextmanager
from passlib.context import CryptContext

DB_PATH  = os.getenv("DB_PATH", "research_store.db")
pwd_ctx  = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

@contextmanager
def db_cursor():
    conn = get_conn()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL UNIQUE,
    full_name     TEXT    NOT NULL,
    password_hash TEXT    NOT NULL,      -- bcrypt hash via passlib
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    last_login    TEXT
);

CREATE TABLE IF NOT EXISTS research_sessions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    topic         TEXT    NOT NULL,
    queries       TEXT,          -- JSON array: ["q1", "q2", ...]
    sources       TEXT,          -- JSON array: validated_sources objects
    evidence      TEXT,          -- JSON array: evidence objects
    report        TEXT,          -- Full Markdown report (Synthesizer output)
    elapsed_sec   REAL,          -- Pipeline wall-clock time
    model_used    TEXT,          -- NVIDIA NIM model string
    temperature   REAL,          -- Slider value used
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_rs_user
    ON research_sessions(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS document_sessions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    filename      TEXT    NOT NULL,
    file_size_kb  REAL,
    mime_type     TEXT,
    full_text     TEXT,          -- OCR-extracted full text (cap: 8 000 chars)
    summary       TEXT,          -- 3-paragraph executive summary
    key_findings  TEXT,          -- Newline-separated findings list
    key_topics    TEXT,          -- JSON array of topic strings
    metadata_info TEXT,          -- Document type, date, authors
    question      TEXT,          -- Original question provided by user (if any)
    answer        TEXT,          -- Answer to original question (same API call)
    model_used    TEXT,          -- OpenRouter model string
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_ds_user
    ON document_sessions(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS chat_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    role          TEXT    NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content       TEXT    NOT NULL,
    session_tag   TEXT    NOT NULL,   -- UUID generated when chat opens; resets on logout
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_ch_user
    ON chat_history(user_id, session_tag, created_at);
"""

def init_db():
    """Called once at app startup."""
    with db_cursor() as cur:
        cur.executescript(SCHEMA_SQL)

# ── Auth ──
def create_user(email, full_name, password):
    h = pwd_ctx.hash(password)
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO users (email, full_name, password_hash) VALUES (?,?,?)",
            (email.lower(), full_name, h)
        )

def verify_login(email, password) -> dict | None:
    with db_cursor() as cur:
        row = cur.execute(
            "SELECT id, email, full_name, password_hash FROM users WHERE email=?",
            (email.lower(),)
        ).fetchone()
    if not row:
        return None
    try:
        if pwd_ctx.verify(password, row["password_hash"]):
            return dict(row)
    except Exception:
        return None
    return None

# ── Research ──
def save_research(user_id, topic, queries, sources, evidence, report, elapsed, model, temp):
    import json
    with db_cursor() as cur:
        cur.execute(
            """INSERT INTO research_sessions
               (user_id,topic,queries,sources,evidence,report,elapsed_sec,model_used,temperature)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (user_id, topic,
             json.dumps(queries), json.dumps(sources), json.dumps(evidence),
             report, elapsed, model, temp)
        )

def get_latest_research(user_id) -> dict | None:
    with db_cursor() as cur:
        row = cur.execute(
            "SELECT topic,report,sources,evidence FROM research_sessions "
            "WHERE user_id=? ORDER BY created_at DESC LIMIT 1", (user_id,)
        ).fetchone()
    return dict(row) if row else None

# ── Document ──
def save_document(user_id, filename, file_size_kb, mime, full_text, summary,
                  key_findings, key_topics, metadata_info, question, answer, model):
    import json
    with db_cursor() as cur:
        cur.execute(
            """INSERT INTO document_sessions
               (user_id,filename,file_size_kb,mime_type,full_text,summary,
                key_findings,key_topics,metadata_info,question,answer,model_used)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (user_id, filename, file_size_kb, mime,
             full_text[:8000], summary, key_findings,
             json.dumps(key_topics) if isinstance(key_topics, list) else key_topics,
             metadata_info, question, answer, model)
        )

def get_latest_document(user_id) -> dict | None:
    with db_cursor() as cur:
        row = cur.execute(
            "SELECT filename,full_text,summary,key_findings FROM document_sessions "
            "WHERE user_id=? ORDER BY created_at DESC LIMIT 1", (user_id,)
        ).fetchone()
    return dict(row) if row else None

# ── Chat ──
def save_chat_msg(user_id, role, content, session_tag):
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO chat_history (user_id,role,content,session_tag) VALUES (?,?,?,?)",
            (user_id, role, content, session_tag)
        )

def get_chat_history(user_id, session_tag, limit=12) -> list:
    with db_cursor() as cur:
        rows = cur.execute(
            "SELECT role,content FROM chat_history "
            "WHERE user_id=? AND session_tag=? "
            "ORDER BY created_at DESC LIMIT ?",
            (user_id, session_tag, limit)
        ).fetchall()
    return [dict(r) for r in reversed(rows)]
