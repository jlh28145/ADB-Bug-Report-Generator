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
    collect_protected_path_diagnostics,
    evaluate_requested_collectors,
    filter_log_specs,
    get_application_directories,
    pull_directory,
    pull_recent_files,
    select_device,
)
from adb_bug_report_generator.compatibility import detect_device_profile, profile_to_metadata
from adb_bug_report_generator.exceptions import (
    ADBBugReportError,
    CompatibilityConstraintError,
    DeviceAuthorizationError,
    DeviceBootIncompleteError,
    NoConnectedDevicesError,
    DeviceUnavailableError,
    InvalidDeviceSelectionError,
)
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
        "--device",
        help="Use a specific connected device serial instead of prompting.",
    )
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
        "--incident-summary",
        help="Provide the incident summary without prompting.",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Do not prompt for user input; requires explicit choices or defaults.",
    )
    parser.add_argument(
        "--fail-on-partial",
        action="store_true",
        help="Return a non-zero exit code when any artifact collection step fails.",
    )
    parser.add_argument(
        "--package",
        help="Collect optional diagnostics for a specific Android package.",
    )
    parser.add_argument(
        "--allow-emulator",
        action="store_true",
        help="Allow execution against an Android emulator target.",
    )
    parser.add_argument(
        "--require-root",
        action="store_true",
        help="Fail if the selected device does not appear to have root available.",
    )
    parser.add_argument(
        "--compat-mode",
        choices=("auto", "strict", "permissive"),
        default="auto",
        help="Compatibility policy for target validation: auto, strict, or permissive.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="ADB command timeout in seconds.",
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
    except ADBBugReportError as exc:
        logger.error(format_operator_error(exc))
        return getattr(exc, "exit_code", 1)


def run(args, logger, client=None, prompt=input, device_prompt=input):
    """Orchestrate a collection run."""
    client = client or ADBClient(timeout_seconds=args.timeout)
    paths = create_report_paths(args.output_dir)
    options = CollectionOptions(
        num_recent_files=args.num_recent_files,
        simplified=args.simplified,
        include_logcat=args.include_logcat,
        include_device_info=args.include_device_info,
        include_bugreport=args.include_bugreport,
        package=args.package,
        device=args.device,
        incident_summary=args.incident_summary,
        non_interactive=args.non_interactive,
        fail_on_partial=args.fail_on_partial,
        timeout=args.timeout,
        allow_emulator=args.allow_emulator,
        require_root=args.require_root,
        compat_mode=args.compat_mode,
    )

    device_records = _list_device_records(client)
    devices = _resolve_ready_devices(device_records)
    selected_device = _resolve_selected_device(options, devices, device_prompt, logger)
    logger.info("Selected device: %s", selected_device)

    device_profile = detect_device_profile(client, selected_device)
    logger.info(
        "Detected profile: model=%s manufacturer=%s android=%s sdk=%s emulator=%s boot_completed=%s rooted=%s",
        device_profile.model,
        device_profile.manufacturer,
        device_profile.android_version,
        device_profile.sdk_level,
        device_profile.is_emulator,
        device_profile.is_boot_completed,
        device_profile.is_rooted,
    )
    log_specs = filter_log_specs(options)
    _validate_device_constraints(options, device_profile, log_specs)

    app_directories = list(device_profile.accessible_paths) or get_application_directories(client, selected_device)
    recent_file_commands = build_recent_file_commands(app_directories)

    if not app_directories:
        logger.info("No valid application directories found.")

    user_summary = _resolve_incident_summary(options, prompt, logger)
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
    artifact_results.append(
        collect_protected_path_diagnostics(
            client,
            selected_device,
            paths,
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
            "device": options.device,
            "incident_summary": options.incident_summary,
            "non_interactive": options.non_interactive,
            "fail_on_partial": options.fail_on_partial,
            "timeout": options.timeout,
            "allow_emulator": options.allow_emulator,
            "require_root": options.require_root,
            "compat_mode": options.compat_mode,
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

    if options.fail_on_partial and any(result.status == "failed" for result in artifact_results):
        logger.error("Run completed with partial failures and --fail-on-partial was set.")
        return 2

    return 0


def _resolve_selected_device(options, devices, device_prompt, logger):
    if options.device:
        if options.device not in devices:
            raise InvalidDeviceSelectionError(
                f"Requested device '{options.device}' is not connected. Available devices: {', '.join(devices) or 'none'}."
            )
        return options.device

    if options.non_interactive and len(devices) != 1:
        raise InvalidDeviceSelectionError(
            "Non-interactive mode requires exactly one connected device or an explicit --device value."
        )

    return select_device(devices, prompt=device_prompt, output=logger.info)


def _resolve_incident_summary(options, prompt, logger):
    if options.incident_summary is not None:
        return options.incident_summary

    if options.non_interactive:
        logger.info("No incident summary provided; using an empty summary in non-interactive mode.")
        return ""

    logger.info("Please provide a summary of the incident.")
    return prompt("Incident Summary: ")


def _validate_device_constraints(options, device_profile, log_specs):
    if device_profile.is_emulator and not device_profile.is_boot_completed:
        raise DeviceBootIncompleteError(
            "Emulator target detected, but Android boot is not complete. Wait for the emulator to finish booting and try again."
        )

    if (
        device_profile.is_emulator
        and options.compat_mode != "permissive"
        and not options.allow_emulator
    ):
        raise CompatibilityConstraintError(
            "Emulator target detected. Re-run with --allow-emulator to continue or use a physical device."
        )

    if options.require_root and not device_profile.is_rooted:
        raise CompatibilityConstraintError(
            "This run requires root access, but the selected device does not appear rooted."
        )

    if options.compat_mode != "strict":
        return

    unsupported_collectors = evaluate_requested_collectors(options, device_profile, log_specs)
    if not unsupported_collectors:
        return

    details = "; ".join(item["detail"] for item in unsupported_collectors)
    raise CompatibilityConstraintError(
        "Strict compatibility mode rejected this run because one or more requested collectors are unsupported "
        f"on the selected device: {details}"
    )


def _list_device_records(client):
    if hasattr(client, "list_device_records"):
        return client.list_device_records()

    return [{"serial": serial, "state": "device"} for serial in client.list_devices()]


def _resolve_ready_devices(device_records):
    ready_devices = [record["serial"] for record in device_records if record.get("state") == "device"]
    if ready_devices:
        return ready_devices

    if not device_records:
        raise NoConnectedDevicesError("No devices connected. Please connect a device and try again.")

    unauthorized = [record["serial"] for record in device_records if record.get("state") == "unauthorized"]
    if unauthorized:
        raise DeviceAuthorizationError(
            "Connected device is unauthorized. Check the device for an ADB authorization prompt and accept it before retrying."
        )

    offline = [record["serial"] for record in device_records if record.get("state") == "offline"]
    if offline:
        raise DeviceUnavailableError(
            "Connected device is offline. Reconnect the device or restart ADB before retrying."
        )

    raise DeviceUnavailableError(
        "No connected devices are currently available for collection."
    )
