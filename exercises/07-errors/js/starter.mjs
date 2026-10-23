// Exercise 7: turn API errors into clear messages.
//
// Every error body is JSON with a stable `error` code, sometimes with a
// `detail` sentence and an `allowed` list:
//   401 {"error": "unauthorized"}       the key is missing, wrong or disabled
//   403 {"error": "upgrade_required"}   the endpoint is above your plan
//   404 {"error": "not_found"}          no such id
//   429 {"error": "rate_limited", ...}  too many requests (exercise 6)
//
// Run the tests with: node --test exercises/07-errors/js/errors.test.mjs
// See the real errors (three requests; refused calls do not use up your daily allowance):
//   node exercises/07-errors/js/starter.mjs

import { pathToFileURL } from 'node:url';

export const BASE_URL = 'https://api.livetennisapi.com/api/public/v1';
export const PRICING_URL = 'https://livetennisapi.com/pricing';
export const FREE_PLAN =
  'live and upcoming matches, current scores, players, fixtures, tournaments and usage stats';

// Given code
export const authHeaders = (key) => ({ Authorization: `Bearer ${key}`, Accept: 'application/json' });

export class ApiError extends Error {
  constructor(status, code, message) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

// Your code

// Return one clear message for a failed request. Start it with "HTTP <status>".
// - 401: say the key was not accepted and name LIVETENNISAPI_KEY.
// - 403 upgrade_required: say `path` is not on the plan, include the code
//   "upgrade_required", list what FREE covers (FREE_PLAN) and give PRICING_URL.
//   If body.free_history_taste === "used", add that the free history calls
//   for this month are used up.
// - 404: include `path` and suggest checking the id. Mention body.see if present.
// - 429: say to wait for Retry-After. If body.scope === "day", say the daily
//   quota is used up and when it resets (body.resets_at). If the code is
//   "abuse_throttled", say the key is blocked for 24 hours.
// - Never put the key in a message.
// - anything else: "HTTP <status> <code>: <detail>", plus the allowed values
//   when the body lists them.
// `body` may be an empty object when the response was not JSON.
export function explainError(status, body, path) {
  // TODO
  throw new Error('not implemented');
}

// GET BASE_URL + path with the key. Resolve to the parsed body on 200.
// Otherwise throw new ApiError(status, code, explainError(...)). The code is
// body.error, or null when the body is not JSON.
export async function requestJson(path, key, fetchImpl = fetch) {
  // TODO
  throw new Error('not implemented');
}

export const DEMO_CALLS = [
  ['a bad key', '/matches?status=live&limit=1', 'not-a-real-key'],
  ['a paid endpoint', '/rankings?system=atp', null],
  ['an unknown id', '/players/999999999', null],
];

// Given: make each call in DEMO_CALLS on purpose and collect the messages.
export async function demo(key, fetchImpl = fetch) {
  const messages = [];
  for (const [label, path, override] of DEMO_CALLS) {
    try {
      await requestJson(path, override ?? key, fetchImpl);
      messages.push(`${label}: no error (your plan may include this endpoint)`);
    } catch (error) {
      if (!(error instanceof ApiError)) throw error;
      messages.push(`${label}: ${error.message}`);
    }
  }
  return messages;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const key = (process.env.LIVETENNISAPI_KEY ?? '').trim();
  if (!key) {
    console.error('Set LIVETENNISAPI_KEY first.');
    process.exitCode = 1;
  } else {
    for (const line of await demo(key)) console.log(line);
  }
}
