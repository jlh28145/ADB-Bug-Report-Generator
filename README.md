# ADB Bug Report Generator

## Overview
ADB Bug Report Generator is a CLI-driven Android diagnostics utility for collecting troubleshooting artifacts from connected devices with ADB and packaging them into a predictable archive.

It is built for repeatable debugging workflows where the goal is not just "grab some logs," but:
- detect what kind of device is connected
- collect the artifacts that make sense for that device
- explain what was skipped, failed, or degraded
- preserve metadata so the run is reviewable later

## Features
- CLI-driven collection flow with interactive or automation-friendly usage
- connected-device discovery with explicit device targeting
- startup device profiling for model, manufacturer, Android version, SDK level, emulator state, root availability, accessible paths, and available shell commands
- compatibility-aware collection decisions with explicit skip reasons
- standard diagnostics including logcat, device info, storage, network, battery, activity/event state, and optional package diagnostics
- optional Android-generated `adb bugreport` collection
- structured output with `metadata.json` and `run_summary.txt`
- coverage-backed test pyramid with unit, integration, and opt-in emulator smoke coverage
- GitHub Actions quality gates for lint, tests, coverage, build, import validation, and emulator smoke execution

## Use Case
This tool is useful when a team needs a repeatable Android diagnostics bundle instead of an ad hoc checklist.

Examples:
- QA or support needs a standard package for investigating a field issue
- an engineer wants non-interactive collection in a scripted workflow
- emulator and physical-device troubleshooting need to share one CLI surface
- a repo wants to demonstrate practical ADB automation with compatibility and failure handling built in

## Prerequisites and Setup
1. Install Python 3.10 or newer.
2. Install Android Platform Tools and ensure `adb` is on your `PATH`.
3. Enable Developer Options and USB debugging on the target device or start an Android emulator.
4. Verify connectivity:

```bash
adb devices
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
.venv/bin/pip install -r requirements.txt
```

Run the compatibility wrapper:

```bash
python3 generate_bug_report.py --help
```

Or run the packaged module entry point:

```bash
PYTHONPATH=src .venv/bin/python -m adb_bug_report_generator --help
```

Contributor-focused setup, emulator onboarding, and troubleshooting live in [CONTRIBUTING.md](/home/vhinson/dev/ADB-Bug-Report-Generator/CONTRIBUTING.md).

## CLI Examples
Basic physical-device run:

```bash
PYTHONPATH=src .venv/bin/python -m adb_bug_report_generator \
  --device 2BKHA09608 \
  --incident-summary "Field issue reproduction review" \
  --non-interactive \
  --output-dir output/basic-review
```

Full review with package diagnostics and Android-generated bugreport:

```bash
PYTHONPATH=src .venv/bin/python -m adb_bug_report_generator \
  --device 2BKHA09608 \
  --incident-summary "Full manual validation review" \
  --non-interactive \
  --include-bugreport \
  --package ai.pdw.gcs \
  --output-dir output/full-review
```

Emulator-targeted run:

```bash
PYTHONPATH=src .venv/bin/python -m adb_bug_report_generator \
  --device emulator-5554 \
  --allow-emulator \
  --incident-summary "Emulator smoke validation" \
  --non-interactive \
  --output-dir output/emulator-review
```

Key CLI flags:
- `--device`: target a specific connected device
- `--non-interactive`: disable prompts for scripted runs
- `--include-bugreport`: include Android-generated `adb bugreport`
- `--package`: collect diagnostics for a specific package
- `--allow-emulator`: permit collection on emulator targets
- `--require-root`: fail if root is required but unavailable
- `--include-protected-paths`: explicitly allow root-enhanced protected-path diagnostics
- `--simplified`: skip broad directory pulls
- `--fail-on-partial`: return a non-zero exit code when any collection step fails
- `--compat-mode`: choose `auto`, `strict`, or `permissive`
- `--timeout`: set the normal ADB command timeout in seconds

## Output Structure
Each run produces a timestamped archive:

```text
output/
  QA_bug_report_<timestamp>.zip
```

Typical archive contents:

```text
run_summary.txt
metadata.json
bugreport.zip
Device Info/
  logcat.txt
  device_info.txt
  cpu_usage.txt
  network_config.txt
  network_stats.txt
  storage_info.txt
  battery_info.txt
  event_logs.txt
  package_diagnostics.txt
QGC Logs/
Navsuite Logs/
Screen Recordings/
Pictures/
Movies/
```

`metadata.json` records:
- timestamp and incident summary
- selected device
- detected device profile
- selected CLI options
- artifact-level status for collected, skipped, or failed steps

This makes the archive reviewable even when a device only supports a subset of the collectors.

## Testing
The repo follows a pragmatic test pyramid:
- unit tests in `tests/unit/` for collector logic, filesystem behavior, and compatibility decisions
- integration tests in `tests/integration/` for CLI orchestration and fake ADB interactions
- opt-in end-to-end coverage in `tests/e2e/` for emulator-backed smoke validation and real-device checklists

Common local commands:

```bash
make test
make lint
make validate
```

Direct equivalents:

```bash
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/black --check src tests generate_bug_report.py
.venv/bin/pytest --cov=adb_bug_report_generator --cov-report=term-missing --cov-report=xml
.venv/bin/mypy src/adb_bug_report_generator
```

Supporting docs:
- [CONTRIBUTING.md](/home/vhinson/dev/ADB-Bug-Report-Generator/CONTRIBUTING.md)
- [examples/README.md](/home/vhinson/dev/ADB-Bug-Report-Generator/examples/README.md)
- [tests/integration/README.md](/home/vhinson/dev/ADB-Bug-Report-Generator/tests/integration/README.md)
- [tests/e2e/README.md](/home/vhinson/dev/ADB-Bug-Report-Generator/tests/e2e/README.md)
- [tests/e2e/manual_validation_checklist.md](/home/vhinson/dev/ADB-Bug-Report-Generator/tests/e2e/manual_validation_checklist.md)

## Emulator Testing
The repo includes an opt-in emulator smoke test in [test_emulator_smoke.py](/home/vhinson/dev/ADB-Bug-Report-Generator/tests/e2e/test_emulator_smoke.py).

Run it locally with:

```bash
ADB_RUN_EMULATOR_SMOKE=1 \
ADB_EMULATOR_SERIAL=emulator-5554 \
.venv/bin/pytest tests/e2e/test_emulator_smoke.py -q
```

Recommended local emulator baseline:
- Android Studio Device Manager
- `x86_64` image
- API level 30 or newer
- emulator fully booted before the smoke test starts

Useful readiness check:

```bash
adb devices
adb -s emulator-5554 shell getprop sys.boot_completed
```

The smoke test validates:
- explicit device targeting
- device profile detection
- logcat capture
- device-info capture
- final zip packaging

The GitHub Actions workflow also runs the emulator smoke job automatically on `push` to `main`, and it can be launched manually with `workflow_dispatch`.

## Real Device Support
Real-device validation has been exercised on non-root hardware and documented in [manual_validation_checklist.md](/home/vhinson/dev/ADB-Bug-Report-Generator/tests/e2e/manual_validation_checklist.md).

Observed physical-device validation summary:
- `PANASONIC FZ-S1` on Android `11` / SDK `30`
  - successful non-root run
  - populated app/media directories
  - package diagnostics succeeded for `ai.pdw.gcs`
  - full review succeeded with `bugreport.zip`
- `NUU S6304L` on Android `13` / SDK `33`
  - successful non-root run
  - diagnostics and `bugreport.zip` collected successfully
  - no matching app/media directories were present, so the archive was diagnostics-focused

What that means in practice:
- the tool supports both content-rich and diagnostics-only device states
- physical-device output can vary substantially based on what is actually present on-device
- rooted-device enhanced validation is still intentionally deferred

Sanitized demo material is available in [examples/README.md](/home/vhinson/dev/ADB-Bug-Report-Generator/examples/README.md).

## Compatibility and Fallback Strategy
The tool builds a device profile before collection starts and uses that profile to decide what to collect and what to skip.

Current compatibility behavior includes:
- detecting emulator vs physical-device targets
- detecting emulator boot-complete state
- recording root availability
- detecting accessible application directories
- recording available shell commands such as `getprop`, `dumpsys`, `logcat`, `bugreport`, `ifconfig`, `ip`, and `top`
- skipping unsupported collectors with explicit reasons
- preferring standard non-root diagnostics first
- requiring explicit opt-in before protected-path diagnostics are attempted
- falling back from `getprop` to `dumpsys` for device info when needed
- falling back from `ifconfig` to `ip addr` for network configuration when appropriate
- applying older-shell fallbacks for selected collectors on legacy Android SDK levels

Compatibility modes:
- `auto`: default guardrails and normal degraded behavior
- `strict`: fail early if requested collectors are clearly unsupported
- `permissive`: prefer degraded collection over early rejection

## Architecture
The project is organized around a few focused modules:
- [cli.py](/home/vhinson/dev/ADB-Bug-Report-Generator/src/adb_bug_report_generator/cli.py): argument parsing, orchestration, operator-facing flow
- [adb.py](/home/vhinson/dev/ADB-Bug-Report-Generator/src/adb_bug_report_generator/adb.py): ADB abstraction, structured command results, timeout behavior, retry handling, and exception mapping
- [collector.py](/home/vhinson/dev/ADB-Bug-Report-Generator/src/adb_bug_report_generator/collector.py): collection workflow, artifact handling, and compatibility-aware collector execution
- [compatibility.py](/home/vhinson/dev/ADB-Bug-Report-Generator/src/adb_bug_report_generator/compatibility.py): device profiling and compatibility decisions
- [filesystem.py](/home/vhinson/dev/ADB-Bug-Report-Generator/src/adb_bug_report_generator/filesystem.py): output creation, metadata writing, sanitization, and archive packaging

High-level flow:
1. Parse CLI arguments and validate operator input.
2. Detect and select a device.
3. Build a device profile.
4. Run compatible collectors and record artifact-level status.
5. Write metadata and run summary.
6. Package everything into a final zip archive.

## Failure Handling
The CLI is designed to be explicit about degraded or failed collection instead of hiding it.

Current operator-facing failure handling includes:
- missing `adb`
- no connected devices
- unauthorized devices
- offline devices
- invalid multi-device selection
- non-interactive mode without enough information to proceed
- emulator boot incomplete
- emulator target rejected unless `--allow-emulator` is set
- root-required runs on non-rooted devices
- strict compatibility rejection for unsupported requested collectors
- partial-failure exit behavior when `--fail-on-partial` is enabled

Current exit codes:
- `0`: successful run
- `2`: partial collection failure with `--fail-on-partial`
- `3`: no connected device available
- `4`: `adb` executable unavailable
- `5`: ADB command timeout
- `6`: connected device blocked by authorization or offline state
- `7`: emulator detected before Android boot completed
- `8`: invalid operator input or compatibility constraint rejection

## CI Quality Gates
GitHub Actions in `.github/workflows/ci.yml` enforces the project’s basic quality gates.

The `quality` job validates:
- Ruff linting
- Black formatting checks
- pytest execution
- coverage reporting with a minimum threshold of 70%
- package build success
- packaged import validation
- pre-commit hook execution

The `emulator-smoke` job:
- runs automatically on `push` to `main`
- can be triggered manually from any branch with `workflow_dispatch`
- exercises the emulator-backed smoke path in CI

Useful local shortcuts:

```bash
make run
make test
make lint
make format
make smoke
make validate
```

## Sensitive Data
Some collectors can capture sensitive troubleshooting data, including application state, device properties, and log content.

Current safeguards:
- bugreport collection requires explicit `--include-bugreport`
- protected-path diagnostics require explicit `--include-protected-paths`
- package diagnostics require explicit `--package`
- metadata text is sanitized before writing `metadata.json`
- device-provided filenames are sanitized before being written locally

Recommended handling:
- treat generated archives as sensitive by default
- avoid sharing raw bugreports or log archives publicly without review
- prefer emulator validation or reduced collector scope when full artifact collection is unnecessary

## Current Limitations and Tradeoffs
This project is intentionally focused on practical Android diagnostics collection, not full device-lab automation.

Current limitations:
- rooted-device validation is still pending
- physical-device results vary based on what files and app data actually exist on-device
- emulator smoke coverage is intentionally small and opt-in
- some collectors depend on device-specific command availability and shell behavior
- the tool is not intended to replace broader test automation, performance benchmarking, or hardware certification workflows
