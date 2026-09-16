from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np

COLUMNS = ["t_ms", "ax", "ay", "az", "gx", "gy", "gz", "roll", "pitch", "alt_m"]
GRAVITY = 9.81


@dataclass
class Session:
    t: np.ndarray
    acc: np.ndarray
    gyro: np.ndarray
    roll: np.ndarray
    pitch: np.ndarray
    alt: np.ndarray
    fs: float
    gaps: List[Tuple[float, float]] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return float(self.t[-1] - self.t[0])

    @property
    def acc_mag(self) -> np.ndarray:
        return np.linalg.norm(self.acc, axis=1)


def load_session(path, fs: float = 100.0, max_gap_ms: float = 50.0) -> Session:
    raw = np.genfromtxt(path, delimiter=",", names=True, dtype=float)
    if raw.size == 0:
        raise ValueError(f"{path} has no data")

    missing = [c for c in COLUMNS if c not in raw.dtype.names]
    if missing:
        raise ValueError(f"{path} is missing columns: {', '.join(missing)}")

    raw = np.atleast_1d(raw)
    keep = np.all([np.isfinite(raw[c]) for c in COLUMNS], axis=0)
    raw = raw[keep]

    t_ms = raw["t_ms"]
    order = np.argsort(t_ms, kind="stable")
    raw = raw[order]
    t_ms = raw["t_ms"]
    _, first = np.unique(t_ms, return_index=True)
    raw = raw[first]
    t_ms = raw["t_ms"]

    if len(t_ms) < 2:
        raise ValueError(f"{path} is too short to analyze")

    diffs = np.diff(t_ms)
    gaps = [(t_ms[i] / 1000.0, diffs[i]) for i in np.nonzero(diffs > max_gap_ms)[0]]
    if gaps:
        warnings.warn(f"{len(gaps)} gaps longer than {max_gap_ms:.0f} ms, interpolating over them")

    t_src = (t_ms - t_ms[0]) / 1000.0
    t = np.arange(0.0, t_src[-1], 1.0 / fs)

    def resample(name):
        return np.interp(t, t_src, raw[name])

    acc = np.column_stack([resample("ax"), resample("ay"), resample("az")])
    gyro = np.column_stack([resample("gx"), resample("gy"), resample("gz")])

    return Session(
        t=t,
        acc=acc,
        gyro=gyro,
        roll=resample("roll"),
        pitch=resample("pitch"),
        alt=resample("alt_m"),
        fs=fs,
        gaps=gaps,
    )
