#!/usr/bin/env python3
"""Flash MicroPython and deploy this repository's application files safely."""

import configparser
import os
from pathlib import Path
import shlex
import sys


FORBIDDEN_PORT_OPTIONS = {"port", "upload_port", "monitor_port"}
PYTHON_CACHE_SUFFIXES = {".pyc", ".pyo", ".pyd"}


class UploadConfig:
    """Validated stable upload settings; USB ports intentionally do not exist."""

    def __init__(self, firmware, source, uploader, chip, baud, address,
                 esptool, mpremote, reconnect_seconds):
        self.firmware = firmware
        self.source = source
        self.uploader = uploader
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

    return UploadConfig(
        firmware=_resolve_path(base_dir, _required(section, "firmware")),
        source=_resolve_path(base_dir, _required(section, "source")),
        uploader=_resolve_path(base_dir, _required(section, "uploader")),
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
