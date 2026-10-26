# Tennis API coding exercises in Python and JavaScript

Eight graded coding exercises that teach students to work with a real JSON API. Each one comes in Python and JavaScript, with tests that run offline. The data is live tennis from the free plan of [Live Tennis API](https://livetennisapi.com).

Students start by calling a health endpoint. By the end they have built a terminal scoreboard that polls live scores and stays inside a daily quota of 100 requests.

## Who it is for

The set fits an introductory programming course, a web APIs module, a data course or a bootcamp week. Students need to know functions, loops and dictionaries (or objects in JavaScript). Nothing else is assumed.

Teachers should read [TEACHERS.md](TEACHERS.md). It covers learning outcomes, a suggested order, a grading rubric for each exercise and the mistakes students make most often. It also explains how to run a whole class on the free quota.

## What you need

- Python 3.11 or newer with pytest, or Node.js 22 or newer. Both if you want both tracks.
- No other packages. The code uses the Python standard library and the `fetch` built into Node.
- A free API key, but only for running your code against the real API. The tests do not need one.

Get a free key at <https://livetennisapi.com/subscribe/free>. It needs no card. Then put it in an environment variable, never in your code:

```sh
export LIVETENNISAPI_KEY=your_key_here        # macOS and Linux
setx LIVETENNISAPI_KEY your_key_here          # Windows, then open a new terminal
```

The commands below use `python3`, as on macOS and Linux. On Windows, type `python` instead.

## Run the tests

Each exercise folder holds a starter file for you to fill in, the tests, and a worked solution. The tests replay recorded API responses from [fixtures/](fixtures/), so they run without a network or a key.

```sh
python3 -m venv .venv                              # once: a private place for pytest
source .venv/bin/activate                          # each new terminal (Windows: .venv\Scripts\activate)
pip install pytest                                 # once

python3 scripts/run_python_tests.py 01             # test your Python starter for exercise 1
node scripts/run-js-tests.mjs 01                   # test your JavaScript starter for exercise 1

python3 scripts/run_python_tests.py --solutions    # every Python solution
node scripts/run-js-tests.mjs --solutions          # every JavaScript solution
```

Recent Debian and Ubuntu refuse a plain `pip install` outside a virtual environment, which is why the first two lines are there.

With `make` you can type `make -k test EX=01`, `make solutions` or `make check` instead. The `-k` makes the JavaScript tests run even when the Python ones fail. The starters fail their tests until you write the code. That is the point.

You can also call pytest or node directly. Set `SOLUTION=1` to point the tests at the solution instead of the starter:

```sh
python3 -m pytest exercises/02-read-a-score/python
node --test exercises/02-read-a-score/js/read_score.test.mjs
SOLUTION=1 python3 -m pytest exercises/02-read-a-score/python      # macOS and Linux
$env:SOLUTION=1; python -m pytest exercises/02-read-a-score/python # Windows PowerShell
```

To check that the tests are strong enough, `python3 mutants/run_mutants.py` (or `make mutants`) applies over 100 plausible wrong solutions and confirms the tests reject every one.

### The live smoke test

A small optional test runs the solutions against the real API. Each language spends about three requests of your daily quota, so both together spend about six. Checking usage and the refused calls cost nothing.

```sh
LIVE=1 python3 scripts/run_python_tests.py --smoke      # macOS and Linux
LIVE=1 node scripts/run-js-tests.mjs --smoke
$env:LIVE=1; node scripts/run-js-tests.mjs --smoke      # Windows PowerShell
```

## The exercises

| # | Exercise | You learn to | Level | Time |
|---|---|---|---|---|
| 1 | [First request](exercises/01-first-request/) | call an endpoint with no key, then with a key from the environment | Beginner | 30 min |
| 2 | [Read a score](exercises/02-read-a-score/) | turn player-major score arrays into a line such as "6-4 3-4, 30-15" | Beginner | 45 min |
| 3 | [Break points](exercises/03-break-points/) | write a pure function with careful edge cases | Intermediate | 40 min |
| 4 | [Filter and group](exercises/04-filter-and-group/) | group live matches by tour and count them by tournament | Intermediate | 45 min |
| 5 | [Player search](exercises/05-player-search/) | handle zero, one and many search results | Intermediate | 45 min |
| 6 | [Rate limits and quota](exercises/06-rate-limits-and-quota/) | respect 30 requests a minute, retry a 429 and read your quota | Advanced | 60 min |
| 7 | [Errors](exercises/07-errors/) | turn 401, 403 and 404 responses into messages people understand | Intermediate | 45 min |
| 8 | [Terminal scoreboard](exercises/08-terminal-scoreboard/) | poll live scores at a rate that fits 100 requests a day | Advanced | 90 min |

Exercises 2, 3 and 4 need no network at all. Exercises 1, 5, 6, 7 and 8 make real requests when you run the program, and use fixtures when you run the tests.

## The API in one screen

- Base URL: `https://api.livetennisapi.com/api/public/v1`
- Send the key as `Authorization: Bearer <key>` or `X-API-Key: <key>`. A `?token=<key>` query parameter also works, but URLs end up in logs and browser history, so use a header in code.
- `GET /health` needs no key.
- The free plan covers live and upcoming matches, current scores, players, fixtures, tournaments and your own usage. It allows 30 requests a minute and 100 a day.
- Market prices, model fields and the WebSocket feed need a paid plan. An endpoint above your plan answers `403 {"error":"upgrade_required"}`.
- Historical results are not part of the free plan. The spec says a free key "may spend 20 calls per calendar month on the history endpoints". Past that they answer `403 upgrade_required` with `free_history_taste: "used"`.
- Every score array is player-major. `"games": [[6,3],[4,4]]` reads 6-4 in the first set and 3-4 in the second.

The full reference is at <https://docs.livetennisapi.com>. The OpenAPI spec is at <https://docs.livetennisapi.com/openapi.yaml>.

## Folder layout

```
exercises/NN-name/
  README.md             goal, steps, hints, how to check your work
  python/starter.py     your Python file
  python/test_*.py      the Python tests
  js/starter.mjs        your JavaScript file
  js/*.test.mjs         the JavaScript tests
  solutions/python/     a worked Python solution
  solutions/js/         a worked JavaScript solution
fixtures/               recorded API responses the tests replay (CC BY 4.0)
smoke/                  the optional live test
mutants/                wrong solutions the tests must reject, and their runner
scripts/                test runners and the fixture recorder
```

## Licence

The code is under the [MIT licence](LICENSE). The recorded responses in `fixtures/` are under CC BY 4.0, credited to Live Tennis API. See [fixtures/README.md](fixtures/README.md). If you cite the set in a paper or a syllabus, [CITATION.cff](CITATION.cff) has the details.

## Related

- Official Python client: [livetennisapi on PyPI](https://pypi.org/project/livetennisapi/)
- Official JavaScript client: [livetennisapi on npm](https://www.npmjs.com/package/livetennisapi)
- Source for this set: <https://github.com/livetennisapi/tennis-api-exercises>

The exercises use plain HTTP on purpose, so students see every header and status code. The clients are the better choice once they have.
