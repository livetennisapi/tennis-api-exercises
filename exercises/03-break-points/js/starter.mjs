// Exercise 3: break point detector.
//
// A break point is a point where the RECEIVER wins the game by winning it.
// The receiver is whoever is not serving: if server is 1, the receiver is 2.
// Points are player-major strings: points[0] is player 1, points[1] is player 2.
// The values are "0", "15", "30", "40" and "AD" (advantage).
// Tiebreaks have no break points.
//
// Run the tests with: node --test exercises/03-break-points/js/break_points.test.mjs

import { pathToFileURL } from 'node:url';

export const POINT_VALUES = { 0: 0, 15: 1, 30: 2, 40: 3, AD: 4 };

// Turn "30" into 2 using POINT_VALUES. Throw a RangeError for anything unknown,
// including a number such as 40 (the API always sends strings).
export function pointValue(text) {
  // TODO
  throw new Error('not implemented');
}

// How many break points the receiver holds right now:
// 0-40 -> 3, 15-40 -> 2, 30-40 -> 1, receiver on AD -> 1, anything else -> 0
// (scores written server first). Return 0 when score is null, when
// is_tiebreak is true, when server is not 1 or 2, or when points is missing.
export function breakPointsHeld(score) {
  // TODO
  throw new Error('not implemented');
}

// True when the receiver holds at least one break point.
export function isBreakPoint(score) {
  // TODO
  throw new Error('not implemented');
}

// Ids of matches with status "live" whose current point is a break point,
// in input order.
export function findBreakPoints(matches) {
  // TODO
  throw new Error('not implemented');
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  console.log(isBreakPoint({ points: ['15', '40'], server: 1, is_tiebreak: false }));
}
