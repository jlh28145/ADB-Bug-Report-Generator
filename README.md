# ADB Bug Report Generator

## Overview
ADB Bug Report Generator is a CLI-driven Android diagnostics utility for collecting troubleshooting artifacts from connected devices using ADB.

The project is designed to support repeatable debugging workflows by:
- collecting standardized diagnostic outputs
- packaging artifacts into a predictable archive layout
- recording device capabilities and run metadata
- supporting both operator-driven and automation-friendly usage

## Current Capabilities
The current implementation can:
- detect connected devices and prompt for selection when needed
- collect a device profile at startup
- detect:
  - device serial
  - model
  - manufacturer
  - Android version
  - SDK level
  - emulator status
  - root availability
  - accessible app paths
  - available shell commands
- collect:
  - logcat
  - device information
  - optional package diagnostics
  - optional bugreport
  - selected recent files and directories from device storage
- apply compatibility-aware command fallbacks for some collectors
- write a structured output bundle with:
  - `run_summary.txt`
  - `metadata.json`
  - standardized artifact filenames

## Prerequisites
1. Install Python 3.9 or newer.
2. Install Android Debug Bridge (`adb`) and make sure it is on your `PATH`.
3. Enable Developer Options and USB debugging on the Android device.
4. Verify device connectivity:

```bash
adb devices
```

## Installation
Create and activate the local virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install test tooling:

```bash
.venv/bin/pip install -r requirements.txt
```

You can run the compatibility wrapper directly:

```bash
python3 generate_bug_report.py
```

Or run the packaged entry point:

```bash
PYTHONPATH=src .venv/bin/python -m adb_bug_report_generator
```

In restricted or offline environments, editable install may require local packaging tools already present in the virtual environment.

## Usage
Basic example:

```bash
python3 generate_bug_report.py \
  --device emulator-5554 \
  --allow-emulator \
  --incident-summary "Login flow failure on emulator" \
  --include-bugreport \
  --package com.example.app \
  --output-dir output
```

Automation-friendly example:

```bash
python3 generate_bug_report.py \
  --device emulator-5554 \
  --allow-emulator \
  --incident-summary "Nightly smoke failure" \
  --non-interactive \
  --fail-on-partial \
  --output-dir output
```

### CLI Flags
- `--device`: Use a specific connected device serial instead of prompting.
- `-n`, `--num-recent-files`: Number of recent files to pull from configured directories.
- `-s`, `--simplified`: Skip broad directory pulls.
- `--no-include-logcat`: Skip logcat collection.
- `--no-include-device-info`: Skip device-info and diagnostic text collection.
- `--include-bugreport`: Include bugreport collection when supported.
- `--incident-summary`: Supply the incident summary without prompting.
- `--non-interactive`: Disable interactive prompts.
- `--fail-on-partial`: Return a non-zero exit code when any artifact collection step fails.
- `--package`: Collect package diagnostics for a specific Android package.
- `--allow-emulator`: Permit collection from an emulator target.
- `--require-root`: Fail fast unless the selected device appears to have root available.
- `--compat-mode`: Choose `auto`, `strict`, or `permissive` target validation behavior.
- `--timeout`: Set the ADB command timeout in seconds.
- `--output-dir`: Set the local output directory.
- `--verbose`: Enable verbose logging.

## Output Structure
Each run produces a timestamped archive containing standardized files such as:

```text
output/
  QA_bug_report_<timestamp>.zip
```

Inside the zip:

```text
run_summary.txt
metadata.json
bugreport.zip
Device Info/
  logcat.txt
  device_info.txt
  network_config.txt
  package_diagnostics.txt
Screen Recordings/
Navsuite Logs/
Pictures/
Movies/
```

`metadata.json` includes:
- incident summary
- timestamp
- selected device
- detected device profile
- selected CLI options
- artifact-level collected/skipped/failed status

## Compatibility Behavior
The current implementation already makes some capability-aware decisions:
- detects emulator vs physical-device signals
- detects emulator boot-complete state
- records root availability
- records available shell commands
- skips unsupported collectors with explicit reasons
- prefers standard non-root diagnostics first and adds protected-path diagnostics only when root is available
- falls back from `getprop` to `dumpsys` for device-info collection when needed
- skips hardware-oriented battery diagnostics on emulator targets
- uses older-shell fallbacks for selected collectors on legacy Android SDK levels
- uses command fallback for network configuration collection when `ifconfig` is unavailable and `ip addr` is available

Compatibility policy modes:
- `auto`: default behavior, with normal guardrails such as requiring `--allow-emulator` for emulator targets
- `strict`: fail before collection starts if requested collectors are clearly unsupported on the target device
- `permissive`: allow emulator targets without `--allow-emulator` and prefer degraded collection over early rejection

This is the foundation for broader Android-version and root-aware fallback behavior in later phases.

## Testing Strategy
This repo follows the QA testing pyramid:
- unit tests in `tests/unit/`
- integration tests in `tests/integration/`
- end-to-end placeholders in `tests/e2e/`

Current local test command:

```bash
.venv/bin/python -m pytest
```

The current suite covers:
- collector selection logic
- filesystem/output behavior
- device capability detection
- CLI orchestration with fake ADB clients
- partial-failure handling
- explicit exit-code behavior
- operator-facing failure messages
- fallback command behavior
- optional package diagnostics

## Error Handling
Current operator-facing failure handling includes:
- missing `adb`
- no connected device
- unauthorized device
- offline device
- invalid multi-device selection
- non-interactive mode without enough information to proceed
- emulator boot incomplete
- emulator target rejected unless `--allow-emulator` is set
- root-required runs on non-rooted devices
- strict compatibility rejection for unsupported requested collectors
- partial failure exit behavior when `--fail-on-partial` is enabled

Current exit codes:
- `0`: successful run
- `2`: partial collection failure with `--fail-on-partial`
- `3`: no connected device available
- `4`: `adb` executable unavailable
- `5`: ADB command timeout
- `6`: connected device blocked by authorization or offline state
- `7`: emulator detected before Android boot completed
- `8`: invalid operator input or compatibility constraint rejection

## Scope
This project is intentionally focused on:
- Android diagnostics collection
- artifact packaging
- troubleshooting workflows

Out of scope:
- performance benchmarking
- battery or thermal testing
- full end-to-end QA automation
