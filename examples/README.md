# Demo Examples

This directory holds sanitized, documentation-friendly demo material for reviewing how the tool behaves without committing raw device artifacts.

## Included Files

- `sample_archive_tree.txt`: example archive layout from a successful run
- `sample_metadata.json`: sanitized example metadata showing device profile, selected options, and artifact status
- `sample_run_summary.txt`: sanitized run summary text
- `sample_terminal_output.txt`: recorded CLI output from a representative run

## Demo Paths

### Emulator Demo

Use an Android emulator when you want a low-risk local walkthrough without needing a physical device:

```bash
PYTHONPATH=src .venv/bin/python -m adb_bug_report_generator \
  --device emulator-5554 \
  --allow-emulator \
  --incident-summary "demo emulator run" \
  --non-interactive \
  --output-dir output/demo-emulator
```

Optional smoke validation:

```bash
ADB_RUN_EMULATOR_SMOKE=1 \
ADB_EMULATOR_SERIAL=emulator-5554 \
.venv/bin/pytest tests/e2e/test_emulator_smoke.py -q
```

### Real-Device Demo

Use a connected physical device when you want to show the non-root collection flow with more realistic diagnostics:

```bash
PYTHONPATH=src .venv/bin/python -m adb_bug_report_generator \
  --device <serial> \
  --incident-summary "demo real-device run" \
  --non-interactive \
  --include-bugreport \
  --package ai.pdw.gcs \
  --output-dir output/demo-real-device
```

## Real-Device Validation Summary

Validated non-root examples captured during manual review:

- `PANASONIC FZ-S1` on Android `11` / SDK `30`
  - package diagnostics succeeded for `ai.pdw.gcs`
  - broad media and app-log collection was populated
  - `bugreport.zip` completed successfully
- `NUU S6304L` on Android `13` / SDK `33`
  - package diagnostics succeeded for `ai.pdw.gcs`
  - diagnostics and `bugreport.zip` completed successfully
  - no matching app/media directories were present, so the archive was diagnostics-focused

These examples are summarized from the documented validation notes in [tests/e2e/manual_validation_checklist.md](/home/vhinson/dev/ADB-Bug-Report-Generator/tests/e2e/manual_validation_checklist.md).
