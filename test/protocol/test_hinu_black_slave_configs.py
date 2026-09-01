# -*- coding: utf-8 -*-
"""Contracts for the canonical Hi-Nu black physical Slave profiles."""

import json
import os
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROFILES_ROOT = os.path.join(
    ROOT, "ports", "S3", "ESP32-S3_1_18_hinu_black"
)
MASTER_PATH = os.path.join(PROFILES_ROOT, "master", "config.json")
ACTIVE_SLAVE_IDS = (
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
    11, 12, 13, 14, 15, 18, 19, 20,
)

EXPECTED_ADDRESSES = {
    1: [40, 39],
    2: [],
    3: [83, 85, 84, 86, 87],
    4: [],
    5: [73, 75, 74, 76, 77],
    6: [],
    7: [32, 33, 34, 38, 36, 37],
    8: [24, 25, 26, 27],
    9: [22],
    10: [28, 29, 30, 31],
    11: [23],
    12: [42],
    13: [45, 46, 48, 49],
    14: [44, 53, 91, 63, 101, 54, 92, 64, 102, 55, 93, 65, 103],
    15: [43, 57, 94, 67, 104, 58, 95, 68, 105, 59, 96, 69, 106],
    18: [],
    19: [],
    20: [60, 61, 70, 71],
}


def profile_path(slave_id):
    return os.path.join(
        PROFILES_ROOT, "slave{:02d}".format(slave_id), "config.json"
    )


def load_profile(slave_id):
    with open(profile_path(slave_id), encoding="utf-8") as handle:
        return json.load(handle)


class HinuBlackSlaveConfigTests(unittest.TestCase):
    def test_master_and_all_physical_slave_profiles_exist(self):
        """Removing or omitting one board profile must break the update bundle."""
        actual = []
        if os.path.isdir(PROFILES_ROOT):
            actual = sorted(
                name
                for name in os.listdir(PROFILES_ROOT)
                if os.path.isfile(os.path.join(PROFILES_ROOT, name, "config.json"))
            )
        expected = ["master"] + [
            "slave{:02d}".format(value) for value in ACTIVE_SLAVE_IDS
        ]
        self.assertEqual(expected, actual)

    def test_master_profile_keeps_runtime_modules_disabled(self):
        """Enabling a config UART would conflict with hinu_motor_master.py."""
        with open(MASTER_PATH, encoding="utf-8") as handle:
            profile = json.load(handle)

        self.assertEqual("0000", profile["System"]["cID"])
        self.assertEqual(0, profile["System"]["num_pixels"])
        for module in (
            "CircuitDecode", "ProjectMode", "SPI", "I2C", "UART", "PWM",
            "I2S", "SDcard", "PIN", "ENC", "TFT", "HUSB238", "WS2812",
            "APA102", "PCA9685", "uartMotor",
        ):
            self.assertEqual(0, profile[module]["enable"], module)

    def test_profiles_keep_unique_identity_and_exact_motor_routes(self):
        """A cloned cID or wrong per-Slave motor address can move another mechanism."""
        seen_cids = set()
        seen_addresses = set()

        for slave_id in ACTIVE_SLAVE_IDS:
            profile = load_profile(slave_id)
            expected_cid = "{:04X}".format(slave_id)
            self.assertEqual(expected_cid, profile["System"]["cID"])
            self.assertNotIn(expected_cid, seen_cids)
            seen_cids.add(expected_cid)

            self.assertEqual(1, profile["CircuitDecode"]["enable"])
            self.assertEqual(
                [{"GPIO": {"uart": 0}}], profile["CircuitDecode"]["list"]
            )

            rs485 = profile["UART"]["list"][0]
            self.assertEqual(115200, rs485["baudrate"])
            self.assertEqual({"tx": 10, "rx": 11, "en": 9}, rs485["GPIO"])

            expected_addresses = EXPECTED_ADDRESSES[slave_id]
            if expected_addresses:
                self.assertEqual(1, profile["uartMotor"]["enable"])
                self.assertEqual(2, len(profile["UART"]["list"]))
                motor_uart = profile["UART"]["list"][1]
                self.assertEqual(9600, motor_uart["baudrate"])
                self.assertEqual({"tx": 12, "rx": None}, motor_uart["GPIO"])

                motor = profile["uartMotor"]["list"][0]
                self.assertEqual({"uart": 1}, motor["GPIO"])
                actual_addresses = [int(value) for value in motor["address"]]
                self.assertEqual(expected_addresses, actual_addresses)
                self.assertTrue(seen_addresses.isdisjoint(actual_addresses))
                seen_addresses.update(actual_addresses)
            else:
                self.assertEqual(0, profile["uartMotor"]["enable"])
                self.assertEqual([], profile["uartMotor"]["list"])
                self.assertEqual(1, len(profile["UART"]["list"]))

            self.assertEqual(1, profile["ProjectMode"]["enable"])
            self.assertEqual(2, profile["ProjectMode"]["dev_mode_id"])

        self.assertEqual(63, len(seen_addresses))
        self.assertNotIn(35, seen_addresses)
        self.assertNotIn(41, seen_addresses)

    def test_slave15_absorbs_slave17_motor_routes(self):
        """Leaving a Slave17 profile would split motors across two controllers."""
        self.assertFalse(os.path.exists(profile_path(17)))
        slave15 = load_profile(15)["uartMotor"]["list"][0]["address"]
        self.assertEqual(
            [
                "43", "57", "94", "67", "104", "58", "95", "68",
                "105", "59", "96", "69", "106",
            ],
            slave15,
        )

    def test_slave14_absorbs_slave16_motor_routes(self):
        """Leaving a Slave16 profile would split one physical controller identity."""
        self.assertFalse(os.path.exists(profile_path(16)))
        slave14 = load_profile(14)["uartMotor"]["list"][0]["address"]
        self.assertEqual(
            [
                "44", "53", "91", "63", "101", "54", "92", "64",
                "102", "55", "93", "65", "103",
            ],
            slave14,
        )

    def test_slave13_and_slave20_split_left_and_right_tanks(self):
        """Copying Slave13 unchanged to Slave20 must not duplicate the left tank."""
        slave13 = load_profile(13)["uartMotor"]["list"][0]["address"]
        slave20 = load_profile(20)["uartMotor"]["list"][0]["address"]
        self.assertEqual(["45", "46", "48", "49"], slave13)
        self.assertEqual(["60", "61", "70", "71"], slave20)


if __name__ == "__main__":
    unittest.main()
