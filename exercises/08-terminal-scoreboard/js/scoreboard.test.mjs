// Offline tests for exercise 8. Time is faked, so a 10-hour session runs instantly.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const target = process.env.SOLUTION === '1' ? '../solutions/js/solution.mjs' : './starter.mjs';
const ex = await import(new URL(target, import.meta.url));

function fixture(name) {
  const url = new URL(`../../../fixtures/${name}.json`, import.meta.url);
  return JSON.parse(readFileSync(url, 'utf8')).response;
}
const LIVE = fixture('matches_live').body.data;

function fakeTime() {
  const time = { now: 1000, slept: [] };
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

// Part 1: the arithmetic

for (const [minutes, expected] of [
  [180, 120], // 10800 s / 90 requests
  [120, 80], // 7200 / 90
  [10, 7], // 600 / 90 = 6.67, rounded up
  [600, 400], // 36000 / 90
  [1, 3], // under a second, but 30 a minute means 2 s, plus 1 s to spare
]) {
  test(`a ${minutes}-minute session polls every ${expected} s`, () => {
    assert.equal(ex.pollIntervalSeconds(minutes), expected);
  });
}

test('two requests per poll', () => {
  // 90 usable / 2 per poll = 45 polls; 5400 s / 45 = 120 s
  assert.equal(ex.pollIntervalSeconds(90, { requestsPerPoll: 2 }), 120);
});

for (const minutes of [5, 10, 37, 180, 240, 1440]) {
  test(`a ${minutes}-minute session stays inside the budget`, () => {
    const interval = ex.pollIntervalSeconds(minutes);
    assert.ok(ex.requestsNeeded(minutes, interval) <= 90);
  });
}

test('requests needed', () => {
  assert.equal(ex.requestsNeeded(180, 120), 90);
  assert.equal(ex.requestsNeeded(10, 7), Math.ceil(600 / 7));
});

for (const [label, call] of [
  ['0 minutes', () => ex.pollIntervalSeconds(0)],
  ['-5 minutes', () => ex.pollIntervalSeconds(-5)],
  ['no usable budget', () => ex.pollIntervalSeconds(60, { dailyBudget: 10, reserve: 10 })],
]) {
  test(`bad input throws a RangeError: ${label}`, () => {
    assert.throws(call, RangeError);
  });
}

test('explainInterval shows the working', () => {
  const text = ex.explainInterval(180);
  for (const number of ['100', '10', '90', '10800', '120']) {
    assert.match(text, new RegExp(`(?<![0-9.])${number}(?![0-9])`), number);
  }
});

// Part 2: the board

test('board header and tour order', () => {
  const lines = ex.renderBoard(LIVE).split('\n');
  assert.equal(lines[0], 'Live tennis: 29 matches');
  assert.deepEqual(lines.filter((line) => !line.startsWith(' ')).slice(1), ['ATP', 'CHALLENGER', 'ITF', 'OTHER']);
});

test('board lines', () => {
  const board = ex.renderBoard(LIVE);
  const lines = board.split('\n');
  assert.ok(lines.includes('  Brussels | Jiri Lehecka v Tallon Griekspoor | 0-1, 30-30, Jiri Lehecka serving'));
  assert.ok(board.includes('Lyon (France) | Tommy Paul v Corentin Moutet | 6-4 3-6 2-0, 0-15, Corentin Moutet serving'));
  assert.ok(board.indexOf('Brussels') < board.indexOf('Lyon (France)'));
  assert.equal(lines.filter((line) => line.startsWith('  ')).length, 29);
});

test('board with one match and with none', () => {
  assert.equal(ex.renderBoard([]), 'No live matches right now.');
  assert.equal(ex.renderBoard(LIVE.slice(0, 1)).split('\n')[0], 'Live tennis: 1 match');
});

// Part 3: the loop

test('a ten-minute session', async () => {
  const time = fakeTime();
  const fetchImpl = fakeFetch(fixture('matches_live'));
  const boards = [];
  const calls = await ex.runScoreboard('abc123', 10, { fetchImpl, sleep: time.sleep, clock: time.clock, out: (b) => boards.push(b) });
  assert.equal(calls, Math.ceil(600 / 7));
  assert.equal(fetchImpl.calls.length, calls);
  assert.deepEqual([...new Set(time.slept)], [7]);
  assert.ok(boards.every((board) => board.startsWith('Live tennis: 29 matches')));
  assert.equal(fetchImpl.calls[0].url, ex.LIVE_URL);
  assert.equal(fetchImpl.calls[0].headers.get('authorization'), 'Bearer abc123');
});

test('a long session never exceeds the budget', async () => {
  const time = fakeTime();
  const fetchImpl = fakeFetch(fixture('matches_live'));
  const calls = await ex.runScoreboard('abc123', 600, { fetchImpl, sleep: time.sleep, clock: time.clock, out: () => {} });
  assert.ok(calls <= 90);
  assert.ok(time.now - 1000 <= 600 * 60);
});

test('a rate-limited poll waits longer', async () => {
  const time = fakeTime();
  const minute = structuredClone(fixture('error_429_minute'));
  minute.headers['retry-after'] = '45';
  const fetchImpl = fakeFetch(fixture('matches_live'), minute, fixture('matches_live'));
  const messages = [];
  await ex.runScoreboard('abc123', 3, { fetchImpl, sleep: time.sleep, clock: time.clock, out: (m) => messages.push(m) });
  assert.equal(time.slept[0], 3);
  assert.equal(time.slept[1], 45);
  assert.ok(messages.some((m) => m.toLowerCase().includes('rate')));
});

test('the daily quota stops the loop', async () => {
  const time = fakeTime();
  const fetchImpl = fakeFetch(fixture('matches_live'), fixture('error_429_day'));
  const calls = await ex.runScoreboard('abc123', 60, { fetchImpl, sleep: time.sleep, clock: time.clock, out: () => {} });
  assert.equal(calls, 2);
});

test('a bad key stops the loop', async () => {
  const time = fakeTime();
  const fetchImpl = fakeFetch(fixture('error_401_bad_key'));
  const messages = [];
  const calls = await ex.runScoreboard('bad', 60, { fetchImpl, sleep: time.sleep, clock: time.clock, out: (m) => messages.push(m) });
  assert.equal(calls, 1);
  assert.deepEqual(time.slept, []);
  assert.ok(messages[0].includes('401'));
});

// Rules from the rubric and the common mistakes in TEACHERS.md

test('explainInterval for ten minutes', () => {
  const text = ex.explainInterval(10);
  for (const number of ['100', '10', '90', '600', '7', '86']) {
    assert.match(text, new RegExp(`(?<![0-9.])${number}(?![0-9])`), number);
  }
});

test('a ten-minute session sleeps only between polls', async () => {
  // 86 polls need 85 sleeps of 7 s. Sleeping once more before checking the clock overshoots.
  const time = fakeTime();
  await ex.runScoreboard('abc123', 10, { fetchImpl: fakeFetch(fixture('matches_live')), sleep: time.sleep, clock: time.clock, out: () => {} });
  assert.equal(time.slept.length, 85);
  assert.equal(time.slept.reduce((a, b) => a + b, 0), 595);
});

test('a three-hour session uses exactly the budget', async () => {
  const time = fakeTime();
  const calls = await ex.runScoreboard('abc123', 180, { fetchImpl: fakeFetch(fixture('matches_live')), sleep: time.sleep, clock: time.clock, out: () => {} });
  assert.equal(calls, 90);
  assert.equal(time.slept.length, 89);
});

test('a short Retry-After still waits the interval', async () => {
  const time = fakeTime();
  const minute = structuredClone(fixture('error_429_minute'));
  minute.headers['retry-after'] = '1';
  const fetchImpl = fakeFetch(fixture('matches_live'), minute, fixture('matches_live'));
  await ex.runScoreboard('abc123', 10, { fetchImpl, sleep: time.sleep, clock: time.clock, out: () => {} });
  assert.equal(time.slept[1], 7);
});

test('a frozen clock still stops at the budget', async () => {
  const inner = fakeFetch(fixture('matches_live'));
  const fetchImpl = async (url, init) => {
    if (inner.calls.length >= 100) throw new Error('the loop does not stop at the request budget');
    return inner(url, init);
  };
  fetchImpl.calls = inner.calls;
  const made = await ex.runScoreboard('abc123', 180, { fetchImpl, sleep: async () => {}, clock: () => 0, out: () => {} });
  assert.equal(made, 90);
  assert.equal(fetchImpl.calls.length, 90);
});

test('a 403 stops the loop', async () => {
  const time = fakeTime();
  const calls = await ex.runScoreboard('abc123', 60, { fetchImpl: fakeFetch(fixture('error_403_upgrade_required')), sleep: time.sleep, clock: time.clock, out: () => {} });
  assert.equal(calls, 1);
});

test('a server error does not stop the loop', async () => {
  const time = fakeTime();
  const fetchImpl = fakeFetch({ status: 500, headers: {}, body: { error: 'internal' } }, fixture('matches_live'));
  const messages = [];
  const calls = await ex.runScoreboard('abc123', 10, { fetchImpl, sleep: time.sleep, clock: time.clock, out: (m) => messages.push(m) });
  assert.ok(calls > 2);
  assert.ok(messages[0].includes('500'));
  assert.ok(messages[1].startsWith('Live tennis: 29 matches'));
});

test('the abuse block stops the loop', async () => {
  const time = fakeTime();
  const abuse = structuredClone(fixture('error_429_abuse'));
  abuse.headers['retry-after'] = '5'; // even a short wait must not tempt the loop to carry on
  const fetchImpl = fakeFetch(fixture('matches_live'), abuse, fixture('matches_live'));
  const messages = [];
  const calls = await ex.runScoreboard('abc123', 60, { fetchImpl, sleep: time.sleep, clock: time.clock, out: (m) => messages.push(m) });
  assert.equal(calls, 2);
  assert.ok(messages.at(-1).toLowerCase().includes('blocked'));
});

test('the board ignores matches that are not live', () => {
  const finished = { ...LIVE[0], status: 'completed' };
  assert.equal(ex.renderBoard([...LIVE, finished]).split('\n')[0], 'Live tennis: 29 matches');
});

test('the board with a null tournament and a level match tiebreak', () => {
  const match = {
    id: 1, status: 'live', tour: 'atp', tournament: null,
    players: { p1: { name: 'A' }, p2: { name: 'B' } },
    score: { sets: [1, 1], games: [[6, 4, 5], [4, 6, 5]], points: ['0', '0'], server: 1, is_tiebreak: true },
  };
  assert.ok(ex.renderBoard([match]).split('\n').includes('  Unknown tournament | A v B | 6-4 4-6 [5-5], A serving'));
});

test('no poll after a late wake-up', async () => {
  const time = fakeTime();
  const lateSleep = async (seconds) => {
    time.slept.push(seconds);
    time.now += 70; // the machine slept through the rest of the session
  };
  const calls = await ex.runScoreboard('abc123', 1, { fetchImpl: fakeFetch(fixture('matches_live')), sleep: lateSleep, clock: time.clock, out: () => {} });
  assert.equal(calls, 1);
});

test('the caller budget and reserve are used', async () => {
  assert.equal(ex.pollIntervalSeconds(60, { dailyBudget: 13, reserve: 10 }), 1200);
  const inner = fakeFetch(fixture('matches_live'));
  const fetchImpl = async (url, init) => {
    if (inner.calls.length >= 10) throw new Error('the loop ignores the budget it was given');
    return inner(url, init);
  };
  const made = await ex.runScoreboard('abc123', 60, {
    fetchImpl, sleep: async () => {}, clock: () => 0, out: () => {}, dailyBudget: 13, reserve: 10,
  });
  assert.equal(made, 3);
  assert.equal(inner.calls.length, 3);
});

test('a non-default reserve is used', async () => {
  assert.equal(ex.pollIntervalSeconds(60, { dailyBudget: 13, reserve: 12 }), 3600);
  const inner = fakeFetch(fixture('matches_live'));
  const fetchImpl = async (url, init) => {
    if (inner.calls.length >= 10) throw new Error('the loop ignores the reserve it was given');
    return inner(url, init);
  };
  const made = await ex.runScoreboard('abc123', 60, {
    fetchImpl, sleep: async () => {}, clock: () => 0, out: () => {}, dailyBudget: 13, reserve: 12,
  });
  assert.equal(made, 1);
  assert.equal(inner.calls.length, 1);
});
