"""Unit tests for collector helpers."""

from types import SimpleNamespace

import pytest

from tests import _bootstrap  # noqa: F401
from adb_bug_report_generator.collector import (
    CollectionOptions,
    build_recent_file_commands,
    collect_logs,
    evaluate_requested_collectors,
    filter_log_specs,
    select_device,
)
from adb_bug_report_generator.compatibility import DeviceProfile
from adb_bug_report_generator.exceptions import DeviceSelectionError


def test_select_device_returns_only_device():
    captured = []

    selected = select_device(["emulator-5554"], output=captured.append)

    assert selected == "emulator-5554"
    assert captured == ["Using the only connected device: emulator-5554"]


def test_select_device_raises_when_no_devices():
    with pytest.raises(DeviceSelectionError) as context:
        select_device([])

    assert str(context.value) == "No devices connected. Please connect a device and try again."


def test_select_device_reprompts_until_valid_choice():
    prompts = iter(["abc", "5", "2"])
    captured = []

    selected = select_device(
        ["emulator-5554", "device-1234"],
        prompt=lambda _: next(prompts),
        output=captured.append,
    )

    assert selected == "device-1234"
    assert captured == [
        "Multiple devices detected:",
        "1: emulator-5554",
        "2: device-1234",
        "Invalid input. Please enter a number.",
        "Invalid choice. Please try again.",
    ]


def test_build_recent_file_commands_includes_application_logs():
    commands = build_recent_file_commands(
        ["/sdcard/Android/data/example/files/PDW_GCS"]
    )

    assert (
        "/sdcard/Android/data/example/files/PDW_GCS/Logs/ConsoleLogs",
        "ls -t /sdcard/Android/data/example/files/PDW_GCS/Logs/ConsoleLogs",
    ) in commands


def test_filter_log_specs_can_disable_logcat_only():
    options = CollectionOptions(
        num_recent_files=2,
        simplified=True,
        include_logcat=False,
        include_device_info=True,
    )

    specs = filter_log_specs(options)

    assert all(spec[0] != "logcat" for spec in specs)
    assert any(spec[0] == "device_info" for spec in specs)


def test_filter_log_specs_can_disable_all_text_diagnostics():
    options = CollectionOptions(
        num_recent_files=2,
        simplified=True,
        include_logcat=False,
        include_device_info=False,
    )

    assert filter_log_specs(options) == ()


def test_collection_options_supports_optional_package_name():
    options = CollectionOptions(
        num_recent_files=2,
        simplified=True,
        package="com.example.app",
    )

    assert options.package == "com.example.app"


def test_evaluate_requested_collectors_reports_unsupported_requirements():
    options = CollectionOptions(
        num_recent_files=2,
        simplified=True,
        include_logcat=True,
        include_device_info=True,
        include_bugreport=True,
        package="com.example.app",
    )
    profile = DeviceProfile(
        serial="device-1234",
        model="Pixel",
        manufacturer="Google",
        android_version="14",
        sdk_level=34,
        is_emulator=False,
        is_boot_completed=True,
        is_rooted=False,
        accessible_paths=(),
        available_commands={
            "getprop": True,
            "dumpsys": False,
            "logcat": True,
            "bugreport": False,
            "ifconfig": False,
            "ip": True,
            "top": True,
            "pidof": False,
        },
    )

    unsupported = evaluate_requested_collectors(options, profile, filter_log_specs(options))

    assert any(item["name"] == "meminfo_pdw_gcs" for item in unsupported)
    assert any(item["name"] == "bugreport" for item in unsupported)
    assert any(item["name"] == "package_diagnostics" for item in unsupported)


def test_collect_logs_falls_back_to_dumpsys_for_device_info(tmp_path):
    class FakeClient:
        def shell_text(self, command, device=None):
            responses = {
                "getprop": "",
                "dumpsys window": "window diagnostics",
            }
            return responses.get(command, "")

    profile = DeviceProfile(
        serial="device-1234",
        model="Pixel",
        manufacturer="Google",
        android_version="14",
        sdk_level=34,
        is_emulator=False,
        is_boot_completed=True,
        is_rooted=False,
        accessible_paths=(),
        available_commands={
            "getprop": False,
            "dumpsys": True,
            "logcat": True,
            "bugreport": False,
            "ifconfig": False,
            "ip": True,
            "top": True,
            "pidof": False,
        },
    )

    results = collect_logs(
        FakeClient(),
        "device-1234",
        SimpleNamespace(device_info_dir=tmp_path),
        profile,
        log_specs=(("device_info", "device_info.txt", ("getprop", "dumpsys window"), "getprop_or_dumpsys"),),
    )

    assert results[0].status == "collected"
    assert "dumpsys window" in results[0].detail
    assert (tmp_path / "device_info.txt").read_text(encoding="utf-8") == "window diagnostics"


def test_collect_logs_skips_battery_info_on_emulator_targets(tmp_path):
    class FakeClient:
        def shell_text(self, command, device=None):
            return "battery info"

    profile = DeviceProfile(
        serial="emulator-5554",
        model="Pixel",
        manufacturer="Google",
        android_version="14",
        sdk_level=34,
        is_emulator=True,
        is_boot_completed=True,
        is_rooted=False,
        accessible_paths=(),
        available_commands={
            "getprop": True,
            "dumpsys": True,
            "logcat": True,
            "bugreport": False,
            "ifconfig": False,
            "ip": True,
            "top": True,
            "pidof": False,
        },
    )

    results = collect_logs(
        FakeClient(),
        "emulator-5554",
        SimpleNamespace(device_info_dir=tmp_path),
        profile,
        log_specs=(("battery_info", "battery_info.txt", ("dumpsys battery",), "dumpsys"),),
    )

    assert results[0].status == "skipped"
    assert "not a reliable hardware signal on emulator targets" in results[0].detail
