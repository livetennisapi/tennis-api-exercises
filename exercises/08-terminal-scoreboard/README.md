# Exercise 8: Terminal scoreboard

**Level:** Advanced · **Time:** about 90 minutes · **Network:** yes, for the real run

## Goal

Build a scoreboard that runs in a terminal and refreshes live scores for a whole session. It must never spend more than the free plan allows. You choose the refresh interval and show the arithmetic that proves it fits.

```
Daily budget 100 - reserve 10 = 90 requests for polling. Session 180 min x 60 = 10800 s. ...

Live tennis: 29 matches
ATP
  Brussels | Jiri Lehecka v Tallon Griekspoor | 0-1, 30-30, Jiri Lehecka serving
  Lyon (France) | Tommy Paul v Corentin Moutet | 6-4 3-6 2-0, 0-15, Corentin Moutet serving
CHALLENGER
  ...
```

## What you learn

- How to plan an API budget before you write the loop.
- How to reuse your own code from earlier exercises.
- How to write a polling loop that stops cleanly, backs off on 429 and never overspends.
- How to test a loop that runs for hours, in a fraction of a second.

## The arithmetic

The free plan gives 100 requests a day. One call to `/matches?status=live&limit=200` returns every live match, so one refresh costs one request. Keep 10 requests in reserve for other work, such as a search or a retry. That leaves 90 for polling.

For a session of `S` minutes:

```
usable   = 100 - 10                 = 90 requests
seconds  = S x 60
interval = ceil(seconds / usable)
check:     ceil(seconds / interval) <= usable
```

| Session | Seconds | Interval | Requests used |
|---|---|---|---|
| 1 hour | 3,600 | 40 s | 90 |
| 2 hours | 7,200 | 80 s | 90 |
| 3 hours | 10,800 | 120 s | 90 |
| 10 minutes | 600 | 7 s | 86 |

Round the interval up, never down. Rounding down would give a few more polls than the budget allows.

The minute limit sets a floor too. At 30 requests a minute, polling every 2 seconds uses the whole minute and leaves nothing for a search. So the floor here is 3 seconds, one more than the limit allows. It only matters for sessions of 4 minutes or less.

A 2-minute refresh can feel slow for live tennis. That is the trade the free plan asks of you. A shorter session buys a faster refresh.

## Steps

### Part 1: the arithmetic

1. `poll_interval_seconds`: apply the formula above. Raise `ValueError` (`RangeError` in JS) for a session of 0 minutes or less, or for a reserve that leaves nothing.
2. `requests_needed`: how many requests a session will use at a given interval.
3. `explain_interval`: return your working as a short paragraph. Include the budget, the reserve, the usable requests, the session in seconds, the interval and the requests used.

### Part 2: the board

4. `format_score`: copy your function from exercise 2.
5. `render_board`: a header line, then each tour in order with its matches, as in the example above.

### Part 3: the loop

6. `run_scoreboard`: poll, print, sleep, repeat. Stop when the session is over or the budget is spent. On a 429, wait the longer of your interval and `Retry-After`. Stop on a daily 429, an `abuse_throttled` 429, a 401 or a 403. Carry on after a 500, at the next poll.

## Hints

- Count requests as you make them and check the count at the top of the loop.
- Decide whether to stop before you sleep: if `elapsed + wait` reaches the session length, there is no point sleeping first.
- Check the clock again before each request. A laptop that sleeps can wake long after the session ended, and that late poll would spend a request for nothing.
- The tests replace `clock`, `sleep` and `out`. Your loop should never call `print`, `time.sleep` or `console.log` directly.
- Clear the screen between boards if you like (`print("\033[2J\033[H")`), but do it in `main`, not in `render_board`. The tests compare plain text.

## Check your work

```sh
python3 -m pytest exercises/08-terminal-scoreboard/python
node --test exercises/08-terminal-scoreboard/js/scoreboard.test.mjs
```

One test runs a 10-hour session against a fake clock and checks that it makes no more than 90 requests. Another feeds a 429 with `Retry-After: 45` and checks that your loop waits 45 seconds.

Then run it for real for a short session, such as 20 minutes:

```sh
python3 exercises/08-terminal-scoreboard/python/starter.py 20
```

## Going further

- Call `/usage` at start-up and size the budget from `today.remaining_day` instead of assuming 100. That call is free.
- Highlight a match at break point with your function from exercise 3.
- Show only one tour, using the `tour` query parameter. Does that change the cost of a refresh?
- Compare your interval with the 1 Hz polling a broadcast graphic needs. Which plan would that take?
