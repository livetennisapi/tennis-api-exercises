#!/usr/bin/env node
// Run the JavaScript tests with node:test.
//
//   node scripts/run-js-tests.mjs                 your starters, every exercise
//   node scripts/run-js-tests.mjs 02 05           only exercises 02 and 05
//   node scripts/run-js-tests.mjs --solutions     the reference solutions
//   node scripts/run-js-tests.mjs --smoke         the live smoke test (needs LIVE=1)
//
// An exercise is named by its number (2 or 02) or its folder (02-read-a-score).
// It works the same on Linux, macOS and Windows.

import { existsSync, readdirSync } from 'node:fs';
import { join, relative } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('..', import.meta.url));
const FLAGS = new Set(['--solutions', '--smoke']);
const args = process.argv.slice(2);
const flags = new Set(args.filter((arg) => arg.startsWith('-')));
const filters = args.filter((arg) => !arg.startsWith('-'));

function fail(message) {
  console.error(`${message}\nUsage: node scripts/run-js-tests.mjs [--solutions | --smoke] [exercise number ...]`);
  process.exit(2);
}

const unknown = [...flags].filter((flag) => !FLAGS.has(flag));
if (unknown.length) fail(`Unknown option: ${unknown.join(', ')}`);

const testsIn = (dir) => readdirSync(dir).filter((name) => name.endsWith('.test.mjs')).map((name) => join(dir, name));

let files;
if (flags.has('--smoke')) {
  if (filters.length || flags.has('--solutions')) fail('--smoke takes no other arguments.');
  files = testsIn(join(root, 'smoke'));
} else {
  const folders = readdirSync(join(root, 'exercises'), { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();
  let chosen = folders;
  if (filters.length) {
    chosen = [];
    for (const wanted of filters) {
      const hits = folders.filter((name) => name === wanted || (/^\d+$/.test(wanted) && name.split('-')[0] === wanted.padStart(2, '0')));
      if (hits.length === 0) fail(`No exercise called "${wanted}".`);
      for (const hit of hits) if (!chosen.includes(hit)) chosen.push(hit);
    }
    chosen.sort();
  }
  if (flags.has('--solutions')) {
    const missing = chosen.filter((name) => !existsSync(join(root, 'exercises', name, 'solutions', 'js', 'solution.mjs')));
    if (missing.length) fail(`No JavaScript solution in: ${missing.join(', ')}. This copy may have had them removed.`);
  }
  files = chosen.flatMap((name) => testsIn(join(root, 'exercises', name, 'js')));
}
files = files.map((path) => relative(root, path));
if (files.length === 0) fail('No test files found.');

const env = { ...process.env };
if (flags.has('--solutions')) env.SOLUTION = '1';
else delete env.SOLUTION;
const result = spawnSync(process.execPath, ['--test', ...files], { cwd: root, env, stdio: 'inherit' });
process.exit(result.status ?? 1);
