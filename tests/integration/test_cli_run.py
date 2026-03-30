"""Integration tests for CLI orchestration with a fake ADB client."""

import json
import logging
from types import SimpleNamespace
from zipfile import ZipFile

from adb_bug_report_generator.cli import format_operator_error, main, run
from adb_bug_report_generator.exceptions import AdbCommandError
from tests import _bootstrap  # noqa: F401
from tests.integration.fakes import (
    BootingEmulatorADBClient,
    FakeADBClient,
    FallbackNetworkADBClient,
    MissingAdbClient,
    MultiDeviceADBClient,
    NoDeviceADBClient,
    OfflineADBClient,
    PartiallyFailingADBClient,
    RootedADBClient,
    TimeoutADBClient,
    UnauthorizedADBClient,
    UnsupportedCollectorsADBClient,
)


def build_args(tmp_path, **overrides):
    defaults = {
        "device": None,
        "num_recent_files": 2,
        "simplified": True,
        "include_logcat": True,
        "include_device_info": True,
        "include_bugreport": False,
        "package": None,
        "incident_summary": None,
        "non_interactive": False,
        "fail_on_partial": False,
        "timeout": 60.0,
        "output_dir": str(tmp_path / "output"),
        "verbose": False,
        "allow_emulator": True,
        "require_root": False,
        "compat_mode": "auto",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_run_creates_zip_archive_with_expected_artifacts(tmp_path):
    args = build_args(tmp_path)
    logger = logging.getLogger("test_cli_integration")
    fake_client = FakeADBClient()

    exit_code = run(args, logger, client=fake_client, prompt=lambda _: "integration summary")

    assert exit_code == 0

    zip_files = list((tmp_path / "output").glob("QA_bug_report_*.zip"))
    assert len(zip_files) == 1

    with ZipFile(zip_files[0]) as archive:
        archive_names = set(archive.namelist())
        assert "Device Info/logcat.txt" in archive_names
        assert "Device Info/device_info.txt" in archive_names
        assert "Navsuite Logs/navsuite.log" in archive_names
        assert "Screen Recordings/screen-001.mp4" in archive_names
        assert "metadata.json" in archive_names
        assert "run_summary.txt" in archive_names

        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
        assert metadata["incident_summary"] == "integration summary"
        assert metadata["device"] == "emulator-5554"
        assert metadata["device_profile"]["model"] == "Pixel 8"
        assert metadata["device_profile"]["android_version"] == "14"
        assert metadata["device_profile"]["is_emulator"] is True


def test_run_still_creates_archive_when_one_pull_fails(tmp_path):
    args = build_args(tmp_path)
    logger = logging.getLogger("test_cli_partial_failure")
    fake_client = PartiallyFailingADBClient()

    exit_code = run(args, logger, client=fake_client, prompt=lambda _: "partial failure summary")

    assert exit_code == 0

    zip_files = list((tmp_path / "output").glob("QA_bug_report_*.zip"))
    assert len(zip_files) == 1

    with ZipFile(zip_files[0]) as archive:
        archive_names = set(archive.namelist())
        assert "Screen Recordings/screen-001.mp4" in archive_names
        assert "Screen Recordings/screen-002.mp4" not in archive_names
        assert "metadata.json" in archive_names

        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
        assert metadata["incident_summary"] == "partial failure summary"
        assert any(item["status"] == "failed" for item in metadata["artifacts"])
        assert any(
            "screen-002.mp4" in item["name"]
            for item in metadata["artifacts"]
            if item["status"] == "failed"
        )


def test_run_includes_bugreport_when_requested(tmp_path):
    args = build_args(tmp_path, simplified=False, include_bugreport=True)
    logger = logging.getLogger("test_cli_bugreport")
    fake_client = FakeADBClient()

    exit_code = run(args, logger, client=fake_client, prompt=lambda _: "bugreport summary")

    assert exit_code == 0

    zip_files = list((tmp_path / "output").glob("QA_bug_report_*.zip"))
    assert len(zip_files) == 1

    with ZipFile(zip_files[0]) as archive:
        archive_names = set(archive.namelist())
        assert "bugreport.zip" in archive_names
        assert "Pictures/" in " ".join(archive_names)
        assert "Movies/" in " ".join(archive_names)
        assert "bugreport.zip" in archive_names


def test_main_returns_clear_error_when_no_devices_found(tmp_path, caplog):
    args = build_args(tmp_path)
    logger = logging.getLogger("test_cli_no_device")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        exit_code = main(
            args=args,
            logger=logger,
            client=NoDeviceADBClient(),
            prompt=lambda _: "unused",
        )

    assert exit_code == 3
    assert "No devices connected. Please connect a device and try again." in caplog.text


def test_format_operator_error_includes_command_details():
    error = AdbCommandError(
        "ADB command failed.",
        ["adb", "devices"],
        stderr="device offline",
    )

    message = format_operator_error(error)

    assert "ADB command failed." in message
    assert "Command: adb devices." in message
    assert "Details: device offline" in message


def test_main_returns_clear_error_when_adb_is_missing(tmp_path, caplog):
    args = build_args(tmp_path)
    logger = logging.getLogger("test_cli_missing_adb")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        exit_code = main(
            args=args,
            logger=logger,
            client=MissingAdbClient(),
            prompt=lambda _: "unused",
        )

    assert exit_code == 4
    assert "ADB executable not found." in caplog.text
    assert "Install Android Platform Tools" in caplog.text
    assert "Command: adb devices." in caplog.text


def test_main_returns_clear_error_when_adb_times_out(tmp_path, caplog):
    args = build_args(tmp_path)
    logger = logging.getLogger("test_cli_timeout")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        exit_code = main(
            args=args,
            logger=logger,
            client=TimeoutADBClient(),
            prompt=lambda _: "unused",
        )

    assert exit_code == 5
    assert "ADB command timed out after 60.0 seconds." in caplog.text
    assert "Command: adb devices." in caplog.text


def test_run_allows_operator_to_select_from_multiple_devices(tmp_path):
    args = build_args(tmp_path)
    logger = logging.getLogger("test_cli_multi_device")
    fake_client = MultiDeviceADBClient()
    prompts = iter(["2"])

    exit_code = run(
        args,
        logger,
        client=fake_client,
        prompt=lambda _: "multi-device summary",
        device_prompt=lambda _: next(prompts),
    )

    assert exit_code == 0

    zip_files = list((tmp_path / "output").glob("QA_bug_report_*.zip"))
    assert len(zip_files) == 1

    with ZipFile(zip_files[0]) as archive:
        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
        assert metadata["device"] == "device-1234"


def test_run_uses_network_command_fallback_when_ifconfig_is_unavailable(tmp_path):
    args = build_args(tmp_path)
    logger = logging.getLogger("test_cli_network_fallback")
    fake_client = FallbackNetworkADBClient()

    exit_code = run(args, logger, client=fake_client, prompt=lambda _: "fallback summary")

    assert exit_code == 0

    zip_files = list((tmp_path / "output").glob("QA_bug_report_*.zip"))
    assert len(zip_files) == 1

    with ZipFile(zip_files[0]) as archive:
        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
        network_result = next(
            item for item in metadata["artifacts"] if item["name"] == "network_config"
        )
        assert network_result["status"] == "collected"
        assert "ip addr" in network_result["detail"]


def test_run_can_disable_logcat_and_device_info_collection(tmp_path):
    args = build_args(tmp_path, include_logcat=False, include_device_info=False)
    logger = logging.getLogger("test_cli_disable_text_diagnostics")
    fake_client = FakeADBClient()

    exit_code = run(args, logger, client=fake_client, prompt=lambda _: "no diagnostics summary")

    assert exit_code == 0

    zip_files = list((tmp_path / "output").glob("QA_bug_report_*.zip"))
    assert len(zip_files) == 1

    with ZipFile(zip_files[0]) as archive:
        archive_names = set(archive.namelist())
        assert "Device Info/logcat.txt" not in archive_names
        assert "Device Info/device_info.txt" not in archive_names

        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
        assert metadata["selected_options"]["include_logcat"] is False
        assert metadata["selected_options"]["include_device_info"] is False
        diagnostics_result = next(
            item for item in metadata["artifacts"] if item["name"] == "diagnostics"
        )
        assert diagnostics_result["status"] == "skipped"


def test_run_collects_optional_package_diagnostics(tmp_path):
    args = build_args(tmp_path, package="com.example.app")
    logger = logging.getLogger("test_cli_package_diagnostics")
    fake_client = FakeADBClient()

    exit_code = run(args, logger, client=fake_client, prompt=lambda _: "package summary")

    assert exit_code == 0

    zip_files = list((tmp_path / "output").glob("QA_bug_report_*.zip"))
    assert len(zip_files) == 1

    with ZipFile(zip_files[0]) as archive:
        archive_names = set(archive.namelist())
        assert "Device Info/package_diagnostics.txt" in archive_names

        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
        assert metadata["selected_options"]["package"] == "com.example.app"
        package_result = next(
            item for item in metadata["artifacts"] if item["name"] == "package_diagnostics"
        )
        assert package_result["status"] == "collected"


def test_run_skips_protected_path_diagnostics_when_root_is_unavailable(tmp_path):
    args = build_args(tmp_path)
    logger = logging.getLogger("test_cli_protected_paths_non_root")

    exit_code = run(
        args, logger, client=FakeADBClient(), prompt=lambda _: "protected paths summary"
    )

    assert exit_code == 0

    zip_files = list((tmp_path / "output").glob("QA_bug_report_*.zip"))
    assert len(zip_files) == 1

    with ZipFile(zip_files[0]) as archive:
        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
        result = next(
            item for item in metadata["artifacts"] if item["name"] == "protected_path_diagnostics"
        )
        assert result["status"] == "skipped"
        assert "preferred non-root collection strategy" in result["detail"]


def test_run_collects_protected_path_diagnostics_when_root_is_available(tmp_path):
    args = build_args(tmp_path)
    logger = logging.getLogger("test_cli_protected_paths_root")

    exit_code = run(
        args, logger, client=RootedADBClient(), prompt=lambda _: "root protected paths summary"
    )

    assert exit_code == 0

    zip_files = list((tmp_path / "output").glob("QA_bug_report_*.zip"))
    assert len(zip_files) == 1

    with ZipFile(zip_files[0]) as archive:
        archive_names = set(archive.namelist())
        assert "Device Info/protected_path_diagnostics.txt" in archive_names
        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
        result = next(
            item for item in metadata["artifacts"] if item["name"] == "protected_path_diagnostics"
        )
        assert result["status"] == "collected"


def test_run_can_use_explicit_device_and_incident_summary_non_interactively(tmp_path):
    args = build_args(
        tmp_path,
        device="emulator-5554",
        incident_summary="non interactive summary",
        non_interactive=True,
    )
    logger = logging.getLogger("test_cli_non_interactive")
    fake_client = FakeADBClient()

    exit_code = run(args, logger, client=fake_client, prompt=lambda _: "should not be used")

    assert exit_code == 0

    zip_files = list((tmp_path / "output").glob("QA_bug_report_*.zip"))
    assert len(zip_files) == 1

    with ZipFile(zip_files[0]) as archive:
        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
        assert metadata["incident_summary"] == "non interactive summary"
        assert metadata["device"] == "emulator-5554"
        assert metadata["selected_options"]["non_interactive"] is True


def test_main_fails_in_non_interactive_mode_without_device_choice(tmp_path, caplog):
    args = build_args(tmp_path, non_interactive=True)
    logger = logging.getLogger("test_cli_non_interactive_device_failure")
    fake_client = MultiDeviceADBClient()

    with caplog.at_level(logging.ERROR, logger=logger.name):
        exit_code = main(
            args=args,
            logger=logger,
            client=fake_client,
            prompt=lambda _: "unused",
        )

    assert exit_code == 8
    assert (
        "Non-interactive mode requires exactly one connected device or an explicit --device value."
        in caplog.text
    )


def test_run_returns_error_code_when_fail_on_partial_is_enabled(tmp_path):
    args = build_args(tmp_path, fail_on_partial=True)
    logger = logging.getLogger("test_cli_fail_on_partial")
    fake_client = PartiallyFailingADBClient()

    exit_code = run(args, logger, client=fake_client, prompt=lambda _: "partial failure summary")

    assert exit_code == 2


def test_main_blocks_emulator_when_allow_emulator_is_not_set(tmp_path, caplog):
    args = build_args(tmp_path, allow_emulator=False)
    logger = logging.getLogger("test_cli_emulator_guard")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        exit_code = main(
            args=args,
            logger=logger,
            client=UnsupportedCollectorsADBClient(),
            prompt=lambda _: "unused",
        )

    assert exit_code == 8
    assert "Emulator target detected." in caplog.text
    assert "--allow-emulator" in caplog.text


def test_main_blocks_run_when_root_is_required_but_unavailable(tmp_path, caplog):
    args = build_args(tmp_path, require_root=True)
    logger = logging.getLogger("test_cli_root_guard")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        exit_code = main(
            args=args,
            logger=logger,
            client=UnsupportedCollectorsADBClient(),
            prompt=lambda _: "unused",
        )

    assert exit_code == 8
    assert "This run requires root access" in caplog.text


def test_run_allows_root_required_mode_when_device_is_rooted(tmp_path):
    args = build_args(tmp_path, require_root=True)
    logger = logging.getLogger("test_cli_root_required_success")

    exit_code = run(
        args,
        logger,
        client=RootedADBClient(),
        prompt=lambda _: "root-required summary",
    )

    assert exit_code == 0


def test_run_allows_emulator_in_permissive_compat_mode_without_explicit_flag(tmp_path):
    args = build_args(tmp_path, allow_emulator=False, compat_mode="permissive")
    logger = logging.getLogger("test_cli_permissive_mode")

    exit_code = run(
        args,
        logger,
        client=FakeADBClient(),
        prompt=lambda _: "permissive summary",
    )

    assert exit_code == 0


def test_main_fails_in_strict_compat_mode_when_requested_collectors_are_unsupported(
    tmp_path, caplog
):
    args = build_args(
        tmp_path,
        compat_mode="strict",
        include_bugreport=True,
        package="com.example.app",
    )
    logger = logging.getLogger("test_cli_strict_mode")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        exit_code = main(
            args=args,
            logger=logger,
            client=UnsupportedCollectorsADBClient(),
            prompt=lambda _: "unused",
        )

    assert exit_code == 8
    assert "Strict compatibility mode rejected this run" in caplog.text
    assert "package diagnostics require dumpsys" in caplog.text


def test_main_returns_clear_error_when_device_is_unauthorized(tmp_path, caplog):
    args = build_args(tmp_path)
    logger = logging.getLogger("test_cli_unauthorized")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        exit_code = main(
            args=args,
            logger=logger,
            client=UnauthorizedADBClient(),
            prompt=lambda _: "unused",
        )

    assert exit_code == 6
    assert "Connected device is unauthorized." in caplog.text
    assert "ADB authorization prompt" in caplog.text


def test_main_returns_clear_error_when_device_is_offline(tmp_path, caplog):
    args = build_args(tmp_path)
    logger = logging.getLogger("test_cli_offline")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        exit_code = main(
            args=args,
            logger=logger,
            client=OfflineADBClient(),
            prompt=lambda _: "unused",
        )

    assert exit_code == 6
    assert "Connected device is offline." in caplog.text


def test_main_returns_clear_error_when_emulator_boot_is_incomplete(tmp_path, caplog):
    args = build_args(tmp_path)
    logger = logging.getLogger("test_cli_boot_incomplete")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        exit_code = main(
            args=args,
            logger=logger,
            client=BootingEmulatorADBClient(),
            prompt=lambda _: "unused",
        )

    assert exit_code == 7
    assert "Android boot is not complete" in caplog.text
