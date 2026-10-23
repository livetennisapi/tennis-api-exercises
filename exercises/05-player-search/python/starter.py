"""Exercise 5: player search.

Search players by name with GET /players?search=..., decide what to do with
zero, one or many results, then read one player with GET /players/{id}.

Watch out: the search parameter is called `search`. When this was written
(2026-10-23) the API ignored a `name` parameter, so /players?name=sinner
quietly returned the whole roster. Always check what came back.

Run the tests with:
    python3 -m pytest exercises/05-player-search/python
Try it for real:
    python3 exercises/05-player-search/python/starter.py Jannik Sinner
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
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


class PlayerNotFound(LookupError):
    pass


class AmbiguousPlayer(LookupError):
    def __init__(self, message: str, candidates: list[str]):
        super().__init__(message)
        self.candidates = candidates


# ---------------------------------------------------------------------------
# Your code
# ---------------------------------------------------------------------------


def search_url(name: str, limit: int = 10) -> str:
    """Build BASE_URL + /players?search=<name>&limit=<limit>.

    Encode the name with urllib.parse.quote so "Jannik Sinner" becomes "Jannik%20Sinner".
    """
    # TODO
    raise NotImplementedError


def search_players(name: str, key: str, get=http_get) -> dict:
    """Search and return {"players": [...], "total": <int>}.

    - Strip the name. Raise ValueError for a blank name WITHOUT making a request.
    - Raise RuntimeError when the status is not 200.
    - total is meta.total when it is a number, otherwise len(players).
    """
    # TODO
    raise NotImplementedError


def pick_player(players: list[dict], total: int | None = None, singles_only: bool = True) -> dict:
    """Choose one player or explain why you cannot.

    - If `total` is bigger than len(players), only one page came back and a
      better match may be on the next one. Raise AmbiguousPlayer (candidates
      from the singles rows, or from all rows if there are none). Never pick
      a player, and never say "not found", from an incomplete page.
    - With singles_only, drop rows where is_doubles_team is True.
    - Nothing left: raise PlayerNotFound.
    - Exactly one left: return it.
    - More than one: raise AmbiguousPlayer. Put the first five names in
      `candidates` (keep the API's order: ranked players come first) and say
      how many matched in the message (use `total` when it is given).
    """
    # TODO
    raise NotImplementedError


def get_player(player_id: int, key: str, get=http_get) -> dict:
    """GET /players/{player_id}. Raise PlayerNotFound on 404, RuntimeError on other errors."""
    # TODO
    raise NotImplementedError


def describe_player(player: dict) -> str:
    """One line about a player.

    "Jannik Sinner (ITA), ATP rank 1, 10950 points"
    - country is upper-cased; leave the brackets out when it is null
    - ranking null, or ranking_status "unranked": "<name> (<COUNTRY>), unranked".
      An unranked player may still carry the last rank they held. It is not
      their current rank, so do not show it.
    - tour null: "rank 1" instead of "ATP rank 1"
    - ranking_points null: leave the points part out
    """
    # TODO
    raise NotImplementedError


def find_player(name: str, key: str, get=http_get) -> dict:
    """Search, pick one player, then return the full record from get_player."""
    # TODO
    raise NotImplementedError


def main(argv: list[str]) -> int:
    key = os.environ.get("LIVETENNISAPI_KEY", "").strip()
    if not key:
        print("Set LIVETENNISAPI_KEY first.", file=sys.stderr)
        return 1
    name = " ".join(argv) or "Jannik Sinner"
    try:
        print(describe_player(find_player(name, key)))
    except LookupError as error:
        print(error)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
