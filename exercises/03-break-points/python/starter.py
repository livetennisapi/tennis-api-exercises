"""Exercise 3: break point detector.

A break point is a point where the RECEIVER wins the game by winning it.
The receiver is whoever is not serving: if server is 1, the receiver is 2.
Points are player-major strings: points[0] is player 1, points[1] is player 2.
The values are "0", "15", "30", "40" and "AD" (advantage).
Tiebreaks have no break points.

Run the tests with:
    python3 -m pytest exercises/03-break-points/python
"""

from __future__ import annotations

POINT_VALUES = {"0": 0, "15": 1, "30": 2, "40": 3, "AD": 4}


def point_value(text: str) -> int:
    """Turn "30" into 2 using POINT_VALUES. Raise ValueError for anything unknown,
    including a number such as 40 (the API always sends strings)."""
    # TODO
    raise NotImplementedError


def break_points_held(score: dict | None) -> int:
    """How many break points the receiver holds right now.

    0-40 -> 3, 15-40 -> 2, 30-40 -> 1, receiver on AD -> 1, anything else -> 0
    (scores written server first). Return 0 when the score is None, when
    is_tiebreak is True, when server is not 1 or 2, or when points is missing.
    """
    # TODO
    raise NotImplementedError


def is_break_point(score: dict | None) -> bool:
    """True when the receiver holds at least one break point."""
    # TODO
    raise NotImplementedError


def find_break_points(matches: list[dict]) -> list[int]:
    """Ids of matches with status "live" whose current point is a break point.

    Keep the input order.
    """
    # TODO
    raise NotImplementedError


if __name__ == "__main__":
    print(is_break_point({"points": ["15", "40"], "server": 1, "is_tiebreak": False}))
