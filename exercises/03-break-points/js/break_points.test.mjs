// Offline tests for exercise 3.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const target = process.env.SOLUTION === '1' ? '../solutions/js/solution.mjs' : './starter.mjs';
const ex = await import(new URL(target, import.meta.url));

const LIVE = JSON.parse(readFileSync(new URL('../../../fixtures/matches_live.json', import.meta.url), 'utf8'))
  .response.body.data;

const score = (p1, p2, server, isTiebreak = false) => ({ points: [p1, p2], server, is_tiebreak: isTiebreak });

test('point values', () => {
  assert.deepEqual(['0', '15', '30', '40', 'AD'].map(ex.pointValue), [0, 1, 2, 3, 4]);
});

test('an unknown point value throws a RangeError', () => {
  assert.throws(() => ex.pointValue('45'), RangeError);
});

const cases = [
  [['0', '40'], 1, 3], // 0-40, player 2 receiving
  [['15', '40'], 1, 2],
  [['30', '40'], 1, 1],
  [['40', '0'], 2, 3], // same thing with player 1 receiving
  [['40', '30'], 2, 1],
  [['40', 'AD'], 1, 1], // advantage receiver
  [['AD', '40'], 2, 1],
  [['40', '40'], 1, 0], // deuce is not a break point
  [['AD', '40'], 1, 0], // advantage server
  [['40', '15'], 1, 0], // server holds game points
  [['0', '0'], 2, 0],
  [['30', '30'], 1, 0],
];
for (const [points, server, held] of cases) {
  test(`points ${points.join('-')} with player ${server} serving -> ${held}`, () => {
    assert.equal(ex.breakPointsHeld(score(...points, server)), held);
    assert.equal(ex.isBreakPoint(score(...points, server)), held > 0);
  });
}

test('a tiebreak has no break points', () => {
  assert.equal(ex.isBreakPoint(score('5', '6', 1, true)), false);
  assert.equal(ex.breakPointsHeld(score('0', '40', 1, true)), 0);
});

const missing = [null, {}, { points: ['0', '40'], server: null, is_tiebreak: false }, { points: [], server: 1 }];
missing.forEach((bad, i) => {
  test(`missing data case ${i + 1} is not a break point`, () => {
    assert.equal(ex.isBreakPoint(bad), false);
  });
});

test('a number is not a point value', () => {
  assert.throws(() => ex.pointValue(40), RangeError);
});

test('finds break points in the recorded slate', () => {
  // 209391: 15-40 with player 1 serving. 207819: 40-AD with player 1 serving.
  assert.deepEqual(ex.findBreakPoints(LIVE), [209391, 207819]);
});

test('skips matches that are not live', () => {
  const finished = { id: 1, status: 'completed', score: score('0', '40', 1) };
  const live = { id: 2, status: 'live', score: score('0', '40', 1) };
  const upcoming = { id: 3, status: 'upcoming', score: null };
  assert.deepEqual(ex.findBreakPoints([finished, live, upcoming]), [2]);
});
