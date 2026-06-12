# 🎵 Music Recommendation System

사용자가 음악 파일을 업로드하면 음원의 특징을 분석하여 유사한 노래를 추천하는 웹 서비스입니다.

## 📌 프로젝트 소개

본 프로젝트는 사용자가 업로드한 음악 파일의 오디오 특징을 추출하고,
데이터베이스에 저장된 음악들과 비교하여 유사한 곡을 추천하는 AI 기반 음악 추천 시스템입니다.

사용자는 별도의 검색 없이 자신이 좋아하는 음악과 비슷한 곡을 발견할 수 있습니다.

---

## 🎯 프로젝트 목표

- 음악 파일 업로드 기능 구현
- 오디오 특징 추출
- 유사도 계산 알고리즘 구현
- 추천 결과 시각화
- 웹 기반 사용자 인터페이스 제공

---

## 🛠 기술 스택

### Frontend
- React
- HTML/CSS
- JavaScript

### Backend
- FastAPI
- Python

### AI / Data Analysis
- Librosa
- NumPy
- Pandas
- Scikit-learn

### Database
- SQLite (개발용)
- PostgreSQL (확장 가능)

---

## 📂 프로젝트 구조

```text
music-recommendation-system/

├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── backend/
│   ├── main.py
│   ├── recommendation.py
│   ├── feature_extractor.py
│   └── database.py
│
├── dataset/
│   └── songs/
│
├── models/
│
├── requirements.txt
│
└── README.md
```

---

## ⚙ 주요 기능

### 1. 음악 업로드

- MP3 파일 업로드
- 파일 유효성 검사

### 2. 특징 추출

음원에서 다음 정보를 추출

- Tempo(BPM)
- MFCC
- Spectral Centroid
- Chroma Features
- Zero Crossing Rate

### 3. 유사도 계산

- Cosine Similarity
- Euclidean Distance

활용하여 유사 곡 탐색

### 4. 음악 추천

- Top-N 추천
- 유사도 점수 제공

### 5. 추천 결과 출력

- 추천 곡 목록
- 유사도 순위 표시

---

## 🔄 시스템 동작 과정

1. 사용자가 음악 업로드
2. 서버에서 특징 추출
3. 데이터베이스 음악들과 비교
4. 유사도 계산
5. 추천 결과 반환

---

## 🚀 실행 방법

### Backend

```bash
cd backend

pip install -r requirements.txt

uvicorn main:app --reload
```

### Frontend

```bash
cd frontend

npm install

npm start
```

---

## 📊 추천 알고리즘

음악 특징 벡터를 생성한 후

```text
[tempo,
 mfcc_1,
 mfcc_2,
 ...
 chroma]
```

형태로 변환하여 벡터 간 거리를 계산합니다.

가장 가까운 음악을 추천 결과로 제공합니다.

---

## 📈 향후 개선 계획

- Spotify API 연동
- 딥러닝 기반 추천 모델
- 사용자 취향 학습
- 플레이리스트 자동 생성
- 실시간 추천 시스템

---

## 👨‍💻 개발 목적

본 프로젝트는

- FastAPI 학습
- React 학습
- 오디오 데이터 분석
- 추천 시스템 구현
- AI 서비스 개발 경험

을 목표로 진행되었습니다.
