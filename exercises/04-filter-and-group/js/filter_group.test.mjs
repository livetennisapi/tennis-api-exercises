// Offline tests for exercise 4, run against fixtures/matches_live.json.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const target = process.env.SOLUTION === '1' ? '../solutions/js/solution.mjs' : './starter.mjs';
const ex = await import(new URL(target, import.meta.url));

const LIVE = JSON.parse(readFileSync(new URL('../../../fixtures/matches_live.json', import.meta.url), 'utf8'))
  .response.body.data;
const ids = (matches) => matches.map((match) => match.id);

test('filter by draw', () => {
  assert.equal(ex.filterDraw(LIVE, 'singles').length, 19);
  assert.equal(ex.filterDraw(LIVE, 'doubles').length, 6);
});

test('a null draw is neither singles nor doubles', () => {
  const known = [...ids(ex.filterDraw(LIVE, 'singles')), ...ids(ex.filterDraw(LIVE, 'doubles'))];
  const unknown = ids(LIVE.filter((match) => match.draw === null));
  assert.equal(known.length + unknown.length, LIVE.length);
  assert.ok(unknown.every((id) => !known.includes(id)));
});

test('group keys follow the tour order', () => {
  assert.deepEqual(Object.keys(ex.groupByTour(LIVE)), ['atp', 'challenger', 'itf', 'other']);
});

test('group sizes add up', () => {
  const sizes = Object.fromEntries(Object.entries(ex.groupByTour(LIVE)).map(([tour, group]) => [tour, group.length]));
  assert.deepEqual(sizes, { atp: 2, challenger: 2, itf: 21, other: 4 });
});

test('groups are sorted by tournament, then id', () => {
  const groups = ex.groupByTour(LIVE);
  assert.deepEqual(ids(groups.atp), [208138, 207981]); // Brussels before Lyon
  assert.deepEqual(ids(groups.challenger), [208113, 207819]); // Florence before Lisbon
  assert.deepEqual(ids(groups.other), [209439, 209440, 209429, 209431]);
});

test('skips matches that are not live and leaves the input alone', () => {
  const slate = structuredClone(LIVE);
  slate[0].status = 'completed';
  const before = structuredClone(slate);
  const grouped = Object.values(ex.groupByTour(slate)).flat();
  assert.ok(!ids(grouped).includes(slate[0].id));
  assert.deepEqual(slate, before);
});

test('an unknown tour goes to other', () => {
  const match = { id: 1, status: 'live', tour: 'exhibition', tournament: 'Show' };
  assert.deepEqual(Object.keys(ex.groupByTour([match])), ['other']);
});

test('count by tournament', () => {
  const counts = ex.countByTournament(LIVE);
  assert.deepEqual(counts.slice(0, 2), [
    ['M15 Bol 2', 4],
    ['W15 Bol 2', 3],
  ]);
  assert.equal(counts.filter(([, count]) => count === 2).length, 4);
  assert.equal(counts.reduce((sum, [, count]) => sum + count, 0), LIVE.length);
  assert.equal(counts.length, new Set(LIVE.map((match) => match.tournament)).size);
});

test('count ties are alphabetical', () => {
  const counts = ex.countByTournament(LIVE);
  for (let i = 1; i < counts.length; i += 1) {
    const [prevName, prevCount] = counts[i - 1];
    const [name, count] = counts[i];
    assert.ok(prevCount > count || (prevCount === count && prevName.toLowerCase() <= name.toLowerCase()), `${prevName} / ${name}`);
  }
  assert.ok(counts.some(([name, count]) => name === 'W35 Loule' && count === 2));
});

test('an empty slate', () => {
  assert.deepEqual(ex.groupByTour([]), {});
  assert.deepEqual(ex.countByTournament([]), []);
});

test('itf group order', () => {
  assert.deepEqual(ids(ex.groupByTour(LIVE).itf), [
    209438, 209420, 209382, 209377, 209393, 209394, 209414, 208275, 208222, 208208, 208242,
    208245, 209381, 209391, 209413, 208278, 208279, 208268, 208191, 208211, 208219,
  ]);
});

test('the two-key sort ignores case', () => {
  // Built by hand: ids out of order inside one tournament, names in mixed case.
  const slate = [
    { id: 5, status: 'live', tour: 'atp', tournament: 'b open' },
    { id: 1, status: 'live', tour: 'atp', tournament: 'Zed Cup' },
    { id: 3, status: 'live', tour: 'atp', tournament: 'B Open' },
    { id: 9, status: 'live', tour: 'atp', tournament: 'a cup' },
  ];
  assert.deepEqual(ids(ex.groupByTour(slate).atp), [9, 3, 5, 1]);
  assert.deepEqual(
    ex.countByTournament([
      { id: 1, tournament: 'beta' },
      { id: 2, tournament: 'Alpha' },
      { id: 3, tournament: 'Gamma' },
    ]),
    [['Alpha', 1], ['beta', 1], ['Gamma', 1]],
  );
});

test('no function changes its input', () => {
  const slate = structuredClone(LIVE).reverse(); // unsorted on purpose
  const before = structuredClone(slate);
  ex.countByTournament(slate);
  ex.filterDraw(slate, 'singles');
  ex.groupByTour(slate);
  assert.deepEqual(slate, before);
});

test('every tour in order', () => {
  // Built by hand and shuffled: one or two live matches on every supported tour, plus one with no tour.
  const slate = [
    { id: 7, status: 'live', tour: 'juniors', tournament: 'Junior Open' },
    { id: 2, status: 'live', tour: 'wta', tournament: 'Wuhan' },
    { id: 5, status: 'live', tour: null, tournament: 'Exhibition' },
    { id: 4, status: 'live', tour: 'itf', tournament: 'M15 Bol 2' },
    { id: 1, status: 'live', tour: 'atp', tournament: 'Basel' },
    { id: 6, status: 'live', tour: 'wta', tournament: 'Beijing' },
    { id: 3, status: 'live', tour: 'challenger', tournament: 'Lisbon' },
  ];
  const groups = ex.groupByTour(slate);
  assert.deepEqual(Object.keys(groups), ['atp', 'wta', 'challenger', 'itf', 'juniors', 'other']);
  assert.deepEqual(Object.fromEntries(Object.entries(groups).map(([tour, group]) => [tour, ids(group)])), {
    atp: [1], wta: [6, 2], challenger: [3], itf: [4], juniors: [7], other: [5],
  });
});
