import pytest

from balancetrack.features import stride_features, summarize
from balancetrack.reference import expected, zscores
from balancetrack.steps import detect_steps


def run(session, profile):
    s, _ = session(profile, minutes=2, seed=1)
    strides = stride_features(s, detect_steps(s))
    return zscores(summarize(s, strides), expected(175, 70))


def test_normal_gait_within_range(session):
    z = run(session, "normal")
    assert all(abs(v) < 1.5 for v in z.values())


def test_roll_direction(session):
    assert run(session, "medial")["stance_roll_deg"] > 1.5
    assert run(session, "lateral")["stance_roll_deg"] < -1.5


def test_instability_and_impact(session):
    assert run(session, "unstable")["stance_roll_sd_deg"] > 1.5
    assert run(session, "hard")["peak_accel_mps2"] > 1.5


def test_too_short_session(session):
    s, _ = session("normal", minutes=0.05)
    with pytest.raises(ValueError):
        summarize(s, stride_features(s, detect_steps(s)))


def test_reference_scales_with_height():
    short = expected(150, 50)["stride_time_s"][0]
    tall = expected(195, 90)["stride_time_s"][0]
    assert tall > short


def test_reference_rejects_wrong_units():
    with pytest.raises(ValueError):
        expected(5.9, 70)
