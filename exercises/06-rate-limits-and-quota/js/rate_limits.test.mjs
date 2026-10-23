// Offline tests for exercise 6. Time is faked, so nothing really sleeps.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const target = process.env.SOLUTION === '1' ? '../solutions/js/solution.mjs' : './starter.mjs';
const ex = await import(new URL(target, import.meta.url));

function fixture(name) {
  const url = new URL(`../../../fixtures/${name}.json`, import.meta.url);
  return JSON.parse(readFileSync(url, 'utf8')).response;
}

function fakeTime() {
  const time = { now: 0, slept: [] };
  time.clock = () => time.now;
  time.sleep = async (seconds) => {
    time.slept.push(seconds);
    time.now += seconds;
  };
  return time;
}

function fakeFetch(...replies) {
  const calls = [];
  const fake = async (url, init = {}) => {
    calls.push({ url: String(url), headers: new Headers(init.headers ?? {}) });
    const reply = replies.length > 1 ? replies.shift() : replies[0];
    return new Response(JSON.stringify(reply.body), { status: reply.status, headers: reply.headers });
  };
  fake.calls = calls;
  return fake;
}

test('the limiter allows thirty calls, then waits', async () => {
  const time = fakeTime();
  const limiter = new ex.SlidingWindowLimiter(30, 60, time.clock, time.sleep);
  for (let i = 0; i < 30; i += 1) assert.equal(await limiter.acquire(), 0);
  assert.equal(await limiter.acquire(), 60);
  assert.deepEqual(time.slept, [60]);
});

test('the limiter with spread-out calls', async () => {
  const time = fakeTime();
  const limiter = new ex.SlidingWindowLimiter(30, 60, time.clock, time.sleep);
  for (let second = 0; second < 30; second += 1) {
    time.now = second;
    await limiter.acquire();
  }
  time.now = 30;
  // The oldest call was at t=0, so the 31st call may go at t=60.
  assert.equal(await limiter.acquire(), 30);
  assert.equal(time.now, 60);
});

test('the limiter never exceeds the window', async () => {
  const time = fakeTime();
  const limiter = new ex.SlidingWindowLimiter(30, 60, time.clock, time.sleep);
  const times = [];
  for (let i = 0; i < 100; i += 1) {
    await limiter.acquire();
    times.push(time.now);
  }
  times.forEach((start, i) => {
    assert.ok(times.slice(i).filter((t) => t < start + 60).length <= 30);
  });
});

const delays = [
  [0, '12', 12],
  [3, '12', 12],
  [0, '120', 60], // capped
  [0, '0', 0],
  [0, null, 1],
  [1, null, 2],
  [2, null, 4],
  [3, null, 8],
  [10, null, 60], // capped
  [2, 'soon', 4], // not a number: back off
  [2, '-5', 4], // negative: back off
];
for (const [attempt, header, expected] of delays) {
  test(`retryDelay(${attempt}, ${header}) is ${expected}`, () => {
    assert.equal(ex.retryDelay(attempt, header), expected);
  });
}

test('retry, then success', async () => {
  const time = fakeTime();
  const fetchImpl = fakeFetch(fixture('error_429_minute'), fixture('health'));
  const url = 'https://example.test/matches?status=live';
  const response = await ex.getWithRetry(url, { headers: { Authorization: 'Bearer abc123' } }, { fetchImpl, sleep: time.sleep });
  assert.equal(response.status, 200);
  assert.deepEqual(time.slept, [12]);
  assert.equal(fetchImpl.calls.length, 2);
  for (const call of fetchImpl.calls) {
    // the retry sends the same request again
    assert.equal(call.url, url);
    assert.equal(call.headers.get('authorization'), 'Bearer abc123');
  }
});

test('gives up after maxAttempts', async () => {
  const time = fakeTime();
  const fetchImpl = fakeFetch(fixture('error_429_minute'));
  await assert.rejects(
    ex.getWithRetry('https://example.test/x', {}, { fetchImpl, sleep: time.sleep, maxAttempts: 4 }),
    ex.RateLimited,
  );
  assert.equal(fetchImpl.calls.length, 4);
  assert.deepEqual(time.slept, [12, 12, 12]);
});

test('backs off when there is no Retry-After', async () => {
  const time = fakeTime();
  const reply = structuredClone(fixture('error_429_minute'));
  delete reply.headers['retry-after'];
  const fetchImpl = fakeFetch(reply);
  await assert.rejects(
    ex.getWithRetry('https://example.test/x', {}, { fetchImpl, sleep: time.sleep, maxAttempts: 4 }),
    ex.RateLimited,
  );
  assert.deepEqual(time.slept, [1, 2, 4]);
});

test('the daily quota is not retried', async () => {
  const time = fakeTime();
  const fetchImpl = fakeFetch(fixture('error_429_day'));
  await assert.rejects(
    ex.getWithRetry('https://example.test/x', {}, { fetchImpl, sleep: time.sleep }),
    (error) => error instanceof ex.QuotaExhausted && error.resetsAt === '2026-10-24T00:00:00Z',
  );
  assert.deepEqual(time.slept, []);
  assert.equal(fetchImpl.calls.length, 1);
});

test('other errors are returned, not retried', async () => {
  const fetchImpl = fakeFetch(fixture('error_404_player'));
  const response = await ex.getWithRetry('https://example.test/x', {}, { fetchImpl, sleep: fakeTime().sleep });
  assert.equal(response.status, 404);
});

test('fetchUsage', async () => {
  const fetchImpl = fakeFetch(fixture('usage_free'));
  const usage = await ex.fetchUsage('abc123', fetchImpl);
  assert.equal(usage.tier, 'free');
  assert.equal(fetchImpl.calls[0].url, `${ex.BASE_URL}/usage`);
  assert.equal(fetchImpl.calls[0].headers.get('authorization'), 'Bearer abc123');
});

test('requests left from remaining_day', () => {
  assert.equal(ex.requestsLeftToday(fixture('usage_free').body), 68);
});

test('requests left worked out', () => {
  const usage = structuredClone(fixture('usage_free').body);
  delete usage.today.remaining_day;
  assert.equal(ex.requestsLeftToday(usage), 100 - (37 - 5));
});

test('requests left is never negative', () => {
  assert.equal(ex.requestsLeftToday({ limits: { per_day: 100 }, today: { calls: 140, errors: 10 } }), 0);
});

test('no daily cap', () => {
  assert.equal(ex.requestsLeftToday({ limits: { per_day: null }, today: { calls: 5, errors: 0 } }), null);
  assert.equal(
    ex.requestsLeftToday({ limits: { per_day: null }, today: { calls: 5, errors: 0, remaining_day: null } }),
    null,
  );
});

test('minute headroom', () => {
  assert.equal(ex.minuteHeadroom(fixture('usage_free').headers), 29);
  assert.equal(ex.minuteHeadroom({}), null);
});

function windowOk(times, limit = 30, period = 60) {
  const sorted = [...times].sort((a, b) => a - b);
  return sorted.every((start, i) => sorted.slice(i).filter((t) => t < start + period).length <= limit);
}

test('the limiter is a sliding window, not a fixed one', async () => {
  // One call at t=0, 29 at t=59, then 30 more as fast as allowed.
  // A fixed window that resets at t=60 would let 59 calls through in about a second.
  const time = fakeTime();
  const limiter = new ex.SlidingWindowLimiter(30, 60, time.clock, time.sleep);
  const times = [];
  await limiter.acquire();
  times.push(time.now);
  time.now = 59;
  for (let i = 0; i < 29; i += 1) {
    await limiter.acquire();
    times.push(time.now);
  }
  for (let i = 0; i < 30; i += 1) {
    await limiter.acquire();
    times.push(time.now);
  }
  assert.ok(windowOk(times));
});

test('the limiter checks again after an early wake-up', async () => {
  const time = fakeTime();
  const earlySleep = async (seconds) => {
    // The first timer fires a millisecond early. Later ones are on time.
    time.now += time.slept.length === 0 ? seconds - 0.001 : seconds;
    time.slept.push(seconds);
  };
  const limiter = new ex.SlidingWindowLimiter(30, 60, time.clock, earlySleep);
  const times = [];
  for (let i = 0; i < 31; i += 1) {
    await limiter.acquire();
    times.push(time.now);
  }
  assert.ok(windowOk(times));
});

for (const header of ['0x1A', 'Infinity', 'NaN', '1e3', '']) {
  test(`retryDelay ignores ${JSON.stringify(header)}`, () => {
    assert.equal(ex.retryDelay(2, header), 4);
  });
}

test('retryDelay accepts decimals', () => {
  assert.equal(ex.retryDelay(0, '1.5'), 1.5);
});

test('getWithRetry respects its cap', async () => {
  const time = fakeTime();
  const fetchImpl = fakeFetch(fixture('error_429_minute'), fixture('health'));
  await ex.getWithRetry('https://example.test/x', {}, { fetchImpl, sleep: time.sleep, cap: 5 });
  assert.deepEqual(time.slept, [5]);
});

test('the daily quota is not retried even with a short Retry-After', async () => {
  const reply = structuredClone(fixture('error_429_day'));
  reply.headers['retry-after'] = '5';
  const time = fakeTime();
  await assert.rejects(
    ex.getWithRetry('https://example.test/x', {}, { fetchImpl: fakeFetch(reply), sleep: time.sleep }),
    ex.QuotaExhausted,
  );
  assert.deepEqual(time.slept, []);
});

test('the abuse block stops at once', async () => {
  const time = fakeTime();
  const fetchImpl = fakeFetch(fixture('error_429_abuse'));
  await assert.rejects(ex.getWithRetry('https://example.test/x', {}, { fetchImpl, sleep: time.sleep }), (error) => {
    assert.ok(error instanceof ex.ClientBlocked);
    assert.equal(error.retryAtEpoch, 1792851360);
    assert.ok(error.message.includes('24 hours'));
    return true;
  });
  assert.deepEqual(time.slept, []);
  assert.equal(fetchImpl.calls.length, 1);
});

test('fetchUsage rejects a bad status', async () => {
  await assert.rejects(ex.fetchUsage('bad', fakeFetch(fixture('error_401_bad_key'))), /401/);
});

test('requests left with a null count', () => {
  assert.equal(ex.requestsLeftToday({ limits: { per_day: 100 }, today: { calls: null, errors: null } }), 100);
});

for (const value of ['29abc', '', ' ', '-1', '2.5']) {
  test(`minuteHeadroom(${JSON.stringify(value)}) is null`, () => {
    assert.equal(ex.minuteHeadroom({ 'x-ratelimit-remaining': value }), null);
  });
}

for (const attempts of [1, 2, 5]) {
  test(`maxAttempts ${attempts} is respected`, async () => {
    const time = fakeTime();
    const fetchImpl = fakeFetch(fixture('error_429_minute'));
    await assert.rejects(
      ex.getWithRetry('https://example.test/x', {}, { fetchImpl, sleep: time.sleep, maxAttempts: attempts }),
      ex.RateLimited,
    );
    assert.equal(fetchImpl.calls.length, attempts);
    assert.equal(time.slept.length, attempts - 1);
  });
}
