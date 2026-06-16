"""
SQLite DB 스냅샷 생성 스크립트.

목적:
- backend/music.db 안에 저장된 songs 레코드를 읽어서
  사람이 보기 좋은 텍스트로 출력합니다.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone


def main() -> None:
    db_path = os.path.join(os.path.dirname(__file__), "music.db")
    print(f"db_path: {db_path}")
    print(f"exists: {os.path.exists(db_path)}")

    if not os.path.exists(db_path):
        print("No database file found. Run the backend and upload at least one song first.")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print(f"generated_at_utc: {datetime.now(timezone.utc).isoformat()}")
    tables = [r["name"] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f"tables: {tables}")

    if "songs" not in tables:
        print("songs table not found.")
        return

    cols = cur.execute("PRAGMA table_info(songs)").fetchall()
    print("songs_columns:")
    for c in cols:
        # PRAGMA table_info: cid, name, type, notnull, dflt_value, pk
        print(f"- {c[1]} ({c[2]})")

    rows = cur.execute(
        """
        SELECT id, title, artist, tempo, duration, mfcc, chroma, spectral_centroid, zcr
        FROM songs
        ORDER BY id ASC
        """
    ).fetchall()

    print(f"songs_count: {len(rows)}")
    print("")
    print("songs:")
    for r in rows:
        mfcc = json.loads(r["mfcc"]) if r["mfcc"] else []
        chroma = json.loads(r["chroma"]) if r["chroma"] else []
        print(
            f"- id={int(r['id'])} "
            f"title={r['title']!r} "
            f"artist={r['artist']!r} "
            f"tempo={float(r['tempo']):.2f} "
            f"duration={float(r['duration']):.2f} "
            f"spectral_centroid={float(r['spectral_centroid']):.2f} "
            f"zcr={float(r['zcr']):.4f} "
            f"mfcc_len={len(mfcc)} "
            f"chroma_len={len(chroma)}"
        )

    conn.close()


if __name__ == "__main__":
    main()

