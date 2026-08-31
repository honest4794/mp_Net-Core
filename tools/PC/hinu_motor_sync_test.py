#!/usr/bin/env python3
"""Test 2: offline timing/frame synchronization of both black motor Slaves."""

import argparse
import json
import os
import sys

from hinu_motor_bench_common import ROOT, black_profiles, load_json, write_markdown_report


SLAVE_ROOT = os.path.join(ROOT, "slave")
if SLAVE_ROOT not in sys.path:
    sys.path.insert(0, SLAVE_ROOT)

from lib.hw.uart_motor import STOP, UartMotor
from lib.sw.effect_core import Effect
from lib.sw.pixel_layout import PixelLayout
from pixel.effects.effects import uart_motor_dev_sine, uart_motor_story_mode


EFFECTS_PATH = os.path.join(SLAVE_ROOT, "pixel", "effects", "effects.json")
MAPPING_PATH = os.path.join(
    SLAVE_ROOT, "pixel", "map", "hi_nu_uart_motor_test.json"
)
MODE_PATHS = {
    0: os.path.join(SLAVE_ROOT, "pixel", "registry.json"),
    1: os.path.join(SLAVE_ROOT, "pixel", "modes", "motor_max_open.json"),
    2: os.path.join(SLAVE_ROOT, "pixel", "modes", "motor_dev_sine.json"),
    3: os.path.join(SLAVE_ROOT, "pixel", "modes", "story_mode_motor.json"),
}


class FakeClock:
    def __init__(self):
        self.now_ms = 0

    def __call__(self):
        return self.now_ms

    @staticmethod
    def diff(a, b):
        return a - b


class TimestampUART:
    def __init__(self, clock):
        self.clock = clock
        self.writes = []

    def write(self, data):
        self.writes.append((self.clock.now_ms, bytes(data)))
        return len(data)


def _mode(mode_id):
    data = load_json(MODE_PATHS[mode_id])
    if mode_id == 0:
        return next(item for item in data["modes"] if item["id"] == 0)
    return data


def _effect(mode):
    name = mode["map"][0]["effect"]
    params = next(
        item for item in load_json(EFFECTS_PATH)["effects"] if item["name"] == name
    )
    if name == "uart_motor_dev_sine":
        cls = uart_motor_dev_sine
    elif name == "uart_motor_story_mode":
        cls = uart_motor_story_mode
    else:
        cls = Effect
    return cls(name, params), params


def _duration_frames(params):
    if params.get("program"):
        cycle = int(params["program"][-1]["end_Time"])
    else:
        cycle = 0
    return cycle * int(params.get("cycles", 1))


def _simulate_profile(profile, mode_id, scheduled_start_ms=300):
    mode = _mode(mode_id)
    effect, params = _effect(mode)
    duration_frames = _duration_frames(params)
    frame_interval = profile["frame_interval_ms"]
    clock = FakeClock()
    uart = TimestampUART(clock)
    motor_cfg = profile["motor"]
    motor = UartMotor({
        "version": motor_cfg.get("version", 1),
        "addresses": profile["motor_addresses"],
        "uart": uart,
        "clock": clock,
        "clock_diff": FakeClock.diff,
        "dStay": motor_cfg.get("dStay", 2048),
        "sync_broadcast_span": motor_cfg.get("sync_broadcast_span", 0),
        "sync_tx_interval_ms": motor_cfg.get("sync_tx_interval_ms", 0),
    })
    mapping = load_json(MAPPING_PATH)
    layout = PixelLayout(["uartMotor1"], {"uartMotor1": motor.num_pixels})
    layout.register_mapping(mapping["id"], mapping["name"], mapping["groups"])
    write_mode = mode["map"][0]["write"]

    first_motion_ms = None
    controlled_history = []
    for frame_no in range(duration_frames + 1):
        clock.now_ms = scheduled_start_ms + frame_no * frame_interval
        target = bytearray(motor.frame_size)
        layout.scatter(
            target,
            mapping["name"],
            "all_uart_motors",
            effect.frame(frame_no),
            write_mode,
        )
        motor.st_load_and_convert(target, 0)
        motor.st_show()
        values = tuple(motor.buffer[address - 1] for address in profile["motor_addresses"])
        controlled_history.append(values)
        if first_motion_ms is None and any(value != STOP for value in values):
            first_motion_ms = clock.now_ms

    final_values = controlled_history[-1]
    if mode_id == 0:
        peak = min(value for values in controlled_history for value in values)
    else:
        peak = max(value for values in controlled_history for value in values)
    return {
        "cid": profile["cid"],
        "addresses": profile["motor_addresses"],
        "scheduled_start_ms": scheduled_start_ms,
        "first_motion_ms": first_motion_ms,
        "stop_at_ms": duration_frames * frame_interval,
        "final_values": final_values,
        "peak_value": peak,
        "history": controlled_history,
        "uart_writes": uart.writes,
    }


def run_offline_sync_test(mode_ids=(0, 1, 2, 3)):
    profiles = black_profiles()
    modes = []
    for mode_id in mode_ids:
        runs = [_simulate_profile(profile, int(mode_id)) for profile in profiles]
        uniform_within_each_slave = all(
            len(set(values)) == 1
            for run in runs
            for values in run["history"]
        )
        same_history = (
            [values[0] for values in runs[0]["history"]]
            == [values[0] for values in runs[1]["history"]]
        )
        same_frame_times = (
            [stamp for stamp, _frame in runs[0]["uart_writes"]]
            == [stamp for stamp, _frame in runs[1]["uart_writes"]]
        )
        start_skew = abs(runs[0]["scheduled_start_ms"] - runs[1]["scheduled_start_ms"])
        motion_skew = abs(runs[0]["first_motion_ms"] - runs[1]["first_motion_ms"])
        stop_skew = abs(runs[0]["stop_at_ms"] - runs[1]["stop_at_ms"])
        final_value = runs[0]["final_values"][0]
        passed = (
            uniform_within_each_slave
            and same_history
            and same_frame_times
            and start_skew == 0
            and motion_skew == 0
            and stop_skew == 0
            and final_value == STOP
            and all(value == STOP for run in runs for value in run["final_values"])
        )
        modes.append({
            "mode_id": int(mode_id),
            "scheduled_start_skew_ms": start_skew,
            "first_motion_skew_ms": motion_skew,
            "stop_skew_ms": stop_skew,
            "stop_at_ms": runs[0]["stop_at_ms"],
            "peak_value": runs[0]["peak_value"],
            "final_value": final_value,
            "uart_write_count": len(runs[0]["uart_writes"]),
            "result": "PASS" if passed else "FAIL",
        })
    return {
        "result": "PASS" if all(item["result"] == "PASS" for item in modes) else "FAIL",
        "motor_addresses": [
            address for profile in profiles for address in profile["motor_addresses"]
        ],
        "modes": modes,
        "hardware": "NOT RUN",
    }


def _write_report(path, result):
    rows = [
        (
            "Mode {}".format(item["mode_id"]),
            "start/motion/stop skew={}/{}/{}ms；stop={}ms；final=0x{:02X}".format(
                item["scheduled_start_skew_ms"],
                item["first_motion_skew_ms"],
                item["stop_skew_ms"],
                item["stop_at_ms"],
                item["final_value"],
            ),
            item["result"],
        )
        for item in result["modes"]
    ]
    write_markdown_report(
        path,
        "Hi-Nu 兩黑 Slave／七 motor 同步測試紀錄",
        "Host 以真實 JSON effect、兩份 black config 及 UART-412 encoder 重播 Mode 0–3。",
        rows,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modes", nargs="+", type=int, default=[0, 1, 2, 3])
    parser.add_argument("--report")
    args = parser.parse_args(argv)
    if any(mode not in (0, 1, 2, 3) for mode in args.modes):
        parser.error("--modes only accepts 0, 1, 2, 3")
    result = run_offline_sync_test(tuple(args.modes))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.report:
        _write_report(args.report, result)
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
