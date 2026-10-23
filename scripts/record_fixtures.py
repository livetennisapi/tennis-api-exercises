#!/usr/bin/env python3
"""Re-record the fixtures in fixtures/ from the real API.

Reads the key from the LIVETENNISAPI_KEY environment variable and never
prints it. Every recorded body, header and path is scrubbed of the key
before it is written. Only FREE-plan endpoints are called.

Fields that only paid plans fill in are set to null, which is how a FREE
key sees them. Every response is held in memory and checked (expected
status, JSON body, no trace of the key) before any file is written, so a
failed run leaves the fixtures as they were. The constructed fixtures (403, 429, free usage) are not
touched by this script.

Usage:
    LIVETENNISAPI_KEY=... python3 scripts/record_fixtures.py

This spends about ten requests of your daily quota.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://api.livetennisapi.com/api/public/v1"
ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"

# name -> (path, auth mode, expected status). auth is "header", "none" or "bad".
RECORDINGS = {
    "health": ("/health", "none", 200),
    "matches_live": ("/matches?status=live&limit=200", "header", 200),
    "players_search_none": ("/players?search=zzqxv&limit=10", "header", 200),
    "players_search_one": ("/players?search=" + urllib.parse.quote("Jannik Sinner") + "&limit=10", "header", 200),
    "players_search_sinner": ("/players?search=sinner&limit=10", "header", 200),
    "players_search_williams": ("/players?search=williams&limit=10", "header", 200),
    "player_34": ("/players/34", "header", 200),
    "error_404_player": ("/players/999999999", "header", 404),
    "error_401_bad_key": ("/matches?status=live&limit=1", "bad", 401),
}

# Rate-limit header values describe the recording key's plan, not FREE, so the
# names are kept and the values blanked. A Retry-After on a 429 is kept whole.
RATE_HEADERS = ("x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset")
PAID_SCORE_FIELDS = ("win_probability_p1", "danger", "win_probability_p1_model", "win_probability_meta")
PAID_PLAYER_FIELDS = ("itf_ranking", "height_cm", "doubles_ranking")


class RecordingError(RuntimeError):
    pass


def fetch(path: str, auth: str, key: str) -> tuple[int, dict, object]:
    headers = {"Accept": "application/json", "User-Agent": "tennis-api-exercises-recorder"}
    if auth == "header":
        headers["Authorization"] = f"Bearer {key}"
    elif auth == "bad":
        headers["Authorization"] = "Bearer not-a-real-key"
    request = urllib.request.Request(BASE_URL + path, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status, raw_headers, raw = response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as error:
        status, raw_headers, raw = error.code, dict(error.headers), error.read()
    lowered = {k.lower(): v for k, v in raw_headers.items()}
    kept = {name: "" for name in RATE_HEADERS if name in lowered}
    if status == 429 and "retry-after" in lowered:
        kept["retry-after"] = lowered["retry-after"]
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as error:
        raise RecordingError(f"{path}: HTTP {status} with a body that is not JSON") from error
    return status, kept, body


def free_view_of_player(player: dict) -> None:
    for field in PAID_PLAYER_FIELDS:
        if field in player:
            player[field] = None
    player.pop("itf_id", None)  # absent below ULTRA
    meta = ((player.get("stats") or {}).get("ratings") or {}).get("meta")
    if isinstance(meta, dict) and "height_cm" in meta:
        meta["height_cm"] = None  # height is paid-only, wherever it appears


def free_view(body: object) -> object:
    """Null the fields a FREE key does not get, in place."""
    if not isinstance(body, dict):
        return body
    rows = body.get("data") if isinstance(body.get("data"), list) else [body]
    for row in rows:
        if not isinstance(row, dict):
            continue
        score = row.get("score")
        if isinstance(score, dict):
            for field in PAID_SCORE_FIELDS:
                if field in score:
                    score[field] = None
        players = row.get("players")
        if isinstance(players, dict):
            for player in players.values():
                if isinstance(player, dict):
                    free_view_of_player(player)
        if "name" in row and "is_doubles_team" in row:
            free_view_of_player(row)
    return body


def scrub(text: str, key: str) -> str:
    """Replace the key, raw or URL-encoded, then refuse if any 8-character piece survives."""
    for form in {key, urllib.parse.quote(key, safe=""), urllib.parse.quote_plus(key)}:
        text = text.replace(form, "YOUR_KEY")
    for i in range(max(len(key) - 7, 0)):
        if key[i:i + 8] in text:
            raise RecordingError("part of the key survived scrubbing; nothing was written")
    return text


def main() -> int:
    key = os.environ.get("LIVETENNISAPI_KEY", "").strip()
    if not key:
        print("Set LIVETENNISAPI_KEY first.", file=sys.stderr)
        return 2
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    pending = {}
    try:
        for name, (path, auth, expected) in RECORDINGS.items():
            status, headers, body = fetch(path, auth, key)
            if status != expected:
                raise RecordingError(f"{name}: expected HTTP {expected}, got {status}")
            fixture = {
                "source": f"recorded from the live API on {today}",
                "request": {"method": "GET", "path": path, "auth": auth},
                "response": {"status": status, "headers": headers, "body": free_view(body)},
            }
            pending[name] = scrub(json.dumps(fixture, indent=1, ensure_ascii=False) + "\n", key)
            print(f"{name}: HTTP {status}")
    except (RecordingError, OSError) as error:
        print(f"Recording failed, no fixture was changed: {error}", file=sys.stderr)
        return 1
    for name, text in pending.items():
        (FIXTURES / f"{name}.json").write_text(text, encoding="utf-8")
    print(f"Wrote {len(pending)} fixtures.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
