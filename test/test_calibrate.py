#!/usr/bin/env python3
"""校準工具（calibrate_motor / calib_loader）與分段內插的 PC self-test。

涵蓋：
  - speed_to_byte 速度→byte 換算
  - MotorCalibrator._measure 的觸發 / 超時
  - MotorCalibrator.run 的順序（home→伸出→縮回，死區跳過反向）
  - save → load_calibration 的往返（含 address）與 t_full 同步
  - _lookup_rate 的分段線性內插 / 死區 / 單點線性
  - 每台（per-address）校準互相獨立
  - analyze 線性判定
"""

import os
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "slave"))   # lib.uart_motor（slave/lib）
sys.path.insert(0, _ROOT)                          # tools.calibrate_motor / tools.calib_loader

from lib.uart_motor import (
    UartMotor, speed_to_byte,
    SPEED_MAX, SPEED_MED, STOP,
)
from tools.calibrate_motor import MotorCalibrator, analyze
from tools.calib_loader import load_calibration


class FakeUART:
    def __init__(self):
        self.writes = []

    def write(self, data):
        self.writes.append(bytes(data))
        return len(data)


class FakeClock:
    def __init__(self):
        self.t = 0

    def __call__(self):
        return self.t

    @staticmethod
    def diff(a, b):
        return a - b


class FakeSwitch:
    """模擬限位開關：第一次輪詢記住「量測開始」，每次輪詢耗 1ms 推進時鐘，
    輪詢滿 reach_ms 次後觸發（value()==0，active_low）。"""

    def __init__(self, clock, reach_ms):
        self.clock = clock
        self.reach_ms = reach_ms
        self._start = None

    def value(self):
        if self._start is None:
            self._start = self.clock.t
        self.clock.t += 1
        return 0 if (self.clock.t - self._start) >= self.reach_ms else 1


class _ScriptedCal(MotorCalibrator):
    """把 _home/_measure 替換成腳本，驗證 run() 的控制流程。"""

    def __init__(self, motor, address, script, **kw):
        super().__init__(motor, address, extend_pin=0, retract_pin=1, **kw)
        self._script = list(script)
        self.homes = 0
        self.calls = []

    def _home(self):
        self.homes += 1

    def _measure(self, byte, which):
        self.calls.append(which)
        return self._script.pop(0)


def _motor():
    return UartMotor({"version": 1, "addresses": [11], "uart": FakeUART()})


class TestSpeedToByte(unittest.TestCase):

    def test_forward(self):
        self.assertEqual(speed_to_byte(SPEED_MAX, 1), 0x00)
        self.assertEqual(speed_to_byte(SPEED_MED, 1), 0x40)
        self.assertEqual(speed_to_byte(0, 1), STOP)

    def test_reverse(self):
        self.assertEqual(speed_to_byte(SPEED_MAX, -1), 0xFF)
        self.assertEqual(speed_to_byte(SPEED_MED, -1), 0xC0)
        self.assertEqual(speed_to_byte(0, -1), STOP)


class TestMeasure(unittest.TestCase):

    def _cal(self, reach_ms, timeout_ms=1000):
        clock = FakeClock()
        motor = UartMotor({"version": 1, "addresses": [11],
                           "uart": FakeUART(), "clock": clock,
                           "clock_diff": FakeClock.diff})
        switch = FakeSwitch(clock, reach_ms)
        cal = MotorCalibrator(motor, 11, extend_pin=0, retract_pin=1,
                              timeout_ms=timeout_ms, clock=clock,
                              clock_diff=FakeClock.diff,
                              pin_factory=lambda n: switch)
        return cal

    def test_trigger_returns_elapsed(self):
        cal = self._cal(reach_ms=50)
        elapsed = cal._measure(speed_to_byte(SPEED_MAX, 1), "extend")
        self.assertEqual(elapsed, 50)

    def test_timeout_returns_none(self):
        cal = self._cal(reach_ms=999999, timeout_ms=100)
        elapsed = cal._measure(speed_to_byte(SPEED_MAX, 1), "extend")
        self.assertIsNone(elapsed)


class TestRun(unittest.TestCase):

    def test_sequence(self):
        motor = _motor()
        cal = _ScriptedCal(motor, 11, script=[100, 90, 50, 45, 200, 180])
        res = cal.run([24, 64, 128])
        self.assertEqual(cal.homes, 3)
        self.assertEqual(cal.calls,
                         ["extend", "retract", "extend", "retract", "extend", "retract"])
        self.assertEqual([r["speed"] for r in res], [24, 64, 128])
        self.assertEqual(res[0]["forward_ms"], 100)
        self.assertEqual(res[0]["reverse_ms"], 90)

    def test_dead_forward_skips_reverse(self):
        motor = _motor()
        cal = _ScriptedCal(motor, 11, script=[None])
        res = cal.run([24])
        self.assertEqual(cal.homes, 1)
        self.assertEqual(cal.calls, ["extend"])
        self.assertIsNone(res[0]["forward_ms"])
        self.assertIsNone(res[0]["reverse_ms"])


class TestSaveLoad(unittest.TestCase):

    def test_roundtrip(self):
        cal = MotorCalibrator(_motor(), 11, extend_pin=0, retract_pin=1)
        with tempfile.TemporaryDirectory() as d:
            results = [
                {"speed": 24, "forward_ms": 16000, "reverse_ms": 17000},
                {"speed": 64, "forward_ms": 8000, "reverse_ms": 8500},
                {"speed": 128, "forward_ms": 4000, "reverse_ms": 4200},
            ]
            cal.save(results, d)

            m = _motor()
            loaded = load_calibration(m, d)
            self.assertEqual(loaded, [(11, 24), (11, 64), (11, 128)])
            self.assertIn(24, m._rate_fwd[11])
            self.assertIn(128, m._rate_rev[11])
            # 全速點同步該台 t_full
            self.assertEqual(m._t_full_fwd_ms[11], 4000)
            self.assertEqual(m._t_full_rev_ms[11], 4200)

    def test_dead_zone_null_skipped(self):
        cal = MotorCalibrator(_motor(), 11, extend_pin=0, retract_pin=1)
        with tempfile.TemporaryDirectory() as d:
            cal.save([{"speed": 24, "forward_ms": None, "reverse_ms": None}], d)
            m = _motor()
            load_calibration(m, d)
            self.assertNotIn(24, m._rate_fwd[11])
            self.assertNotIn(24, m._rate_rev[11])


class TestInterpolation(unittest.TestCase):

    def _m(self):
        return UartMotor({"version": 1, "addresses": [11], "uart": FakeUART(),
                          "t_full_ms": 4000})

    def test_piecewise(self):
        m = self._m()
        m.calibrate(11, 1, 24, 16000)
        m.calibrate(11, 1, 64, 8000)
        m.calibrate(11, 1, 128, 4000)
        # rate = (4095<<12)/ms
        self.assertEqual(m._lookup_rate(11, 24, 1), (4095 << 12) // 16000)
        self.assertEqual(m._lookup_rate(11, 64, 1), (4095 << 12) // 8000)
        self.assertEqual(m._lookup_rate(11, 128, 1), (4095 << 12) // 4000)
        # 44 落在 24..64 之間 → 線性內插
        r24 = m._lookup_rate(11, 24, 1)
        r64 = m._lookup_rate(11, 64, 1)
        expected = r24 + (r64 - r24) * (44 - 24) // (64 - 24)
        self.assertEqual(m._lookup_rate(11, 44, 1), expected)
        # 低於最低點 → 死區 0
        self.assertEqual(m._lookup_rate(11, 10, 1), 0)
        # 高於最高點 → clamp 到最高（128）
        self.assertEqual(m._lookup_rate(11, 200, 1), m._lookup_rate(11, 128, 1))

    def test_single_point_linear_from_origin(self):
        m = self._m()
        m.calibrate(11, 1, 128, 4000)   # 只校準全速
        r128 = m._lookup_rate(11, 128, 1)
        self.assertEqual(m._lookup_rate(11, 64, 1), r128 * 64 // 128)   # 半速 = 一半


class TestPerAddress(unittest.TestCase):

    def test_t_full_and_calib_independent(self):
        m = UartMotor({"version": 1, "addresses": [11, 12], "uart": FakeUART(),
                       "t_full_fwd_ms": {11: 4000, 12: 8000}})
        self.assertEqual(m._t_full_fwd_ms[11], 4000)
        self.assertEqual(m._t_full_fwd_ms[12], 8000)
        self.assertEqual(m._rate_full_fwd[11], (4095 << 12) // 4000)
        self.assertEqual(m._rate_full_fwd[12], (4095 << 12) // 8000)

        # 校準表各自獨立
        m.calibrate(11, 1, 64, 8000)
        m.calibrate(12, 1, 64, 16000)
        self.assertNotEqual(m._rate_fwd[11][64], m._rate_fwd[12][64])
        self.assertNotEqual(m._lookup_rate(11, 64, 1), m._lookup_rate(12, 64, 1))

    def test_set_t_full_and_calibrate_unknown_addr(self):
        m = UartMotor({"version": 1, "addresses": [11], "uart": FakeUART()})
        with self.assertRaises(ValueError):
            m.set_t_full(99, 1, 1000)
        with self.assertRaises(ValueError):
            m.calibrate(99, 1, 64, 8000)


class TestAnalyze(unittest.TestCase):

    def test_linear(self):
        results = [
            {"speed": 24, "forward_ms": 21333, "reverse_ms": 21333},
            {"speed": 64, "forward_ms": 8000, "reverse_ms": 8000},
            {"speed": 128, "forward_ms": 4000, "reverse_ms": 4000},
        ]
        by_dir = {d["direction"]: d for d in analyze(results)}
        self.assertEqual(by_dir["forward"]["verdict"], "linear")
        self.assertEqual(by_dir["reverse"]["verdict"], "linear")

    def test_nonlinear_low_speed_slow(self):
        results = [
            {"speed": 24, "forward_ms": 16000, "reverse_ms": None},
            {"speed": 64, "forward_ms": 8000, "reverse_ms": None},
            {"speed": 128, "forward_ms": 4000, "reverse_ms": None},
        ]
        by_dir = {d["direction"]: d for d in analyze(results)}
        self.assertEqual(by_dir["forward"]["verdict"], "nonlinear")
        self.assertEqual(by_dir["reverse"]["verdict"], "dead")

    def test_insufficient_single_point(self):
        results = [{"speed": 128, "forward_ms": 4000, "reverse_ms": 4000}]
        by_dir = {d["direction"]: d for d in analyze(results)}
        self.assertEqual(by_dir["forward"]["verdict"], "insufficient")


class TestCalibConfig(unittest.TestCase):

    def test_per_axis_dict(self):
        m = UartMotor({"version": 1, "addresses": [11, 12], "uart": FakeUART(),
                       "calib": {
                           11: {128: 4000},
                           12: {128: 8000},
                       }})
        self.assertEqual(m._t_full_fwd_ms[11], 4000)
        self.assertEqual(m._t_full_fwd_ms[12], 8000)
        self.assertEqual(m._rate_full_fwd[11], (4095 << 12) // 4000)
        self.assertEqual(m._rate_full_fwd[12], (4095 << 12) // 8000)

    def test_three_point_table_symmetric(self):
        m = UartMotor({"version": 1, "addresses": [11, 12], "uart": FakeUART(),
                       "calib": {
                           11: {24: 16000, 64: 8000, 128: 4000},
                           12: {24: 24000, 64: 12000, 128: 6000},
                       }})
        # 三點進校準表，正反同值（speed=128 同步 t_full）
        self.assertIn(24, m._rate_fwd[11])
        self.assertIn(24, m._rate_rev[11])
        self.assertIn(64, m._rate_rev[12])
        self.assertEqual(m._t_full_fwd_ms[11], 4000)
        self.assertEqual(m._t_full_rev_ms[11], 4000)   # 正反同值
        self.assertEqual(m._t_full_fwd_ms[12], 6000)

    def test_single_point_linear_from_origin(self):
        m = UartMotor({"version": 1, "addresses": [11], "uart": FakeUART(),
                       "calib": {11: {128: 4000}}})
        r128 = m._lookup_rate(11, 128, 1)
        self.assertEqual(m._lookup_rate(11, 64, 1), r128 * 64 // 128)

    def test_invalid_calib_raises(self):
        with self.assertRaises(ValueError):
            UartMotor({"version": 1, "addresses": [11], "uart": FakeUART(),
                       "calib": {99: {128: 4000}}})     # 不在控制列表
        with self.assertRaises(ValueError):
            UartMotor({"version": 1, "addresses": [11], "uart": FakeUART(),
                       "calib": {11: {24: 0}}})         # ms 必須 > 0
        with self.assertRaises(ValueError):
            UartMotor({"version": 1, "addresses": [11], "uart": FakeUART(),
                       "calib": 4000})                  # 不接受裸 int

    def test_missing_high_point_interpolates_to_full(self):
        # 只校準低/中，沒給 128：全速仍應來自 rate_full，而非被 clamp 到中速
        m = UartMotor({"version": 1, "addresses": [11], "uart": FakeUART(),
                       "t_full_ms": 4000})
        m.calibrate(11, 1, 24, 16000)
        m.calibrate(11, 1, 64, 8000)
        self.assertEqual(m._lookup_rate(11, 128, 1), (4095 << 12) // 4000)
        # 100 落在 64..128 之間 → 內插，不是 clamp 到 64
        r64 = m._lookup_rate(11, 64, 1)
        r128 = m._lookup_rate(11, 128, 1)
        expected = r64 + (r128 - r64) * (100 - 64) // (128 - 64)
        self.assertEqual(m._lookup_rate(11, 100, 1), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
