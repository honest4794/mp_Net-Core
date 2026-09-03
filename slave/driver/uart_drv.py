"""
uart_drv.py — UART / RS485 管理

設定來源: bus.shared["UART"]  ({enable, list})
產物:    bus.register_service("uart_list", [UART_obj, ...])

RS485 方向腳:
  list 項目可加 "GPIO": {"en": <gpio>} 指定方向控制腳 (DE+RE)。
  共用總線 sidecar 可加 "rx_only": 1：硬停 UART TX、EN 固定為
  "rx_en_level"（預設 0），所有 write 回報已消耗但不會驅動總線。
  可加 "en_settle_ms": <ms> 調整 DE 使能穩定時間（預設 1ms，實測 0ms 不穩、1ms 穩定）。
  不填 en、或 en = -1 → 純 UART，行為與原本完全一致。
  有 en 時會包成 _Rs485Uart：write() 自動拉起 en → 等真正送完(txdone) → 放低回接收，
  對上層 (CircuitBus / action_task / uart_motor) 完全透明，仍是 readinto/read/write 介面。
"""
from machine import UART, Pin
from lib.sys.sys_bus import bus
from lib.sys.log_service import get_log
import time


class _RxOnlyUart:
    """只收 UART：保留讀取介面，但永不驅動共用 RS485 總線。"""

    def __init__(self, uart, en_pin=None, en_level=0):
        self.io = uart
        self.en = en_pin
        self.en_level = 1 if int(en_level) else 0
        if self.en is not None:
            self.en.value(self.en_level)

    def write(self, data):
        # CircuitBus 會重試短寫；回報整段已消耗可抑制所有 reply/retry，
        # 而底層 UART 的 TX 已在建構時設為 -1，形成雙重保護。
        return len(data)

    def readinto(self, buf):
        return self.io.readinto(buf)

    def read(self, n=-1):
        return self.io.read(n)

    def any(self):
        return self.io.any()


class _Rs485Uart:
    """RS485 半雙工薄包裝：DE 腳自動切換，對外介面與 machine.UART 一致。

    方向控制與收發「同步」，不做盲延遲：
      1) 發送前 listen-before-talk：持續讀線路，確認總線已安靜才拉高 DE。
      2) 發送完成用 txdone() 等 FIFO 排空 + 再等最後 1 byte 離開 shift register，
         資料真正送完才放低 DE 回接收。
    """

    def __init__(self, uart, en_pin, baudrate, settle_ms=1):
        self.io = uart
        self.en = en_pin
        self.baud = int(baudrate)
        self.settle_ms = int(settle_ms)
        self.en.value(0)                       # 閒置 = 接收

    def _byte_ms(self):
        return max(1, (10 * 1000) // self.baud)

    def _wait_bus_quiet(self, quiet_ms=None):
        """Listen-before-talk：持續讀線路，連續 quiet_ms 無資料才視為總線空閒。
        期間收到的資料視為「別人在發 / 殘留」，讀掉不保留（不是給我的）。"""
        if quiet_ms is None:
            quiet_ms = max(2, 3 * self._byte_ms())
        deadline = time.ticks_add(time.ticks_ms(), quiet_ms)
        while True:
            n = 0
            try:
                n = self.io.any()
            except Exception:
                n = 0
            if n:
                try:
                    self.io.read(n)            # 讀掉線上的殘留/他方發送
                except Exception:
                    pass
                deadline = time.ticks_add(time.ticks_ms(), quiet_ms)
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                return
            time.sleep_ms(1)

    def _wait_sent(self, nbytes):
        """同步等資料真正離開 shift register：txdone() 等 FIFO 空，再等最後 1 byte。
        不依賴固定超時上限（那會在大幀還沒送完就誤判完成、截斷尾段）。"""
        if hasattr(self.io, "txdone"):
            try:
                while not self.io.txdone():
                    time.sleep_ms(0)
            except Exception:
                pass
        time.sleep_ms(self._byte_ms() + 1)

    def write(self, data):
        # 1) 發送前先聽線路：確認總線空閒才拉高 DE（避免撞上對端還在發）
        self._wait_bus_quiet()
        # 2) 拉高 DE 發送。DE settle 實測：0ms 不穩（start bit 會被吃）、1ms 穩定，
        #    預設 1ms；可用 config 的 en_settle_ms 調整。
        self.en.value(1)
        time.sleep_ms(self.settle_ms)
        try:
            n = self.io.write(data)
            # 3) 同步等送完，才放低 DE 回接收
            self._wait_sent(len(data) if (n is None or n <= 0) else n)
            return n
        finally:
            self.en.value(0)                   # 送完立即回接收

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
        rx_only = bool(item.get("rx_only", 0))
        # MicroPython 1.28 on ESP32-S3 rejects both None and -1 when they are
        # explicitly passed as UART pins.  Preserve TX-only/RX-only profiles
        # by omitting the unused keyword entirely.
        tx_pin = gpio.get("tx")
        rx_pin = gpio.get("rx")
        uart_kwargs = {
            "baudrate": item.get("baudrate", 115200),
            "rxbuf": item.get("rxbuf", 16384),  # ≥ 最大幀 8205B
            "txbuf": item.get("txbuf", 16384),  # ≥ 最大幀 8205B
        }
        if not rx_only and tx_pin is not None:
            uart_kwargs["tx"] = Pin(tx_pin)
        if rx_pin is not None:
            uart_kwargs["rx"] = Pin(rx_pin)
        uart = UART(item.get("id", 1), **uart_kwargs)

        en = gpio.get("en", -1)
        en_pin = None
        if en is not None and int(en) >= 0:
            en_pin = Pin(int(en), Pin.OUT, value=0)

        if rx_only:
            uart = _RxOnlyUart(
                uart,
                en_pin,
                en_level=item.get("rx_en_level", 0),
            )
        elif en_pin is not None:
            uart = _Rs485Uart(
                uart,
                en_pin,
                item.get("baudrate", 115200),
                settle_ms=item.get("en_settle_ms", 1),
            )

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
