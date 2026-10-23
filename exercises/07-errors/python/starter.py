"""Exercise 7: turn API errors into clear messages.

Every error body is JSON with a stable `error` code, sometimes with a
`detail` sentence and an `allowed` list:
    401 {"error": "unauthorized"}          the key is missing, wrong or disabled
    403 {"error": "upgrade_required"}      the endpoint is above your plan
    404 {"error": "not_found"}             no such id
    429 {"error": "rate_limited", ...}     too many requests (exercise 6)

Run the tests with:
    python3 -m pytest exercises/07-errors/python
See the real errors (three requests; refused calls do not use up your daily allowance):
    python3 exercises/07-errors/python/starter.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

BASE_URL = "https://api.livetennisapi.com/api/public/v1"
PRICING_URL = "https://livetennisapi.com/pricing"
FREE_PLAN = "live and upcoming matches, current scores, players, fixtures, tournaments and usage stats"


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


class ApiError(Exception):
    def __init__(self, status: int, code, message: str):
        super().__init__(message)
        self.status = status
        self.code = code


# ---------------------------------------------------------------------------
# Your code
# ---------------------------------------------------------------------------


def explain_error(status: int, body: dict, path: str) -> str:
    """Return one clear message for a failed request. Start it with "HTTP <status>".

    - 401: say the key was not accepted and name LIVETENNISAPI_KEY.
    - 403 upgrade_required: say `path` is not on the plan, include the code
      "upgrade_required", list what FREE covers (FREE_PLAN) and give PRICING_URL.
      If body["free_history_taste"] == "used", add that the free history calls
      for this month are used up.
    - 404: include `path` and suggest checking the id. If the body has a
      `see` link, mention it.
    - 429: say to wait for Retry-After. If body["scope"] == "day", say the
      daily quota is used up and when it resets (body["resets_at"]). If the
      code is "abuse_throttled", say the key is blocked for 24 hours.
    - Never put the key in a message.
    - anything else: "HTTP <status> <code>: <detail>", plus the allowed
      values when the body lists them.
    `body` may be an empty dict when the response was not JSON.
    """
    # TODO
    raise NotImplementedError


def request_json(path: str, key: str, get=http_get):
    """GET BASE_URL + path with the key. Return the parsed body on 200.

    Otherwise raise ApiError(status, code, explain_error(...)). The code is
    body["error"], or None when the body is not JSON.
    """
    # TODO
    raise NotImplementedError


DEMO_CALLS = [
    ("a bad key", "/matches?status=live&limit=1", "not-a-real-key"),
    ("a paid endpoint", "/rankings?system=atp", None),
    ("an unknown id", "/players/999999999", None),
]


def demo(key: str, get=http_get) -> list[str]:
    """Given: make each call in DEMO_CALLS on purpose and collect the messages."""
    messages = []
    for label, path, override in DEMO_CALLS:
        try:
            request_json(path, override or key, get)
            messages.append(f"{label}: no error (your plan may include this endpoint)")
        except ApiError as error:
            messages.append(f"{label}: {error}")
    return messages


def main() -> int:
    key = os.environ.get("LIVETENNISAPI_KEY", "").strip()
    if not key:
        print("Set LIVETENNISAPI_KEY first.", file=sys.stderr)
        return 1
    for line in demo(key):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
