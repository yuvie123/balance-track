from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, filtfilt, find_peaks

from .io import GRAVITY, Session


@dataclass
class Steps:
    peaks: np.ndarray
    signal: np.ndarray
    threshold: float

    def __len__(self):
        return len(self.peaks)


def lowpass(x, fs, cutoff):
    b, a = butter(4, cutoff / (fs / 2.0), btype="low")
    return filtfilt(b, a, x)


def split_heights(heights, iters=30):
    lo, hi = np.percentile(heights, 25), np.percentile(heights, 90)
    for _ in range(iters):
        cut = (lo + hi) / 2.0
        low = heights[heights < cut]
        high = heights[heights >= cut]
        if len(low) == 0 or len(high) == 0:
            break
        new_lo, new_hi = low.mean(), high.mean()
        if np.isclose(new_lo, lo) and np.isclose(new_hi, hi):
            break
        lo, hi = new_lo, new_hi
    return lo, hi


def detect_steps(session: Session, refractory=0.35, cutoff=20.0, k=4.0, split=0.4) -> Steps:
    sig = lowpass(session.acc_mag - GRAVITY, session.fs, cutoff)
    distance = max(1, int(refractory * session.fs))

    med = np.median(sig)
    mad = np.median(np.abs(sig - med)) * 1.4826
    noise_floor = med + k * mad

    candidates, _ = find_peaks(sig, distance=distance)
    if len(candidates) < 4:
        return Steps(np.array([], dtype=int), sig, noise_floor)

    # heel strikes and everything else (push off, swing) form two groups of peak heights
    lo, hi = split_heights(sig[candidates])
    threshold = max(noise_floor, lo + split * (hi - lo))

    # refractory window keeps the bounce right after a heel strike from counting as another step
    peaks, _ = find_peaks(sig, height=threshold, distance=distance)
    return Steps(peaks, sig, float(threshold))
