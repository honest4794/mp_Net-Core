"""
控制面板 Task — 編碼器 + 按鈕 → ESP-NOW (HW_CTL)

只報告用戶操作 (id = config PIN.list 索引):
  btn  按下 → broadcast HW_CTL(0x1401) type=PIN id=0    value=0
  encC 按下 → broadcast HW_CTL(0x1401) type=0xFF id=0  value=encoder
"""

import time, struct
from machine import Encoder
from lib.task import Task
from lib.sys_bus import bus
from lib.hw_manager import _PIN_CACHE
from lib.proto import Proto
from lib.log_service import get_log

CMD_HW = 0x1401


def _find_pin_obj(label, fallback=0):
    plist = bus.get_service("pin_list")
    if plist:
        cfg = bus.shared.get("PIN") or {}
        lst = cfg.get("list") or []
        for i, item in enumerate(lst):
            if isinstance(item, dict) and item.get("label") == label:
                if i < len(plist):
                    return plist[i]
    gpio = fallback
    cfg = bus.shared.get("PIN") or {}
    lst = cfg.get("list") or []
    for item in lst:
        if isinstance(item, dict) and item.get("label") == label:
            gpio = int(item.get("GPIO", fallback))
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
        get_log().info("[CP] encA={} encB={} btn={} encC={}".format(
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

    def _hwctl(self, hw_type, hw_id, value):
        if self._now_bus is None:
            return
        payload = struct.pack("<BBH", hw_type, hw_id, value)
        self._now_bus.broadcast(Proto.pack(CMD_HW, payload))

    def loop(self):
        if not self.running:
            return

        now = time.ticks_ms()

        pos = self._enc.value()
        if pos != self._enc_last:
            self._enc_last = pos
            self._lw_ex(0, pos)
            self.success += 1

        for label in self._read_buttons(now):
            if label == "btn":
                self._hwctl(0, 0, 0)    # type=PIN, id=0 (btn = list[0])
                get_log().immediate("[CP] btn")
            elif label == "encC":
                val = self._enc.value() & 0xFFFF
                self._hwctl(0xFF, 0, val)
                get_log().immediate("[CP] encC {}".format(self._enc.value()))
            self.success += 1
