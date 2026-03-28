"""CLI entry point."""

import argparse
import json
import shlex

from adb_bug_report_generator.adb import ADBClient
from adb_bug_report_generator.collector import (
    ArtifactResult,
    DIRECTORIES_TO_PULL,
    CollectionOptions,
    build_recent_file_commands,
    build_run_summary,
    collect_bugreport,
    collect_logs,
    collect_package_diagnostics,
    filter_log_specs,
    get_application_directories,
    pull_directory,
    pull_recent_files,
    select_device,
)
from adb_bug_report_generator.compatibility import detect_device_profile, profile_to_metadata
from adb_bug_report_generator.exceptions import ADBBugReportError, DeviceSelectionError
from adb_bug_report_generator.filesystem import (
    cleanup_report_dir,
    create_report_paths,
    create_zip_archive,
    write_json_file,
    write_text_file,
)
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
        "--no-include-logcat",
        dest="include_logcat",
        action="store_false",
        help="Skip logcat collection.",
    )
    parser.add_argument(
        "--no-include-device-info",
        dest="include_device_info",
        action="store_false",
        help="Skip device-info and diagnostic text collection.",
    )
    parser.add_argument(
        "--include-bugreport",
        action="store_true",
        help="Include an ADB bugreport in the collected artifacts.",
    )
    parser.add_argument(
        "--package",
        help="Collect optional diagnostics for a specific Android package.",
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
    parser.set_defaults(include_logcat=True, include_device_info=True)
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
        include_logcat=args.include_logcat,
        include_device_info=args.include_device_info,
        include_bugreport=args.include_bugreport,
        package=args.package,
    )

    devices = client.list_devices()
    selected_device = select_device(devices, prompt=device_prompt, output=logger.info)
    logger.info("Selected device: %s", selected_device)

    device_profile = detect_device_profile(client, selected_device)
    logger.info(
        "Detected profile: model=%s manufacturer=%s android=%s sdk=%s emulator=%s rooted=%s",
        device_profile.model,
        device_profile.manufacturer,
        device_profile.android_version,
        device_profile.sdk_level,
        device_profile.is_emulator,
        device_profile.is_rooted,
    )

    app_directories = list(device_profile.accessible_paths) or get_application_directories(client, selected_device)
    recent_file_commands = build_recent_file_commands(app_directories)

    if not app_directories:
        logger.info("No valid application directories found.")

    logger.info("Please provide a summary of the incident.")
    user_summary = prompt("Incident Summary: ")
    artifact_results = []

    if not options.simplified:
        for directory in DIRECTORIES_TO_PULL:
            artifact_results.extend(
                pull_directory(client, directory, paths.report_dir, selected_device, output=logger.info)
            )

    for directory, ls_command in recent_file_commands:
        artifact_results.extend(
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
        )

    log_specs = filter_log_specs(options)
    if log_specs:
        artifact_results.extend(
            collect_logs(
                client,
                selected_device,
                paths,
                device_profile,
                output=logger.info,
                log_specs=log_specs,
            )
        )
    else:
        artifact_results.append(
            ArtifactResult(
                name="diagnostics",
                status="skipped",
                detail="Logcat and device-info collection were both disabled for this run.",
            )
        )

    if options.include_bugreport and not options.simplified:
        artifact_results.append(
            collect_bugreport(
            client,
            paths.report_dir,
            selected_device,
            device_profile,
            output=logger.info,
        )
        )
    else:
        artifact_results.append(
            ArtifactResult(
                name="bugreport",
                status="skipped",
                detail="Bugreport collection was not requested for this run.",
            )
        )

    artifact_results.append(
        collect_package_diagnostics(
            client,
            selected_device,
            paths,
            options.package,
            device_profile,
            output=logger.info,
        )
    )

    run_summary = build_run_summary(artifact_results)
    write_text_file(paths.report_dir / "run_summary.txt", run_summary)

    metadata = {
        "incident_summary": user_summary,
        "timestamp": paths.timestamp,
        "device": selected_device,
        "device_profile": profile_to_metadata(device_profile),
        "selected_options": {
            "num_recent_files": options.num_recent_files,
            "simplified": options.simplified,
            "include_logcat": options.include_logcat,
            "include_device_info": options.include_device_info,
            "include_bugreport": options.include_bugreport,
            "package": options.package,
            "output_dir": args.output_dir,
        },
        "artifacts": [result.to_metadata() for result in artifact_results],
    }
    write_json_file(paths.report_dir / "metadata.json", metadata)

    zip_file_name = paths.incident_dir / f"QA_bug_report_{paths.timestamp}.zip"
    create_zip_archive(paths.report_dir, zip_file_name)
    logger.info("Incident report created: %s", zip_file_name)

    try:
        cleanup_report_dir(paths.report_dir)
        logger.info("Cleaned up temporary folder: %s", paths.report_dir)
    except OSError as exc:
        logger.warning("Failed to delete temporary folder: %s", exc)

    return 0
