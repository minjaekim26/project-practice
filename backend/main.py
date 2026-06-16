from __future__ import annotations

import os
import tempfile
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db, insert_song, list_songs_with_features
from .feature_extractor import extract_features
from .recommendation import recommend_similar


app = FastAPI(title="Music Recommendation System", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/upload")
async def upload_audio(file: Annotated[UploadFile, File(...)]) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".mp3", ".wav", ".flac", ".ogg", ".m4a"]:
        raise HTTPException(status_code=400, detail="Unsupported audio type")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp_path = tmp.name
        content = await file.read()
        tmp.write(content)

    try:
        features = extract_features(tmp_path)
        song_id = insert_song(filename=file.filename, features=features)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    return {"song_id": song_id, "filename": file.filename, "features": features}


@app.get("/songs")
def songs() -> dict:
    rows = list_songs_with_features()
    return {"songs": rows}


@app.get("/recommend/{song_id}")
def recommend(song_id: int, top_n: int = 5, metric: str = "cosine") -> dict:
    songs = list_songs_with_features()
    if not any(s["id"] == song_id for s in songs):
        raise HTTPException(status_code=404, detail="Song not found")

    recs = recommend_similar(songs=songs, query_song_id=song_id, top_n=top_n, metric=metric)
    return {"song_id": song_id, "recommendations": recs, "metric": metric}

