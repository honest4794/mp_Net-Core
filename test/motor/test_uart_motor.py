#!/usr/bin/env python3
"""uart_motor.py 的 PC self-test（不依賴 MicroPython / 硬體）

FakeUART 收集 write 的 bytes，驗證：
  - v1 frame 位元組（廣播 / 單台 / 未控制位置停車）
  - set / set_all / set_many / send / send_all / stop_all 語義
  - version 分派（v1、未知 version raise、register_command_method 擴充）
  - show_all 單次 write（一次過推送）
  - get_write_view 零拷貝語義
  - 初始化參數防呆（addresses 驗證、uart 缺失）
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "slave"))

from lib.uart_motor import (
    UartMotor, register_command_method,
    HEADER, ENDING, STOP, FWD, REV, FWD_FS, REV_FS,
    SPEED_MAX, SPEED_MED, SPEED_STOP, POS_MAX,
)


class FakeUART:
    def __init__(self):
        self.writes = []

    def write(self, data):
        self.writes.append(bytes(data))
        return len(data)


class TestFramesV1(unittest.TestCase):

    def setUp(self):
        self.uart = FakeUART()
        self.motor = UartMotor({
            "version": 1,
            "addresses": [1, 2, 3],
            "uart": self.uart,
        })

    def test_initial_buffer_safe_stop(self):
        self.assertEqual(bytes(self.motor.buffer), bytes([STOP] * 3))

    def test_broadcast_frame_after_show_all(self):
        self.motor.set(1, FWD)
        self.motor.set(2, REV)
        self.motor.show_all()
        # addr3 未設定 → 停車 0x80
        self.assertEqual(self.uart.writes[-1],
                         bytes([HEADER, 0x00, FWD, REV, STOP, ENDING]))

    def test_single_frame_via_send(self):
        self.motor.send(2, FWD)
        self.assertEqual(self.uart.writes[-1],
                         bytes([HEADER, 0x02, FWD, ENDING]))

    def test_send_updates_buffer(self):
        self.motor.send(1, FWD)
        self.assertEqual(self.motor.buffer[0], FWD)
        # buffer 為權威狀態：之後 show_all 廣播的是最新值
        self.motor.show_all()
        self.assertEqual(self.uart.writes[-1][2], FWD)

    def test_show_all_single_write(self):
        self.motor.send_all(REV)
        n_before = len(self.uart.writes)
        for _ in range(3):
            self.motor.show_all()
        self.assertEqual(len(self.uart.writes) - n_before, 3)
        for w in self.uart.writes[-3:]:
            self.assertEqual(w, bytes([HEADER, 0x00, REV, REV, REV, ENDING]))

    def test_set_all_and_stop_all(self):
        self.motor.set_all(REV)
        self.assertEqual(bytes(self.motor.buffer), bytes([REV] * 3))
        self.motor.stop_all()
        self.assertEqual(self.uart.writes[-1],
                         bytes([HEADER, 0x00, STOP, STOP, STOP, ENDING]))
        self.assertEqual(bytes(self.motor.buffer), bytes([STOP] * 3))

    def test_send_all_immediate(self):
        self.motor.send_all(FWD)
        self.assertEqual(self.uart.writes[-1],
                         bytes([HEADER, 0x00, FWD, FWD, FWD, ENDING]))

    def test_set_many_dict(self):
        self.motor.set_many({1: FWD, 3: REV})
        self.assertEqual(bytes(self.motor.buffer),
                         bytes([FWD, STOP, REV]))

    def test_set_many_list(self):
        self.motor.set_many([FWD, REV, STOP])
        self.assertEqual(bytes(self.motor.buffer),
                         bytes([FWD, REV, STOP]))

    def test_set_many_list_wrong_len(self):
        with self.assertRaises(ValueError):
            self.motor.set_many([FWD, REV])

    def test_set_unknown_address_raises(self):
        with self.assertRaises(ValueError):
            self.motor.set(4, FWD)
        with self.assertRaises(ValueError):
            self.motor.send(0, FWD)

    def test_get_write_view_zero_copy(self):
        view = self.motor.get_write_view()
        view[0] = FWD
        self.assertEqual(self.motor.buffer[0], FWD)
        self.motor.show_all()
        self.assertEqual(self.uart.writes[-1][2], FWD)


class TestNumDevices(unittest.TestCase):

    def test_num_devices_is_max_address(self):
        motor = UartMotor({
            "version": 1,
            "addresses": [1, 8],
            "uart": FakeUART(),
        })
        self.assertEqual(motor.num_devices, 8)
        self.assertEqual(len(motor), 8)
        self.assertEqual(len(motor.buffer), 8)
        # 未控制的中間位置維持停車
        self.assertEqual(bytes(motor.buffer), bytes([STOP] * 8))

    def test_single_address(self):
        motor = UartMotor({
            "version": 1,
            "addresses": 2,      # 單一 int 也接受
            "uart": FakeUART(),
        })
        self.assertEqual(motor.addresses, [2])
        self.assertEqual(motor.num_devices, 2)


class TestInitValidation(unittest.TestCase):

    def test_missing_uart_raises(self):
        with self.assertRaises(ValueError):
            UartMotor({"version": 1, "addresses": [1]})

    def test_missing_addresses_raises(self):
        with self.assertRaises(ValueError):
            UartMotor({"version": 1, "uart": FakeUART()})

    def test_empty_addresses_raises(self):
        with self.assertRaises(ValueError):
            UartMotor({"version": 1, "addresses": [], "uart": FakeUART()})

    def test_address_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            UartMotor({"version": 1, "addresses": [0], "uart": FakeUART()})
        with self.assertRaises(ValueError):
            UartMotor({"version": 1, "addresses": [256], "uart": FakeUART()})

    def test_unknown_version_raises(self):
        with self.assertRaises(ValueError):
            UartMotor({"version": 99, "addresses": [1], "uart": FakeUART()})


class TestVersionDispatch(unittest.TestCase):

    def test_register_v2_switches_frame(self):
        # 模擬對方改協定：v2 用不同 HEADER（0xEE）與結尾
        def build_v2_broadcast(frame, buffer, n):
            frame[0] = 0xEE
            frame[1] = 0x00
            for i in range(n):
                frame[2 + i] = buffer[i]
            frame[2 + n] = 0xEF

        def build_v2_single(frame, addr, value):
            frame[0] = 0xEE
            frame[1] = addr
            frame[2] = value
            frame[3] = 0xEF

        register_command_method(2, build_v2_broadcast, build_v2_single)

        uart = FakeUART()
        motor = UartMotor({
            "version": 2,
            "addresses": [1, 2],
            "uart": uart,
        })
        motor.send(1, FWD)
        self.assertEqual(uart.writes[-1], bytes([0xEE, 0x01, FWD, 0xEF]))
        motor.show_all()
        self.assertEqual(uart.writes[-1],
                         bytes([0xEE, 0x00, FWD, STOP, 0xEF]))

        # v1 不受影響
        uart_v1 = FakeUART()
        motor_v1 = UartMotor({
            "version": 1,
            "addresses": [1, 2],
            "uart": uart_v1,
        })
        motor_v1.send(1, FWD)
        self.assertEqual(uart_v1.writes[-1],
                         bytes([HEADER, 0x01, FWD, ENDING]))


class FakeClock:
    def __init__(self):
        self.t = 0

    def __call__(self):
        return self.t

    @staticmethod
    def diff(a, b):
        return a - b


class TestMotionLayer(unittest.TestCase):

    def _motor(self, **kw):
        self.clock = FakeClock()
        cfg = {
            "version": 1,
            "addresses": [1, 2],
            "uart": FakeUART(),
            "clock": self.clock,
            "clock_diff": FakeClock.diff,
            "t_full_ms": 4095,      # 全速 = 4096 定點格/ms → 1 格/ms
        }
        cfg.update(kw)
        return UartMotor(cfg)

    def test_move_to_full_speed_byte(self):
        m = self._motor()
        m.move_to(1, 4095, SPEED_MAX)          # 伸 → 正轉全速 0x00
        self.assertEqual(m.buffer[0], 0x00)
        m.move_to(2, 0, SPEED_MAX)             # addr2 已在 0 → 停
        self.assertEqual(m.buffer[1], STOP)

    def test_speed_byte_mid_direction(self):
        m = self._motor()
        m.move_to(1, 4095, SPEED_MED)          # 中速伸 → 0x40
        self.assertEqual(m.buffer[0], FWD)
        self.clock.t = 8190                     # 中速全程 = 2 × 全速時間
        m.update()
        self.assertEqual(m.position(1), 4095)
        m.move_to(1, 0, SPEED_MED)             # 中速縮 → 0xC0
        self.assertEqual(m.buffer[0], REV)

    def test_position_advances_with_time(self):
        m = self._motor()
        m.move_to(1, 4095, SPEED_MAX)
        self.clock.t = 1000
        self.assertEqual(m.position(1), 1000)

    def test_half_speed(self):
        m = self._motor()
        m.move_to(1, 4095, SPEED_MED)
        self.clock.t = 1000
        self.assertEqual(m.position(1), 500)

    def test_stop_at_target(self):
        m = self._motor()
        m.move_to(1, 1000, SPEED_MAX)
        self.clock.t = 1000
        m.update()
        self.assertEqual(m.position(1), 1000)
        self.assertEqual(m.buffer[0], STOP)
        self.clock.t = 9999
        self.assertEqual(m.position(1), 1000)   # 停後時間走也不動

    def test_clamp_at_limits(self):
        m = self._motor()
        m.move_to(1, 4095, SPEED_MAX)
        self.clock.t = 99999
        m.update()
        self.assertEqual(m.position(1), POS_MAX)
        m.move_to(1, 0, SPEED_MAX)
        self.clock.t = 199999
        m.update()
        self.assertEqual(m.position(1), 0)

    def test_move_relative(self):
        m = self._motor()
        m.move(1, 1000, SPEED_MAX)
        self.clock.t = 500
        self.assertEqual(m.position(1), 500)
        m.move(1, -300, SPEED_MAX)             # 從結算位置 500 往回 300
        self.clock.t = 800
        self.assertEqual(m.position(1), 200)

    def test_calibrate_overrides_rate(self):
        m = self._motor()
        # 預設全速 1 格/ms；校準全程 8190ms → 速率減半 = 0.5 格/ms
        m.calibrate(1, 1, SPEED_MAX, 8190)
        m.move_to(1, 4095, SPEED_MAX)
        self.clock.t = 1000
        self.assertEqual(m.position(1), 500)

    def test_set_t_full(self):
        m = self._motor()
        m.set_t_full(1, -1, 8190)              # 縮回全程 8190ms → 0.5 格/ms
        m.move_to(1, 4095, SPEED_MAX)          # 先伸到頂
        self.clock.t = 4095
        m.update()
        m.move_to(1, 0, SPEED_MAX)             # 縮回，用 rev 速率
        self.clock.t = 4095 + 1000
        self.assertEqual(m.position(1), 4095 - 500)

    def test_speed_stop(self):
        m = self._motor()
        m.move_to(1, 4095, SPEED_STOP)
        self.assertEqual(m.buffer[0], STOP)
        self.clock.t = 1000
        self.assertEqual(m.position(1), 0)

    def test_move_to_clamps_target(self):
        m = self._motor()
        m.move_to(1, 999999, SPEED_MAX)
        self.clock.t = 9999
        m.update()
        self.assertEqual(m.position(1), POS_MAX)

    def test_position_unknown_addr(self):
        m = self._motor()
        with self.assertRaises(ValueError):
            m.position(99)

    def test_calibrate_bad_args(self):
        m = self._motor()
        with self.assertRaises(ValueError):
            m.calibrate(1, 1, 0, 100)
        with self.assertRaises(ValueError):
            m.calibrate(1, 1, SPEED_MAX, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
