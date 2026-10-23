# Run the exercises' tests in both languages.
#   make -k test         your starters, both languages (EX=02 for one exercise)
#   make test-python     your Python starters only
#   make test-js         your JavaScript starters only
#   make solutions       every reference solution, both languages
#   make check           solutions pass and starters still fail (what CI runs)
#   make mutants         wrong solutions that the tests must reject
#   make smoke           the live test in both languages (needs LIVETENNISAPI_KEY,
#                        about 6 requests; smoke-python or smoke-js for one language)

PYTHON ?= python3
NODE ?= node
EX ?=

.PHONY: test test-python test-js solutions solutions-python solutions-js check-starters check mutants smoke smoke-python smoke-js

test: test-python test-js

test-python:
	$(PYTHON) scripts/run_python_tests.py $(EX)

test-js:
	$(NODE) scripts/run-js-tests.mjs $(EX)

solutions: solutions-python solutions-js

solutions-python:
	$(PYTHON) scripts/run_python_tests.py --solutions $(EX)

solutions-js:
	$(NODE) scripts/run-js-tests.mjs --solutions $(EX)

check-starters:
	$(PYTHON) scripts/check_starters_fail.py

check: solutions check-starters

mutants:
	$(PYTHON) mutants/run_mutants.py

smoke: smoke-python smoke-js

smoke-python:
	LIVE=1 $(PYTHON) scripts/run_python_tests.py --smoke

smoke-js:
	LIVE=1 $(NODE) scripts/run-js-tests.mjs --smoke
