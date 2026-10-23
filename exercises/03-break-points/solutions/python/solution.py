"""Exercise 3 solution: break point detector.

A break point is a point where the RECEIVER wins the game by winning it.
Tiebreaks have no break points.
"""

from __future__ import annotations

POINT_VALUES = {"0": 0, "15": 1, "30": 2, "40": 3, "AD": 4}


def point_value(text: str) -> int:
    try:
        return POINT_VALUES[text]
    except KeyError:
        raise ValueError(f"not a game score: {text!r}") from None


def break_points_held(score: dict | None) -> int:
    """How many break points the receiver holds right now (0 to 3)."""
    if not score or score.get("is_tiebreak"):
        return 0
    server = score.get("server")
    points = score.get("points")
    if server not in (1, 2) or not points or len(points) != 2:
        return 0
    server_points = point_value(points[server - 1])
    receiver_points = point_value(points[2 - server])
    if receiver_points == 4:
        return 1
    if receiver_points == 3 and server_points <= 2:
        return 3 - server_points
    return 0


def is_break_point(score: dict | None) -> bool:
    return break_points_held(score) > 0


def find_break_points(matches: list[dict]) -> list[int]:
    """Ids of live matches where the current point is a break point, in input order."""
    return [
        match["id"]
        for match in matches
        if match.get("status") == "live" and is_break_point(match.get("score"))
    ]


if __name__ == "__main__":
    print(is_break_point({"points": ["15", "40"], "server": 1, "is_tiebreak": False}))
