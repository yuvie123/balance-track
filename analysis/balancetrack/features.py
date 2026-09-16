from __future__ import annotations

from typing import Dict, List

import numpy as np

from .io import GRAVITY, Session
from .steps import Steps, lowpass

MIN_STRIDE = 0.5
MAX_STRIDE = 2.5


def stride_features(session: Session, steps: Steps) -> List[Dict[str, float]]:
    fs = session.fs
    mag = session.acc_mag - GRAVITY
    jerk = np.abs(np.gradient(lowpass(session.acc_mag, fs, 20.0))) * fs
    strides = []

    for start, end in zip(steps.peaks[:-1], steps.peaks[1:]):
        duration = (end - start) / fs
        if duration < MIN_STRIDE or duration > MAX_STRIDE:
            continue

        stance_end = start + int(0.5 * (end - start))
        lo = max(0, start - int(0.03 * fs))
        hi = start + int(0.03 * fs) + 1

        strides.append({
            "start_s": float(session.t[start]),
            "duration_s": float(duration),
            "peak_accel": float(mag[lo:hi].max()),
            "stance_roll": float(session.roll[start:stance_end].mean()),
            "roll_range": float(np.ptp(session.roll[start:end])),
            "pitch_range": float(np.ptp(session.pitch[start:end])),
            "jerk_rms": float(np.sqrt(np.mean(jerk[start:end] ** 2))),
        })

    return strides


def summarize(session: Session, strides: List[Dict[str, float]]) -> Dict[str, float]:
    if len(strides) < 5:
        raise ValueError(f"only {len(strides)} usable strides found, walk for longer")

    def col(name):
        return np.array([s[name] for s in strides])

    durations = col("duration_s")
    roll = col("stance_roll")
    alt = lowpass(session.alt, session.fs, 0.5) if len(session.alt) > 30 else session.alt

    return {
        "strides": len(strides),
        "duration_s": session.duration,
        "cadence_spm": float(120.0 / np.median(durations)),
        "stride_time_s": float(durations.mean()),
        "stride_time_cv": float(durations.std() / durations.mean()),
        "stance_roll_deg": float(roll.mean()),
        "stance_roll_sd_deg": float(roll.std()),
        "roll_range_deg": float(col("roll_range").mean()),
        "pitch_range_deg": float(col("pitch_range").mean()),
        "peak_accel_mps2": float(col("peak_accel").mean()),
        "jerk_rms": float(col("jerk_rms").mean()),
        "altitude_change_m": float(np.ptp(alt)),
    }
