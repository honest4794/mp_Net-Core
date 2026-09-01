#!/usr/bin/env python3
"""Shared host helpers for the two Hi-Nu motor bench programs."""

import json
import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SLAVE_ROOT = os.path.join(ROOT, "slave")
if SLAVE_ROOT not in sys.path:
    sys.path.insert(0, SLAVE_ROOT)

from action import pixel_actions
from lib.sys.proto import ADDR_BROADCAST, Proto, StreamParser
from lib.sys.schema_codec import SchemaCodec
from lib.sys.schema_loader import SchemaStore
from lib.sys.sys_bus import bus


BLACK_PROFILES = (
    os.path.join(ROOT, "ports", "S3", "ESP32-S3_1_18_hinu_black",
                 "slave13", "config.json"),
    os.path.join(ROOT, "ports", "S3", "ESP32-S3_1_18_hinu_black",
                 "slave20", "config.json"),
)

BOARD_PORTS = {
    "blue_master": "/dev/cu.usbmodem1127101",
    "blue_slave1": "/dev/cu.usbmodem1127201",
    "blue_slave2": "/dev/cu.usbmodem1127401",
    "black_master": "/dev/cu.usbmodem1127301",
    "black_slave1": "/dev/cu.usbmodem1121301",
    "black_slave2": "/dev/cu.usbmodem1121201",
}

_SCHEMA_STORE = None


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def black_profiles():
    profiles = []
    for path in BLACK_PROFILES:
        config = load_json(path)
        motor = config["uartMotor"]["list"][0]
        profiles.append({
            "path": path,
            "cid": config["System"]["cID"],
            "motor_addresses": sorted(int(value) for value in motor["address"]),
            "frame_interval_ms": int(config["System"]["frame_interval_ms"]),
            "motor": motor,
        })
    return sorted(profiles, key=lambda item: item["cid"])


def schema_store():
    global _SCHEMA_STORE
    if _SCHEMA_STORE is None:
        _SCHEMA_STORE = SchemaStore(os.path.join(SLAVE_ROOT, "schema"))
        _SCHEMA_STORE.finalize()
    return _SCHEMA_STORE


def encode_nc4(command, fields):
    store = schema_store()
    definition = store.get(command)
    payload = SchemaCodec.encode(definition, fields)
    frame = bytes(Proto.pack(command, payload, addr=ADDR_BROADCAST))
    return payload, frame


def decode_single_frame(frame):
    parser = StreamParser()
    parser.feed(frame)
    parsed = parser.pop_frame()
    if parsed is None:
        raise ValueError("NC4 frame did not decode")
    version, address, command, payload = parsed
    return version, address, command, bytes(payload)


class FixedTime:
    now_ms = 0

    @classmethod
    def ticks_ms(cls):
        return cls.now_ms

    @staticmethod
    def ticks_add(value, delta):
        return value + delta

    @staticmethod
    def ticks_diff(a, b):
        return a - b


def dispatch_to_profile(profile, command, payload, received_at_ms=0):
    """Decode with the real schema and execute the real pixel action handler."""
    store = schema_store()
    args = SchemaCodec.decode(store.get(command), payload, store)
    old_shared = bus.shared
    old_cid = bus.cid
    old_time = pixel_actions.time
    try:
        bus.shared = {}
        bus.cid = int(profile["cid"], 16)
        FixedTime.now_ms = int(received_at_ms)
        pixel_actions.time = FixedTime
        if command == 0x3105:
            pixel_actions.on_mode_set({}, args)
        elif command == 0x3106:
            bus.shared["pixel_nc4_status"] = {
                "mode_type": 1,
                "mode_id": 0,
                "started_at": received_at_ms,
                "running": 1,
            }
            pixel_actions.on_mode_stop({}, args)
        else:
            raise ValueError("unsupported bench command 0x{:04X}".format(command))
        return dict(bus.shared)
    finally:
        bus.shared = old_shared
        bus.cid = old_cid
        pixel_actions.time = old_time


def write_markdown_report(path, title, summary, rows, hardware_status="NOT RUN"):
    """Write the same status/observation/result shape as the NC4 acceptance log."""
    lines = [
        "# {}".format(title),
        "",
        "> 此檔由測試程式產生。Host 與 hardware 結果分開記錄。",
        "",
        "## 〇、一分鐘理解",
        "",
        summary,
        "",
        "## 一、狀態與時序",
        "",
        "| 項目 | 實測現象 | 結果 |",
        "|---|---|---|",
    ]
    for item, observed, result in rows:
        lines.append("| {} | {} | {} |".format(item, observed, result))
    lines.extend([
        "",
        "## 二、限制與注意事項",
        "",
        "- UART-412 沒有 ACK；Host frame PASS 不代表 ATtiny 已套用或 motor 已完成。",
        "- 本輪 hardware 狀態：`{}`。".format(hardware_status),
        "- 接駁六板後仍要 upload、monitor，並由人眼或 logic analyzer 記錄實體同步。",
        "",
        "## 三、結論",
        "",
        "- Host／offline 結果只證明 codec、排程、JSON 與 frame contract。",
        "- Hardware 未執行時，不得把本報告寫成實機 PASS。",
        "",
    ])
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
