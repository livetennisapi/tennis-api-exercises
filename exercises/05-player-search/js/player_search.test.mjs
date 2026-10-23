// Offline tests for exercise 5. They replay recorded responses from fixtures/.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const target = process.env.SOLUTION === '1' ? '../solutions/js/solution.mjs' : './starter.mjs';
const ex = await import(new URL(target, import.meta.url));

function fixture(name) {
  const url = new URL(`../../../fixtures/${name}.json`, import.meta.url);
  return JSON.parse(readFileSync(url, 'utf8')).response;
}
const players = (name) => fixture(name).body.data;

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

test('the search URL uses the search parameter', () => {
  const url = ex.searchUrl('Jannik Sinner');
  assert.ok(url.startsWith(`${ex.BASE_URL}/players?`));
  assert.ok(url.includes('search=Jannik%20Sinner'));
  assert.ok(!url.includes('name='));
  assert.ok(url.includes('limit=10'));
});

test('searchPlayers returns players and total', async () => {
  const fetchImpl = fakeFetch(fixture('players_search_williams'));
  const result = await ex.searchPlayers('williams', 'abc123', fetchImpl);
  assert.equal(result.players.length, 10);
  assert.equal(result.total, 64);
  assert.equal(fetchImpl.calls[0].headers.get('authorization'), 'Bearer abc123');
});

test('a blank search makes no request', async () => {
  const fetchImpl = fakeFetch(fixture('players_search_none'));
  await assert.rejects(ex.searchPlayers('   ', 'abc123', fetchImpl), RangeError);
  assert.equal(fetchImpl.calls.length, 0);
});

test('zero results', () => {
  assert.throws(() => ex.pickPlayer(players('players_search_none'), 0), ex.PlayerNotFound);
});

test('one result', () => {
  assert.equal(ex.pickPlayer(players('players_search_one'), 1).id, 34);
});

test('many results drop doubles teams', () => {
  assert.throws(
    () => ex.pickPlayer(players('players_search_sinner'), 10),
    (error) => error instanceof ex.AmbiguousPlayer && error.candidates.join('|') === 'Jannik Sinner|Sinner',
  );
});

test('many results including teams', () => {
  assert.throws(
    () => ex.pickPlayer(players('players_search_sinner'), 10, false),
    (error) => error instanceof ex.AmbiguousPlayer && error.candidates.length === 5 && error.candidates[0] === 'Jannik Sinner',
  );
});

test('the ambiguous message names the total', () => {
  assert.throws(
    () => ex.pickPlayer(players('players_search_williams'), 64),
    (error) => error instanceof ex.AmbiguousPlayer && error.message.includes('64') && error.candidates[0] === 'Venus Williams',
  );
});

test('player detail', async () => {
  const fetchImpl = fakeFetch(fixture('player_34'));
  const player = await ex.getPlayer(34, 'abc123', fetchImpl);
  assert.equal(player.name, 'Jannik Sinner');
  assert.equal(fetchImpl.calls[0].url, `${ex.BASE_URL}/players/34`);
  assert.equal(fetchImpl.calls[0].headers.get('authorization'), 'Bearer abc123');
});

test('player 404', async () => {
  const fetchImpl = fakeFetch(fixture('error_404_player'));
  await assert.rejects(ex.getPlayer(999999999, 'abc123', fetchImpl), ex.PlayerNotFound);
});

test('describe a player', () => {
  assert.equal(ex.describePlayer(fixture('player_34').body), 'Jannik Sinner (ITA), ATP rank 1, 10950 points');
});

test('describe an unranked player', () => {
  const player = { name: 'Sinner / Sonego', country: null, ranking: null, tour: 'atp' };
  assert.equal(ex.describePlayer(player), 'Sinner / Sonego, unranked');
});

test('describe a player without a tour', () => {
  const player = { name: 'A Player', country: 'fra', ranking: 250, ranking_points: null, tour: null };
  assert.equal(ex.describePlayer(player), 'A Player (FRA), rank 250');
});

test('findPlayer end to end', async () => {
  const fetchImpl = fakeFetch(fixture('players_search_one'), fixture('player_34'));
  const player = await ex.findPlayer('Jannik Sinner', 'abc123', fetchImpl);
  assert.equal(player.id, 34);
  assert.deepEqual(
    fetchImpl.calls.map((call) => call.url),
    [ex.searchUrl('Jannik Sinner'), `${ex.BASE_URL}/players/34`],
  );
  assert.deepEqual(fetchImpl.calls.map((call) => call.headers.get('authorization')), ['Bearer abc123', 'Bearer abc123']);
});

for (const [name, encoded] of [
  ['Gaël Monfils', 'search=Ga%C3%ABl%20Monfils'],
  ['Tom & Jerry', 'search=Tom%20%26%20Jerry'],
]) {
  test(`the search URL encodes ${name}`, () => {
    assert.ok(ex.searchUrl(name).includes(encoded));
  });
}

test('findPlayer never guesses', async () => {
  const fetchImpl = fakeFetch(fixture('players_search_sinner'));
  await assert.rejects(ex.findPlayer('sinner', 'abc123', fetchImpl), ex.AmbiguousPlayer);
  assert.equal(fetchImpl.calls.length, 1);
});

test('searchPlayers rejects a bad status', async () => {
  await assert.rejects(ex.searchPlayers('sinner', 'bad', fakeFetch(fixture('error_401_bad_key'))), /401/);
});

test('a 401 from getPlayer is not a missing player', async () => {
  await assert.rejects(ex.getPlayer(34, 'bad', fakeFetch(fixture('error_401_bad_key'))), (error) => {
    assert.ok(!(error instanceof ex.PlayerNotFound));
    assert.match(error.message, /401/);
    return true;
  });
});

function oneSinglesNineTeams() {
  const rows = players('players_search_sinner');
  const teams = rows.filter((p) => p.is_doubles_team);
  return [rows[0], ...teams, { ...teams[0], id: 99999, name: 'Extra / Sinner' }];
}

test('an incomplete page is not a single match', () => {
  const rows = oneSinglesNineTeams();
  assert.equal(rows.length, 10);
  assert.throws(() => ex.pickPlayer(rows, 11), (error) => error instanceof ex.AmbiguousPlayer && error.message.includes('11'));
});

test('an incomplete page of teams is not "not found"', () => {
  const teams = oneSinglesNineTeams().filter((p) => p.is_doubles_team);
  assert.throws(() => ex.pickPlayer(teams, 20), ex.AmbiguousPlayer);
});

test('a complete page of teams is not found', () => {
  const teams = oneSinglesNineTeams().filter((p) => p.is_doubles_team);
  assert.throws(() => ex.pickPlayer(teams, teams.length), ex.PlayerNotFound);
});

test('a retained rank is not current', () => {
  const cooper = players('players_search_williams').find((p) => p.name === 'Cooper Williams');
  assert.equal(cooper.ranking_status, 'unranked');
  assert.equal(cooper.ranking, 604);
  assert.equal(ex.describePlayer(cooper), 'Cooper Williams (USA), unranked');
});
