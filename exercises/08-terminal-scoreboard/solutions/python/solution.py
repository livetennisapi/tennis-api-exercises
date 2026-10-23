"""Exercise 8 solution: a terminal scoreboard that stays inside the FREE quota.

Usage:
    LIVETENNISAPI_KEY=... python solution.py 180    # a 3-hour session
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


# --- the arithmetic --------------------------------------------------------


def poll_interval_seconds(session_minutes: float, daily_budget: int = 100, reserve: int = 10,
                          requests_per_poll: int = 1, per_minute: int = 30) -> int:
    if session_minutes <= 0:
        raise ValueError("The session must last more than 0 minutes.")
    usable = daily_budget - reserve
    if usable < requests_per_poll:
        raise ValueError("The reserve leaves no requests for polling.")
    polls = usable // requests_per_poll
    interval = math.ceil(session_minutes * 60 / polls)
    # Polling exactly at the minute limit leaves no room for anything else, so add a second.
    floor = math.ceil(60 * requests_per_poll / per_minute) + 1
    return max(interval, floor)


def requests_needed(session_minutes: float, interval: int, requests_per_poll: int = 1) -> int:
    return math.ceil(session_minutes * 60 / interval) * requests_per_poll


def explain_interval(session_minutes: float, daily_budget: int = 100, reserve: int = 10) -> str:
    usable = daily_budget - reserve
    seconds = round(session_minutes * 60)
    interval = poll_interval_seconds(session_minutes, daily_budget, reserve)
    needed = requests_needed(session_minutes, interval)
    return (
        f"Daily budget {daily_budget} - reserve {reserve} = {usable} requests for polling. "
        f"Session {session_minutes:g} min x 60 = {seconds} s. "
        f"{seconds} s / {usable} requests = {seconds / usable:.1f} s, rounded up to {interval} s. "
        f"Check: {seconds} s / {interval} s = {needed} requests, which is at most {usable}."
    )


# --- the board -------------------------------------------------------------


def _name(match: dict, number: int) -> str:
    return ((match.get("players") or {}).get(f"p{number}") or {}).get("name") or f"Player {number}"


def format_score(match: dict) -> str:
    """The same rules as exercise 2."""
    score = match.get("score")
    if score is None:
        if match.get("status") != "completed":
            return "not started"
        # A completed match with no score row, such as a walkover.
        if match.get("outcome") in ("unresolved", "abandoned"):
            return "no result"
        if match.get("winner") in (1, 2):
            how = " by walkover" if match.get("outcome") == "walkover" else ""
            return f"{_name(match, match['winner'])} won{how}"
        return "final"
    games = score.get("games")
    if games is None:
        return "score unavailable"
    match_tb = bool(score.get("is_tiebreak")) and bool(games[0]) and bool(games[1]) and (games[0][-1], games[1][-1]) != (6, 6)
    parts_sets = [f"{a}-{b}" for a, b in zip(*games)]
    if match_tb:
        parts_sets[-1] = f"[{parts_sets[-1]}]"
    sets_text = " ".join(parts_sets) or "0-0"
    if match.get("status") == "completed":
        if match.get("outcome") in ("unresolved", "abandoned"):
            return f"{sets_text}, no result"
        winner = match.get("winner")
        if winner not in (1, 2):
            sets = score.get("sets") or [0, 0]
            if sets[0] == sets[1]:
                return f"{sets_text}, final"
            winner = 1 if sets[0] > sets[1] else 2
        return f"{sets_text}, {_name(match, winner)} won"
    parts = [sets_text]
    points = score.get("points")
    if points and len(points) == 2 and not match_tb:
        a, b = points
        if score.get("is_tiebreak"):
            parts.append(f"tiebreak {a}-{b}")
        elif a == "40" and b == "40":
            parts.append("deuce")
        elif a == "AD":
            parts.append(f"advantage {_name(match, 1)}")
        elif b == "AD":
            parts.append(f"advantage {_name(match, 2)}")
        else:
            parts.append(f"{a}-{b}")
    if score.get("server") in (1, 2):
        parts.append(f"{_name(match, score['server'])} serving")
    return ", ".join(parts)


def render_board(matches: list[dict]) -> str:
    live = [m for m in matches if m.get("status") == "live"]
    if not live:
        return "No live matches right now."
    noun = "match" if len(live) == 1 else "matches"
    lines = [f"Live tennis: {len(live)} {noun}"]
    for tour in TOUR_ORDER + ["other"]:
        group = [m for m in live if (m.get("tour") if m.get("tour") in TOUR_ORDER else "other") == tour]
        if not group:
            continue
        lines.append(tour.upper())
        for match in sorted(group, key=lambda m: ((m.get("tournament") or "").casefold(), m.get("id") or 0)):
            lines.append(f"  {match.get('tournament') or 'Unknown tournament'} | {_name(match, 1)} v {_name(match, 2)} | {format_score(match)}")
    return "\n".join(lines)


# --- the loop --------------------------------------------------------------


def run_scoreboard(key: str, session_minutes: float, get=http_get, sleep=time.sleep, clock=time.monotonic,
                   out=print, daily_budget: int = 100, reserve: int = 10) -> int:
    interval = poll_interval_seconds(session_minutes, daily_budget, reserve)
    usable = daily_budget - reserve
    session_seconds = session_minutes * 60
    start = clock()
    calls = 0
    while calls < usable:
        if calls and clock() - start >= session_seconds:
            break  # a sleep can wake late, so check the clock before every request
        response = get(LIVE_URL, auth_headers(key))
        calls += 1
        wait = interval
        if response.status == 200:
            out(render_board(response.json().get("data", [])))
        elif response.status == 429:
            try:
                body = response.json()
            except ValueError:
                body = {}
            if body.get("error") == "abuse_throttled":
                out("This key is blocked for 24 hours for ignoring rate limits. Stopping.")
                break
            if body.get("scope") == "day":
                out("The daily quota is used up. Stopping.")
                break
            try:
                wait = max(interval, float(response.headers.get("retry-after", interval)))
            except ValueError:
                wait = interval
            out(f"Rate limited. Waiting {wait:g} s.")
        elif response.status in (401, 403):
            out(f"HTTP {response.status}. Check your key and plan. Stopping.")
            break
        else:
            out(f"HTTP {response.status}. Trying again at the next poll.")
        if clock() - start + wait >= session_seconds:
            break
        sleep(wait)
    return calls


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
