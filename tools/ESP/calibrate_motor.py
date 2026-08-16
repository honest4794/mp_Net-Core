"""calibrate_motor.py — UART 電機行程校準工具（限位開關自動偵測）

在裝置上跑：對每個速度點量「伸出全程時間」與「縮回全程時間」，
寫出 JSON（每速度一檔 speed_XXX.json），之後用 calib_loader.load_calibration() 讀回。

硬體假設（需依實物接線調整）：
  - 被校準的電機，伸到頭／縮到頭各接一顆限位開關到 GPIO 數位輸入。
  - 預設低電平觸發（開關導通時 pin.value()==0），可用 active_high 改。
  - 量測期間 busy-poll 限位開關直到觸發或 timeout，屬校準專用的一次性流程，
    與主控的「非阻塞 update()」無關。

流程（每速度點）：home（全速縮回對齊起點）→ 該速度伸出計時 → 該速度縮回計時。
timeout 表示該速度在此方向推不動（死區），記為 null。

用法（裝置上）:
    from lib.uart_motor import UartMotor
    from tools.ESP.calibrate_motor import MotorCalibrator

    motor = UartMotor({"version": 1, "addresses": [11], "uart": uart})
    cal = MotorCalibrator(motor, 11,
                          extend_pin=4, retract_pin=5,
                          timeout_ms=30000)
    results = cal.run([24, 64, 128])      # 低 / 中 / 高
    report(results)                        # 印出是否線性的報告
    cal.save(results, "/calib")           # → /calib/speed_024.json 等（含 address）
"""

import os
import time as _time

try:
    import machine
    _HAS_MACHINE = True
except ImportError:
    machine = None
    _HAS_MACHINE = False

try:
    import ujson as _json
except ImportError:
    import json as _json

try:
    _default_clock_ms = _time.ticks_ms
    _default_clock_diff = _time.ticks_diff
except AttributeError:
    def _default_clock_ms():
        return _time.monotonic_ns() // 1_000_000

    def _default_clock_diff(a, b):
        return a - b

from lib.uart_motor import UartMotor, speed_to_byte, STOP, SPEED_MAX


class MotorCalibrator:
    """單顆電機的行程校準器（限位開關自動偵測）。"""

    def __init__(self, motor, address, extend_pin, retract_pin,
                 active_high=False, timeout_ms=30000,
                 clock=None, clock_diff=None, pin_factory=None):
        if not isinstance(motor, UartMotor):
            raise TypeError("MotorCalibrator: motor 必須是 UartMotor 實例")
        if int(address) not in motor.addresses:
            raise ValueError(
                "MotorCalibrator: address {} 不在 motor 控制列表".format(address))
        self.motor = motor
        self.address = int(address)
        self.extend_pin_no = extend_pin
        self.retract_pin_no = retract_pin
        self.active_level = 1 if active_high else 0
        self.timeout_ms = int(timeout_ms)
        self._clock = clock if clock is not None else _default_clock_ms
        self._clock_diff = clock_diff if clock_diff is not None else _default_clock_diff
        self._pin_factory = pin_factory

        # 限位開關惰性建立（首次讀取才碰 machine，方便 PC 測試注入）
        self._extend_pin = None
        self._retract_pin = None

    def _pin(self, which):
        n = self.extend_pin_no if which == "extend" else self.retract_pin_no
        if self._pin_factory is not None:
            return self._pin_factory(n)
        if not _HAS_MACHINE:
            raise RuntimeError(
                "MotorCalibrator: 需要 machine 模組（裝置上）或注入 pin_factory")
        return machine.Pin(n, machine.Pin.IN, machine.Pin.PULL_UP)

    def _triggered(self, which):
        if which == "extend":
            if self._extend_pin is None:
                self._extend_pin = self._pin("extend")
            pin = self._extend_pin
        else:
            if self._retract_pin is None:
                self._retract_pin = self._pin("retract")
            pin = self._retract_pin
        return pin.value() == self.active_level

    def _measure(self, byte, which):
        """發 byte，busy-poll 對應限位開關直到觸發或超時。

        回傳經過 ms；超時回傳 None（該速度在此方向為死區）。
        """
        self.motor.send(self.address, byte)
        t0 = self._clock()
        while not self._triggered(which):
            if self._clock_diff(self._clock(), t0) >= self.timeout_ms:
                self.motor.send(self.address, STOP)
                return None
        self.motor.send(self.address, STOP)
        return self._clock_diff(self._clock(), t0)

    def _home(self):
        """全速縮回到底，對齊量測起點（全速假設一定能動）。"""
        self._measure(speed_to_byte(SPEED_MAX, -1), "retract")

    def run(self, speeds):
        """逐個速度點量測，回傳 [{speed, forward_ms, reverse_ms}, ...]。"""
        results = []
        for speed in speeds:
            self._home()
            fwd = self._measure(speed_to_byte(speed, 1), "extend")
            if fwd is None:
                rev = None          # 起點沒動 → 反向行程不可量
            else:
                rev = self._measure(speed_to_byte(speed, -1), "retract")
            results.append({"speed": int(speed),
                            "forward_ms": fwd,
                            "reverse_ms": rev})
        return results

    def save(self, results, out_dir):
        """把 run() 的結果寫成 JSON（每速度一檔 speed_XXX.json，含 address）。

        JSON 欄位：{"address": N, "speed": S, "forward_ms": T|null, "reverse_ms": T|null}
        """
        try:
            os.mkdir(out_dir)
        except OSError:
            pass
        for r in results:
            d = dict(r)
            d["address"] = self.address
            path = "{}/speed_{:03d}.json".format(out_dir.rstrip("/"), r["speed"])
            with open(path, "w") as f:
                _json.dump(d, f)
        return [r["speed"] for r in results]


# === 線性分析 ===
_LINEAR_TOL_PCT = 15   # 等效全速時間最大偏差 ≤ 15% 視為線性


def analyze(results):
    """判斷量測結果「速度 vs 全程時間」是否線性。

    原理：若線性（速率 ∝ speed），則「等效全速時間」equiv_full = ms × speed / 128
    在每一點應為同一常數。各點 equiv_full 愈接近 → 線性愈好。

    回傳 list of dict：
      {"direction": "forward"/"reverse",
       "points": [(speed, ms, equiv_full), ...],       # 依 speed 升冪，只含有值點
       "verdict": "linear"/"nonlinear"/"insufficient"/"dead",
       "spread_pct": 最大最小 equiv_full 的相對偏差%}
    """
    out = []
    for label, key in (("forward", "forward_ms"), ("reverse", "reverse_ms")):
        pts = sorted((int(r["speed"]), int(r[key]))
                     for r in results if r.get(key) is not None)
        if not pts:
            out.append({"direction": label, "points": [],
                        "verdict": "dead", "spread_pct": 0})
            continue
        if len(pts) == 1:
            out.append({"direction": label,
                        "points": [(s, ms, ms * s // SPEED_MAX) for s, ms in pts],
                        "verdict": "insufficient", "spread_pct": 0})
            continue
        eq = [(s, ms, ms * s // SPEED_MAX) for s, ms in pts]
        vals = [e for _, _, e in eq]
        lo, hi = min(vals), max(vals)
        spread = (hi - lo) * 100 // hi if hi else 0
        verdict = "linear" if spread <= _LINEAR_TOL_PCT else "nonlinear"
        out.append({"direction": label, "points": eq,
                    "verdict": verdict, "spread_pct": spread})
    return out


def report(results):
    """把 analyze() 的結論印成可讀報表（含「是否線性」）。回傳 analyze 結果。"""
    a = analyze(results)
    print("=== 校準線性報告 ===")
    for d in a:
        print("[{}]".format(d["direction"]))
        if d["verdict"] == "dead":
            print("  無有效數據（此方向全部死區）")
            continue
        for s, ms, eq in d["points"]:
            print("  speed={:3d}  全程={:6d}ms  等效全速={:6d}ms".format(s, ms, eq))
        if d["verdict"] == "linear":
            print("  判定：線性良好（等效全速一致，偏差 {}%）".format(d["spread_pct"]))
        elif d["verdict"] == "nonlinear":
            print("  判定：非線性（等效全速不一致，偏差 {}%；建議保留分段表）".format(d["spread_pct"]))
        else:
            print("  判定：數據不足（僅一點，無法判線性）")
    return a
