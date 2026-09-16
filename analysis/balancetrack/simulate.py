from __future__ import annotations

import numpy as np

from .io import COLUMNS, GRAVITY

PROFILES = {
    "normal": dict(stride=1.10, stride_sd=0.025, roll=0.5, roll_sd=0.8, heel=14.0, double=0.1, pitch_scale=1.0),
    "medial": dict(stride=1.12, stride_sd=0.03, roll=9.0, roll_sd=1.0, heel=15.0, double=0.1, pitch_scale=1.0),
    "lateral": dict(stride=1.12, stride_sd=0.03, roll=-9.0, roll_sd=1.0, heel=15.0, double=0.1, pitch_scale=1.0),
    "unstable": dict(stride=1.20, stride_sd=0.12, roll=1.0, roll_sd=5.0, heel=16.0, double=0.3, pitch_scale=0.9),
    "shuffle": dict(stride=0.95, stride_sd=0.06, roll=1.0, roll_sd=2.0, heel=8.0, double=0.0, pitch_scale=0.45),
    "hard": dict(stride=1.05, stride_sd=0.03, roll=0.5, roll_sd=1.0, heel=28.0, double=0.2, pitch_scale=1.1),
}

PITCH_KEYS = np.array([0.0, 0.1, 0.45, 0.62, 0.8, 1.0])
PITCH_VALS = np.array([15.0, 0.0, 0.0, -30.0, -5.0, 15.0])


def simulate(profile="normal", minutes=2.0, fs=100.0, seed=0, lead_in=3.0):
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile}, pick from {', '.join(PROFILES)}")
    p = PROFILES[profile]
    rng = np.random.default_rng(seed)

    walk_time = minutes * 60.0
    total = lead_in + walk_time + 2.0
    t = np.arange(0.0, total, 1.0 / fs)
    n = len(t)

    dyn = np.zeros(n)
    fwd = np.zeros(n)
    roll = np.zeros(n)
    pitch = np.zeros(n)

    strikes = []
    start = lead_in
    while start < lead_in + walk_time:
        T = max(0.6, rng.normal(p["stride"], p["stride_sd"]))
        strikes.append(start)

        mask = (t >= start) & (t < start + T)
        local = t[mask] - start
        phase = local / T

        heel = p["heel"] * rng.uniform(0.9, 1.1)
        dyn[mask] += heel * np.exp(-0.5 * (local / 0.02) ** 2)
        if rng.random() < p["double"]:
            dyn[mask] += 0.6 * heel * np.exp(-0.5 * ((local - 0.07) / 0.015) ** 2)
        dyn[mask] += 0.3 * heel * np.exp(-0.5 * ((local - 0.55 * T) / 0.05) ** 2)
        swing = phase >= 0.62
        dyn[mask] += np.where(swing, 2.0 * np.sin(2 * np.pi * (phase - 0.62) / 0.38), 0.0)
        fwd[mask] += 1.5 * np.sin(2 * np.pi * phase)

        stance_roll = rng.normal(p["roll"], p["roll_sd"])
        roll[mask] += np.where(phase < 0.6, stance_roll * np.sin(np.pi * phase / 0.6), 0.0)
        pitch[mask] += p["pitch_scale"] * np.interp(phase, PITCH_KEYS, PITCH_VALS)

        start += T

    roll += rng.normal(0, 0.3, n)
    pitch += rng.normal(0, 0.3, n)

    r = np.radians(roll)
    pt = np.radians(pitch)
    ax = -GRAVITY * np.sin(pt) + fwd
    ay = GRAVITY * np.sin(r) * np.cos(pt)
    az = GRAVITY * np.cos(r) * np.cos(pt) + dyn
    acc = np.column_stack([ax, ay, az]) + rng.normal(0, 0.25, (n, 3))

    gx = np.gradient(r, t) + rng.normal(0, 0.02, n)
    gy = np.gradient(pt, t) + rng.normal(0, 0.02, n)
    gz = rng.normal(0, 0.05, n)
    alt = 112.0 + np.cumsum(rng.normal(0, 0.002, n)) + rng.normal(0, 0.08, n)

    t_ms = np.round(t * 1000.0 + rng.integers(0, 2, n)).astype(int)
    keep = rng.random(n) > 0.002

    data = np.column_stack([t_ms, acc, gx, gy, gz, roll, pitch, alt])[keep]
    return data, np.array(strikes)


def write_csv(path, data):
    fmt = ["%d"] + ["%.3f"] * 3 + ["%.4f"] * 3 + ["%.2f"] * 3
    np.savetxt(path, data, delimiter=",", fmt=fmt, header=",".join(COLUMNS), comments="")
