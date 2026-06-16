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
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware


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
        # 서버 실행 시 uploads 폴더를 자동 생성합니다.
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    @app.get("/health")
    def health() -> dict:
        # 서버 헬스체크 엔드포인트
        return {"ok": True}

    @app.post("/upload")
    async def upload_mp3(file: Annotated[UploadFile, File(...)]) -> dict:
        """
        MP3 파일 업로드 API.

        Swagger(/docs)에서:
        - Try it out → file 선택 → Execute
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
        # (Swagger에서도 한 번에 테스트할 수 있게 하기 위함)
        try:
            features = extract_audio_features(save_path)
        except Exception as e:
            # 분석 실패 시에도 파일은 저장되어 있으므로, 원인을 반환합니다.
            raise HTTPException(status_code=500, detail=f"Feature extraction failed: {e}")

        return {
            "original_filename": file.filename,
            "saved_filename": safe_name,
            "saved_path": str(save_path),
            "bytes": len(content),
            "features": features,
        }

    return app


# uvicorn이 import할 app 객체를 노출합니다.
# 실행 예: python -m uvicorn app:app --reload --port 8000
app = create_app()

