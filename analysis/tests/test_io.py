import numpy as np
import pytest

from balancetrack.io import COLUMNS, load_session


def test_resamples_to_uniform_rate(session):
    s, _ = session()
    assert np.allclose(np.diff(s.t), 0.01)
    assert s.acc.shape == (len(s.t), 3)


def test_handles_unsorted_and_duplicate_rows(tmp_path):
    rows = [
        [20, 0, 0, 9.81, 0, 0, 0, 0, 0, 100],
        [0, 0, 0, 9.81, 0, 0, 0, 0, 0, 100],
        [10, 0, 0, 9.81, 0, 0, 0, 0, 0, 100],
        [10, 0, 0, 9.81, 0, 0, 0, 0, 0, 100],
        [200, 0, 0, 9.81, 0, 0, 0, 0, 0, 100],
    ]
    path = tmp_path / "s.csv"
    np.savetxt(path, rows, delimiter=",", header=",".join(COLUMNS), comments="", fmt="%g")
    with pytest.warns(UserWarning):
        s = load_session(path)
    assert len(s.gaps) == 1
    assert s.t[0] == 0


def test_missing_columns(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("t_ms,ax\n0,1\n10,2\n")
    with pytest.raises(ValueError, match="missing columns"):
        load_session(path)
