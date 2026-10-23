"""Exercise 6 solution: rate limits and quota."""

from __future__ import annotations

import json
import re
import os
import sys
import time
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass

BASE_URL = "https://api.livetennisapi.com/api/public/v1"


@dataclass
class Response:
    status: int
    headers: dict
    text: str

    def json(self):
        return json.loads(self.text)


def http_get(url: str, headers: dict, timeout: float = 10.0) -> Response:
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as reply:
            raw_headers, body, status = reply.headers, reply.read(), reply.status
    except urllib.error.HTTPError as error:
        raw_headers, body, status = error.headers, error.read(), error.code
    lowered = {name.lower(): value for name, value in raw_headers.items()}
    return Response(status, lowered, body.decode("utf-8", "replace"))


def auth_headers(key: str) -> dict:
    return {"Authorization": f"Bearer {key}", "Accept": "application/json"}


class QuotaExhausted(Exception):
    def __init__(self, message: str, resets_at=None):
        super().__init__(message)
        self.resets_at = resets_at


class ClientBlocked(QuotaExhausted):
    """The 24-hour block for clients that keep calling far past their limit."""

    def __init__(self, message: str, retry_at_epoch=None):
        super().__init__(message, None)
        self.retry_at_epoch = retry_at_epoch


class RateLimited(Exception):
    pass


SECONDS = re.compile(r"\s*[0-9]+(\.[0-9]+)?\s*")  # "12" or "1.5", nothing else


class SlidingWindowLimiter:
    """Allow at most max_calls in any period of `period` seconds."""

    def __init__(self, max_calls: int = 30, period: float = 60.0, clock=time.monotonic, sleep=time.sleep):
        self.max_calls = max_calls
        self.period = period
        self.clock = clock
        self.sleep = sleep
        self.calls: deque[float] = deque()

    def _forget_old(self, now: float) -> None:
        while self.calls and self.calls[0] <= now - self.period:
            self.calls.popleft()

    def acquire(self) -> float:
        """Wait until a call is allowed, record it, and return the seconds waited."""
        now = self.clock()
        self._forget_old(now)
        waited = 0.0
        while len(self.calls) >= self.max_calls:
            pause = self.calls[0] + self.period - now
            self.sleep(pause)
            waited += pause
            now = self.clock()
            self._forget_old(now)
        self.calls.append(now)
        return waited


def retry_delay(attempt: int, retry_after=None, base: float = 1.0, cap: float = 60.0) -> float:
    """Seconds to wait before retry number `attempt` (0 for the first retry)."""
    if retry_after is not None and SECONDS.fullmatch(str(retry_after)):
        return min(float(retry_after), cap)
    return min(base * (2 ** attempt), cap)


def get_with_retry(url: str, headers: dict, get=http_get, sleep=time.sleep, max_attempts: int = 4, cap: float = 60.0) -> Response:
    for attempt in range(max_attempts):
        response = get(url, headers)
        if response.status != 429:
            return response
        try:
            body = response.json()
        except ValueError:
            body = {}
        if body.get("error") == "abuse_throttled":
            raise ClientBlocked(
                "This key is blocked for 24 hours for ignoring rate limits. Fix the loop before trying again.",
                body.get("retry_at_epoch"),
            )
        if body.get("scope") == "day":
            raise QuotaExhausted(
                "The daily quota is used up. Stop and try again after it resets.",
                body.get("resets_at"),
            )
        if attempt == max_attempts - 1:
            break
        sleep(retry_delay(attempt, response.headers.get("retry-after"), cap=cap))
    raise RateLimited(f"Still rate limited after {max_attempts} attempts.")


def fetch_usage(key: str, get=http_get) -> dict:
    response = get(f"{BASE_URL}/usage", auth_headers(key))
    if response.status != 200:
        raise RuntimeError(f"GET /usage answered HTTP {response.status}")
    return response.json()


def requests_left_today(usage: dict):
    today = usage.get("today") or {}
    if "remaining_day" in today:
        return today["remaining_day"]
    per_day = (usage.get("limits") or {}).get("per_day")
    if per_day is None:
        return None
    served = (today.get("calls") or 0) - (today.get("errors") or 0)
    return max(per_day - served, 0)


def minute_headroom(headers: dict):
    value = str(headers.get("x-ratelimit-remaining", "")).strip()
    return int(value) if re.fullmatch(r"[0-9]+", value) else None


def main() -> int:
    key = os.environ.get("LIVETENNISAPI_KEY", "").strip()
    if not key:
        print("Set LIVETENNISAPI_KEY first.", file=sys.stderr)
        return 1
    usage = fetch_usage(key)
    left = requests_left_today(usage)
    limits = usage.get("limits", {})
    print(f"Plan: {usage.get('tier')}, {limits.get('per_minute')} per minute, {limits.get('per_day')} per day.")
    print("No daily cap on this plan." if left is None else f"{left} requests left today.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
