#!/usr/bin/env python3
"""Check that every starter fails its tests, and for the right reason.

The starters are exercises, so every test must fail. A starter that passes
means a solution leaked into it. A failure for the wrong reason (a broken
import, a missing test file, pytest not installed) would make the check
prove nothing, so:
- the same tests run against the solution first, and must all pass;
- the starter run must fail exactly that many tests, with no errors;
- the starter output must show NotImplementedError.
The solutions must be present; a class copy without them has no use for it.

    python3 scripts/check_starters_fail.py            both languages
    python3 scripts/check_starters_fail.py --python   Python only
    python3 scripts/check_starters_fail.py --js       JavaScript only (runs check-starters-fail.mjs)
"""

import os
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LANGUAGES = {"--python": "python", "--js": "js"}


def run_pytest(tests, env, solution):
    env = dict(env)
    if solution:
        env["SOLUTION"] = "1"
    run = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *map(str, tests)],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )
    out = run.stdout + run.stderr

    def count(word):
        found = re.search(rf"(\d+) {word}", out)
        return int(found[1]) if found else 0

    return {"code": run.returncode, "out": out, "passed": count("passed"), "failed": count("failed"), "errors": count("errors?")}


def check_python():
    probe = subprocess.run([sys.executable, "-c", "import pytest"], capture_output=True)
    if probe.returncode != 0:
        print(f"pytest is not installed for {sys.executable}. Install it, or run this script with an interpreter that has it.")
        return None
    env = dict(os.environ)
    env.pop("SOLUTION", None)
    problems, checked = [], 0
    folders = sorted(path for path in (ROOT / "exercises").iterdir() if path.is_dir())
    if not folders:
        return ["no exercises found"]
    for folder in folders:
        tests = sorted((folder / "python").glob("test_*.py"))
        if not tests:
            problems.append(f"{folder.name}: no Python test file")
            continue
        if not (folder / "solutions" / "python" / "solution.py").exists():
            problems.append(f"{folder.name}: no Python solution to compare against")
            continue
        reference = run_pytest(tests, env, solution=True)
        if reference["code"] != 0 or reference["passed"] == 0 or reference["failed"] or reference["errors"]:
            problems.append(f"{folder.name}: the solution does not pass its own tests, so the starter cannot be checked")
            continue
        starter = run_pytest(tests, env, solution=False)
        if starter["code"] == 0:
            problems.append(f"{folder.name}: the Python starter passes its tests")
        elif starter["code"] != 1 or starter["errors"]:
            problems.append(f"{folder.name}: pytest exited {starter['code']} with {starter['errors']} errors (a load error?)")
        elif starter["passed"]:
            problems.append(f"{folder.name}: {starter['passed']} tests pass on the starter")
        elif starter["failed"] != reference["passed"]:
            problems.append(f"{folder.name}: {starter['failed']} tests failed on the starter but {reference['passed']} ran on the solution")
        elif "NotImplementedError" not in starter["out"]:
            problems.append(f"{folder.name}: no failure mentions NotImplementedError")
        else:
            checked += 1
    if not problems:
        print(f"Every Python starter fails its tests, as it should ({checked} exercises).", flush=True)
    return problems


def check_js():
    node = shutil.which("node")
    if node is None:
        print("node is not installed, so the JavaScript starters cannot be checked.")
        return None
    run = subprocess.run([node, str(ROOT / "scripts" / "check-starters-fail.mjs")], cwd=ROOT)
    return [] if run.returncode == 0 else ["the JavaScript check failed (see above)"]


def main(argv):
    unknown = [arg for arg in argv if arg not in LANGUAGES]
    if unknown:
        print(f"Unknown argument: {' '.join(unknown)}\n\n{__doc__.strip()}", file=sys.stderr)
        return 2
    languages = [LANGUAGES[arg] for arg in argv] or ["python", "js"]
    problems = []
    for language in dict.fromkeys(languages):
        result = check_python() if language == "python" else check_js()
        if result is None:
            return 2
        problems.extend(result)
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
