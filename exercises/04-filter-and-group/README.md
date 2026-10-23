# Exercise 4: Filter and group

**Level:** Intermediate · **Time:** about 45 minutes · **Network:** none

## Goal

Take the live slate from `/matches?status=live` and organise it. Group the matches by tour in a sensible order, sort each group, and count matches per tournament.

```
ATP (2)
  Brussels: Jiri Lehecka v Tallon Griekspoor
  Lyon (France): Tommy Paul v Corentin Moutet
CHALLENGER (2)
  ...
```

## What you learn

- How to filter, group, sort and count a list of records, the core of most data work.
- How to treat `null` as "unknown" instead of "no".
- How to sort by more than one key, with ties broken on purpose.
- How to keep a function free of side effects, so it never changes its input.

## Before you start

Each match carries these fields:

| Field | Values | Notes |
|---|---|---|
| `tour` | `atp`, `wta`, `challenger`, `itf`, `juniors` or null | null for exhibitions and team events |
| `tournament` | a name such as `"W35 Loule"` | free text |
| `draw` | `singles`, `doubles` or null | null means unknown |
| `status` | `live`, `upcoming`, `completed`, `cancelled` | |

The API's own docs warn against parsing the tournament name to find the tour. Use the `tour` field.

The `draw` field has three values on purpose. A null draw is neither singles nor doubles, so a filter for singles must leave it out.

## Steps

1. `filter_draw`: keep matches whose `draw` equals the value asked for.
2. `group_by_tour`: skip anything not live. Put a null or unknown tour in `"other"`. Return the groups in the order of `TOUR_ORDER`, then `"other"`, leaving out empty groups. Sort each group by tournament name (ignore case), then by id.
3. `count_by_tournament`: return `(name, count)` pairs. Most matches first. Break ties alphabetically.
4. Run the starter file to see `summary` print your groups.

## Hints

- In Python, `dict` keeps insertion order. Build the groups first, then copy them into a new dict in the order you want.
- In JavaScript, a plain object keeps insertion order for keys that are not numbers. A `Map` is handy while grouping.
- To sort by two keys, return a tuple in Python (`(name.casefold(), id)`). In JS, compare the names first and fall back to the ids.
- To sort counts high to low and names low to high, sort on `(-count, name)`.
- `sorted()` and `[...array].sort()` return a new list. `list.sort()` and `array.sort()` change the original.

## Check your work

```sh
python3 -m pytest exercises/04-filter-and-group/python
node --test exercises/04-filter-and-group/js/filter_group.test.mjs
```

The recorded slate has 29 live matches. Expect 2 ATP, 2 Challenger, 21 ITF and 4 in "other". "M15 Bol 2" leads the tournament count with 4.

## Going further

- The same event appears as "W15 Bol 2" and as "ITF W15 Bol 2 Women". Count by `tournament_id` instead and compare the results.
- Fetch `/matches?status=upcoming` with your key and group those too. What changes?
- `/matches` also takes a `tour` parameter. When is it better to filter on the server than in your code?
