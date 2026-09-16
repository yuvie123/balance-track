from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import binary_fill_holes, binary_opening, label

SYSTEMS = ("us-men", "us-women", "uk", "eu")

# fraction along the insole from heel to toe, half widths as a fraction of insole length
U = [0.0, 0.01, 0.03, 0.08, 0.18, 0.30, 0.42, 0.55, 0.68, 0.78, 0.87, 0.94, 0.98, 1.0]
MEDIAL = [0.0, 0.045, 0.075, 0.105, 0.115, 0.105, 0.095, 0.125, 0.17, 0.18, 0.165, 0.13, 0.08, 0.0]
LATERAL = [0.0, 0.045, 0.075, 0.105, 0.12, 0.13, 0.14, 0.15, 0.16, 0.155, 0.13, 0.085, 0.04, 0.0]

INSOLE_ALLOWANCE_MM = 6.0


@dataclass
class Outline:
    mask: np.ndarray
    cell_mm: float
    length_mm: float
    foot: str
    u: np.ndarray
    v: np.ndarray


def foot_length_mm(size: float, system: str) -> float:
    if system == "eu":
        return (size / 1.5 - 1.5) * 10.0
    if system == "us-men":
        return (size + 22.0) / 3.0 * 25.4
    if system == "us-women":
        return (size + 21.0) / 3.0 * 25.4
    if system == "uk":
        return (size + 23.0) / 3.0 * 25.4
    raise ValueError(f"unknown size system {system}, use one of {', '.join(SYSTEMS)}")


def half_widths(u):
    med = PchipInterpolator(U, MEDIAL)(u)
    lat = PchipInterpolator(U, LATERAL)(u)
    return np.clip(med, 0, None), np.clip(lat, 0, None)


def clean_mask(mask):
    mask = binary_opening(mask, structure=np.ones((3, 3)))
    mask = binary_fill_holes(mask)
    labels, count = label(mask)
    if count > 1:
        sizes = np.bincount(labels.ravel())[1:]
        mask = labels == (np.argmax(sizes) + 1)

    # cells that only touch at a corner make a pinched mesh, so fill in one side
    changed = True
    while changed:
        a = mask[:-1, :-1]
        b = mask[:-1, 1:]
        c = mask[1:, :-1]
        d = mask[1:, 1:]
        diag1 = a & d & ~b & ~c
        diag2 = b & c & ~a & ~d
        changed = bool(diag1.any() or diag2.any())
        r, col = np.nonzero(diag1)
        mask[r, col + 1] = True
        r, col = np.nonzero(diag2)
        mask[r, col] = True
    return mask


def make_outline(size: float, system: str, foot: str = "left", cell_mm: float = 1.0) -> Outline:
    if foot not in ("left", "right"):
        raise ValueError("foot must be left or right")

    length = foot_length_mm(size, system) + INSOLE_ALLOWANCE_MM
    max_med = max(MEDIAL) * length
    max_lat = max(LATERAL) * length

    rows = int(np.ceil(length / cell_mm)) + 2
    cols = int(np.ceil((max_med + max_lat) / cell_mm)) + 2

    y = (np.arange(rows) - 1 + 0.5) * cell_mm
    x = (np.arange(cols) - 1 + 0.5) * cell_mm - max_lat

    u = np.clip(y / length, 0.0, 1.0)
    med, lat = half_widths(u)
    inside_len = (y > 0) & (y < length)

    X, _ = np.meshgrid(x, y)
    mask = (X <= med[:, None] * length) & (X >= -lat[:, None] * length) & inside_len[:, None]
    mask = clean_mask(mask)

    scale = 0.17 * length
    U_grid = np.repeat(u[:, None], cols, axis=1)
    V_grid = np.clip(X / scale, -1.0, 1.0)

    # grid is built with the medial side on +x, which is how a left foot looks from above
    if foot == "right":
        mask = mask[:, ::-1]
        V_grid = V_grid[:, ::-1]

    return Outline(mask=mask, cell_mm=cell_mm, length_mm=length, foot=foot, u=U_grid, v=V_grid)
