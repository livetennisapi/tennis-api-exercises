"""Offline tests for exercise 1. They replay recorded responses from fixtures/."""

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
    spec = importlib.util.spec_from_file_location("ex01_first_request", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ex = load_exercise()


def fixture(name):
    return json.loads((ROOT / "fixtures" / f"{name}.json").read_text(encoding="utf-8"))["response"]


class FakeGet:
    """Stands in for http_get. Records every call and replays fixture responses."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, headers):
        self.calls.append((url, {name.lower(): value for name, value in headers.items()}))
        reply = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        return ex.Response(reply["status"], dict(reply["headers"]), json.dumps(reply["body"]))


def test_read_api_key_from_env():
    assert ex.read_api_key({"LIVETENNISAPI_KEY": "  abc123  "}) == "abc123"


@pytest.mark.parametrize("env", [{}, {"LIVETENNISAPI_KEY": ""}, {"LIVETENNISAPI_KEY": "   "}])
def test_read_api_key_missing(env):
    with pytest.raises(ex.MissingKeyError) as error:
        ex.read_api_key(env)
    assert "LIVETENNISAPI_KEY" in str(error.value)


def test_auth_headers_use_bearer():
    headers = {name.lower(): value for name, value in ex.auth_headers("abc123").items()}
    assert headers["authorization"] == "Bearer abc123"
    assert "json" in headers.get("accept", "")


def test_health_needs_no_key():
    get = FakeGet(fixture("health"))
    assert ex.check_health(get) is True
    url, headers = get.calls[0]
    assert url == ex.BASE_URL + "/health"
    assert "authorization" not in headers
    assert "x-api-key" not in headers
    assert "token=" not in url


def test_health_failure_is_false():
    get = FakeGet({"status": 503, "headers": {}, "body": {"status": "down"}})
    assert ex.check_health(get) is False


def test_count_live_matches_from_fixture():
    get = FakeGet(fixture("matches_live"))
    assert ex.count_live_matches("abc123", get) == 29
    url, headers = get.calls[0]
    assert url.startswith(ex.BASE_URL + "/matches?")
    assert "status=live" in url
    assert headers["authorization"] == "Bearer abc123"


def test_key_never_in_url():
    get = FakeGet(fixture("matches_live"))
    ex.count_live_matches("abc123", get)
    url, _ = get.calls[0]
    assert "abc123" not in url
    assert "token=" not in url


def test_count_falls_back_to_data_length():
    reply = fixture("matches_live")
    reply["body"]["meta"]["total"] = None
    get = FakeGet(reply)
    assert ex.count_live_matches("abc123", get) == len(reply["body"]["data"])


def test_bad_status_raises():
    get = FakeGet(fixture("error_401_bad_key"))
    with pytest.raises(RuntimeError) as error:
        ex.count_live_matches("not-a-real-key", get)
    assert not isinstance(error.value, NotImplementedError)
    assert "401" in str(error.value)


def test_read_api_key_defaults_to_the_environment(monkeypatch):
    monkeypatch.setenv("LIVETENNISAPI_KEY", " from-env ")
    assert ex.read_api_key() == "from-env"
    monkeypatch.delenv("LIVETENNISAPI_KEY")
    with pytest.raises(ex.MissingKeyError):
        ex.read_api_key()


def test_asks_for_the_largest_page():
    get = FakeGet(fixture("matches_live"))
    ex.count_live_matches("abc123", get)
    assert "limit=200" in get.calls[0][0]


def test_count_uses_meta_total_not_the_page():
    reply = fixture("matches_live")
    reply["body"]["meta"]["total"] = 57  # more matches than fit on this page
    get = FakeGet(reply)
    assert ex.count_live_matches("abc123", get) == 57


@pytest.mark.parametrize("body", [{}, {"status": "degraded"}, {"version": "v1"}])
def test_health_reads_the_body_not_just_the_status(body):
    get = FakeGet({"status": 200, "headers": {}, "body": body})
    assert ex.check_health(get) is False
