# ADB Bug Report Generator — Portfolio Upgrade Roadmap

## 🎯 End Goal

Transform this repo from:
> a one-off Python script

into:
> a clean, reusable, CLI-driven system diagnostics tool for Android debugging workflows

This repo should demonstrate:
- system-level tooling
- structured debugging workflows
- clean Python engineering practices
- testability and maintainability
- CI/CD integration

---

## Phase 0: Define Repo Identity

### Purpose
- Collect Android diagnostics using ADB
- Package debugging artifacts consistently
- Support troubleshooting workflows

### Out of Scope
- Performance benchmarking
- Battery/thermal testing
- Full QA automation suite

---

## Phase 1: Audit Current Repo

### Tasks
- Review structure and entry point
- Identify hardcoded values
- Remove dead code
- Identify duplicated logic
- Document assumptions:
  - device connection
  - ADB availability
  - single-device limitations

### Output
- Strengths
- Weaknesses
- Cleanup targets

---

## Phase 2: Restructure Project

### Target Structure

ADB-Bug-Report-Generator/
- README.md
- pyproject.toml
- requirements.txt
- src/
  - adb_bug_report_generator/
    - cli.py
    - adb.py
    - collector.py
    - filesystem.py
    - logging_config.py
    - exceptions.py
- tests/
- examples/

### Tasks
- [x] Move logic into `src/`
- [x] Separate CLI from logic
- [x] Create ADB wrapper module
- [x] Add structured error handling
- [x] Add `pyproject.toml` and `requirements.txt`
- [x] Keep a compatibility wrapper for `generate_bug_report.py`
- [x] Create `tests/` and `examples/` scaffolding
- [x] Add initial `pytest` unit and integration coverage

### Current Progress
- Package layout created under `src/adb_bug_report_generator/`
- Legacy script converted to a compatibility wrapper entry point
- Filesystem, collector, CLI, ADB, logging, and exception concerns split into modules
- `pytest` adopted for unit and integration test layers

---

## Phase 3: Standardize Core Functionality

### Features
- Collect bugreport
- Collect logcat
- Collect device info
- Optional package diagnostics

### Output Structure

output/
- YYYY-MM-DD_HHMMSS/
  - run_summary.txt
  - device_info.txt
  - logcat.txt
  - bugreport.zip
  - metadata.json

### Tasks
- Standardize file naming
- Handle failures gracefully
- Ensure consistent output

---

## Phase 4: Build CLI

### Example Usage

python -m adb_bug_report_generator \
  --output-dir output \
  --package com.example.app \
  --include-logcat \
  --include-bugreport

### Flags
- --device
- --package
- --output-dir
- --include-logcat
- --include-bugreport
- --include-device-info
- --verbose
- --timeout

---

## Phase 5: Logging & Error Handling

### Tasks
- Replace prints with logging
- Support log levels
- Add clear error messages

### Handle Errors
- ADB not installed
- No device connected
- Multiple devices
- Timeout

---

## Phase 6: ADB Abstraction Layer

### Create ADB Client

Functions:
- list_devices()
- collect_bugreport()
- collect_logcat()
- get_device_info()

### Requirements
- No scattered subprocess calls
- Structured return values
- Timeout support

---

## Phase 7: Testing

### Tools
- pytest
- mock / monkeypatch

### Test Pyramid
- Unit tests should be the majority of coverage
- Integration tests should validate module collaboration with mocked ADB behavior
- End-to-end tests should stay small and focus on emulator and selected real-device smoke coverage

### Coverage Targets
- CLI behavior
- ADB wrapper
- filesystem handling
- collector logic

### Goal
70–85% meaningful coverage

---

## Phase 8: Quality Tooling

### Add
- black
- ruff or flake8
- pytest

### Commands

pytest
ruff check .  
black --check .  

---

## Phase 9: CI/CD

### GitHub Actions Pipeline
- install dependencies
- lint
- run tests

### Trigger
- push
- pull_request

---

## Phase 10: README Rewrite

### Sections
- Overview
- Features
- Use Case
- CLI Examples
- Output Structure
- Setup
- Testing

---

## Phase 11: Repo Presentation

### Update Description
System-level debugging utility for Android devices using ADB, focused on automated log collection and diagnostic artifact generation

### Add Tags
- python
- adb
- android
- debugging
- qa
- sdet

---

## Phase 12: Add One Professional Feature

### Recommended
Add metadata.json

Include:
- timestamp
- device info
- selected options
- generated files
- success/failure status

---

## Phase 13: Final Checklist

### Structure
- Clean package layout
- No dead code

### Quality
- Tests pass
- CI passes
- Logging is clear

### Documentation
- README is clear
- CLI examples work

### Signal
Repo should show:
- system thinking
- debugging workflows
- maintainable tooling

---

## Suggested Timeline

### Week 1
- Identity
- Audit
- Structure

### Week 2
- Core functionality
- CLI
- Logging

### Week 3
- ADB abstraction
- Testing

### Week 4
- CI/CD
- README
- Final polish

---

## Minimum Viable Portfolio Version

- Clean structure
- CLI
- Logging
- Tests
- CI
- README

---

## Guiding Principle

Do not bloat scope.

This repo should excel at one thing:

Collecting Android debugging artifacts in a reliable, repeatable, professional way
