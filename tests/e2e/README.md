# End-to-End Tests

This layer is the top of the testing pyramid and should stay small.

Use this level for:
- emulator-backed smoke tests
- selected real-device validation flows
- compatibility checks that require actual ADB behavior

These tests should prove the system works in realistic environments without becoming the main source of coverage.

## Emulator Smoke Flow

The repo includes an opt-in emulator smoke test in `tests/e2e/test_emulator_smoke.py`.

It is intentionally skipped unless you provide both:
- `ADB_RUN_EMULATOR_SMOKE=1`
- `ADB_EMULATOR_SERIAL=<serial>`

Example:

```bash
ADB_RUN_EMULATOR_SMOKE=1 \
ADB_EMULATOR_SERIAL=emulator-5554 \
.venv/bin/pytest tests/e2e/test_emulator_smoke.py -q
```

The smoke test validates:
- explicit emulator device targeting
- startup device-profile detection
- logcat capture
- device-info capture
- output packaging into the final zip archive

CI behavior:
- runs automatically on `push` to `main`
- can be triggered manually from any branch with `workflow_dispatch`

## Supported Local Emulator Setup

Recommended baseline:
- Android Emulator created from Android Studio Device Manager
- API level 30 or newer
- boot completed before starting the smoke run
- `adb devices` shows the emulator in `device` state

Quick sanity check:

```bash
adb devices
adb -s emulator-5554 shell getprop sys.boot_completed
```

The second command should return `1` before the smoke test is started.

## Collector Notes

Safe on emulator targets:
- device detection and profile capture
- logcat collection
- device-info collection
- compatibility and packaging validation

Usually less useful or intentionally limited on emulator targets:
- battery diagnostics
- hardware-dependent troubleshooting artifacts
- root-enhanced protected-path diagnostics unless you are using a rooted emulator image

Physical-device validation is still needed for rooted and non-rooted hardware-specific behavior.
