"""Unit tests for filesystem helpers."""

from tests import _bootstrap  # noqa: F401
from adb_bug_report_generator.filesystem import create_report_paths, create_zip_archive


def test_create_report_paths_creates_expected_directories(tmp_path):
    paths = create_report_paths(tmp_path / "output")

    assert paths.incident_dir.exists()
    assert paths.report_dir.exists()
    assert paths.screen_recordings_dir.exists()
    assert paths.qgc_logs_dir.exists()
    assert paths.device_info_dir.exists()
    assert paths.navsuite_log_dir.exists()


def test_create_zip_archive_writes_metadata_and_files(tmp_path):
    source_dir = tmp_path / "report"
    source_dir.mkdir()
    sample_file = source_dir / "device_info.txt"
    sample_file.write_text("hello", encoding="utf-8")

    zip_path = tmp_path / "report.zip"
    create_zip_archive(source_dir, zip_path, "metadata")

    assert zip_path.exists()
    assert (source_dir / "metadata.txt").exists()
