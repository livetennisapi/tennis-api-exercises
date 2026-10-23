// Exercise 1 solution: your first request.

import { pathToFileURL } from 'node:url';

export const BASE_URL = 'https://api.livetennisapi.com/api/public/v1';

export class MissingKeyError extends Error {}

export function readApiKey(env = process.env) {
  const key = (env.LIVETENNISAPI_KEY ?? '').trim();
  if (!key) {
    throw new MissingKeyError(
      'LIVETENNISAPI_KEY is not set. Get a free key at ' +
        'https://livetennisapi.com/subscribe/free and export it in your shell.',
    );
  }
  return key;
}

export function authHeaders(key) {
  return { Authorization: `Bearer ${key}`, Accept: 'application/json' };
}

export async function checkHealth(fetchImpl = fetch) {
  const response = await fetchImpl(`${BASE_URL}/health`, {
    headers: { Accept: 'application/json' },
    signal: AbortSignal.timeout(10_000),
  });
  if (response.status !== 200) return false;
  const body = await response.json();
  return body.status === 'ok';
}

export async function countLiveMatches(key, fetchImpl = fetch) {
  const response = await fetchImpl(`${BASE_URL}/matches?status=live&limit=200`, {
    headers: authHeaders(key),
    signal: AbortSignal.timeout(10_000),
  });
  if (response.status !== 200) {
    throw new Error(`GET /matches answered HTTP ${response.status}`);
  }
  const payload = await response.json();
  const total = payload.meta?.total;
  if (Number.isInteger(total)) return total;
  return (payload.data ?? []).length;
}

async function main() {
  console.log((await checkHealth()) ? 'API is up.' : 'API health check failed.');
  let key;
  try {
    key = readApiKey();
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
    return;
  }
  const count = await countLiveMatches(key);
  console.log(`${count} matches are live right now.`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  await main();
}
