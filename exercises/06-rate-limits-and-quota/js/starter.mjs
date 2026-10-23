// Exercise 6: rate limits and quota.
//
// The FREE plan allows 30 requests a minute and 100 a day. Go over the
// minute limit and the API answers 429 with a Retry-After header (seconds).
// Go over the day limit and the 429 body says "scope": "day"; retrying then
// only wastes time until the quota resets.
//
// GET /usage reports your plan, its limits and today's calls. Calling it
// does not count against the quota.
//
// Run the tests with: node --test exercises/06-rate-limits-and-quota/js/rate_limits.test.mjs

import { pathToFileURL } from 'node:url';

export const BASE_URL = 'https://api.livetennisapi.com/api/public/v1';

// Given code
export const authHeaders = (key) => ({ Authorization: `Bearer ${key}`, Accept: 'application/json' });
export const realClock = () => performance.now() / 1000; // seconds
export const realSleep = (seconds) => new Promise((resolve) => setTimeout(resolve, seconds * 1000));

export class QuotaExhausted extends Error {
  constructor(message, resetsAt = null) {
    super(message);
    this.resetsAt = resetsAt;
  }
}

// The 24-hour block for clients that keep calling far past their limit.
export class ClientBlocked extends QuotaExhausted {
  constructor(message, retryAtEpoch = null) {
    super(message, null);
    this.retryAtEpoch = retryAtEpoch;
  }
}

export class RateLimited extends Error {}

export const SECONDS = /^\s*[0-9]+(\.[0-9]+)?\s*$/; // "12" or "1.5", nothing else

// Your code

// Allow at most maxCalls in any window of `period` seconds.
// clock() returns the time in seconds and sleep(seconds) returns a promise.
// The tests pass in a fake clock, so never call Date.now() directly.
export class SlidingWindowLimiter {
  constructor(maxCalls = 30, period = 60, clock = realClock, sleep = realSleep) {
    this.maxCalls = maxCalls;
    this.period = period;
    this.clock = clock;
    this.sleep = sleep;
    this.calls = []; // times of recent calls, oldest first
  }

  // Wait until one more call is allowed, record it, resolve to the seconds waited.
  // 1. Forget calls made `period` or more seconds ago.
  // 2. While maxCalls remain, sleep until the oldest one is `period` old, then
  //    read the clock and forget old calls again. (A timer can fire a little
  //    early, so check again instead of assuming.)
  // 3. Record the time of this call.
  async acquire() {
    // TODO
    throw new Error('not implemented');
  }
}

// Seconds to wait before retry number `attempt` (0 for the first retry).
// - If retryAfter (a header value such as "12" or "1.5") matches SECONDS, use
//   it, but never more than `cap`. Anything else ("soon", "-5", "0x1A",
//   "Infinity") does not count.
// - Otherwise back off exponentially: base * 2 ** attempt, capped at `cap`.
export function retryDelay(attempt, retryAfter = null, base = 1, cap = 60) {
  // TODO
  throw new Error('not implemented');
}

// Call fetchImpl(url, init) and retry on 429.
// - Any status other than 429: return the response at once.
// - 429 whose body has error "abuse_throttled": throw ClientBlocked with
//   retryAtEpoch from the body's retry_at_epoch. Do not retry.
// - 429 whose body has "scope": "day": throw QuotaExhausted with resetsAt from
//   the body's resets_at. Do not retry, whatever Retry-After says.
// - Other 429s: await sleep(retryDelay(attempt, Retry-After header)) and retry.
// - After maxAttempts tries in total, throw RateLimited.
export async function getWithRetry(url, init = {}, { fetchImpl = fetch, sleep = realSleep, maxAttempts = 4, cap = 60 } = {}) {
  // TODO
  throw new Error('not implemented');
}

// GET /usage with the key and return the parsed body. Throw on non-200.
export async function fetchUsage(key, fetchImpl = fetch) {
  // TODO
  throw new Error('not implemented');
}

// How many requests the key can still make today.
// - Use today.remaining_day when the field is present (null there means the
//   plan has no daily cap).
// - Otherwise: limits.per_day minus served calls (today.calls - today.errors,
//   where a missing or null count is 0), never below 0.
// - Return null when limits.per_day is null.
export function requestsLeftToday(usage) {
  // TODO
  throw new Error('not implemented');
}

// Requests left in the current minute, from the x-ratelimit-remaining header.
// `headers` is a plain object with lower-case names. Return null when the
// header is absent, blank or not a plain whole number ("29abc" is not).
export function minuteHeadroom(headers) {
  // TODO
  throw new Error('not implemented');
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const key = (process.env.LIVETENNISAPI_KEY ?? '').trim();
  if (!key) {
    console.error('Set LIVETENNISAPI_KEY first.');
    process.exitCode = 1;
  } else {
    const usage = await fetchUsage(key);
    const left = requestsLeftToday(usage);
    console.log(`Plan: ${usage.tier}, ${usage.limits?.per_minute} per minute, ${usage.limits?.per_day} per day.`);
    console.log(left === null ? 'No daily cap on this plan.' : `${left} requests left today.`);
  }
}
