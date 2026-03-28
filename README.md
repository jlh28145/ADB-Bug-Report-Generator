# ADB Bug Report Generator

## Overview
This Python script automates the process of collecting various data and logs from a connected Android device using ADB (Android Debug Bridge). It organizes the collected files into a structured directory and generates a zipped bug report for further analysis.

The repo is now being restructured into a package under `src/adb_bug_report_generator/` so the CLI, ADB interactions, filesystem behavior, and collection workflow can evolve independently.

---

## Features
- Automatically detects connected Android devices.
- Allows selecting from multiple connected devices.
- Pulls specific directories and recent files from the device:
  - **Screen Recordings**
  - **QGroundControl Logs**
  - **Navsuite Logs**
- Collects detailed system information and logs, including:
  - Logcat logs
  - Device properties
  - Memory usage
  - CPU usage
  - Network stats
  - Battery information
  - Storage info
  - Event logs
- Generates an ADB bug report.
- Saves all data in a timestamped incident report folder.
- Option to zip the collected data for easy sharing or archival.

---

## Prerequisites
1. **Python Environment**: Install Python 3.7 or higher.
2. **ADB (Android Debug Bridge)**:
   - Ensure ADB is installed and available in your system's PATH.
   - Verify ADB connectivity with your device using `adb devices`.
3. **ADB Device Setup**:
   - Enable Developer Options on your Android device.
   - Enable USB Debugging.

- Collect Android diagnostics using ADB
- Package debugging artifacts consistently
- Support repeatable troubleshooting workflows

## Current Behavior
Today the repo provides a single script, [generate_bug_report.py](/home/vhinson/dev/ADB-Bug-Report-Generator/generate_bug_report.py), that:

### Running the Script
1. Connect the Android device to your computer via USB.
2. Run the compatibility script:
   ```bash
   python3 generate_bug_report.py
   ```
3. Or install the package in editable mode and run the module entry point:
   ```bash
   pip install -e .
   python3 -m adb_bug_report_generator
   ```
   In restricted or offline environments, editable install may require local packaging tools already present in the virtual environment.
4. Follow the prompts to select a device (if multiple devices are connected).
5. Provide a summary of the incident when prompted.

### Command-line Arguments
- `-n`, `--num-recent-files`: Specify the number of recent files to pull from directories. Default is 5.
- `-s`, `--simplified`: Generate a simplified report (skips pulling directories and bug report).
- `--include-bugreport`: Include a bugreport when running a full collection.
- `--output-dir`: Set the local output directory for report artifacts.
- `--verbose`: Enable verbose logging.

Example:
```bash
python3 generate_bug_report.py -n 3 -s
```

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

## Testing Strategy
This repo will follow the QA testing pyramid:

- **Unit tests** in `tests/unit/` for small, deterministic logic such as path creation, selection logic, and compatibility decisions.
- **Integration tests** in `tests/integration/` for module interactions using mocked or controlled ADB behavior.
- **End-to-end tests** in `tests/e2e/` for small smoke-test coverage against emulators and selected real devices.

The goal is to keep most coverage in unit tests, add targeted integration coverage for orchestration and failure handling, and keep emulator or physical-device runs focused and lightweight.

Current local test command:
```bash
.venv/bin/python -m pytest
```

---

## Error Handling
- If no devices are detected, the script exits with an appropriate message.
- If directories or files cannot be pulled, errors are logged, and the script continues execution for other tasks.

Optional arguments:

- `-n`, `--num_recent_files`: Number of recent files to pull from configured directories. Default is `5`.
- `-s`, `--simplified`: Skip the broad directory pulls and create a smaller report.

Example:

```bash
python3 generate_bug_report.py -n 3 -s
```

### Full Report
To generate a full incident report with all data:
```bash
python3 generate_bug_report.py -n 5
```

---

- `Device Info`
- `QGC Logs`
- `Screen Recordings`
- `Navsuite Logs`

---
