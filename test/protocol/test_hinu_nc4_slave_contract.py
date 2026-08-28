# -*- coding: utf-8 -*-
"""Hi-Nu Master to MicroPython Slave NC4 wire-contract tests."""

import os
import struct
import sys
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SLAVE = os.path.join(ROOT, "slave")
if SLAVE not in sys.path:
    sys.path.insert(0, SLAVE)

from action import pixel_actions
from lib.sys.proto import StreamParser
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


if __name__ == "__main__":
    unittest.main()
