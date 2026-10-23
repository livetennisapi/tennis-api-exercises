// Exercise 8: a terminal scoreboard that stays inside the FREE quota.
//
// The FREE plan allows 100 requests a day and 30 a minute. One poll of
// GET /matches?status=live&limit=200 is one request and returns every live
// match, so the whole board costs one request per refresh.
//
// Run the tests with: node --test exercises/08-terminal-scoreboard/js/scoreboard.test.mjs
// Run it for real (a 3-hour session):
//   node exercises/08-terminal-scoreboard/js/starter.mjs 180

import { pathToFileURL } from 'node:url';

export const BASE_URL = 'https://api.livetennisapi.com/api/public/v1';
export const LIVE_URL = `${BASE_URL}/matches?status=live&limit=200`;
export const TOUR_ORDER = ['atp', 'wta', 'challenger', 'itf', 'juniors'];

// Given code
export const authHeaders = (key) => ({ Authorization: `Bearer ${key}`, Accept: 'application/json' });
export const realClock = () => performance.now() / 1000; // seconds
export const realSleep = (seconds) => new Promise((resolve) => setTimeout(resolve, seconds * 1000));

// --- Part 1: the arithmetic -------------------------------------------------

// Whole seconds to wait between polls so the session fits the budget.
//   usable   = dailyBudget - reserve        (keep a reserve for other calls)
//   polls    = floor(usable / requestsPerPoll)
//   interval = ceil(sessionMinutes * 60 / polls)
// Stay under the minute limit with a second to spare:
// at least ceil(60 * requestsPerPoll / perMinute) + 1.
// Throw a RangeError when sessionMinutes <= 0 or usable < requestsPerPoll.
export function pollIntervalSeconds(sessionMinutes, { dailyBudget = 100, reserve = 10, requestsPerPoll = 1, perMinute = 30 } = {}) {
  // TODO
  throw new Error('not implemented');
}

// Requests a session uses: ceil(session seconds / interval) * requestsPerPoll.
export function requestsNeeded(sessionMinutes, interval, requestsPerPoll = 1) {
  // TODO
  throw new Error('not implemented');
}

// Show your working as one paragraph. It must contain the budget, the reserve,
// the usable requests, the session in seconds, the interval, and the requests
// the session will use. For 180 minutes: 100 - 10 = 90 requests;
// 180 x 60 = 10800 s; 10800 / 90 = 120 s; check 10800 / 120 = 90 requests.
export function explainInterval(sessionMinutes, { dailyBudget = 100, reserve = 10 } = {}) {
  // TODO
  throw new Error('not implemented');
}

// --- Part 2: the board ------------------------------------------------------

// Copy your formatScore from exercise 2 (and its helpers).
export function formatScore(match) {
  // TODO
  throw new Error('not implemented');
}

// Build the text for one refresh.
// - Only status "live" counts. None live: "No live matches right now."
// - First line: "Live tennis: <n> matches" ("1 match" for one).
// - Then each tour in TOUR_ORDER, then "other" (null or unknown tour): a line
//   with the tour in capitals, e.g. "ATP", then one line per match, sorted by
//   tournament (ignoring case) then id:
//   "  <tournament> | <p1 name> v <p2 name> | <formatScore(match)>"
// - Leave out tours with no matches. A null tournament prints as
//   "Unknown tournament".
export function renderBoard(matches) {
  // TODO
  throw new Error('not implemented');
}

// --- Part 3: the loop -------------------------------------------------------

// Poll LIVE_URL until the session ends. Resolve to the number of requests made.
// - interval = pollIntervalSeconds(...). Never make more than
//   dailyBudget - reserve requests.
// - 200: out(renderBoard(data)).
// - 429 with "scope": "day" or error "abuse_throttled" in the body: out a
//   message and stop.
// - other 429: wait the larger of interval and the Retry-After header.
// - 401 or 403: out a message and stop.
// - anything else: out a message and carry on at the next poll.
// - Before sleeping, stop if (clock() - start) + wait >= session seconds.
// - Before every request after the first, stop if the session is over. A
//   sleep can wake late, and a late poll would spend a request you planned
//   to keep.
// Use the fetchImpl, clock, sleep and out you are given; the tests replace them.
export async function runScoreboard(
  key,
  sessionMinutes,
  { fetchImpl = fetch, sleep = realSleep, clock = realClock, out = console.log, dailyBudget = 100, reserve = 10 } = {},
) {
  // TODO
  throw new Error('not implemented');
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const key = (process.env.LIVETENNISAPI_KEY ?? '').trim();
  if (!key) {
    console.error('Set LIVETENNISAPI_KEY first.');
    process.exitCode = 1;
  } else {
    const minutes = Number(process.argv[2] ?? 180);
    console.log(explainInterval(minutes));
    const calls = await runScoreboard(key, minutes, { out: (text) => console.log(`\n${text}`) });
    console.log(`Done after ${calls} requests.`);
  }
}
