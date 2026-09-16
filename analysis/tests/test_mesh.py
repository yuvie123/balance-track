import numpy as np
import pytest

from balancetrack.mesh import heightfield_mesh, is_watertight, read_stl, volume, write_stl
from balancetrack.outline import make_outline


def test_single_cell_is_a_box():
    v, f = heightfield_mesh(np.array([[2.0]]), np.array([[True]]), 1.0)
    assert len(f) == 12
    assert is_watertight(f)
    assert volume(v, f) == pytest.approx(2.0)


def test_flat_insole_volume():
    o = make_outline(10, "us-men")
    h = np.where(o.mask, 3.0, 0.0)
    v, f = heightfield_mesh(h, o.mask, o.cell_mm)
    assert is_watertight(f)
    assert volume(v, f) == pytest.approx(o.mask.sum() * 3.0, rel=1e-6)


def test_bumpy_insole_is_closed():
    o = make_outline(40, "eu", "right")
    rng = np.random.default_rng(0)
    h = np.where(o.mask, rng.uniform(3, 10, o.mask.shape), 0.0)
    v, f = heightfield_mesh(h, o.mask, o.cell_mm)
    assert is_watertight(f)
    assert volume(v, f) > 0


def test_detects_open_mesh():
    _, f = heightfield_mesh(np.array([[2.0]]), np.array([[True]]), 1.0)
    assert not is_watertight(f[:-1])


def test_stl_roundtrip(tmp_path):
    v, f = heightfield_mesh(np.array([[2.0, 3.0]]), np.array([[True, True]]), 1.0)
    path = tmp_path / "box.stl"
    write_stl(path, v, f)
    data = read_stl(path)
    assert len(data) == len(f)
    assert path.stat().st_size == 84 + 50 * len(f)
    assert np.allclose(data["v0"], v[f[:, 0]])
