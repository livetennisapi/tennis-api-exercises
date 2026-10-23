// Exercise 5 solution: player search.

import { pathToFileURL } from 'node:url';

export const BASE_URL = 'https://api.livetennisapi.com/api/public/v1';

export const authHeaders = (key) => ({ Authorization: `Bearer ${key}`, Accept: 'application/json' });

export class PlayerNotFound extends Error {}

export class AmbiguousPlayer extends Error {
  constructor(message, candidates) {
    super(message);
    this.candidates = candidates;
  }
}

export function searchUrl(name, limit = 10) {
  return `${BASE_URL}/players?search=${encodeURIComponent(name)}&limit=${limit}`;
}

export async function searchPlayers(name, key, fetchImpl = fetch) {
  const trimmed = name.trim();
  if (!trimmed) throw new RangeError("Type at least one letter of a player's name.");
  const response = await fetchImpl(searchUrl(trimmed), { headers: authHeaders(key), signal: AbortSignal.timeout(10_000) });
  if (response.status !== 200) throw new Error(`GET /players answered HTTP ${response.status}`);
  const payload = await response.json();
  const players = payload.data ?? [];
  const total = payload.meta?.total;
  return { players, total: Number.isInteger(total) ? total : players.length };
}

export function pickPlayer(players, total = null, singlesOnly = true) {
  const pool = singlesOnly ? players.filter((p) => !p.is_doubles_team) : [...players];
  if (total !== null && total > players.length) {
    // Only one page came back. A better match may be on the next page, so do not decide.
    const candidates = (pool.length ? pool : players).slice(0, 5).map((p) => p.name);
    throw new AmbiguousPlayer(
      `${total} players match and only ${players.length} came back. Be more specific, for example: ${candidates.join(', ')}.`,
      candidates,
    );
  }
  if (pool.length === 0) throw new PlayerNotFound('No player matches that name.');
  if (pool.length === 1) return pool[0];
  const candidates = pool.slice(0, 5).map((p) => p.name);
  const count = total ?? pool.length;
  throw new AmbiguousPlayer(
    `${count} players match. Be more specific, for example: ${candidates.join(', ')}.`,
    candidates,
  );
}

export async function getPlayer(playerId, key, fetchImpl = fetch) {
  const response = await fetchImpl(`${BASE_URL}/players/${Number.parseInt(playerId, 10)}`, {
    headers: authHeaders(key),
    signal: AbortSignal.timeout(10_000),
  });
  if (response.status === 404) throw new PlayerNotFound(`No player has id ${playerId}.`);
  if (response.status !== 200) throw new Error(`GET /players/${playerId} answered HTTP ${response.status}`);
  return response.json();
}

export function describePlayer(player) {
  let text = player.name;
  if (player.country) text += ` (${player.country.toUpperCase()})`;
  if (player.ranking == null || player.ranking_status === 'unranked') return `${text}, unranked`;
  const tour = (player.tour ?? '').toUpperCase();
  text += tour ? `, ${tour} rank ${player.ranking}` : `, rank ${player.ranking}`;
  if (player.ranking_points != null) text += `, ${player.ranking_points} points`;
  return text;
}

export async function findPlayer(name, key, fetchImpl = fetch) {
  const { players, total } = await searchPlayers(name, key, fetchImpl);
  const chosen = pickPlayer(players, total);
  return getPlayer(chosen.id, key, fetchImpl);
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
