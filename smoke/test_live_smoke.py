"""Optional live smoke test against the real API.

Skipped unless LIVE=1 and LIVETENNISAPI_KEY are set. It runs the reference
solutions, or the starters in a copy with the solutions removed. It spends
about three requests of your daily quota (GET /usage and refused calls are
free). Run it with:

    LIVE=1 python -m pytest smoke
"""

import importlib.util
import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = os.environ.get("LIVETENNISAPI_KEY", "").strip()

pytestmark = pytest.mark.skipif(
    os.environ.get("LIVE") != "1" or not KEY,
    reason="live smoke test: set LIVE=1 and LIVETENNISAPI_KEY to run it",
)


def solution(exercise):
    path = ROOT / "exercises" / exercise / "solutions" / "python" / "solution.py"
    if not path.exists():  # a class copy: test the student's own code
        path = ROOT / "exercises" / exercise / "python" / "starter.py"
    spec = importlib.util.spec_from_file_location(f"live_{exercise[:2]}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_health_and_live_count():
    first = solution("01-first-request")
    assert first.check_health() is True
    assert first.count_live_matches(KEY) >= 0


def test_player_search():
    search = solution("05-player-search")
    player = search.find_player("Jannik Sinner", KEY)
    assert "Sinner" in player["name"]


def test_usage_and_plan_gating():
    quota = solution("06-rate-limits-and-quota")
    errors = solution("07-errors")
    usage = quota.fetch_usage(KEY)
    left = quota.requests_left_today(usage)
    assert left is None or left >= 0
    if usage.get("tier") != "free":
        pytest.skip("this key is above FREE, so the paid endpoint will not answer 403")
    with pytest.raises(errors.ApiError) as error:
        errors.request_json("/rankings?system=atp", KEY)
    assert error.value.status == 403
    assert error.value.code == "upgrade_required"
