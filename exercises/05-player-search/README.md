# Exercise 5: Player search

**Level:** Intermediate · **Time:** about 45 minutes · **Network:** optional

## Goal

Find a player by name, then read their full record. Your code must handle three outcomes: no match, exactly one, and many.

```
$ python3 starter.py Jannik Sinner
Jannik Sinner (ITA), ATP rank 1, 10950 points
$ python3 starter.py williams
64 players match. Be more specific, for example: Venus Williams, Cooper Williams, ...
```

## What you learn

- How to encode user input safely in a query string.
- How to design for zero, one and many results instead of assuming one.
- How to chain two requests: search for an id, then fetch the record.
- Why you check what came back instead of trusting the request.

## Before you start

The search endpoint is `GET /players?search=<text>`. It returns `{"data": [...], "meta": {...}}`, ranked players first. `GET /players/{id}` returns one player object.

The parameter is `search`, not `name`. The spec lists no `name` parameter, and on 2026-10-23 the API ignored it. `/players?name=sinner` answered 200 with the first page of the whole roster, 40,464 players, starting with Elena Rybakina. Nothing failed, and the answer was wrong. That is why your code should look at the results it gets.

Search results include doubles teams such as "Sinner / Sonego". Each row has `is_doubles_team` to tell them apart.

## Steps

1. `search_url`: build the URL. Encode the name, so a space becomes `%20`.
2. `search_players`: refuse a blank name before making any request. Return the players and `meta.total`.
3. `pick_player`: if only part of the results came back, raise `AmbiguousPlayer`. Otherwise drop doubles teams, then decide. None left raises `PlayerNotFound`. One left is the answer. More than one raises `AmbiguousPlayer` with up to five candidate names.
4. `get_player`: fetch `/players/{id}`. A 404 raises `PlayerNotFound`.
5. `describe_player`: one line with name, country, tour, rank and points. Cope with null fields, and with a rank that is no longer current.
6. `find_player`: put it together.

## Hints

- Python: `urllib.parse.quote(name)`. JavaScript: `encodeURIComponent(name)`.
- "sinner" finds two singles players: Jannik Sinner and a separate roster entry called "Sinner". Do not guess between them. Ask the user.
- `meta.total` counts every match, while `data` holds only one page. Use the total in your message.
- `ranking` is null for doubles teams and for players who were never ranked. A player who has dropped off the table keeps the last rank they held, with `ranking_status: "unranked"`. Check the status before you call a rank current. Cooper Williams in the fixture is one such player.
- When `meta.total` is bigger than the page you got, a better match may be on the next page. Do not pick a player, or say "not found", until you have all the results.

## Check your work

```sh
python3 -m pytest exercises/05-player-search/python
node --test exercises/05-player-search/js/player_search.test.mjs
```

The fixtures hold real searches: one with no results, one with exactly one, "sinner" with teams mixed in, and "williams" with 64 results. Your function should handle all four the same way the tests expect.

Then set your key and try your own searches. Each run costs one or two requests.

## Going further

- Let the user pick from the candidates by number, then fetch that player.
- If one candidate's name matches the search exactly, should it win? Try it with "sinner" and decide whether you like the result.
- Page through all 64 Williams results with `offset`. How many requests does that cost?
