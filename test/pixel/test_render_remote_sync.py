#!/usr/bin/env python3
"""RenderTask must react to a remote mode command without a 500 ms stale cache."""

import os
import sys
import types
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SLAVE = os.path.join(ROOT, "slave")
if SLAVE not in sys.path:
    sys.path.insert(0, SLAVE)


fake_log_service = types.ModuleType("lib.sys.log_service")
fake_log_service._viper_write_i32 = lambda *_args: None
fake_log_service.get_log = lambda: types.SimpleNamespace(
    info=lambda _msg: None,
)
sys.modules.setdefault("lib.sys.log_service", fake_log_service)

from lib.sys.sys_bus import bus
from tasks import render as render_module


class FakeTime:
    now_ms = 100
    now_us = 100_000

    @classmethod
    def ticks_ms(cls):
        return cls.now_ms

    @classmethod
    def ticks_us(cls):
        return cls.now_us

    @staticmethod
    def ticks_diff(a, b):
        return a - b

    @staticmethod
    def ticks_add(a, b):
        return a + b


class FakeStreamer:
    def __init__(self):
        self.big_buffer = bytearray(4)
        self.show_count = 0
        self.clear_count = 0

    def show_all(self):
        self.show_count += 1

    def clear_all(self):
        self.clear_count += 1


class ReadyHub:
    def read_into(self, _target):
        return True


class RenderRemoteSyncTests(unittest.TestCase):
    def setUp(self):
        self.old_shared = bus.shared
        self.old_render_time = render_module.time
        import lib.sys.task as task_module
        self.task_module = task_module
        self.old_task_time = task_module.time
        bus.shared = {
            "is_streaming": False,
            "is_ready": False,
            "is_paused": False,
        }
        render_module.time = FakeTime
        task_module.time = FakeTime

    def tearDown(self):
        bus.shared = self.old_shared
        render_module.time = self.old_render_time
        self.task_module.time = self.old_task_time

    def test_remote_start_bypasses_stale_streaming_cache(self):
        streamer = FakeStreamer()
        task = render_module.RenderTask("render", {"st_pixel": streamer})
        task.running = True
        task.hub = ReadyHub()
        task.interval_us = 20_000
        task.next_tick_us = 0

        # Reproduce the real failure: RenderTask cached False just before MODE_SET.
        task._fcache["is_streaming"] = False
        task._fcache_ts = FakeTime.now_ms
        bus.shared["is_streaming"] = True
        bus.shared["is_ready"] = True

        task.loop()

        self.assertEqual(1, streamer.show_count)


if __name__ == "__main__":
    unittest.main()
