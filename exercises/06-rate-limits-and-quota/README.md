# Exercise 6: Rate limits and quota

**Level:** Advanced · **Time:** about 60 minutes · **Network:** optional

## Goal

Make your code a good API citizen. Keep under 30 requests a minute and retry politely when the API says "too many". Stop when the daily quota is gone, and report how many requests are left today.

## What you learn

- How a sliding-window rate limiter works.
- How to read a `Retry-After` header and fall back to exponential backoff with a cap.
- The difference between a limit you can wait out (per minute) and one you cannot (per day).
- How to inject a clock and a sleep function so time-based code can be tested in milliseconds.

## Before you start

The free plan allows 30 requests a minute and 100 a day.

| Situation | Status | Body | What to do |
|---|---|---|---|
| over the minute limit | 429 | `{"error": "rate_limited", ...}` | wait `Retry-After` seconds, then retry |
| over the daily quota | 429 | `{"error": "rate_limited", "scope": "day", "resets_at": "..."}` | stop until `resets_at` |
| ignoring 429s for a long time | 429 | `{"error": "abuse_throttled", "retry_at_epoch": ...}` | a 24-hour block: stop, then fix your loop |

`GET /usage` reports your plan, its limits, today's calls and `today.remaining_day`. Calling it never counts against the quota. Requests the API refuses (a 403, 404 or 429) do not spend the daily allowance either.

The spec says the per-minute window is on the `X-RateLimit-*` headers of every response. On 2026-10-23 the API sent `X-RateLimit-Limit`, `X-RateLimit-Remaining` and `X-RateLimit-Reset`. The second one is the requests left in the current minute.

## Steps

1. `SlidingWindowLimiter.acquire`: keep the times of recent calls. Forget calls older than the window. If the window is full, sleep until the oldest call drops out. Then record this call.
2. `retry_delay`: use `Retry-After` when it is a number of seconds that is 0 or more. Otherwise use `base * 2 ** attempt`. Never go over `cap`.
3. `get_with_retry`: return any response that is not a 429. On a daily 429, raise `QuotaExhausted` straight away. On a minute 429, sleep and try again, up to `max_attempts` calls in total.
4. `fetch_usage` and `requests_left_today`: read `/usage` and work out what is left.
5. `minute_headroom`: read `x-ratelimit-remaining` from the headers.

In step 3, raise `ClientBlocked` for an `abuse_throttled` body. It is a kind of `QuotaExhausted`, so code that stops on one stops on both.

## Hints

- Python's `collections.deque` has a fast `popleft()`. In JS, an array with `shift()` is fine at this size.
- Never call `time.time()`, `time.sleep()`, `Date.now()` or `setTimeout` directly in your logic. Use the `clock` and `sleep` you are given, or the tests will really wait.
- `Retry-After` may be missing or not a number. Both mean "back off".
- `remaining_day` is `limits.per_day - (calls - errors)`, because only served calls spend the allowance. Use that formula when the field is missing. A `null` there means the plan has no daily cap.

## Check your work

```sh
python3 -m pytest exercises/06-rate-limits-and-quota/python
node --test exercises/06-rate-limits-and-quota/js/rate_limits.test.mjs
```

The tests use a fake clock, so a test that "waits" 60 seconds finishes at once. One test makes 100 calls through your limiter and checks that no 60-second window ever holds more than 30.

Then run the starter with your key to see your real plan and what is left today. That call is free.

## Going further

- Add random jitter to the backoff. Why does that help when many clients retry at once?
- Combine the limiter with `get_with_retry` so every call goes through both.
- Your free key and a classmate's share nothing. What happens if a whole class shares one key? Read TEACHERS.md for the answer.
