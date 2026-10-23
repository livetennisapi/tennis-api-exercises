"""Offline tests for exercise 6. Time is faked, so nothing really sleeps."""

import copy
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
    spec = importlib.util.spec_from_file_location("ex06_rate_limits", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ex = load_exercise()


def fixture(name):
    return json.loads((ROOT / "fixtures" / f"{name}.json").read_text(encoding="utf-8"))["response"]


class FakeTime:
    def __init__(self):
        self.now = 0.0
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


def test_limiter_allows_thirty_then_waits():
    fake = FakeTime()
    limiter = ex.SlidingWindowLimiter(30, 60, clock=fake.clock, sleep=fake.sleep)
    for _ in range(30):
        assert limiter.acquire() == 0
    assert limiter.acquire() == pytest.approx(60)
    assert fake.slept == [pytest.approx(60)]


def test_limiter_with_spread_out_calls():
    fake = FakeTime()
    limiter = ex.SlidingWindowLimiter(30, 60, clock=fake.clock, sleep=fake.sleep)
    for second in range(30):
        fake.now = float(second)
        limiter.acquire()
    fake.now = 30.0
    # The oldest call was at t=0, so the 31st call may go at t=60.
    assert limiter.acquire() == pytest.approx(30)
    assert fake.now == pytest.approx(60)


def test_limiter_never_exceeds_the_window():
    fake = FakeTime()
    limiter = ex.SlidingWindowLimiter(30, 60, clock=fake.clock, sleep=fake.sleep)
    times = []
    for _ in range(100):
        limiter.acquire()
        times.append(fake.now)
    for i, start in enumerate(times):
        in_window = [t for t in times[i:] if t < start + 60]
        assert len(in_window) <= 30


@pytest.mark.parametrize(
    "attempt, header, expected",
    [
        (0, "12", 12),
        (3, "12", 12),
        (0, "120", 60),       # capped
        (0, "0", 0),
        (0, None, 1),
        (1, None, 2),
        (2, None, 4),
        (3, None, 8),
        (10, None, 60),       # capped
        (2, "soon", 4),       # not a number: back off
        (2, "-5", 4),         # negative: back off
    ],
)
def test_retry_delay(attempt, header, expected):
    assert ex.retry_delay(attempt, header) == pytest.approx(expected)


def test_retry_then_success():
    fake = FakeTime()
    get = FakeGet(fixture("error_429_minute"), fixture("health"))
    url = "https://example.test/matches?status=live"
    response = ex.get_with_retry(url, {"Authorization": "Bearer abc123"}, get=get, sleep=fake.sleep)
    assert response.status == 200
    assert fake.slept == [12]
    assert len(get.calls) == 2
    for called_url, headers in get.calls:  # the retry sends the same request again
        assert called_url == url
        assert headers.get("authorization") == "Bearer abc123"


def test_gives_up_after_max_attempts():
    fake = FakeTime()
    get = FakeGet(fixture("error_429_minute"))
    with pytest.raises(ex.RateLimited):
        ex.get_with_retry("https://example.test/x", {}, get=get, sleep=fake.sleep, max_attempts=4)
    assert len(get.calls) == 4
    assert fake.slept == [12, 12, 12]


def test_backs_off_without_retry_after():
    fake = FakeTime()
    reply = copy.deepcopy(fixture("error_429_minute"))
    del reply["headers"]["retry-after"]
    get = FakeGet(reply)
    with pytest.raises(ex.RateLimited):
        ex.get_with_retry("https://example.test/x", {}, get=get, sleep=fake.sleep, max_attempts=4)
    assert fake.slept == [1, 2, 4]


def test_daily_quota_is_not_retried():
    fake = FakeTime()
    get = FakeGet(fixture("error_429_day"))
    with pytest.raises(ex.QuotaExhausted) as error:
        ex.get_with_retry("https://example.test/x", {}, get=get, sleep=fake.sleep)
    assert error.value.resets_at == "2026-10-24T00:00:00Z"
    assert fake.slept == []
    assert len(get.calls) == 1


def test_other_errors_are_returned_not_retried():
    get = FakeGet(fixture("error_404_player"))
    response = ex.get_with_retry("https://example.test/x", {}, get=get, sleep=FakeTime().sleep)
    assert response.status == 404


def test_fetch_usage():
    get = FakeGet(fixture("usage_free"))
    usage = ex.fetch_usage("abc123", get)
    assert usage["tier"] == "free"
    assert get.calls[0][0] == ex.BASE_URL + "/usage"
    assert get.calls[0][1]["authorization"] == "Bearer abc123"


def test_requests_left_from_remaining_day():
    assert ex.requests_left_today(fixture("usage_free")["body"]) == 68


def test_requests_left_worked_out():
    usage = copy.deepcopy(fixture("usage_free")["body"])
    del usage["today"]["remaining_day"]
    assert ex.requests_left_today(usage) == 100 - (37 - 5)


def test_requests_left_never_negative():
    usage = {"limits": {"per_day": 100}, "today": {"calls": 140, "errors": 10}}
    assert ex.requests_left_today(usage) == 0


def test_no_daily_cap():
    usage = {"limits": {"per_day": None}, "today": {"calls": 5, "errors": 0}}
    assert ex.requests_left_today(usage) is None
    usage = {"limits": {"per_day": None}, "today": {"calls": 5, "errors": 0, "remaining_day": None}}
    assert ex.requests_left_today(usage) is None


def test_minute_headroom():
    assert ex.minute_headroom(fixture("usage_free")["headers"]) == 29
    assert ex.minute_headroom({}) is None


def window_ok(times, limit=30, period=60):
    times = sorted(times)
    return all(len([t for t in times[i:] if t < start + period]) <= limit for i, start in enumerate(times))


def test_limiter_is_a_sliding_window_not_a_fixed_one():
    # One call at t=0, 29 at t=59, then 30 more as fast as allowed.
    # A fixed window that resets at t=60 would let 59 calls through in about a second.
    fake = FakeTime()
    limiter = ex.SlidingWindowLimiter(30, 60, clock=fake.clock, sleep=fake.sleep)
    times = []
    limiter.acquire()
    times.append(fake.now)
    fake.now = 59.0
    for _ in range(29):
        limiter.acquire()
        times.append(fake.now)
    for _ in range(30):
        limiter.acquire()
        times.append(fake.now)
    assert window_ok(times)


def test_limiter_checks_again_after_an_early_wake_up():
    fake = FakeTime()

    def early_sleep(seconds):
        # The first timer fires a millisecond early. Later ones are on time.
        fake.now += seconds - 0.001 if not fake.slept else seconds
        fake.slept.append(seconds)

    limiter = ex.SlidingWindowLimiter(30, 60, clock=fake.clock, sleep=early_sleep)
    times = []
    for _ in range(31):
        limiter.acquire()
        times.append(fake.now)
    assert window_ok(times)


@pytest.mark.parametrize("header", ["0x1A", "inf", "nan", "1e3", ""])
def test_retry_delay_only_trusts_plain_seconds(header):
    assert ex.retry_delay(2, header) == pytest.approx(4)


def test_retry_delay_accepts_decimals():
    assert ex.retry_delay(0, "1.5") == pytest.approx(1.5)


def test_get_with_retry_respects_its_cap():
    fake = FakeTime()
    get = FakeGet(fixture("error_429_minute"), fixture("health"))
    ex.get_with_retry("https://example.test/x", {}, get=get, sleep=fake.sleep, cap=5)
    assert fake.slept == [5]


def test_daily_quota_is_not_retried_even_with_a_short_retry_after():
    reply = copy.deepcopy(fixture("error_429_day"))
    reply["headers"]["retry-after"] = "5"
    fake = FakeTime()
    get = FakeGet(reply)
    with pytest.raises(ex.QuotaExhausted):
        ex.get_with_retry("https://example.test/x", {}, get=get, sleep=fake.sleep)
    assert fake.slept == []


def test_abuse_block_stops_at_once():
    fake = FakeTime()
    get = FakeGet(fixture("error_429_abuse"))
    with pytest.raises(ex.ClientBlocked) as error:
        ex.get_with_retry("https://example.test/x", {}, get=get, sleep=fake.sleep)
    assert error.value.retry_at_epoch == 1792851360
    assert "24 hours" in str(error.value)
    assert fake.slept == [] and len(get.calls) == 1


def test_fetch_usage_rejects_a_bad_status():
    get = FakeGet(fixture("error_401_bad_key"))
    with pytest.raises(RuntimeError) as error:
        ex.fetch_usage("bad", get)
    assert not isinstance(error.value, NotImplementedError)


def test_requests_left_with_a_null_count():
    assert ex.requests_left_today({"limits": {"per_day": 100}, "today": {"calls": None, "errors": None}}) == 100


@pytest.mark.parametrize("value", ["29abc", "", " ", "-1", "2.5"])
def test_minute_headroom_needs_a_whole_number(value):
    assert ex.minute_headroom({"x-ratelimit-remaining": value}) is None


@pytest.mark.parametrize("attempts", [1, 2, 5])
def test_max_attempts_is_respected(attempts):
    fake = FakeTime()
    get = FakeGet(fixture("error_429_minute"))
    with pytest.raises(ex.RateLimited):
        ex.get_with_retry("https://example.test/x", {}, get=get, sleep=fake.sleep, max_attempts=attempts)
    assert len(get.calls) == attempts
    assert len(fake.slept) == attempts - 1
