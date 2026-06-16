from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def _flatten_features(features: dict[str, Any]) -> np.ndarray:
    parts: list[float] = []
    parts.append(float(features.get("tempo", 0.0) or 0.0))
    parts.append(float(features.get("zcr_mean", 0.0) or 0.0))
    parts.append(float(features.get("zcr_std", 0.0) or 0.0))
    parts.append(float(features.get("spectral_centroid_mean", 0.0) or 0.0))
    parts.append(float(features.get("spectral_centroid_std", 0.0) or 0.0))

    for k in ["chroma_mean", "mfcc_mean", "mfcc_std"]:
        arr = features.get(k) or []
        parts.extend([float(x or 0.0) for x in arr])

    v = np.array(parts, dtype=np.float32)
    v = np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0)
    return v


def _euclidean(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def recommend_similar(
    *,
    songs: list[dict[str, Any]],
    query_song_id: int,
    top_n: int = 5,
    metric: str = "cosine",
) -> list[dict[str, Any]]:
    query = next(s for s in songs if s["id"] == query_song_id)
    query_vec = _flatten_features(query["features"])

    candidates = [s for s in songs if s["id"] != query_song_id]
    if not candidates:
        return []

    cand_vecs = np.vstack([_flatten_features(s["features"]) for s in candidates])

    metric = (metric or "cosine").lower()
    if metric == "cosine":
        sims = cosine_similarity(query_vec.reshape(1, -1), cand_vecs)[0]
        scored = list(zip(candidates, [float(x) for x in sims]))
        scored.sort(key=lambda x: x[1], reverse=True)
        out = []
        for s, score in scored[: max(0, int(top_n))]:
            out.append({"id": s["id"], "filename": s["filename"], "score": score})
        return out

    if metric in ["euclidean", "l2"]:
        dists = [_euclidean(query_vec, v) for v in cand_vecs]
        scored = list(zip(candidates, dists))
        scored.sort(key=lambda x: x[1])
        out = []
        for s, dist in scored[: max(0, int(top_n))]:
            out.append({"id": s["id"], "filename": s["filename"], "distance": float(dist)})
        return out

    raise ValueError("metric must be one of: cosine, euclidean")

