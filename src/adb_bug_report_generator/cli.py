"""CLI entry point."""

import argparse
import shlex

from adb_bug_report_generator.adb import ADBClient
from adb_bug_report_generator.collector import (
    DIRECTORIES_TO_PULL,
    CollectionOptions,
    build_recent_file_commands,
    collect_bugreport,
    collect_logs,
    get_application_directories,
    pull_directory,
    pull_recent_files,
    select_device,
)
from adb_bug_report_generator.exceptions import ADBBugReportError, DeviceSelectionError
from adb_bug_report_generator.filesystem import cleanup_report_dir, create_report_paths, create_zip_archive
from adb_bug_report_generator.logging_config import setup_logging


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Generate an incident report from an Android device.")
    parser.add_argument(
        "-n",
        "--num-recent-files",
        dest="num_recent_files",
        type=int,
        default=5,
        help="Number of recent files to pull (default: 5)",
    )
    parser.add_argument(
        "-s",
        "--simplified",
        action="store_true",
        help="Generate a simplified report (without broad directory pulls)",
    )
    parser.add_argument(
        "--include-bugreport",
        action="store_true",
        help="Include an ADB bugreport in the collected artifacts.",
    )
    parser.add_argument(
        "--output-dir",
        default="incident_reports",
        help="Directory where incident reports should be written.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    return parser.parse_args()


def format_operator_error(exc):
    """Return a clear operator-facing error message."""
    if getattr(exc, "command", None):
        command = " ".join(shlex.quote(str(part)) for part in exc.command)
        if getattr(exc, "stderr", ""):
            return f"{exc} Command: {command}. Details: {exc.stderr}"
        return f"{exc} Command: {command}."

    return str(exc)


def main(args=None, logger=None, client=None, prompt=input, device_prompt=input):
    """Run the CLI workflow."""
    args = args or parse_args()
    logger = logger or setup_logging(verbose=args.verbose)

    try:
        return run(args, logger, client=client, prompt=prompt, device_prompt=device_prompt)
    except DeviceSelectionError as exc:
        logger.error(format_operator_error(exc))
        return 1
    except ADBBugReportError as exc:
        logger.error(format_operator_error(exc))
        return 1


def run(args, logger, client=None, prompt=input, device_prompt=input):
    """Orchestrate a collection run."""
    client = client or ADBClient()
    paths = create_report_paths(args.output_dir)
    options = CollectionOptions(
        num_recent_files=args.num_recent_files,
        simplified=args.simplified,
        include_bugreport=args.include_bugreport,
    )

    devices = client.list_devices()
    selected_device = select_device(devices, prompt=device_prompt, output=logger.info)
    logger.info("Selected device: %s", selected_device)

    app_directories = get_application_directories(client, selected_device)
    recent_file_commands = build_recent_file_commands(app_directories)

    if not app_directories:
        logger.info("No valid application directories found.")

    logger.info("Please provide a summary of the incident.")
    user_summary = prompt("Incident Summary: ")

    if not options.simplified:
        for directory in DIRECTORIES_TO_PULL:
            pull_directory(client, directory, paths.report_dir, selected_device, output=logger.info)

    for directory, ls_command in recent_file_commands:
        pull_recent_files(
            client,
            directory,
            ls_command,
            paths.report_dir,
            options.num_recent_files,
            selected_device,
            paths,
            output=logger.info,
        )

    collect_logs(client, selected_device, paths, output=logger.info)

    if options.include_bugreport and not options.simplified:
        collect_bugreport(
            client,
            paths.report_dir,
            selected_device,
            paths.timestamp,
            output=logger.info,
        )

    metadata = (
        f"Incident Summary: {user_summary}\n"
        f"Timestamp: {paths.timestamp}\n"
        f"Device: {selected_device}"
    )
    zip_file_name = paths.incident_dir / f"QA_bug_report_{paths.timestamp}.zip"
    create_zip_archive(paths.report_dir, zip_file_name, metadata)
    logger.info("Incident report created: %s", zip_file_name)

    try:
        cleanup_report_dir(paths.report_dir)
        logger.info("Cleaned up temporary folder: %s", paths.report_dir)
    except OSError as exc:
        logger.warning("Failed to delete temporary folder: %s", exc)

    return 0
