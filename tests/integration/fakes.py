"""Shared fake collaborators for integration tests."""


class FakeADBClient:
    """Small fake ADB client for integration-style CLI tests."""

    def __init__(self):
        self.pulled = []

    def list_devices(self):
        return ["emulator-5554"]

    def shell_text(self, command, device=None):
        responses = {
            "test -d '/sdcard/Android/data/org.mavlink.qgroundcontrol/files/PDW_GCS' && echo exists": "",
            "test -d '/sdcard/Android/data/ai.pdw.gcs/files/PDW_GCS' && echo exists": "",
            "ls -p /sdcard/Pictures": "photo-001.jpg\nScreenshots/\n",
            "ls -p /sdcard/Movies": "screen-archive.mp4\nmovie-001.mp4\n",
            "ls -t /sdcard/Movies | grep '^screen-' | head -n 2": "screen-001.mp4\nscreen-002.mp4",
            "ls -t /sdcard/Documents/Navsuite | head -n 2": "navsuite.log",
            "logcat -d": "fake logcat",
            "getprop": "[ro.build.version.release]: [14]",
            "dumpsys meminfo ai.pdw.gcs": "meminfo ai.pdw.gcs",
            "dumpsys meminfo org.mavlink.qgroundcontrol": "meminfo qgc",
            "top -n 1": "cpu usage",
            "dumpsys netstats": "netstats",
            "ifconfig": "ifconfig output",
            "dumpsys battery": "battery info",
            "df -h": "storage info",
            "dumpsys activity": "activity dump",
        }
        return responses.get(command, "")

    def pull(self, remote_path, local_path, device=None):
        self.pulled.append((remote_path, str(local_path), device))

        if local_path.is_dir():
            destination = local_path / remote_path.split("/")[-1]
        else:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            destination = local_path

        destination.write_text(f"pulled from {remote_path}", encoding="utf-8")

    def bugreport(self, output_path, device=None):
        output_path.write_text("bugreport", encoding="utf-8")


class PartiallyFailingADBClient(FakeADBClient):
    """ADB client fake that fails one artifact pull to exercise degraded runs."""

    def pull(self, remote_path, local_path, device=None):
        if remote_path.endswith("screen-002.mp4"):
            raise RuntimeError("simulated pull failure")
        super().pull(remote_path, local_path, device=device)


class NoDeviceADBClient(FakeADBClient):
    """ADB client fake that reports no connected devices."""

    def list_devices(self):
        return []


class MissingAdbClient(FakeADBClient):
    """ADB client fake that simulates adb not being available."""

    def list_devices(self):
        from adb_bug_report_generator.exceptions import AdbCommandError

        raise AdbCommandError(
            "ADB executable not found. Install Android Platform Tools and ensure 'adb' is available on your PATH.",
            ["adb", "devices"],
        )
