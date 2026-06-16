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

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware


# 프로젝트 루트 기준으로 uploads 폴더를 사용합니다.
# (현재 파일은 backend/app.py 이므로, uploads는 backend/uploads/ 에 생성됩니다.)
BACKEND_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BACKEND_DIR / "uploads"


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

        return {
            "original_filename": file.filename,
            "saved_filename": safe_name,
            "saved_path": str(save_path),
            "bytes": len(content),
        }

    return app


# uvicorn이 import할 app 객체를 노출합니다.
# 실행 예: python -m uvicorn app:app --reload --port 8000
app = create_app()

