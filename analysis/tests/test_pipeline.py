import json

import numpy as np

from balancetrack import cli
from balancetrack.mesh import read_stl


def region(report, name):
    return report["insole"]["regions_mm"][name]


def run(tmp_path, session_file, profile, foot="left"):
    path, _ = session_file(profile, minutes=2, seed=2)
    out = tmp_path / profile
    cli.main(["run", str(path), "--height", "175", "--weight", "70", "--shoe", "10",
              "--foot", foot, "-o", str(out), "--no-plot", "--both"])
    with open(out / f"report_{foot}.json") as f:
        return json.load(f), out


def test_normal_gait_gives_flat_insole(tmp_path, session_file):
    report, out = run(tmp_path, session_file, "normal")
    assert report["rules"] == []
    assert report["insole"]["max_mm"] - report["insole"]["min_mm"] < 0.1
    assert (out / "insole_left.stl").exists()
    assert (out / "insole_right.stl").exists()


def test_medial_roll_builds_up_medial_side(tmp_path, session_file):
    report, _ = run(tmp_path, session_file, "medial")
    assert any(r["rule"] == "medial arch post" for r in report["rules"])
    assert region(report, "arch_medial") > region(report, "arch_lateral") + 0.5


def test_lateral_roll_builds_up_lateral_side(tmp_path, session_file):
    report, _ = run(tmp_path, session_file, "lateral", foot="right")
    assert region(report, "arch_lateral") > region(report, "arch_medial") + 0.5


def test_mirrored_stl(tmp_path, session_file):
    _, out = run(tmp_path, session_file, "medial")
    left = read_stl(out / "insole_left.stl")
    right = read_stl(out / "insole_right.stl")
    assert len(left) == len(right)
    lv = np.concatenate([left["v0"], left["v1"], left["v2"]])
    rv = np.concatenate([right["v0"], right["v1"], right["v2"]])
    assert np.allclose(lv.min(axis=0), rv.min(axis=0))
    assert np.allclose(lv.max(axis=0), rv.max(axis=0))


def test_simulate_command(tmp_path):
    out = tmp_path / "fake.csv"
    cli.main(["simulate", "--profile", "shuffle", "--minutes", "0.5", "-o", str(out)])
    assert out.read_text().startswith("t_ms,ax,ay,az")
