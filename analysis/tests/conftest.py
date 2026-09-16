import pytest

from balancetrack.io import load_session
from balancetrack.simulate import simulate, write_csv


@pytest.fixture
def session_file(tmp_path):
    def make(profile="normal", minutes=1.5, seed=0):
        data, strikes = simulate(profile, minutes, seed=seed)
        path = tmp_path / f"{profile}_{seed}.csv"
        write_csv(path, data)
        return path, strikes
    return make


@pytest.fixture
def session(session_file):
    def make(profile="normal", minutes=1.5, seed=0):
        path, strikes = session_file(profile, minutes, seed)
        return load_session(path), strikes
    return make
