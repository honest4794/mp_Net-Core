#!/usr/bin/env python3
"""Behavior contract for the two-port motor synchronization stress monitor."""

import os
import sys
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "tools", "PC")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import hinu_motor_sync_stress_monitor as monitor


class SyncStressMonitorTests(unittest.TestCase):
    def test_batch_parser_expands_one_hundred_tagged_jitter_values(self):
        samples = monitor.parse_batch(
            "[SYNC-STRESS-BATCH] lead=20 count=100 data=" + "01" * 100
        )

        self.assertEqual(100, len(samples))
        self.assertEqual(
            {"lead_ms": 20, "tag": 1, "jitter_ms": 1}, samples[0])
        self.assertEqual(
            {"lead_ms": 20, "tag": 100, "jitter_ms": 1}, samples[-1])

    def test_parser_extracts_device_measurement_from_prefixed_log(self):
        sample = monitor.parse_sample(
            "[12345] INFO [SYNC-STRESS] lead=20 tag=37 "
            "target=1300 actual=1301 jitter=1"
        )

        self.assertEqual(
            {"lead_ms": 20, "tag": 37, "target_ms": 1300,
             "actual_ms": 1301, "jitter_ms": 1},
            sample,
        )

    def test_summary_aligns_by_lead_and_tag_not_arrival_order(self):
        slave1 = [
            {"lead_ms": 10, "tag": 1, "jitter_ms": 0},
            {"lead_ms": 10, "tag": 2, "jitter_ms": 1},
        ]
        slave2 = [
            {"lead_ms": 10, "tag": 2, "jitter_ms": 1},
            {"lead_ms": 10, "tag": 1, "jitter_ms": 1},
        ]

        report = monitor.summarize_samples(slave1, slave2, expected_per_lead=2)

        self.assertEqual(2, report["matched_samples"])
        self.assertEqual(0, report["missing_samples"])
        self.assertEqual(0.5, report["overall"]["mean_skew_ms"])
        self.assertEqual(1, report["overall"]["max_skew_ms"])

    def test_summary_reports_a_dropped_slave_sample(self):
        slave1 = [
            {"lead_ms": 5, "tag": 1, "jitter_ms": 0},
            {"lead_ms": 5, "tag": 2, "jitter_ms": 0},
        ]
        slave2 = [{"lead_ms": 5, "tag": 1, "jitter_ms": 0}]

        report = monitor.summarize_samples(slave1, slave2, expected_per_lead=2)

        self.assertEqual(1, report["matched_samples"])
        self.assertEqual(1, report["missing_samples"])

    def test_unique_sample_store_ignores_the_same_key_from_a_later_round(self):
        store = {}
        first = {"lead_ms": 5, "tag": 7, "jitter_ms": 0}
        duplicate = {"lead_ms": 5, "tag": 7, "jitter_ms": 99}

        self.assertTrue(monitor.store_first_sample(store, first))
        self.assertFalse(monitor.store_first_sample(store, duplicate))
        self.assertEqual(first, store[(5, 7)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
