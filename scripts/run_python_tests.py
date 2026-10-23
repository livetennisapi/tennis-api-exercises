#!/usr/bin/env python3
"""Run the Python tests with pytest.

    python3 scripts/run_python_tests.py                 your starters, every exercise
    python3 scripts/run_python_tests.py 02 05           only exercises 02 and 05
    python3 scripts/run_python_tests.py --solutions     the reference solutions
    python3 scripts/run_python_tests.py --smoke         the live smoke test (needs LIVE=1)

An exercise is named by its number (2 or 02) or its folder (02-read-a-score).
It works the same on Linux, macOS and Windows.
"""

import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FLAGS = {"--solutions", "--smoke"}


def usage(message):
    print(f"{message}\n\n{__doc__.strip()}", file=sys.stderr)
    return 2


def select(folders, filters):
    chosen = []
    for wanted in filters:
        hits = [f for f in folders if f.name == wanted or (wanted.isdigit() and f.name.split("-")[0] == wanted.zfill(2))]
        if not hits:
            raise ValueError(f"No exercise called {wanted!r}.")
        chosen.extend(h for h in hits if h not in chosen)
    return sorted(chosen) if filters else folders


def main(argv):
    flags = {arg for arg in argv if arg.startswith("-")}
    if flags - FLAGS:
        return usage(f"Unknown option: {', '.join(sorted(flags - FLAGS))}")
    filters = [arg for arg in argv if not arg.startswith("-")]
    if "--smoke" in flags:
        if filters or "--solutions" in flags:
            return usage("--smoke takes no other arguments.")
        targets = ["smoke"]
    else:
        folders = sorted(path for path in (ROOT / "exercises").iterdir() if path.is_dir())
        try:
            chosen = select(folders, filters)
        except ValueError as error:
            return usage(str(error))
        if "--solutions" in flags:
            missing = [f.name for f in chosen if not (f / "solutions" / "python" / "solution.py").exists()]
            if missing:
                return usage(f"No Python solution in: {', '.join(missing)}. This copy may have had them removed.")
        targets = [str((folder / "python").relative_to(ROOT)) for folder in chosen]
    env = dict(os.environ)
    if "--solutions" in flags:
        env["SOLUTION"] = "1"
    else:
        env.pop("SOLUTION", None)
    return subprocess.call([sys.executable, "-m", "pytest", "-q", "-rs", *targets], cwd=ROOT, env=env)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
