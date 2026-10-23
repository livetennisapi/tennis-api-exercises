// Exercise 1: your first request.
//
// Fill in every function marked TODO. Run the tests with:
//   node --test exercises/01-first-request/js/first_request.test.mjs
// Run the program against the real API with:
//   export LIVETENNISAPI_KEY=your_key_here
//   node exercises/01-first-request/js/starter.mjs

import { pathToFileURL } from 'node:url';

export const BASE_URL = 'https://api.livetennisapi.com/api/public/v1';

export class MissingKeyError extends Error {}

// Return the key from env.LIVETENNISAPI_KEY with surrounding spaces removed.
// Throw MissingKeyError with a helpful message when it is missing or blank.
export function readApiKey(env = process.env) {
  // TODO
  throw new Error('not implemented');
}

// Return a plain object of request headers that carry the key as
// "Authorization: Bearer <key>". Also ask for JSON with Accept.
export function authHeaders(key) {
  // TODO
  throw new Error('not implemented');
}

// Call GET /health WITHOUT a key: fetchImpl(url, { headers }).
// Return true when the body says status "ok", false otherwise.
export async function checkHealth(fetchImpl = fetch) {
  // TODO
  throw new Error('not implemented');
}

// Call GET /matches?status=live&limit=200 with the key in a header.
// Return meta.total when it is an integer, otherwise data.length.
// Throw an Error that names the status when it is not 200.
// Never put the key in the URL.
export async function countLiveMatches(key, fetchImpl = fetch) {
  // TODO
  throw new Error('not implemented');
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
