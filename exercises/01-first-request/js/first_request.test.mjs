// Offline tests for exercise 1. They replay recorded responses from fixtures/.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const target = process.env.SOLUTION === '1' ? '../solutions/js/solution.mjs' : './starter.mjs';
const ex = await import(new URL(target, import.meta.url));

function fixture(name) {
  const url = new URL(`../../../fixtures/${name}.json`, import.meta.url);
  return JSON.parse(readFileSync(url, 'utf8')).response;
}

// Stands in for fetch. Records every call and replays fixture responses.
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


test('reads the key from the environment', () => {
  assert.equal(ex.readApiKey({ LIVETENNISAPI_KEY: '  abc123  ' }), 'abc123');
});

for (const env of [{}, { LIVETENNISAPI_KEY: '' }, { LIVETENNISAPI_KEY: '   ' }]) {
  test(`a missing or blank key throws MissingKeyError: ${JSON.stringify(env)}`, () => {
    assert.throws(() => ex.readApiKey(env), (error) => {
      assert.ok(error instanceof ex.MissingKeyError);
      assert.match(error.message, /LIVETENNISAPI_KEY/);
      return true;
    });
  });
}

test('auth headers use Bearer', () => {
  const headers = new Headers(ex.authHeaders('abc123'));
  assert.equal(headers.get('authorization'), 'Bearer abc123');
  assert.match(headers.get('accept') ?? '', /json/);
});

test('health needs no key', async () => {
  const fetchImpl = fakeFetch(fixture('health'));
  assert.equal(await ex.checkHealth(fetchImpl), true);
  const { url, headers } = fetchImpl.calls[0];
  assert.equal(url, `${ex.BASE_URL}/health`);
  assert.ok(!headers.has('authorization'));
  assert.ok(!headers.has('x-api-key'));
  assert.ok(!url.includes('token='));
});

test('a failed health check is false', async () => {
  const fetchImpl = fakeFetch({ status: 503, headers: {}, body: { status: 'down' } });
  assert.equal(await ex.checkHealth(fetchImpl), false);
});

test('counts live matches from the fixture', async () => {
  const fetchImpl = fakeFetch(fixture('matches_live'));
  assert.equal(await ex.countLiveMatches('abc123', fetchImpl), 29);
  const { url, headers } = fetchImpl.calls[0];
  assert.ok(url.startsWith(`${ex.BASE_URL}/matches?`));
  assert.ok(url.includes('status=live'));
  assert.equal(headers.get('authorization'), 'Bearer abc123');
});

test('the key never goes in the URL', async () => {
  const fetchImpl = fakeFetch(fixture('matches_live'));
  await ex.countLiveMatches('abc123', fetchImpl);
  assert.ok(!fetchImpl.calls[0].url.includes('abc123'));
  assert.ok(!fetchImpl.calls[0].url.includes('token='));
});

test('falls back to data length when meta.total is null', async () => {
  const reply = fixture('matches_live');
  reply.body.meta.total = null;
  const fetchImpl = fakeFetch(reply);
  assert.equal(await ex.countLiveMatches('abc123', fetchImpl), reply.body.data.length);
});

test('a non-200 status throws and names the status', async () => {
  const fetchImpl = fakeFetch(fixture('error_401_bad_key'));
  await assert.rejects(ex.countLiveMatches('not-a-real-key', fetchImpl), /401/);
});

test('readApiKey defaults to process.env', () => {
  const saved = process.env.LIVETENNISAPI_KEY;
  try {
    process.env.LIVETENNISAPI_KEY = ' from-env ';
    assert.equal(ex.readApiKey(), 'from-env');
    delete process.env.LIVETENNISAPI_KEY;
    assert.throws(() => ex.readApiKey(), ex.MissingKeyError);
  } finally {
    if (saved === undefined) delete process.env.LIVETENNISAPI_KEY;
    else process.env.LIVETENNISAPI_KEY = saved;
  }
});

test('asks for the largest page', async () => {
  const fetchImpl = fakeFetch(fixture('matches_live'));
  await ex.countLiveMatches('abc123', fetchImpl);
  assert.ok(fetchImpl.calls[0].url.includes('limit=200'));
});

test('uses meta.total, not the page length', async () => {
  const reply = fixture('matches_live');
  reply.body.meta.total = 57; // more matches than fit on this page
  assert.equal(await ex.countLiveMatches('abc123', fakeFetch(reply)), 57);
});

for (const body of [{}, { status: 'degraded' }, { version: 'v1' }]) {
  test(`health reads the body, not just the status: ${JSON.stringify(body)}`, async () => {
    assert.equal(await ex.checkHealth(fakeFetch({ status: 200, headers: {}, body })), false);
  });
}
