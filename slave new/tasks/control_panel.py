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
_EX_IC_SLOT_KEY = "_ex_ic_slot"
_EX_IC_PENDING_KEY = "_ex_ic_pending"
_UART_SOF = 0xB4
_UART_EOF = 0xFF
_ENC_DELTA_KEY = "_enc_delta"
_ENC_EVENT_TYPE = 0xFE
_ENC_EVENT_LABEL = b"enc_delta"

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


def _format_mode_bits(mode):
    return "{:08b}".format(mode & 0xFF)


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

    def _send_encoder_delta(self, delta):
        """ESP-NOW 發送編碼器增量事件，value 以 u16 裝載 (+1 / 0xFFFF[-1])"""
        if self._now_bus is None:
            return
        encoded = delta & 0xFFFF
        payload = struct.pack("<BB", _ENC_EVENT_TYPE, 0)
        payload += struct.pack("<H", len(_ENC_EVENT_LABEL)) + _ENC_EVENT_LABEL
        payload += struct.pack("<H", encoded)
        self._now_bus.broadcast(Proto.pack(CMD_HW, payload))

    def _poll_ex_ic(self):
        if not bus.shared.get(_EX_IC_PENDING_KEY):
            return

        event = bus.shared.get(_EX_IC_SLOT_KEY) or {}
        chip_type = int(event.get("chip_type", -1) or -1)
        chip_id = int(event.get("chip_id", -1) or -1)
        data = event.get("data", b"") or b""
        if isinstance(data, memoryview):
            data = bytes(data)
        elif not isinstance(data, (bytes, bytearray)):
            data = bytes(data)

        bus.shared[_EX_IC_PENDING_KEY] = 0

        if len(data) != 5 or data[0] != _UART_SOF or data[4] != _UART_EOF:
            get_log().info("[CP][RX][0x1403][DROP] chip={} id={} len={}".format(
                chip_type, chip_id, len(data)))
            return

        mode = data[1]
        brightness = data[2]
        time_remaining = data[3]
        bus.shared["_display_mode"] = mode
        bus.shared["_display_brightness"] = brightness
        bus.shared["_display_time"] = time_remaining
        get_log().info("[CP][RX][0x1403] chip={} id={} mod={} bit={} bri={} time={}".format(
            chip_type,
            chip_id,
            mode & 0x3F,
            _format_mode_bits(mode),
            brightness,
            time_remaining))

    def loop(self):
        if not self.running:
            return

        now = time.ticks_ms()
        self._poll_ex_ic()

        pos = self._enc.value()
        if pos != self._enc_last:
            step = 1 if pos > self._enc_last else -1
            self._enc_last = pos
            self._lw_ex(0, pos)
            cur = int(bus.shared.get(_ENC_DELTA_KEY, 0) or 0)
            bus.shared[_ENC_DELTA_KEY] = cur + step
            self._send_encoder_delta(step)
            get_log().immediate("[CP] enc_delta={:+d} pos={}".format(step, pos))
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
