"""ADB client abstraction."""

from dataclasses import dataclass
import re
import subprocess

from adb_bug_report_generator.exceptions import AdbCommandError, AdbTimeoutError


ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")


@dataclass
class ADBClient:
    """Thin wrapper around ADB subprocess calls."""

    executable: str = "adb"
    timeout_seconds: float | None = None

    def list_devices(self):
        """Return connected device serials."""
        return [record["serial"] for record in self.list_device_records() if record["state"] == "device"]

    def list_device_records(self):
        """Return connected device serials and their reported ADB states."""
        result = self._run([self.executable, "devices"])
        lines = result.stdout.strip().splitlines()
        records = []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) < 2:
                continue
            records.append({"serial": parts[0], "state": parts[1]})
        return records

    def shell_text(self, command, device=None):
        """Run an ADB shell command and return cleaned text output."""
        args = self._device_prefix(device) + ["shell", "sh", "-c", command]
        result = self._run(args)
        return ANSI_ESCAPE_PATTERN.sub("", result.stdout.strip())

    def pull(self, remote_path, local_path, device=None):
        """Pull a file or directory from the device."""
        args = self._device_prefix(device) + ["pull", remote_path, str(local_path)]
        self._run(args)

    def bugreport(self, output_path, device=None):
        """Collect an ADB bugreport zip."""
        args = self._device_prefix(device) + ["bugreport", str(output_path)]
        self._run(args)

    def _device_prefix(self, device):
        args = [self.executable]
        if device:
            args.extend(["-s", device])
        return args

    def _run(self, args):
        try:
            return subprocess.run(
                args,
                text=True,
                capture_output=True,
                check=True,
                timeout=self.timeout_seconds,
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
            raise AdbCommandError(
                "ADB command failed.",
                args,
                stderr=exc.stderr.strip(),
            ) from exc
