## Spotify 스타일 음악 추천 웹서비스: 코드베이스 분석

분석 기준: 현재 `project-practice` 저장소(React+Vite 프론트, FastAPI 백엔드, SQLite)로 **Spotify 스타일(개인화/대규모/실시간/안정성/보안)** 서비스를 확장할 수 있는지 관점에서 평가합니다.

---

## 1) 폴더 구조 평가

현재 구조(핵심):

- **`backend/`**
  - `app.py`: FastAPI 엔트리 + 업로드/분석/추천/조회 라우트가 한 파일에 집중
  - `database.py`: SQLite 스키마/CRUD/seed
  - `requirements.txt`
  - `uploads/`: 업로드 파일 저장 디렉터리(런타임 생성)
  - `music.db`: 런타임 생성(SQLite)
- **`frontend/`**
  - Vite + React 단일 페이지
  - Tailwind 설정(`tailwind.config.js`, `postcss.config.js`)
  - `src/App.jsx`: UI/네트워크/상태가 단일 컴포넌트에 집중

평가:
- **장점**: 학습/프로토타이핑엔 매우 빠른 단일 구조
- **한계**: Spotify 스타일로 커지면 “도메인/레이어” 분리가 필요
  - 백엔드: 라우트/서비스(추천)/스토리지/설정 분리 필요
  - 프론트: API 클라이언트/상태관리/페이지 분리 필요

권장 구조(확장 시):
- `backend/app/` 아래에 `routers/`, `services/`, `db/`, `schemas/`, `settings.py`로 분리
- `frontend/src/` 아래에 `api/`, `components/`, `pages/`, `hooks/`, `styles/` 분리

---

## 2) 코드 품질 평가

### 백엔드(`backend/app.py`, `backend/database.py`)
- **장점**
  - 엔드포인트가 단순하고 Swagger로 테스트 가능
  - 업로드→분석→DB저장→추천 흐름이 한 번에 재현 가능
- **개선 필요**
  - 비즈니스 로직(특징 추출/유사도 계산)이 라우트 함수 내부에 섞여 있음
  - 타입/스키마(요청/응답) 모델이 없어 문서/검증이 약함(Pydantic 모델 권장)
  - DB 마이그레이션이 `DROP TABLE` 기반이라 데이터 손실 위험(개발 초기엔 OK)

### 프론트(`frontend/src/App.jsx`)
- **장점**
  - UI 완성도(레이아웃/상태/에러 표시)가 좋고 즉시 사용 가능
  - 업로드 진행률 표시 구현(axios `onUploadProgress`)
- **개선 필요**
  - `App.jsx`에 UI+네트워크+상태가 집중 → 유지보수 어려움
  - API 에러 메시지 파싱은 있으나 케이스 분리(타임아웃/네트워크/서버 응답) 개선 여지

---

## 3) 버그 가능성(리스크)

### 백엔드
- **상대 import/작업 디렉터리 의존**: `from database import ...` 형태는 실행 위치에 따라 깨질 수 있음
  - 권장: 패키지화(`backend/app/__init__.py`) 후 `from app.db import ...` 같은 절대 import
- **대용량 파일 메모리 사용**: `await file.read()`로 전체 바이트를 메모리에 올림
  - 큰 MP3 업로드 시 메모리 급증 가능
  - 해결: 스트리밍 저장(`shutil.copyfileobj(file.file, ...)`)
- **uploads 디렉터리 관리**: 오래된 업로드 파일이 누적되면 디스크 증가
  - 해결: TTL 삭제/정리 작업(크론/백그라운드)
- **seed 데이터**: 서버 시작 시 DB가 비면 예시 데이터 삽입
  - 실제 운영에서 “의도치 않은 데이터”가 들어갈 수 있음 → 개발/운영 분리 필요

### 프론트
- **Node/npm 미설치 환경**에서 실행 불가(현재 사용자가 실제로 겪음)
  - 해결: README에 Node 설치 안내/프론트 실행 조건 명확화
- **CORS**: 백엔드가 `*` 허용이라 운영 환경에서 위험

---

## 4) 성능 개선 제안

### 추천/검색 성능
현재는 곡 수가 늘면 `O(N)`으로 cosine을 전부 계산합니다.
- **단기**: 벡터 구성 시 정규화/캐싱(특징 벡터 미리 정규화 저장)
- **중기**: 근사 최근접(ANN)
  - FAISS / ScaNN / Annoy 같은 벡터 인덱스
  - 또는 PostgreSQL + pgvector로 전환
- **장기(Spotify 스타일)**:
  - 후보 생성(협업필터/콘텐츠/그래프) + 랭킹 모델(learning-to-rank) 2단계 구조

### 특징 추출 성능
- librosa는 CPU 부담 큼
  - 업로드 요청이 많아지면 비동기/큐 필요(Celery/RQ/BackgroundTasks + 워커)
  - 결과를 캐시하고 재분석 방지(해시 기반)

### API 응답 성능
- `/songs`가 커지면 pagination 필요
- gzip/etag, CDN(정적 프론트) 고려

---

## 5) 보안 문제(중요)

현재는 “학습/로컬 데모” 수준으로 안전장치가 거의 없습니다.

- **CORS `allow_origins=["*"]`**: 운영에선 특정 도메인만 허용
- **인증/인가 없음**: 누구나 업로드/추천/DB 조회 가능
  - Spotify 스타일이라면 OAuth(Spotify OAuth) 또는 자체 계정/세션 필요
- **파일 업로드 검증 약함**
  - 확장자만 검사 → 실제 MIME/헤더 검증 필요
  - 파일 크기 제한/레이트리밋 필요
- **DB 노출**
  - `/songs` 전체를 노출하는 API는 운영에선 제한 필요(관리자/개발용)
- **비밀값 관리**
  - 현재는 API 키 없음. 추후 Spotify API/DB 접속정보 들어가면 `.env`/Secrets 관리 필요

---

## 6) 리팩토링 제안(우선순위)

### P0 (바로)
- 백엔드: 업로드 저장을 스트리밍으로 변경(메모리 폭주 방지)
- 백엔드: Pydantic 스키마 추가(응답 형태 고정, 문서 자동화)
- 프론트: API 호출 로직을 `src/api/client.js`로 분리
- `backend/__pycache__/`는 gitignore 처리

### P1 (다음)
- 추천 로직 분리: `services/recommender.py`
- DB 레이어 분리: `db/connection.py`, `db/repository.py`
- pagination: `/songs?limit=&offset=`

### P2 (확장)
- 벡터 인덱스/pgvector 도입
- 비동기 특징추출(큐)
- 사용자/플레이리스트/라이브러리 도메인 모델 추가

---

## 7) 다음 단계 개발 계획(Spotify 스타일 로드맵)

### 단계 1: 제품 뼈대(1~2주)
- 사용자 인증(간단 로그인) + 개인 라이브러리
- 업로드 곡 메타데이터(title/artist/cover) UI 개선
- 추천 결과 “플레이 버튼/미리듣기” (업로드 파일 스트리밍 제공)

### 단계 2: 추천 품질 향상(2~4주)
- 콘텐츠 기반 특징 벡터 고도화(리듬/키/세그먼트/embedding)
- 유사도 결과에 “왜 추천됐는지”(설명) 추가
- 오프라인 평가(precision@k) 파이프라인

### 단계 3: 확장/운영(지속)
- pgvector/ANN 인덱싱
- 워커 기반 특징추출
- 레이트리밋/파일 검증/권한 분리
- 관측성(로그/메트릭/트레이싱)

---

## 메모: 현재 상태에서 바로 가능한 데모 시나리오

- `POST /upload`로 DB에 곡을 몇 개 저장
- `POST /recommend`로 새 MP3 업로드 → DB와 cosine 비교 → Top 10 추천
- 프론트는 axios로 `/recommend` 호출해 결과 표시(단, Node/npm 설치 필요)

