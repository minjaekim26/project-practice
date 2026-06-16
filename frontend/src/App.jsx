import React, { useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function apiJson(path, init) {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || `HTTP ${res.status}`);
  }
  return await res.json();
}

export default function App() {
  const [file, setFile] = useState(null);
  const [songs, setSongs] = useState([]);
  const [selectedSongId, setSelectedSongId] = useState("");
  const [recommendations, setRecommendations] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const selectedIdNum = useMemo(() => {
    const n = Number(selectedSongId);
    return Number.isFinite(n) ? n : null;
  }, [selectedSongId]);

  async function refreshSongs() {
    const data = await apiJson("/songs");
    setSongs(data.songs || []);
  }

  async function handleUpload(e) {
    e.preventDefault();
    setError("");
    setRecommendations(null);
    if (!file) {
      setError("업로드할 파일을 선택해 주세요.");
      return;
    }
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const up = await apiJson("/upload", { method: "POST", body: fd });
      await refreshSongs();
      setSelectedSongId(String(up.song_id));
    } catch (err) {
      setError(err?.message || String(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleRecommend() {
    setError("");
    setRecommendations(null);
    if (!selectedIdNum) {
      setError("추천 기준 곡을 선택해 주세요.");
      return;
    }
    setBusy(true);
    try {
      const data = await apiJson(`/recommend/${selectedIdNum}?top_n=5&metric=cosine`);
      setRecommendations(data);
    } catch (err) {
      setError(err?.message || String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <header className="header">
        <div className="title">Music Recommendation</div>
        <div className="subtitle">파일 업로드 → 특징 추출 → 유사 곡 추천</div>
      </header>

      <main className="grid">
        <section className="card">
          <div className="cardTitle">1) 음악 업로드</div>
          <form onSubmit={handleUpload} className="row">
            <input
              type="file"
              accept=".mp3,.wav,.flac,.ogg,.m4a"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              disabled={busy}
            />
            <button className="btn" type="submit" disabled={busy}>
              {busy ? "처리 중..." : "업로드"}
            </button>
          </form>
          <div className="hint">백엔드: {API_BASE}</div>
        </section>

        <section className="card">
          <div className="cardTitle">2) 등록된 곡</div>
          <div className="row">
            <button className="btnSecondary" onClick={refreshSongs} disabled={busy}>
              목록 새로고침
            </button>
            <select
              value={selectedSongId}
              onChange={(e) => setSelectedSongId(e.target.value)}
              disabled={busy}
            >
              <option value="">추천 기준 곡 선택</option>
              {songs.map((s) => (
                <option key={s.id} value={s.id}>
                  #{s.id} {s.filename}
                </option>
              ))}
            </select>
            <button className="btn" onClick={handleRecommend} disabled={busy}>
              추천 받기
            </button>
          </div>
        </section>

        <section className="card full">
          <div className="cardTitle">3) 추천 결과</div>
          {error ? <div className="error">{error}</div> : null}
          {recommendations?.recommendations?.length ? (
            <ul className="list">
              {recommendations.recommendations.map((r) => (
                <li key={r.id} className="listItem">
                  <div className="primary">
                    #{r.id} {r.filename}
                  </div>
                  <div className="secondary">
                    {"score" in r ? `cosine=${r.score.toFixed(4)}` : `dist=${Number(r.distance).toFixed(4)}`}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="empty">아직 결과가 없어요. 업로드 후 추천 기준 곡을 선택해 주세요.</div>
          )}
        </section>
      </main>
    </div>
  );
}

