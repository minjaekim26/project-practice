from __future__ import annotations

import json
import os
import sqlite3
from typing import Any


_DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "music.db")


def _connect(db_path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or _DEFAULT_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | None = None) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                features_json TEXT NOT NULL
            )
            """.strip()
        )
        conn.commit()


def insert_song(*, filename: str, features: dict[str, Any], db_path: str | None = None) -> int:
    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO songs (filename, features_json) VALUES (?, ?)",
            (filename, json.dumps(features, ensure_ascii=False)),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_songs_with_features(db_path: str | None = None) -> list[dict[str, Any]]:
    with _connect(db_path) as conn:
        rows = conn.execute("SELECT id, filename, features_json FROM songs ORDER BY id ASC").fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "id": int(r["id"]),
                    "filename": str(r["filename"]),
                    "features": json.loads(r["features_json"]),
                }
            )
        return out

