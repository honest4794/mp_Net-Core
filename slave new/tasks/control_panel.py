"""
控制面板 Task — 編碼器 + 按鈕 → ESP-NOW + 虛擬按鈕

每組按鈕事件連續發送兩次 ESP-NOW:
  1. 真實按鈕: type=HW.PIN(0), id=0, label="btn"|"encC",  value=state
  2. 虛擬按鈕: type=HW.VBTN(8), id=vbtn_id, label="vbtn", value=state

同時寫入本地 HW.VBTN 緩衝。
"""

import time, struct
from machine import Encoder
from lib.task import Task
from lib.sys_bus import bus
from lib.hw_manager import HW, _PIN_CACHE
from lib.proto import Proto
from lib.log_service import get_log

CMD_HW = 0x1401

# 需要同步的實體按鈕: [(label, vbtn_id), ...]
_VBTN_SYNC = [
    ("btn",  0),
    ("encC", 1),
]


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
        for _, vbtn_id in _VBTN_SYNC:
            HW.set(HW.VBTN, vbtn_id, 1)
        for pin, stable, label, _ in self._btns:
            for sync_label, vbtn_id in _VBTN_SYNC:
                if label == sync_label:
                    HW.set(HW.VBTN, vbtn_id, stable)
                    self._send_vbtn(vbtn_id, stable)
                    break
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
                    triggered.append((label, raw))
            else:
                entry[3] = now
        return triggered

    def _send(self, label, state):
        """ESP-NOW 發送真實按鈕 (type=PIN, id=0, label="btn"|"encC")"""
        if self._now_bus is None:
            return
        lb = label.encode()
        payload = struct.pack("<BB", HW.PIN, 0)
        payload += struct.pack("<H", len(lb)) + lb
        payload += struct.pack("<H", state)
        self._now_bus.broadcast(Proto.pack(CMD_HW, payload))

    def _send_vbtn(self, vbtn_id, state):
        """ESP-NOW 發送虛擬按鈕 (type=VBTN, id=vbtn_id, label="vbtn")"""
        if self._now_bus is None:
            return
        label = b"vbtn"
        payload = struct.pack("<BB", HW.VBTN, vbtn_id)
        payload += struct.pack("<H", len(label)) + label
        payload += struct.pack("<H", state)
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

        for label, raw in self._read_buttons(now):
            # ── 第 1 次 ESP-NOW: 真實按鈕 ──
            self._send(label, raw)

            # ── 第 2 次 ESP-NOW + 本地緩衝: 虛擬按鈕 ──
            for sync_label, vbtn_id in _VBTN_SYNC:
                if label == sync_label:
                    self._send_vbtn(vbtn_id, raw)
                    HW.set(HW.VBTN, vbtn_id, raw)
                    # 同核旗標，供 action_task_1 即時讀取
                    if vbtn_id == 1:
                        bus.shared["_vbtn1_event"] = raw
                    break

            get_log().immediate("[CP] {}={}".format(label, raw))
            self.success += 1
