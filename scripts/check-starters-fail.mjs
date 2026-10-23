#!/usr/bin/env node
// Check that every JavaScript starter fails its tests for the right reason.
//
// The starters are exercises, so every test must fail. A starter that passes
// means a solution leaked into it. A failure for the wrong reason (a broken
// import, a missing test file) would make the check prove nothing, so:
// - the same test files run against the solution first, and must all pass;
// - the starter run must report the same number of tests, none passing;
// - the starter output must show the "not implemented" placeholder.
// Exit 0 only when every exercise was checked and is sound.

import { readdirSync } from 'node:fs';
import { join, relative } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('..', import.meta.url));
if (process.argv.length > 2) {
  console.error('Usage: node scripts/check-starters-fail.mjs (it takes no arguments)');
  process.exit(2);
}

const folders = readdirSync(join(root, 'exercises'), { withFileTypes: true })
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name)
  .sort();
if (folders.length === 0) {
  console.error('No exercises found.');
  process.exit(2);
}

const env = { ...process.env };
delete env.SOLUTION;
const problems = [];
let checked = 0;
for (const name of folders) {
  const dir = join(root, 'exercises', name, 'js');
  let files = [];
  try {
    files = readdirSync(dir).filter((file) => file.endsWith('.test.mjs')).map((file) => relative(root, join(dir, file)));
  } catch {
    files = [];
  }
  if (files.length === 0) {
    problems.push(`${name}: no JavaScript test file`);
    continue;
  }
  const run = (solution) => {
    const result = spawnSync(process.execPath, ['--test', '--test-reporter=tap', ...files], {
      cwd: root,
      env: solution ? { ...env, SOLUTION: '1' } : env,
      encoding: 'utf8',
    });
    const out = `${result.stdout}\n${result.stderr}`;
    const count = (label) => Number(new RegExp(`^# ${label} (\\d+)`, 'm').exec(out)?.[1] ?? -1);
    return { status: result.status, out, tests: count('tests'), pass: count('pass'), fail: count('fail') };
  };
  const reference = run(true);
  if (reference.status !== 0 || reference.tests <= 0 || reference.pass !== reference.tests) {
    problems.push(`${name}: the solution does not pass its own tests, so the starter cannot be checked`);
    continue;
  }
  const starter = run(false);
  if (starter.status === 0) problems.push(`${name}: the starter passes its tests`);
  else if (starter.tests !== reference.tests) {
    problems.push(`${name}: ${starter.tests} tests ran on the starter but ${reference.tests} on the solution (a load error?)`);
  } else if (starter.pass !== 0) problems.push(`${name}: ${starter.pass} of ${starter.tests} tests pass on the starter`);
  else if (!starter.out.includes('not implemented')) problems.push(`${name}: no failure mentions "not implemented"`);
  else checked += 1;
}
for (const problem of problems) console.log(problem);
if (problems.length) process.exit(1);
console.log(`Every JavaScript starter fails its tests, as it should (${checked} exercises).`);
