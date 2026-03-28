"""Project-specific exceptions."""


class ADBBugReportError(Exception):
    """Base exception for the package."""


class DeviceSelectionError(ADBBugReportError):
    """Raised when no valid device can be selected."""


class AdbCommandError(ADBBugReportError):
    """Raised when an ADB command fails."""

    def __init__(self, message, command, stderr=""):
        super().__init__(message)
        self.command = command
        self.stderr = stderr
