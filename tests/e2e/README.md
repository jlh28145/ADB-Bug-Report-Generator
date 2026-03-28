# End-to-End Tests

This layer is the top of the testing pyramid and should stay small.

Use this level for:
- emulator-backed smoke tests
- selected real-device validation flows
- compatibility checks that require actual ADB behavior

These tests should prove the system works in realistic environments without becoming the main source of coverage.
