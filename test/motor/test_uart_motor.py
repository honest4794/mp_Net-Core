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

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_ROOT, "slave"))

from lib.hw.uart_motor import (
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


def _chain(*pairs):
    """單台串接 frame：pairs = [(addr, value), ...] → b'FF addr value FE' × N。"""
    out = bytearray()
    for addr, value in pairs:
        out += bytes([HEADER, addr, value, ENDING])
    return bytes(out)


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

    def test_show_all_single_chain(self):
        """show_all = 單台 frame 串接（UART-412 廣播受 MAX_DEVICE=32 限制，
        address 不連續/超 32 時只能單台串接一次過發送）。"""
        self.motor.set(1, FWD)
        self.motor.set(2, REV)
        self.motor.show_all()
        # addr3 未設定 → 停車 0x80
        self.assertEqual(self.uart.writes[-1],
                         _chain((1, FWD), (2, REV), (3, STOP)))

    def test_single_frame_via_send(self):
        self.motor.send(2, FWD)
        self.assertEqual(self.uart.writes[-1],
                         bytes([HEADER, 0x02, FWD, ENDING]))

    def test_send_updates_buffer(self):
        self.motor.send(1, FWD)
        self.assertEqual(self.motor.buffer[0], FWD)
        # buffer 為權威狀態：之後 show_all 串接的是最新值
        self.motor.show_all()
        self.assertEqual(self.uart.writes[-1][2], FWD)

    def test_show_all_single_write(self):
        self.motor.send_all(REV)
        n_before = len(self.uart.writes)
        for _ in range(3):
            self.motor.show_all()
        self.assertEqual(len(self.uart.writes) - n_before, 3)
        for w in self.uart.writes[-3:]:
            self.assertEqual(w, _chain((1, REV), (2, REV), (3, REV)))

    def test_set_all_and_stop_all(self):
        self.motor.set_all(REV)
        self.assertEqual(bytes(self.motor.buffer), bytes([REV] * 3))
        self.motor.stop_all()
        self.assertEqual(self.uart.writes[-1],
                         _chain((1, STOP), (2, STOP), (3, STOP)))
        self.assertEqual(bytes(self.motor.buffer), bytes([STOP] * 3))

    def test_send_all_immediate(self):
        self.motor.send_all(FWD)
        self.assertEqual(self.uart.writes[-1],
                         _chain((1, FWD), (2, FWD), (3, FWD)))

    def test_sparse_address_chain(self):
        """address 不連續（如 [1,51]）→ 單台串接，中間不填空洞。"""
        uart = FakeUART()
        motor = UartMotor({"version": 1, "addresses": [1, 51], "uart": uart})
        motor.set(1, FWD)
        motor.set(51, REV)
        motor.show_all()
        self.assertEqual(uart.writes[-1], _chain((1, FWD), (51, REV)))

    def test_zero_to_deadzone_protection(self):
        """歸零保護：big_buffer W=0（初始/熄燈）→ 死區 0x80，不是全速正轉。"""
        big = bytearray(self.motor.frame_size)   # 全 0
        self.motor.st_load_and_convert(big, 0)
        self.assertEqual(bytes(self.motor.buffer), bytes([STOP] * 3))
        self.motor.st_show()
        self.assertEqual(self.uart.writes[-1],
                         _chain((1, STOP), (2, STOP), (3, STOP)))

    def test_w_channel_to_motor(self):
        """W 通道直讀：0x40 正轉中速、0xC0 反轉中速、0x80 停。"""
        big = bytearray(12)
        big[3] = 0x40
        big[7] = 0xC0
        big[11] = 0x80
        self.motor.st_load_and_convert(big, 0)
        self.motor.st_show()
        self.assertEqual(self.uart.writes[-1],
                         _chain((1, 0x40), (2, 0xC0), (3, 0x80)))

    def test_nonzero_marker_requests_true_direction_a_full_speed(self):
        """W=1 is explicit raw 0x00; W=0 remains the safe empty-cell STOP."""
        big = bytearray(self.motor.frame_size)
        big[3] = 1
        big[7] = 0
        big[11] = STOP
        self.motor.st_load_and_convert(big, 0)
        self.assertEqual(bytes(self.motor.buffer), bytes([FWD_FS, STOP, STOP]))

    def test_rgbw_raw_marker_preserves_zero_one_and_dead_zone(self):
        """R=0xFF marks W as exact raw, including otherwise ambiguous 0x00/0x01."""
        big = bytearray(self.motor.frame_size)
        for i, raw in enumerate((0x00, 0x01, STOP)):
            big[i * 4] = 0xFF
            big[i * 4 + 3] = raw
        self.motor.st_load_and_convert(big, 0)
        self.assertEqual(bytes(self.motor.buffer), bytes([0x00, 0x01, STOP]))

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
        # 模擬對方改協定：v2 用不同 HEADER（0xEE）與結尾（單台 frame 格式）
        def build_v2_single(frame, addr, value):
            frame[0] = 0xEE
            frame[1] = addr
            frame[2] = value
            frame[3] = 0xEF

        register_command_method(2, None, build_v2_single)

        uart = FakeUART()
        motor = UartMotor({
            "version": 2,
            "addresses": [1, 2],
            "uart": uart,
        })
        motor.send(1, FWD)
        self.assertEqual(uart.writes[-1], bytes([0xEE, 0x01, FWD, 0xEF]))
        # show_all = 單台 frame 串接（v2 用自己的 frame 格式）
        motor.set(2, STOP)
        motor.show_all()
        self.assertEqual(uart.writes[-1],
                         bytes([0xEE, 0x01, FWD, 0xEF,
                                0xEE, 0x02, STOP, 0xEF]))

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


class TestSynchronizedBroadcast(unittest.TestCase):

    def _motor(self, addresses=(15, 19), span=21, interval=40):
        self.clock = FakeClock()
        self.uart = FakeUART()
        return UartMotor({
            "version": 1,
            "addresses": list(addresses),
            "uart": self.uart,
            "clock": self.clock,
            "clock_diff": FakeClock.diff,
            "sync_broadcast_span": span,
            "sync_tx_interval_ms": interval,
        })

    def test_common_span_broadcast_latches_controlled_motors_at_same_eof(self):
        motor = self._motor()
        motor.set(15, 0x01)
        motor.set(19, 0x01)
        motor.show_all()

        expected_values = [STOP] * 21
        expected_values[14] = 0x01
        expected_values[18] = 0x01
        self.assertEqual(
            bytes([HEADER, 0x00] + expected_values + [ENDING]),
            self.uart.writes[-1],
        )
        self.assertEqual(24, len(self.uart.writes[-1]))

    def test_unchanged_payload_is_not_retransmitted(self):
        motor = self._motor()
        motor.set(15, REV_FS)
        motor.set(19, REV_FS)
        motor.show_all()
        motor.show_all()
        self.assertEqual(1, len(self.uart.writes))

    def test_throttle_keeps_latest_value_without_uart_backlog(self):
        motor = self._motor()
        motor.set_all(0x10)
        motor.show_all()

        self.clock.t = 20
        motor.set_all(0x20)
        motor.show_all()
        self.clock.t = 39
        motor.set_all(0x30)
        motor.show_all()
        self.assertEqual(1, len(self.uart.writes))

        self.clock.t = 40
        motor.show_all()
        self.assertEqual(2, len(self.uart.writes))
        self.assertEqual(0x30, self.uart.writes[-1][2 + 14])
        self.assertEqual(0x30, self.uart.writes[-1][2 + 18])

    def test_stop_all_bypasses_throttle(self):
        motor = self._motor()
        motor.set_all(REV_FS)
        motor.show_all()
        self.clock.t = 1
        motor.stop_all()

        self.assertEqual(2, len(self.uart.writes))
        self.assertEqual(bytes([HEADER, 0x00] + [STOP] * 21 + [ENDING]),
                         self.uart.writes[-1])

    def test_reserved_ending_value_cannot_truncate_sync_broadcast(self):
        """UART-412 treats the first 0xFE in broadcast data as the frame ending."""
        motor = self._motor(addresses=(12, 21))
        motor.set(12, ENDING)
        motor.set(21, ENDING)
        motor.show_all()

        frame = self.uart.writes[-1]
        self.assertEqual(ENDING, frame[-1])
        self.assertEqual(1, frame.count(ENDING))
        self.assertEqual(REV_FS, frame[2 + 11])
        self.assertEqual(REV_FS, frame[2 + 20])

    def test_span_must_cover_highest_address_and_uart412_limit(self):
        with self.assertRaises(ValueError):
            self._motor(addresses=(15, 19), span=18)
        with self.assertRaises(ValueError):
            self._motor(addresses=(15, 19), span=33)

    def test_sync_mode_requires_a_broadcast_encoder(self):
        def build_v2_single(frame, addr, value):
            frame[:] = bytes([0xEE, addr, value, 0xEF])

        register_command_method(22, None, build_v2_single)
        with self.assertRaises(ValueError):
            UartMotor({
                "version": 22,
                "addresses": [1],
                "uart": FakeUART(),
                "sync_broadcast_span": 1,
            })


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
