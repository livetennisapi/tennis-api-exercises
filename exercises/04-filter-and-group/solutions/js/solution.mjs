// Exercise 4 solution: filter and group the live slate.

import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

export const TOUR_ORDER = ['atp', 'wta', 'challenger', 'itf', 'juniors'];
export const OTHER = 'other';

export function filterDraw(matches, draw) {
  return matches.filter((match) => match.draw === draw);
}

function compareMatches(a, b) {
  const nameA = (a.tournament ?? '').toLowerCase();
  const nameB = (b.tournament ?? '').toLowerCase();
  if (nameA !== nameB) return nameA < nameB ? -1 : 1;
  return (a.id ?? 0) - (b.id ?? 0);
}

export function groupByTour(matches) {
  const groups = new Map();
  for (const match of matches) {
    if (match.status !== 'live') continue;
    const tour = TOUR_ORDER.includes(match.tour) ? match.tour : OTHER;
    if (!groups.has(tour)) groups.set(tour, []);
    groups.get(tour).push(match);
  }
  const ordered = {};
  for (const tour of [...TOUR_ORDER, OTHER]) {
    if (groups.has(tour)) ordered[tour] = [...groups.get(tour)].sort(compareMatches);
  }
  return ordered;
}

export function countByTournament(matches) {
  const counts = new Map();
  for (const match of matches) {
    const name = match.tournament || 'Unknown tournament';
    counts.set(name, (counts.get(name) ?? 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => {
    if (a[1] !== b[1]) return b[1] - a[1];
    const nameA = a[0].toLowerCase();
    const nameB = b[0].toLowerCase();
    return nameA < nameB ? -1 : nameA > nameB ? 1 : 0;
  });
}

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
  const url = new URL('../../../../fixtures/matches_live.json', import.meta.url);
  const data = JSON.parse(readFileSync(url, 'utf8')).response.body.data;
  console.log(summary(data));
  for (const [name, count] of countByTournament(data).slice(0, 5)) {
    console.log(`${String(count).padStart(3)}  ${name}`);
  }
}
