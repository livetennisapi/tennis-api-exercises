"""Exercise 8: a terminal scoreboard that stays inside the FREE quota.

The FREE plan allows 100 requests a day and 30 a minute. One poll of
GET /matches?status=live&limit=200 is one request and returns every live
match, so the whole board costs one request per refresh.

Run the tests with:
    python3 -m pytest exercises/08-terminal-scoreboard/python
Run it for real (a 3-hour session):
    python3 exercises/08-terminal-scoreboard/python/starter.py 180
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

BASE_URL = "https://api.livetennisapi.com/api/public/v1"
LIVE_URL = f"{BASE_URL}/matches?status=live&limit=200"
TOUR_ORDER = ["atp", "wta", "challenger", "itf", "juniors"]


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


# ---------------------------------------------------------------------------
# Part 1: the arithmetic
# ---------------------------------------------------------------------------


def poll_interval_seconds(session_minutes: float, daily_budget: int = 100, reserve: int = 10,
                          requests_per_poll: int = 1, per_minute: int = 30) -> int:
    """Whole seconds to wait between polls so the session fits the budget.

    usable   = daily_budget - reserve          (keep a reserve for other calls)
    polls    = usable // requests_per_poll
    interval = ceil(session_minutes * 60 / polls)
    Stay under the minute limit with a second to spare:
    at least ceil(60 * requests_per_poll / per_minute) + 1.
    Raise ValueError when session_minutes <= 0 or usable < requests_per_poll.
    """
    # TODO
    raise NotImplementedError


def requests_needed(session_minutes: float, interval: int, requests_per_poll: int = 1) -> int:
    """Requests a session uses: ceil(session seconds / interval) * requests_per_poll."""
    # TODO
    raise NotImplementedError


def explain_interval(session_minutes: float, daily_budget: int = 100, reserve: int = 10) -> str:
    """Show your working as one paragraph. It must contain these numbers:

    the budget, the reserve, the usable requests, the session in seconds,
    the interval, and the requests the session will use.
    For 180 minutes: 100 - 10 = 90 requests; 180 x 60 = 10800 s;
    10800 / 90 = 120 s; check 10800 / 120 = 90 requests.
    """
    # TODO
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Part 2: the board
# ---------------------------------------------------------------------------


def format_score(match: dict) -> str:
    """Copy your format_score from exercise 2 (and its helpers)."""
    # TODO
    raise NotImplementedError


def render_board(matches: list[dict]) -> str:
    """Build the text for one refresh.

    - Only status "live" counts. None live: "No live matches right now."
    - First line: "Live tennis: <n> matches" ("1 match" for one).
    - Then each tour in TOUR_ORDER, then "other" (null or unknown tour):
      a line with the tour in capitals, e.g. "ATP", then one line per match,
      sorted by tournament (ignoring case) then id:
      "  <tournament> | <p1 name> v <p2 name> | <format_score(match)>"
    - Leave out tours with no matches. A null tournament prints as
      "Unknown tournament".
    """
    # TODO
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Part 3: the loop
# ---------------------------------------------------------------------------


def run_scoreboard(key: str, session_minutes: float, get=http_get, sleep=time.sleep, clock=time.monotonic,
                   out=print, daily_budget: int = 100, reserve: int = 10) -> int:
    """Poll LIVE_URL until the session ends. Return the number of requests made.

    - interval = poll_interval_seconds(...). Never make more than
      daily_budget - reserve requests.
    - 200: out(render_board(data)).
    - 429 with "scope": "day" or error "abuse_throttled" in the body: out a
      message and stop.
    - other 429: wait the larger of interval and the Retry-After header.
    - 401 or 403: out a message and stop.
    - anything else: out a message and carry on at the next poll.
    - Before sleeping, stop if (clock() - start) + wait >= session seconds.
    - Before every request after the first, stop if the session is over. A
      sleep can wake late, and a late poll would spend a request you planned
      to keep.
    Use the clock, sleep and out you are given; the tests replace them.
    """
    # TODO
    raise NotImplementedError


def main(argv: list[str]) -> int:
    key = os.environ.get("LIVETENNISAPI_KEY", "").strip()
    if not key:
        print("Set LIVETENNISAPI_KEY first.", file=sys.stderr)
        return 1
    minutes = float(argv[0]) if argv else 180.0
    print(explain_interval(minutes))
    calls = run_scoreboard(key, minutes, out=lambda text: print("\n" + text))
    print(f"Done after {calls} requests.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
