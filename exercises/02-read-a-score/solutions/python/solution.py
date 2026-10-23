"""Exercise 2 solution: read a score.

Every score array is player-major: index 0 is player 1, index 1 is player 2.
"""

from __future__ import annotations


# Outcomes where nobody was awarded the match.
NO_RESULT = ("unresolved", "abandoned")


def player_name(match: dict, number: int) -> str:
    player = (match.get("players") or {}).get(f"p{number}") or {}
    return player.get("name") or f"Player {number}"


def is_match_tiebreak(score: dict) -> bool:
    """An ordinary tiebreak only happens at 6-6. Any other tiebreak is a deciding match tiebreak."""
    games = score.get("games") or [[], []]
    if not score.get("is_tiebreak") or not games[0] or not games[1]:
        return False
    return (games[0][-1], games[1][-1]) != (6, 6)


def set_scores(games: list, match_tiebreak: bool = False) -> list[str]:
    """[[6, 3], [4, 4]] -> ["6-4", "3-4"]. With match_tiebreak the last set reads [10-5]."""
    first, second = games
    parts = [f"{a}-{b}" for a, b in zip(first, second)]
    if match_tiebreak and parts:
        parts[-1] = f"[{parts[-1]}]"  # pair first, then bracket
    return parts


def point_score(score: dict, match: dict) -> str | None:
    """Describe the game in progress, or None when there is nothing to say."""
    points = score.get("points")
    if not points or len(points) != 2:
        return None
    a, b = points
    if score.get("is_tiebreak"):
        if is_match_tiebreak(score):
            return None
        return f"tiebreak {a}-{b}"
    if a == "40" and b == "40":
        return "deuce"
    if a == "AD":
        return f"advantage {player_name(match, 1)}"
    if b == "AD":
        return f"advantage {player_name(match, 2)}"
    return f"{a}-{b}"


def format_score(match: dict) -> str:
    score = match.get("score")
    if score is None:
        if match.get("status") != "completed":
            return "not started"
        # A completed match with no score row, such as a walkover.
        if match.get("outcome") in NO_RESULT:
            return "no result"
        if match.get("winner") in (1, 2):
            how = " by walkover" if match.get("outcome") == "walkover" else ""
            return f"{player_name(match, match['winner'])} won{how}"
        return "final"
    games = score.get("games")
    if games is None:
        return "score unavailable"
    sets_text = " ".join(set_scores(games, is_match_tiebreak(score))) or "0-0"
    if match.get("status") == "completed":
        if match.get("outcome") in NO_RESULT:
            return f"{sets_text}, no result"
        winner = match.get("winner")
        if winner not in (1, 2):
            sets = score.get("sets") or [0, 0]
            if sets[0] == sets[1]:
                return f"{sets_text}, final"
            winner = 1 if sets[0] > sets[1] else 2
        return f"{sets_text}, {player_name(match, winner)} won"
    parts = [sets_text]
    points_text = point_score(score, match)
    if points_text:
        parts.append(points_text)
    server = score.get("server")
    if server in (1, 2):
        parts.append(f"{player_name(match, server)} serving")
    return ", ".join(parts)


if __name__ == "__main__":
    example = {
        "status": "live",
        "players": {"p1": {"name": "Jannik Sinner"}, "p2": {"name": "Carlos Alcaraz"}},
        "score": {"sets": [1, 0], "games": [[6, 3], [4, 4]], "points": ["30", "15"], "server": 1, "is_tiebreak": False},
    }
    print(format_score(example))
