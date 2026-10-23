"""Exercise 6: rate limits and quota.

The FREE plan allows 30 requests a minute and 100 a day. Go over the
minute limit and the API answers 429 with a Retry-After header (seconds).
Go over the day limit and the 429 body says "scope": "day"; retrying then
only wastes time until the quota resets.

GET /usage reports your plan, its limits and today's calls. Calling it
does not count against the quota.

Run the tests with:
    python3 -m pytest exercises/06-rate-limits-and-quota/python
"""

from __future__ import annotations

import json
import math
import re
import os
import sys
import time
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass

BASE_URL = "https://api.livetennisapi.com/api/public/v1"


# ---------------------------------------------------------------------------
# Given code
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Your code
# ---------------------------------------------------------------------------


class SlidingWindowLimiter:
    """Allow at most max_calls in any window of `period` seconds.

    clock() returns the current time in seconds and sleep(seconds) waits.
    The tests pass in a fake clock, so never call time.time() directly.
    """

    def __init__(self, max_calls: int = 30, period: float = 60.0, clock=time.monotonic, sleep=time.sleep):
        self.max_calls = max_calls
        self.period = period
        self.clock = clock
        self.sleep = sleep
        self.calls: deque[float] = deque()  # times of recent calls, oldest first

    def acquire(self) -> float:
        """Wait until one more call is allowed, record it, return the seconds waited.

        1. Forget calls made `period` or more seconds ago.
        2. While max_calls remain, sleep until the oldest one is `period` old,
           then read the clock and forget old calls again. (A sleep can wake
           a little early, so check again instead of assuming.)
        3. Record the time of this call.
        """
        # TODO
        raise NotImplementedError


def retry_delay(attempt: int, retry_after=None, base: float = 1.0, cap: float = 60.0) -> float:
    """Seconds to wait before retry number `attempt` (0 for the first retry).

    - If retry_after (a header value such as "12" or "1.5") matches SECONDS,
      use it, but never more than `cap`. Anything else ("soon", "-5", "0x1A",
      "inf") does not count.
    - Otherwise back off exponentially: base * 2**attempt, capped at `cap`.
    """
    # TODO
    raise NotImplementedError


def get_with_retry(url: str, headers: dict, get=http_get, sleep=time.sleep, max_attempts: int = 4, cap: float = 60.0) -> Response:
    """Call get(url, headers) and retry on 429.

    - Any status other than 429: return the response at once.
    - 429 whose body has error "abuse_throttled": raise ClientBlocked with
      retry_at_epoch from the body. Do not retry.
    - 429 whose body has "scope": "day": raise QuotaExhausted with resets_at
      from the body. Do not retry, whatever Retry-After says.
    - Other 429s: sleep retry_delay(attempt, Retry-After header) and try again.
    - After max_attempts tries in total, raise RateLimited.
    Header names in Response.headers are lower-case.
    """
    # TODO
    raise NotImplementedError


def fetch_usage(key: str, get=http_get) -> dict:
    """GET /usage with the key and return the parsed body. RuntimeError on non-200."""
    # TODO
    raise NotImplementedError


def requests_left_today(usage: dict):
    """How many requests the key can still make today.

    - Use today.remaining_day when the field is present (it may be None:
      that means the plan has no daily cap).
    - Otherwise work it out: limits.per_day minus served calls, where
      served = today.calls - today.errors (a missing or null count is 0).
      Never below 0.
    - Return None when limits.per_day is None.
    """
    # TODO
    raise NotImplementedError


def minute_headroom(headers: dict):
    """Requests left in the current minute, from the x-ratelimit-remaining header.

    Return None when the header is absent, blank or not a plain whole number.
    """
    # TODO
    raise NotImplementedError


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
