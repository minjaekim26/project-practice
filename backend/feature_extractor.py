from __future__ import annotations

from typing import Any

import librosa
import numpy as np


def _safe_float(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return float("nan")


def extract_features(path: str, sr: int = 22050, duration: float | None = 60.0) -> dict[str, Any]:
    y, sr = librosa.load(path, sr=sr, mono=True, duration=duration)

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

    features: dict[str, Any] = {
        "tempo": _safe_float(tempo),
        "zcr_mean": _safe_float(np.mean(zcr)),
        "zcr_std": _safe_float(np.std(zcr)),
        "spectral_centroid_mean": _safe_float(np.mean(spectral_centroid)),
        "spectral_centroid_std": _safe_float(np.std(spectral_centroid)),
        "chroma_mean": [_safe_float(v) for v in np.mean(chroma, axis=1)],
        "mfcc_mean": [_safe_float(v) for v in np.mean(mfcc, axis=1)],
        "mfcc_std": [_safe_float(v) for v in np.std(mfcc, axis=1)],
    }

    return features

