"""Shared fake collaborators for integration tests."""


class FakeADBClient:
    """Small fake ADB client for integration-style CLI tests."""

    def __init__(self):
        self.pulled = []

    def list_devices(self):
        return ["emulator-5554"]

    def list_device_records(self):
        return [{"serial": serial, "state": "device"} for serial in self.list_devices()]

    def shell_text(self, command, device=None):
        responses = {
            "test -d '/sdcard/Android/data/org.mavlink.qgroundcontrol/files/PDW_GCS' && echo exists": "",
            "test -d '/sdcard/Android/data/ai.pdw.gcs/files/PDW_GCS' && echo exists": "",
            "getprop ro.product.model": "Pixel 8",
            "getprop ro.product.manufacturer": "Google",
            "getprop ro.build.version.release": "14",
            "getprop ro.build.version.sdk": "34",
            "getprop ro.kernel.qemu": "1",
            "getprop sys.boot_completed": "1",
            "getprop dev.bootcomplete": "1",
            "command -v su >/dev/null 2>&1 && echo available": "",
            "command -v getprop >/dev/null 2>&1 && echo available": "available",
            "command -v dumpsys >/dev/null 2>&1 && echo available": "available",
            "command -v logcat >/dev/null 2>&1 && echo available": "available",
            "command -v bugreport >/dev/null 2>&1 && echo available": "available",
            "command -v ifconfig >/dev/null 2>&1 && echo available": "available",
            "command -v ip >/dev/null 2>&1 && echo available": "available",
            "command -v pidof >/dev/null 2>&1 && echo available": "available",
            "command -v top >/dev/null 2>&1 && echo available": "available",
            "ls -p /sdcard/Pictures": "photo-001.jpg\nScreenshots/\n",
            "ls -p /sdcard/Movies": "screen-archive.mp4\nmovie-001.mp4\n",
            "ls -t /sdcard/Movies | grep '^screen-' | head -n 2": "screen-001.mp4\nscreen-002.mp4",
            "ls -t /sdcard/Documents/Navsuite | head -n 2": "navsuite.log",
            "logcat -d": "fake logcat",
            "getprop": "[ro.build.version.release]: [14]",
            "dumpsys meminfo ai.pdw.gcs": "meminfo ai.pdw.gcs",
            "dumpsys meminfo org.mavlink.qgroundcontrol": "meminfo qgc",
            "dumpsys package com.example.app": "Package [com.example.app] (12345)",
            "pidof com.example.app": "4321",
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
            exit_code=4,
        )


class TimeoutADBClient(FakeADBClient):
    """ADB client fake that simulates a timeout while listing devices."""

    def list_devices(self):
        from adb_bug_report_generator.exceptions import AdbTimeoutError

        raise AdbTimeoutError(
            "ADB command timed out after 60.0 seconds.",
            ["adb", "devices"],
            60.0,
        )


class MultiDeviceADBClient(FakeADBClient):
    """ADB client fake that reports more than one connected device."""

    def list_devices(self):
        return ["emulator-5554", "device-1234"]

    def list_device_records(self):
        return [
            {"serial": "emulator-5554", "state": "device"},
            {"serial": "device-1234", "state": "device"},
        ]


class RootedADBClient(FakeADBClient):
    """ADB client fake that reports root availability."""

    def shell_text(self, command, device=None):
        if command == "command -v su >/dev/null 2>&1 && echo available":
            return "available"
        if command == "su -c 'ls -ld /data/anr /data/tombstones 2>/dev/null'":
            return "/data/anr\n/data/tombstones"
        if command == "su -c 'ls -t /data/anr 2>/dev/null | head -n 5'":
            return "traces.txt"
        if command == "su -c 'ls -t /data/tombstones 2>/dev/null | head -n 5'":
            return "tombstone_01"
        return super().shell_text(command, device=device)


class FallbackNetworkADBClient(FakeADBClient):
    """ADB client fake that requires network command fallback."""

    def shell_text(self, command, device=None):
        if command == "command -v ifconfig >/dev/null 2>&1 && echo available":
            return ""
        if command == "ifconfig":
            return ""
        if command == "ip addr":
            return "ip route output"
        return super().shell_text(command, device=device)


class UnsupportedCollectorsADBClient(FakeADBClient):
    """ADB client fake that simulates a target with limited collector support."""

    def shell_text(self, command, device=None):
        if command == "command -v bugreport >/dev/null 2>&1 && echo available":
            return ""
        if command == "command -v dumpsys >/dev/null 2>&1 && echo available":
            return ""
        return super().shell_text(command, device=device)


class UnauthorizedADBClient(FakeADBClient):
    """ADB client fake that reports an unauthorized connected device."""

    def list_device_records(self):
        return [{"serial": "device-unauthorized", "state": "unauthorized"}]


class OfflineADBClient(FakeADBClient):
    """ADB client fake that reports an offline connected device."""

    def list_device_records(self):
        return [{"serial": "device-offline", "state": "offline"}]


class BootingEmulatorADBClient(FakeADBClient):
    """ADB client fake that reports an emulator before boot is complete."""

    def shell_text(self, command, device=None):
        if command in {"getprop sys.boot_completed", "getprop dev.bootcomplete"}:
            return "0"
        return super().shell_text(command, device=device)
