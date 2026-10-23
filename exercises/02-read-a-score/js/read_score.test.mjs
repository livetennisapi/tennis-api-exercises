// Offline tests for exercise 2.
// Some cases come from fixtures/matches_live.json. The edge cases are built
// by hand, because a recording only holds the states live when it was made.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const target = process.env.SOLUTION === '1' ? '../solutions/js/solution.mjs' : './starter.mjs';
const ex = await import(new URL(target, import.meta.url));

const LIVE = JSON.parse(readFileSync(new URL('../../../fixtures/matches_live.json', import.meta.url), 'utf8'))
  .response.body.data;
const liveMatch = (id) => LIVE.find((match) => match.id === id);

function makeMatch(games, { points = ['0', '0'], server = 1, isTiebreak = false, sets = [0, 0], status = 'live' } = {}) {
  return {
    status,
    players: { p1: { name: 'Jannik Sinner' }, p2: { name: 'Carlos Alcaraz' } },
    score: { sets, games, points, server, is_tiebreak: isTiebreak },
  };
}

test('set scores are player-major', () => {
  assert.deepEqual(ex.setScores([[6, 3], [4, 4]]), ['6-4', '3-4']);
  assert.deepEqual(ex.setScores([[6, 3, 2], [4, 6, 1]]), ['6-4', '3-6', '2-1']);
});

test('set scores with a match tiebreak', () => {
  assert.deepEqual(ex.setScores([[6, 4, 10], [4, 6, 5]], true), ['6-4', '4-6', '[10-5]']);
});

test('the example from the brief', () => {
  const match = makeMatch([[6, 3], [4, 4]], { points: ['30', '15'], sets: [1, 0] });
  assert.equal(ex.formatScore(match), '6-4 3-4, 30-15, Jannik Sinner serving');
});

const recorded = [
  [207981, '6-4 3-6 2-0, 0-15, Corentin Moutet serving'],
  [207819, '1-1, advantage Elmer Moller, Henrique Rocha serving'],
  [208138, '0-1, 30-30, Jiri Lehecka serving'],
  [208279, '0-0, 30-30, Ana Sofia Sanchez serving'],
];
for (const [id, expected] of recorded) {
  test(`recorded live match ${id}`, () => {
    assert.equal(ex.formatScore(liveMatch(id)), expected);
  });
}

test('every recorded match formats', () => {
  for (const match of LIVE) {
    const line = ex.formatScore(match);
    assert.equal(typeof line, 'string');
    assert.ok(line.length > 0);
  }
});

test('not started', () => {
  const match = makeMatch([[0], [0]]);
  match.score = null;
  assert.equal(ex.formatScore(match), 'not started');
});

test('withheld score', () => {
  assert.equal(ex.formatScore(makeMatch(null)), 'score unavailable');
});

test('no games yet', () => {
  assert.equal(ex.formatScore(makeMatch([[], []])), '0-0, 0-0, Jannik Sinner serving');
});

test('deuce', () => {
  const match = makeMatch([[2], [2]], { points: ['40', '40'], server: 2 });
  assert.equal(ex.formatScore(match), '2-2, deuce, Carlos Alcaraz serving');
});

test('advantage player one', () => {
  const match = makeMatch([[2], [2]], { points: ['AD', '40'], server: 2 });
  assert.equal(ex.formatScore(match), '2-2, advantage Jannik Sinner, Carlos Alcaraz serving');
});

test('tiebreak points', () => {
  const match = makeMatch([[6, 6], [4, 6]], { points: ['5', '3'], isTiebreak: true, sets: [1, 0] });
  assert.equal(ex.formatScore(match), '6-4 6-6, tiebreak 5-3, Jannik Sinner serving');
});

test('match tiebreak', () => {
  const match = makeMatch([[6, 4, 10], [4, 6, 5]], { server: 2, isTiebreak: true, sets: [1, 1] });
  assert.equal(ex.isMatchTiebreak(match.score), true);
  assert.equal(ex.formatScore(match), '6-4 4-6 [10-5], Carlos Alcaraz serving');
});

test('an ordinary tiebreak is not a match tiebreak', () => {
  const match = makeMatch([[6, 6], [4, 6]], { points: ['5', '3'], isTiebreak: true });
  assert.equal(ex.isMatchTiebreak(match.score), false);
});

test('finished match', () => {
  const match = makeMatch([[6, 6], [4, 3]], { sets: [2, 0], status: 'completed', server: null });
  assert.equal(ex.formatScore(match), '6-4 6-3, Jannik Sinner won');
});

test('finished match, player two wins', () => {
  const match = makeMatch([[6, 3, 4], [4, 6, 6]], { sets: [1, 2], status: 'completed', server: null });
  assert.equal(ex.formatScore(match), '6-4 3-6 4-6, Carlos Alcaraz won');
});

test('no server known', () => {
  const match = makeMatch([[1], [0]], { points: ['15', '0'], server: null });
  assert.equal(ex.formatScore(match), '1-0, 15-0');
});

for (const level of [0, 5]) {
  test(`match tiebreak at ${level}-${level}`, () => {
    const match = makeMatch([[6, 4, level], [4, 6, level]], { server: 1, isTiebreak: true, sets: [1, 1] });
    assert.equal(ex.isMatchTiebreak(match.score), true);
    assert.equal(ex.formatScore(match), `6-4 4-6 [${level}-${level}], Jannik Sinner serving`);
  });
}

test('a tiebreak in a full deciding set', () => {
  // A third set played to 6-6 then a normal tiebreak. Three sets alone do not mean a match tiebreak.
  const match = makeMatch([[6, 3, 6], [4, 6, 6]], { points: ['5', '3'], isTiebreak: true, sets: [1, 1] });
  assert.equal(ex.isMatchTiebreak(match.score), false);
  assert.equal(ex.formatScore(match), '6-4 3-6 6-6, tiebreak 5-3, Jannik Sinner serving');
});

test('the winner comes from sets, not the last set', () => {
  // Player 1 won the only completed set. The last set's games favour player 2.
  const match = makeMatch([[6, 2], [4, 5]], { sets: [1, 0], status: 'completed', server: null });
  assert.equal(ex.formatScore(match), '6-4 2-5, Jannik Sinner won');
});

test('set scores stop at the shorter array', () => {
  assert.deepEqual(ex.setScores([[6, 3], [4]]), ['6-4']);
});

for (const outcome of ['unresolved', 'abandoned']) {
  test(`${outcome} is not a win`, () => {
    const match = { ...makeMatch([[6], [4]], { sets: [1, 0], status: 'completed', server: null }), outcome, winner: null };
    assert.equal(ex.formatScore(match), '6-4, no result');
  });
}

test('the winner field beats sets', () => {
  // A retirement: player 1 led on sets, retired, and lost.
  const match = { ...makeMatch([[6, 2], [4, 3]], { sets: [1, 0], status: 'completed', server: null }), outcome: 'retired', winner: 2 };
  assert.equal(ex.formatScore(match), '6-4 2-3, Carlos Alcaraz won');
});

test('bracket after pairing unequal arrays', () => {
  assert.deepEqual(ex.setScores([[6, 3], [4]], true), ['[6-4]']);
});

for (const points of ['absent', null, [], ['15'], ['15', '30', '40']]) {
  test(`missing or malformed points: ${JSON.stringify(points)}`, () => {
    const match = makeMatch([[2], [2]]);
    if (points === 'absent') delete match.score.points;
    else match.score.points = points;
    assert.equal(ex.formatScore(match), '2-2, Jannik Sinner serving');
  });
}

function noScore({ status = 'completed', outcome = null, winner = null } = {}) {
  return { ...makeMatch(null), score: null, status, outcome, winner };
}

test('a walkover without a score row', () => {
  assert.equal(ex.formatScore(noScore({ outcome: 'walkover', winner: 1 })), 'Jannik Sinner won by walkover');
});

for (const [outcome, winner, expected] of [
  ['unresolved', null, 'no result'],
  ['completed', 2, 'Carlos Alcaraz won'],
  [null, null, 'final'],
]) {
  test(`completed without a score row: ${outcome}, ${winner}`, () => {
    assert.equal(ex.formatScore(noScore({ outcome, winner })), expected);
  });
}

test('upcoming without a score row is not started', () => {
  assert.equal(ex.formatScore(noScore({ status: 'upcoming' })), 'not started');
});

test('level sets and no winner is final', () => {
  const match = { ...makeMatch([[6, 4], [4, 6]], { sets: [1, 1], status: 'completed', server: null }), winner: null };
  assert.equal(ex.formatScore(match), '6-4 4-6, final');
});
