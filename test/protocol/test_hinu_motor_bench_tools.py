#!/usr/bin/env python3
"""Hi-Nu black-board motor command and synchronization bench contracts."""

import os
import importlib.util
import shutil
import sys
import types
import unittest
from unittest.mock import patch


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SLAVE = os.path.join(ROOT, "slave")
TOOLS = os.path.join(ROOT, "tools", "PC")
for path in (SLAVE, TOOLS):
    if path not in sys.path:
        sys.path.insert(0, path)

from action import pixel_actions
from lib.sys.sys_bus import bus

fake_log_service = types.ModuleType("lib.sys.log_service")
fake_log_service._viper_write_i32 = lambda *_args: None
fake_log_service.get_log = lambda: types.SimpleNamespace(
    info=lambda _message: None,
    warn=lambda _message: None,
    error=lambda _message: None,
)
sys.modules.setdefault("lib.sys.log_service", fake_log_service)

from tasks import pixel_task as pixel_task_module

import hinu_motor_command_test
import hinu_motor_sync_test


class FakeTime:
    now_ms = 1000
    sleep_calls = []

    @classmethod
    def ticks_ms(cls):
        return cls.now_ms

    @staticmethod
    def ticks_add(value, delta):
        return value + delta

    @staticmethod
    def ticks_diff(a, b):
        return a - b

    @classmethod
    def sleep_ms(cls, value):
        cls.sleep_calls.append(value)
        cls.now_ms += value


class NonBlockingModeScheduleTests(unittest.TestCase):
    def setUp(self):
        self.old_shared = bus.shared
        self.old_time = pixel_actions.time
        self.old_task_time = pixel_task_module.time
        self.old_task_get_log = pixel_task_module.get_log
        bus.shared = {}
        FakeTime.now_ms = 1000
        FakeTime.sleep_calls = []
        pixel_actions.time = FakeTime
        pixel_task_module.time = FakeTime
        pixel_task_module.get_log = lambda: types.SimpleNamespace(
            info=lambda _message: None,
            warn=lambda _message: None,
            error=lambda _message: None,
        )

    def tearDown(self):
        bus.shared = self.old_shared
        pixel_actions.time = self.old_time
        pixel_task_module.time = self.old_task_time
        pixel_task_module.get_log = self.old_task_get_log

    def test_mode_set_records_deadline_without_blocking_the_nc4_handler(self):
        """Reintroducing sleep_ms in MODE_SET would serialize command handling."""
        pixel_actions.on_mode_set({}, {
            "mode_type": 1,
            "mode_id": 2,
            "start_delay_ms": 300,
            "brightness": 255,
        })

        self.assertEqual([], FakeTime.sleep_calls)
        self.assertEqual(
            {
                "mode_type": 1,
                "mode_id": 2,
                "start_at": 1300,
                "brightness": 255,
                "start_delay_ms": 300,
            },
            bus.shared["pixel_remote_schedule"],
        )
        self.assertEqual(0, bus.shared["pixel_nc4_status"]["running"])
        self.assertEqual(1300, bus.shared["pixel_nc4_status"]["scheduled_at"])

    def test_pixel_task_starts_only_when_the_common_deadline_is_due(self):
        """Consuming a scheduled mode early would reintroduce cross-board skew."""
        bus.shared = {
            "pixel_remote_schedule": {
                "mode_type": 1,
                "mode_id": 2,
                "start_at": 1300,
                "brightness": 255,
                "start_delay_ms": 300,
            },
            "pixel_nc4_status": {
                "mode_type": 1,
                "mode_id": 2,
                "scheduled_at": 1300,
                "elapsed_ms": 0,
                "running": 0,
            },
        }
        mode = {"id": 2}
        task = pixel_task_module.PixelTask("pixel", {})
        task._modes = {2: mode}

        FakeTime.now_ms = 1279
        task._consume_cmds()
        self.assertFalse(task._playing)
        self.assertIn("pixel_remote_schedule", bus.shared)

        FakeTime.now_ms = 1300
        task._consume_cmds()
        self.assertTrue(task._playing)
        self.assertEqual([mode], task._show_list)
        self.assertNotIn("pixel_remote_schedule", bus.shared)
        self.assertEqual(1, bus.shared["pixel_nc4_status"]["running"])
        self.assertEqual(1300, bus.shared["pixel_nc4_status"]["started_at"])

    def test_pixel_task_waits_the_final_twenty_ms_to_hit_deadline_exactly(self):
        """Polling past a near deadline would preserve the observed 2–20ms skew."""
        bus.shared = {
            "pixel_remote_schedule": {
                "mode_type": 1,
                "mode_id": 2,
                "start_at": 1300,
                "brightness": 255,
                "start_delay_ms": 300,
            },
            "pixel_nc4_status": {"running": 0},
        }
        task = pixel_task_module.PixelTask("pixel", {})
        task._modes = {2: {"id": 2}}

        FakeTime.now_ms = 1280
        task._consume_cmds()

        self.assertEqual(1300, FakeTime.now_ms)
        self.assertEqual([20], FakeTime.sleep_calls)
        self.assertTrue(task._playing)
        self.assertEqual(1300, bus.shared["pixel_nc4_status"]["actual_started_at"])

    def test_sync_probe_records_without_driving_a_motor_or_logging_each_sample(self):
        """Per-sample USB output can block core0 and create the jitter being measured."""
        messages = []
        old_print = getattr(pixel_task_module, "print", None)
        pixel_task_module.print = messages.append
        bus.shared = {
            "pixel_remote_schedule": {
                "mode_type": 1,
                "mode_id": 250,
                "start_at": 1300,
                "brightness": 37,
                "start_delay_ms": 20,
            },
            "pixel_nc4_status": {"running": 0},
        }
        task = pixel_task_module.PixelTask("pixel", {})
        task._modes = {250: {"id": 250}}

        FakeTime.now_ms = 1301
        try:
            task._consume_cmds()
        finally:
            if old_print is None:
                del pixel_task_module.print
            else:
                pixel_task_module.print = old_print

        self.assertEqual([], messages)
        self.assertFalse(task._playing)
        self.assertNotIn("pixel_remote_set", bus.shared)

    def test_sync_probe_emits_one_compact_batch_after_all_one_hundred_tags(self):
        """A missing tag or per-sample flush must prevent a valid compact batch."""
        messages = []
        old_print = getattr(pixel_task_module, "print", None)
        pixel_task_module.print = messages.append
        try:
            for native_tag in range(1, 101):
                pixel_task_module._record_sync_stress_sample(
                    lead_ms=20, native_tag=native_tag, jitter_ms=1)
        finally:
            if old_print is None:
                del pixel_task_module.print
            else:
                pixel_task_module.print = old_print

        self.assertEqual(1, len(messages))
        self.assertEqual(
            "[SYNC-STRESS-BATCH] lead=20 count=100 data=" + "01" * 100,
            messages[0],
        )

    def test_new_immediate_mode_cancels_an_older_scheduled_mode(self):
        """A stale deadline must not resurrect after a Master retry/mode change."""
        pixel_actions.on_mode_set({}, {
            "mode_type": 1,
            "mode_id": 2,
            "start_delay_ms": 300,
            "brightness": 255,
        })
        pixel_actions.on_mode_set({}, {
            "mode_type": 1,
            "mode_id": 1,
            "start_delay_ms": 0,
            "brightness": 255,
        })

        self.assertNotIn("pixel_remote_schedule", bus.shared)
        self.assertEqual(1, bus.shared["pixel_remote_set"])

    def test_stop_cancels_both_pending_and_immediate_mode_commands(self):
        """MODE_STOP must not let an unconsumed motor start run first."""
        pixel_actions.on_mode_set({}, {
            "mode_type": 1,
            "mode_id": 1,
            "start_delay_ms": 0,
            "brightness": 255,
        })
        pixel_actions.on_mode_stop({}, {"action": 1})

        self.assertNotIn("pixel_remote_set", bus.shared)
        self.assertNotIn("pixel_remote_schedule", bus.shared)
        self.assertEqual(1, bus.shared["pixel_remote_stop"])


class CommandProgramTests(unittest.TestCase):
    def test_black_master_uses_gpio9_10_11_rs485_wiring(self):
        """Using the former GPIO14/15/16 map sends valid NC4 bytes to no transceiver."""
        uart_calls = []

        class FakePin:
            OUT = 1

            def __init__(self, pin, *_args, **_kwargs):
                self.pin = pin

            def value(self, _value=None):
                return 0

        class FakeUART:
            def __init__(self, uart_id, baudrate, **kwargs):
                uart_calls.append((uart_id, baudrate, kwargs))

        fake_machine = types.ModuleType("machine")
        fake_machine.Pin = FakePin
        fake_machine.UART = FakeUART
        old_machine = sys.modules.get("machine")
        sys.modules["machine"] = fake_machine
        try:
            path = os.path.join(ROOT, "tools", "ESP", "hinu_motor_master.py")
            spec = importlib.util.spec_from_file_location("hinu_motor_master_pins", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            link = module.Link()
        finally:
            if old_machine is None:
                sys.modules.pop("machine", None)
            else:
                sys.modules["machine"] = old_machine

        self.assertEqual(1, uart_calls[0][0])
        self.assertEqual(115200, uart_calls[0][1])
        self.assertEqual(10, uart_calls[0][2]["tx"].pin)
        self.assertEqual(11, uart_calls[0][2]["rx"].pin)
        self.assertEqual(9, link.enable.pin)

    def test_black_master_waits_for_shared_bus_quiet_before_enabling_tx(self):
        """Blue and black masters share A/B, so black TX must not start on busy RX."""
        events = []

        class FakePin:
            OUT = 1

            def __init__(self, pin, *_args, **kwargs):
                self.pin = pin
                self.level = kwargs.get("value", 0)

            def value(self, value=None):
                if value is not None:
                    self.level = value
                    if self.pin == 9:
                        events.append(("en", value))
                return self.level

        class FakeUART:
            def __init__(self, *_args, **_kwargs):
                self.busy = bytearray(b"BLUE")

            def any(self):
                return len(self.busy)

            def read(self, count=-1):
                events.append(("read", bytes(self.busy)))
                self.busy.clear()
                return b"BLUE"

            def write(self, data):
                events.append(("write", bytes(data)))
                return len(data)

            def flush(self):
                events.append(("flush", None))

        class FakeTime:
            @staticmethod
            def sleep_ms(value):
                events.append(("sleep", value))

        fake_machine = types.ModuleType("machine")
        fake_machine.Pin = FakePin
        fake_machine.UART = FakeUART
        old_machine = sys.modules.get("machine")
        sys.modules["machine"] = fake_machine
        try:
            path = os.path.join(ROOT, "tools", "ESP", "hinu_motor_master.py")
            spec = importlib.util.spec_from_file_location("hinu_motor_master_lbt", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.time = FakeTime
            module.Link().send(b"NC4")
        finally:
            if old_machine is None:
                sys.modules.pop("machine", None)
            else:
                sys.modules["machine"] = old_machine

        read_at = events.index(("read", b"BLUE"))
        enable_at = events.index(("en", 1))
        write_at = events.index(("write", b"NC4"))
        disable_at = len(events) - 1 - events[::-1].index(("en", 0))
        self.assertLess(read_at, enable_at)
        self.assertLess(enable_at, write_at)
        self.assertLess(write_at, disable_at)

    def test_host_cli_falls_back_to_uvx_when_mpremote_is_not_on_path(self):
        """Hard-coding mpremote makes every hardware subcommand fail on this bench."""
        with patch.object(
            shutil,
            "which",
            side_effect=lambda name: "/opt/bin/uvx" if name == "uvx" else None,
        ):
            try:
                prefix = hinu_motor_command_test._mpremote_prefix()
            except AttributeError:
                self.fail("host CLI has no mpremote executable resolver")
            self.assertEqual(["/opt/bin/uvx", "mpremote"], prefix)

    def test_black_master_device_sender_uses_the_same_nc4_wire_frame(self):
        """A standalone sender with different CRC/header bytes would not control Slaves."""
        class FakePin:
            OUT = 1

            def __init__(self, *_args, **_kwargs):
                pass

        fake_machine = types.ModuleType("machine")
        fake_machine.Pin = FakePin
        fake_machine.UART = object
        old_machine = sys.modules.get("machine")
        sys.modules["machine"] = fake_machine
        try:
            path = os.path.join(ROOT, "tools", "ESP", "hinu_motor_master.py")
            spec = importlib.util.spec_from_file_location("hinu_motor_master_contract", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        finally:
            if old_machine is None:
                sys.modules.pop("machine", None)
            else:
                sys.modules["machine"] = old_machine

        expected_payload, expected_frame = hinu_motor_command_test.encode_nc4(
            0x3105,
            {
                "mode_type": 1,
                "mode_id": 2,
                "start_delay_ms": 300,
                "brightness": 255,
            },
        )
        self.assertEqual(
            expected_frame,
            module._pack(0x3105, expected_payload),
        )

    def test_black_master_reboot_command_uses_nc4_u32_delay_payload(self):
        """A malformed recovery command cannot release a Slave with blocked USB."""
        class FakePin:
            OUT = 1

            def __init__(self, *_args, **_kwargs):
                pass

        fake_machine = types.ModuleType("machine")
        fake_machine.Pin = FakePin
        fake_machine.UART = object
        old_machine = sys.modules.get("machine")
        sys.modules["machine"] = fake_machine
        try:
            path = os.path.join(ROOT, "tools", "ESP", "hinu_motor_master.py")
            spec = importlib.util.spec_from_file_location("hinu_motor_master_reboot", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        finally:
            if old_machine is None:
                sys.modules.pop("machine", None)
            else:
                sys.modules["machine"] = old_machine

        frames = []
        module.Link = lambda: types.SimpleNamespace(
            send=lambda frame: frames.append(bytes(frame)) or len(frame))
        module.reboot_slaves(250)
        _payload, expected = hinu_motor_command_test.encode_nc4(
            0x100F, {"delay_ms": 250})

        self.assertEqual([expected], frames)

    def test_offline_master_command_reaches_both_real_slave_profiles(self):
        """A wrong CID, address list, mode payload, or deadline must fail."""
        result = hinu_motor_command_test.run_offline_mode(
            mode_id=0, start_delay_ms=300, received_at_ms=1000
        )

        self.assertEqual("PASS", result["result"])
        self.assertEqual("3105", result["command"])
        self.assertEqual("01002c01ff", result["payload_hex"])
        self.assertEqual(
            [
                {"cid": "0001", "motor_addresses": [13, 15, 19], "start_at_ms": 1300},
                {"cid": "0002", "motor_addresses": [10, 12, 17, 21], "start_at_ms": 1300},
            ],
            result["slaves"],
        )

    def test_stop_command_uses_action_one_and_leaves_both_slaves_stopped(self):
        """A stop command that leaves a running mode is unsafe."""
        result = hinu_motor_command_test.run_offline_stop()

        self.assertEqual("PASS", result["result"])
        self.assertEqual("3106", result["command"])
        self.assertEqual("01", result["payload_hex"])
        self.assertEqual([0, 0], [item["running"] for item in result["slaves"]])


class SynchronizationProgramTests(unittest.TestCase):
    def test_modes_zero_one_two_have_zero_offline_skew_for_all_seven_motors(self):
        """Different profile timing or one omitted address must fail the bench."""
        result = hinu_motor_sync_test.run_offline_sync_test((0, 1, 2))

        self.assertEqual("PASS", result["result"])
        self.assertEqual([13, 15, 19, 10, 12, 17, 21], result["motor_addresses"])
        for mode in result["modes"]:
            self.assertEqual(0, mode["scheduled_start_skew_ms"])
            self.assertEqual(0, mode["first_motion_skew_ms"])
            self.assertEqual(0, mode["stop_skew_ms"])
            self.assertEqual(0x80, mode["final_value"])
            self.assertEqual("PASS", mode["result"])

        by_id = {item["mode_id"]: item for item in result["modes"]}
        self.assertEqual(0x00, by_id[0]["peak_value"])
        self.assertEqual(0xFF, by_id[1]["peak_value"])
        self.assertEqual(10000, by_id[0]["stop_at_ms"])
        self.assertEqual(10000, by_id[1]["stop_at_ms"])
        self.assertEqual(180000, by_id[2]["stop_at_ms"])

    def test_story_mode_motor_uses_one_deadline_and_stops_all_seven_motors(self):
        """Staggering either black Slave or omitting the final dead-zone STOP is unsafe."""
        try:
            result = hinu_motor_sync_test.run_offline_sync_test((3,))
        except KeyError:
            self.fail("storyMode_motor mode 3 is not registered")

        self.assertEqual("PASS", result["result"])
        self.assertEqual([13, 15, 19, 10, 12, 17, 21], result["motor_addresses"])
        story = result["modes"][0]
        self.assertEqual(3, story["mode_id"])
        self.assertEqual(0, story["scheduled_start_skew_ms"])
        self.assertEqual(0, story["first_motion_skew_ms"])
        self.assertEqual(0, story["stop_skew_ms"])
        self.assertEqual(24000, story["stop_at_ms"])
        # Hydraulic Cinematic's cruise plateau is 95%; Direction B encodes it as 0xF9.
        self.assertEqual(0xF9, story["peak_value"])
        self.assertEqual(0x80, story["final_value"])
        self.assertEqual("PASS", story["result"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
