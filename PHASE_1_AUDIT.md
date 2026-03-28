# Phase 1 Audit

## Snapshot
The repository currently contains a single executable script, [generate_bug_report.py](/home/vhinson/dev/ADB-Bug-Report-Generator/generate_bug_report.py), plus project documentation in [README.md](/home/vhinson/dev/ADB-Bug-Report-Generator/README.md) and planning notes in [todo.md](/home/vhinson/dev/ADB-Bug-Report-Generator/todo.md).

## Entry Point
- Primary entry point: [generate_bug_report.py](/home/vhinson/dev/ADB-Bug-Report-Generator/generate_bug_report.py)
- Interface style: interactive script with minimal CLI flags
- Current execution model: collect device artifacts, package them into a local report directory, then zip the results

## Strengths
- The repo already solves a real Android debugging workflow.
- Device discovery and multi-device selection are implemented.
- The script has recognizable functional boundaries such as device discovery, file pulling, log collection, and archive creation.
- The worktree started clean, so refactoring can proceed from a stable baseline.

## Weaknesses
- Runtime side effects occur at import time, including timestamp generation and directory creation.
- ADB execution is scattered and inconsistent, mixing `shell=True` string commands with list-based subprocess calls.
- Collection rules are tightly coupled to specific app IDs and storage paths.
- Error handling is print-based and not structured for reuse or testing.
- The README previously overstated current behavior, especially around bugreport generation.

## Hardcoded Values
- Local output root: `incident_reports`
- Device directories: `/sdcard/Pictures`, `/sdcard/Movies`
- App-specific directories:
  - `/sdcard/Android/data/org.mavlink.qgroundcontrol/files/PDW_GCS`
  - `/sdcard/Android/data/ai.pdw.gcs/files/PDW_GCS`
- App package diagnostics:
  - `ai.pdw.gcs`
  - `org.mavlink.qgroundcontrol`
- Report subdirectory names:
  - `Screen Recordings`
  - `QGC Logs`
  - `Device Info`
  - `Navsuite Logs`

## Dead Code Or Incomplete Paths
- `collect_bugreport()` exists but its only invocation is commented out in the main flow.
- The README described bugreport generation as active behavior even though it is currently disabled.

## Duplicated Or Coupled Logic
- Path creation is spread across globals instead of being created from a single run configuration.
- Several functions depend on module-level directories and timestamp values rather than explicit parameters.
- File pull logic mixes generic behavior with destination routing rules for specific content types.

## Current Assumptions
- `adb` is installed and callable from the command line.
- At least one Android device is connected and authorized.
- The user is available to respond to interactive prompts.
- The environment is effectively single-run and terminal-based.
- Multi-device handling requires manual selection.
- Device storage paths match the expected app-specific layout.

## Cleanup Targets
- Move all runtime setup under a `main()` function.
- Replace module-level output paths with run-scoped parameters or context objects.
- Centralize ADB subprocess handling behind a consistent interface.
- Separate generic Android diagnostics from app-specific collectors.
- Standardize output naming and metadata format.
- Introduce structured logging and explicit exceptions in later phases.
