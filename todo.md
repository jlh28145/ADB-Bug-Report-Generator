# ADB Bug Report Generator — Senior QA / SDET Portfolio Roadmap

## 🎯 End Goal

Transform this repo from:
> a one-off Python script

into:
> a reusable, CLI-driven Android diagnostics tool that works across emulators and real devices, handles platform differences gracefully, and demonstrates senior-level QA / SDET engineering judgment

This repo should demonstrate:
- [ ] system-level tooling
- [ ] structured debugging workflows
- [ ] clean Python engineering practices
- [ ] testability and maintainability
- [ ] CI/CD integration
- [ ] senior QA / SDET ownership
- [ ] automation design judgment
- [ ] reliability and failure analysis thinking
- [ ] developer enablement and documentation quality

---

## Execution Tracks

### Track 1: Implementation
- [ ] Build the tool into a clean, testable diagnostics package
- [ ] Support real devices and Android emulators
- [ ] Add fallbacks based on Android version and root access
- [ ] Make behavior observable, reliable, and automation-friendly

### Track 2: Portfolio Presentation
- [ ] Explain architecture and tradeoffs clearly
- [ ] Show meaningful tests and quality gates
- [ ] Include examples, demo artifacts, and polished documentation
- [ ] Make the repo easy for hiring managers to evaluate quickly

---

## Compatibility Goals

### Device Types
- [ ] Physical Android devices
- [ ] Android emulators

### Environment Modes
- [ ] Rooted devices
- [ ] Non-rooted devices

### Platform Support
- [ ] Handle Android version differences where commands, paths, or permissions vary
- [ ] Prefer capability detection over hardcoded assumptions
- [ ] Gracefully degrade when an artifact cannot be collected on a given device

### Desired Behavior
- [ ] Detect device characteristics before collection begins
- [ ] Choose the safest supported collection strategy for the target device
- [ ] Record which collectors succeeded, failed, or were skipped
- [ ] Make fallback behavior explicit in logs and metadata

---

## Track 1 — Implementation Phases

## Phase 0: Define Repo Identity

### Purpose
- [x] Collect Android diagnostics using ADB
- [x] Package debugging artifacts consistently
- [x] Support troubleshooting workflows

### Out of Scope
- [x] Performance benchmarking
- [x] Battery or thermal testing
- [x] Full QA automation suite

### Senior SDET Signal
- [x] Clear scope control and product thinking

---

## Phase 1: Audit Current Repo

### Tasks
- [x] Review structure and entry point
- [x] Identify hardcoded values
- [x] Identify dead or incomplete code paths
- [x] Identify duplicated or tightly coupled logic
- [x] Document assumptions about device connection
- [x] Document assumptions about ADB availability
- [x] Document assumptions about emulator compatibility
- [x] Document assumptions about root access
- [x] Document assumptions about Android version behavior

### Output
- [x] Document strengths
- [x] Document weaknesses
- [x] Document cleanup targets
- [x] Document risk areas
- [x] Document testability gaps
- [x] Document automation opportunities

### Senior SDET Signal
- [x] Shows analytical baseline before refactoring

---

## Phase 2: Restructure Project

### Target Structure

ADB-Bug-Report-Generator/
- [ ] README.md
- [ ] pyproject.toml
- [ ] requirements.txt
- [ ] src/
- [ ] `adb_bug_report_generator/`
- [ ] cli.py
- [ ] adb.py
- [ ] collector.py
- [ ] compatibility.py
- [ ] filesystem.py
- [ ] logging_config.py
- [ ] exceptions.py
- [ ] tests/
- [ ] examples/
- [ ] docs/
- [ ] `adr/`

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

## Phase 3: Device Capability Detection

### Goals
- [x] Detect whether the target is an emulator or physical device
- [x] Detect Android version and SDK level
- [x] Detect root availability
- [x] Detect supported commands and accessible paths

### Tasks
- [x] Add device profile collection at startup
- [x] Capture values such as:
- [x] serial
- [x] model
- [x] manufacturer
- [x] Android version
- [x] SDK level
- [x] emulator flag
- [x] root availability
- [x] Build a compatibility decision layer
- [x] Record capability results in metadata

### Senior SDET Signal
- [x] Shows robust environment-aware automation instead of happy-path scripting

---

## Phase 4: Standardize Core Functionality

### Core Features
- [x] Collect bugreport when supported
- [x] Collect logcat
- [x] Collect device info
- [x] Collect optional package diagnostics
- [x] Collect run metadata

### Output Structure

output/
- [x] YYYY-MM-DD_HHMMSS/
- [x] run_summary.txt
- [x] device_info.txt
- [x] logcat.txt
- [x] bugreport.zip
- [x] metadata.json

### Tasks
- [x] Standardize file naming
- [x] Ensure consistent output structure
- [x] Support partial-success runs with explicit status reporting
- [x] Make outputs deterministic enough for automated validation

### Senior SDET Signal
- [x] Shows consistency, diagnosability, and automation-friendly outputs

---

## Phase 5: Build Compatibility Fallbacks

### Fallback Categories
- [ ] Android version differences
- [ ] Rooted vs non-rooted devices
- [ ] Emulator vs physical device
- [ ] Missing commands or inaccessible paths

### Tasks
- [x] Define preferred and fallback collectors for each artifact type
- [ ] Prefer non-root strategies first where practical
- [ ] Use root-enhanced collection only when available and justified
- [x] Skip unsupported steps with explicit reasons
- [x] Add compatibility notes to logs and metadata

### Example Fallbacks
- [ ] Use one device-info command when another is unavailable
- [ ] Skip protected-path pulls on non-rooted devices
- [ ] Mark hardware-specific collectors as unsupported on emulators
- [x] Adjust shell commands when Android version output differs

### Senior SDET Signal
- [ ] Demonstrates resilient automation design and platform-aware troubleshooting

---

## Phase 6: Build CLI

### Example Usage

python -m adb_bug_report_generator \
  --output-dir output \
  --package com.example.app \
  --include-logcat \
  --include-bugreport

### Flags
- [ ] --device
- [ ] --package
- [ ] --output-dir
- [ ] --include-logcat
- [ ] --include-bugreport
- [ ] --include-device-info
- [ ] --verbose
- [ ] --timeout
- [ ] --non-interactive
- [ ] --incident-summary
- [ ] --fail-on-partial
- [ ] --allow-emulator
- [ ] --require-root
- [ ] --compat-mode

### Senior SDET Signal
- [ ] Clear operator-facing interfaces and predictable tooling behavior

---

## Phase 7: Logging, Error Handling, and Exit Codes

### Tasks
- [ ] Replace prints with logging
- [ ] Support log levels
- [ ] Add clear operator-facing error messages
- [ ] Add explicit exit codes for common failure modes
- [ ] Ensure runs still produce useful summaries when one collector fails

### Handle Errors
- [ ] ADB not installed
- [ ] no device connected
- [ ] multiple devices
- [ ] unauthorized device
- [ ] timeout
- [ ] emulator boot not complete
- [ ] missing paths
- [ ] unsupported collector for this device type
- [ ] root required but unavailable
- [ ] invalid user input
- [ ] partial artifact collection

### Senior SDET Signal
- [ ] Demonstrates diagnosability and operational maturity

---

## Phase 8: ADB Abstraction Layer

### Create ADB Client

Functions:
- [ ] list_devices()
- [ ] get_device_profile()
- [ ] collect_bugreport()
- [ ] collect_logcat()
- [ ] get_device_info()
- [ ] pull_file()
- [ ] pull_directory()
- [ ] run_shell_command()

### Requirements
- [ ] No scattered subprocess calls
- [ ] Structured return values
- [ ] Timeout support
- [ ] Retry strategy where appropriate
- [ ] Clear exception mapping for common ADB failures
- [ ] Device targeting that works for both physical devices and emulators

### Senior SDET Signal
- [ ] Abstraction quality and testable automation infrastructure

---

## Phase 9: Testing Strategy and Coverage

### Tools
- [ ] pytest
- [ ] mock / monkeypatch

### Test Pyramid
- Unit tests should be the majority of coverage
- Integration tests should validate module collaboration with mocked ADB behavior
- End-to-end tests should stay small and focus on emulator and selected real-device smoke coverage

### Coverage Targets
- [ ] CLI behavior
- [ ] ADB wrapper
- [ ] filesystem handling
- [ ] collector logic
- [ ] failure handling paths
- [ ] partial-success behavior
- [ ] metadata generation
- [ ] compatibility decisions
- [ ] emulator-targeted flows
- [ ] rooted vs non-rooted decision paths

### Goal
- [ ] 70–85% meaningful coverage

### Test Layers
- [ ] Unit tests for decision logic and file handling
- [ ] Mocked integration-style tests for ADB interactions
- [ ] Emulator smoke tests for supported end-to-end flows
- [ ] Manual validation checklist for real-device scenarios

### Emulator Testing
- [ ] Document a supported Android emulator setup for local validation
- [ ] Add a minimal smoke test flow against an emulator
- [ ] Validate device detection, logcat capture, device info capture, and output packaging on emulator targets
- [ ] Note which collectors require physical hardware and which are emulator-safe

### Real Device Testing
- [ ] Validate at least one non-rooted physical device path
- [ ] Validate rooted-device enhanced flows if hardware is available
- [ ] Record differences observed across Android versions

### Senior SDET Signal
- [ ] Shows layered, pragmatic automation strategy

---

## Phase 10: Quality Tooling and CI/CD

### Add
- [ ] ruff
- [ ] black
- [ ] pytest
- [ ] pre-commit
- [ ] coverage reporting
- [ ] optional mypy

### Quality Gates
- [ ] tests must pass
- [ ] lint must pass
- [ ] minimum coverage threshold
- [ ] packaging/import checks must pass

### GitHub Actions
- [ ] install dependencies
- [ ] run lint
- [ ] run tests
- [ ] upload coverage artifacts
- [ ] publish test results
- [ ] optionally run emulator smoke tests when the environment supports it

### Trigger
- [ ] push
- [ ] pull_request

pytest
ruff check .  
black --check .  

---

## Phase 11: Security and Data Handling

### Tasks
- [ ] Remove unsafe shell command patterns where possible
- [ ] Validate CLI inputs and output paths
- [ ] Sanitize generated filenames and metadata content
- [ ] Document sensitive-data considerations for logs, bugreports, and archives
- [ ] Avoid collecting privileged data unless explicitly requested

### Senior SDET Signal
- [ ] Shows quality ownership beyond happy paths

---

## Phase 12: Developer Experience

### Tasks
- [ ] Add contributor setup instructions
- [ ] Add simple run/test/lint commands
- [ ] Make local validation fast and easy
- [ ] Provide troubleshooting for common environment issues
- [ ] Add emulator startup instructions for contributors without physical test devices

### Senior SDET Signal
- [ ] Enablement mindset and team-friendly automation

---

## Track 2 — Portfolio Presentation Phases

## Phase 13: README Rewrite

### Sections
- [x] Overview
- [ ] Features
- [ ] Use Case
- [ ] CLI Examples
- [ ] Output Structure
- [x] Prerequisites and setup
- [ ] Testing
- [ ] Emulator Testing
- [ ] Real Device Support
- [ ] Compatibility and Fallback Strategy
- [ ] Architecture
- [ ] Failure Handling
- [ ] CI Quality Gates
- [x] Current limitations and tradeoffs

### Senior SDET Signal
- [x] README now reflects current behavior and known limitations more accurately

---

## Phase 14: Architecture Decision Records

### Tasks
- [ ] Add an ADR for project structure and module boundaries
- [ ] Add an ADR for ADB abstraction and subprocess handling
- [ ] Add an ADR for compatibility detection and fallback design
- [ ] Add an ADR for test strategy and CI scope

### Senior SDET Signal
- [ ] Demonstrates design reasoning and maintainability thinking

---

## Phase 15: Demo Readiness

### Tasks
- [ ] Add sanitized example output under `examples/`
- [ ] Add a walkthrough of a sample run
- [ ] Add terminal screenshots or recorded output
- [ ] Include at least one emulator-based demo path
- [ ] Include one real-device validation summary if available

### Senior SDET Signal
- [ ] Makes results visible and reviewable

---

## Phase 16: Portfolio Storytelling

### Tasks
- [ ] Add a before-vs-after comparison from the original script to the refactored tool
- [ ] Add a short engineering decisions and tradeoffs section
- [ ] Highlight emulator-backed validation and real-device support
- [ ] Highlight Android-version and root/non-root fallback design
- [ ] Add a resume-ready project summary

### Senior SDET Signal
- [ ] Communicates technical leadership, not just implementation effort

---

## Phase 17: Repo Presentation

### Update Description
- [ ] System-level Android diagnostics utility using ADB, designed for repeatable artifact collection across emulators and physical devices with compatibility-aware fallbacks and strong test automation practices

### Add Tags
- [ ] python
- [ ] adb
- [ ] android
- [ ] debugging
- [ ] qa
- [ ] sdet
- [ ] test-automation
- [ ] reliability
- [ ] ci-cd

### Senior SDET Signal
- [ ] Makes the project searchable and easy to position professionally

---

## Final Checklist

### Functional
- [ ] Works on emulator and real device targets
- [ ] Handles rooted and non-rooted modes sensibly
- [ ] Applies Android-version-aware fallbacks
- [ ] Produces useful output even on partial failure

### Quality
- [x] Script import-time side effects reduced
- [ ] Tests pass
- [ ] CI passes
- [ ] Logging is clear
- [ ] Output and metadata are easy to validate

### Documentation
- [x] README is aligned with current behavior
- [ ] CLI examples work
- [x] Compatibility strategy is captured in the roadmap
- [ ] Testing strategy is documented in the README

### Portfolio Signal
- [x] Repo shows clearer system-design intent than the starting point
- [x] Repo shows stronger debugging workflow direction than the starting point
- [ ] Repo shows maintainable automation practices
- [ ] Repo shows senior QA / SDET decision-making

---

Collecting Android debugging artifacts in a reliable, repeatable, professional way
