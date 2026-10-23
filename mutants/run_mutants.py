#!/usr/bin/env python3
"""Apply each wrong solution in catalog.py and check that the tests reject it.

For every exercise and language, the unmodified solution runs first and must
pass all its tests. That baseline also fixes how many tests should run. Then,
for every mutant, the edits go into a scratch copy and the same tests run
with SOLUTION=1.

- killed:    the same number of tests ran and at least one failed
- killed (hang): the tests did not finish in 60 s (a loop that never stops)
- SURVIVED:  every test passed, so the tests missed the mistake
- ERROR:     anything else (a tool missing, a load or collection error, a
             different test count). It proves nothing and is never a kill.
- BROKEN:    the code a mutant edits has changed, so it no longer applies

Exit 0 only when every baseline passed and every mutant was killed.

    python3 mutants/run_mutants.py            every mutant
    python3 mutants/run_mutants.py 06 08      only exercises 06 and 08
"""

import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mutants"))
from catalog import MUTANTS  # noqa: E402


def run_tests(workdir, exercise, lang):
    """Return (status, tests, failed). status is 'ok', 'failed', 'hang' or 'error'."""
    env = dict(os.environ, SOLUTION="1")
    folder = workdir / "exercises" / exercise
    if lang == "py":
        command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(folder / "python")]
    else:
        command = ["node", "--test", "--test-reporter=tap", *map(str, sorted((folder / "js").glob("*.test.mjs")))]
    try:
        run = subprocess.run(command, cwd=workdir, env=env, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return "hang", None, None
    except OSError:
        return "error", None, None
    out = run.stdout + run.stderr
    if lang == "py":
        def count(word):
            found = re.search(rf"(\d+) {word}\b", out)
            return int(found[1]) if found else 0
        passed, failed, errors = count("passed"), count("failed"), count("errors?")
        if run.returncode == 0 and passed and not failed and not errors:
            return "ok", passed, 0
        if run.returncode == 1 and failed and not errors:
            return "failed", passed + failed, failed
        return "error", None, None
    tests = re.search(r"^# tests (\d+)", out, re.M)
    failed = re.search(r"^# fail (\d+)", out, re.M)
    if not tests or not failed:
        return "error", None, None
    tests, failed = int(tests[1]), int(failed[1])
    if run.returncode == 0 and tests and not failed:
        return "ok", tests, 0
    if run.returncode != 0 and failed:
        return "failed", tests, failed
    return "error", None, None


def prepare(scratch, name, exercise):
    workdir = scratch / name
    shutil.copytree(ROOT / "fixtures", workdir / "fixtures")
    shutil.copytree(ROOT / "exercises" / exercise, workdir / "exercises" / exercise)
    return workdir


def main(argv):
    wanted = [arg.zfill(2) for arg in argv]
    selected = [mt for mt in MUTANTS if not wanted or mt["exercise"][:2] in wanted]
    counts = {"killed": 0, "survived": 0, "error": 0, "broken": 0}
    with tempfile.TemporaryDirectory() as scratch:
        scratch = pathlib.Path(scratch)
        baselines = {}
        for exercise, lang in sorted({(mt["exercise"], mt["lang"]) for mt in selected}):
            status, tests, _ = run_tests(prepare(scratch, f"base-{exercise}-{lang}", exercise), exercise, lang)
            if status == "ok":
                baselines[(exercise, lang)] = tests
                print(f"baseline  {exercise[:2]} {lang:2}  {tests} tests pass")
            else:
                print(f"ERROR     {exercise[:2]} {lang:2}  the unmodified solution does not pass ({status}); its mutants are skipped")
        for index, mutant in enumerate(selected):
            label = f"{mutant['exercise'][:2]} {mutant['lang']:2}  {mutant['name']}"
            expected = baselines.get((mutant["exercise"], mutant["lang"]))
            if expected is None:
                counts["error"] += 1
                print(f"ERROR     {label} (no passing baseline)")
                continue
            workdir = prepare(scratch, str(index), mutant["exercise"])
            target = workdir / "exercises" / mutant["exercise"] / mutant["file"]
            text = target.read_text(encoding="utf-8")
            applies = True
            for find, replace in mutant["edits"]:
                if text.count(find) != 1:
                    applies = False
                    break
                text = text.replace(find, replace)
            if not applies:
                counts["broken"] += 1
                print(f"BROKEN    {label} (the code it edits has changed)")
                continue
            target.write_text(text, encoding="utf-8")
            status, tests, failed = run_tests(workdir, mutant["exercise"], mutant["lang"])
            if status == "hang":
                counts["killed"] += 1
                print(f"killed    {label} (hang)")
            elif status == "failed" and tests == expected:
                counts["killed"] += 1
                print(f"killed    {label} ({failed} of {tests} tests fail)")
            elif status == "ok":
                counts["survived"] += 1
                print(f"SURVIVED  {label}")
            else:
                counts["error"] += 1
                print(f"ERROR     {label} (status {status}, {tests} tests where {expected} were expected)")
            shutil.rmtree(workdir)
    print(f"\n{counts['killed']} of {len(selected)} mutants killed, {counts['survived']} survived, "
          f"{counts['error']} errors, {counts['broken']} no longer apply.")
    ok = len(baselines) == len({(mt['exercise'], mt['lang']) for mt in selected}) and selected
    return 0 if ok and counts["killed"] == len(selected) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
