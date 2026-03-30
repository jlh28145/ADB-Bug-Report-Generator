"""ADB client abstraction."""

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

from adb_bug_report_generator.exceptions import (
    AdbCommandError,
    AdbTimeoutError,
    DeviceAuthorizationError,
    DeviceUnavailableError,
    InvalidDeviceSelectionError,
    NoConnectedDevicesError,
)


ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")
RETRYABLE_STDERR_PATTERNS = (
    "device offline",
    "device still authorizing",
    "protocol fault",
    "connection reset",
    "closed",
)


@dataclass(frozen=True)
class ADBCommandResult:
    """Structured result for an ADB command invocation."""

    command: tuple[str, ...]
    stdout: str
    stderr: str
    returncode: int


@dataclass(frozen=True)
class DeviceRecord:
    """ADB-reported state for a connected device or emulator."""

    serial: str
    state: str


@dataclass
class ADBClient:
    """ADB client with timeout, retry, and structured command support."""

    executable: str = "adb"
    timeout_seconds: float | None = None
    retry_attempts: int = 1

    def list_devices(self):
        """Return connected device serials."""
        return [record.serial for record in self.list_device_records() if record.state == "device"]

    def list_device_records(self):
        """Return connected device serials and their reported ADB states."""
        result = self._run([self.executable, "devices"], retryable=True)
        lines = result.stdout.strip().splitlines()
        records = []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) < 2:
                continue
            records.append(DeviceRecord(serial=parts[0], state=parts[1]))
        return records

    def get_device_profile(self, serial):
        """Collect a capability profile for the requested device serial."""
        from adb_bug_report_generator.compatibility import (
            KNOWN_COMMANDS,
            DeviceProfile,
            detect_accessible_paths,
            detect_boot_completed,
            detect_root,
        )

        model = self.run_shell_command("getprop ro.product.model", device=serial).stdout or "unknown"
        manufacturer = (
            self.run_shell_command("getprop ro.product.manufacturer", device=serial).stdout or "unknown"
        )
        android_version = (
            self.run_shell_command("getprop ro.build.version.release", device=serial).stdout or "unknown"
        )
        sdk_level = _parse_int(
            self.run_shell_command("getprop ro.build.version.sdk", device=serial).stdout
        )
        emulator_property = self.run_shell_command("getprop ro.kernel.qemu", device=serial).stdout

        return DeviceProfile(
            serial=serial,
            model=model,
            manufacturer=manufacturer,
            android_version=android_version,
            sdk_level=sdk_level,
            is_emulator=serial.startswith("emulator-") or emulator_property == "1",
            is_boot_completed=detect_boot_completed(self, serial),
            is_rooted=detect_root(self, serial),
            accessible_paths=tuple(detect_accessible_paths(self, serial)),
            available_commands={name: self.command_exists(name, serial) for name in KNOWN_COMMANDS},
        )

    def run_shell_command(self, command, device=None):
        """Run an ADB shell command and return a cleaned structured result."""
        args = self._device_prefix(device) + ["shell", "sh", "-c", command]
        result = self._run(args)
        return ADBCommandResult(
            command=result.command,
            stdout=ANSI_ESCAPE_PATTERN.sub("", result.stdout.strip()),
            stderr=result.stderr.strip(),
            returncode=result.returncode,
        )

    def shell_text(self, command, device=None):
        """Backwards-compatible helper for callers that only need stdout text."""
        return self.run_shell_command(command, device=device).stdout

    def command_exists(self, command, device=None):
        """Check whether a shell command is available on the target."""
        result = self.run_shell_command(
            f"command -v {command} >/dev/null 2>&1 && echo available",
            device=device,
        )
        return result.stdout == "available"

    def pull_file(self, remote_path, local_path, device=None):
        """Pull a file from the target device to a local path."""
        args = self._device_prefix(device) + ["pull", remote_path, str(local_path)]
        return self._run(args, retryable=True)

    def pull_directory(self, remote_path, local_dir, device=None):
        """Pull a directory from the target device to a local directory."""
        Path(local_dir).mkdir(parents=True, exist_ok=True)
        return self.pull_file(remote_path, local_dir, device=device)

    def pull(self, remote_path, local_path, device=None):
        """Backwards-compatible alias for file or directory pulls."""
        return self.pull_file(remote_path, local_path, device=device)

    def collect_bugreport(self, output_path, device=None):
        """Collect an ADB bugreport zip."""
        args = self._device_prefix(device) + ["bugreport", str(output_path)]
        return self._run(args, retryable=True)

    def bugreport(self, output_path, device=None):
        """Backwards-compatible alias for bugreport collection."""
        return self.collect_bugreport(output_path, device=device)

    def collect_logcat(self, output_path, device=None, command="logcat -d"):
        """Collect logcat text and write it to a local file."""
        result = self.run_shell_command(command, device=device)
        Path(output_path).write_text(result.stdout, encoding="utf-8")
        return result

    def get_device_info(self, commands, device=None):
        """Run one or more device-info shell commands and return structured results."""
        return [self.run_shell_command(command, device=device) for command in commands]

    def _device_prefix(self, device):
        args = [self.executable]
        if device:
            args.extend(["-s", device])
        return args

    def _run(self, args, retryable=False):
        attempts = 1 + self.retry_attempts if retryable else 1
        last_error = None

        for attempt in range(1, attempts + 1):
            try:
                completed = subprocess.run(
                    args,
                    text=True,
                    capture_output=True,
                    check=True,
                    timeout=self.timeout_seconds,
                )
                return ADBCommandResult(
                    command=tuple(str(part) for part in completed.args),
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                    returncode=completed.returncode,
                )
            except FileNotFoundError as exc:
                raise AdbCommandError(
                    "ADB executable not found. Install Android Platform Tools and ensure 'adb' is available on your PATH.",
                    args,
                    exit_code=4,
                ) from exc
            except subprocess.TimeoutExpired as exc:
                timeout_seconds = self.timeout_seconds if self.timeout_seconds is not None else 0
                raise AdbTimeoutError(
                    f"ADB command timed out after {timeout_seconds} seconds.",
                    args,
                    timeout_seconds,
                ) from exc
            except subprocess.CalledProcessError as exc:
                last_error = self._map_command_error(args, exc.stderr.strip())
                if attempt < attempts and self._should_retry(exc.stderr):
                    continue
                raise last_error from exc

        assert last_error is not None
        raise last_error

    def _should_retry(self, stderr):
        normalized = (stderr or "").strip().lower()
        return any(pattern in normalized for pattern in RETRYABLE_STDERR_PATTERNS)

    def _map_command_error(self, args, stderr):
        normalized = (stderr or "").lower()

        if "unauthorized" in normalized:
            error = DeviceAuthorizationError(
                "Connected device is unauthorized. Check the device for an ADB authorization prompt and accept it before retrying."
            )
            error.command = args
            error.stderr = stderr
            return error

        if "offline" in normalized:
            error = DeviceUnavailableError(
                "Connected device is offline. Reconnect the device or restart ADB before retrying."
            )
            error.command = args
            error.stderr = stderr
            return error

        if "more than one device/emulator" in normalized:
            error = InvalidDeviceSelectionError(
                "ADB requires an explicit device selection because multiple devices/emulators are connected."
            )
            error.command = args
            error.stderr = stderr
            return error

        if "no devices/emulators found" in normalized:
            error = NoConnectedDevicesError("No devices connected. Please connect a device and try again.")
            error.command = args
            error.stderr = stderr
            return error

        return AdbCommandError(
            "ADB command failed.",
            args,
            stderr=stderr,
        )


def _parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
