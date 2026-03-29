"""Project-specific exceptions."""


class ADBBugReportError(Exception):
    """Base exception for the package."""

    exit_code = 1


class DeviceSelectionError(ADBBugReportError):
    """Raised when no valid device can be selected."""

    exit_code = 3


class NoConnectedDevicesError(DeviceSelectionError):
    """Raised when no connected devices are available for collection."""


class InvalidDeviceSelectionError(DeviceSelectionError):
    """Raised when the operator's device choice cannot be used."""

    exit_code = 8


class DeviceAuthorizationError(ADBBugReportError):
    """Raised when a connected device is blocked by authorization state."""

    exit_code = 6


class DeviceUnavailableError(ADBBugReportError):
    """Raised when a connected device is unavailable for collection."""

    exit_code = 6


class DeviceBootIncompleteError(ADBBugReportError):
    """Raised when the target device has not finished booting."""

    exit_code = 7


class CompatibilityConstraintError(ADBBugReportError):
    """Raised when target capabilities do not satisfy requested constraints."""

    exit_code = 8


class AdbCommandError(ADBBugReportError):
    """Raised when an ADB command fails."""

    def __init__(self, message, command, stderr="", exit_code=1):
        super().__init__(message)
        self.command = command
        self.stderr = stderr
        self.exit_code = exit_code


class AdbTimeoutError(ADBBugReportError):
    """Raised when an ADB command exceeds the configured timeout."""

    exit_code = 5

    def __init__(self, message, command, timeout_seconds):
        super().__init__(message)
        self.command = command
        self.timeout_seconds = timeout_seconds
