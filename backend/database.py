"""
SQLite 데이터베이스 모듈.

songs 테이블에 음악 특징을 저장/조회합니다.
"""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any

# DB 파일 경로 (backend/music.db)
_DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "music.db")


def _connect(db_path: str | None = None) -> sqlite3.Connection:
    """SQLite 연결을 생성합니다."""
    conn = sqlite3.connect(db_path or _DEFAULT_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | None = None) -> None:
    """
    1) DB 파일 생성 (없으면 자동 생성)
    2) songs 테이블 생성
    """
    expected_columns = {
        "id",
        "title",
        "artist",
        "tempo",
        "duration",
        "mfcc",
        "chroma",
        "spectral_centroid",
        "zcr",
    }

    with _connect(db_path) as conn:
        # 이전 스키마(filename/features_json)가 남아 있으면 테이블을 재생성합니다.
        table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='songs'"
        ).fetchone()
        if table is not None:
            current_columns = {
                row[1] for row in conn.execute("PRAGMA table_info(songs)").fetchall()
            }
            if current_columns != expected_columns:
                conn.execute("DROP TABLE songs")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist TEXT NOT NULL,
                tempo REAL NOT NULL,
                duration REAL NOT NULL,
                mfcc TEXT NOT NULL,
                chroma TEXT NOT NULL,
                spectral_centroid REAL NOT NULL,
                zcr REAL NOT NULL
            )
            """.strip()
        )
        conn.commit()


def insert_song(
    *,
    title: str,
    artist: str,
    tempo: float,
    duration: float,
    mfcc: list[float],
    chroma: list[float],
    spectral_centroid: float,
    zcr: float,
    db_path: str | None = None,
) -> int:
    """
    3) INSERT 함수 — 분석된 특징을 songs 테이블에 저장합니다.

    mfcc, chroma는 리스트이므로 JSON 문자열로 직렬화해 TEXT 컬럼에 저장합니다.
  """
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO songs (
                title, artist, tempo, duration,
                mfcc, chroma, spectral_centroid, zcr
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                artist,
                float(tempo),
                float(duration),
                json.dumps(mfcc, ensure_ascii=False),
                json.dumps(chroma, ensure_ascii=False),
                float(spectral_centroid),
                float(zcr),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """DB Row를 API 응답용 dict로 변환합니다."""
    return {
        "id": int(row["id"]),
        "title": str(row["title"]),
        "artist": str(row["artist"]),
        "tempo": float(row["tempo"]),
        "duration": float(row["duration"]),
        "mfcc": json.loads(row["mfcc"]),
        "chroma": json.loads(row["chroma"]),
        "spectral_centroid": float(row["spectral_centroid"]),
        "zcr": float(row["zcr"]),
    }


def select_all_songs(db_path: str | None = None) -> list[dict[str, Any]]:
    """4) SELECT 함수 — 전체 곡 목록을 조회합니다."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, title, artist, tempo, duration,
                   mfcc, chroma, spectral_centroid, zcr
            FROM songs
            ORDER BY id ASC
            """
        ).fetchall()
        return [_row_to_dict(r) for r in rows]


def select_song_by_id(song_id: int, db_path: str | None = None) -> dict[str, Any] | None:
    """4) SELECT 함수 — id로 곡 1개를 조회합니다."""
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT id, title, artist, tempo, duration,
                   mfcc, chroma, spectral_centroid, zcr
            FROM songs
            WHERE id = ?
            """,
            (song_id,),
        ).fetchone()
        if row is None:
            return None
        return _row_to_dict(row)
