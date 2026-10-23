"""Offline tests for exercise 3."""

import importlib.util
import json
import os
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load_exercise():
    if os.environ.get("SOLUTION") == "1":
        path = HERE.parent / "solutions" / "python" / "solution.py"
    else:
        path = HERE / "starter.py"
    spec = importlib.util.spec_from_file_location("ex03_break_points", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ex = load_exercise()
LIVE = json.loads((ROOT / "fixtures" / "matches_live.json").read_text(encoding="utf-8"))["response"]["body"]["data"]


def score(p1, p2, server, is_tiebreak=False):
    return {"points": [p1, p2], "server": server, "is_tiebreak": is_tiebreak}


def test_point_values():
    assert [ex.point_value(p) for p in ["0", "15", "30", "40", "AD"]] == [0, 1, 2, 3, 4]


def test_unknown_point_value():
    with pytest.raises(ValueError) as error:
        ex.point_value("45")
    assert not isinstance(error.value, NotImplementedError)


@pytest.mark.parametrize(
    "points, server, held",
    [
        (("0", "40"), 1, 3),   # 0-40, player 2 receiving
        (("15", "40"), 1, 2),
        (("30", "40"), 1, 1),
        (("40", "0"), 2, 3),   # same thing with player 1 receiving
        (("40", "30"), 2, 1),
        (("40", "AD"), 1, 1),  # advantage receiver
        (("AD", "40"), 2, 1),
        (("40", "40"), 1, 0),  # deuce is not a break point
        (("AD", "40"), 1, 0),  # advantage server
        (("40", "15"), 1, 0),  # server holds game points
        (("0", "0"), 2, 0),
        (("30", "30"), 1, 0),
    ],
)
def test_break_points_held(points, server, held):
    assert ex.break_points_held(score(*points, server)) == held
    assert ex.is_break_point(score(*points, server)) is (held > 0)


def test_a_number_is_not_a_point_value():
    with pytest.raises(ValueError) as error:
        ex.point_value(40)
    assert not isinstance(error.value, NotImplementedError)


def test_tiebreak_has_no_break_points():
    # 5-6 in a tiebreak with player 1 serving would look like danger, but it is not a break point.
    assert ex.is_break_point(score("5", "6", 1, is_tiebreak=True)) is False
    assert ex.break_points_held(score("0", "40", 1, is_tiebreak=True)) == 0


@pytest.mark.parametrize("bad", [None, {}, {"points": ["0", "40"], "server": None, "is_tiebreak": False}, {"points": [], "server": 1}])
def test_missing_data_is_not_a_break_point(bad):
    assert ex.is_break_point(bad) is False


def test_find_break_points_in_recorded_slate():
    # 209391: 15-40 with player 1 serving. 207819: 40-AD with player 1 serving.
    assert ex.find_break_points(LIVE) == [209391, 207819]


def test_find_break_points_skips_non_live():
    finished = {"id": 1, "status": "completed", "score": score("0", "40", 1)}
    live = {"id": 2, "status": "live", "score": score("0", "40", 1)}
    upcoming = {"id": 3, "status": "upcoming", "score": None}
    assert ex.find_break_points([finished, live, upcoming]) == [2]
