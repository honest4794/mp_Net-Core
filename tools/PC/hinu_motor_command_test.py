#!/usr/bin/env python3
"""Test 1: black Master NC4 command control of black Slave13/Slave20 motors."""

import argparse
import json
import os
import shutil
import subprocess
import sys

from hinu_motor_bench_common import (
    BOARD_PORTS,
    ROOT,
    black_profiles,
    decode_single_frame,
    dispatch_to_profile,
    encode_nc4,
    write_markdown_report,
)


DEVICE_SCRIPT = os.path.join(ROOT, "tools", "ESP", "hinu_motor_master.py")
PROJECT_MAIN = os.path.join(
    ROOT, "tools", "ESP", "hinu_motor_project_main.py")


def run_offline_mode(mode_id, start_delay_ms=300, received_at_ms=1000):
    payload, frame = encode_nc4(0x3105, {
        "mode_type": 1,
        "mode_id": int(mode_id),
        "start_delay_ms": int(start_delay_ms),
        "brightness": 255,
    })
    version, address, command, decoded_payload = decode_single_frame(frame)
    slaves = []
    for profile in black_profiles():
        shared = dispatch_to_profile(
            profile, command, decoded_payload, received_at_ms=received_at_ms
        )
        schedule = shared["pixel_remote_schedule"]
        slaves.append({
            "cid": profile["cid"],
            "motor_addresses": profile["motor_addresses"],
            "start_at_ms": schedule["start_at"],
        })
    deadlines = {item["start_at_ms"] for item in slaves}
    return {
        "result": "PASS" if len(deadlines) == 1 else "FAIL",
        "nc4_version": version,
        "address": address,
        "command": "{:04x}".format(command),
        "payload_hex": payload.hex(),
        "mode_id": int(mode_id),
        "slaves": slaves,
    }


def run_offline_stop():
    payload, frame = encode_nc4(0x3106, {"action": 1})
    _version, _address, command, decoded_payload = decode_single_frame(frame)
    slaves = []
    for profile in black_profiles():
        shared = dispatch_to_profile(profile, command, decoded_payload)
        slaves.append({
            "cid": profile["cid"],
            "motor_addresses": profile["motor_addresses"],
            "running": int(shared["pixel_nc4_status"]["running"]),
        })
    return {
        "result": "PASS" if all(not item["running"] for item in slaves) else "FAIL",
        "command": "{:04x}".format(command),
        "payload_hex": payload.hex(),
        "slaves": slaves,
    }


def _mpremote_prefix():
    executable = shutil.which("mpremote")
    if executable:
        return [executable]
    executable = shutil.which("uvx")
    if executable:
        return [executable, "mpremote"]
    raise RuntimeError("mpremote not found; install mpremote or uvx")


def _mpremote(port, expression=None, copy=False):
    command = _mpremote_prefix() + ["connect", port]
    if copy:
        command += ["fs", "cp", DEVICE_SCRIPT, ":/hinu_motor_master.py"]
    else:
        command += ["exec", expression]
    return subprocess.run(command, check=False).returncode


def _deploy_project_master(port):
    prefix = _mpremote_prefix() + ["connect", port, "fs", "cp"]
    if subprocess.run(
            prefix + [DEVICE_SCRIPT, ":/hinu_motor_master.py"],
            check=False).returncode:
        return 1
    return subprocess.run(
        prefix + [PROJECT_MAIN, ":/main.py"], check=False).returncode


def _write_report(path, results):
    rows = []
    for result in results:
        rows.append((
            "MODE_SET {}".format(result["mode_id"]),
            "CID 000D/0014 start_at={}ms，payload={}".format(
                result["slaves"][0]["start_at_ms"], result["payload_hex"]),
            result["result"],
        ))
    write_markdown_report(
        path,
        "Hi-Nu 黑板 Master→Slaves motor command 測試紀錄",
        "Slave13／20 profiles 使用同一 NC4 broadcast deadline；hardware 未接。",
        rows,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)

    offline = sub.add_parser("offline", help="用真實 schema/handler 做 host 驗證")
    offline.add_argument("--modes", nargs="+", type=int, default=[0, 1, 2, 3])
    offline.add_argument("--start-delay-ms", type=int, default=300)
    offline.add_argument("--report")

    sub.add_parser("ports", help="列出 Figma 六板 port mapping")
    deploy = sub.add_parser("deploy-master", help="把 command sender 放到 black Master")
    deploy.add_argument("--port", default=BOARD_PORTS["black_master"])
    project = sub.add_parser(
        "deploy-project-master",
        help="部署開機自動 Mode 0→1→2 的 real-project Black Master",
    )
    project.add_argument("--port", required=True)
    send = sub.add_parser("send-mode", help="由 black Master 廣播 MODE_SET")
    send.add_argument("mode", type=int, choices=(0, 1, 2, 3))
    send.add_argument("--start-delay-ms", type=int, default=300)
    send.add_argument("--port", default=BOARD_PORTS["black_master"])
    stop = sub.add_parser("stop", help="由 black Master 廣播安全停止")
    stop.add_argument("--port", default=BOARD_PORTS["black_master"])

    args = parser.parse_args(argv)
    if args.action == "ports":
        print(json.dumps(BOARD_PORTS, indent=2, ensure_ascii=False))
        return 0
    if args.action == "offline":
        results = [
            run_offline_mode(mode, args.start_delay_ms)
            for mode in args.modes
        ]
        results.append(run_offline_stop())
        print(json.dumps(results, indent=2, ensure_ascii=False))
        if args.report:
            _write_report(args.report, results[:-1])
        return 0 if all(item["result"] == "PASS" for item in results) else 1
    if args.action == "deploy-master":
        return _mpremote(args.port, copy=True)
    if args.action == "deploy-project-master":
        return _deploy_project_master(args.port)
    if args.action == "send-mode":
        expr = "import hinu_motor_master as m; m.send_mode({}, {})".format(
            args.mode, args.start_delay_ms
        )
        return _mpremote(args.port, expression=expr)
    if args.action == "stop":
        return _mpremote(
            args.port,
            expression="import hinu_motor_master as m; m.stop()",
        )
    return 2


if __name__ == "__main__":
    sys.exit(main())
