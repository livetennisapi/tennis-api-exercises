// Exercise 4: filter and group the live slate.
//
// Work on the `data` array from GET /matches?status=live. Each match has a
// `tour` field ("atp", "wta", "challenger", "itf", "juniors" or null), a
// `tournament` name and a three-valued `draw` ("singles", "doubles" or null).
//
// Run the tests with: node --test exercises/04-filter-and-group/js/filter_group.test.mjs

import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

export const TOUR_ORDER = ['atp', 'wta', 'challenger', 'itf', 'juniors'];
export const OTHER = 'other';

// Keep matches whose draw equals `draw` exactly.
// A null draw means "unknown". It matches neither "singles" nor "doubles".
export function filterDraw(matches, draw) {
  // TODO
  throw new Error('not implemented');
}

// Group LIVE matches by tour and return a plain object.
// - Skip any match whose status is not "live".
// - A null or unrecognised tour goes in the "other" group.
// - Keys follow TOUR_ORDER, then "other". Leave out empty groups.
// - Inside a group, sort by tournament name (ignoring case), then by id.
// - Do not change the input array.
export function groupByTour(matches) {
  // TODO
  throw new Error('not implemented');
}

// Return [tournament name, number of matches] pairs.
// Most matches first. Break ties by name, ignoring case.
export function countByTournament(matches) {
  // TODO
  throw new Error('not implemented');
}

// Given: print-friendly text built from groupByTour.
export function summary(matches) {
  const lines = [];
  for (const [tour, group] of Object.entries(groupByTour(matches))) {
    lines.push(`${tour.toUpperCase()} (${group.length})`);
    for (const match of group) {
      lines.push(`  ${match.tournament}: ${match.players.p1.name} v ${match.players.p2.name}`);
    }
  }
  return lines.join('\n');
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const url = new URL('../../../fixtures/matches_live.json', import.meta.url);
  const data = JSON.parse(readFileSync(url, 'utf8')).response.body.data;
  console.log(summary(data));
  for (const [name, count] of countByTournament(data).slice(0, 5)) {
    console.log(`${String(count).padStart(3)}  ${name}`);
  }
}
