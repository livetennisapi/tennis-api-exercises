"""Offline tests for exercise 2.

Some cases come from the recorded live slate in fixtures/matches_live.json.
The edge cases are built by hand with make_match, because a recording only
holds the states that happened to be live when it was made.
"""

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
    spec = importlib.util.spec_from_file_location("ex02_read_a_score", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ex = load_exercise()
LIVE = json.loads((ROOT / "fixtures" / "matches_live.json").read_text(encoding="utf-8"))["response"]["body"]["data"]


def live_match(match_id):
    return next(match for match in LIVE if match["id"] == match_id)


def make_match(games, points=("0", "0"), server=1, is_tiebreak=False, sets=(0, 0), status="live"):
    return {
        "status": status,
        "players": {"p1": {"name": "Jannik Sinner"}, "p2": {"name": "Carlos Alcaraz"}},
        "score": {
            "sets": list(sets),
            "games": games,
            "points": list(points),
            "server": server,
            "is_tiebreak": is_tiebreak,
        },
    }


def test_set_scores_are_player_major():
    assert ex.set_scores([[6, 3], [4, 4]]) == ["6-4", "3-4"]
    assert ex.set_scores([[6, 3, 2], [4, 6, 1]]) == ["6-4", "3-6", "2-1"]


def test_set_scores_with_match_tiebreak():
    assert ex.set_scores([[6, 4, 10], [4, 6, 5]], match_tiebreak=True) == ["6-4", "4-6", "[10-5]"]


def test_example_from_the_brief():
    match = make_match([[6, 3], [4, 4]], points=("30", "15"), sets=(1, 0))
    assert ex.format_score(match) == "6-4 3-4, 30-15, Jannik Sinner serving"


@pytest.mark.parametrize(
    "match_id, expected",
    [
        (207981, "6-4 3-6 2-0, 0-15, Corentin Moutet serving"),
        (207819, "1-1, advantage Elmer Moller, Henrique Rocha serving"),
        (208138, "0-1, 30-30, Jiri Lehecka serving"),
        (208279, "0-0, 30-30, Ana Sofia Sanchez serving"),
    ],
)
def test_recorded_live_matches(match_id, expected):
    assert ex.format_score(live_match(match_id)) == expected


def test_every_recorded_match_formats():
    for match in LIVE:
        line = ex.format_score(match)
        assert isinstance(line, str) and line


def test_not_started():
    match = make_match([[0], [0]])
    match["score"] = None
    assert ex.format_score(match) == "not started"


def test_withheld_score():
    match = make_match(None)
    assert ex.format_score(match) == "score unavailable"


def test_no_games_yet():
    assert ex.format_score(make_match([[], []])) == "0-0, 0-0, Jannik Sinner serving"


def test_deuce():
    match = make_match([[2], [2]], points=("40", "40"), server=2)
    assert ex.format_score(match) == "2-2, deuce, Carlos Alcaraz serving"


def test_advantage_player_one():
    match = make_match([[2], [2]], points=("AD", "40"), server=2)
    assert ex.format_score(match) == "2-2, advantage Jannik Sinner, Carlos Alcaraz serving"


def test_tiebreak_points():
    match = make_match([[6, 6], [4, 6]], points=("5", "3"), is_tiebreak=True, sets=(1, 0))
    assert ex.format_score(match) == "6-4 6-6, tiebreak 5-3, Jannik Sinner serving"


def test_match_tiebreak():
    match = make_match([[6, 4, 10], [4, 6, 5]], points=("0", "0"), server=2, is_tiebreak=True, sets=(1, 1))
    assert ex.is_match_tiebreak(match["score"]) is True
    assert ex.format_score(match) == "6-4 4-6 [10-5], Carlos Alcaraz serving"


def test_ordinary_tiebreak_is_not_a_match_tiebreak():
    match = make_match([[6, 6], [4, 6]], points=("5", "3"), is_tiebreak=True)
    assert ex.is_match_tiebreak(match["score"]) is False


def test_finished_match():
    match = make_match([[6, 6], [4, 3]], sets=(2, 0), status="completed", server=None)
    assert ex.format_score(match) == "6-4 6-3, Jannik Sinner won"


def test_finished_match_player_two_wins():
    match = make_match([[6, 3, 4], [4, 6, 6]], sets=(1, 2), status="completed", server=None)
    assert ex.format_score(match) == "6-4 3-6 4-6, Carlos Alcaraz won"


def test_no_server_known():
    match = make_match([[1], [0]], points=("15", "0"), server=None)
    assert ex.format_score(match) == "1-0, 15-0"


@pytest.mark.parametrize("level", [0, 5])
def test_match_tiebreak_at_a_level_score(level):
    match = make_match([[6, 4, level], [4, 6, level]], server=1, is_tiebreak=True, sets=(1, 1))
    assert ex.is_match_tiebreak(match["score"]) is True
    assert ex.format_score(match) == f"6-4 4-6 [{level}-{level}], Jannik Sinner serving"


def test_tiebreak_in_a_full_deciding_set():
    # A third set played to 6-6 then a normal tiebreak. Three sets alone do not mean a match tiebreak.
    match = make_match([[6, 3, 6], [4, 6, 6]], points=("5", "3"), is_tiebreak=True, sets=(1, 1))
    assert ex.is_match_tiebreak(match["score"]) is False
    assert ex.format_score(match) == "6-4 3-6 6-6, tiebreak 5-3, Jannik Sinner serving"


def test_winner_comes_from_sets_not_the_last_set():
    # Player 1 won the only completed set. The last set's games favour player 2.
    match = make_match([[6, 2], [4, 5]], sets=(1, 0), status="completed", server=None)
    assert ex.format_score(match) == "6-4 2-5, Jannik Sinner won"


def test_set_scores_stop_at_the_shorter_list():
    assert ex.set_scores([[6, 3], [4]]) == ["6-4"]


@pytest.mark.parametrize("outcome", ["unresolved", "abandoned"])
def test_no_result_is_not_a_win(outcome):
    match = make_match([[6], [4]], sets=(1, 0), status="completed", server=None)
    match["outcome"], match["winner"] = outcome, None
    assert ex.format_score(match) == "6-4, no result"


def test_winner_field_beats_sets():
    # A retirement: player 1 led on sets, retired, and lost.
    match = make_match([[6, 2], [4, 3]], sets=(1, 0), status="completed", server=None)
    match["outcome"], match["winner"] = "retired", 2
    assert ex.format_score(match) == "6-4 2-3, Carlos Alcaraz won"


def test_bracket_after_pairing_unequal_lists():
    assert ex.set_scores([[6, 3], [4]], match_tiebreak=True) == ["[6-4]"]


@pytest.mark.parametrize("points", ["absent", None, [], ["15"], ["15", "30", "40"]])
def test_missing_or_malformed_points(points):
    match = make_match([[2], [2]])
    if points == "absent":
        del match["score"]["points"]
    else:
        match["score"]["points"] = points
    assert ex.format_score(match) == "2-2, Jannik Sinner serving"


def no_score(status="completed", outcome=None, winner=None):
    match = make_match(None)
    match.update(score=None, status=status, outcome=outcome, winner=winner)
    return match


def test_walkover_without_a_score_row():
    assert ex.format_score(no_score(outcome="walkover", winner=1)) == "Jannik Sinner won by walkover"


@pytest.mark.parametrize(
    "outcome, winner, expected",
    [("unresolved", None, "no result"), ("completed", 2, "Carlos Alcaraz won"), (None, None, "final")],
)
def test_completed_without_a_score_row(outcome, winner, expected):
    assert ex.format_score(no_score(outcome=outcome, winner=winner)) == expected


def test_upcoming_without_a_score_row_is_not_started():
    assert ex.format_score(no_score(status="upcoming")) == "not started"


def test_level_sets_and_no_winner_is_final():
    match = make_match([[6, 4], [4, 6]], sets=(1, 1), status="completed", server=None)
    match["winner"] = None
    assert ex.format_score(match) == "6-4 4-6, final"
