"""
FastAPI 백엔드 엔트리포인트.

요구사항 충족:
- CORS 설정
- 파일 업로드 API
- uploads 폴더 자동 생성
- 업로드한 MP3 저장
- Swagger(/docs)에서 업로드 테스트 가능
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Annotated

import librosa
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from database import init_db, insert_song, seed_example_songs, select_all_songs, select_song_by_id


# 프로젝트 루트 기준으로 uploads 폴더를 사용합니다.
# (현재 파일은 backend/app.py 이므로, uploads는 backend/uploads/ 에 생성됩니다.)
BACKEND_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BACKEND_DIR / "uploads"


def extract_audio_features(mp3_path: Path) -> dict:
    """
    MP3 파일을 librosa로 분석하여 특징을 JSON으로 반환 가능한 dict로 만듭니다.

    추출 특징:
    - BPM(Tempo)
    - Duration(초)
    - MFCC 13개 평균값
    - Chroma Features(12개 평균값)
    - Spectral Centroid(평균)
    - Zero Crossing Rate(평균)
    """

    # sr=None: 원본 샘플레이트 유지(불필요한 리샘플링 방지)
    # mono=True: 스테레오를 모노로 합쳐 특징 추출을 단순화
    y, sr = librosa.load(str(mp3_path), sr=None, mono=True)

    # 길이(초)
    duration = float(librosa.get_duration(y=y, sr=sr))

    # Tempo(BPM)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

    # MFCC(13)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)  # shape: (13, frames)
    mfcc_mean = np.mean(mfcc, axis=1)  # shape: (13,)

    # Chroma(12)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)  # shape: (12, frames)
    chroma_mean = np.mean(chroma, axis=1)  # shape: (12,)

    # Spectral Centroid
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]  # shape: (frames,)
    centroid_mean = float(np.mean(centroid))

    # Zero Crossing Rate
    zcr = librosa.feature.zero_crossing_rate(y)[0]  # shape: (frames,)
    zcr_mean = float(np.mean(zcr))

    # numpy 타입은 JSON 직렬화가 안 되므로 Python 기본 타입으로 변환합니다.
    return {
        "tempo_bpm": float(tempo),
        "duration_sec": duration,
        "mfcc13_mean": [float(x) for x in mfcc_mean],
        "chroma_mean": [float(x) for x in chroma_mean],
        "spectral_centroid_mean": centroid_mean,
        "zero_crossing_rate_mean": zcr_mean,
        "sample_rate": int(sr),
    }


def create_app() -> FastAPI:
    """
    FastAPI 앱을 생성합니다.

    앱 생성과 동시에:
    - CORS 설정
    - 업로드 폴더 생성
    - 라우터 등록
    """

    app = FastAPI(title="Music Recommendation System API", version="0.2.0")

    # CORS 설정: 개발 편의상 모든 origin 허용
    # 배포 환경에서는 allow_origins를 특정 도메인으로 제한하세요.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _startup() -> None:
        # 서버 실행 시 uploads 폴더와 SQLite DB/테이블을 자동 생성합니다.
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        init_db()
        # DB가 비어있으면 예시 데이터를 추가합니다.
        seed_example_songs()

    @app.get("/health")
    def health() -> dict:
        # 서버 헬스체크 엔드포인트
        return {"ok": True}

    @app.get("/songs")
    def get_songs() -> dict:
        """저장된 전체 곡 목록을 JSON으로 반환합니다."""
        return {"songs": select_all_songs()}

    @app.get("/songs/{song_id}")
    def get_song(song_id: int) -> dict:
        """id로 곡 1개를 조회합니다."""
        song = select_song_by_id(song_id)
        if song is None:
            raise HTTPException(status_code=404, detail="Song not found")
        return song

    @app.post("/upload")
    async def upload_mp3(
        file: Annotated[UploadFile, File(...)],
        title: Annotated[str | None, Form()] = None,
        artist: Annotated[str | None, Form()] = None,
    ) -> dict:
        """
        MP3 파일 업로드 API.

        Swagger(/docs)에서:
        - Try it out → file 선택 → (선택) title/artist 입력 → Execute
        로 테스트할 수 있습니다.
        """

        if not file.filename:
            raise HTTPException(status_code=400, detail="Missing filename")

        # 확장자 검사 (간단 검증)
        ext = os.path.splitext(file.filename)[1].lower()
        if ext != ".mp3":
            raise HTTPException(status_code=400, detail="Only .mp3 is allowed")

        # 파일 이름 충돌 방지: UUID 기반으로 저장
        safe_name = f"{uuid.uuid4().hex}.mp3"
        save_path = UPLOAD_DIR / safe_name

        # 업로드 파일을 디스크에 저장
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")
        save_path.write_bytes(content)

        # 업로드된 파일을 바로 분석하여 결과를 함께 반환합니다.
        try:
            features = extract_audio_features(save_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Feature extraction failed: {e}")

        # title/artist가 없으면 파일명을 title로 사용
        song_title = title or os.path.splitext(file.filename)[0]
        song_artist = artist or "Unknown"

        # 5) FastAPI 연동 — 분석 결과를 SQLite에 저장
        song_id = insert_song(
            title=song_title,
            artist=song_artist,
            tempo=features["tempo_bpm"],
            duration=features["duration_sec"],
            mfcc=features["mfcc13_mean"],
            chroma=features["chroma_mean"],
            spectral_centroid=features["spectral_centroid_mean"],
            zcr=features["zero_crossing_rate_mean"],
        )

        return {
            "song_id": song_id,
            "original_filename": file.filename,
            "saved_filename": safe_name,
            "saved_path": str(save_path),
            "bytes": len(content),
            "title": song_title,
            "artist": song_artist,
            "features": features,
        }

    def _to_vector(song: dict) -> np.ndarray:
        """
        songs 테이블 레코드를 1차원 벡터로 펼칩니다.

        구성(총 1 + 1 + 13 + 12 + 1 + 1 = 29차원):
        - tempo, duration, mfcc(13), chroma(12), spectral_centroid, zcr
        """
        parts: list[float] = []
        parts.append(float(song["tempo"]))
        parts.append(float(song["duration"]))
        parts.extend([float(x) for x in song["mfcc"]])
        parts.extend([float(x) for x in song["chroma"]])
        parts.append(float(song["spectral_centroid"]))
        parts.append(float(song["zcr"]))
        v = np.array(parts, dtype=np.float32)
        return np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0)

    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """
        Cosine Similarity 계산.
        - 1에 가까울수록 유사, -1에 가까울수록 반대 방향
        """
        denom = float(np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0.0:
            return 0.0
        return float(np.dot(a, b) / denom)

    @app.get("/recommend/{song_id}")
    def recommend_by_song_id(song_id: int, top_k: int = 10) -> dict:
        """
        4) FastAPI API 생성

        DB에 저장된 곡(id)을 기준으로, 다른 곡들과 Cosine Similarity를 계산해 상위 10곡 추천.
        """
        songs = select_all_songs()
        query = next((s for s in songs if s["id"] == song_id), None)
        if query is None:
            raise HTTPException(status_code=404, detail="Song not found")

        query_v = _to_vector(query)
        results = []
        for s in songs:
            if s["id"] == song_id:
                continue
            score = _cosine_similarity(query_v, _to_vector(s))
            results.append({"id": s["id"], "title": s["title"], "artist": s["artist"], "score": score})

        results.sort(key=lambda x: x["score"], reverse=True)
        return {"query_song_id": song_id, "top_k": int(top_k), "recommendations": results[: int(top_k)]}

    @app.post("/recommend")
    async def recommend_by_upload(
        file: Annotated[UploadFile, File(...)],
        top_k: int = 10,
    ) -> dict:
        """
        업로드한 MP3를 기준으로 DB의 곡들과 비교하여 추천합니다.

        - Cosine Similarity 사용
        - 상위 10곡 추천
        - 유사도 점수 반환
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="Missing filename")

        ext = os.path.splitext(file.filename)[1].lower()
        if ext != ".mp3":
            raise HTTPException(status_code=400, detail="Only .mp3 is allowed")

        safe_name = f"{uuid.uuid4().hex}.mp3"
        save_path = UPLOAD_DIR / safe_name

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")
        save_path.write_bytes(content)

        try:
            features = extract_audio_features(save_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Feature extraction failed: {e}")

        # 업로드 파일의 특징을 songs 테이블 스키마에 맞는 임시 dict로 변환
        query_song = {
            "tempo": features["tempo_bpm"],
            "duration": features["duration_sec"],
            "mfcc": features["mfcc13_mean"],
            "chroma": features["chroma_mean"],
            "spectral_centroid": features["spectral_centroid_mean"],
            "zcr": features["zero_crossing_rate_mean"],
        }
        query_v = _to_vector(query_song)

        songs = select_all_songs()
        if not songs:
            raise HTTPException(status_code=400, detail="No songs in database to compare")

        results = []
        for s in songs:
            score = _cosine_similarity(query_v, _to_vector(s))
            results.append({"id": s["id"], "title": s["title"], "artist": s["artist"], "score": score})

        results.sort(key=lambda x: x["score"], reverse=True)
        return {
            "uploaded_filename": file.filename,
            "saved_filename": safe_name,
            "features": features,
            "top_k": int(top_k),
            "recommendations": results[: int(top_k)],
        }

    return app


# uvicorn이 import할 app 객체를 노출합니다.
# 실행 예: python -m uvicorn app:app --reload --port 8000
app = create_app()

