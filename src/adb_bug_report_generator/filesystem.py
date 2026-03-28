"""Filesystem helpers for report creation."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import shutil
import zipfile


@dataclass(frozen=True)
class ReportPaths:
    """Local output paths for a report run."""

    incident_dir: Path
    report_dir: Path
    screen_recordings_dir: Path
    qgc_logs_dir: Path
    device_info_dir: Path
    navsuite_log_dir: Path
    timestamp: str


def create_report_paths(output_root="incident_reports"):
    """Create report directories for a single run."""
    incident_dir = Path(output_root)
    incident_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%m-%d-%Y_%H:%M:%S")
    report_dir = incident_dir / f"report_{timestamp}"

    paths = ReportPaths(
        incident_dir=incident_dir,
        report_dir=report_dir,
        screen_recordings_dir=report_dir / "Screen Recordings",
        qgc_logs_dir=report_dir / "QGC Logs",
        device_info_dir=report_dir / "Device Info",
        navsuite_log_dir=report_dir / "Navsuite Logs",
        timestamp=timestamp,
    )

    for path in (
        paths.report_dir,
        paths.screen_recordings_dir,
        paths.qgc_logs_dir,
        paths.device_info_dir,
        paths.navsuite_log_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)

    return paths


def write_text_file(path, content):
    """Write text content to disk."""
    path.write_text(content, encoding="utf-8")


def create_zip_archive(source_dir, output_filename, metadata):
    """Create a zip archive containing report files and metadata."""
    metadata_path = source_dir / "metadata.txt"
    write_text_file(metadata_path, metadata)

    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in source_dir.rglob("*"):
            if file_path.is_file():
                zipf.write(file_path, file_path.relative_to(source_dir))
        zipf.write(metadata_path, "user_report.txt")


def cleanup_report_dir(report_dir):
    """Remove the temporary extracted report directory."""
    shutil.rmtree(report_dir)
