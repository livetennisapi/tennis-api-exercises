"""Exercise 2: read a score.

Turn one match object from GET /matches into a line a person can read, for
example "6-4 3-4, 30-15, Jannik Sinner serving".

Every score array is player-major: index 0 is player 1, index 1 is player 2.
    sets   [1, 0]            player 1 leads one set to nil
    games  [[6, 3], [4, 4]]  6-4 in the first set, 3-4 in the second
    points ["30", "15"]      the game in progress
    server 1                 player 1 is serving

Run the tests with:
    python3 -m pytest exercises/02-read-a-score/python
"""

from __future__ import annotations


def player_name(match: dict, number: int) -> str:
    """Given: the name of player 1 or 2, with a fallback when it is missing."""
    player = (match.get("players") or {}).get(f"p{number}") or {}
    return player.get("name") or f"Player {number}"


def is_match_tiebreak(score: dict) -> bool:
    """Return True when a deciding match tiebreak (first to 10) is being played.

    The API sets is_tiebreak to True and puts the breaker's points in the last
    set's games slot: [[6, 4, 10], [4, 6, 5]] reads 6-4 4-6 [10-5].
    An ordinary tiebreak only happens at 6-6, so: is_tiebreak is True AND the
    last set is not 6-6. Empty games lists mean False. (A match tiebreak that
    reaches 6-6 looks the same as an ordinary one; treat it as ordinary.)
    """
    # TODO
    raise NotImplementedError


def set_scores(games: list, match_tiebreak: bool = False) -> list[str]:
    """[[6, 3], [4, 4]] -> ["6-4", "3-4"].

    If one list is longer than the other, stop at the shorter one.
    When match_tiebreak is True, pair the scores first, then put brackets
    round the last pair: "[10-5]".
    """
    # TODO
    raise NotImplementedError


def point_score(score: dict, match: dict) -> str | None:
    """Describe the game in progress.

    - points missing or not two values: None
    - ordinary tiebreak: "tiebreak 5-3"
    - match tiebreak: None (the score is already in the sets part)
    - 40-40: "deuce"
    - "AD" for a player: "advantage <name>"
    - anything else: "30-15" (player 1 first)
    """
    # TODO
    raise NotImplementedError


def format_score(match: dict) -> str:
    """Build the full line.

    - score is None and status is not "completed": "not started"
    - score is None and status "completed" (a walkover has no score row):
      "no result" for an unresolved or abandoned outcome, otherwise
      "<winner name> won by walkover" when outcome is "walkover",
      "<winner name> won" for another outcome, or "final" with no winner
    - games is None (the API withheld the score): "score unavailable"
    - no games yet ([[], []]): use "0-0" for the sets part
    - status "completed":
      - outcome "unresolved" or "abandoned" (nobody was awarded the match):
        "<sets>, no result"
      - otherwise "<sets>, <winner name> won". Use the match's `winner`
        field (1 or 2) when it is set. If it is null, take the winner from
        `sets` (or write "<sets>, final" when sets are level).
    - otherwise join the sets part, the point score and "<name> serving"
      with ", ". Leave out the parts that are None.
    """
    # TODO
    raise NotImplementedError


if __name__ == "__main__":
    example = {
        "status": "live",
        "players": {"p1": {"name": "Jannik Sinner"}, "p2": {"name": "Carlos Alcaraz"}},
        "score": {"sets": [1, 0], "games": [[6, 3], [4, 4]], "points": ["30", "15"], "server": 1, "is_tiebreak": False},
    }
    print(format_score(example))
