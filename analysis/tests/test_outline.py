import numpy as np
import pytest

from balancetrack.outline import foot_length_mm, make_outline


@pytest.mark.parametrize("size,system,expected_mm", [
    (42, "eu", 265.0),
    (10, "us-men", 270.9),
    (8, "us-women", 245.5),
    (9, "uk", 270.9),
])
def test_foot_length(size, system, expected_mm):
    assert foot_length_mm(size, system) == pytest.approx(expected_mm, abs=0.5)


def test_outline_size():
    o = make_outline(10, "us-men", "left")
    rows = np.nonzero(o.mask.any(axis=1))[0]
    cols = np.nonzero(o.mask.any(axis=0))[0]
    length = (rows[-1] - rows[0] + 1) * o.cell_mm
    width = (cols[-1] - cols[0] + 1) * o.cell_mm
    assert length == pytest.approx(o.length_mm, abs=5)
    assert 85 < width < 115


def test_left_and_right_mirror():
    left = make_outline(9, "us-men", "left")
    right = make_outline(9, "us-men", "right")
    assert np.array_equal(left.mask, right.mask[:, ::-1])


def test_no_corner_only_cells():
    m = make_outline(7.5, "us-women", "right").mask
    a, b, c, d = m[:-1, :-1], m[:-1, 1:], m[1:, :-1], m[1:, 1:]
    assert not (a & d & ~b & ~c).any()
    assert not (b & c & ~a & ~d).any()


def test_bad_inputs():
    with pytest.raises(ValueError):
        foot_length_mm(10, "jp")
    with pytest.raises(ValueError):
        make_outline(10, "us-men", "middle")
