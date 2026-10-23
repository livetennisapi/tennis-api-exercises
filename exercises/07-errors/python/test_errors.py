"""Offline tests for exercise 7. They replay recorded and constructed errors from fixtures/."""

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
    spec = importlib.util.spec_from_file_location("ex07_errors", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ex = load_exercise()


def fixture(name):
    return json.loads((ROOT / "fixtures" / f"{name}.json").read_text(encoding="utf-8"))["response"]


class FakeGet:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, headers):
        self.calls.append((url, {name.lower(): value for name, value in headers.items()}))
        reply = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        text = reply["body"] if isinstance(reply["body"], str) else json.dumps(reply["body"])
        return ex.Response(reply["status"], dict(reply["headers"]), text)


def test_401_message():
    reply = fixture("error_401_bad_key")
    message = ex.explain_error(401, reply["body"], "/matches?status=live")
    assert message.startswith("HTTP 401")
    assert "LIVETENNISAPI_KEY" in message


def test_403_message_explains_plan_gating():
    reply = fixture("error_403_upgrade_required")
    message = ex.explain_error(403, reply["body"], "/rankings?system=atp")
    assert message.startswith("HTTP 403")
    assert "upgrade_required" in message
    assert "/rankings?system=atp" in message
    assert "FREE" in message
    assert ex.PRICING_URL in message


def test_403_history_taste_used():
    body = {"error": "upgrade_required", "free_history_taste": "used"}
    message = ex.explain_error(403, body, "/history/matches")
    assert "history" in message.lower()
    assert message != ex.explain_error(403, {"error": "upgrade_required"}, "/history/matches")


def test_404_message():
    reply = fixture("error_404_player")
    message = ex.explain_error(404, reply["body"], "/players/999999999")
    assert message.startswith("HTTP 404")
    assert "/players/999999999" in message


def test_404_with_archive_pointer():
    body = {"error": "not_found", "detail": "corpus id", "see": "/api/public/v1/history/archive/players?id=104925"}
    message = ex.explain_error(404, body, "/players/104925")
    assert body["see"] in message


def test_429_messages():
    minute = ex.explain_error(429, fixture("error_429_minute")["body"], "/matches")
    day = ex.explain_error(429, fixture("error_429_day")["body"], "/matches")
    assert minute.startswith("HTTP 429") and "Retry-After" in minute
    assert day.startswith("HTTP 429") and "2026-10-24T00:00:00Z" in day


def test_other_errors_use_detail_and_allowed():
    body = {"error": "bad_status", "detail": "status must be one of the allowed values", "allowed": ["live", "upcoming"]}
    message = ex.explain_error(400, body, "/matches?status=finished")
    assert message.startswith("HTTP 400 bad_status")
    assert body["detail"] in message
    assert "live" in message and "upcoming" in message


def test_explain_error_with_empty_body():
    assert ex.explain_error(500, {}, "/matches").startswith("HTTP 500")


def test_request_json_success():
    get = FakeGet(fixture("player_34"))
    body = ex.request_json("/players/34", "abc123", get)
    assert body["id"] == 34
    assert get.calls[0][0] == ex.BASE_URL + "/players/34"
    assert get.calls[0][1]["authorization"] == "Bearer abc123"


@pytest.mark.parametrize(
    "name, status, code",
    [
        ("error_401_bad_key", 401, "unauthorized"),
        ("error_403_upgrade_required", 403, "upgrade_required"),
        ("error_404_player", 404, "not_found"),
    ],
)
def test_request_json_raises_api_error(name, status, code):
    get = FakeGet(fixture(name))
    with pytest.raises(ex.ApiError) as error:
        ex.request_json("/somewhere", "abc123", get)
    assert error.value.status == status
    assert error.value.code == code
    assert str(error.value).startswith(f"HTTP {status}")


def test_request_json_non_json_body():
    get = FakeGet({"status": 502, "headers": {}, "body": "<html>Bad gateway</html>"})
    with pytest.raises(ex.ApiError) as error:
        ex.request_json("/matches", "abc123", get)
    assert error.value.status == 502
    assert error.value.code is None


def test_demo_runs_all_three_errors():
    get = FakeGet(fixture("error_401_bad_key"), fixture("error_403_upgrade_required"), fixture("error_404_player"))
    messages = ex.demo("abc123", get)
    assert [m.split(": ", 1)[0] for m in messages] == ["a bad key", "a paid endpoint", "an unknown id"]
    assert "HTTP 401" in messages[0] and "HTTP 403" in messages[1] and "HTTP 404" in messages[2]
    assert get.calls[0][1]["authorization"] == "Bearer not-a-real-key"


SECRET = "sk-test-DO-NOT-LEAK-1234"


@pytest.mark.parametrize("name", ["error_401_bad_key", "error_403_upgrade_required", "error_404_player", "error_429_minute"])
def test_the_key_never_appears_in_a_message(name):
    get = FakeGet(fixture(name))
    with pytest.raises(ex.ApiError) as error:
        ex.request_json("/players/34", SECRET, get)
    assert SECRET not in str(error.value)
    assert SECRET not in repr(error.value.args)


def test_demo_output_has_no_key():
    get = FakeGet(fixture("error_401_bad_key"), fixture("error_403_upgrade_required"), fixture("error_404_player"))
    messages = ex.demo(SECRET, get)
    assert not any(SECRET in m or "not-a-real-key" in m for m in messages)


def test_abuse_block_message():
    message = ex.explain_error(429, fixture("error_429_abuse")["body"], "/matches")
    assert message.startswith("HTTP 429") and "24 hours" in message


def test_allowed_values_that_are_not_strings():
    message = ex.explain_error(400, {"error": "bad_limit", "allowed": [1, 200]}, "/matches?limit=0")
    assert "1" in message and "200" in message
