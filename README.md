# Music Recommendation System (Practice)

`project-practice` README의 흐름(업로드 → 특징추출 → 유사도 계산 → Top-N 추천)을 **최소 동작 버전**으로 구현한 샘플입니다.

## 구조

```text
music-recommendation-system/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── feature_extractor.py
│   ├── recommendation.py
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx
        ├── main.jsx
        └── styles.css
```

## Backend (FastAPI)

```powershell
cd music-recommendation-system\backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

엔드포인트:

- `GET /health`
- `POST /upload` (multipart form-data: `file`)
- `GET /songs`
- `GET /recommend/{song_id}?top_n=5&metric=cosine` (`metric`: `cosine` | `euclidean`)

> 업로드된 곡의 특징 벡터는 `backend/music.db`(SQLite)에 저장됩니다.

## Frontend (React + Vite)

```powershell
cd music-recommendation-system\frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속 후 파일 업로드 → 추천 기준 곡 선택 → 추천 받기.

환경변수로 백엔드 주소 변경:

```powershell
$env:VITE_API_BASE="http://localhost:8000"
npm run dev
```

## 메모 (제약/단순화)

- 실제 서비스 수준이 아니라 “대략적으로 동작”하는 연습용입니다.
- 데이터셋/DB에 기존 곡을 미리 적재하는 기능은 넣지 않았고, 업로드로만 곡이 쌓입니다.
- 특징은 `librosa` 기반(tempo, MFCC, chroma, centroid, ZCR) 요약 통계만 사용합니다.

