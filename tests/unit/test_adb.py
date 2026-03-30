"""Unit tests for the ADB abstraction layer."""

import subprocess

import pytest

from tests import _bootstrap  # noqa: F401
from adb_bug_report_generator.adb import ADBClient, DeviceRecord
from adb_bug_report_generator.exceptions import (
    DeviceAuthorizationError,
    DeviceUnavailableError,
    InvalidDeviceSelectionError,
)


def _completed_process(args, stdout="", stderr="", returncode=0):
    return subprocess.CompletedProcess(args=args, returncode=returncode, stdout=stdout, stderr=stderr)


def test_list_device_records_returns_structured_records(monkeypatch):
    client = ADBClient()

    def fake_run(*_args, **_kwargs):
        return _completed_process(
            ["adb", "devices"],
            stdout="List of devices attached\nemulator-5554\tdevice\ndevice-1234\toffline\n",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    records = client.list_device_records()

    assert records == [
        DeviceRecord(serial="emulator-5554", state="device"),
        DeviceRecord(serial="device-1234", state="offline"),
    ]


def test_run_retries_transient_offline_error(monkeypatch):
    client = ADBClient(retry_attempts=1)
    calls = {"count": 0}

    def fake_run(*_args, **_kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise subprocess.CalledProcessError(
                returncode=1,
                cmd=["adb", "devices"],
                stderr="error: device offline",
            )
        return _completed_process(["adb", "devices"], stdout="List of devices attached\nemulator-5554\tdevice\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    records = client.list_device_records()

    assert calls["count"] == 2
    assert records == [DeviceRecord(serial="emulator-5554", state="device")]


def test_run_maps_authorization_error(monkeypatch):
    client = ADBClient()

    def fake_run(*_args, **_kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=["adb", "devices"],
            stderr="error: device unauthorized",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(DeviceAuthorizationError):
        client.list_device_records()


def test_run_maps_multiple_device_error(monkeypatch):
    client = ADBClient()

    def fake_run(*_args, **_kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=["adb", "shell"],
            stderr="error: more than one device/emulator",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(InvalidDeviceSelectionError):
        client.run_shell_command("getprop")


def test_run_maps_offline_error_without_retry_when_attempts_exhausted(monkeypatch):
    client = ADBClient(retry_attempts=0)

    def fake_run(*_args, **_kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=["adb", "pull"],
            stderr="error: device offline",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(DeviceUnavailableError):
        client.pull_file("/sdcard/example.txt", "/tmp/example.txt")


class FakeProfileClient(ADBClient):
    def run_shell_command(self, command, device=None):
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
            "test -d '/sdcard/Android/data/org.mavlink.qgroundcontrol/files/PDW_GCS' && echo exists": "",
            "test -d '/sdcard/Android/data/ai.pdw.gcs/files/PDW_GCS' && echo exists": "exists",
        }
        from adb_bug_report_generator.adb import ADBCommandResult

        return ADBCommandResult(
            command=("adb", "shell", "sh", "-c", command),
            stdout=responses.get(command, ""),
            stderr="",
            returncode=0,
        )


def test_get_device_profile_builds_expected_metadata():
    profile = FakeProfileClient().get_device_profile("emulator-5554")

    assert profile.serial == "emulator-5554"
    assert profile.model == "Pixel 8"
    assert profile.manufacturer == "Google"
    assert profile.android_version == "14"
    assert profile.sdk_level == 34
    assert profile.is_emulator is True
    assert profile.is_boot_completed is True
    assert profile.is_rooted is True
    assert profile.accessible_paths == ("/sdcard/Android/data/ai.pdw.gcs/files/PDW_GCS",)
    assert profile.available_commands["ip"] is True
    assert profile.available_commands["bugreport"] is False
