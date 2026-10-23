// Exercise 8 solution: a terminal scoreboard that stays inside the FREE quota.
// Usage: LIVETENNISAPI_KEY=... node solution.mjs 180   (a 3-hour session)

import { pathToFileURL } from 'node:url';

export const BASE_URL = 'https://api.livetennisapi.com/api/public/v1';
export const LIVE_URL = `${BASE_URL}/matches?status=live&limit=200`;
export const TOUR_ORDER = ['atp', 'wta', 'challenger', 'itf', 'juniors'];

export const authHeaders = (key) => ({ Authorization: `Bearer ${key}`, Accept: 'application/json' });
export const realClock = () => performance.now() / 1000;
export const realSleep = (seconds) => new Promise((resolve) => setTimeout(resolve, seconds * 1000));

// --- the arithmetic ---------------------------------------------------------

export function pollIntervalSeconds(sessionMinutes, { dailyBudget = 100, reserve = 10, requestsPerPoll = 1, perMinute = 30 } = {}) {
  if (!(sessionMinutes > 0)) throw new RangeError('The session must last more than 0 minutes.');
  const usable = dailyBudget - reserve;
  if (usable < requestsPerPoll) throw new RangeError('The reserve leaves no requests for polling.');
  const polls = Math.floor(usable / requestsPerPoll);
  const interval = Math.ceil((sessionMinutes * 60) / polls);
  // Polling exactly at the minute limit leaves no room for anything else, so add a second.
  const floor = Math.ceil((60 * requestsPerPoll) / perMinute) + 1;
  return Math.max(interval, floor);
}

export function requestsNeeded(sessionMinutes, interval, requestsPerPoll = 1) {
  return Math.ceil((sessionMinutes * 60) / interval) * requestsPerPoll;
}

export function explainInterval(sessionMinutes, { dailyBudget = 100, reserve = 10 } = {}) {
  const usable = dailyBudget - reserve;
  const seconds = Math.round(sessionMinutes * 60);
  const interval = pollIntervalSeconds(sessionMinutes, { dailyBudget, reserve });
  const needed = requestsNeeded(sessionMinutes, interval);
  return (
    `Daily budget ${dailyBudget} - reserve ${reserve} = ${usable} requests for polling. ` +
    `Session ${sessionMinutes} min x 60 = ${seconds} s. ` +
    `${seconds} s / ${usable} requests = ${(seconds / usable).toFixed(1)} s, rounded up to ${interval} s. ` +
    `Check: ${seconds} s / ${interval} s = ${needed} requests, which is at most ${usable}.`
  );
}

// --- the board --------------------------------------------------------------

const nameOf = (match, n) => match.players?.[`p${n}`]?.name || `Player ${n}`;

// The same rules as exercise 2.
export function formatScore(match) {
  const score = match.score;
  if (score == null) {
    if (match.status !== 'completed') return 'not started';
    // A completed match with no score row, such as a walkover.
    if (['unresolved', 'abandoned'].includes(match.outcome)) return 'no result';
    if (match.winner === 1 || match.winner === 2) {
      return `${nameOf(match, match.winner)} won${match.outcome === 'walkover' ? ' by walkover' : ''}`;
    }
    return 'final';
  }
  const games = score.games;
  if (games == null) return 'score unavailable';
  const matchTb = Boolean(score.is_tiebreak) && games[0].length > 0 && games[1].length > 0 && !(games[0].at(-1) === 6 && games[1].at(-1) === 6);
  const setParts = games[0].slice(0, games[1].length).map((a, i) => `${a}-${games[1][i]}`);
  if (matchTb && setParts.length) setParts[setParts.length - 1] = `[${setParts.at(-1)}]`;
  const setsText = setParts.join(' ') || '0-0';
  if (match.status === 'completed') {
    if (['unresolved', 'abandoned'].includes(match.outcome)) return `${setsText}, no result`;
    let winner = match.winner;
    if (winner !== 1 && winner !== 2) {
      const sets = score.sets ?? [0, 0];
      if (sets[0] === sets[1]) return `${setsText}, final`;
      winner = sets[0] > sets[1] ? 1 : 2;
    }
    return `${setsText}, ${nameOf(match, winner)} won`;
  }
  const parts = [setsText];
  const points = score.points;
  if (Array.isArray(points) && points.length === 2 && !matchTb) {
    const [a, b] = points;
    if (score.is_tiebreak) parts.push(`tiebreak ${a}-${b}`);
    else if (a === '40' && b === '40') parts.push('deuce');
    else if (a === 'AD') parts.push(`advantage ${nameOf(match, 1)}`);
    else if (b === 'AD') parts.push(`advantage ${nameOf(match, 2)}`);
    else parts.push(`${a}-${b}`);
  }
  if (score.server === 1 || score.server === 2) parts.push(`${nameOf(match, score.server)} serving`);
  return parts.join(', ');
}

function compareMatches(a, b) {
  const nameA = (a.tournament ?? '').toLowerCase();
  const nameB = (b.tournament ?? '').toLowerCase();
  if (nameA !== nameB) return nameA < nameB ? -1 : 1;
  return (a.id ?? 0) - (b.id ?? 0);
}

export function renderBoard(matches) {
  const live = matches.filter((m) => m.status === 'live');
  if (live.length === 0) return 'No live matches right now.';
  const lines = [`Live tennis: ${live.length} ${live.length === 1 ? 'match' : 'matches'}`];
  for (const tour of [...TOUR_ORDER, 'other']) {
    const group = live.filter((m) => (TOUR_ORDER.includes(m.tour) ? m.tour : 'other') === tour).sort(compareMatches);
    if (group.length === 0) continue;
    lines.push(tour.toUpperCase());
    for (const match of group) {
      lines.push(`  ${match.tournament || 'Unknown tournament'} | ${nameOf(match, 1)} v ${nameOf(match, 2)} | ${formatScore(match)}`);
    }
  }
  return lines.join('\n');
}

// --- the loop ---------------------------------------------------------------

export async function runScoreboard(
  key,
  sessionMinutes,
  { fetchImpl = fetch, sleep = realSleep, clock = realClock, out = console.log, dailyBudget = 100, reserve = 10 } = {},
) {
  const interval = pollIntervalSeconds(sessionMinutes, { dailyBudget, reserve });
  const usable = dailyBudget - reserve;
  const sessionSeconds = sessionMinutes * 60;
  const start = clock();
  let calls = 0;
  while (calls < usable) {
    if (calls && clock() - start >= sessionSeconds) break; // a sleep can wake late, so check before every request
    const response = await fetchImpl(LIVE_URL, { headers: authHeaders(key), signal: AbortSignal.timeout(10_000) });
    calls += 1;
    let wait = interval;
    if (response.status === 200) {
      const body = await response.json();
      out(renderBoard(body.data ?? []));
    } else if (response.status === 429) {
      let body = {};
      try {
        body = await response.json();
      } catch {
        body = {};
      }
      if (body.error === 'abuse_throttled') {
        out('This key is blocked for 24 hours for ignoring rate limits. Stopping.');
        break;
      }
      if (body.scope === 'day') {
        out('The daily quota is used up. Stopping.');
        break;
      }
      const header = response.headers.get('retry-after') ?? '';
      const retryAfter = /^\s*[0-9]+(\.[0-9]+)?\s*$/.test(header) ? Number(header) : NaN;
      wait = Number.isFinite(retryAfter) ? Math.max(interval, retryAfter) : interval;
      out(`Rate limited. Waiting ${wait} s.`);
    } else if (response.status === 401 || response.status === 403) {
      out(`HTTP ${response.status}. Check your key and plan. Stopping.`);
      break;
    } else {
      out(`HTTP ${response.status}. Trying again at the next poll.`);
    }
    if (clock() - start + wait >= sessionSeconds) break;
    await sleep(wait);
  }
  return calls;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const key = (process.env.LIVETENNISAPI_KEY ?? '').trim();
  if (!key) {
    console.error('Set LIVETENNISAPI_KEY first.');
    process.exitCode = 1;
  } else {
    const minutes = Number(process.argv[2] ?? 180);
    console.log(explainInterval(minutes));
    const calls = await runScoreboard(key, minutes, { out: (text) => console.log(`\n${text}`) });
    console.log(`Done after ${calls} requests.`);
  }
}
