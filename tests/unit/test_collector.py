"""Unit tests for collector helpers."""

import pytest

from tests import _bootstrap  # noqa: F401
from adb_bug_report_generator.collector import (
    CollectionOptions,
    build_recent_file_commands,
    filter_log_specs,
    select_device,
)
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
