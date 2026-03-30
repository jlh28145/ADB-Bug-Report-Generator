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
