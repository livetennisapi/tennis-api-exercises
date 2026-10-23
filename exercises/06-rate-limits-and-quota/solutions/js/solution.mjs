// Exercise 6 solution: rate limits and quota.

import { pathToFileURL } from 'node:url';

export const BASE_URL = 'https://api.livetennisapi.com/api/public/v1';

export const authHeaders = (key) => ({ Authorization: `Bearer ${key}`, Accept: 'application/json' });
export const realClock = () => performance.now() / 1000;
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

export class SlidingWindowLimiter {
  constructor(maxCalls = 30, period = 60, clock = realClock, sleep = realSleep) {
    this.maxCalls = maxCalls;
    this.period = period;
    this.clock = clock;
    this.sleep = sleep;
    this.calls = [];
  }

  forgetOld(now) {
    while (this.calls.length && this.calls[0] <= now - this.period) this.calls.shift();
  }

  async acquire() {
    let now = this.clock();
    this.forgetOld(now);
    let waited = 0;
    while (this.calls.length >= this.maxCalls) {
      const pause = this.calls[0] + this.period - now;
      await this.sleep(pause);
      waited += pause;
      now = this.clock();
      this.forgetOld(now);
    }
    this.calls.push(now);
    return waited;
  }
}

export function retryDelay(attempt, retryAfter = null, base = 1, cap = 60) {
  if (retryAfter !== null && retryAfter !== undefined && SECONDS.test(String(retryAfter))) {
    return Math.min(Number(retryAfter), cap);
  }
  return Math.min(base * 2 ** attempt, cap);
}

export async function getWithRetry(url, init = {}, { fetchImpl = fetch, sleep = realSleep, maxAttempts = 4, cap = 60 } = {}) {
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const response = await fetchImpl(url, init);
    if (response.status !== 429) return response;
    let body = {};
    try {
      body = await response.json();
    } catch {
      body = {};
    }
    if (body.error === 'abuse_throttled') {
      throw new ClientBlocked(
        'This key is blocked for 24 hours for ignoring rate limits. Fix the loop before trying again.',
        body.retry_at_epoch ?? null,
      );
    }
    if (body.scope === 'day') {
      throw new QuotaExhausted('The daily quota is used up. Stop and try again after it resets.', body.resets_at ?? null);
    }
    if (attempt === maxAttempts - 1) break;
    await sleep(retryDelay(attempt, response.headers.get('retry-after'), 1, cap));
  }
  throw new RateLimited(`Still rate limited after ${maxAttempts} attempts.`);
}

export async function fetchUsage(key, fetchImpl = fetch) {
  const response = await fetchImpl(`${BASE_URL}/usage`, { headers: authHeaders(key), signal: AbortSignal.timeout(10_000) });
  if (response.status !== 200) throw new Error(`GET /usage answered HTTP ${response.status}`);
  return response.json();
}

export function requestsLeftToday(usage) {
  const today = usage.today ?? {};
  if (Object.hasOwn(today, 'remaining_day')) return today.remaining_day;
  const perDay = usage.limits?.per_day ?? null;
  if (perDay === null) return null;
  const served = (today.calls ?? 0) - (today.errors ?? 0);
  return Math.max(perDay - served, 0);
}

export function minuteHeadroom(headers) {
  const raw = headers instanceof Headers ? headers.get('x-ratelimit-remaining') : headers['x-ratelimit-remaining'];
  const value = String(raw ?? '').trim();
  return /^[0-9]+$/.test(value) ? Number(value) : null;
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
