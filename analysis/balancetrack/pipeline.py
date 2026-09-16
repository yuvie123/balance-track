from __future__ import annotations

from pathlib import Path

import numpy as np

from . import report
from .correction import build_thickness, region_means
from .features import stride_features, summarize
from .io import load_session
from .mesh import heightfield_mesh, is_watertight, volume, write_stl
from .outline import make_outline
from .reference import bmi, expected, zscores
from .steps import detect_steps


def analyze(csv_path, out_dir, height, weight, shoe, system, foot, plot=True):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    session = load_session(csv_path)
    steps = detect_steps(session)
    strides = stride_features(session, steps)
    summary = summarize(session, strides)

    ref = expected(height, weight)
    z = zscores(summary, ref)
    person_bmi = bmi(height, weight)

    outline = make_outline(shoe, system, foot)
    thickness, rules = build_thickness(outline, z, person_bmi)

    np.savez_compressed(
        out_dir / f"insole_{foot}.npz",
        thickness=thickness,
        mask=outline.mask,
        cell_mm=outline.cell_mm,
        foot=foot,
    )

    result = {
        "session": str(csv_path),
        "person": {"height_cm": height, "weight_kg": weight, "bmi": round(person_bmi, 1),
                   "shoe": shoe, "system": system, "foot": foot},
        "summary": summary,
        "expected": {k: {"mean": m, "sd": s} for k, (m, s) in ref.items()},
        "z": z,
        "rules": rules,
        "insole": {
            "length_mm": outline.length_mm,
            "min_mm": float(thickness[outline.mask].min()),
            "max_mm": float(thickness[outline.mask].max()),
            "regions_mm": region_means(outline, thickness),
        },
        "gaps": len(session.gaps),
    }
    report.write_json(out_dir / f"report_{foot}.json", result)
    if plot:
        report.plot(out_dir / f"report_{foot}.png", session, steps, z, outline, thickness)
    return result


def build(npz_path, stl_path, mirror=False):
    data = np.load(npz_path)
    thickness = data["thickness"]
    mask = data["mask"]
    if mirror:
        thickness = thickness[:, ::-1]
        mask = mask[:, ::-1]

    vertices, faces = heightfield_mesh(thickness, mask, float(data["cell_mm"]))
    if not is_watertight(faces):
        raise RuntimeError("mesh is not watertight, not writing it")
    write_stl(stl_path, vertices, faces)
    return {"triangles": len(faces), "volume_cm3": volume(vertices, faces) / 1000.0}
