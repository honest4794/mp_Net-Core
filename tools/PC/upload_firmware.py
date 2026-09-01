#!/usr/bin/env python3
"""Flash MicroPython and deploy this repository's application files safely."""

import argparse
import configparser
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time


FORBIDDEN_PORT_OPTIONS = {"port", "upload_port", "monitor_port"}
PYTHON_CACHE_SUFFIXES = {".pyc", ".pyo", ".pyd"}


class UploadConfig:
    """Validated stable upload settings; USB ports intentionally do not exist."""

    def __init__(self, firmware, source, uploader, device_config, chip, baud,
                 address, esptool, mpremote, reconnect_seconds):
        self.firmware = firmware
        self.source = source
        self.uploader = uploader
        self.device_config = device_config
        self.chip = chip
        self.baud = baud
        self.address = address
        self.esptool = esptool
        self.mpremote = mpremote
        self.reconnect_seconds = reconnect_seconds


def _required(section, option):
    value = section.get(option, "").strip()
    if not value:
        raise ValueError("missing [upload] option: %s" % option)
    return value


def _resolve_path(base_dir, value):
    path = Path(os.path.expanduser(value))
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def load_config(path):
    """Load stable local settings and reject any persisted USB port."""
    config_path = Path(path).expanduser().resolve()
    parser = configparser.ConfigParser()
    if not parser.read(config_path, encoding="utf-8"):
        raise ValueError("upload config not found: %s" % config_path)
    if "upload" not in parser:
        raise ValueError("upload config requires an [upload] section")

    section = parser["upload"]
    saved_ports = FORBIDDEN_PORT_OPTIONS.intersection(section.keys())
    if saved_ports:
        raise ValueError(
            "upload_local.ini must not store USB ports: %s" %
            ", ".join(sorted(saved_ports)))

    base_dir = config_path.parent
    try:
        reconnect_seconds = float(section.get("reconnect_seconds", "3"))
    except ValueError as error:
        raise ValueError("reconnect_seconds must be a number") from error
    if reconnect_seconds < 0:
        raise ValueError("reconnect_seconds must not be negative")

    device_config_value = section.get("device_config", "").strip()
    device_config = (
        _resolve_path(base_dir, device_config_value)
        if device_config_value else None
    )
    return UploadConfig(
        firmware=_resolve_path(base_dir, _required(section, "firmware")),
        source=_resolve_path(base_dir, _required(section, "source")),
        uploader=_resolve_path(base_dir, _required(section, "uploader")),
        device_config=device_config,
        chip=_required(section, "chip"),
        baud=_required(section, "baud"),
        address=section.get("address", "0x0").strip() or "0x0",
        esptool=tuple(shlex.split(_required(section, "esptool"))),
        mpremote=tuple(shlex.split(_required(section, "mpremote"))),
        reconnect_seconds=reconnect_seconds,
    )


def collect_upload_files(source):
    """Return stable local-to-device mappings for an application tree."""
    source = Path(source)
    mappings = []
    for local_path in source.rglob("*"):
        relative = local_path.relative_to(source)
        if not local_path.is_file():
            continue
        if "__pycache__" in relative.parts:
            continue
        if local_path.suffix.lower() in PYTHON_CACHE_SUFFIXES:
            continue
        remote_path = "/" + relative.as_posix()
        mappings.append((local_path, remote_path))
    return sorted(mappings, key=lambda item: item[1])


def build_flash_command(config, port):
    """Build an esptool write command with an explicit current port."""
    return list(config.esptool) + [
        "--chip", config.chip,
        "--port", port,
        "--baud", config.baud,
        "write-flash", "-z", config.address,
        os.fspath(config.firmware),
    ]


def build_upload_command(config, port, local_path, remote_path):
    """Build a normal-REPL uploader command with an explicit current port."""
    return [
        sys.executable,
        "-B",
        os.fspath(config.uploader),
        port,
        os.fspath(local_path),
        remote_path,
    ]


def confirm_erase(port, input_fn=input):
    """Require an exact port-bound phrase before erasing a board."""
    expected = "ERASE " + port
    answer = input_fn("Type %r to erase the board: " % expected)
    return answer.strip() == expected


def build_erase_command(config, port):
    """Build an esptool erase command with an explicit current port."""
    return list(config.esptool) + [
        "--chip", config.chip,
        "--port", port,
        "erase-flash",
    ]


def build_reset_command(config, port):
    """Build an mpremote reset command with an explicit current port."""
    return list(config.mpremote) + ["connect", port, "reset"]


def build_list_command():
    """Use the active Python interpreter to enumerate serial ports."""
    return [sys.executable, "-B", "-m", "serial.tools.list_ports", "-v"]


def run_command(command, dry_run=False, runner=subprocess.run):
    """Print an argv-safe preview, then run it unless this is a dry-run."""
    print("+ " + shlex.join([os.fspath(part) for part in command]))
    if not dry_run:
        runner(command, check=True)


def _require_port(port):
    port = (port or "").strip()
    if not port:
        raise ValueError("an explicitly verified --port is required")
    return port


def _require_file(path, label):
    if not Path(path).is_file():
        raise ValueError("%s not found: %s" % (label, path))


def _require_directory(path, label):
    if not Path(path).is_dir():
        raise ValueError("%s not found: %s" % (label, path))


def flash_firmware(config, port, erase=False, dry_run=False, input_fn=input,
                   runner=subprocess.run):
    """Optionally erase, then flash the configured image."""
    port = _require_port(port)
    _require_file(config.firmware, "firmware image")
    if erase:
        if not dry_run and not confirm_erase(port, input_fn=input_fn):
            print("Erase cancelled; firmware was not written.", file=sys.stderr)
            return False
        run_command(build_erase_command(config, port), dry_run, runner)
    run_command(build_flash_command(config, port), dry_run, runner)
    return True


def deploy_files(config, port, dry_run=False, runner=subprocess.run):
    """Upload the application tree and reset only after every file succeeds."""
    port = _require_port(port)
    _require_directory(config.source, "application source")
    _require_file(config.uploader, "normal-REPL uploader")
    mappings = collect_upload_files(config.source)
    if config.device_config is not None:
        _require_file(config.device_config, "device config")
        mappings = [mapping for mapping in mappings
                    if mapping[1] != "/config.json"]
        mappings.insert(0, (config.device_config, "/config.json"))
    if not mappings:
        raise ValueError("application source contains no uploadable files: %s" %
                         config.source)

    for local_path, remote_path in mappings:
        run_command(
            build_upload_command(config, port, local_path, remote_path),
            dry_run,
            runner,
        )
    run_command(build_reset_command(config, port), dry_run, runner)
    return len(mappings)


def list_serial_ports(dry_run=False, runner=subprocess.run):
    """List serial ports without selecting or remembering one."""
    run_command(build_list_command(), dry_run, runner)


def run_all(config, initial_port, erase=False, dry_run=False, input_fn=input,
            runner=subprocess.run, sleep_fn=time.sleep):
    """Flash, require a fresh port decision, then deploy the application."""
    initial_port = _require_port(initial_port)
    if erase and config.device_config is None:
        raise ValueError(
            "all --erase requires device_config so /config.json is restored")
    if erase:
        _require_file(config.device_config, "device config")
    if not flash_firmware(
            config, initial_port, erase=erase, dry_run=dry_run,
            input_fn=input_fn, runner=runner):
        return False

    if dry_run:
        print("# Real run pauses here and requires a freshly verified files port.")
        deploy_files(config, initial_port, dry_run=True, runner=runner)
        return True

    sleep_fn(config.reconnect_seconds)
    print("Firmware finished. Re-enumerating ports before project deployment.")
    list_serial_ports(runner=runner)
    files_port = _require_port(input_fn("Verified port for application files: "))
    deploy_files(config, files_port, runner=runner)
    return True


def _build_parser():
    parser = argparse.ArgumentParser(
        description="Flash MicroPython and/or deploy slave files safely.")
    parser.add_argument(
        "--config", default="upload_local.ini",
        help="local INI settings (default: upload_local.ini)")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="print commands without opening a serial port")
    subparsers = parser.add_subparsers(dest="action", required=True)

    subparsers.add_parser("list", help="list current serial ports")

    flash_parser = subparsers.add_parser(
        "flash", help="write the configured MicroPython image")
    flash_parser.add_argument("--port", required=True)
    flash_parser.add_argument("--erase", action="store_true")

    files_parser = subparsers.add_parser(
        "files", help="deploy the configured application tree")
    files_parser.add_argument("--port", required=True)

    all_parser = subparsers.add_parser(
        "all", help="flash, reconfirm the port, and deploy files")
    all_parser.add_argument("--port", required=True)
    all_parser.add_argument("--erase", action="store_true")
    return parser


def main(argv=None):
    args = _build_parser().parse_args(argv)
    try:
        if args.action == "list":
            list_serial_ports(dry_run=args.dry_run)
            return 0

        config = load_config(args.config)
        if args.action == "flash":
            ok = flash_firmware(
                config, args.port, erase=args.erase, dry_run=args.dry_run)
        elif args.action == "files":
            deploy_files(config, args.port, dry_run=args.dry_run)
            ok = True
        else:
            ok = run_all(
                config, args.port, erase=args.erase, dry_run=args.dry_run)
        return 0 if ok else 1
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print("upload failed: %s" % error, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("upload cancelled", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
