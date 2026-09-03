# -*- coding: utf-8 -*-
"""Contract tests for the canonical Hi-Nu Project Mode motor sequence."""

import json
import os
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST_PATH = os.path.join(
    ROOT, "slave", "pixel", "sequences", "hi_nu_motor_project.json"
)

EXPECTED_ORDER = [str(value) for value in range(1, 7)]
EXPECTED_ROUTES = {
    "1": [(1, [40]), (12, [42])],
    "2": [
        (9, [22]), (11, [23]),
        (8, [24, 25, 26]), (10, [28, 29, 30]),
    ],
    "3": [
        (8, [27]), (10, [31]),
        (7, [32, 33, 34, 38, 36, 37]),
    ],
    "4": [
        (5, [73, 75, 74, 76, 77]),
        (3, [83, 85, 84, 86, 87]),
    ],
    "5": [
        (15, [43]), (14, [44]),
        (13, [45, 46, 48, 49]), (20, [60, 61, 70, 71]),
    ],
    "6": [
        (1, [39]),
        (14, [53, 91, 63, 101, 54, 92, 64, 102, 55, 93, 65, 103]),
        (15, [57, 94, 67, 104, 58, 95, 68, 105, 59, 96, 69, 106]),
    ],
}
EXPECTED_PENDING_COMPONENTS = {
    "4": [
        {"part": "胸", "motion": "正前方"},
        {"part": "胸", "motion": "兩邊散氣口甲"},
        {"part": "胸", "motion": "駕駛艙上"},
        {"part": "胸", "motion": "駕駛艙中"},
        {"part": "胸", "motion": "駕駛艙下"},
    ],
    "6": [
        {"part": "盾", "motion": "中間兩邊"},
        {"part": "盾", "motion": "頂"},
        {"part": "盾", "motion": "尾兩邊"},
    ],
}


class HiNuMotorProjectSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(MANIFEST_PATH, encoding="utf-8") as handle:
            cls.manifest = json.load(handle)
        cls.stages = cls.manifest["stages"]

    def test_stage_timeline_has_fixed_order(self):
        """A dropped or reordered stage would desync the project."""
        self.assertEqual(3, self.manifest["version"])
        self.assertEqual("hi_nu_motor_project", self.manifest["name"])
        self.assertNotIn("motor_open_interval_ms", self.manifest)
        self.assertEqual(EXPECTED_ORDER, [stage["sequence"] for stage in self.stages])

    def test_servo_timeline_matches_the_blue_master_schedule(self):
        """Both boards must interpret the video timecode as the same ms timeline."""
        self.assertEqual(
            {
                "time_unit": "ms",
                "story_modes": [
                    {"id": 0, "name": "storyMode_signals", "start_ms": 0,
                     "end_ms": 15000},
                    {"id": 1, "name": "storyMode_0_v2", "start_ms": 15000,
                     "fade_start_ms": 31900, "end_ms": 34000},
                    {"id": 2, "name": "storyMode_motor", "start_ms": 34000,
                     "end_ms": 102000},
                    {"id": 3, "name": "storyMode_motor_reset", "start_ms": 102000,
                     "end_ms": 113000},
                ],
                "sequence_global_start_ms": [35064, 46044, 57054,
                                             66145, 77739, 86915],
                "sequence_motor_local_start_ms": [1064, 12044, 23054,
                                                  32145, 43739, 52915],
                "default_open_duration_ms": 10000,
                "funnel_point_open_duration_ms": 4500,
                "all_close": {
                    "global_start_ms": 102289,
                    "reset_local_start_ms": 289,
                    "duration_ms": 10000,
                    "global_end_ms": 112289,
                },
            },
            self.manifest["servo_timeline"],
        )

    def test_open_and_close_use_the_confirmed_direction_and_fastest_raw_value(self):
        """Swapping A/B or using a ramp value would reverse or slow the motors."""
        self.assertEqual(
            {
                "close": {"direction": "A", "raw": 0},
                "open": {"direction": "B", "raw": 255},
            },
            self.manifest["directions"],
        )

    def test_unknown_chest_and_shield_addresses_stay_explicitly_pending(self):
        """Inventing an address for an unmapped component could move the wrong part."""
        pending = {
            stage["sequence"]: stage["pending_components"]
            for stage in self.stages
            if "pending_components" in stage
        }
        self.assertEqual(EXPECTED_PENDING_COMPONENTS, pending)

    def test_active_stages_route_to_the_approved_slave_addresses(self):
        """Wrong Slave ownership or address would actuate the wrong body part."""
        actual = {}
        for stage in self.stages:
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
            if isinstance(address, int)
        ]
        self.assertEqual(len(addresses), len(set(addresses)))
        self.assertEqual(63, len(addresses))
        self.assertTrue({12, 15, 19, 21, 35, 41}.isdisjoint(addresses))
        self.assertEqual(
            [{"address": 35, "reason": "short_circuit", "replacement": 38}],
            self.manifest["excluded_addresses"],
        )
        self.assertEqual([41], self.manifest["unsequenced_addresses"])


if __name__ == "__main__":
    unittest.main()
