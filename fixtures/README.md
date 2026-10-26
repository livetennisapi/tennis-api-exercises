# Fixtures

These files are API responses that the tests replay, so the tests run offline and never touch anyone's quota. Every request here is one the free plan can make, apart from the deliberate 403 example.

## Licence and credit

The fixtures are licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0). You may copy, share and adapt them for any purpose, including commercial teaching. Credit them like this:

> Tennis data: Live Tennis API (https://livetennisapi.com), CC BY 4.0.

The code elsewhere in this repository is under the MIT licence. The CC BY 4.0 terms cover only the files in this folder. The full legal code is in [LICENSE](LICENSE) in this folder.

## File format

Each file holds one request and its response:

```json
{
  "source": "recorded from the live API on 2026-10-23",
  "request": { "method": "GET", "path": "/players/34", "auth": "header" },
  "response": { "status": 200, "headers": { "x-ratelimit-limit": "" }, "body": { "...": "..." } }
}
```

`auth` is `header` when the request sent the key in an `Authorization: Bearer` header. It is `none` for `/health` and `bad` for the deliberate wrong key. Paths are relative to `https://api.livetennisapi.com/api/public/v1`.

## What is here

| File | Request | Status | Origin |
|---|---|---|---|
| `health.json` | `/health` with no key | 200 | recorded |
| `matches_live.json` | `/matches?status=live&limit=200` | 200 | recorded, 29 live matches |
| `players_search_none.json` | `/players?search=zzqxv&limit=10` | 200 | recorded, no results |
| `players_search_one.json` | `/players?search=Jannik%20Sinner&limit=10` | 200 | recorded, one result |
| `players_search_sinner.json` | `/players?search=sinner&limit=10` | 200 | recorded, singles players and doubles teams |
| `players_search_williams.json` | `/players?search=williams&limit=10` | 200 | recorded, first 10 of 64 |
| `player_34.json` | `/players/34` | 200 | recorded |
| `error_401_bad_key.json` | `/matches` with a wrong key | 401 | recorded |
| `error_404_player.json` | `/players/999999999` | 404 | recorded |
| `error_403_upgrade_required.json` | `/rankings?system=atp` | 403 | built from the spec |
| `error_429_minute.json` | `/matches` over the minute limit | 429 | built from the spec |
| `error_429_day.json` | `/matches` over the daily quota | 429 | built from the spec |
| `error_429_abuse.json` | `/matches` after ignoring 429s | 429 | built from the spec |
| `usage_free.json` | `/usage` on a free key | 200 | built from the spec |

## How they were made

The recorded files came from `scripts/record_fixtures.py` on 2026-10-23. The recording key was on a paid plan, so the script changes two things to show what the free plan returns:

- It sets the paid-only fields to null. On a match score these are `win_probability_p1`, `danger`, `win_probability_p1_model` and `win_probability_meta`. On a player they are `itf_ranking`, `height_cm` and `doubles_ranking`, and it removes `itf_id`. The spec says height is null on a free key, so the copy inside `stats.ratings.meta` is set to null too.
- It keeps the names of the `X-RateLimit-*` headers but blanks their values, because the numbers describe the recording key's plan.

No file contains the key. The script reads it from `LIVETENNISAPI_KEY` and sends it only in a header. It replaces any echo of it, raw or URL-encoded, and refuses to write if any 8-character piece remains. It also checks every status and body first, so a failed run changes no file.

A paid plan cannot produce the free plan's 403, 429 or usage response. So five files were written by hand from the shapes in the [OpenAPI spec](https://docs.livetennisapi.com/openapi.yaml), version 1.13.68. The error codes and field names follow the spec. Where the spec gives no example value, such as the `price` on a minute-limit 429 or the `resets_at` instant, the value is a stand-in. Each of these files says so in its `source` field.

## Re-recording

Live data moves, so a fresh recording will not match the expected values in the tests. If you re-record for your own class, update the tests to match. Recording spends about ten requests:

```sh
LIVETENNISAPI_KEY=your_key python3 scripts/record_fixtures.py
```
