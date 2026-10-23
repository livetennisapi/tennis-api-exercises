# Exercise 2: Read a score

**Level:** Beginner · **Time:** about 45 minutes · **Network:** none

## Goal

Write a pure function that turns one match from `/matches` into a line a person can read.

```
6-4 3-4, 30-15, Jannik Sinner serving
```

## What you learn

- How to read nested JSON: a match holds `players` and a `score`, and the score holds arrays of arrays.
- How a player-major layout works, and how to walk two lists side by side.
- How to handle missing data (`null`) without crashing.
- How to grow a function one edge case at a time, with a test for each.

## Before you start

Every score array in the API is player-major. The first list is player 1 and the second is player 2.

| Field | Example | Meaning |
|---|---|---|
| `sets` | `[1, 0]` | player 1 has won one set, player 2 none |
| `games` | `[[6, 3], [4, 4]]` | set 1 went 6-4, set 2 is 3-4 |
| `points` | `["30", "15"]` | the game in progress, player 1 first |
| `server` | `1` | player 1 is serving |
| `is_tiebreak` | `false` | the current game is not a tiebreak |

A common mistake is to read `games` as one list per set. It is one list per player. To get the set scores, pair `games[0][i]` with `games[1][i]`.

Point values are strings: `"0"`, `"15"`, `"30"`, `"40"` and `"AD"` for advantage. In a tiebreak they count up as plain numbers, such as `"5"`.

## Steps

Open `python/starter.py` or `js/starter.mjs`. `player_name` is written for you.

1. `set_scores`: `[[6, 3], [4, 4]]` becomes `["6-4", "3-4"]`.
2. `point_score`: the game in progress. `40-40` reads "deuce". `"AD"` reads "advantage" and the player's name. In a tiebreak, write "tiebreak 5-3".
3. `format_score`: join the parts with `", "`. Add the server's name and the word "serving" when `server` is 1 or 2.
4. Handle the edge cases below, one test at a time.

| Case | What the API sends | Expected text |
|---|---|---|
| not started | `score` is null | `not started` |
| walkover | `score` is null, `status` is `completed`, `outcome` is `walkover` | `Jannik Sinner won by walkover` |
| score withheld | `games` is null | `score unavailable` |
| no games yet | `games` is `[[], []]` | `0-0, ...` |
| finished | `status` is `completed` | `6-4 6-3, Jannik Sinner won` |
| no result | `outcome` is `unresolved` or `abandoned` | `6-4, no result` |
| match tiebreak | `is_tiebreak` true, last set not 6-6 | `6-4 4-6 [10-5], ...` |

## Hints

- `zip(games[0], games[1])` in Python pairs the two lists. In JS, use `games[0].map((a, i) => ...)`.
- A null `games` means the API holds no score it can stand behind. It never means 0-0.
- An ordinary tiebreak only happens at 6-6. A deciding match tiebreak puts the breaker's points in the last set's slot, so `[[6, 4, 10], [4, 6, 5]]` reads 6-4 4-6 [10-5]. So `is_match_tiebreak` asks one question: is the tiebreak flag on while the last set is anything other than 6-6? A breaker at 0-0 or 5-5 is still a match tiebreak.
- One case stays ambiguous. A match tiebreak that reaches 6-6 looks exactly like an ordinary tiebreak. Treat it as ordinary.
- For a finished match, use the `winner` field when it is set. When it is null, take the winner from `sets`, not from the last set's games. A player who retires loses, even when they led on sets.
- An `unresolved` or `abandoned` match has no winner at all. Do not announce one.
- Check `status` before you treat a null `score` as "not started". A walkover is completed but was never played, so it has no score row.

## Check your work

```sh
python3 -m pytest exercises/02-read-a-score/python
node --test exercises/02-read-a-score/js/read_score.test.mjs
```

Four tests use real matches from `fixtures/matches_live.json`. One of them is Tommy Paul against Corentin Moutet at Lyon, which should read `6-4 3-6 2-0, 0-15, Corentin Moutet serving`. Another runs your function over all 29 recorded matches to make sure none of them crashes it.

## Going further

- Broadcasters put the server's points first. Add an option that does this.
- Use short names: "J. Sinner" instead of "Jannik Sinner". What happens with doubles teams such as "Fryer / McKay"?
- Some recorded matches look odd, such as sets `[0, 0]` with two finished sets. Find them and decide what your function should do. Real data is messy.
