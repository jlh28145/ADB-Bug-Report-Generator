# Android Bug Report Script

## Overview
This Python script automates the process of collecting various data and logs from a connected Android device using ADB (Android Debug Bridge). It organizes the collected files into a structured directory and generates a zipped bug report for further analysis.

---

## Features
- Automatically detects connected Android devices.
- Allows selecting from multiple connected devices.
- Pulls specific directories and recent files from the device:
  - **Screen Recordings**
  - **QGroundControl Logs**
  - **Navsuite Logs**
- Collects detailed system information and logs, including:
  - Logcat logs
  - Device properties
  - Memory usage
  - CPU usage
  - Network stats
  - Battery information
  - Storage info
  - Event logs
- Generates an ADB bug report.
- Saves all data in a timestamped incident report folder.
- Option to zip the collected data for easy sharing or archival.

---

## Prerequisites
1. **Python Environment**: Install Python 3.7 or higher.
2. **ADB (Android Debug Bridge)**:
   - Ensure ADB is installed and available in your system's PATH.
   - Verify ADB connectivity with your device using `adb devices`.
3. **Required Python Packages**:
4. **ADB Device Setup**:
   - Enable Developer Options on your Android device.
   - Enable USB Debugging.

---

## Usage

### Running the Script
1. Connect the Android device to your computer via USB.
2. Run the script:
   ```bash
   python generate_bug_report.py
   ```
3. Follow the prompts to select a device (if multiple devices are connected).
4. Provide the number of recent files to pull (optional, default is 5).
5. Provide a summary of the incident when prompted.

### Command-line Arguments
- `-n`, `--num_recent_files`: Specify the number of recent files to pull from directories. Default is 5.
- `-s`, `--simplified`: Generate a simplified report (skips pulling directories and bug report).

Example:
```bash
python generate_bug_report.py -n 3 -s
```

---

## Directory Structure
The script organizes collected files as follows:
```
incident_reports/
  report_<timestamp>/
    Device Info/
      logcat_<timestamp>.txt
      device_info_<timestamp>.txt
      ...
    QGC Logs/
      <recent_console_logs>
    Screen Recordings/
      <recent_screen_recordings>
    Navsuite Logs/
      <recent_navsuite_logs>
    bugreport_<timestamp>.zip
```

---

## Output
1. **Incident Report Directory**: All files are saved in a timestamped directory under `incident_reports/`.
2. **Zipped Report**: A zip file containing the entire report is created for convenience.
3. **Metadata**: Includes a user-provided incident summary and other details.

---

## Error Handling
- If no devices are detected, the script exits with an appropriate message.
- If directories or files cannot be pulled, errors are logged, and the script continues execution for other tasks.

---

## Customization
To add or modify the data collected:
1. Edit the `log_types` dictionary to include new commands.
2. Add additional directories to the `directories_to_pull` list.

---

## Example
### Simplified Mode
To generate a simplified report with the 3 most recent files:
```bash
python generate_bug_report.py -n 3 -s
```

### Full Report
To generate a full incident report with all data:
```bash
python generate_bug_report.py -n 5
```

---

## Troubleshooting
1. **Device Not Detected**:
   - Ensure the device is properly connected and USB debugging is enabled.
   - Check ADB connectivity with `adb devices`.
2. **Permission Denied**:
   - Ensure you have appropriate permissions to execute ADB commands.
   - Verify that the ADB connection is authorized on the device.

---

