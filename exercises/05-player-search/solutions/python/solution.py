"""Exercise 5 solution: player search."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
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


def search_url(name: str, limit: int = 10) -> str:
    return f"{BASE_URL}/players?search={urllib.parse.quote(name)}&limit={limit}"


def search_players(name: str, key: str, get=http_get) -> dict:
    name = name.strip()
    if not name:
        raise ValueError("Type at least one letter of a player's name.")
    response = get(search_url(name), auth_headers(key))
    if response.status != 200:
        raise RuntimeError(f"GET /players answered HTTP {response.status}")
    payload = response.json()
    players = payload.get("data", [])
    total = payload.get("meta", {}).get("total")
    return {"players": players, "total": total if isinstance(total, int) else len(players)}


def pick_player(players: list[dict], total: int | None = None, singles_only: bool = True) -> dict:
    pool = [p for p in players if not p.get("is_doubles_team")] if singles_only else list(players)
    if total is not None and total > len(players):
        # Only one page came back. A better match may be on the next page, so do not decide.
        candidates = [p["name"] for p in (pool or players)[:5]]
        raise AmbiguousPlayer(
            f"{total} players match and only {len(players)} came back. Be more specific, for example: "
            f"{', '.join(candidates)}.",
            candidates,
        )
    if not pool:
        raise PlayerNotFound("No player matches that name.")
    if len(pool) == 1:
        return pool[0]
    candidates = [p["name"] for p in pool[:5]]
    count = total if total is not None else len(pool)
    raise AmbiguousPlayer(
        f"{count} players match. Be more specific, for example: {', '.join(candidates)}.",
        candidates,
    )


def get_player(player_id: int, key: str, get=http_get) -> dict:
    response = get(f"{BASE_URL}/players/{int(player_id)}", auth_headers(key))
    if response.status == 404:
        raise PlayerNotFound(f"No player has id {player_id}.")
    if response.status != 200:
        raise RuntimeError(f"GET /players/{player_id} answered HTTP {response.status}")
    return response.json()


def describe_player(player: dict) -> str:
    text = player["name"]
    if player.get("country"):
        text += f" ({player['country'].upper()})"
    ranking = player.get("ranking")
    if ranking is None or player.get("ranking_status") == "unranked":
        return f"{text}, unranked"
    tour = (player.get("tour") or "").upper()
    text += f", {tour} rank {ranking}" if tour else f", rank {ranking}"
    if player.get("ranking_points") is not None:
        text += f", {player['ranking_points']} points"
    return text


def find_player(name: str, key: str, get=http_get) -> dict:
    result = search_players(name, key, get)
    chosen = pick_player(result["players"], result["total"])
    return get_player(chosen["id"], key, get)


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
