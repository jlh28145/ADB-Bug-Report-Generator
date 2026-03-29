"""Collection workflow and orchestration."""

from dataclasses import asdict, dataclass
from pathlib import Path

from adb_bug_report_generator.exceptions import NoConnectedDevicesError


DIRECTORIES_TO_PULL = [
    "/sdcard/Pictures",
    "/sdcard/Movies",
]

APPLICATION_DIRECTORIES = [
    "/sdcard/Android/data/org.mavlink.qgroundcontrol/files/PDW_GCS",
    "/sdcard/Android/data/ai.pdw.gcs/files/PDW_GCS",
]

LOG_SPECS = (
    ("logcat", "logcat.txt", ("logcat -d",), "logcat"),
    ("device_info", "device_info.txt", ("getprop", "dumpsys window"), "getprop_or_dumpsys"),
    ("meminfo_pdw_gcs", "meminfo_pdw_gcs.txt", ("dumpsys meminfo ai.pdw.gcs",), "dumpsys"),
    (
        "meminfo_qgroundcontrol",
        "meminfo_qgroundcontrol.txt",
        ("dumpsys meminfo org.mavlink.qgroundcontrol",),
        "dumpsys",
    ),
    ("cpu_usage", "cpu_usage.txt", ("top -n 1",), "top"),
    ("network_stats", "network_stats.txt", ("dumpsys netstats",), "dumpsys"),
    ("network_config", "network_config.txt", ("ifconfig", "ip addr"), "ifconfig_or_ip"),
    ("battery_info", "battery_info.txt", ("dumpsys battery",), "dumpsys"),
    ("storage_info", "storage_info.txt", ("df -h",), "df"),
    ("event_logs", "event_logs.txt", ("dumpsys activity",), "dumpsys"),
)


COMMAND_REQUIREMENTS = {
    "logcat": ("logcat",),
    "getprop": ("getprop",),
    "getprop_or_dumpsys": ("getprop", "dumpsys"),
    "bugreport": ("bugreport",),
    "dumpsys": ("dumpsys",),
    "pidof": ("pidof",),
    "top": ("top",),
    "df": tuple(),
    "ifconfig_or_ip": ("ifconfig", "ip"),
}


def _noop(*_args, **_kwargs):
    """Default output sink for non-CLI callers."""


@dataclass
class CollectionOptions:
    """Collection-time options for the workflow."""

    num_recent_files: int
    simplified: bool
    include_logcat: bool = True
    include_device_info: bool = True
    include_bugreport: bool = False
    package: str | None = None
    device: str | None = None
    incident_summary: str | None = None
    non_interactive: bool = False
    fail_on_partial: bool = False
    timeout: float | None = None
    allow_emulator: bool = False
    require_root: bool = False
    compat_mode: str = "auto"


@dataclass
class ArtifactResult:
    """Status information for a collected or skipped artifact."""

    name: str
    status: str
    path: str | None = None
    detail: str = ""

    def to_metadata(self):
        return asdict(self)


def select_device(devices, prompt=input, output=None):
    """Pick a device from the list or prompt interactively."""
    output = output or _noop

    if not devices:
        raise NoConnectedDevicesError("No devices connected. Please connect a device and try again.")

    if len(devices) == 1:
        output(f"Using the only connected device: {devices[0]}")
        return devices[0]

    output("Multiple devices detected:")
    for index, device in enumerate(devices, start=1):
        output(f"{index}: {device}")

    while True:
        try:
            choice = int(prompt("Select a device by number: "))
        except ValueError:
            output("Invalid input. Please enter a number.")
            continue

        if 1 <= choice <= len(devices):
            return devices[choice - 1]

        output("Invalid choice. Please try again.")


def get_application_directories(client, device):
    """Check which application directories exist on the target device."""
    existing_dirs = []
    for dir_path in APPLICATION_DIRECTORIES:
        result = client.shell_text(f"test -d '{dir_path}' && echo exists", device=device)
        if result == "exists":
            existing_dirs.append(dir_path)
    return existing_dirs


def build_recent_file_commands(app_directories):
    """Return the list of recent-file collection commands."""
    commands = [
        ("/sdcard/Movies", "ls -t /sdcard/Movies | grep '^screen-'"),
        ("/sdcard/Documents/Navsuite", "ls -t /sdcard/Documents/Navsuite"),
    ]

    for app_dir in app_directories:
        commands.append(
            (f"{app_dir}/Logs/ConsoleLogs", f"ls -t {app_dir}/Logs/ConsoleLogs")
        )

    return commands


def pull_directory(client, directory, dest_dir, device, output=None):
    """Pull top-level files and subdirectories from a device directory."""
    output = output or _noop
    local_dir = Path(dest_dir) / Path(directory).name
    local_dir.mkdir(parents=True, exist_ok=True)
    results = []

    items = client.shell_text(f"ls -p {directory}", device=device)
    if not items:
        output(f"No items found in {directory}")
        return results

    for item in items.splitlines():
        if ".thumbnails" in item:
            continue
        if directory == "/sdcard/Movies" and item.startswith("screen-"):
            continue

        item_path = f"{directory}/{item.rstrip('/')}"
        try:
            client.pull(item_path, local_dir, device=device)
            output(f"Pulled {item_path} to {local_dir}")
            results.append(
                ArtifactResult(
                    name=f"pull:{item_path}",
                    status="collected",
                    path=str(local_dir / Path(item_path).name),
                )
            )
        except Exception:
            output(f"Failed to pull {item_path}")
            results.append(
                ArtifactResult(
                    name=f"pull:{item_path}",
                    status="failed",
                    detail=f"Failed to pull {item_path}.",
                )
            )

    return results


def pull_recent_files(client, directory, ls_command, dest_dir, num_files, device, report_paths, output=None):
    """Pull the most recent files from a specific device directory."""
    output = output or _noop
    output(f"Getting {num_files} most recent file(s) from {directory} on device {device}")
    recent_files = client.shell_text(f"{ls_command} | head -n {num_files}", device=device)
    results = []

    if not recent_files:
        output(f"No files found in {directory}")
        return results

    for recent_file in recent_files.splitlines():
        file_path = f"{directory}/{recent_file}"

        if "Movies" in directory and recent_file.startswith("screen-"):
            local_path = report_paths.screen_recordings_dir / recent_file
        elif "ConsoleLogs" in directory:
            local_path = report_paths.qgc_logs_dir / recent_file
        elif "Navsuite" in directory:
            local_path = report_paths.navsuite_log_dir / recent_file
        else:
            local_path = Path(dest_dir) / recent_file

        try:
            client.pull(file_path, local_path, device=device)
            output(f"Pulled {file_path} to {local_path}")
            results.append(
                ArtifactResult(
                    name=f"pull:{file_path}",
                    status="collected",
                    path=str(local_path),
                )
            )
        except Exception:
            output(f"Failed to pull file {file_path}")
            results.append(
                ArtifactResult(
                    name=f"pull:{file_path}",
                    status="failed",
                    detail=f"Failed to pull file {file_path}.",
                )
            )

    return results


def collect_bugreport(client, dest_dir, device, device_profile, output=None):
    """Collect a bugreport zip."""
    output = output or _noop
    if not _supports_requirement(device_profile, "bugreport"):
        detail = "Skipped bugreport collection because the required command is unavailable on this device."
        output(detail)
        return ArtifactResult(name="bugreport", status="skipped", detail=detail)

    output("Generating bug report...")
    bugreport_zip = Path(dest_dir) / "bugreport.zip"
    try:
        client.bugreport(bugreport_zip, device=device)
        output(f"Bug report saved to {bugreport_zip}")
        return ArtifactResult(name="bugreport", status="collected", path=str(bugreport_zip))
    except Exception:
        detail = "Failed to generate bugreport."
        output(detail)
        return ArtifactResult(name="bugreport", status="failed", detail=detail)


def collect_logs(client, device, report_paths, device_profile, output=None, log_specs=LOG_SPECS):
    """Collect text-based diagnostic artifacts using compatibility-aware fallbacks."""
    output = output or _noop
    results = []
    for log_name, filename, commands, requirement in log_specs:
        compatibility_reason = _compatibility_skip_reason(log_name, device_profile)
        if compatibility_reason:
            output(compatibility_reason)
            results.append(ArtifactResult(name=log_name, status="skipped", detail=compatibility_reason))
            continue

        if not _supports_requirement(device_profile, requirement):
            detail = f"Skipped {log_name} because the required command is unavailable on this device."
            output(detail)
            results.append(ArtifactResult(name=log_name, status="skipped", detail=detail))
            continue

        log_path = report_paths.device_info_dir / filename
        output(f"Collecting {log_name}...")
        used_command = None
        result = ""

        for command in commands:
            result = client.shell_text(command, device=device)
            if result:
                used_command = command
                break

        if result:
            log_path.write_text(result, encoding="utf-8")
            output(f"{log_name} saved to {log_path}")
            detail = f"Collected using `{used_command}`." if used_command else ""
            results.append(
                ArtifactResult(
                    name=log_name,
                    status="collected",
                    path=str(log_path),
                    detail=detail,
                )
            )
        else:
            detail = f"No output returned for {log_name}."
            output(detail)
            results.append(ArtifactResult(name=log_name, status="failed", detail=detail))

    return results


def collect_package_diagnostics(client, device, report_paths, package, device_profile, output=None):
    """Collect optional package diagnostics for a specific application."""
    output = output or _noop
    if not package:
        return ArtifactResult(
            name="package_diagnostics",
            status="skipped",
            detail="Package diagnostics were not requested for this run.",
        )

    if not _supports_requirement(device_profile, "dumpsys"):
        detail = "Skipped package diagnostics because dumpsys is unavailable on this device."
        output(detail)
        return ArtifactResult(name="package_diagnostics", status="skipped", detail=detail)

    sections = []

    package_dump = client.shell_text(f"dumpsys package {package}", device=device)
    if package_dump:
        sections.append(f"## dumpsys package {package}\n{package_dump}")

    if _supports_requirement(device_profile, "pidof"):
        package_pid = client.shell_text(f"pidof {package}", device=device)
        if package_pid:
            sections.append(f"## pidof {package}\n{package_pid}")

    if not sections:
        detail = f"No package diagnostics returned for {package}."
        output(detail)
        return ArtifactResult(name="package_diagnostics", status="failed", detail=detail)

    diagnostics_path = report_paths.device_info_dir / "package_diagnostics.txt"
    diagnostics_path.write_text("\n\n".join(sections), encoding="utf-8")
    output(f"Package diagnostics saved to {diagnostics_path}")
    return ArtifactResult(
        name="package_diagnostics",
        status="collected",
        path=str(diagnostics_path),
        detail=f"Collected package diagnostics for {package}.",
    )


def evaluate_requested_collectors(options, device_profile, log_specs):
    """Summarize requested collector support for compatibility policy decisions."""
    unsupported = []

    for log_name, _filename, _commands, requirement in log_specs:
        compatibility_reason = _compatibility_skip_reason(log_name, device_profile)
        if compatibility_reason:
            unsupported.append({"name": log_name, "detail": compatibility_reason})
            continue

        if not _supports_requirement(device_profile, requirement):
            unsupported.append(
                {
                    "name": log_name,
                    "detail": f"{log_name} requires { _describe_requirement(requirement) }.",
                }
            )

    if options.include_bugreport and not _supports_requirement(device_profile, "bugreport"):
        unsupported.append(
            {
                "name": "bugreport",
                "detail": "bugreport requires the bugreport command.",
            }
        )

    if options.package and not _supports_requirement(device_profile, "dumpsys"):
        unsupported.append(
            {
                "name": "package_diagnostics",
                "detail": "package diagnostics require dumpsys.",
            }
        )

    return unsupported


def filter_log_specs(options):
    """Return enabled log specs based on collection options."""
    enabled_specs = []
    for spec in LOG_SPECS:
        log_name = spec[0]
        if log_name == "logcat" and not options.include_logcat:
            continue
        if log_name != "logcat" and not options.include_device_info:
            continue
        enabled_specs.append(spec)
    return tuple(enabled_specs)


def build_run_summary(artifact_results):
    """Build a human-readable run summary."""
    lines = ["Run Summary", ""]
    for result in artifact_results:
        line = f"- {result.name}: {result.status}"
        if result.path:
            line += f" ({result.path})"
        if result.detail:
            line += f" - {result.detail}"
        lines.append(line)
    return "\n".join(lines) + "\n"


def _supports_requirement(device_profile, requirement):
    commands = COMMAND_REQUIREMENTS.get(requirement, tuple())
    if not commands:
        return True
    return any(device_profile.available_commands.get(command, False) for command in commands)


def _describe_requirement(requirement):
    commands = COMMAND_REQUIREMENTS.get(requirement, tuple())
    if requirement == "ifconfig_or_ip":
        return "ifconfig or ip"
    if requirement == "getprop_or_dumpsys":
        return "getprop or dumpsys"
    if not commands:
        return requirement
    if len(commands) == 1:
        return commands[0]
    return " or ".join(commands)


def _compatibility_skip_reason(log_name, device_profile):
    if log_name == "battery_info" and device_profile.is_emulator:
        return "Skipped battery_info because it is not a reliable hardware signal on emulator targets."
    return ""
