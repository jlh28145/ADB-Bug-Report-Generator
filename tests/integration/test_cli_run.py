"""Integration tests for CLI orchestration with a fake ADB client."""

import logging
from types import SimpleNamespace
from zipfile import ZipFile

from tests import _bootstrap  # noqa: F401
from adb_bug_report_generator.cli import format_operator_error, main, run
from adb_bug_report_generator.exceptions import AdbCommandError
from tests.integration.fakes import (
    FakeADBClient,
    MissingAdbClient,
    NoDeviceADBClient,
    PartiallyFailingADBClient,
)


def test_run_creates_zip_archive_with_expected_artifacts(tmp_path):
    args = SimpleNamespace(
        num_recent_files=2,
        simplified=True,
        include_bugreport=False,
        output_dir=str(tmp_path / "output"),
    )
    logger = logging.getLogger("test_cli_integration")
    fake_client = FakeADBClient()

    exit_code = run(args, logger, client=fake_client, prompt=lambda _: "integration summary")

    assert exit_code == 0

    zip_files = list((tmp_path / "output").glob("QA_bug_report_*.zip"))
    assert len(zip_files) == 1

    with ZipFile(zip_files[0]) as archive:
        archive_names = set(archive.namelist())
        assert "Device Info/logcat_" in " ".join(archive_names)
        assert "Navsuite Logs/navsuite.log" in archive_names
        assert "Screen Recordings/screen-001.mp4" in archive_names
        assert "user_report.txt" in archive_names

        metadata = archive.read("user_report.txt").decode("utf-8")
        assert "integration summary" in metadata
        assert "emulator-5554" in metadata


def test_run_still_creates_archive_when_one_pull_fails(tmp_path):
    args = SimpleNamespace(
        num_recent_files=2,
        simplified=True,
        include_bugreport=False,
        output_dir=str(tmp_path / "output"),
    )
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
        assert "user_report.txt" in archive_names

        metadata = archive.read("user_report.txt").decode("utf-8")
        assert "partial failure summary" in metadata


def test_run_includes_bugreport_when_requested(tmp_path):
    args = SimpleNamespace(
        num_recent_files=2,
        simplified=False,
        include_bugreport=True,
        output_dir=str(tmp_path / "output"),
    )
    logger = logging.getLogger("test_cli_bugreport")
    fake_client = FakeADBClient()

    exit_code = run(args, logger, client=fake_client, prompt=lambda _: "bugreport summary")

    assert exit_code == 0

    zip_files = list((tmp_path / "output").glob("QA_bug_report_*.zip"))
    assert len(zip_files) == 1

    with ZipFile(zip_files[0]) as archive:
        archive_names = set(archive.namelist())
        assert "bugreport_" in " ".join(archive_names)
        assert "Pictures/" in " ".join(archive_names)
        assert "Movies/" in " ".join(archive_names)


def test_main_returns_clear_error_when_no_devices_found(tmp_path, caplog):
    args = SimpleNamespace(
        num_recent_files=2,
        simplified=True,
        include_bugreport=False,
        output_dir=str(tmp_path / "output"),
        verbose=False,
    )
    logger = logging.getLogger("test_cli_no_device")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        exit_code = main(
            args=args,
            logger=logger,
            client=NoDeviceADBClient(),
            prompt=lambda _: "unused",
        )

    assert exit_code == 1
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
    args = SimpleNamespace(
        num_recent_files=2,
        simplified=True,
        include_bugreport=False,
        output_dir=str(tmp_path / "output"),
        verbose=False,
    )
    logger = logging.getLogger("test_cli_missing_adb")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        exit_code = main(
            args=args,
            logger=logger,
            client=MissingAdbClient(),
            prompt=lambda _: "unused",
        )

    assert exit_code == 1
    assert "ADB executable not found." in caplog.text
    assert "Install Android Platform Tools" in caplog.text
    assert "Command: adb devices." in caplog.text
