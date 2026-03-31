"""Unit tests for device compatibility detection."""

from adb_bug_report_generator.adb import ADBCommandResult
from adb_bug_report_generator.compatibility import detect_accessible_paths, detect_device_profile
from tests import _bootstrap  # noqa: F401


class FakeProfileClient:
    def shell_text(self, command, device=None):
        responses = {
            "getprop ro.product.model": "Pixel 8",
            "getprop ro.product.manufacturer": "Google",
            "getprop ro.build.version.release": "14",
            "getprop ro.build.version.sdk": "34",
            "getprop ro.kernel.qemu": "1",
            "getprop sys.boot_completed": "1",
            "getprop dev.bootcomplete": "1",
            "command -v su >/dev/null 2>&1 && echo available": "available",
            "command -v getprop >/dev/null 2>&1 && echo available": "available",
            "command -v dumpsys >/dev/null 2>&1 && echo available": "available",
            "command -v logcat >/dev/null 2>&1 && echo available": "available",
            "command -v bugreport >/dev/null 2>&1 && echo available": "",
            "command -v ifconfig >/dev/null 2>&1 && echo available": "",
            "command -v ip >/dev/null 2>&1 && echo available": "available",
            "command -v top >/dev/null 2>&1 && echo available": "available",
            (
                "test -d '/sdcard/Android/data/org.mavlink.qgroundcontrol/files/PDW_GCS' "
                "&& echo exists"
            ): "",
            "test -d '/sdcard/Android/data/ai.pdw.gcs/files/PDW_GCS' && echo exists": "exists",
        }
        return responses.get(command, "")


def test_detect_device_profile_collects_capabilities():
    profile = detect_device_profile(FakeProfileClient(), "emulator-5554")

    assert profile.serial == "emulator-5554"
    assert profile.model == "Pixel 8"
    assert profile.manufacturer == "Google"
    assert profile.android_version == "14"
    assert profile.sdk_level == 34
    assert profile.is_emulator is True
    assert profile.is_boot_completed is True
    assert profile.is_rooted is True
    assert profile.accessible_paths == ("/sdcard/Android/data/ai.pdw.gcs/files/PDW_GCS",)
    assert profile.available_commands["getprop"] is True
    assert profile.available_commands["bugreport"] is False


class ProbeFriendlyClient:
    def run_shell_command(self, command, device=None, allow_failure=False):
        responses = {
            (
                "test -d '/sdcard/Android/data/org.mavlink.qgroundcontrol/files/PDW_GCS' "
                "&& echo exists"
            ): ("", 1),
            "test -d '/sdcard/Android/data/ai.pdw.gcs/files/PDW_GCS' && echo exists": (
                "exists",
                0,
            ),
        }
        stdout, returncode = responses.get(command, ("", 1))
        return ADBCommandResult(
            command=("adb", "shell", "sh", "-c", command),
            stdout=stdout,
            stderr="",
            returncode=returncode,
        )


def test_detect_accessible_paths_tolerates_missing_directories():
    paths = detect_accessible_paths(ProbeFriendlyClient(), "device-1234")

    assert paths == ["/sdcard/Android/data/ai.pdw.gcs/files/PDW_GCS"]
