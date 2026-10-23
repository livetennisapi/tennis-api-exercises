// Exercise 5: player search.
//
// Search players by name with GET /players?search=..., decide what to do
// with zero, one or many results, then read one player with GET /players/{id}.
//
// Watch out: the search parameter is called `search`. When this was written
// (2026-10-23) the API ignored a `name` parameter, so /players?name=sinner
// quietly returned the whole roster. Always check what came back.
//
// Run the tests with: node --test exercises/05-player-search/js/player_search.test.mjs
// Try it for real:    node exercises/05-player-search/js/starter.mjs Jannik Sinner

import { pathToFileURL } from 'node:url';

export const BASE_URL = 'https://api.livetennisapi.com/api/public/v1';

// Given code
export const authHeaders = (key) => ({ Authorization: `Bearer ${key}`, Accept: 'application/json' });

export class PlayerNotFound extends Error {}

export class AmbiguousPlayer extends Error {
  constructor(message, candidates) {
    super(message);
    this.candidates = candidates;
  }
}

// Your code

// Build BASE_URL + /players?search=<name>&limit=<limit>.
// Encode the name with encodeURIComponent so "Jannik Sinner" becomes "Jannik%20Sinner".
export function searchUrl(name, limit = 10) {
  // TODO
  throw new Error('not implemented');
}

// Search and return { players: [...], total: <number> }.
// - Trim the name. Throw a RangeError for a blank name WITHOUT making a request.
// - Throw an Error when the status is not 200.
// - total is meta.total when it is an integer, otherwise players.length.
export async function searchPlayers(name, key, fetchImpl = fetch) {
  // TODO
  throw new Error('not implemented');
}

// Choose one player or explain why you cannot.
// - If `total` is bigger than players.length, only one page came back and a
//   better match may be on the next one. Throw AmbiguousPlayer (candidates
//   from the singles rows, or from all rows if there are none). Never pick a
//   player, and never say "not found", from an incomplete page.
// - With singlesOnly, drop rows where is_doubles_team is true.
// - Nothing left: throw PlayerNotFound.
// - Exactly one left: return it.
// - More than one: throw AmbiguousPlayer. Put the first five names in
//   `candidates` (keep the API's order: ranked players come first) and say
//   how many matched in the message (use `total` when it is given).
export function pickPlayer(players, total = null, singlesOnly = true) {
  // TODO
  throw new Error('not implemented');
}

// GET /players/{playerId}. Throw PlayerNotFound on 404, an Error on other errors.
export async function getPlayer(playerId, key, fetchImpl = fetch) {
  // TODO
  throw new Error('not implemented');
}

// One line about a player: "Jannik Sinner (ITA), ATP rank 1, 10950 points"
// - country is upper-cased; leave the brackets out when it is null
// - ranking null, or ranking_status "unranked": "<name> (<COUNTRY>), unranked".
//   An unranked player may still carry the last rank they held. It is not
//   their current rank, so do not show it.
// - tour null: "rank 1" instead of "ATP rank 1"
// - ranking_points null: leave the points part out
export function describePlayer(player) {
  // TODO
  throw new Error('not implemented');
}

// Search, pick one player, then return the full record from getPlayer.
export async function findPlayer(name, key, fetchImpl = fetch) {
  // TODO
  throw new Error('not implemented');
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const key = (process.env.LIVETENNISAPI_KEY ?? '').trim();
  if (!key) {
    console.error('Set LIVETENNISAPI_KEY first.');
    process.exitCode = 1;
  } else {
    const name = process.argv.slice(2).join(' ') || 'Jannik Sinner';
    try {
      console.log(describePlayer(await findPlayer(name, key)));
    } catch (error) {
      console.log(error.message);
      process.exitCode = 1;
    }
  }
}
