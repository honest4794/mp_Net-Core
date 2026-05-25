"""
action_task_1.py — 綜合動作控制任務

三階段馬達控制:
  RISE (升高) → 正轉
  WAIT (等待) → 停止
  FALL (下降) → 反轉

觸發: 從 bus.shared["_vbtn1_event"] 讀取虛擬按鈕旗標 (hw_actions 寫入)
  v[1]==1:
    空閒(IDLE)       → 啟動 RISE 階段
    升高/等待中        → 提早跳到 FALL 階段

可設定參數 (bus.shared):
  _motor_rise_ms  (預設 5000)
  _motor_wait_ms  (預設 500)
  _motor_fall_ms  (預設 5000)
"""

import time
from lib.task import Task
from lib.sys_bus import bus
from lib.hw_manager import HW, _PIN_CACHE
from lib.log_service import get_log

# ═══ 腳位解析 ═══

def _resolve_pin(gpio_or_label):
    from machine import Pin
    if isinstance(gpio_or_label, str):
        cfg = bus.shared.get("PIN") or {}
        lst = cfg.get("list") or []
        for item in lst:
            if isinstance(item, dict) and item.get("label") == gpio_or_label:
                gpio_num = int(item.get("GPIO", 0))
                if gpio_num in _PIN_CACHE:
                    return _PIN_CACHE[gpio_num]
                return Pin(gpio_num, Pin.OUT)
        return None
    gpio = int(gpio_or_label)
    if gpio in _PIN_CACHE:
        return _PIN_CACHE[gpio]
    p = Pin(gpio, Pin.OUT)
    _PIN_CACHE[gpio] = p
    return p


# ═══ 常數 ═══

STATE_IDLE = 0
STATE_RISE = 1
STATE_WAIT = 2
STATE_FALL = 3

_DEFAULT_RISE_MS = 5000
_DEFAULT_WAIT_MS = 500
_DEFAULT_FALL_MS = 5000


def _read_cfg(key, default):
    v = bus.shared.get(key)
    return int(v) if v is not None else default


# 馬達腳位預設 GPIO（label 找不到時的回落）
_MOTOR_DEFAULT_PINS = {
    "m1":   8,
    "m2":   9,
    "m_en": 10,
}


def _resolve_pin_or(label, fallback_gpio):
    """按 label 解析 pin，找不到則用 fallback GPIO"""
    p = _resolve_pin(label)
    if p is not None:
        return p
    return _resolve_pin(fallback_gpio)


# ═══ ActionTask1 ═══

class ActionTask1(Task):
    def __init__(self, name, ctx):
        super().__init__(name, ctx)
        self._m1 = None
        self._m2 = None
        self._m_en = None
        self._state = STATE_IDLE
        self._deadline = 0
        self._rise_ms = _DEFAULT_RISE_MS
        self._wait_ms = _DEFAULT_WAIT_MS
        self._fall_ms = _DEFAULT_FALL_MS

    def on_start(self):
        super().on_start()

        self._rise_ms = _read_cfg("_motor_rise_ms", _DEFAULT_RISE_MS)
        self._wait_ms = _read_cfg("_motor_wait_ms", _DEFAULT_WAIT_MS)
        self._fall_ms = _read_cfg("_motor_fall_ms", _DEFAULT_FALL_MS)

        self._m1   = _resolve_pin_or("m1",   _MOTOR_DEFAULT_PINS["m1"])
        self._m2   = _resolve_pin_or("m2",   _MOTOR_DEFAULT_PINS["m2"])
        self._m_en = _resolve_pin_or("m_en", _MOTOR_DEFAULT_PINS["m_en"])
        self._enter(STATE_IDLE)

        get_log().info(
            "[Motor] rise={} wait={} fall={}ms".format(
                self._rise_ms, self._wait_ms, self._fall_ms))

    # ═══ 階段切換 ═══

    def _enter(self, state):
        self._state = state
        now = time.ticks_ms()

        if state == STATE_IDLE:
            self._motor_stop()
            self._deadline = 0
            HW.set(HW.VBTN, 1, 0)
        elif state == STATE_RISE:
            self._motor_fwd()
            self._deadline = time.ticks_add(now, self._rise_ms)
        elif state == STATE_WAIT:
            self._motor_stop()
            self._deadline = time.ticks_add(now, self._wait_ms)
        elif state == STATE_FALL:
            self._motor_rev()
            self._deadline = time.ticks_add(now, self._fall_ms)

    # ═══ 馬達控制 ═══

    def _motor_stop(self):
        if self._m1: self._m1.value(0)
        if self._m2: self._m2.value(0)
        if self._m_en: self._m_en.value(0)

    def _motor_fwd(self):
        if self._m1: self._m1.value(0)
        if self._m2: self._m2.value(1)
        if self._m_en: self._m_en.value(1)

    def _motor_rev(self):
        if self._m1: self._m1.value(1)
        if self._m2: self._m2.value(0)
        if self._m_en: self._m_en.value(1)

    # ═══ 主迴圈 ═══

    def loop(self):
        if not self.running:
            return
        now = time.ticks_ms()

        # ── 計時: 階段到期 → 下一階段 ──
        if self._state != STATE_IDLE and self._deadline > 0:
            if time.ticks_diff(now, self._deadline) >= 0:
                if self._state == STATE_RISE:
                    self._enter(STATE_WAIT)
                elif self._state == STATE_WAIT:
                    self._enter(STATE_FALL)
                elif self._state == STATE_FALL:
                    self._enter(STATE_IDLE)
                self.success += 1

        # ── 虛擬按鈕旗標 (hw_actions 接收端寫入) ──
        v = bus.shared.pop("_vbtn1_event", None)
        if v is not None and v == 1:
            self._on_vbtn1(now)

    def _on_vbtn1(self, now):
        """VBTN[1] 按下"""
        if self._state == STATE_IDLE:
            self._enter(STATE_RISE)
        elif self._state in (STATE_RISE, STATE_WAIT):
            self._enter(STATE_FALL)   # 提早下降
        self.success += 1

    def on_stop(self):
        self._motor_stop()
        self._deadline = 0
        super().on_stop()
