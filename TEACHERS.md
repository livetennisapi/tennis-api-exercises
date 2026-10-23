# Notes for teachers

This guide is for anyone running these exercises with a group: a lecturer, a bootcamp coach or a teaching assistant. It covers what students learn, a sensible order, a rubric for each exercise and the mistakes you will see. It ends with how to keep a class inside the free quota.

## Learning outcomes

By the end of the set, a student can:

1. Make an authenticated HTTP request from Python or JavaScript, with the secret kept out of the code.
2. Read nested JSON with confidence, including arrays of arrays and fields that may be null.
3. Write pure functions with clear edge cases, and test them with a table of inputs.
4. Filter, group, sort and count records without changing the input.
5. Handle zero, one and many results from a search.
6. Explain the common HTTP error codes and turn each into a message a user can act on.
7. Respect a rate limit, retry with backoff and stop when a quota runs out.
8. Plan a request budget with arithmetic and build a polling loop that never overspends.

| Exercise | Outcomes | Level | Time |
|---|---|---|---|
| 1 First request | 1 | Beginner | 30 min |
| 2 Read a score | 2, 3 | Beginner | 45 min |
| 3 Break points | 3 | Intermediate | 40 min |
| 4 Filter and group | 2, 4 | Intermediate | 45 min |
| 5 Player search | 1, 5 | Intermediate | 45 min |
| 6 Rate limits and quota | 7 | Advanced | 60 min |
| 7 Errors | 6 | Intermediate | 45 min |
| 8 Terminal scoreboard | 7, 8 | Advanced | 90 min |

## Suggested order

The numbers give a sensible path, but you can move things around. Exercises 2, 3 and 4 need no network, so they work in a lab with no internet or before students have keys.

**One long day (about 6 hours).** Do 1, 2, 3 and 4 in the morning. After lunch, do 5 and 7, then 6. Set 8 as homework.

**Three 2-hour sessions.**

| Session | Exercises | Theme |
|---|---|---|
| 1 | 1, 2 | requests and nested data |
| 2 | 3, 4, 5 | functions, collections and search |
| 3 | 7, 6, then start 8 | errors, limits and a real program |

Doing 7 before 6 works well. Students meet the 429 error code in 7, then learn to handle it in 6.

**An intro programming course.** Use 2, 3 and 4 alone as practice with lists, dictionaries and functions. Students never need a key.

**A web APIs module.** Put the weight on 1, 5, 6 and 7, and use 8 as the assessed project.

## Running the tests

Students run the tests for their own starter file:

```sh
python3 -m pytest exercises/03-break-points/python
node --test exercises/03-break-points/js/break_points.test.mjs
```

The tests replay recorded responses from `fixtures/`, so they need no network and no key. They pass only when the student's code is right.

To check that your copy is sound, run `make check`. It runs every solution in both languages and confirms that every starter still fails, for the right reason. The GitLab CI file does the same.

To check that the tests are strong enough, run `make mutants`. It applies over 100 plausible wrong solutions, many taken from the common mistakes below, and confirms that the tests reject every one. If you add a test or change a solution, run it again.

### Hiding the solutions

The `solutions/` folders sit next to the starters. For graded work, give students a copy without them:

```sh
git clone https://gitlab.com/livetennisapi/tennis-api-exercises.git class-copy
cd class-copy
rm -rf exercises/*/solutions
```

Leave `.gitlab-ci.yml` as it is. When it finds no `solutions` folders, it grades the starters instead of checking the solutions. A student's pipeline goes green once every test in both languages passes. If you only teach one language, delete the other job.

The live smoke test also works in a class copy. Without the solutions it runs the student's own starters against the real API, so use it only once their code passes the offline tests.

## Grading rubric

Each exercise is worth 10 points. Six come from the tests, and four from reading the code.

| Points | What you are looking for |
|---|---|
| 6 | Tests. One point for each sixth of the tests that pass, rounded down. Both languages have the same tests, so a mistake costs the same in either. |
| 2 | Correctness beyond the tests. The rules for that exercise in the table below. |
| 2 | Clarity. Readable names, no dead code, no copy-and-paste where a helper would do. |

The rules for each exercise:

| Exercise | Award the 2 correctness points when the student |
|---|---|
| 1 | reads the key from the environment, never puts it in a URL, and prints a helpful message when the variable is unset |
| 2 | walks the two `games` lists in parallel instead of reading them as one list per set, and treats a null `games` as unknown |
| 3 | picks server and receiver points by index, and returns before the lookup for a tiebreak |
| 4 | treats a null `draw` as unknown, sorts by two keys on purpose and leaves the input list untouched |
| 5 | encodes the search text, uses `search` (not `name`) and never guesses between several candidates |
| 6 | injects the clock and sleep, caps the backoff and does not retry a daily 429 |
| 7 | keeps the error code on the exception, handles a body that is not JSON and never puts the key in a message |
| 8 | shows the arithmetic, rounds the interval up and stops before the budget runs out |

For exercise 8, consider two extra points for the written arithmetic. Ask for a short paragraph that justifies the chosen interval for a session length the student picks.

## Common mistakes

**Exercise 1.** Students paste their key in the code to "just test it", then commit it. Teach `git diff` before every commit. Some put `?token=` in the URL because it works in the browser. Others forget that `os.environ["X"]` raises an error when the variable is missing.

**Exercise 2.** The big one is reading `games` as one list per set. `[[6, 3], [4, 4]]` then comes out as "6-3 4-4" instead of "6-4 3-4". Others print `None-None` for a match that has not started, or treat `"AD"` as a number.

**Exercise 3.** Students mix up server and receiver. They count deuce as a break point, or forget that a tiebreak has none. Some convert `"AD"` with `int()` and crash.

**Exercise 4.** Students filter `draw != "doubles"` to get singles, which lets the unknown rows in. Others sort the input list in place and break the next test. Many parse "ITF" out of the tournament name instead of reading `tour`.

**Exercise 5.** Students use `?name=`. On 2026-10-23 the API ignored it and answered 200 with the whole roster, so everything seemed fine. Others pick the first result without checking, or build the URL by string concatenation and break on spaces and accents.

**Exercise 6.** Students call `time.sleep` directly, and the tests then really wait. Others retry forever, retry a daily 429, or let the backoff grow past any sensible cap.

**Exercise 7.** Students call `response.json()` on an HTML error page and crash inside their own error handler. Others print the raw status with no advice, or include the key in a log message.

**Exercise 8.** Students round the interval down and overspend by a few requests. Others sleep before checking whether the session has ended, or forget the minute limit for very short sessions.

## Keeping a class inside the free quota

The free plan allows 100 requests a day and 30 a minute. That is plenty for one student and far too little for a class sharing a key.

**Every student gets their own free key.** Sign-up at <https://livetennisapi.com/subscribe/free> needs no card. Never hand out one key to the room. Thirty students sharing it would hit the minute limit at once and use up the day's 100 requests within minutes.

**Work offline by default.** All the tests use the fixtures. A student can finish every exercise without a single live request. Save the live runs for the end of each exercise, when the student wants to see their code work for real.

**Share fixtures instead of live calls.** If you want fresh data for a lesson, record it once and share the files:

```sh
LIVETENNISAPI_KEY=your_key python3 scripts/record_fixtures.py
```

That costs you about ten requests. The tests expect the 2026-10-23 recording, so update the expected values if you swap the files in.

**Know what is free.** `GET /usage` never counts against the quota, so students can check their headroom as often as they like. Requests the API refuses (a 403, 404 or 429) do not spend the daily allowance. `/health` takes no key at all.

**Plan the live runs.** A typical student spends their requests like this:

| Activity | Requests |
|---|---|
| Exercise 1, run once | 1 |
| Exercise 5, three searches | about 6 |
| Exercise 6, check usage | 0 |
| Exercise 7, the three error demos | 0 |
| Exercise 8, a 20-minute session | 86 |
| The live smoke test in one language, if you use it | about 3 |
| Total | about 96 |

Exercise 8 is the only one that can use up a day. A 20-minute session polls every 14 seconds, which is 86 requests. Its budget logic keeps 10 requests in reserve, and that reserve covers the other rows.

**If a student runs out.** The 429 body gives `resets_at`, the moment the daily window resets. Until then the student can keep working against the fixtures. Running out is a fine lesson in why exercise 8 asks for the arithmetic first.

## Facts the exercises rely on

All product facts come from the [API documentation](https://docs.livetennisapi.com) and the [OpenAPI spec](https://docs.livetennisapi.com/openapi.yaml), version 1.13.68, read on 2026-10-23. If the API changes, the spec is the authority. The [changelog](https://docs.livetennisapi.com/changelog.html) lists every change by date.
