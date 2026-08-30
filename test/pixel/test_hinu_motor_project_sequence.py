# -*- coding: utf-8 -*-
"""Contract tests for the canonical Hi-Nu Project Mode motor sequence."""

import json
import os
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST_PATH = os.path.join(
    ROOT, "slave", "pixel", "sequences", "hi_nu_motor_project.json"
)

EXPECTED_ORDER = (
    [str(value) for value in range(1, 19)]
    + [
        "18A", "19", "19A", "20", "20A", "21", "21A",
        "22", "22A", "23", "23A", "24",
    ]
)
EXPECTED_NO_OPS = {"6", "7", "8", "9", "10", "13", "14", "15", "16"}
EXPECTED_ROUTES = {
    "1": [(9, [22]), (11, [23])],
    "2": [(8, [24]), (10, [28])],
    "3": [(8, [25, 26]), (10, [29, 30])],
    "4": [(8, [27]), (10, [31])],
    "5": [(7, [32, 33, 34, 38, 36, 37])],
    "11": [(1, [41])],
    "12": [(1, [42])],
    "17": [(15, [43]), (14, [44])],
    "18": [(16, [53]), (17, [57])],
    "18A": [(16, [91]), (17, [94])],
    "19": [(16, [63]), (17, [67])],
    "19A": [(16, [101]), (17, [104])],
    "20": [(16, [54]), (17, [58])],
    "20A": [(16, [92]), (17, [95])],
    "21": [(16, [64]), (17, [68])],
    "21A": [(16, [102]), (17, [105])],
    "22": [(16, [55]), (17, [59])],
    "22A": [(16, [93]), (17, [96])],
    "23": [(16, [65]), (17, [69])],
    "23A": [(16, [103]), (17, [106])],
    "24": [(13, [45, 46, 48, 49, 60, 61, 70, 71])],
}


class HiNuMotorProjectSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(MANIFEST_PATH, encoding="utf-8") as handle:
            cls.manifest = json.load(handle)
        cls.stages = cls.manifest["stages"]

    def test_stage_timeline_has_fixed_order_and_global_interval(self):
        """A dropped/reordered stage or interval change would desync the project."""
        self.assertEqual(1, self.manifest["version"])
        self.assertEqual("hi_nu_motor_project", self.manifest["name"])
        self.assertEqual(5000, self.manifest["motor_open_interval_ms"])
        self.assertEqual(EXPECTED_ORDER, [stage["sequence"] for stage in self.stages])

    def test_reserved_stages_are_timed_no_ops(self):
        """Reserved timeline slots must not accidentally drive a motor or disappear."""
        actual_no_ops = {
            stage["sequence"] for stage in self.stages if not stage["targets"]
        }
        self.assertEqual(EXPECTED_NO_OPS, actual_no_ops)

    def test_active_stages_route_to_the_approved_slave_addresses(self):
        """Wrong Slave ownership or address would actuate the wrong body part."""
        actual = {}
        for stage in self.stages:
            if not stage["targets"]:
                continue
            actual[stage["sequence"]] = [
                (target["slave_id"], target["addresses"])
                for target in stage["targets"]
            ]
        self.assertEqual(EXPECTED_ROUTES, actual)

    def test_unsafe_and_unsequenced_addresses_cannot_be_targets(self):
        """Shorted, unassigned, and Test Kit addresses must stay out of Project Mode."""
        addresses = [
            address
            for stage in self.stages
            for target in stage["targets"]
            for address in target["addresses"]
        ]
        self.assertEqual(len(addresses), len(set(addresses)))
        self.assertTrue({12, 15, 19, 21, 35, 39, 40}.isdisjoint(addresses))
        self.assertEqual(
            [{"address": 35, "reason": "short_circuit", "replacement": 38}],
            self.manifest["excluded_addresses"],
        )
        self.assertEqual([39, 40], self.manifest["unsequenced_addresses"])


if __name__ == "__main__":
    unittest.main()
