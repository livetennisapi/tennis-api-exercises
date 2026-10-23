"""Exercise 7 solution: turn API errors into clear messages."""

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


def explain_error(status: int, body: dict, path: str) -> str:
    body = body if isinstance(body, dict) else {}
    code = body.get("error")
    detail = body.get("detail")
    if status == 401:
        return (
            "HTTP 401 unauthorized: the API did not accept your key. "
            "Check that LIVETENNISAPI_KEY holds the whole key with no extra spaces."
        )
    if status == 403 and code == "upgrade_required":
        message = (
            f"HTTP 403 upgrade_required: {path} is not part of your plan. "
            f"The FREE plan covers {FREE_PLAN}. Plans are listed at {PRICING_URL}."
        )
        if body.get("free_history_taste") == "used":
            message += " Your free history calls for this month are used up."
        return message
    if status == 404:
        message = f"HTTP 404 not_found: nothing exists at {path}. Check the id."
        if body.get("see"):
            message += f" That id belongs to the results archive: {body['see']}."
        return message
    if status == 429:
        if code == "abuse_throttled":
            return (
                "HTTP 429 abuse_throttled: this key is blocked for 24 hours for calling far past its limits. "
                "Fix the loop before you try again."
            )
        if body.get("scope") == "day":
            return f"HTTP 429 rate_limited: the daily quota is used up. It resets at {body.get('resets_at')}."
        return "HTTP 429 rate_limited: too many requests this minute. Wait for the Retry-After seconds, then slow down."
    message = f"HTTP {status} {code or 'error'}: {detail or 'the API did not say why'}"
    if body.get("allowed"):
        message += f" Allowed values: {', '.join(str(value) for value in body['allowed'])}."
    return message


def request_json(path: str, key: str, get=http_get):
    response = get(BASE_URL + path, auth_headers(key))
    try:
        body = response.json()
    except ValueError:
        body = {}
    if response.status == 200:
        return body
    raise ApiError(response.status, body.get("error") if isinstance(body, dict) else None,
                   explain_error(response.status, body, path))


DEMO_CALLS = [
    ("a bad key", "/matches?status=live&limit=1", "not-a-real-key"),
    ("a paid endpoint", "/rankings?system=atp", None),
    ("an unknown id", "/players/999999999", None),
]


def demo(key: str, get=http_get) -> list[str]:
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
