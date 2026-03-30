"""Filesystem helpers for report creation."""

import json
import re
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

INVALID_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
CONTROL_CHARS = re.compile(r"[\x00-\x1F\x7F]")


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
    incident_dir = validate_output_root(output_root)
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


def write_json_file(path, content):
    """Write JSON content to disk."""
    path.write_text(json.dumps(content, indent=2, sort_keys=True), encoding="utf-8")


def create_zip_archive(source_dir, output_filename):
    """Create a zip archive containing report files."""

    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in source_dir.rglob("*"):
            if file_path.is_file():
                zipf.write(file_path, file_path.relative_to(source_dir))


def cleanup_report_dir(report_dir):
    """Remove the temporary extracted report directory."""
    shutil.rmtree(report_dir)


def sanitize_filename_component(name, fallback="artifact"):
    """Return a filesystem-safe filename component."""
    sanitized = INVALID_FILENAME_CHARS.sub("_", Path(name).name).strip("._-")
    return sanitized or fallback


def sanitize_metadata_text(value):
    """Strip control characters from metadata text fields."""
    if value is None:
        return None
    return CONTROL_CHARS.sub("", str(value))


def validate_output_root(output_root):
    """Validate the requested output root path."""
    path = Path(output_root).expanduser()
    if path.exists() and not path.is_dir():
        raise ValueError(f"Output path '{path}' exists and is not a directory.")
    return path
