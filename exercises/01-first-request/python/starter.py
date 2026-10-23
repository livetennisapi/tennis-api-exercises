"""Exercise 1: your first request.

Fill in every function marked TODO. Run the tests with:

    python3 -m pytest exercises/01-first-request/python

Run the program against the real API with:

    export LIVETENNISAPI_KEY=your_key_here
    python3 exercises/01-first-request/python/starter.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

BASE_URL = "https://api.livetennisapi.com/api/public/v1"


# ---------------------------------------------------------------------------
# Given code: a tiny HTTP helper. You do not need to change it.
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Your code
# ---------------------------------------------------------------------------


def read_api_key(env=None) -> str:
    """Return the key from LIVETENNISAPI_KEY, with surrounding spaces removed.

    `env` is a dict-like object; use os.environ when it is None.
    Raise MissingKeyError with a helpful message when the key is missing or blank.
    """
    # TODO
    raise NotImplementedError


def auth_headers(key: str) -> dict:
    """Return the request headers that carry the key.

    Send it as "Authorization: Bearer <key>". Also ask for JSON with Accept.
    """
    # TODO
    raise NotImplementedError


def check_health(get=http_get) -> bool:
    """Call GET /health WITHOUT a key. Return True when the body says status "ok".

    Call it as get(url, headers). Do not send Authorization or X-API-Key here.
    """
    # TODO
    raise NotImplementedError


def count_live_matches(key: str, get=http_get) -> int:
    """Call GET /matches?status=live&limit=200 with the key in a header.

    Return meta.total when it is a number, otherwise the length of data.
    Raise RuntimeError when the status is not 200.
    Never put the key in the URL.
    """
    # TODO
    raise NotImplementedError


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
