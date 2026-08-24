"""
core/db.py

Local SQLite storage for parsed resumes and their scores against
job descriptions. Standard library only.
"""

from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / ".smart_resume_screener" / "screener.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            extracted_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS screenings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            job_title TEXT NOT NULL,
            job_description TEXT NOT NULL,
            score_breakdown_json TEXT NOT NULL,
            justification TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (candidate_id) REFERENCES candidates (id)
        );
        """
    )
    conn.commit()
    conn.close()


def save_candidate(file_name: str, raw_text: str, extracted: dict) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO candidates (file_name, raw_text, extracted_json, created_at) "
        "VALUES (?, ?, ?, ?)",
        (file_name, raw_text, json.dumps(extracted), datetime.utcnow().isoformat()),
    )
    conn.commit()
    candidate_id = cur.lastrowid
    conn.close()
    return candidate_id


def save_screening(
    candidate_id: int,
    job_title: str,
    job_description: str,
    score_breakdown: dict,
    justification: str,
) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO screenings "
        "(candidate_id, job_title, job_description, score_breakdown_json, justification, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            candidate_id,
            job_title,
            job_description,
            json.dumps(score_breakdown),
            justification,
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    screening_id = cur.lastrowid
    conn.close()
    return screening_id


def get_screenings_for_job(job_title: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT s.id, s.job_title, s.score_breakdown_json, s.justification,
               c.file_name, c.extracted_json
        FROM screenings s
        JOIN candidates c ON c.id = s.candidate_id
        WHERE s.job_title = ?
        ORDER BY s.created_at DESC
        """,
        (job_title,),
    ).fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append(
            {
                "screening_id": row["id"],
                "file_name": row["file_name"],
                "candidate": json.loads(row["extracted_json"]),
                "score": json.loads(row["score_breakdown_json"]),
                "justification": row["justification"],
            }
        )
    return results
