from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional, Tuple

NORMS_PATH = Path(__file__).parent / "data" / "reference_norms.json"

COMPARED = ["stride_time_s", "stride_time_cv", "stance_roll_deg", "stance_roll_sd_deg",
            "pitch_range_deg", "peak_accel_mps2"]


def load_norms(path: Optional[Path] = None) -> dict:
    with open(path or NORMS_PATH) as f:
        return json.load(f)


def bmi(height_cm: float, weight_kg: float) -> float:
    return weight_kg / (height_cm / 100.0) ** 2


def expected(height_cm: float, weight_kg: float, norms: Optional[dict] = None) -> Dict[str, Tuple[float, float]]:
    if height_cm < 100 or height_cm > 230:
        raise ValueError("height should be in cm")
    if weight_kg < 25 or weight_kg > 250:
        raise ValueError("weight should be in kg")

    n = norms or load_norms()
    stride_length = n["stride_length_per_height"] * height_cm / 100.0
    stride_time = stride_length / n["walking_speed_mps"]

    peak = n["peak_accel_mps2"]["mean"] * (1 + n["peak_accel_per_bmi"] * (bmi(height_cm, weight_kg) - n["bmi_reference"]) / 10.0)

    ref = {
        "stride_time_s": (stride_time, n["stride_time_sd"]),
        "peak_accel_mps2": (peak, n["peak_accel_mps2"]["sd"]),
    }
    for key in ["stride_time_cv", "stance_roll_deg", "stance_roll_sd_deg", "pitch_range_deg"]:
        ref[key] = (n[key]["mean"], n[key]["sd"])
    return ref


def zscores(summary: Dict[str, float], ref: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
    return {k: (summary[k] - ref[k][0]) / ref[k][1] for k in COMPARED}
