"""
Thin SQLite helper.

SQLite is file based, not a network service, so it does not need a host
port mapping and it will not be affected by the Docker network mode
(bridge / host / none). It is included here so the FastAPI app has a
persistent store in addition to Redis, to make it comparable to the
Mongo + Redis app on the Node/React side.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def add_item(name: str) -> dict:
    conn = get_connection()
    try:
        cur = conn.execute("INSERT INTO items (name) VALUES (?)", (name,))
        conn.commit()
        row = conn.execute(
            "SELECT id, name, created_at FROM items WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


def list_items() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, name, created_at FROM items ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
