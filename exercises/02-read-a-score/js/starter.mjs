// Exercise 2: read a score.
//
// Turn one match object from GET /matches into a line a person can read,
// for example "6-4 3-4, 30-15, Jannik Sinner serving".
//
// Every score array is player-major: index 0 is player 1, index 1 is player 2.
//   sets   [1, 0]            player 1 leads one set to nil
//   games  [[6, 3], [4, 4]]  6-4 in the first set, 3-4 in the second
//   points ["30", "15"]      the game in progress
//   server 1                 player 1 is serving
//
// Run the tests with: node --test exercises/02-read-a-score/js/read_score.test.mjs

import { pathToFileURL } from 'node:url';

// Given: the name of player 1 or 2, with a fallback when it is missing.
export function playerName(match, number) {
  return match.players?.[`p${number}`]?.name || `Player ${number}`;
}

// Return true when a deciding match tiebreak (first to 10) is being played.
// The API sets is_tiebreak and puts the breaker's points in the last set's
// games slot: [[6, 4, 10], [4, 6, 5]] reads 6-4 4-6 [10-5].
// An ordinary tiebreak only happens at 6-6, so: is_tiebreak is true AND the
// last set is not 6-6. Empty games lists mean false. (A match tiebreak that
// reaches 6-6 looks the same as an ordinary one; treat it as ordinary.)
export function isMatchTiebreak(score) {
  // TODO
  throw new Error('not implemented');
}

// [[6, 3], [4, 4]] -> ["6-4", "3-4"]. With matchTiebreak the last set is "[10-5]".
// If one array is longer than the other, stop at the shorter one. With
// matchTiebreak, pair the scores first, then put brackets round the last pair.
export function setScores(games, matchTiebreak = false) {
  // TODO
  throw new Error('not implemented');
}

// Describe the game in progress:
// - points missing or not two values: null
// - ordinary tiebreak: "tiebreak 5-3"; match tiebreak: null
// - 40-40: "deuce"; "AD" for a player: "advantage <name>"
// - anything else: "30-15" (player 1 first)
export function pointScore(score, match) {
  // TODO
  throw new Error('not implemented');
}

// Build the full line:
// - score is null and status is not "completed": "not started"
// - score is null and status "completed" (a walkover has no score row):
//   "no result" for an unresolved or abandoned outcome, otherwise
//   "<winner name> won by walkover" when outcome is "walkover",
//   "<winner name> won" for another outcome, or "final" with no winner
// - games is null (the API withheld the score): "score unavailable"
// - no games yet ([[], []]): use "0-0" for the sets part
// - status "completed":
//   - outcome "unresolved" or "abandoned" (nobody was awarded the match):
//     "<sets>, no result"
//   - otherwise "<sets>, <winner name> won". Use the match's `winner` field
//     (1 or 2) when it is set. If it is null, take the winner from `sets`
//     (or write "<sets>, final" when sets are level).
// - otherwise join the sets part, the point score and "<name> serving" with ", "
export function formatScore(match) {
  // TODO
  throw new Error('not implemented');
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
