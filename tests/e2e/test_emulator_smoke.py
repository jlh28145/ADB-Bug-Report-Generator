"""Opt-in emulator-backed smoke coverage."""

import json
import logging
import os
from types import SimpleNamespace
from zipfile import ZipFile

import pytest

from adb_bug_report_generator.adb import ADBClient
from adb_bug_report_generator.cli import run
from tests import _bootstrap  # noqa: F401

pytestmark = pytest.mark.skipif(
    os.environ.get("ADB_RUN_EMULATOR_SMOKE") != "1",
    reason="Set ADB_RUN_EMULATOR_SMOKE=1 to execute emulator-backed smoke coverage.",
)


def test_emulator_smoke_collects_core_artifacts(tmp_path):
    serial = os.environ.get("ADB_EMULATOR_SERIAL")
    if not serial:
        pytest.skip(
            "Set ADB_EMULATOR_SERIAL to the target emulator serial, for example emulator-5554."
        )

    args = SimpleNamespace(
        device=serial,
        num_recent_files=1,
        simplified=True,
        include_logcat=True,
        include_device_info=True,
        include_bugreport=False,
        package=None,
        incident_summary="emulator smoke test",
        non_interactive=True,
        fail_on_partial=False,
        timeout=60.0,
        output_dir=str(tmp_path / "output"),
        verbose=False,
        allow_emulator=True,
        require_root=False,
        compat_mode="auto",
    )

    logger = logging.getLogger("tests.e2e.emulator_smoke")

    exit_code = run(
        args,
        logger,
        client=ADBClient(timeout_seconds=args.timeout),
        prompt=lambda _: "unused",
        device_prompt=lambda _: serial,
    )

    assert exit_code == 0

    zip_files = list((tmp_path / "output").glob("QA_bug_report_*.zip"))
    assert len(zip_files) == 1

    with ZipFile(zip_files[0]) as archive:
        archive_names = set(archive.namelist())
        assert "Device Info/logcat.txt" in archive_names
        assert "Device Info/device_info.txt" in archive_names
        assert "metadata.json" in archive_names
        assert "run_summary.txt" in archive_names

        metadata = json.loads(archive.read("metadata.json").decode("utf-8"))
        assert metadata["device"] == serial
        assert metadata["incident_summary"] == "emulator smoke test"
        assert metadata["device_profile"]["is_emulator"] is True
