# Exercise 1: First request

**Level:** Beginner · **Time:** about 30 minutes · **Network:** optional

## Goal

Call the API twice. First call `/health`, which needs no key. Then ask how many matches are live right now, reading your key from the environment. Print the answer.

```
API is up.
29 matches are live right now.
```

## What you learn

- How a REST call is built: a base URL, a path, a query string and headers.
- Why a secret belongs in an environment variable and not in your source code.
- Why the `Authorization` header beats `?token=` in the URL.
- How a list response is shaped: `{"data": [...], "meta": {...}}`.

## Before you start

The base URL is `https://api.livetennisapi.com/api/public/v1`. The API accepts the key in three ways:

| Way | Example | Use it for |
|---|---|---|
| Header | `Authorization: Bearer <key>` | code (this exercise) |
| Header | `X-API-Key: <key>` | code, if your tool prefers it |
| Query | `?token=<key>` | a quick test in a browser |

The query form is handy for clicking a link. But a URL gets copied into server logs, browser history and the `Referer` header of the next page. Anything in it should be treated as public. A header does not travel that far.

Never put your key in a file you commit. Read it from `LIVETENNISAPI_KEY` instead. If you share your code, nobody gets your key with it.

## Steps

Open `python/starter.py` or `js/starter.mjs`. The HTTP helper is already written for you in Python. In JavaScript you call the built-in `fetch`.

1. Write `read_api_key` (`readApiKey` in JS). Read `LIVETENNISAPI_KEY`, strip spaces, and raise `MissingKeyError` if nothing is left. Name the variable in the error message so the user knows what to set.
2. Write `auth_headers`. Return a dictionary (an object in JS) with `Authorization: Bearer <key>` and `Accept: application/json`.
3. Write `check_health`. Call `/health` with no key at all and return `True` when the body says `"status": "ok"`.
4. Write `count_live_matches`. Call `/matches?status=live&limit=200` with your headers. Return `meta.total`. If `total` is null, fall back to the length of `data`.
5. Run the tests until they pass. Then set your key and run the starter file itself.

## Hints

- Every function takes the HTTP function as a parameter (`get` in Python, `fetchImpl` in JS). The tests pass in a fake that replays a recorded response. Always call the parameter, never `http_get` or `fetch` directly.
- In Python, `response.json()` parses the body. In JS it is `await response.json()`.
- `limit` defaults to 50 and goes up to 200. A busy afternoon can have more than 50 live matches.
- `meta.total` is the size of the whole filtered set. Use it instead of counting the page.
- A request with no timeout can hang for minutes on a bad connection. The Python helper waits 10 seconds at most. In JS, add `signal: AbortSignal.timeout(10_000)` next to `headers`.

## Check your work

```sh
python3 -m pytest exercises/01-first-request/python
node --test exercises/01-first-request/js/first_request.test.mjs
```

All tests should pass. They check that `/health` gets no key and that no URL contains your key. They also check that a 401 raises an error naming the status.

Then try it for real:

```sh
export LIVETENNISAPI_KEY=your_key_here
python3 exercises/01-first-request/python/starter.py
```

This spends one request of your 100 a day. The `/health` call sends no key, so it cannot touch your quota.

## Going further

- Unset the variable and run the program again. Is the message clear enough for someone who has never seen your code?
- Send the key as `X-API-Key` instead and check that it still works.
- Print the tournament of each live match as well as the count.
