// Exercise 7 solution: turn API errors into clear messages.

import { pathToFileURL } from 'node:url';

export const BASE_URL = 'https://api.livetennisapi.com/api/public/v1';
export const PRICING_URL = 'https://livetennisapi.com/pricing';
export const FREE_PLAN =
  'live and upcoming matches, current scores, players, fixtures, tournaments and usage stats';

export const authHeaders = (key) => ({ Authorization: `Bearer ${key}`, Accept: 'application/json' });

export class ApiError extends Error {
  constructor(status, code, message) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export function explainError(status, body, path) {
  const safe = body && typeof body === 'object' ? body : {};
  const code = safe.error;
  if (status === 401) {
    return (
      'HTTP 401 unauthorized: the API did not accept your key. ' +
      'Check that LIVETENNISAPI_KEY holds the whole key with no extra spaces.'
    );
  }
  if (status === 403 && code === 'upgrade_required') {
    let message =
      `HTTP 403 upgrade_required: ${path} is not part of your plan. ` +
      `The FREE plan covers ${FREE_PLAN}. Plans are listed at ${PRICING_URL}.`;
    if (safe.free_history_taste === 'used') message += ' Your free history calls for this month are used up.';
    return message;
  }
  if (status === 404) {
    let message = `HTTP 404 not_found: nothing exists at ${path}. Check the id.`;
    if (safe.see) message += ` That id belongs to the results archive: ${safe.see}.`;
    return message;
  }
  if (status === 429) {
    if (code === 'abuse_throttled') {
      return (
        'HTTP 429 abuse_throttled: this key is blocked for 24 hours for calling far past its limits. ' +
        'Fix the loop before you try again.'
      );
    }
    if (safe.scope === 'day') {
      return `HTTP 429 rate_limited: the daily quota is used up. It resets at ${safe.resets_at}.`;
    }
    return 'HTTP 429 rate_limited: too many requests this minute. Wait for the Retry-After seconds, then slow down.';
  }
  let message = `HTTP ${status} ${code || 'error'}: ${safe.detail || 'the API did not say why'}`;
  if (Array.isArray(safe.allowed) && safe.allowed.length) message += ` Allowed values: ${safe.allowed.join(', ')}.`;
  return message;
}

export async function requestJson(path, key, fetchImpl = fetch) {
  const response = await fetchImpl(BASE_URL + path, { headers: authHeaders(key), signal: AbortSignal.timeout(10_000) });
  let body = {};
  try {
    body = await response.json();
  } catch {
    body = {};
  }
  if (response.status === 200) return body;
  const code = body && typeof body === 'object' ? (body.error ?? null) : null;
  throw new ApiError(response.status, code, explainError(response.status, body, path));
}

export const DEMO_CALLS = [
  ['a bad key', '/matches?status=live&limit=1', 'not-a-real-key'],
  ['a paid endpoint', '/rankings?system=atp', null],
  ['an unknown id', '/players/999999999', null],
];

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
