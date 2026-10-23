# Exercise 3: Break point detector

**Level:** Intermediate · **Time:** about 40 minutes · **Network:** none

## Goal

Write a pure function that says whether the next point is a break point. Then use it to find every live match that is at break point right now.

## What you learn

- How to turn a rule from the real world into code, edge cases included.
- How to map string values to numbers with a lookup table.
- How to use an index (`server`) to pick values out of a player-major array.
- How to test a function with a table of cases.

## The tennis you need

The player serving is the server and the other player is the receiver. A break point is a point where the receiver wins the game by winning that point.

Scores below are written server first.

| Score | Break points held |
|---|---|
| 0-40 | 3 |
| 15-40 | 2 |
| 30-40 | 1 |
| 40-40 (deuce) | 0 |
| advantage receiver | 1 |
| advantage server | 0 |
| 40-15 | 0 (the server has game points) |

A tiebreak has no break points, because the serve changes every two points.

Some events play a no-ad rule, where the point at deuce decides the game. Most tour and ITF doubles matches use it, and then 40-40 is a break point for the receiver. The API does not say which matches use no-ad, so this exercise ignores it. Keep that in mind for the six doubles matches in the fixture.

## Before you start

The API sends points player-major, not server first. With `"points": ["15", "40"]` and `"server": 1`, player 1 is serving at 15-40. That is two break points. With the same points and `"server": 2`, player 2 is serving at 40-15. That is none.

## Steps

1. `point_value`: map `"0"`, `"15"`, `"30"`, `"40"` and `"AD"` to 0, 1, 2, 3 and 4. Raise `ValueError` (a `RangeError` in JS) for anything else.
2. `break_points_held`: find the server's points and the receiver's points, then apply the table. Return 0 for a tiebreak, a missing score, a missing server or missing points.
3. `is_break_point`: true when at least one break point is held.
4. `find_break_points`: return the ids of live matches at break point, in the order given.

## Hints

- The server's points are `points[server - 1]`. The receiver's are `points[2 - server]`.
- With the receiver on 40, the number of break points is 3 minus the server's value.
- Check `is_tiebreak` first. Tiebreak points such as `"5"` are not in your lookup table.

## Check your work

```sh
python3 -m pytest exercises/03-break-points/python
node --test exercises/03-break-points/js/break_points.test.mjs
```

In the recorded slate, two matches are at break point: 209391 (15-40) and 207819 (40-AD). Your `find_break_points` should return exactly those, in that order.

## Going further

- Count the break points across the whole slate.
- A set point or match point follows the same idea one level up. Write `is_set_point` for normal sets without a tiebreak.
- The API's ULTRA plan can push a `break_point` event over a WebSocket. Why would a big app want that instead of polling and running this function?
