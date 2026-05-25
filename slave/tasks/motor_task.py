"""
馬達控制 Task — 接收 HW_CTL label 事件，控制電機

接線:
  m1 = GPIO 8  (IN1)
  m2 = GPIO 9  (IN2)
  EN = PWM[0]

運作:
  從 bus.shared["hw_events"] 取得 label 事件
  btn 按下 → stop→fwd→rev 循環
"""

import time
from machine import Pin, PWM
from lib.task import Task
from lib.sys_bus import bus
from lib.hw_manager import _PIN_CACHE
from lib.log_service import get_log

PIN_M1 = 8
PIN_M2 = 9
PWM_EN = 0
PWM_FREQ = 1000
PWM_DUTY = 512


def _ensure_output(gpio):
    if gpio not in _PIN_CACHE:
        _PIN_CACHE[gpio] = Pin(gpio, Pin.OUT, value=0)
    else:
        p = _PIN_CACHE[gpio]
        try:
            p.init(Pin.OUT, value=0)
        except Exception:
            _PIN_CACHE[gpio] = Pin(gpio, Pin.OUT, value=0)
    return _PIN_CACHE[gpio]


class MotorTask(Task):
    def __init__(self, name, ctx):
        super().__init__(name, ctx)
        self._m1 = None
        self._m2 = None
        self._en = None
        self._state = 0

    def on_start(self):
        super().on_start()
        self._m1 = _ensure_output(PIN_M1)
        self._m2 = _ensure_output(PIN_M2)
        pwm_list = bus.get_service("pwm_list")
        if pwm_list and len(pwm_list) > PWM_EN:
            self._en = pwm_list[PWM_EN]
            self._en.freq(PWM_FREQ)
        get_log().info("[Motor] m1={} m2={} en={}".format(PIN_M1, PIN_M2, PWM_EN))

    def _stop(self):
        self._m1.value(0); self._m2.value(0)
        if self._en: self._en.duty(0)
        get_log().info("[Motor] stop")

    def _fwd(self):
        self._m1.value(0); self._m2.value(1)
        if self._en: self._en.duty(PWM_DUTY)
        get_log().info("[Motor] forward")

    def _rev(self):
        self._m1.value(1); self._m2.value(0)
        if self._en: self._en.duty(PWM_DUTY)
        get_log().info("[Motor] reverse")

    def loop(self):
        if not self.running:
            return
        ev = bus.shared.pop("hw_events", None)
        if ev is None:
            return
        label = ev.get("label", "")
        value = ev.get("value", 0)
        if label == "btn" and value == 0:
            self._state = (self._state + 1) % 3
            if self._state == 0:
                self._stop()
            elif self._state == 1:
                self._fwd()
            else:
                self._rev()
            self.success += 1
