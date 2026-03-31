# Manual Validation Checklist

Use this checklist when validating behavior against real Android hardware.

## Non-Rooted Device

- Confirm `adb devices` reports the phone or tablet in `device` state.
- Run the CLI with `--device <serial> --incident-summary "manual validation" --non-interactive`.
- Verify the run succeeds without requiring root-specific permissions.
- Confirm the final zip contains `run_summary.txt`, `metadata.json`, `Device Info/logcat.txt`, and `Device Info/device_info.txt`.
- Confirm `metadata.json` records `is_rooted: false` and the expected Android version and SDK.
- Confirm protected-path diagnostics are skipped with an explicit non-root reason.

## Rooted Device

- Confirm `su` is available from `adb shell`.
- Run the CLI with `--device <serial> --incident-summary "root validation" --non-interactive --require-root`.
- Verify the run succeeds and `metadata.json` records `is_rooted: true`.
- Confirm `Device Info/protected_path_diagnostics.txt` is present when root-enhanced commands return data.
- Confirm standard non-root collectors still run before any root-enhanced diagnostics.

## Cross-Version Checks

- Record Android version, SDK level, model, and manufacturer for each validated device.
- Note whether legacy command fallbacks were needed for older Android builds.
- Note any collectors that were skipped because of unavailable commands or device-specific restrictions.
- Capture differences between emulator and physical-device results in a short test note or PR comment.

## Observed Results

### 2026-03-31 Non-Root Physical Device

- Device: `PANASONIC FZ-S1` (`2BKHA09608`)
- Android: `11`
- SDK: `30`
- Primary non-root validation succeeded with `is_rooted: false` and `is_emulator: false` in `metadata.json`.
- Expected archive contents were present, including `run_summary.txt`, `metadata.json`, `Device Info/logcat.txt`, and `Device Info/device_info.txt`.
- Accessible app data path detected: `/sdcard/Android/data/ai.pdw.gcs/files/PDW_GCS`
- Package diagnostics were tested separately with `--package ai.pdw.gcs` and collected successfully.
- Full report review with `--include-bugreport` also succeeded after removing the bugreport timeout, and the archive included `bugreport.zip`.
- Protected-path diagnostics were skipped as expected because privileged collection was not explicitly requested.
- No collector-specific fallbacks were observed during the successful run; `ifconfig` was available and used for network capture.

### 2026-03-31 Non-Root Physical Device (Cross-Version Comparison)

- Device: `NUU S6304L` (`MBA23P233500452`)
- Android: `13`
- SDK: `33`
- Full report review succeeded with `is_rooted: false`, `is_emulator: false`, and `bugreport.zip` present in the final archive.
- Package diagnostics for `ai.pdw.gcs` were collected successfully.
- Protected-path diagnostics were skipped as expected because privileged collection was not explicitly requested.
- No matching app/media directories were present for the broad pull and recent-file collectors, so the run produced diagnostics-only artifacts plus `bugreport.zip`.
- No collector-specific command fallbacks were observed; `ifconfig` was available and used for network capture.

### Cross-Version Notes

- Android `11` / SDK `30` device (`PANASONIC FZ-S1`) exposed populated app/media directories and produced both diagnostics and user-content pulls.
- Android `13` / SDK `33` device (`NUU S6304L`) produced diagnostics and `bugreport.zip` successfully, but had no matching app/media directories to collect.
- Both non-root devices reported `is_rooted: false`, skipped protected-path diagnostics for the expected explicit reason, and supported package diagnostics for `ai.pdw.gcs`.
