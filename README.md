# 🎵 Music Recommendation System

사용자가 음악 파일을 업로드하면 음원의 특징을 분석하여 **유사한 노래를 추천**하는 웹 서비스입니다.

- 저장소: https://github.com/minjaekim26/project-practice
- 구현: FastAPI(백엔드) + React(프론트엔드)

---

## 📌 프로젝트 소개

업로드한 음악에서 **tempo, MFCC, chroma, spectral centroid, ZCR** 등의 특징을 추출하고,
DB에 저장된 다른 곡들과 비교해 **유사도가 높은 Top-N 곡**을 추천합니다.

```
음악 업로드 → 특징 추출 → DB 저장 → 유사도 계산 → 추천 결과 표시
```

---

## 🛠 사전 준비

| 항목 | 권장 버전 |
|------|-----------|
| Python | 3.10 이상 |
| Node.js | 18 이상 (npm 포함) |
| Git | 최신 버전 |

Windows PowerShell 기준으로 안내합니다.

---

## 📥 프로젝트 받기 (GitHub에서 클론)

**처음 받을 때만** 아래를 실행하세요.

```powershell
cd C:\Users\selen\Projects
git clone https://github.com/minjaekim26/project-practice.git
cd project-practice
```

이미 `project-practice` 폴더 안에 있다면 `cd project-practice`를 **다시 하지 마세요.**  
(그러면 `project-practice\project-practice` 같은 없는 경로로 들어가서 오류가 납니다.)

현재 위치 확인:

```powershell
Get-Location
```

`...\project-practice` 가 보이면 이미 프로젝트 루트입니다. 바로 `backend` 또는 `frontend`로 이동하면 됩니다.

이미 클론했다면 최신 코드 받기:

```powershell
# project-practice 폴더 안에서
git pull origin main
```

---

## 🚀 실행 방법 (가장 쉬운 방법)

프로젝트 루트(`project-practice` 폴더)에서 **터미널 2개**를 엽니다.

**터미널 1 — 백엔드**

```powershell
cd C:\Users\selen\Projects\project-practice
.\run-backend.ps1
```

**터미널 2 — 프론트**

```powershell
cd C:\Users\selen\Projects\project-practice
.\run-frontend.ps1
```

실행 후 브라우저에서 **http://localhost:5173** 접속.

---

## 🚀 실행 방법 (수동)

백엔드와 프론트엔드를 **각각 따로** 실행해야 합니다.

### 1) 백엔드 실행 (터미널 1)

```powershell
# project-practice 폴더 안에서
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

### 2) 프론트엔드 실행 (터미널 2)

```powershell
# project-practice 폴더 안에서
cd frontend
npm install
npm run dev
```

정상 실행 시 아래 주소로 접속 가능합니다.

| 용도 | 주소 |
|------|------|
| 웹 UI (메인) | http://localhost:5173 |
| API 상태 확인 | http://localhost:8000/health |
| API 문서 (Swagger) | http://localhost:8000/docs |
| 곡 목록 API | http://localhost:8000/songs |

`http://localhost:8000/health` 에 접속했을 때 `{"ok": true}` 가 보이면 백엔드가 켜진 것입니다.

---

## 📂 프로젝트 구조

```text
project-practice/
├── backend/                 # FastAPI 서버
│   ├── main.py
│   ├── database.py
│   ├── feature_extractor.py
│   ├── recommendation.py
│   └── requirements.txt
├── frontend/                # React 웹 UI
│   ├── src/App.jsx
│   ├── package.json
│   └── vite.config.js
├── run-backend.ps1          # 백엔드 실행 스크립트
├── run-frontend.ps1         # 프론트 실행 스크립트
└── README.md
```

---

## 🌐 들어가는 방법 (웹에서 사용하기)

1. 브라우저에서 **http://localhost:5173** 접속
2. **1) 음악 업로드** 섹션에서 MP3/WAV 등 음악 파일 선택 후 `업로드` 클릭
3. 같은 곡을 2~3개 이상 업로드하면 추천이 더 잘 보입니다
4. **2) 등록된 곡**에서 `목록 새로고침` → 추천 기준 곡 선택 → `추천 받기`
5. **3) 추천 결과**에 유사한 곡 목록과 cosine 점수가 표시됩니다

### 화면에서 하는 일 요약

| 단계 | 화면 | 하는 일 |
|------|------|---------|
| 1 | 음악 업로드 | 파일 선택 후 업로드 |
| 2 | 등록된 곡 | 기준 곡 선택 후 추천 요청 |
| 3 | 추천 결과 | 유사 곡 Top 5 확인 |

---

## 🔌 API 직접 호출 (선택)

프론트 없이 API만 테스트할 때:

```powershell
# 상태 확인
curl http://localhost:8000/health

# 곡 목록
curl http://localhost:8000/songs

# song_id=1 기준 추천 (업로드 후 id 확인)
curl "http://localhost:8000/recommend/1?top_n=5&metric=cosine"
```

업로드는 Swagger UI에서 테스트하기 쉽습니다: **http://localhost:8000/docs** → `POST /upload`

---

## ⚙ 주요 기능

### 1. 음악 업로드
- 지원 형식: `.mp3`, `.wav`, `.flac`, `.ogg`, `.m4a`
- 업로드 시 자동으로 특징 추출 후 DB 저장

### 2. 특징 추출 (librosa)
- Tempo (BPM)
- MFCC (평균/표준편차)
- Chroma
- Spectral Centroid
- Zero Crossing Rate (ZCR)

### 3. 유사도 계산
- `cosine` (기본): 값이 클수록 유사
- `euclidean`: 값이 작을수록 유사

### 4. 추천
- 기준 곡 1개를 선택하면 나머지 곡 중 Top-N 추천

---

## 🔄 시스템 동작 과정

```
사용자 업로드
    ↓
FastAPI가 파일 수신
    ↓
librosa로 특징 벡터 추출
    ↓
SQLite(music.db)에 저장
    ↓
기준 곡과 다른 곡들의 벡터 비교
    ↓
유사도 순으로 Top-N 반환
    ↓
React UI에 결과 표시
```

---

## 🧪 빠른 동작 확인 체크리스트

- [ ] 백엔드: `http://localhost:8000/health` → `{"ok": true}`
- [ ] 프론트: `http://localhost:5173` 화면 로딩
- [ ] 음악 파일 2개 이상 업로드 성공
- [ ] 등록된 곡 목록에 업로드한 파일 표시
- [ ] 추천 결과에 유사 곡 리스트 표시

---

## ❗ 자주 나는 문제

| 증상 | 해결 |
|------|------|
| `project-practice\project-practice` 경로 없음 | 이미 프로젝트 안에 있음. `cd backend` 또는 `cd frontend` 사용 |
| 프론트에서 업로드 실패 | 백엔드가 먼저 켜져 있는지 확인 (`8000` 포트) |
| `pip` / `python` 인식 안 됨 | Python 설치 후 `python --version` 확인 |
| `npm` 인식 안 됨 | Node.js 설치 후 `npm --version` 확인 |
| 추천 결과가 비어 있음 | 곡을 2개 이상 업로드했는지 확인 (기준 곡 제외할 후보 필요) |
| 포트 사용 중 | 백엔드: `--port 8001` / 프론트: `vite.config.js`에서 port 변경 |

백엔드 주소를 바꿨다면 프론트 실행 전:

```powershell
$env:VITE_API_BASE="http://localhost:8000"
npm run dev
```

---

## 📈 향후 개선 계획

- 데이터셋 일괄 적재 (곡 폴더 스캔)
- Spotify API 연동
- 딥러닝 기반 추천
- 사용자 취향 학습 / 플레이리스트 생성

---

## 👨‍💻 개발 목적

- FastAPI 학습
- React 학습
- 오디오 데이터 분석
- 추천 시스템 구현
- AI 서비스 개발 경험
