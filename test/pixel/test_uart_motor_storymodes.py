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
from pixel.effects.effects import (
    uart_dc_motor_profile_speed,
    uart_dc_motor_scale_profile_speed,
    uart_dc_motor_value,
    uart_motor_dev_sine,
)


EFFECTS_PATH = os.path.join(SLAVE, "pixel", "effects", "effects.json")
MAPPING_PATH = os.path.join(SLAVE, "pixel", "map", "hi_nu_uart_motor_test.json")
MODES_DIR = os.path.join(SLAVE, "pixel", "modes")
REGISTRY_PATH = os.path.join(SLAVE, "pixel", "registry.json")
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
    for mode in load_json(REGISTRY_PATH).get("modes", []):
        if mode["id"] == mode_id:
            return mode
    raise KeyError(mode_id)


def direct_chain(addresses, value):
    payload = bytearray()
    for address in addresses:
        payload.extend((0xFF, address, value, 0xFE))
    return bytes(payload)


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
    def test_diagnostic_mode_is_inline_in_registry_not_a_separate_file(self):
        registry = load_json(REGISTRY_PATH)
        inline = {mode["name"]: mode for mode in registry.get("modes", [])}

        self.assertIn("motor_diagnostic", inline)
        self.assertEqual(0, inline["motor_diagnostic"]["id"])
        self.assertIn("motor_diagnostic", registry["list"])
        self.assertFalse(registry["auto_play"])
        self.assertFalse(os.path.exists(
            os.path.join(MODES_DIR, "motor_diagnostic.json")))

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
                {"id": 2, "baudrate": 9600, "GPIO": {"tx": 12, "rx": None}},
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
        self.assertEqual(12, uart_calls[0][1]["tx"].pin)
        self.assertEqual(-1, uart_calls[0][1]["rx"])

    def test_uart_driver_rx_only_never_drives_shared_rs485_bus(self):
        """Black sidecars share blue A/B: they may receive, but must never reply."""
        uart_calls = []
        pins = {}

        class FakePin:
            OUT = 1

            def __init__(self, pin, *_args, **kwargs):
                self.pin = pin
                self.level = kwargs.get("value")
                pins[pin] = self

            def value(self, value=None):
                if value is not None:
                    self.level = value
                return self.level

        class FakeMachineUART:
            def __init__(self, uart_id, **kwargs):
                self.rx = bytearray(b"NC")
                self.writes = []
                uart_calls.append((uart_id, kwargs, self))

            def write(self, data):
                self.writes.append(bytes(data))
                return len(data)

            def any(self):
                return len(self.rx)

            def read(self, n=-1):
                if n < 0:
                    n = len(self.rx)
                data = bytes(self.rx[:n])
                del self.rx[:n]
                return data

            def readinto(self, buf):
                n = min(len(buf), len(self.rx))
                buf[:n] = self.rx[:n]
                del self.rx[:n]
                return n

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
            spec = importlib.util.spec_from_file_location("uart_drv_rx_only", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            bus = FakeHardwareBus([{
                "id": 1,
                "baudrate": 115200,
                "rx_only": 1,
                "rx_en_level": 0,
                "GPIO": {"tx": 10, "rx": 11, "en": 9},
            }])
            wrapped = module.init_uart(bus)[0]
        finally:
            if old_machine is None:
                sys.modules.pop("machine", None)
            else:
                sys.modules["machine"] = old_machine
            if old_log_service is None:
                sys.modules.pop("lib.sys.log_service", None)
            else:
                sys.modules["lib.sys.log_service"] = old_log_service

        underlying = uart_calls[0][2]
        self.assertEqual(-1, uart_calls[0][1]["tx"])
        self.assertEqual(11, uart_calls[0][1]["rx"].pin)
        self.assertEqual(0, pins[9].level)
        self.assertEqual(3, wrapped.write(b"ACK"))
        self.assertEqual([], underlying.writes)
        self.assertEqual(2, wrapped.any())
        self.assertEqual(b"NC", wrapped.read(2))
        self.assertEqual(0, pins[9].level)

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
            self.assertEqual("rgbw" if mode_id == 2 else "w",
                             mode["map"][0]["write"])

    def test_mode_zero_runs_direction_a_then_stays_stopped(self):
        """Changing diagnostic duration or its safe A command must be detected."""
        effect = Effect("uart_motor_diagnostic", effect_params("uart_motor_diagnostic"))

        self.assertEqual(16, effect.frame(0)[0])       # W >> 4 = marker 0x01
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
        """Mode 2 follows storyMode_dev's B/stop/A/stop timing for six cycles."""
        effect = uart_motor_dev_sine(
            "uart_motor_dev_sine", effect_params("uart_motor_dev_sine"))

        # rgbw transport: R=4095 is the explicit-raw marker; W=raw << 4.
        expected_raw = {
            0: 128,
            125: 242,
            250: 255,
            375: 242,
            499: 131,
            500: 128,
            750: 128,
            875: 13,
            1000: 0,
            1125: 13,
            1249: 125,
            1250: 128,
            1500: 128,
            9000: 128,
            20000: 128,
        }
        for frame_no, raw in expected_raw.items():
            frame = effect.frame(frame_no)
            self.assertEqual([4095, 0, 0], list(frame[:3]))
            self.assertEqual(raw << 4, frame[3], frame_no)

    def test_mode_two_math_matches_hinu_cpp_reference_vectors(self):
        """Literal vectors pin patterns_uart_dc_motor.cpp's two-stage sine math."""
        expected = {
            0: (0, 0, 128, 128),
            125: (71, 90, 13, 242),
            250: (100, 100, 0, 255),
            375: (71, 90, 13, 242),
            499: (1, 2, 125, 131),
            500: (0, 0, 128, 128),
        }
        for elapsed, (profile, scaled, close_raw, open_raw) in expected.items():
            self.assertEqual(profile,
                             uart_dc_motor_profile_speed(elapsed, 500))
            self.assertEqual(
                scaled,
                uart_dc_motor_scale_profile_speed(profile, 100, "Sine"),
            )
            self.assertEqual(close_raw, uart_dc_motor_value("A", scaled))
            self.assertEqual(open_raw, uart_dc_motor_value("B", scaled))

        # FNV-1a over all 500 frames × A/B, independently generated by compiling
        # the referenced C++ float/sinf formulas. This catches differences between
        # checkpoints without copying a 1000-byte golden table into the repo.
        digest = 2166136261
        for elapsed in range(500):
            profile = uart_dc_motor_profile_speed(elapsed, 500)
            scaled = uart_dc_motor_scale_profile_speed(profile, 100, "Sine")
            for direction in ("A", "B"):
                digest ^= uart_dc_motor_value(direction, scaled)
                digest = (digest * 16777619) & 0xFFFFFFFF
        self.assertEqual(0xB13ED0E8, digest)

    def test_profile_addresses_receive_mode_one_max_command(self):
        """A wrong profile/address or mapping selector must change the emitted frames."""
        mapping = load_json(MAPPING_PATH)
        effect = Effect("uart_motor_max_open", effect_params("uart_motor_max_open"))

        for slave_id, profile_info in SLAVE_PROFILES.items():
            profile_path, expected_addresses, _expected_cid = profile_info
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
            self.assertNotIn("sync_broadcast_span", motor_cfg["list"][0])
            self.assertNotIn("sync_tx_interval_ms", motor_cfg["list"][0])
            self.assertNotIn("calib", motor_cfg["list"][0])

            uart = FakeUART()
            motor = UartMotor({
                "version": motor_cfg["list"][0].get("version", 1),
                "addresses": addresses,
                "uart": uart,
                "dStay": motor_cfg["list"][0].get("dStay", 2048),
                "sync_broadcast_span": motor_cfg["list"][0].get(
                    "sync_broadcast_span", 0),
                "sync_tx_interval_ms": motor_cfg["list"][0].get(
                    "sync_tx_interval_ms", 0),
            })
            layout = PixelLayout(["uartMotor1"], {"uartMotor1": motor.num_pixels})
            layout.register_mapping(mapping["id"], mapping["name"], mapping["groups"])
            frame = bytearray(motor.frame_size)
            layout.scatter(frame, mapping["name"], "all_uart_motors", effect.frame(0), "w")
            motor.st_load_and_convert(frame, 0)
            motor.st_show()

            self.assertEqual(
                direct_chain(expected_addresses, 0xFF), uart.writes[-1])

    def test_profile_addresses_receive_mode_zero_true_max_a_then_stop(self):
        """All four motors receive raw 0x00 for 500 frames, then raw 0x80."""
        mapping = load_json(MAPPING_PATH)
        effect = Effect("uart_motor_diagnostic", effect_params("uart_motor_diagnostic"))

        for slave_id, (profile_path, expected_addresses, _expected_cid) in SLAVE_PROFILES.items():
            profile = load_json(profile_path)
            motor_cfg = profile["uartMotor"]["list"][0]
            uart = FakeUART()
            motor = UartMotor({
                "version": motor_cfg.get("version", 1),
                "addresses": expected_addresses,
                "uart": uart,
                "dStay": motor_cfg.get("dStay", 2048),
                "sync_broadcast_span": motor_cfg.get("sync_broadcast_span", 0),
                "sync_tx_interval_ms": motor_cfg.get("sync_tx_interval_ms", 0),
            })
            layout = PixelLayout(["uartMotor1"], {"uartMotor1": motor.num_pixels})
            layout.register_mapping(mapping["id"], mapping["name"], mapping["groups"])

            def emit(frame_no):
                frame = bytearray(motor.frame_size)
                layout.scatter(
                    frame, mapping["name"], "all_uart_motors",
                    effect.frame(frame_no), "w",
                )
                motor.st_load_and_convert(frame, 0)
                motor.st_show()
                return uart.writes[-1]

            self.assertEqual(direct_chain(expected_addresses, 0x00), emit(0))
            self.assertEqual(direct_chain(expected_addresses, 0x80), emit(500))

    def test_mode_two_peak_sends_exact_raw_zero_through_rgbw_transport(self):
        """C++ A peak must survive Pixel's blank-W safety rule as explicit raw 0x00."""
        mapping = load_json(MAPPING_PATH)
        effect = uart_motor_dev_sine(
            "uart_motor_dev_sine", effect_params("uart_motor_dev_sine"))

        for _slave_id, (profile_path, expected_addresses, _cid) in SLAVE_PROFILES.items():
            motor_cfg = load_json(profile_path)["uartMotor"]["list"][0]
            uart = FakeUART()
            motor = UartMotor({
                "version": motor_cfg.get("version", 1),
                "addresses": expected_addresses,
                "uart": uart,
                "dStay": motor_cfg.get("dStay", 2048),
                "sync_broadcast_span": motor_cfg.get("sync_broadcast_span", 0),
                "sync_tx_interval_ms": motor_cfg.get("sync_tx_interval_ms", 0),
            })
            layout = PixelLayout(["uartMotor1"], {"uartMotor1": motor.num_pixels})
            layout.register_mapping(mapping["id"], mapping["name"], mapping["groups"])
            frame = bytearray(motor.frame_size)
            layout.scatter(
                frame, mapping["name"], "all_uart_motors",
                effect.frame(1000), "rgbw",
            )
            motor.st_load_and_convert(frame, 0)
            motor.st_show()

            self.assertEqual(
                direct_chain(expected_addresses, 0x00), uart.writes[-1])

    def test_profiles_use_black_rs485_and_gpio12_motor_hardware(self):
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
                {"tx": 10, "rx": 11, "en": 9},
                rs485["GPIO"],
            )
            self.assertEqual(1, rs485["rx_only"])
            self.assertEqual(0, rs485["rx_en_level"])
            self.assertEqual(1, rs485["en_settle_ms"])

            motor_uart = profile["UART"]["list"][1]
            self.assertEqual(2, motor_uart["id"])
            self.assertEqual(9600, motor_uart["baudrate"])
            self.assertEqual({"tx": 12, "rx": None}, motor_uart["GPIO"])
            self.assertEqual(
                1,
                profile["uartMotor"]["list"][0]["GPIO"]["uart"],
            )

    def test_profiles_use_original_direct_motor_frames(self):
        """Field ATtiny boards must not depend on the optional broadcast parser."""
        for profile_path, _addresses, _cid in SLAVE_PROFILES.values():
            motor = load_json(profile_path)["uartMotor"]["list"][0]
            self.assertNotIn("sync_broadcast_span", motor)
            self.assertNotIn("sync_tx_interval_ms", motor)


if __name__ == "__main__":
    unittest.main()
