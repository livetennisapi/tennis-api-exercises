"""Exercise 1 solution: your first request."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
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
    """GET a URL with the standard library. Header names come back lower-case."""
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as reply:
            raw_headers, body, status = reply.headers, reply.read(), reply.status
    except urllib.error.HTTPError as error:
        raw_headers, body, status = error.headers, error.read(), error.code
    lowered = {name.lower(): value for name, value in raw_headers.items()}
    return Response(status, lowered, body.decode("utf-8", "replace"))


class MissingKeyError(RuntimeError):
    pass


def read_api_key(env=None) -> str:
    env = os.environ if env is None else env
    key = (env.get("LIVETENNISAPI_KEY") or "").strip()
    if not key:
        raise MissingKeyError(
            "LIVETENNISAPI_KEY is not set. Get a free key at "
            "https://livetennisapi.com/subscribe/free and export it in your shell."
        )
    return key


def auth_headers(key: str) -> dict:
    return {"Authorization": f"Bearer {key}", "Accept": "application/json"}


def check_health(get=http_get) -> bool:
    response = get(f"{BASE_URL}/health", {"Accept": "application/json"})
    if response.status != 200:
        return False
    return response.json().get("status") == "ok"


def count_live_matches(key: str, get=http_get) -> int:
    response = get(f"{BASE_URL}/matches?status=live&limit=200", auth_headers(key))
    if response.status != 200:
        raise RuntimeError(f"GET /matches answered HTTP {response.status}")
    payload = response.json()
    total = payload.get("meta", {}).get("total")
    if isinstance(total, int):
        return total
    return len(payload.get("data", []))


def main() -> int:
    print("API is up." if check_health() else "API health check failed.")
    try:
        key = read_api_key()
    except MissingKeyError as error:
        print(error, file=sys.stderr)
        return 1
    count = count_live_matches(key)
    print(f"{count} matches are live right now.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
