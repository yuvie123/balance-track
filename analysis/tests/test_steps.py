import numpy as np
import pytest

from balancetrack.steps import detect_steps


@pytest.mark.parametrize("profile", ["normal", "medial", "unstable", "shuffle", "hard"])
def test_step_count_matches(session, profile):
    s, strikes = session(profile, minutes=2)
    steps = detect_steps(s)
    assert abs(len(steps) - len(strikes)) <= max(1, 0.02 * len(strikes))


def test_peaks_line_up_with_heel_strikes(session):
    s, strikes = session("normal", minutes=1)
    steps = detect_steps(s)
    detected = s.t[steps.peaks]
    nearest = np.abs(detected[:, None] - strikes[None, :]).min(axis=1)
    assert np.all(nearest < 0.05)


def test_heel_bounce_counted_once(session):
    s, strikes = session("unstable", minutes=2, seed=3)
    steps = detect_steps(s)
    assert np.diff(s.t[steps.peaks]).min() > 0.35
    assert abs(len(steps) - len(strikes)) <= 1


def test_standing_still_has_no_steps(session):
    s, _ = session("normal", minutes=0.01)
    s.t = s.t[:250]
    s.acc = s.acc[:250]
    assert len(detect_steps(s)) == 0
