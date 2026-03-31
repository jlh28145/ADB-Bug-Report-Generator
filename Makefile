PYTHON := .venv/bin/python
PIP := .venv/bin/pip
PYTEST := .venv/bin/pytest
RUFF := .venv/bin/ruff
BLACK := .venv/bin/black
MYPY := .venv/bin/mypy
PRE_COMMIT := .venv/bin/pre-commit

.PHONY: help install run test lint format typecheck precommit validate smoke build

help:
	@printf "Available targets:\n"
	@printf "  install    Install development dependencies\n"
	@printf "  run        Show CLI help through the packaged module entry point\n"
	@printf "  test       Run pytest\n"
	@printf "  lint       Run Ruff and Black checks\n"
	@printf "  format     Apply Ruff import fixes and Black formatting\n"
	@printf "  typecheck  Run mypy\n"
	@printf "  precommit  Run pre-commit across all files\n"
	@printf "  smoke      Run the opt-in emulator smoke test\n"
	@printf "  build      Build the package\n"
	@printf "  validate   Run the full local validation flow\n"

install:
	$(PIP) install -r requirements.txt

run:
	PYTHONPATH=src $(PYTHON) -m adb_bug_report_generator --help

test:
	$(PYTEST)

lint:
	$(RUFF) check .
	$(BLACK) --check src tests generate_bug_report.py

format:
	$(RUFF) check . --fix
	$(BLACK) src tests generate_bug_report.py

typecheck:
	$(MYPY) src/adb_bug_report_generator

precommit:
	PRE_COMMIT_HOME=/tmp/pre-commit-cache $(PRE_COMMIT) run --all-files

smoke:
	ADB_RUN_EMULATOR_SMOKE=1 ADB_EMULATOR_SERIAL=emulator-5554 $(PYTEST) tests/e2e/test_emulator_smoke.py -q

build:
	$(PYTHON) -m build --no-isolation

validate:
	$(RUFF) check .
	$(BLACK) --check src tests generate_bug_report.py
	$(PYTEST) --cov=adb_bug_report_generator --cov-report=term-missing --cov-report=xml
	$(MYPY) src/adb_bug_report_generator
	$(PYTHON) -m build --no-isolation
	PYTHONPATH=src $(PYTHON) -c "import adb_bug_report_generator"
