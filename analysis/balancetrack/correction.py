from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter

from .outline import Outline

BASE_MM = 3.0
MIN_MM = 3.0
MAX_MM = 12.0
TRIGGER = 1.5


def bump(outline: Outline, u0, v0, su, sv):
    return np.exp(-0.5 * (((outline.u - u0) / su) ** 2 + ((outline.v - v0) / sv) ** 2))


def strength(z, per_z, cap):
    return float(min(cap, per_z * (abs(z) - TRIGGER) + per_z))


def smooth_inside(grid, mask, sigma):
    weights = gaussian_filter(mask.astype(float), sigma)
    blurred = gaussian_filter(np.where(mask, grid, 0.0), sigma)
    out = np.where(weights > 1e-6, blurred / np.maximum(weights, 1e-6), grid)
    return np.where(mask, out, 0.0)


def build_thickness(outline: Outline, z: Dict[str, float], bmi: float) -> Tuple[np.ndarray, List[dict]]:
    mask = outline.mask
    grid = np.full(mask.shape, BASE_MM)
    rules = []

    if bmi >= 30:
        grid += 0.5
        rules.append({"rule": "firmer base", "reason": f"BMI {bmi:.1f}", "mm": 0.5})

    roll_z = z["stance_roll_deg"]
    if roll_z >= TRIGGER:
        mm = strength(roll_z, 1.2, 4.0)
        arch = bump(outline, 0.38, 0.75, 0.14, 0.35)
        heel_wedge = np.clip((outline.v + 1) / 2, 0, 1) * np.clip((0.3 - outline.u) / 0.3, 0, 1)
        grid += mm * arch + 0.5 * mm * heel_wedge
        rules.append({"rule": "medial arch post", "reason": f"foot rolls inward (z={roll_z:.1f})", "mm": mm})
    elif roll_z <= -TRIGGER:
        mm = strength(roll_z, 1.0, 3.5)
        wedge = np.clip((-outline.v + 1) / 2, 0, 1) ** 1.5
        lateral = bump(outline, 0.3, -0.8, 0.25, 0.4) + 0.7 * bump(outline, 0.72, -0.8, 0.12, 0.4)
        grid += mm * np.maximum(wedge * (outline.u < 0.85), lateral)
        rules.append({"rule": "lateral wedge", "reason": f"foot rolls outward (z={roll_z:.1f})", "mm": mm})

    unstable_z = max(z["stance_roll_sd_deg"], z["stride_time_cv"])
    if unstable_z >= TRIGGER:
        mm = strength(unstable_z, 1.0, 4.0)
        edge_dist = distance_transform_edt(mask) * outline.cell_mm
        rim = np.clip(1.0 - edge_dist / 8.0, 0, 1) * np.clip((0.35 - outline.u) / 0.12, 0, 1)
        grid += mm * rim + 0.5
        rules.append({"rule": "heel cup and stiffer base", "reason": f"step to step instability (z={unstable_z:.1f})", "mm": mm})

    impact_z = z["peak_accel_mps2"]
    if impact_z >= TRIGGER:
        mm = strength(impact_z, 0.6, 2.0)
        grid += mm * bump(outline, 0.1, 0.0, 0.08, 0.6)
        rules.append({"rule": "heel pad", "reason": f"hard heel strike (z={impact_z:.1f})", "mm": mm})

    grid = np.clip(grid, MIN_MM, MAX_MM)
    grid = smooth_inside(grid, mask, sigma=2.0 / outline.cell_mm)
    grid = np.where(mask, np.clip(grid, MIN_MM, MAX_MM), 0.0)
    return grid, rules


def region_means(outline: Outline, grid: np.ndarray) -> Dict[str, float]:
    m = outline.mask
    regions = {
        "heel": m & (outline.u < 0.25),
        "arch_medial": m & (outline.u >= 0.25) & (outline.u < 0.55) & (outline.v > 0),
        "arch_lateral": m & (outline.u >= 0.25) & (outline.u < 0.55) & (outline.v <= 0),
        "forefoot_medial": m & (outline.u >= 0.55) & (outline.v > 0),
        "forefoot_lateral": m & (outline.u >= 0.55) & (outline.v <= 0),
    }
    return {k: float(grid[r].mean()) if r.any() else 0.0 for k, r in regions.items()}
