# ADB Bug Report Generator

## Overview
ADB Bug Report Generator is a Python-based Android diagnostics collector for troubleshooting workflows. The current repo packages common ADB artifacts, selected device files, and incident notes into a timestamped archive so engineers or QA can review a single bundle after a run.

This project is being upgraded from a one-off script into a cleaner CLI-driven tool. The current implementation is still script-first, but the repo direction is now explicit:

- Collect Android diagnostics using ADB
- Package debugging artifacts consistently
- Support repeatable troubleshooting workflows

## Current Behavior
Today the repo provides a single script, [generate_bug_report.py](/home/vhinson/dev/ADB-Bug-Report-Generator/generate_bug_report.py), that:

- Detects connected Android devices with ADB
- Prompts the user to choose a device if more than one is connected
- Pulls selected media and app log directories from device storage
- Collects device diagnostics such as `logcat`, `getprop`, `dumpsys`, `top`, and storage info
- Writes results into a timestamped local report folder
- Creates a zip archive containing the collected artifacts and user-provided incident summary

## Current Limitations
This script is still an early implementation and has a few important constraints:

- It assumes `adb` is installed and available on `PATH`
- It depends on an interactive terminal for device selection and incident summary input
- Several collection targets are hardcoded for a specific workflow
- The bugreport collection function exists in code but is not currently enabled in the main flow
- Error handling is basic and not yet standardized

## Out of Scope
The intended repo scope does not include:

- Performance benchmarking
- Battery or thermal test automation
- Full end-to-end QA automation

## Prerequisites
1. Install Python 3.7 or newer.
2. Install Android Debug Bridge (`adb`) and make sure it is available on your `PATH`.
3. Enable Developer Options and USB debugging on the Android device.
4. Verify connectivity with:

```bash
adb devices
```

## Usage
Run the current script directly:

```bash
python generate_bug_report.py
```

Optional arguments:

- `-n`, `--num_recent_files`: Number of recent files to pull from configured directories. Default is `5`.
- `-s`, `--simplified`: Skip the broad directory pulls and create a smaller report.

Example:

```bash
python generate_bug_report.py -n 3 -s
```

## Current Output
The script writes into `incident_reports/` and creates a timestamped zip archive for each run. The internal folder structure currently includes directories such as:

- `Device Info`
- `QGC Logs`
- `Screen Recordings`
- `Navsuite Logs`

This layout will be standardized in later phases of the roadmap.

## Roadmap
The planned next steps are documented in [todo.md](/home/vhinson/dev/ADB-Bug-Report-Generator/todo.md). Phase 0 defines the repo identity, and Phase 1 captures the current audit so the refactor can proceed from a clear baseline.
