"""Unit tests for collector helpers."""

from types import SimpleNamespace

import pytest

from adb_bug_report_generator.collector import (
    CollectionOptions,
    build_recent_file_commands,
    collect_logs,
    collect_protected_path_diagnostics,
    evaluate_requested_collectors,
    filter_log_specs,
    resolve_log_specs_for_profile,
    select_device,
)
from adb_bug_report_generator.compatibility import DeviceProfile
from adb_bug_report_generator.exceptions import DeviceSelectionError
from tests import _bootstrap  # noqa: F401


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
    commands = build_recent_file_commands(["/sdcard/Android/data/example/files/PDW_GCS"])

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
        log_specs=(
            ("device_info", "device_info.txt", ("getprop", "dumpsys window"), "getprop_or_dumpsys"),
        ),
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


def test_collect_protected_path_diagnostics_skips_when_root_is_unavailable(tmp_path):
    class FakeClient:
        def shell_text(self, command, device=None):
            return ""

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
        available_commands={},
    )

    result = collect_protected_path_diagnostics(
        FakeClient(),
        "device-1234",
        SimpleNamespace(device_info_dir=tmp_path),
        profile,
    )

    assert result.status == "skipped"
    assert "preferred non-root collection strategy" in result.detail


def test_collect_protected_path_diagnostics_uses_root_enhanced_commands(tmp_path):
    class FakeClient:
        def shell_text(self, command, device=None):
            responses = {
                (
                    "su -c 'ls -ld /data/anr /data/tombstones 2>/dev/null'"
                ): "/data/anr\n/data/tombstones",
                "su -c 'ls -t /data/anr 2>/dev/null | head -n 5'": "traces.txt",
                "su -c 'ls -t /data/tombstones 2>/dev/null | head -n 5'": "tombstone_01",
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
        is_rooted=True,
        accessible_paths=(),
        available_commands={},
    )

    result = collect_protected_path_diagnostics(
        FakeClient(),
        "device-1234",
        SimpleNamespace(device_info_dir=tmp_path),
        profile,
    )

    assert result.status == "collected"
    assert "root-enhanced commands" in result.detail
    assert (tmp_path / "protected_path_diagnostics.txt").exists()


def test_resolve_log_specs_for_profile_uses_legacy_commands_for_older_android():
    profile = DeviceProfile(
        serial="device-legacy",
        model="Pixel",
        manufacturer="Google",
        android_version="6.0",
        sdk_level=23,
        is_emulator=False,
        is_boot_completed=True,
        is_rooted=False,
        accessible_paths=(),
        available_commands={},
    )

    specs = resolve_log_specs_for_profile(
        profile,
        (
            ("cpu_usage", "cpu_usage.txt", ("top -n 1",), "top"),
            ("storage_info", "storage_info.txt", ("df -h",), "df"),
            ("event_logs", "event_logs.txt", ("dumpsys activity",), "dumpsys"),
        ),
    )

    assert specs[0][2] == ("top -n 1 -m 10", "top -n 1")
    assert specs[1][2] == ("df", "df -h")
    assert specs[2][2] == ("dumpsys activity activities", "dumpsys activity")


def test_collect_logs_uses_legacy_android_fallback_commands(tmp_path):
    commands_seen = []

    class FakeClient:
        def shell_text(self, command, device=None):
            commands_seen.append(command)
            responses = {
                "top -n 1 -m 10": "legacy cpu usage",
                "df": "legacy storage info",
                "dumpsys activity activities": "legacy event logs",
            }
            return responses.get(command, "")

    profile = DeviceProfile(
        serial="device-legacy",
        model="Pixel",
        manufacturer="Google",
        android_version="6.0",
        sdk_level=23,
        is_emulator=False,
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
        "device-legacy",
        SimpleNamespace(device_info_dir=tmp_path),
        profile,
        log_specs=(
            ("cpu_usage", "cpu_usage.txt", ("top -n 1",), "top"),
            ("storage_info", "storage_info.txt", ("df -h",), "df"),
            ("event_logs", "event_logs.txt", ("dumpsys activity",), "dumpsys"),
        ),
    )

    assert [result.status for result in results] == ["collected", "collected", "collected"]
    assert "top -n 1 -m 10" in commands_seen
    assert "df" in commands_seen
    assert "dumpsys activity activities" in commands_seen
