#!/usr/bin/env python3
"""Collect and compare Black Slave scheduling jitter from two explicit USB ports."""

import argparse
import json
import queue
import re
import threading
import time


SAMPLE_RE = re.compile(
    r"\[SYNC-STRESS\]\s+lead=(\d+)\s+tag=(\d+)\s+"
    r"target=(\d+)\s+actual=(\d+)\s+jitter=(-?\d+)"
)
BATCH_RE = re.compile(
    r"\[SYNC-STRESS-BATCH\]\s+lead=(\d+)\s+count=(\d+)\s+data=([0-9a-fA-F]+)"
)
DEFAULT_LEADS_MS = (300, 100, 50, 20, 10, 5, 2, 1)


def parse_sample(line):
    match = SAMPLE_RE.search(line)
    if match is None:
        return None
    lead, tag, target, actual, jitter = (int(value) for value in match.groups())
    return {
        "lead_ms": lead,
        "tag": tag,
        "target_ms": target,
        "actual_ms": actual,
        "jitter_ms": jitter,
    }


def parse_batch(line):
    match = BATCH_RE.search(line)
    if match is None:
        return None
    lead_ms = int(match.group(1))
    count = int(match.group(2))
    data = bytes.fromhex(match.group(3))
    if count != 100 or len(data) != count:
        return None
    return [
        {"lead_ms": lead_ms, "tag": index + 1, "jitter_ms": value}
        for index, value in enumerate(data)
    ]


def store_first_sample(store, sample):
    key = (sample["lead_ms"], sample["tag"])
    if key in store:
        return False
    store[key] = sample
    return True


def _percentile(values, percentage):
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1,
                       (len(ordered) * percentage + 99) // 100 - 1))
    return ordered[index]


def _stats(values):
    if not values:
        return {"mean_skew_ms": None, "max_skew_ms": None,
                "p95_skew_ms": None, "p99_skew_ms": None}
    return {
        "mean_skew_ms": round(sum(values) / len(values), 3),
        "max_skew_ms": max(values),
        "p95_skew_ms": _percentile(values, 95),
        "p99_skew_ms": _percentile(values, 99),
    }


def summarize_samples(slave1, slave2, expected_per_lead=100):
    by1 = {(item["lead_ms"], item["tag"]): item for item in slave1}
    by2 = {(item["lead_ms"], item["tag"]): item for item in slave2}
    common = sorted(set(by1) & set(by2))
    leads = sorted({key[0] for key in set(by1) | set(by2)}, reverse=True)
    skew_by_lead = {}
    all_skews = []
    for lead in leads:
        values = [abs(by1[key]["jitter_ms"] - by2[key]["jitter_ms"])
                  for key in common if key[0] == lead]
        all_skews.extend(values)
        skew_by_lead[str(lead)] = {
            "matched_samples": len(values),
            **_stats(values),
        }
    expected_pairs = expected_per_lead * len(leads)
    return {
        "matched_samples": len(common),
        "missing_samples": max(0, expected_pairs - len(common)),
        "overall": _stats(all_skews),
        "by_lead_ms": skew_by_lead,
    }


def _reader(label, port, baud, output, stop_event):
    import serial

    with serial.Serial(port, baudrate=baud, timeout=0.1) as stream:
        while not stop_event.is_set():
            raw = stream.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="replace").rstrip()
            batch = parse_batch(line)
            if batch is not None:
                for sample in batch:
                    output.put((label, sample))
                continue
            sample = parse_sample(line)
            if sample is not None:
                output.put((label, sample))


def collect(slave1_port, slave2_port, samples_per_lead, timeout_seconds,
            baud=115200, verbose=True):
    received = {"slave1": {}, "slave2": {}}
    output = queue.Queue()
    stop_event = threading.Event()
    threads = [
        threading.Thread(target=_reader,
                         args=("slave1", slave1_port, baud, output, stop_event),
                         daemon=True),
        threading.Thread(target=_reader,
                         args=("slave2", slave2_port, baud, output, stop_event),
                         daemon=True),
    ]
    for thread in threads:
        thread.start()
    deadline = time.monotonic() + timeout_seconds
    expected = len(DEFAULT_LEADS_MS) * samples_per_lead
    try:
        while time.monotonic() < deadline:
            try:
                label, sample = output.get(timeout=0.25)
            except queue.Empty:
                continue
            if not store_first_sample(received[label], sample):
                continue
            if verbose:
                print("{} lead={} tag={} jitter={}ms ({}/{})".format(
                    label, sample["lead_ms"], sample["tag"],
                    sample["jitter_ms"], len(received[label]), expected))
            if all(len(items) >= expected for items in received.values()):
                break
    finally:
        stop_event.set()
        for thread in threads:
            thread.join(timeout=1)
    return summarize_samples(list(received["slave1"].values()),
                             list(received["slave2"].values()),
                             samples_per_lead)


def main():
    parser = argparse.ArgumentParser(
        description="Measure Black Slave1/2 scheduled-start skew")
    parser.add_argument("--slave1-port", required=True)
    parser.add_argument("--slave2-port", required=True)
    parser.add_argument("--samples-per-lead", type=int, default=100)
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--json-output")
    args = parser.parse_args()

    report = collect(args.slave1_port, args.slave2_port,
                     args.samples_per_lead, args.timeout_seconds, args.baud,
                     verbose=not args.quiet)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as handle:
            handle.write(rendered + "\n")
    return 0 if report["missing_samples"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
