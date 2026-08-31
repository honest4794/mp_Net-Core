# -*- coding: utf-8 -*-
"""Project Slave fallback：Master 失聯 10 秒後本機播放 Dev motor mode。"""

import json
import os
import sys
import types
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SLAVE = os.path.join(ROOT, "slave")
if SLAVE not in sys.path:
    sys.path.insert(0, SLAVE)

if "micropython" not in sys.modules:
    sys.modules["micropython"] = types.SimpleNamespace(
        viper=lambda fn: fn,
        native=lambda fn: fn,
        const=lambda value: value,
    )

from lib.sw.project_mode_fallback import ProjectModeFallback, note_master_seen
from lib.sys.sys_bus import bus
import tasks.pixel_task as pixel_task_module
from tasks.pixel_task import PixelTask


PROFILE = os.path.join(
    ROOT, "ports", "S3", "ESP32-S3_1_18_project_slave7", "config.json")


class ProjectModePolicyTests(unittest.TestCase):

    def test_enters_once_at_exactly_ten_seconds_without_master(self):
        policy = ProjectModeFallback(10000, lambda now, then: now - then)
        policy.start(500)

        self.assertIsNone(policy.poll(10499))
        self.assertEqual("enter", policy.poll(10500))
        self.assertIsNone(policy.poll(20000))
        self.assertTrue(policy.active)

    def test_master_command_resets_deadline_and_exits_fallback(self):
        policy = ProjectModeFallback(10000, lambda now, then: now - then)
        policy.start(0)
        policy.note_master(9000)
        self.assertIsNone(policy.poll(10000))
        self.assertEqual("enter", policy.poll(19000))
        self.assertEqual("leave", policy.note_master(19500))
        self.assertFalse(policy.active)


class ProjectModeIntegrationTests(unittest.TestCase):

    def setUp(self):
        self.old_shared = bus.shared
        bus.shared = {}
        self.old_get_log = pixel_task_module.get_log
        pixel_task_module.get_log = lambda: types.SimpleNamespace(
            info=lambda _msg: None,
            warn=lambda _msg: None,
            error=lambda _msg: None,
        )

    def tearDown(self):
        bus.shared = self.old_shared
        pixel_task_module.get_log = self.old_get_log

    def _task(self):
        task = PixelTask("pixel", {})
        task._project_enabled = True
        task._project_mode_id = 2
        task._project_seen_seq = 0
        task._project_policy = ProjectModeFallback(
            10000, lambda now, then: now - then)
        task._project_policy.start(0)
        task._modes = {2: {"id": 2}}
        return task

    def test_valid_master_packet_records_liveness(self):
        note_master_seen(1234)
        self.assertEqual(1234, bus.shared["master_last_seen_ms"])
        self.assertEqual(1, bus.shared["master_seen_seq"])

    def test_pixel_task_starts_dev_mode_after_timeout(self):
        task = self._task()

        task._service_project_mode(9999)
        self.assertNotIn("pixel_remote_set", bus.shared)
        task._service_project_mode(10000)

        self.assertEqual(2, bus.shared["pixel_remote_set"])
        self.assertTrue(bus.shared["project_fallback_active"])

    def test_master_return_stops_fallback_but_preserves_new_mode_command(self):
        task = self._task()
        task._service_project_mode(10000)
        bus.shared.pop("pixel_remote_set")

        note_master_seen(11000)
        task._service_project_mode(11000)
        self.assertEqual(1, bus.shared["pixel_remote_stop"])
        self.assertFalse(bus.shared["project_fallback_active"])

        task._service_project_mode(21000)
        bus.shared.pop("pixel_remote_set")
        bus.shared.pop("pixel_remote_stop", None)
        bus.shared["pixel_remote_set"] = 3
        note_master_seen(22000)
        task._service_project_mode(22000)
        self.assertEqual(3, bus.shared["pixel_remote_set"])
        self.assertNotIn("pixel_remote_stop", bus.shared)

    def test_slave7_profile_uses_black_gpio12_and_hinu_addresses(self):
        with open(PROFILE, encoding="utf-8") as handle:
            profile = json.load(handle)

        self.assertEqual("0007", profile["System"]["cID"])
        self.assertEqual(
            {"enable": 1, "master_timeout_ms": 10000,
             "dev_mode_type": 1, "dev_mode_id": 2},
            profile["ProjectMode"],
        )
        rs485 = profile["UART"]["list"][0]
        self.assertEqual({"tx": 10, "rx": 11, "en": 9}, rs485["GPIO"])
        self.assertEqual(1, rs485["rx_only"])
        self.assertEqual(0, rs485["rx_en_level"])
        motor_uart = profile["UART"]["list"][1]
        self.assertEqual(9600, motor_uart["baudrate"])
        self.assertEqual({"tx": 12, "rx": None}, motor_uart["GPIO"])
        addresses = sorted(
            int(value) for value in profile["uartMotor"]["list"][0]["address"])
        self.assertEqual([32, 33, 34, 36, 37, 38], addresses)
        self.assertNotIn(
            "sync_broadcast_span", profile["uartMotor"]["list"][0])


if __name__ == "__main__":
    unittest.main()
