"""Collection workflow and orchestration."""

from dataclasses import dataclass
from pathlib import Path

from adb_bug_report_generator.exceptions import DeviceSelectionError


DIRECTORIES_TO_PULL = [
    "/sdcard/Pictures",
    "/sdcard/Movies",
]

APPLICATION_DIRECTORIES = [
    "/sdcard/Android/data/org.mavlink.qgroundcontrol/files/PDW_GCS",
    "/sdcard/Android/data/ai.pdw.gcs/files/PDW_GCS",
]

LOG_TYPES = {
    "logcat": "logcat -d",
    "device_info": "getprop",
    "meminfo_pdw_gcs": "dumpsys meminfo ai.pdw.gcs",
    "meminfo_qgroundcontrol": "dumpsys meminfo org.mavlink.qgroundcontrol",
    "cpu_usage": "top -n 1",
    "network_stats": "dumpsys netstats",
    "network_config": "ifconfig",
    "battery_info": "dumpsys battery",
    "storage_info": "df -h",
    "event_logs": "dumpsys activity",
}


@dataclass
class CollectionOptions:
    """Collection-time options for the workflow."""

    num_recent_files: int
    simplified: bool
    include_bugreport: bool = False


def select_device(devices, prompt=input, output=print):
    """Pick a device from the list or prompt interactively."""
    if not devices:
        raise DeviceSelectionError("No devices connected. Please connect a device and try again.")

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


def pull_directory(client, directory, dest_dir, device, output=print):
    """Pull top-level files and subdirectories from a device directory."""
    local_dir = Path(dest_dir) / Path(directory).name
    local_dir.mkdir(parents=True, exist_ok=True)

    items = client.shell_text(f"ls -p {directory}", device=device)
    if not items:
        output(f"No items found in {directory}")
        return

    for item in items.splitlines():
        if ".thumbnails" in item:
            continue
        if directory == "/sdcard/Movies" and item.startswith("screen-"):
            continue

        item_path = f"{directory}/{item.rstrip('/')}"
        try:
            client.pull(item_path, local_dir, device=device)
            output(f"Pulled {item_path} to {local_dir}")
        except Exception:
            output(f"Failed to pull {item_path}")


def pull_recent_files(client, directory, ls_command, dest_dir, num_files, device, report_paths, output=print):
    """Pull the most recent files from a specific device directory."""
    output(f"Getting {num_files} most recent file(s) from {directory} on device {device}")
    recent_files = client.shell_text(f"{ls_command} | head -n {num_files}", device=device)

    if not recent_files:
        output(f"No files found in {directory}")
        return

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
        except Exception:
            output(f"Failed to pull file {file_path}")


def collect_bugreport(client, dest_dir, device, timestamp, output=print):
    """Collect a bugreport zip."""
    output("Generating bug report...")
    bugreport_zip = Path(dest_dir) / f"bugreport_{timestamp}.zip"
    try:
        client.bugreport(bugreport_zip, device=device)
        output(f"Bug report saved to {bugreport_zip}")
    except Exception:
        output("Failed to generate bug report")


def collect_logs(client, device, report_paths, output=print):
    """Collect text-based diagnostic artifacts."""
    for log_name, command in LOG_TYPES.items():
        log_path = report_paths.device_info_dir / f"{log_name}_{report_paths.timestamp}.txt"
        output(f"Collecting {log_name}...")
        result = client.shell_text(command, device=device)
        if result:
            log_path.write_text(result, encoding="utf-8")
            output(f"{log_name} saved to {log_path}")
