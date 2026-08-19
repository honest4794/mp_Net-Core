"""
uart_drv.py — UART / RS485 管理

設定來源: bus.shared["UART"]  ({enable, list})
產物:    bus.register_service("uart_list", [UART_obj, ...])

RS485 方向腳:
  list 項目可加 "GPIO": {"en": <gpio>} 指定方向控制腳 (DE+RE)。
  不填 en、或 en = -1 → 純 UART，行為與原本完全一致。
  有 en 時會包成 _Rs485Uart：write() 自動拉起 en → 等真正送完(txdone) → 放低回接收，
  對上層 (CircuitBus / action_task / uart_motor) 完全透明，仍是 readinto/read/write 介面。
"""
from machine import UART, Pin
from lib.sys_bus import bus
from lib.log_service import get_log
import time


class _Rs485Uart:
    """RS485 半雙工薄包裝：DE 腳自動切換，對外介面與 machine.UART 一致。"""

    def __init__(self, uart, en_pin, baudrate):
        self.io = uart
        self.en = en_pin
        self.baud = int(baudrate)
        self.en.value(0)                       # 閒置 = 接收

    def _wait_sent(self, nbytes):
        """等資料真正離開 shift register，再放低 DE（避免截斷尾 byte）。"""
        if hasattr(self.io, "txdone"):         # ESP32：非阻塞查詢，每 ~1ms 回來看
            try:
                while not self.io.txdone():
                    time.sleep_ms(0)
                return
            except Exception:
                pass
        # 無 txdone 的板子：用波特率估算傳輸時間
        time.sleep_ms(max(1, (nbytes + 4) * 10 * 1000 // self.baud + 2))

    def write(self, data):
        self.en.value(1)                       # 轉發送
        try:
            n = self.io.write(data)
            self._wait_sent(len(data) if (n is None or n <= 0) else n)
            return n
        finally:
            self.en.value(0)                   # 送完才回接收

    def readinto(self, buf):
        return self.io.readinto(buf)

    def read(self, n=-1):
        return self.io.read(n)

    def any(self):
        return self.io.any()


def init_uart(sysbus=None):
    sysbus = sysbus or bus
    cfg = sysbus.shared.get("UART") or {}
    if not cfg.get("enable"):
        return []

    uart_list = []
    for item in cfg.get("list", []):
        gpio = item.get("GPIO", {})
        uart = UART(
            item.get("id", 1),
            baudrate=item.get("baudrate", 115200),
            tx=Pin(gpio["tx"]) if gpio.get("tx") is not None else None,
            rx=Pin(gpio["rx"]) if gpio.get("rx") is not None else None,
        )

        en = gpio.get("en", -1)
        if en is not None and int(en) >= 0:
            uart = _Rs485Uart(uart, Pin(int(en), Pin.OUT, value=0), item.get("baudrate", 115200))

        uart_list.append(uart)

    sysbus.register_service("uart_list", uart_list)
    get_log().info("UART: {} port(s)".format(len(uart_list)))
    return uart_list


def gpios(sysbus=None):
    sysbus = sysbus or bus
    cfg = sysbus.shared.get("UART") or {}
    if not cfg.get("enable"):
        return {}

    result = {}
    for item in cfg.get("list", []):
        gpio = item.get("GPIO", {})
        uid = item.get("id", "?")
        for name in ("tx", "rx", "en"):
            pin = gpio.get(name)
            if pin is not None and int(pin) >= 0:
                result[pin] = "uart{}_{}".format(uid, name)
    return result
