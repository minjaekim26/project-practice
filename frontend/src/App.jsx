import React, { useMemo, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

function clamp(n, min, max) {
  return Math.max(min, Math.min(max, n));
}

function scoreToPercent(score) {
  // cosine similarity는 [-1, 1] 범위를 가질 수 있어 0~100으로 맵핑
  const p = ((Number(score) || 0) + 1) / 2;
  return Math.round(clamp(p, 0, 1) * 100);
}

function postRecommendWithProgress({ file, onProgress, signal }) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/recommend?top_k=10`);
    xhr.responseType = "json";

    xhr.upload.onprogress = (evt) => {
      if (!evt.lengthComputable) return;
      const pct = Math.round((evt.loaded / evt.total) * 100);
      onProgress?.(clamp(pct, 0, 100));
    };

    xhr.onload = () => {
      const ok = xhr.status >= 200 && xhr.status < 300;
      if (!ok) {
        const detail = xhr.response?.detail || xhr.response || xhr.statusText;
        reject(new Error(typeof detail === "string" ? detail : JSON.stringify(detail)));
        return;
      }
      resolve(xhr.response);
    };

    xhr.onerror = () => reject(new Error("Network error"));

    if (signal) {
      signal.addEventListener(
        "abort",
        () => {
          try {
            xhr.abort();
          } catch {
            // ignore
          }
          reject(new Error("Aborted"));
        },
        { once: true },
      );
    }

    const fd = new FormData();
    fd.append("file", file);
    xhr.send(fd);
  });
}

export default function App() {
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const abortRef = useRef(null);

  const fileMeta = useMemo(() => {
    if (!file) return null;
    return { name: file.name, sizeMb: (file.size / 1024 / 1024).toFixed(2) };
  }, [file]);

  async function handleRecommend(e) {
    e.preventDefault();
    setError("");
    setResult(null);

    if (!file) {
      setError("MP3 파일을 선택해 주세요.");
      return;
    }

    setBusy(true);
    setProgress(0);
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const data = await postRecommendWithProgress({
        file,
        onProgress: setProgress,
        signal: controller.signal,
      });
      setProgress(100);
      setResult(data);
    } catch (err) {
      setError(err?.message || String(err));
    } finally {
      setBusy(false);
      abortRef.current = null;
    }
  }

  function cancel() {
    abortRef.current?.abort();
  }

  const recs = result?.recommendations || [];

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-5xl px-4 py-10">
        <header className="mb-8 flex flex-col gap-3">
          <div className="inline-flex items-center gap-2">
            <div className="h-10 w-10 rounded-2xl bg-gradient-to-br from-sky-400/90 to-fuchsia-500/90 shadow-glow" />
            <h1 className="text-2xl font-extrabold tracking-tight sm:text-3xl">
              음악 추천 서비스
            </h1>
          </div>
          <p className="text-sm text-slate-300">
            MP3 업로드 → 특징 추출(librosa) → DB 곡들과 Cosine Similarity 비교 → Top 10 추천
          </p>
        </header>

        <div className="grid gap-6 lg:grid-cols-5">
          <section className="lg:col-span-2">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-glow backdrop-blur">
              <h2 className="text-sm font-semibold text-slate-200">MP3 업로드</h2>
              <form onSubmit={handleRecommend} className="mt-4 space-y-4">
                <label className="block">
                  <span className="sr-only">MP3 파일 선택</span>
                  <input
                    type="file"
                    accept=".mp3"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    disabled={busy}
                    className="block w-full cursor-pointer rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-slate-200 file:mr-4 file:rounded-lg file:border-0 file:bg-white/10 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-slate-100 hover:file:bg-white/15"
                  />
                </label>

                {fileMeta ? (
                  <div className="rounded-xl border border-white/10 bg-slate-950/30 px-3 py-2 text-xs text-slate-300">
                    <div className="font-semibold text-slate-200">{fileMeta.name}</div>
                    <div>{fileMeta.sizeMb} MB</div>
                  </div>
                ) : (
                  <div className="text-xs text-slate-400">
                    MP3 파일을 선택한 뒤 추천을 눌러주세요.
                  </div>
                )}

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs text-slate-300">
                    <span>업로드 진행</span>
                    <span className="tabular-nums">{busy ? `${progress}%` : "대기"}</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-sky-400 to-fuchsia-500 transition-[width] duration-200"
                      style={{ width: `${busy ? progress : 0}%` }}
                    />
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    type="submit"
                    disabled={busy}
                    className="inline-flex flex-1 items-center justify-center rounded-xl bg-gradient-to-r from-sky-400 to-fuchsia-500 px-4 py-2 text-sm font-extrabold text-slate-950 shadow-glow disabled:opacity-60"
                  >
                    {busy ? "분석/추천 중..." : "추천 받기"}
                  </button>
                  <button
                    type="button"
                    onClick={cancel}
                    disabled={!busy}
                    className="inline-flex items-center justify-center rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-slate-200 disabled:opacity-60"
                  >
                    취소
                  </button>
                </div>

                <div className="text-xs text-slate-400">
                  백엔드:{" "}
                  <span className="font-mono text-slate-300">{API_BASE}</span>
                </div>
              </form>
            </div>

            {error ? (
              <div className="mt-4 rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-100">
                {error}
              </div>
            ) : null}
          </section>

          <section className="lg:col-span-3">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-glow backdrop-blur">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-slate-200">추천 결과</h2>
                <div className="text-xs text-slate-400">
                  {recs.length ? `Top ${recs.length}` : "결과 없음"}
                </div>
              </div>

              {!recs.length ? (
                <div className="mt-6 rounded-xl border border-dashed border-white/10 bg-slate-950/20 p-6 text-sm text-slate-300">
                  MP3를 업로드하면 DB에 저장된 곡들과 비교해 유사한 곡 10개를 추천해요.
                </div>
              ) : (
                <ul className="mt-4 grid gap-3">
                  {recs.map((r, idx) => {
                    const pct = scoreToPercent(r.score);
                    return (
                      <li
                        key={r.id}
                        className="group rounded-2xl border border-white/10 bg-slate-950/25 p-4"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <div className="text-xs text-slate-400">
                              #{idx + 1} · ID {r.id}
                            </div>
                            <div className="mt-1 text-base font-bold text-slate-100">
                              {r.title}
                            </div>
                            <div className="text-sm text-slate-300">{r.artist}</div>
                          </div>

                          <div className="text-right">
                            <div className="text-xs font-semibold text-slate-300">
                              유사도
                            </div>
                            <div className="mt-1 font-mono text-sm text-slate-100 tabular-nums">
                              {Number(r.score).toFixed(4)}
                            </div>
                          </div>
                        </div>

                        <div className="mt-3">
                          <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-sky-400"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <div className="mt-1 text-right text-xs text-slate-400">
                            {pct}%
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

