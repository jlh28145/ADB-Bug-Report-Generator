# Contributing

## Local Setup

1. Install Python 3.10+.
2. Install Android Platform Tools so `adb` is on your `PATH`.
3. Create a virtual environment:

```bash
python3 -m venv .venv
```

4. Activate it:

```bash
source .venv/bin/activate
```

5. Install the developer toolchain:

```bash
.venv/bin/pip install -r requirements.txt
```

Optional editable install:

```bash
.venv/bin/pip install -e .[dev]
```

## Daily Commands

Use the `Makefile` targets for the shortest local workflow:

```bash
make run
make test
make lint
make format
make validate
```

If you prefer direct commands:

```bash
PYTHONPATH=src .venv/bin/python -m adb_bug_report_generator
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/black --check src tests generate_bug_report.py
.venv/bin/mypy src/adb_bug_report_generator
PRE_COMMIT_HOME=/tmp/pre-commit-cache .venv/bin/pre-commit run --all-files
```

## Fast Validation Paths

Quick confidence check:

```bash
make test
make lint
```

Full local validation:

```bash
make validate
```

That runs Ruff, Black, pytest with coverage, mypy, packaging, and packaged import validation.

## Running the CLI

Compatibility wrapper:

```bash
python3 generate_bug_report.py --help
```

Packaged module entry point:

```bash
PYTHONPATH=src .venv/bin/python -m adb_bug_report_generator --help
```

## Emulator Setup

Use this path if you do not have a physical Android device available.

Recommended baseline:
- Android Studio with Device Manager
- an `x86_64` emulator image
- API level 30 or newer
- Google APIs or Google Play image is fine

Create and boot an emulator, then verify readiness:

```bash
adb devices
adb -s emulator-5554 shell getprop sys.boot_completed
```

The boot-complete check should return `1`.

Run the opt-in emulator smoke test:

```bash
ADB_RUN_EMULATOR_SMOKE=1 \
ADB_EMULATOR_SERIAL=emulator-5554 \
.venv/bin/pytest tests/e2e/test_emulator_smoke.py -q
```

Run the CLI against the emulator:

```bash
PYTHONPATH=src .venv/bin/python -m adb_bug_report_generator \
  --device emulator-5554 \
  --allow-emulator \
  --incident-summary "manual emulator validation" \
  --non-interactive \
  --output-dir output/emulator-review
```

## Troubleshooting

### `adb: command not found`

Install Android Platform Tools and make sure `adb` is available on your `PATH`.

Quick check:

```bash
adb version
```

### Device does not appear in `adb devices`

- reconnect the cable
- unlock the device
- confirm USB debugging is enabled
- accept the RSA authorization prompt on the device
- restart the server if needed:

```bash
adb kill-server
adb start-server
adb devices
```

### Device shows `unauthorized`

Disconnect and reconnect the device, then accept the USB debugging prompt on screen.

### Emulator smoke test skips immediately

Make sure both env vars are set:

```bash
echo "$ADB_RUN_EMULATOR_SMOKE"
echo "$ADB_EMULATOR_SERIAL"
```

Also confirm the emulator is still booted and visible in `adb devices`.

### `adb bugreport` takes a long time

This is expected on some devices. The collector now disables the normal command timeout for `adb bugreport`, so a long-running bugreport should be allowed to complete.

### `pre-commit` fails while fetching hooks

That usually means the current environment has restricted network access. The GitHub Actions workflow remains the source of truth when hook environments cannot be fetched locally.

## Notes for Contributors

- Do not commit generated `output/` archives or raw device artifacts.
- Prefer emulator validation for routine checks and reserve physical-device testing for targeted validation.
- Use [tests/e2e/manual_validation_checklist.md](/home/vhinson/dev/ADB-Bug-Report-Generator/tests/e2e/manual_validation_checklist.md) when recording real-device results.
