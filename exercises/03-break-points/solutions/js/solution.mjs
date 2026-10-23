// Exercise 3 solution: break point detector.
// A break point is a point where the RECEIVER wins the game by winning it.
// Tiebreaks have no break points.

import { pathToFileURL } from 'node:url';

export const POINT_VALUES = { 0: 0, 15: 1, 30: 2, 40: 3, AD: 4 };

export function pointValue(text) {
  if (typeof text !== 'string' || !Object.hasOwn(POINT_VALUES, text)) {
    throw new RangeError(`not a game score: ${JSON.stringify(text)}`);
  }
  return POINT_VALUES[text];
}

export function breakPointsHeld(score) {
  if (!score || score.is_tiebreak) return 0;
  const { server, points } = score;
  if ((server !== 1 && server !== 2) || !Array.isArray(points) || points.length !== 2) return 0;
  const serverPoints = pointValue(points[server - 1]);
  const receiverPoints = pointValue(points[2 - server]);
  if (receiverPoints === 4) return 1;
  if (receiverPoints === 3 && serverPoints <= 2) return 3 - serverPoints;
  return 0;
}

export function isBreakPoint(score) {
  return breakPointsHeld(score) > 0;
}

export function findBreakPoints(matches) {
  return matches
    .filter((match) => match.status === 'live' && isBreakPoint(match.score))
    .map((match) => match.id);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  console.log(isBreakPoint({ points: ['15', '40'], server: 1, is_tiebreak: false }));
}
