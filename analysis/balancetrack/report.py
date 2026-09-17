from __future__ import annotations

import json

import numpy as np

LABELS = {
    "stride_time_s": "time per step",
    "stride_time_cv": "step timing wobble",
    "stance_roll_deg": "foot roll (in +, out -)",
    "stance_roll_sd_deg": "foot roll wobble",
    "pitch_range_deg": "heel to toe motion",
    "peak_accel_mps2": "heel impact",
}


def write_json(path, report):
    with open(path, "w") as f:
        json.dump(report, f, indent=2)


def plot(path, session, steps, zscores, outline, thickness, seconds=20.0):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(13, 7))
    grid = fig.add_gridspec(2, 3, width_ratios=[2, 2, 1.2])

    ax = fig.add_subplot(grid[0, :2])
    end = min(len(session.t), int(seconds * session.fs))
    ax.plot(session.t[:end], steps.signal[:end], lw=0.8, color="#3b6ea5")
    shown = steps.peaks[steps.peaks < end]
    ax.plot(session.t[shown], steps.signal[shown], "o", color="#d1495b", ms=4)
    ax.axhline(steps.threshold, ls="--", lw=0.8, color="gray")
    ax.set_title(f"each dot is a step (first {seconds:.0f}s shown, {len(steps)} steps total)")
    ax.set_xlabel("seconds")
    ax.set_ylabel("foot impact")

    ax = fig.add_subplot(grid[1, :2])
    names = list(zscores)
    values = [zscores[n] for n in names]
    colors = ["#d1495b" if abs(v) >= 1.5 else "#8aa9c9" for v in values]
    ax.barh([LABELS.get(n, n) for n in names], values, color=colors)
    ax.axvspan(-1.5, 1.5, color="gray", alpha=0.12)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_title("compared to normal (gray band = normal, red = needs support)")
    ax.set_xlabel("how far from normal")

    ax = fig.add_subplot(grid[:, 2])
    shown = np.ma.masked_where(~outline.mask, thickness)
    extent = [0, outline.mask.shape[1] * outline.cell_mm, 0, outline.mask.shape[0] * outline.cell_mm]
    im = ax.imshow(shown, origin="lower", cmap="viridis", extent=extent)
    ax.set_title(f"{outline.foot} insole from above")
    ax.set_xlabel("width (mm)")
    ax.set_ylabel("heel to toe (mm)")
    fig.colorbar(im, ax=ax, label="thickness (mm)")

    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
