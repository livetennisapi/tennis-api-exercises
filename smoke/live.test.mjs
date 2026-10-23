// Optional live smoke test against the real API.
// Skipped unless LIVE=1 and LIVETENNISAPI_KEY are set. It runs the reference
// solutions, or the starters in a copy with the solutions removed. It spends
// about three requests of your daily quota (GET /usage and refused calls are
// free). Run it with: LIVE=1 node scripts/run-js-tests.mjs --smoke

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';

const KEY = (process.env.LIVETENNISAPI_KEY ?? '').trim();
const skip = process.env.LIVE !== '1' || !KEY ? 'live smoke test: set LIVE=1 and LIVETENNISAPI_KEY to run it' : false;
function solution(exercise) {
  const reference = new URL(`../exercises/${exercise}/solutions/js/solution.mjs`, import.meta.url);
  // In a class copy the solutions are gone, so test the student's own code.
  return import(existsSync(reference) ? reference : new URL(`../exercises/${exercise}/js/starter.mjs`, import.meta.url));
}

test('health and live count', { skip }, async () => {
  const first = await solution('01-first-request');
  assert.equal(await first.checkHealth(), true);
  assert.ok((await first.countLiveMatches(KEY)) >= 0);
});

test('player search', { skip }, async () => {
  const search = await solution('05-player-search');
  const player = await search.findPlayer('Jannik Sinner', KEY);
  assert.ok(player.name.includes('Sinner'));
});

test('usage and plan gating', { skip }, async (t) => {
  const quota = await solution('06-rate-limits-and-quota');
  const errors = await solution('07-errors');
  const usage = await quota.fetchUsage(KEY);
  const left = quota.requestsLeftToday(usage);
  assert.ok(left === null || left >= 0);
  if (usage.tier !== 'free') {
    t.skip('this key is above FREE, so the paid endpoint will not answer 403');
    return;
  }
  await assert.rejects(errors.requestJson('/rankings?system=atp', KEY), (error) => {
    assert.equal(error.status, 403);
    assert.equal(error.code, 'upgrade_required');
    return true;
  });
});
