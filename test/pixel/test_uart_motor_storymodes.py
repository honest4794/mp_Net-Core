# -*- coding: utf-8 -*-
"""Hi-Nu UART motor JSON StoryMode integration tests."""

import json
import importlib.util
import os
import sys
import types
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SLAVE = os.path.join(ROOT, "slave")
if SLAVE not in sys.path:
    sys.path.insert(0, SLAVE)

from lib.hw.uart_motor import UartMotor
from lib.sw.effect_core import Effect
from lib.sw.pixel_layout import PixelLayout


EFFECTS_PATH = os.path.join(SLAVE, "pixel", "effects", "effects.json")
MAPPING_PATH = os.path.join(SLAVE, "pixel", "map", "hi_nu_uart_motor_test.json")
MODES_DIR = os.path.join(SLAVE, "pixel", "modes")
DEPLOY_EFFECTS_PATH = os.path.join(
    ROOT, "test", "pixel", "fixtures", "hinu_uart_motor_effects.json"
)
SLAVE_PROFILES = {
    1: (
        os.path.join(ROOT, "ports", "S3", "ESP32-S3_1_18_hiNew", "config.json"),
        [15, 19],
        "0001",
    ),
    2: (
        os.path.join(ROOT, "ports", "S3", "ESP32-S3-1_18", "config.json"),
        [12, 21],
        "0002",
    ),
}


class FakeUART:
    def __init__(self):
        self.writes = []

    def write(self, data):
        payload = bytes(data)
        self.writes.append(payload)
        return len(payload)


class FakeHardwareBus:
    def __init__(self, uart_items):
        self.shared = {"UART": {"enable": 1, "list": uart_items}}
        self.services = {}

    def register_service(self, name, value):
        self.services[name] = value
        return True


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def effect_params(name):
    data = load_json(EFFECTS_PATH)
    return next(entry for entry in data["effects"] if entry["name"] == name)


def mode_by_id(mode_id):
    for filename in os.listdir(MODES_DIR):
        if not filename.endswith(".json"):
            continue
        mode = load_json(os.path.join(MODES_DIR, filename))
        if mode["id"] == mode_id:
            return mode
    raise KeyError(mode_id)


class FiniteEffectTests(unittest.TestCase):
    def test_effect_holds_neutral_after_requested_cycles(self):
        """Removing finite-cycle handling must restart an unsafe motor command."""
        effect = Effect("finite_test", {
            "pixel_n": 2,
            "program": [
                {"type": "keep", "l_max": 4095, "l_lim": 0, "end_Time": 4},
            ],
            "step": 1,
            "spacing": 0,
            "offset": 0,
            "speed": 1,
            "reverse": False,
            "cycles": 2,
            "hold_value": 2048,
        })

        self.assertEqual([4095, 4095], list(effect.frame(7)))
        self.assertEqual([2048, 2048], list(effect.frame(8)))
        self.assertEqual([2048, 2048], list(effect.frame(800)))


class MotorStoryModeTests(unittest.TestCase):
    def test_low_memory_deployment_effects_match_the_canonical_motor_effects(self):
        names = {
            "uart_motor_diagnostic",
            "uart_motor_max_open",
            "uart_motor_dev_sine",
        }
        canonical = {
            item["name"]: item
            for item in load_json(EFFECTS_PATH)["effects"]
            if item["name"] in names
        }
        deployed = {
            item["name"]: item
            for item in load_json(DEPLOY_EFFECTS_PATH)["effects"]
        }
        self.assertEqual(canonical, deployed)

    def test_uart_driver_translates_json_null_to_disabled_rx_pin(self):
        """MicroPython rejects rx=None; JSON null must become the ESP32 -1 sentinel."""
        uart_calls = []

        class FakePin:
            OUT = 1

            def __init__(self, pin, *args, **kwargs):
                self.pin = pin

            def value(self, _value=None):
                return 0

        class FakeMachineUART:
            def __init__(self, uart_id, **kwargs):
                uart_calls.append((uart_id, kwargs))

        fake_machine = types.ModuleType("machine")
        fake_machine.Pin = FakePin
        fake_machine.UART = FakeMachineUART
        fake_log_service = types.ModuleType("lib.sys.log_service")
        fake_log_service.get_log = lambda: types.SimpleNamespace(info=lambda _msg: None)

        old_machine = sys.modules.get("machine")
        old_log_service = sys.modules.get("lib.sys.log_service")
        sys.modules["machine"] = fake_machine
        sys.modules["lib.sys.log_service"] = fake_log_service
        try:
            path = os.path.join(SLAVE, "driver", "uart_drv.py")
            spec = importlib.util.spec_from_file_location("uart_drv_contract", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            bus = FakeHardwareBus([
                {"id": 2, "baudrate": 9600, "GPIO": {"tx": 17, "rx": None}},
            ])
            module.init_uart(bus)
        finally:
            if old_machine is None:
                sys.modules.pop("machine", None)
            else:
                sys.modules["machine"] = old_machine
            if old_log_service is None:
                sys.modules.pop("lib.sys.log_service", None)
            else:
                sys.modules["lib.sys.log_service"] = old_log_service

        self.assertEqual(2, uart_calls[0][0])
        self.assertEqual(17, uart_calls[0][1]["tx"].pin)
        self.assertEqual(-1, uart_calls[0][1]["rx"])

    def test_motor_driver_forwards_json_sync_settings(self):
        """The runtime driver must not silently drop the synchronization contract."""
        fake_log_service = types.ModuleType("lib.sys.log_service")
        fake_log_service.get_log = lambda: types.SimpleNamespace(
            info=lambda _msg: None,
            error=lambda _msg: None,
        )
        old_log_service = sys.modules.get("lib.sys.log_service")
        sys.modules["lib.sys.log_service"] = fake_log_service
        try:
            path = os.path.join(SLAVE, "driver", "motor_drv.py")
            spec = importlib.util.spec_from_file_location("motor_drv_contract", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            class FakeMotorBus:
                def __init__(self):
                    self.shared = {
                        "uartMotor": {
                            "enable": 1,
                            "list": [{
                                "GPIO": {"uart": 1},
                                "address": ["15", "19"],
                                "version": 1,
                                "dStay": 2048,
                                "sync_broadcast_span": 21,
                                "sync_tx_interval_ms": 40,
                            }],
                        }
                    }
                    self.services = {
                        "uart_list": [FakeUART(), FakeUART()],
                    }

                def get_service(self, name):
                    return self.services.get(name)

                def register_service(self, name, value):
                    self.services[name] = value
                    return True

            motors = module.init_motor(FakeMotorBus())
        finally:
            if old_log_service is None:
                sys.modules.pop("lib.sys.log_service", None)
            else:
                sys.modules["lib.sys.log_service"] = old_log_service

        self.assertEqual(1, len(motors))
        self.assertEqual(21, motors[0].sync_broadcast_span)
        self.assertEqual(40, motors[0].sync_tx_interval_ms)

    def test_modes_zero_one_two_select_the_expected_motor_effects(self):
        """Renumbering or cross-wiring a test mode must fail at the user-facing ID."""
        expected = {
            0: "uart_motor_diagnostic",
            1: "uart_motor_max_open",
            2: "uart_motor_dev_sine",
        }
        for mode_id, effect_name in expected.items():
            mode = mode_by_id(mode_id)
            self.assertEqual(effect_name, mode["map"][0]["effect"])
            self.assertEqual("hi_nu_uart_motor_test.all_uart_motors",
                             mode["map"][0]["group"])
            self.assertEqual("w", mode["map"][0]["write"])

    def test_mode_zero_runs_direction_a_then_stays_stopped(self):
        """Changing diagnostic duration or its safe A command must be detected."""
        effect = Effect("uart_motor_diagnostic", effect_params("uart_motor_diagnostic"))

        self.assertEqual(16, effect.frame(0)[0])       # W >> 4 = raw 0x01
        self.assertEqual(16, effect.frame(499)[0])
        self.assertEqual(2048, effect.frame(500)[0])  # W >> 4 = STOP 0x80
        self.assertEqual(2048, effect.frame(5000)[0])

    def test_mode_one_sends_true_max_b_then_stays_stopped(self):
        """Reducing max-open speed or allowing it to repeat must fail."""
        effect = Effect("uart_motor_max_open", effect_params("uart_motor_max_open"))

        self.assertEqual(4095, effect.frame(0)[0])     # W >> 4 = raw 0xFF
        self.assertEqual(4095, effect.frame(499)[0])
        self.assertEqual(2048, effect.frame(500)[0])
        self.assertEqual(2048, effect.frame(5000)[0])

    def test_mode_two_repeats_six_sine_cycles_then_stays_stopped(self):
        """Changing the 10/5/10/5 timing or six-cycle limit must fail."""
        effect = Effect("uart_motor_dev_sine", effect_params("uart_motor_dev_sine"))

        self.assertLessEqual(effect.frame(0)[0], 2080)
        self.assertGreaterEqual(effect.frame(250)[0], 4000)
        self.assertEqual(2048, effect.frame(500)[0])
        self.assertGreaterEqual(effect.frame(750)[0], 2000)
        self.assertLessEqual(effect.frame(1000)[0], 64)
        self.assertEqual(2048, effect.frame(1250)[0])
        self.assertLessEqual(effect.frame(1500)[0], 2080)  # cycle 2 begins
        self.assertEqual(2048, effect.frame(9000)[0])      # 6 * 1500 frames
        self.assertEqual(2048, effect.frame(20000)[0])

    def test_profile_addresses_receive_mode_one_max_command(self):
        """A wrong profile/address or mapping selector must change the emitted frames."""
        mapping = load_json(MAPPING_PATH)
        effect = Effect("uart_motor_max_open", effect_params("uart_motor_max_open"))

        for slave_id, (profile_path, expected_addresses, _expected_cid) in SLAVE_PROFILES.items():
            profile = load_json(profile_path)
            motor_cfg = profile["uartMotor"]
            self.assertEqual(1, motor_cfg["enable"], "Slave {} motor disabled".format(slave_id))
            self.assertEqual(20, profile["System"]["frame_interval_ms"])
            self.assertEqual(1, len(motor_cfg["list"]))
            uart_index = motor_cfg["list"][0]["GPIO"]["uart"]
            self.assertGreaterEqual(uart_index, 0)
            self.assertLess(uart_index, len(profile["UART"]["list"]))
            self.assertEqual(9600, profile["UART"]["list"][uart_index]["baudrate"])
            addresses = sorted(int(v) for v in motor_cfg["list"][0]["address"])
            self.assertEqual(expected_addresses, addresses)
            self.assertEqual(21, motor_cfg["list"][0]["sync_broadcast_span"])
            self.assertEqual(40, motor_cfg["list"][0]["sync_tx_interval_ms"])
            self.assertNotIn("calib", motor_cfg["list"][0])

            uart = FakeUART()
            motor = UartMotor({
                "version": motor_cfg["list"][0].get("version", 1),
                "addresses": addresses,
                "uart": uart,
                "dStay": motor_cfg["list"][0].get("dStay", 2048),
                "sync_broadcast_span": motor_cfg["list"][0]["sync_broadcast_span"],
                "sync_tx_interval_ms": motor_cfg["list"][0]["sync_tx_interval_ms"],
            })
            layout = PixelLayout(["uartMotor1"], {"uartMotor1": motor.num_pixels})
            layout.register_mapping(mapping["id"], mapping["name"], mapping["groups"])
            frame = bytearray(motor.frame_size)
            layout.scatter(frame, mapping["name"], "all_uart_motors", effect.frame(0), "w")
            motor.st_load_and_convert(frame, 0)
            motor.st_show()

            values = [0x80] * 21
            for address in expected_addresses:
                values[address - 1] = 0xFF
            expected = bytes([0xFF, 0x00] + values + [0xFE])
            self.assertEqual(expected, uart.writes[-1])

    def test_profiles_use_hinu_rs485_and_gpio17_motor_hardware(self):
        """The MicroPython profiles must match the accepted Hi-Nu wiring."""
        for slave_id, (profile_path, _addresses, expected_cid) in SLAVE_PROFILES.items():
            profile = load_json(profile_path)

            self.assertEqual(expected_cid, profile["System"]["cID"])
            self.assertEqual(1, profile["CircuitDecode"]["enable"])
            self.assertEqual(
                [{"GPIO": {"uart": 0}}],
                profile["CircuitDecode"]["list"],
            )

            self.assertEqual(2, len(profile["UART"]["list"]))
            rs485 = profile["UART"]["list"][0]
            self.assertEqual(1, rs485["id"])
            self.assertEqual(115200, rs485["baudrate"])
            self.assertEqual(
                {"tx": 14, "rx": 15, "en": 16},
                rs485["GPIO"],
            )
            self.assertEqual(1, rs485["en_settle_ms"])

            motor_uart = profile["UART"]["list"][1]
            self.assertEqual(2, motor_uart["id"])
            self.assertEqual(9600, motor_uart["baudrate"])
            self.assertEqual({"tx": 17, "rx": None}, motor_uart["GPIO"])
            self.assertEqual(
                1,
                profile["uartMotor"]["list"][0]["GPIO"]["uart"],
            )


if __name__ == "__main__":
    unittest.main()
