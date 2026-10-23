# Exercise 7: Errors

**Level:** Intermediate · **Time:** about 45 minutes · **Network:** optional

## Goal

Turn API errors into messages a person can act on. You will meet a wrong key (401), an endpoint above your plan (403) and an id that does not exist (404). Then you will trigger all three on purpose.

```
a bad key: HTTP 401 unauthorized: the API did not accept your key. Check that LIVETENNISAPI_KEY ...
a paid endpoint: HTTP 403 upgrade_required: /rankings?system=atp is not part of your plan. ...
an unknown id: HTTP 404 not_found: nothing exists at /players/999999999. Check the id.
```

## What you learn

- What the common HTTP error codes mean, and who has to fix each one.
- How plan gating works: your plan opens some endpoints and not others.
- How to define your own exception type that carries a status and a code.
- How to survive a body that is not JSON, such as an HTML error page from a proxy.

## Before you start

Every error body from this API is JSON with a stable `error` code. Some add a `detail` sentence or an `allowed` list of valid values.

| Status | Code | Meaning | Who fixes it |
|---|---|---|---|
| 400 | `bad_status`, `bad_tour`, ... | a parameter has a bad value | you, in the request |
| 401 | `unauthorized` | the key is missing, wrong or disabled | you, in your setup |
| 403 | `upgrade_required` | the endpoint is above your plan | nobody in code. It is a plan question |
| 404 | `not_found` | no such id | you, or the user who typed it |
| 429 | `rate_limited` | too many requests (exercise 6) | your loop |

The free plan covers live and upcoming matches, current scores, players, fixtures, tournaments and your usage. Market prices, rankings listings and model analysis need a paid plan. The API answers `403` for those instead of an empty list. An empty list would look like "no data" and hide the real reason.

History works a little differently. The spec says a free key "may spend 20 calls per calendar month on the history endpoints". After that, history calls answer `403 upgrade_required` with `free_history_taste: "used"`.

A 429 with the code `abuse_throttled` is the strongest signal of all. The API blocks a client that keeps calling far past its limit for 24 hours. Your message should say so.

Refused requests do not spend your daily allowance, so running this exercise for real costs nothing.

## Steps

1. `explain_error`: build one message for each case in the table. Start every message with `HTTP <status>`.
2. For 403, name the path, list what the free plan covers and link the pricing page. If the body says `"free_history_taste": "used"`, say the free history calls for the month are gone.
3. For 404, name the path. If the body has a `see` link, include it.
4. `request_json`: return the body on 200. Otherwise raise `ApiError` with the status, the code and your message.
5. Run the starter with your key. `demo` makes the three bad calls on purpose and prints your messages.

## Hints

- Parse the body inside a `try`. A 502 from a proxy may be HTML.
- Keep the `error` code in the exception. A program can branch on `upgrade_required`, while a person reads the message.
- The 403 call uses `/rankings?system=atp`, which needs the PRO plan. With a paid plan the demo prints "no error" for that line, and that is correct.

## Check your work

```sh
python3 -m pytest exercises/07-errors/python
node --test exercises/07-errors/js/errors.test.mjs
```

The 401 and 404 fixtures were recorded from the real API. The 403 fixture was written from the documented error shape, because the recording key was on a paid plan.

## Going further

- Add a `hint` field to `ApiError` with a short next step for each code, and print it on its own line.
- Log every error with its status, code and path, but never the key. Check your log line to be sure.
- What should a user interface show for a 403? Write the text for a button that explains the upgrade without nagging.
