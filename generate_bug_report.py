#!/usr/bin/env python3

import os
import subprocess
import zipfile
from datetime import datetime
import argparse
import re
import sys

# Define file and directory paths on the ADB device
directories_to_pull = [
    "/sdcard/Pictures",
    "/sdcard/Movies"
]

# Local directory to save the incident report
incident_dir = "incident_reports"
os.makedirs(incident_dir, exist_ok=True)

# Timestamp for unique report naming
timestamp = datetime.now().strftime("%m-%d-%Y_%H:%M:%S")
report_dir = os.path.join(incident_dir, f"report_{timestamp}")
os.makedirs(report_dir, exist_ok=True)

# Subfolders within the report directory
screen_recordings_dir = os.path.join(report_dir, "Screen Recordings")
qgc_logs_dir = os.path.join(report_dir, "QGC Logs")
device_info_dir = os.path.join(report_dir, "Device Info")
navsuite_log_dir = os.path.join(report_dir, "Navsuite Logs")

os.makedirs(screen_recordings_dir, exist_ok=True)
os.makedirs(qgc_logs_dir, exist_ok=True)
os.makedirs(device_info_dir, exist_ok=True)
os.makedirs(navsuite_log_dir, exist_ok=True)

def get_connected_devices():
    """Retrieve a list of connected ADB devices."""
    try:
        result = subprocess.run(["adb", "devices"], text=True, capture_output=True, check=True)
        lines = result.stdout.strip().splitlines()
        devices = [line.split()[0] for line in lines[1:] if "device" in line]
        return devices
    except subprocess.CalledProcessError as e:
        print(f"Error listing ADB devices: {e}")
        return []

def select_device(devices):
    """Prompt the user to select a device from the list."""
    if not devices:
        print("No devices connected. Please connect a device and try again.")
        sys.exit(1)
    elif len(devices) == 1:
        print(f"Using the only connected device: {devices[0]}")
        return devices[0]
    else:
        print("Multiple devices detected:")
        for i, device in enumerate(devices, start=1):
            print(f"{i}: {device}")
        while True:
            try:
                choice = int(input("Select a device by number: "))
                if 1 <= choice <= len(devices):
                    return devices[choice - 1]
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

def run_adb_command(command, device=None):
    """Run an ADB command for a specific device and return the output with escape codes removed."""
    try:
        # Prefix command with the device ID if provided
        if device:
            command = f"adb -s {device} {command}"
        print(f"Executing command: {command}")
        result = subprocess.run(command, shell=True, text=True, capture_output=True, check=True)
        clean_output = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout.strip())  # Remove ANSI escape codes
        return clean_output
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{command}': {e}")
        return None

def pull_directory(directory, dest_dir, device):
    """Pull files and subdirectories from the ADB device, excluding .thumbnails."""
    local_dir = os.path.join(dest_dir, os.path.basename(directory))
    os.makedirs(local_dir, exist_ok=True)

    # List all top-level files and folders in the directory
    command = f'shell "ls -p {directory}"'
    items = run_adb_command(command, device=device)
    
    if items:
        for item in items.splitlines():
            if ".thumbnails" in item:
                continue  # Skip .thumbnails
            item_path = os.path.join(directory, item.rstrip("/"))
            try:
                subprocess.run(["adb", "-s", device, "pull", item_path, local_dir], check=True)
                print(f"Pulled {item_path} to {local_dir}")
            except subprocess.CalledProcessError:
                print(f"Failed to pull {item_path}")
    else:
        print(f"No items found in {directory}")


def pull_recent_files(directory, ls_command, dest_dir, num_files, device):
    """Pull the most recent files from a specific directory."""
    print(f"Getting {num_files} most recent file(s) from {directory} on device {device}")
    command = f'shell "{ls_command} | head -n {num_files}"'
    recent_files = run_adb_command(command, device=device)
    if recent_files:
        for recent_file in recent_files.splitlines():
            # Build the correct file path
            file_path = f"{directory}/{recent_file}"
            
            # Determine local destination
            if "Movies" in directory and recent_file.startswith("screen-"):
                local_path = os.path.join(screen_recordings_dir, recent_file)
            elif "ConsoleLogs" in directory:
                local_path = os.path.join(qgc_logs_dir, recent_file)
            elif "Navsuite" in directory:
                local_path = os.path.join(navsuite_log_dir, recent_file)
            else:
                local_path = os.path.join(dest_dir, recent_file)

            try:
                subprocess.run(["adb", "-s", device, "pull", file_path, local_path], check=True)
                print(f"Pulled {file_path} to {local_path}")
            except subprocess.CalledProcessError:
                print(f"Failed to pull file {file_path}")
    else:
        print(f"No files found in {directory}")

def collect_bugreport(dest_dir, device):
    """Collect a bug report from the device."""
    print("Generating bug report...")
    bugreport_zip = os.path.join(dest_dir, f"bugreport_{timestamp}.zip")
    try:
        subprocess.run(["adb", "-s", device, "bugreport", bugreport_zip], check=True)
        print(f"Bug report saved to {bugreport_zip}")
    except subprocess.CalledProcessError:
        print("Failed to generate bug report")

def collect_logs(device):
    """Collect logs from the device."""
    log_types = {
        "logcat": "logcat -d",
        "device_info": "shell getprop",
        #ToDo - Add a check for both org.mavlink.qgroundcontrol and ai.pdw.gcs
        "meminfo": "shell dumpsys meminfo ai.pdw.gcs",
        "cpu_usage": "shell top -n 1",
        "network_stats": "shell dumpsys netstats",
        "network_config": "shell ifconfig",
        "battery_info": "shell dumpsys battery",
        "storage_info": "shell df -h",
        "event_logs": "shell dumpsys activity"
    }

    for log_name, command in log_types.items():
        log_path = os.path.join(device_info_dir, f"{log_name}_{timestamp}.txt")
        print(f"Collecting {log_name}...")
        output = run_adb_command(command, device=device)
        if output:
            with open(log_path, "w") as log_file:
                log_file.write(output)
            print(f"{log_name} saved to {log_path}")

def get_application_directories(device):
    """Check for the presence of both application folders and return the valid ones."""
    dirs_to_check = [
        '/sdcard/Android/data/org.mavlink.qgroundcontrol/files/PDW_GCS',
        '/sdcard/Android/data/ai.pdw.gcs/files/PDW_GCS'
    ]
    existing_dirs = []
    for dir_path in dirs_to_check:
        command = f"shell 'test -d {dir_path} && echo exists'"
        result = run_adb_command(command, device=device)
        if result == "exists":
            existing_dirs.append(dir_path)
    return existing_dirs

def create_zip(source_dir, output_filename, metadata):
    """Create a zip file containing all logs and metadata."""
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, source_dir))
        # Add metadata to the zip file
        metadata_path = os.path.join(source_dir, "metadata.txt")
        with open(metadata_path, "w") as meta_file:
            meta_file.write(metadata)
        zipf.write(metadata_path, "metadata.txt")
    print(f"Incident report created: {output_filename}")

# Main execution
if __name__ == "__main__":
    devices = get_connected_devices()
    selected_device = select_device(devices)
    print(f"Selected device: {selected_device}")

    parser = argparse.ArgumentParser(description="Generate an incident report from an Android device.")
    parser.add_argument("-n", "--num_recent_files", type=int, default=5, help="Number of recent files to pull (default: 1)")
    parser.add_argument("-s", "--simplified", action="store_true", help="Generate a simplified report (without directories and bug report)")
    args = parser.parse_args()

    # Get both application directories (if they exist)
    app_directories = get_application_directories(selected_device)

    # Adjust recent file commands based on the app directories found
    recent_file_commands = [
        ('/sdcard/Movies', 'ls -t /sdcard/Movies | grep "^screen-"'),
        ('/sdcard/Documents/Navsuite', 'ls -t /sdcard/Documents/Navsuite')
    ]

    if app_directories:
        for app_dir in app_directories:
            # Append with Logs/ConsoleLogs subdirectory for proper log fetching
            recent_file_commands.append(
                (f"{app_dir}/Logs/ConsoleLogs", f"ls -t {app_dir}/Logs/ConsoleLogs")
            )
    else:
        print("No valid application directories found.")

    # Step 1: Gather user summary
    print("Please provide a summary of the incident:")
    user_summary = input("Incident Summary: ")

    # Step 2: Pull specific directories (if not simplified)
    if not args.simplified:
        for directory in directories_to_pull:
            pull_directory(directory, report_dir, selected_device)

    # Step 3: Pull most recent files
    for directory, ls_command in recent_file_commands:
        pull_recent_files(directory, ls_command, report_dir, args.num_recent_files, selected_device)

    # Step 4: Collect logs
    collect_logs(selected_device)

    # Step 5: Collect bug report
    #if not args.simplified:
        #collect_bugreport(report_dir, selected_device)

    # Step 6: Create ZIP
    metadata = f"Incident Summary: {user_summary}\nTimestamp: {timestamp}\nDevice: {selected_device}"
    zip_file_name = os.path.join(incident_dir, f"QA_bug_report_{timestamp}.zip")
    create_zip(report_dir, zip_file_name, metadata)
