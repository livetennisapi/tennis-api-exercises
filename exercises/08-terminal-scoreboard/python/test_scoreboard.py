"""Offline tests for exercise 8. Time is faked, so a 10-hour session runs instantly."""

import importlib.util
import json
import math
import os
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load_exercise():
    if os.environ.get("SOLUTION") == "1":
        path = HERE.parent / "solutions" / "python" / "solution.py"
    else:
        path = HERE / "starter.py"
    spec = importlib.util.spec_from_file_location("ex08_scoreboard", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ex = load_exercise()


def fixture(name):
    return json.loads((ROOT / "fixtures" / f"{name}.json").read_text(encoding="utf-8"))["response"]


LIVE = fixture("matches_live")["body"]["data"]


class FakeTime:
    def __init__(self):
        self.now = 1000.0
        self.slept = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


class FakeGet:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, headers):
        self.calls.append((url, {name.lower(): value for name, value in headers.items()}))
        reply = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        return ex.Response(reply["status"], dict(reply["headers"]), json.dumps(reply["body"]))


# Part 1: the arithmetic

@pytest.mark.parametrize(
    "minutes, expected",
    [
        (180, 120),   # 10800 s / 90 requests
        (120, 80),    # 7200 / 90
        (10, 7),      # 600 / 90 = 6.67, rounded up
        (600, 400),   # 36000 / 90
        (1, 3),       # 60 / 90 is under a second, but 30 a minute means 2 s, plus 1 s to spare
    ],
)
def test_poll_interval(minutes, expected):
    assert ex.poll_interval_seconds(minutes) == expected


def test_poll_interval_with_two_requests_per_poll():
    # 90 usable / 2 per poll = 45 polls; 5400 s / 45 = 120 s
    assert ex.poll_interval_seconds(90, requests_per_poll=2) == 120


@pytest.mark.parametrize("minutes", [5, 10, 37, 180, 240, 1440])
def test_session_stays_inside_budget(minutes):
    interval = ex.poll_interval_seconds(minutes)
    assert ex.requests_needed(minutes, interval) <= 90


def test_requests_needed():
    assert ex.requests_needed(180, 120) == 90
    assert ex.requests_needed(10, 7) == math.ceil(600 / 7)


@pytest.mark.parametrize("args", [(0,), (-5,), (60, 10, 10)])
def test_bad_inputs(args):
    with pytest.raises(ValueError):
        ex.poll_interval_seconds(*args)


def test_explain_interval_shows_the_working():
    text = ex.explain_interval(180)
    for number in ["100", "10", "90", "10800", "120"]:
        assert re.search(rf"(?<![0-9.]){number}(?![0-9])", text), number


# Part 2: the board

def test_board_header_and_order():
    lines = ex.render_board(LIVE).splitlines()
    assert lines[0] == "Live tennis: 29 matches"
    headers = [line for line in lines if not line.startswith(" ")][1:]
    assert headers == ["ATP", "CHALLENGER", "ITF", "OTHER"]


def test_board_lines():
    board = ex.render_board(LIVE)
    assert "  Brussels | Jiri Lehecka v Tallon Griekspoor | 0-1, 30-30, Jiri Lehecka serving" in board.splitlines()
    assert "Lyon (France) | Tommy Paul v Corentin Moutet | 6-4 3-6 2-0, 0-15, Corentin Moutet serving" in board
    assert board.index("Brussels") < board.index("Lyon (France)")
    assert len([line for line in board.splitlines() if line.startswith("  ")]) == 29


def test_board_singular_and_empty():
    assert ex.render_board([]) == "No live matches right now."
    assert ex.render_board(LIVE[:1]).splitlines()[0] == "Live tennis: 1 match"


# Part 3: the loop

def test_ten_minute_session():
    fake = FakeTime()
    get = FakeGet(fixture("matches_live"))
    boards = []
    calls = ex.run_scoreboard("abc123", 10, get=get, sleep=fake.sleep, clock=fake.clock, out=boards.append)
    assert calls == math.ceil(600 / 7) == len(get.calls)
    assert set(fake.slept) == {7}
    assert all(board.startswith("Live tennis: 29 matches") for board in boards)
    assert get.calls[0][0] == ex.LIVE_URL
    assert get.calls[0][1]["authorization"] == "Bearer abc123"


def test_long_session_never_exceeds_budget():
    fake = FakeTime()
    get = FakeGet(fixture("matches_live"))
    calls = ex.run_scoreboard("abc123", 600, get=get, sleep=fake.sleep, clock=fake.clock, out=lambda _: None)
    assert calls <= 90
    assert fake.now - 1000.0 <= 600 * 60


def test_rate_limited_poll_waits_longer():
    fake = FakeTime()
    minute = fixture("error_429_minute")
    minute["headers"]["retry-after"] = "45"
    get = FakeGet(fixture("matches_live"), minute, fixture("matches_live"))
    messages = []
    ex.run_scoreboard("abc123", 3, get=get, sleep=fake.sleep, clock=fake.clock, out=messages.append)
    assert fake.slept[0] == 3
    assert fake.slept[1] == 45
    assert any("rate" in m.lower() for m in messages)


def test_daily_quota_stops_the_loop():
    fake = FakeTime()
    get = FakeGet(fixture("matches_live"), fixture("error_429_day"))
    calls = ex.run_scoreboard("abc123", 60, get=get, sleep=fake.sleep, clock=fake.clock, out=lambda _: None)
    assert calls == 2


def test_bad_key_stops_the_loop():
    fake = FakeTime()
    get = FakeGet(fixture("error_401_bad_key"))
    messages = []
    calls = ex.run_scoreboard("bad", 60, get=get, sleep=fake.sleep, clock=fake.clock, out=messages.append)
    assert calls == 1
    assert fake.slept == []
    assert "401" in messages[0]


# Rules from the rubric and the common mistakes in TEACHERS.md

def test_explain_interval_for_ten_minutes():
    text = ex.explain_interval(10)
    for number in ["100", "10", "90", "600", "7", "86"]:
        assert re.search(rf"(?<![0-9.]){number}(?![0-9])", text), number


def test_ten_minute_session_sleeps_only_between_polls():
    # 86 polls need 85 sleeps of 7 s. Sleeping once more before checking the clock overshoots.
    fake = FakeTime()
    get = FakeGet(fixture("matches_live"))
    ex.run_scoreboard("abc123", 10, get=get, sleep=fake.sleep, clock=fake.clock, out=lambda _: None)
    assert len(fake.slept) == 85
    assert sum(fake.slept) == 595


def test_three_hour_session_uses_exactly_the_budget():
    fake = FakeTime()
    get = FakeGet(fixture("matches_live"))
    calls = ex.run_scoreboard("abc123", 180, get=get, sleep=fake.sleep, clock=fake.clock, out=lambda _: None)
    assert calls == 90
    assert len(fake.slept) == 89


def test_short_retry_after_still_waits_the_interval():
    fake = FakeTime()
    minute = fixture("error_429_minute")
    minute["headers"]["retry-after"] = "1"
    get = FakeGet(fixture("matches_live"), minute, fixture("matches_live"))
    ex.run_scoreboard("abc123", 10, get=get, sleep=fake.sleep, clock=fake.clock, out=lambda _: None)
    assert fake.slept[1] == 7


def test_frozen_clock_still_stops_at_the_budget():
    calls = []

    def get(url, headers):
        calls.append(url)
        assert len(calls) <= 100, "the loop does not stop at the request budget"
        reply = fixture("matches_live")
        return ex.Response(reply["status"], {}, json.dumps(reply["body"]))

    made = ex.run_scoreboard("abc123", 180, get=get, sleep=lambda _: None, clock=lambda: 0.0, out=lambda _: None)
    assert made == len(calls) == 90


def test_a_403_stops_the_loop():
    fake = FakeTime()
    get = FakeGet(fixture("error_403_upgrade_required"))
    calls = ex.run_scoreboard("abc123", 60, get=get, sleep=fake.sleep, clock=fake.clock, out=lambda _: None)
    assert calls == 1


def test_a_server_error_does_not_stop_the_loop():
    fake = FakeTime()
    get = FakeGet({"status": 500, "headers": {}, "body": {"error": "internal"}}, fixture("matches_live"))
    messages = []
    calls = ex.run_scoreboard("abc123", 10, get=get, sleep=fake.sleep, clock=fake.clock, out=messages.append)
    assert calls > 2
    assert "500" in messages[0]
    assert messages[1].startswith("Live tennis: 29 matches")


def test_abuse_block_stops_the_loop():
    fake = FakeTime()
    abuse = fixture("error_429_abuse")
    abuse["headers"]["retry-after"] = "5"  # even a short wait must not tempt the loop to carry on
    get = FakeGet(fixture("matches_live"), abuse, fixture("matches_live"))
    messages = []
    calls = ex.run_scoreboard("abc123", 60, get=get, sleep=fake.sleep, clock=fake.clock, out=messages.append)
    assert calls == 2
    assert "blocked" in messages[-1].lower()


def test_board_ignores_matches_that_are_not_live():
    finished = dict(LIVE[0], status="completed")
    assert ex.render_board(LIVE + [finished]).splitlines()[0] == "Live tennis: 29 matches"


def test_board_with_a_null_tournament_and_a_level_match_tiebreak():
    match = {
        "id": 1, "status": "live", "tour": "atp", "tournament": None,
        "players": {"p1": {"name": "A"}, "p2": {"name": "B"}},
        "score": {"sets": [1, 1], "games": [[6, 4, 5], [4, 6, 5]], "points": ["0", "0"], "server": 1, "is_tiebreak": True},
    }
    assert "  Unknown tournament | A v B | 6-4 4-6 [5-5], A serving" in ex.render_board([match]).splitlines()


def test_no_poll_after_a_late_wake_up():
    fake = FakeTime()

    def late_sleep(seconds):
        fake.slept.append(seconds)
        fake.now += 70  # the machine slept through the rest of the session

    get = FakeGet(fixture("matches_live"))
    calls = ex.run_scoreboard("abc123", 1, get=get, sleep=late_sleep, clock=fake.clock, out=lambda _: None)
    assert calls == 1


def test_the_caller_budget_and_reserve_are_used():
    assert ex.poll_interval_seconds(60, daily_budget=13, reserve=10) == 1200
    calls = []

    def get(url, headers):
        calls.append(url)
        assert len(calls) <= 10, "the loop ignores the budget it was given"
        reply = fixture("matches_live")
        return ex.Response(reply["status"], {}, json.dumps(reply["body"]))

    made = ex.run_scoreboard("abc123", 60, get=get, sleep=lambda _: None, clock=lambda: 0.0,
                             out=lambda _: None, daily_budget=13, reserve=10)
    assert made == len(calls) == 3


def test_a_non_default_reserve_is_used():
    assert ex.poll_interval_seconds(60, daily_budget=13, reserve=12) == 3600
    calls = []

    def get(url, headers):
        calls.append(url)
        assert len(calls) <= 10, "the loop ignores the reserve it was given"
        reply = fixture("matches_live")
        return ex.Response(reply["status"], {}, json.dumps(reply["body"]))

    made = ex.run_scoreboard("abc123", 60, get=get, sleep=lambda _: None, clock=lambda: 0.0,
                             out=lambda _: None, daily_budget=13, reserve=12)
    assert made == len(calls) == 1
