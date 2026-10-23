"""Exercise 4: filter and group the live slate.

Work on the `data` list from GET /matches?status=live. Each match has a
`tour` field ("atp", "wta", "challenger", "itf", "juniors" or null), a
`tournament` name and a three-valued `draw` ("singles", "doubles" or null).

Run the tests with:
    python3 -m pytest exercises/04-filter-and-group/python
"""

from __future__ import annotations

TOUR_ORDER = ["atp", "wta", "challenger", "itf", "juniors"]
OTHER = "other"


def filter_draw(matches: list[dict], draw: str) -> list[dict]:
    """Keep matches whose draw equals `draw` exactly.

    A null draw means "unknown". It matches neither "singles" nor "doubles".
    """
    # TODO
    raise NotImplementedError


def group_by_tour(matches: list[dict]) -> dict[str, list[dict]]:
    """Group LIVE matches by tour.

    - Skip any match whose status is not "live".
    - A null or unrecognised tour goes in the "other" group.
    - The dict's keys follow TOUR_ORDER, then "other". Leave out empty groups.
    - Inside a group, sort by tournament name (ignoring case), then by id.
    """
    # TODO
    raise NotImplementedError


def count_by_tournament(matches: list[dict]) -> list[tuple[str, int]]:
    """Return (tournament name, number of matches) pairs.

    Most matches first. Break ties by name, ignoring case.
    """
    # TODO
    raise NotImplementedError


def summary(matches: list[dict]) -> str:
    """Given: print-friendly text built from group_by_tour."""
    lines = []
    for tour, group in group_by_tour(matches).items():
        lines.append(f"{tour.upper()} ({len(group)})")
        for match in group:
            p1 = match["players"]["p1"]["name"]
            p2 = match["players"]["p2"]["name"]
            lines.append(f"  {match['tournament']}: {p1} v {p2}")
    return "\n".join(lines)


if __name__ == "__main__":
    import json
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[3]
    data = json.loads((root / "fixtures" / "matches_live.json").read_text())["response"]["body"]["data"]
    print(summary(data))
    for name, count in count_by_tournament(data)[:5]:
        print(f"{count:3d}  {name}")
