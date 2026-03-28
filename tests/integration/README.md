# Integration Tests

This layer is for mocked or controlled ADB workflow tests.

Use this level for:
- CLI orchestration with a fake ADB client
- collector-to-filesystem interactions
- partial-failure handling across modules

Keep these tests slower than unit tests, but still deterministic and CI-friendly.
