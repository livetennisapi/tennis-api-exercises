// Offline tests for exercise 7. They replay recorded and constructed errors from fixtures/.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const target = process.env.SOLUTION === '1' ? '../solutions/js/solution.mjs' : './starter.mjs';
const ex = await import(new URL(target, import.meta.url));

function fixture(name) {
  const url = new URL(`../../../fixtures/${name}.json`, import.meta.url);
  return JSON.parse(readFileSync(url, 'utf8')).response;
}

function fakeFetch(...replies) {
  const calls = [];
  const fake = async (url, init = {}) => {
    calls.push({ url: String(url), headers: new Headers(init.headers ?? {}) });
    const reply = replies.length > 1 ? replies.shift() : replies[0];
    const text = typeof reply.body === 'string' ? reply.body : JSON.stringify(reply.body);
    return new Response(text, { status: reply.status, headers: reply.headers });
  };
  fake.calls = calls;
  return fake;
}

test('401 message', () => {
  const message = ex.explainError(401, fixture('error_401_bad_key').body, '/matches?status=live');
  assert.ok(message.startsWith('HTTP 401'));
  assert.ok(message.includes('LIVETENNISAPI_KEY'));
});

test('403 message explains plan gating', () => {
  const message = ex.explainError(403, fixture('error_403_upgrade_required').body, '/rankings?system=atp');
  assert.ok(message.startsWith('HTTP 403'));
  for (const part of ['upgrade_required', '/rankings?system=atp', 'FREE', ex.PRICING_URL]) {
    assert.ok(message.includes(part), `missing ${part}`);
  }
});

test('403 when the free history calls are used', () => {
  const message = ex.explainError(403, { error: 'upgrade_required', free_history_taste: 'used' }, '/history/matches');
  assert.ok(message.toLowerCase().includes('history'));
  assert.notEqual(message, ex.explainError(403, { error: 'upgrade_required' }, '/history/matches'));
});

test('404 message', () => {
  const message = ex.explainError(404, fixture('error_404_player').body, '/players/999999999');
  assert.ok(message.startsWith('HTTP 404'));
  assert.ok(message.includes('/players/999999999'));
});

test('404 with an archive pointer', () => {
  const body = { error: 'not_found', detail: 'corpus id', see: '/api/public/v1/history/archive/players?id=104925' };
  assert.ok(ex.explainError(404, body, '/players/104925').includes(body.see));
});

test('429 messages', () => {
  const minute = ex.explainError(429, fixture('error_429_minute').body, '/matches');
  const day = ex.explainError(429, fixture('error_429_day').body, '/matches');
  assert.ok(minute.startsWith('HTTP 429') && minute.includes('Retry-After'));
  assert.ok(day.startsWith('HTTP 429') && day.includes('2026-10-24T00:00:00Z'));
});

test('other errors use detail and allowed', () => {
  const body = { error: 'bad_status', detail: 'status must be one of the allowed values', allowed: ['live', 'upcoming'] };
  const message = ex.explainError(400, body, '/matches?status=finished');
  assert.ok(message.startsWith('HTTP 400 bad_status'));
  assert.ok(message.includes(body.detail));
  assert.ok(message.includes('live') && message.includes('upcoming'));
});

test('an empty body', () => {
  assert.ok(ex.explainError(500, {}, '/matches').startsWith('HTTP 500'));
});

test('requestJson success', async () => {
  const fetchImpl = fakeFetch(fixture('player_34'));
  const body = await ex.requestJson('/players/34', 'abc123', fetchImpl);
  assert.equal(body.id, 34);
  assert.equal(fetchImpl.calls[0].url, `${ex.BASE_URL}/players/34`);
  assert.equal(fetchImpl.calls[0].headers.get('authorization'), 'Bearer abc123');
});

for (const [name, status, code] of [
  ['error_401_bad_key', 401, 'unauthorized'],
  ['error_403_upgrade_required', 403, 'upgrade_required'],
  ['error_404_player', 404, 'not_found'],
]) {
  test(`requestJson throws ApiError for ${status}`, async () => {
    await assert.rejects(ex.requestJson('/somewhere', 'abc123', fakeFetch(fixture(name))), (error) => {
      assert.ok(error instanceof ex.ApiError);
      assert.equal(error.status, status);
      assert.equal(error.code, code);
      assert.ok(error.message.startsWith(`HTTP ${status}`));
      return true;
    });
  });
}

test('requestJson with a body that is not JSON', async () => {
  const fetchImpl = fakeFetch({ status: 502, headers: {}, body: '<html>Bad gateway</html>' });
  await assert.rejects(ex.requestJson('/matches', 'abc123', fetchImpl), (error) => {
    assert.ok(error instanceof ex.ApiError);
    assert.equal(error.status, 502);
    assert.equal(error.code, null);
    return true;
  });
});

test('the demo runs all three errors', async () => {
  const fetchImpl = fakeFetch(fixture('error_401_bad_key'), fixture('error_403_upgrade_required'), fixture('error_404_player'));
  const messages = await ex.demo('abc123', fetchImpl);
  assert.deepEqual(messages.map((m) => m.split(': ')[0]), ['a bad key', 'a paid endpoint', 'an unknown id']);
  assert.ok(messages[0].includes('HTTP 401') && messages[1].includes('HTTP 403') && messages[2].includes('HTTP 404'));
  assert.equal(fetchImpl.calls[0].headers.get('authorization'), 'Bearer not-a-real-key');
});

const SECRET = 'sk-test-DO-NOT-LEAK-1234';

for (const name of ['error_401_bad_key', 'error_403_upgrade_required', 'error_404_player', 'error_429_minute']) {
  test(`the key never appears in a message: ${name}`, async () => {
    await assert.rejects(ex.requestJson('/players/34', SECRET, fakeFetch(fixture(name))), (error) => {
      assert.ok(error instanceof ex.ApiError);
      assert.ok(!error.message.includes(SECRET));
      return true;
    });
  });
}

test('the demo output has no key', async () => {
  const fetchImpl = fakeFetch(fixture('error_401_bad_key'), fixture('error_403_upgrade_required'), fixture('error_404_player'));
  const messages = await ex.demo(SECRET, fetchImpl);
  assert.ok(!messages.some((m) => m.includes(SECRET) || m.includes('not-a-real-key')));
});

test('the abuse block message', () => {
  const message = ex.explainError(429, fixture('error_429_abuse').body, '/matches');
  assert.ok(message.startsWith('HTTP 429') && message.includes('24 hours'));
});

test('allowed values that are not strings', () => {
  const message = ex.explainError(400, { error: 'bad_limit', allowed: [1, 200] }, '/matches?limit=0');
  assert.ok(message.includes('1') && message.includes('200'));
});
