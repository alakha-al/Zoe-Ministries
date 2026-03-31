import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "zoe-leadgen.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist yet."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword     TEXT,
                source      TEXT,
                name        TEXT,
                email       TEXT,
                phone       TEXT,
                whatsapp    TEXT,
                location    TEXT,
                website     TEXT,
                twitter     TEXT,
                instagram   TEXT,
                facebook    TEXT,
                linkedin    TEXT,
                youtube     TEXT,
                raw_title   TEXT,
                contacted   INTEGER DEFAULT 0,
                contacted_at TEXT,
                scraped_at  TEXT DEFAULT (datetime('now')),
                UNIQUE(email, website)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                keywords    TEXT,
                sources     TEXT,
                volume      INTEGER,
                email       TEXT,
                status      TEXT DEFAULT 'running',
                lead_count  INTEGER DEFAULT 0,
                error       TEXT DEFAULT '',
                created_at  TEXT DEFAULT (datetime('now')),
                finished_at TEXT
            )
        """)
        conn.commit()
    print("[db] Tables ready.")


def create_job(keywords, sources, volume, email):
    """Insert a new job record and return its id."""
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO jobs (keywords, sources, volume, email) VALUES (?,?,?,?)",
            (
                ",".join(keywords) if isinstance(keywords, list) else keywords,
                ",".join(sources)  if isinstance(sources,  list) else sources,
                volume,
                email,
            ),
        )
        conn.commit()
        return cur.lastrowid


def update_job(job_id, status, lead_count=0, error=""):
    """Update a job's status and lead count when it finishes."""
    with _connect() as conn:
        conn.execute(
            """UPDATE jobs
               SET status=?, lead_count=?, error=?,
                   finished_at=datetime('now')
               WHERE id=?""",
            (status, lead_count, error, job_id),
        )
        conn.commit()


def get_job(job_id):
    """Return a job row as a dict, or None."""
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return dict(row) if row else None


def insert_lead(lead_dict, job_id=None):
    """
    Insert one lead.  Silently skips duplicates (same email+website).
    Returns the new row id, or None if skipped.
    """
    fields = [
        "keyword", "source", "name", "email", "phone", "whatsapp",
        "location", "website", "twitter", "instagram", "facebook",
        "linkedin", "youtube", "raw_title",
    ]
    values = [lead_dict.get(f, "") for f in fields]
    placeholders = ",".join(["?"] * len(fields))
    col_names    = ",".join(fields)

    with _connect() as conn:
        try:
            cur = conn.execute(
                f"INSERT INTO leads ({col_names}) VALUES ({placeholders})",
                values,
            )
            conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return None   # duplicate — skip silently


def get_leads(job_id=None, source=None, has_email=False, limit=500, offset=0):
    """
    Return leads as a list of dicts.
    Optionally filter by source or require an email address.
    """
    query  = "SELECT * FROM leads WHERE 1=1"
    params = []

    if source:
        query += " AND source=?"
        params.append(source)
    if has_email:
        query += " AND email != ''"

    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params += [limit, offset]

    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_leads_for_job(job_id):
    """Return all leads scraped during a specific job (matched by keyword/source in jobs table)."""
    job = get_job(job_id)
    if not job:
        return []
    # For now return most-recent leads up to job volume
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM leads ORDER BY id DESC LIMIT ?",
            (job["volume"],),
        ).fetchall()
        return [dict(r) for r in rows]


def update_lead(lead_id, fields):
    """Update arbitrary fields on a lead. fields is a dict."""
    if not fields:
        return
    set_clause = ", ".join(f"{k}=?" for k in fields)
    values     = list(fields.values()) + [lead_id]
    with _connect() as conn:
        conn.execute(f"UPDATE leads SET {set_clause} WHERE id=?", values)
        conn.commit()


def delete_lead(lead_id):
    """Hard-delete a lead by id."""
    with _connect() as conn:
        conn.execute("DELETE FROM leads WHERE id=?", (lead_id,))
        conn.commit()


def log_email_sent(lead_id):
    """Mark a lead as contacted with the current timestamp."""
    with _connect() as conn:
        conn.execute(
            "UPDATE leads SET contacted=1, contacted_at=datetime('now') WHERE id=?",
            (lead_id,),
        )
        conn.commit()


def count_leads():
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
