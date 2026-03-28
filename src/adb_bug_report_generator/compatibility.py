"""Device capability detection and compatibility helpers."""

from dataclasses import asdict, dataclass

from adb_bug_report_generator.collector import APPLICATION_DIRECTORIES


KNOWN_COMMANDS = (
    "getprop",
    "dumpsys",
    "logcat",
    "bugreport",
    "ifconfig",
    "ip",
    "top",
)


@dataclass(frozen=True)
class DeviceProfile:
    """Detected capabilities and device metadata for a target serial."""

    serial: str
    model: str
    manufacturer: str
    android_version: str
    sdk_level: int | None
    is_emulator: bool
    is_rooted: bool
    accessible_paths: tuple[str, ...]
    available_commands: dict[str, bool]


def detect_device_profile(client, serial):
    """Collect a basic device profile using ADB shell commands."""
    model = _shell_or_unknown(client, "getprop ro.product.model", serial)
    manufacturer = _shell_or_unknown(client, "getprop ro.product.manufacturer", serial)
    android_version = _shell_or_unknown(client, "getprop ro.build.version.release", serial)
    sdk_level = _parse_int(client.shell_text("getprop ro.build.version.sdk", device=serial))

    emulator_property = client.shell_text("getprop ro.kernel.qemu", device=serial)
    is_emulator = serial.startswith("emulator-") or emulator_property == "1"
    is_rooted = _detect_root(client, serial)
    accessible_paths = tuple(_detect_accessible_paths(client, serial))
    available_commands = {name: _command_exists(client, name, serial) for name in KNOWN_COMMANDS}

    return DeviceProfile(
        serial=serial,
        model=model,
        manufacturer=manufacturer,
        android_version=android_version,
        sdk_level=sdk_level,
        is_emulator=is_emulator,
        is_rooted=is_rooted,
        accessible_paths=accessible_paths,
        available_commands=available_commands,
    )


def profile_to_metadata(profile):
    """Serialize a device profile to metadata-friendly primitives."""
    return asdict(profile)


def _shell_or_unknown(client, command, serial):
    result = client.shell_text(command, device=serial)
    return result or "unknown"


def _parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _detect_root(client, serial):
    result = client.shell_text("command -v su >/dev/null 2>&1 && echo available", device=serial)
    return result == "available"


def _detect_accessible_paths(client, serial):
    paths = []
    for path in APPLICATION_DIRECTORIES:
        exists = client.shell_text(f"test -d '{path}' && echo exists", device=serial)
        if exists == "exists":
            paths.append(path)
    return paths


def _command_exists(client, command, serial):
    result = client.shell_text(f"command -v {command} >/dev/null 2>&1 && echo available", device=serial)
    return result == "available"
