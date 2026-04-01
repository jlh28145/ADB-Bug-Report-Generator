# ADB Bug Report Generator

## Overview

ADB Bug Report Generator is a CLI-driven Android diagnostics utility for collecting troubleshooting artifacts from connected devices with ADB and packaging them into a predictable archive.

It is built for repeatable debugging workflows where the goal is not just "grab some logs," but:

* detect what kind of device is connected
* collect the artifacts that make sense for that device
* explain what was skipped, failed, or degraded
* preserve metadata so the run is reviewable later

---

## Why This Repo Matters

This project demonstrates practical system-level QA automation for Android-based workflows.

It is not just a wrapper around `adb`. It shows how to build a diagnostics tool that:

* profiles a target device before collection
* adapts to compatibility constraints instead of failing blindly
* records skipped, failed, and degraded steps explicitly
* produces reviewable output with structured metadata
* enforces quality through linting, tests, coverage, packaging, and CI

For reviewers, this repo demonstrates:

* Python automation design
* CLI workflow design
* Android / ADB-based diagnostics
* compatibility-aware system testing
* failure handling and degraded-mode behavior
* CI/CD and test strategy discipline

---

## Key Capabilities

* explicit connected-device discovery and targeting
* startup device profiling (Android version, SDK, emulator state, root availability, shell support)
* compatibility-aware collection with explicit skip and degradation reporting
* diagnostics capture (logcat, device info, storage, network, battery, activity/event state, optional package data)
* structured output with `metadata.json`, `run_summary.txt`, and timestamped archive packaging
* quality enforcement through linting, testing, coverage, packaging checks, and GitHub Actions

---

## Quick Start

Use `adb devices` to find your target device serial.

python3 -m venv .venv
source .venv/bin/activate
.venv/bin/pip install -r requirements.txt

PYTHONPATH=src .venv/bin/python -m adb_bug_report_generator --help

Example run:

PYTHONPATH=src .venv/bin/python -m adb_bug_report_generator \
--device DEVICE_SERIAL \
--incident-summary "Field issue review" \
--non-interactive \
--output-dir output/basic-review

---

## CLI Examples

Basic physical-device run:

PYTHONPATH=src .venv/bin/python -m adb_bug_report_generator \
--device DEVICE_SERIAL \
--incident-summary "Field issue reproduction review" \
--non-interactive \
--output-dir output/basic-review

Full review with package diagnostics and Android-generated bugreport:

PYTHONPATH=src .venv/bin/python -m adb_bug_report_generator \
--device DEVICE_SERIAL \
--incident-summary "Full manual validation review" \
--non-interactive \
--include-bugreport \
--package your.package.name \
--output-dir output/full-review

Emulator-targeted run:

PYTHONPATH=src .venv/bin/python -m adb_bug_report_generator \
--device emulator-5554 \
--allow-emulator \
--incident-summary "Emulator smoke validation" \
--non-interactive \
--output-dir output/emulator-review


---

## Example Output

output/
QA_bug_report_20260401_101530.zip
run_summary.txt
metadata.json
bugreport.zip
Device Info/
logcat.txt
device_info.txt
battery_info.txt
network_config.txt

The archive includes both collected artifacts and structured metadata so each run is reviewable, including skipped or degraded steps.

---

## Test Strategy

This repo follows a pragmatic test pyramid:

* Unit tests: collector logic, compatibility decisions, filesystem behavior
* Integration tests: CLI orchestration and ADB interaction simulation
* End-to-end (opt-in): emulator-backed smoke validation
* Manual validation: real-device verification

GitHub Actions enforces:

* Ruff linting
* Black formatting checks
* pytest execution
* coverage threshold (70%+)
* package build validation
* import validation
* pre-commit hooks

---

## Validation Coverage

### Emulator Testing

Opt-in emulator smoke test:

ADB_RUN_EMULATOR_SMOKE=1 \
ADB_EMULATOR_SERIAL=emulator-5554 \
.venv/bin/pytest tests/e2e/test_emulator_smoke.py -q

Validates:

* device targeting
* device profiling
* log collection
* packaging

---

### Real Device Support

Validated on:

* PANASONIC FZ-S1 (Android 11 / SDK 30)
* NUU S6304L (Android 13 / SDK 33)

Supports:

* non-root diagnostics
* package-level diagnostics
* variability across device states

---

## Architecture

Core modules:

* cli.py: CLI parsing and orchestration
* adb.py: ADB abstraction, retries, timeouts, command handling
* collector.py: artifact collection workflow
* compatibility.py: device profiling and decision logic
* filesystem.py: output generation and archive packaging

High-level flow:

1. Parse CLI arguments
2. Detect and select device
3. Build device profile
4. Execute compatible collectors
5. Record results and metadata
6. Package final archive

---

## Compatibility and Fallback Strategy

The tool adapts to device constraints instead of failing blindly.

Includes:

* emulator vs physical detection
* root availability detection
* command availability checks (getprop, dumpsys, logcat, etc.)
* fallback strategies (ifconfig → ip addr)
* explicit skip reasons for unsupported collectors

Modes:

* auto: default behavior
* strict: fail early
* permissive: prefer degraded execution

---

## Failure Handling

Explicit failure handling includes:

* missing adb
* no connected devices
* unauthorized/offline devices
* invalid selections
* emulator boot incomplete
* root-required constraints
* partial failure detection

Exit codes:

* 0: success
* 2: partial failure (--fail-on-partial)
* 3–8: specific failure conditions

---

## Sensitive Data

Generated artifacts may contain:

* device state
* logs
* application data

Safeguards:

* opt-in bugreport collection
* opt-in protected-path diagnostics
* metadata sanitization
* filename sanitization

Treat outputs as sensitive.

---

## Current Limitations and Tradeoffs

* rooted-device validation not yet implemented
* device outputs vary based on available data
* emulator coverage is intentionally minimal
* some collectors depend on device-specific shell behavior

This project focuses on practical diagnostics automation, not full device lab orchestration.
