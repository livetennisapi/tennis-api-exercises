// Exercise 2 solution: read a score.
// Every score array is player-major: index 0 is player 1, index 1 is player 2.

import { pathToFileURL } from 'node:url';

// Outcomes where nobody was awarded the match.
export const NO_RESULT = ['unresolved', 'abandoned'];

export function playerName(match, number) {
  return match.players?.[`p${number}`]?.name || `Player ${number}`;
}

export function isMatchTiebreak(score) {
  const games = score.games ?? [[], []];
  if (!score.is_tiebreak || !games[0]?.length || !games[1]?.length) return false;
  return !(games[0].at(-1) === 6 && games[1].at(-1) === 6);
}

export function setScores(games, matchTiebreak = false) {
  const [first, second] = games;
  const length = Math.min(first.length, second.length);
  const parts = first.slice(0, length).map((a, i) => `${a}-${second[i]}`);
  if (matchTiebreak && parts.length) {
    parts[parts.length - 1] = `[${parts.at(-1)}]`; // pair first, then bracket
  }
  return parts;
}

export function pointScore(score, match) {
  const points = score.points;
  if (!Array.isArray(points) || points.length !== 2) return null;
  const [a, b] = points;
  if (score.is_tiebreak) {
    return isMatchTiebreak(score) ? null : `tiebreak ${a}-${b}`;
  }
  if (a === '40' && b === '40') return 'deuce';
  if (a === 'AD') return `advantage ${playerName(match, 1)}`;
  if (b === 'AD') return `advantage ${playerName(match, 2)}`;
  return `${a}-${b}`;
}

export function formatScore(match) {
  const score = match.score;
  if (score == null) {
    if (match.status !== 'completed') return 'not started';
    // A completed match with no score row, such as a walkover.
    if (NO_RESULT.includes(match.outcome)) return 'no result';
    if (match.winner === 1 || match.winner === 2) {
      return `${playerName(match, match.winner)} won${match.outcome === 'walkover' ? ' by walkover' : ''}`;
    }
    return 'final';
  }
  if (score.games == null) return 'score unavailable';
  const setsText = setScores(score.games, isMatchTiebreak(score)).join(' ') || '0-0';
  if (match.status === 'completed') {
    if (NO_RESULT.includes(match.outcome)) return `${setsText}, no result`;
    let winner = match.winner;
    if (winner !== 1 && winner !== 2) {
      const sets = score.sets ?? [0, 0];
      if (sets[0] === sets[1]) return `${setsText}, final`;
      winner = sets[0] > sets[1] ? 1 : 2;
    }
    return `${setsText}, ${playerName(match, winner)} won`;
  }
  const parts = [setsText];
  const pointsText = pointScore(score, match);
  if (pointsText) parts.push(pointsText);
  if (score.server === 1 || score.server === 2) parts.push(`${playerName(match, score.server)} serving`);
  return parts.join(', ');
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  console.log(
    formatScore({
      status: 'live',
      players: { p1: { name: 'Jannik Sinner' }, p2: { name: 'Carlos Alcaraz' } },
      score: { sets: [1, 0], games: [[6, 3], [4, 4]], points: ['30', '15'], server: 1, is_tiebreak: false },
    }),
  );
}
