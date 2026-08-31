# -*- coding: utf-8 -*-
"""Hi-Nu Master to MicroPython Slave NC4 wire-contract tests."""

import os
import importlib
import struct
import sys
import types
import unittest
from unittest.mock import patch


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SLAVE = os.path.join(ROOT, "slave")
if SLAVE not in sys.path:
    sys.path.insert(0, SLAVE)

from action import pixel_actions
from lib.sys.proto import ADDR_BROADCAST, StreamParser
from lib.sys.schema_loader import SchemaStore
from lib.sys.sys_bus import bus


class FakeApp:
    def __init__(self):
        self.store = SchemaStore(os.path.join(SLAVE, "schema"))
        self.store.finalize()


class HiNuNc4SlaveContractTests(unittest.TestCase):
    def setUp(self):
        self.old_shared = bus.shared
        self.old_cid = bus.cid
        bus.shared = {}
        bus.cid = 0x0001
        self.app = FakeApp()
        self.frames = []
        self.ctx = {
            "app": self.app,
            "send": lambda frame: self.frames.append(bytes(frame)),
        }

    def tearDown(self):
        bus.shared = self.old_shared
        bus.cid = self.old_cid

    def _last_frame(self):
        parser = StreamParser()
        parser.feed(self.frames[-1])
        frames = list(parser.pop())
        self.assertEqual(1, len(frames))
        return frames[0]

    def test_mode_get_reports_active_mode_from_the_addressed_slave(self):
        """Hi-Nu Master must receive a unicast MODE_GET_RSP for convergence."""
        pixel_actions.on_mode_set(self.ctx, {
            "mode_type": 1,
            "mode_id": 1,
            "start_delay_ms": 0,
            "brightness": 255,
        })

        pixel_actions.on_mode_get(self.ctx, {})

        version, addr, cmd, payload = self._last_frame()
        self.assertEqual(4, version)
        self.assertEqual(0x0001, addr)
        self.assertEqual(0x3104, cmd)
        mode_type, mode_id, elapsed_ms, total_ms, running = struct.unpack(
            "<BBIIB", payload
        )
        self.assertEqual((1, 1), (mode_type, mode_id))
        self.assertGreaterEqual(elapsed_ms, 0)
        self.assertEqual(0, total_ms)
        self.assertEqual(1, running)

    def _sys_actions(self):
        fake_config = types.ModuleType("lib.sys.ConfigManager")
        fake_config.cfg_manager = types.SimpleNamespace()
        fake_machine = types.ModuleType("machine")
        with patch.dict(sys.modules, {
            "machine": fake_machine,
            "lib.sys.ConfigManager": fake_config,
        }):
            sys.modules.pop("action.sys_actions", None)
            module = importlib.import_module("action.sys_actions")
        module.time = types.SimpleNamespace(ticks_ms=lambda: 1234)
        return module

    def test_broadcast_time_sync_does_not_create_rs485_reply_collision(self):
        """Every slave replying to one broadcast corrupts the shared RS485 bus."""
        sys_actions = self._sys_actions()
        ctx = dict(self.ctx, frame_addr=ADDR_BROADCAST)

        sys_actions.on_time_sync(ctx, {"master_time_ms": 1000})

        self.assertEqual([], self.frames)

    def test_unicast_time_sync_still_returns_delay_measurement(self):
        """Suppressing all replies would break the Master's unicast RTT probe."""
        sys_actions = self._sys_actions()
        ctx = dict(self.ctx, frame_addr=bus.cid)

        sys_actions.on_time_sync(ctx, {"master_time_ms": 1000})

        _version, addr, command, _payload = self._last_frame()
        self.assertEqual(bus.cid, addr)
        self.assertEqual(0x100B, command)


if __name__ == "__main__":
    unittest.main()
