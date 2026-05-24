"""
控制面板 Task — 編碼器 + 按鈕 → ESP-NOW  v3

硬體 (config.json PIN.list, boot 時 init_pin() 建立):
  btn  = GPIO 40
  encC = GPIO 17 (編碼器按鈕)
  encA = GPIO 18
  encB = GPIO  8
"""

import time
from machine import Encoder
from lib.task import Task
from lib.sys_bus import bus
from lib.hw_manager import _PIN_CACHE
from lib.log_service import get_log


def _find_pin_obj(label, gpio_fallback=0):
    plist = bus.get_service("pin_list")
    if plist:
        cfg = bus.shared.get("PIN") or {}
        lst = cfg.get("list") or []
        for i, item in enumerate(lst):
            if isinstance(item, dict) and item.get("label") == label:
                if i < len(plist):
                    return plist[i]
    gpio = gpio_fallback
    cfg = bus.shared.get("PIN") or {}
    lst = cfg.get("list") or []
    for item in lst:
        if isinstance(item, dict) and item.get("label") == label:
            gpio = int(item.get("GPIO", gpio_fallback))
            break
    if gpio in _PIN_CACHE:
        return _PIN_CACHE[gpio]
    from machine import Pin
    return Pin(gpio, Pin.IN, Pin.PULL_UP)


def _label_gpio(label):
    cfg = bus.shared.get("PIN") or {}
    lst = cfg.get("list") or []
    for item in lst:
        if isinstance(item, dict) and item.get("label") == label:
            return item.get("GPIO", "?")
    return "?"


class ControlPanelTask(Task):
    log_schema = ["enc_pos"]

    def __init__(self, name, ctx):
        super().__init__(name, ctx)
        self._now_bus = None
        self._btns = []
        self._enc = None
        self._enc_last = 0
        self._diag_ts = 0

    def on_start(self):
        super().on_start()

        btn1 = _find_pin_obj("btn", 40)
        btn2 = _find_pin_obj("encC", 17)
        self._btns.append([btn1, btn1.value(), "btn", 0])
        self._btns.append([btn2, btn2.value(), "encC", 0])

        pin_a = _find_pin_obj("encA", 18)
        pin_b = _find_pin_obj("encB", 8)
        self._enc = Encoder(0, pin_a, pin_b)
        self._enc_last = self._enc.value()

        self._now_bus = bus.get_service("NowBus")
        get_log().info("[CP v3] enc={},{} btn={} encC={}".format(
            _label_gpio("encA"), _label_gpio("encB"),
            _label_gpio("btn"), _label_gpio("encC")))

    def _read_buttons(self, now):
        triggered = []
        for entry in self._btns:
            pin, stable, label, ts = entry
            raw = pin.value()
            if raw != stable:
                if time.ticks_diff(now, ts) >= 30:
                    entry[1] = raw
                    entry[3] = now
                    if raw == 0:
                        triggered.append(label)
            else:
                entry[3] = now
        return triggered

    def loop(self):
        if not self.running:
            return

        now = time.ticks_ms()

        if time.ticks_diff(now, self._diag_ts) > 500:
            self._diag_ts = now
            raw1 = self._btns[0][0].value() if self._btns else -1
            raw2 = self._btns[1][0].value() if len(self._btns) > 1 else -1
            get_log().info("[CP] enc={} btn={} encC={}".format(
                self._enc.value(), raw1, raw2))

        pos = self._enc.value()
        if pos != self._enc_last:
            self._enc_last = pos
            self._lw_ex(0, pos)
            self.success += 1

        for label in self._read_buttons(now):
            get_log().immediate("[CP] {} PRESS enc={}".format(
                label, self._enc.value()))
            if self._now_bus:
                self._now_bus.broadcast(bytes([self._enc.value() & 0xFF]))
            self.success += 1
