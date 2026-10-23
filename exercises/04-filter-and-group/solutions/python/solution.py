"""Exercise 4 solution: filter and group the live slate."""

from __future__ import annotations

TOUR_ORDER = ["atp", "wta", "challenger", "itf", "juniors"]
OTHER = "other"


def filter_draw(matches: list[dict], draw: str) -> list[dict]:
    """Keep matches whose draw equals `draw`. A null draw matches nothing."""
    return [match for match in matches if match.get("draw") == draw]


def sort_key(match: dict) -> tuple[str, int]:
    return ((match.get("tournament") or "").casefold(), match.get("id") or 0)


def group_by_tour(matches: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for match in matches:
        if match.get("status") != "live":
            continue
        tour = match.get("tour") if match.get("tour") in TOUR_ORDER else OTHER
        groups.setdefault(tour, []).append(match)
    ordered = {}
    for tour in TOUR_ORDER + [OTHER]:
        if tour in groups:
            ordered[tour] = sorted(groups[tour], key=sort_key)
    return ordered


def count_by_tournament(matches: list[dict]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for match in matches:
        name = match.get("tournament") or "Unknown tournament"
        counts[name] = counts.get(name, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold()))


def summary(matches: list[dict]) -> str:
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

    root = pathlib.Path(__file__).resolve().parents[4]
    data = json.loads((root / "fixtures" / "matches_live.json").read_text())["response"]["body"]["data"]
    print(summary(data))
    for name, count in count_by_tournament(data)[:5]:
        print(f"{count:3d}  {name}")
