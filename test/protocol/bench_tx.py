# -*- coding: utf-8 -*-
"""NC4 性能測試發送端（RS485 半雙工，自包含）

配合 slave 的 bench 模組（schema/bench.json + action/bench_actions.py）。
接收端 slave 開機即監聽 BENCH_READY / BENCH_DATA / BENCH_RESULT。

半雙工核心原則：
  - 發送端「不斷讀」：主迴圈每次迭代都讀 UART，把 byte 餵給 parser
  - 發送前讀一次：確保沒有漏掉的 REPORT
  - 發送後繼續讀：等 REPORT 回來
  - 不用 _wait_bus_quiet（那會把 REPORT 讀掉丟棄）

測試流程（三段式）：
  1. 發 BENCH_READY (0x1811) → 等 BENCH_REPORT {ok:0} 確認計數器已空
  2. 連續發 BENCH_DATA (0x1812) x COUNT
  3. 發 BENCH_RESULT (0x1813) → 等 BENCH_REPORT {ok:N}
  4. 印統計：sent=N  ok=N  lost=N-ok

自包含：只 import machine/time/ubinascii，不 import 任何專案模組。

接線（兩塊板各接一顆 RS485 收發器）：
  GPIO8 = TX → DI、GPIO9 = RX ← RO、GPIO7 = EN → DE+RE
  A-A、B-B、GND 共地。

部署：本檔改名 main.py 丟發送端根目錄 → 開機自動跑；或 REPL exec。
"""

import time
from machine import UART, Pin

try:
    import ubinascii as binascii
except ImportError:
    import binascii

# ── 配置 ──
BAUD = 9600                    # 與接收端一致
TX, RX, EN = 8, 9, 7           # DI, RO, DE+RE
UART_ID = 1
DATA_SIZE = 256                # 測試包 Data 內容（NC4 payload）
COUNT = 10                     # 每輪發幾個測試包
REPORT_TIMEOUT_MS = 800        # 等 REPORT 上限

# 指令碼（對齊 slave/schema/bench.json）
CMD_READY = 0x1811
CMD_DATA = 0x1812
CMD_RESULT = 0x1813
CMD_REPORT = 0x1814

_SOF = b"NC"
_VER = 4
_ADDR = 0xFFFF


# ── NC4 pack（對齊 lib/proto.py::Proto.pack） ──
def nc4_pack(cmd, payload=b"", addr=_ADDR):
    ln = len(payload)
    total = 9 + ln + 4
    buf = bytearray(total)
    buf[0] = 0x4E   # 'N'
    buf[1] = 0x43   # 'C'
    buf[2] = _VER
    buf[3] = addr & 0xFF
    buf[4] = (addr >> 8) & 0xFF
    buf[5] = cmd & 0xFF
    buf[6] = (cmd >> 8) & 0xFF
    buf[7] = ln & 0xFF
    buf[8] = (ln >> 8) & 0xFF
    if ln:
        buf[9:9 + ln] = payload
    crc = binascii.crc32(buf[2:9 + ln], 0) & 0xFFFFFFFF
    buf[9 + ln] = crc & 0xFF
    buf[9 + ln + 1] = (crc >> 8) & 0xFF
    buf[9 + ln + 2] = (crc >> 16) & 0xFF
    buf[9 + ln + 3] = (crc >> 24) & 0xFF
    return bytes(buf)


# ── 簡化 NC4 parser（head 指標，不用 del） ──
class _NC4Parser:
    def __init__(self, cap=256):
        self.buf = bytearray(cap)
        self.n = 0
        self.head = 0

    def feed(self, data):
        ln = len(data)
        if ln <= 0:
            return
        if self.n + ln > len(self.buf):
            self._compact()
            if self.n + ln > len(self.buf):
                self.buf = bytearray(max(len(self.buf) * 2, self.n + ln))
        self.buf[self.n:self.n + ln] = data
        self.n += ln

    def _compact(self):
        if self.head <= 0:
            return
        m = self.n - self.head
        if m > 0:
            self.buf[:m] = self.buf[self.head:self.n]
        self.n = m
        self.head = 0

    def next(self):
        """回傳 (cmd, payload) 或 None。CRC 錯/失步自動重同步。"""
        while True:
            if self.n - self.head < 9:
                self._compact()
                return None
            idx = self.head
            while idx + 1 < self.n and not (self.buf[idx] == 0x4E and self.buf[idx + 1] == 0x43):
                idx += 1
            if idx + 1 >= self.n:
                self.head = max(self.n - 1, 0) if self.n >= 1 else 0
                self._compact()
                return None
            self.head = idx
            if self.n - self.head < 9:
                self._compact()
                return None
            if self.buf[self.head + 2] != _VER:
                self.head += 1
                continue
            cmd = self.buf[self.head + 5] | (self.buf[self.head + 6] << 8)
            ln = self.buf[self.head + 7] | (self.buf[self.head + 8] << 8)
            total = 9 + ln + 4
            if self.n - self.head < total:
                self._compact()
                return None
            crc_calc = binascii.crc32(self.buf[self.head + 2:self.head + 9 + ln], 0) & 0xFFFFFFFF
            crc_recv = (self.buf[self.head + 9 + ln] | (self.buf[self.head + 9 + ln + 1] << 8)
                        | (self.buf[self.head + 9 + ln + 2] << 16)
                        | (self.buf[self.head + 9 + ln + 3] << 24))
            if crc_calc != crc_recv:
                self.head += 1
                continue
            payload = bytes(self.buf[self.head + 9:self.head + 9 + ln])
            self.head += total
            self._compact()
            return cmd, payload


def _ticks_ms():
    return time.ticks_ms() if hasattr(time, "ticks_ms") else int(time.time() * 1000)


def _ticks_diff(a, b):
    return time.ticks_diff(a, b) if hasattr(time, "ticks_diff") else a - b


def _sleep_ms(ms):
    if hasattr(time, "sleep_ms"):
        time.sleep_ms(ms)
    else:
        time.sleep(ms / 1000.0)


def _byte_ms(baud):
    return max(1, (10 * 1000) // int(baud))


# ═══════════════════════════════════════════════════════════════
#  核心：不斷讀 + 發送前讀一次
# ═══════════════════════════════════════════════════════════════

def _poll_rx(uart, parser, rxbuf):
    """讀一次 UART，把 byte 餵給 parser。回傳讀到的 byte 數。
    debug=True 時印出原始 byte，讓你親眼看到發送端到底收沒收到東西。"""
    n = 0
    try:
        n = uart.any()
    except Exception:
        n = 0
    if n and n > 0:
        try:
            got = uart.read(n)
        except Exception:
            got = None
        if got:
            print("    [RX] {}B hex={}".format(
                len(got), " ".join("{:02X}".format(b) for b in got[:32])))
            parser.feed(got)
            return len(got)
    return 0


def _wait_report(uart, parser, rxbuf, timeout_ms):
    """不斷讀直到 parser 解出 REPORT，回傳 ok 值；逾時回 None。"""
    t0 = _ticks_ms()
    while _ticks_diff(_ticks_ms(), t0) < int(timeout_ms):
        _poll_rx(uart, parser, rxbuf)
        r = parser.next()
        while r is not None:
            cmd, payload = r
            if cmd == CMD_REPORT and len(payload) >= 4:
                return payload[0] | (payload[1] << 8) | (payload[2] << 16) | (payload[3] << 24)
            r = parser.next()
        _sleep_ms(1)
    return None


def _send(uart, en, data, baud):
    """RS485 半雙工發送：DE 高 → 10ms 使能 → 寫 → 精確傳輸時間 + 4ms 餘量 → DE 低。
    10ms 使能經實測掃描（20→2ms）：8ms 以上全通、6ms 以下 READY 回覆開始丟。
    取 10ms 為安全值（比 20ms 快，留 2ms 餘量）。回傳實際寫入 byte 數。"""
    ln = len(data)
    en.value(1)
    time.sleep_ms(10)                      # 驅動器使能穩定（掃描 20→2ms，10ms 安全）
    try:
        uart.write(data)
        # 精確傳輸時間 + 4ms 餘量（不用 txdone）
        time.sleep_ms(max(4, (ln + 6) * 10 * 1000 // int(baud) + 4))
        return ln
    finally:
        en.value(0)                        # 送完立即回接收
        # 清掉發送期間 RX 腳浮空採樣到的回音垃圾，讓後續 _poll_rx 能乾淨地收 REPORT
        try:
            while uart.any():
                uart.read(uart.any())
        except Exception:
            pass


def run(baud=BAUD, count=COUNT, data_size=DATA_SIZE,
        tx=TX, rx=RX, en=EN, uart_id=UART_ID):
    uart = UART(int(uart_id), baudrate=int(baud), tx=Pin(int(tx)), rx=Pin(int(rx)))
    en_pin = Pin(int(en), Pin.OUT, value=0)
    en_pin.value(0)                    # 閒置 = 接收

    parser = _NC4Parser()
    rxbuf = bytearray(256)
    data = bytearray(data_size)
    for i in range(data_size):
        data[i] = i & 0xFF

    print("=" * 62)
    print("NC4 BENCH 發送端 (baud={} tx={} rx={} en={})".format(baud, tx, rx, en))
    print("每輪: READY → DATA x{} ({}B) → RESULT → 統計".format(count, data_size))
    print("=" * 62)

    while True:
        # ── 1) READY ──
        _poll_rx(uart, parser, rxbuf)          # 發送前讀一次
        ready_pkt = nc4_pack(CMD_READY)
        rw = _send(uart, en_pin, ready_pkt, baud)
        print("\n-- 新一輪 --")
        print("READY 送出 {} / {} bytes {}".format(
            rw, len(ready_pkt), "✓" if rw == len(ready_pkt) else "⚠️"))
        ok0 = _wait_report(uart, parser, rxbuf, REPORT_TIMEOUT_MS)
        print("READY 回報 ok={} {}".format(
            ok0 if ok0 is not None else "?", "✓ 計數器已空" if ok0 == 0 else "⚠️ 無回覆/非空"))

        # ── 2) DATA x COUNT ──
        t0 = _ticks_ms()
        failed = 0
        for i in range(int(count)):
            _poll_rx(uart, parser, rxbuf)      # 每筆發送前讀一次
            pkt = nc4_pack(CMD_DATA, data)
            w = _send(uart, en_pin, pkt, baud)
            if w != len(pkt):
                failed += 1
                if failed <= 3:
                    print("  DATA[{}] 送出 {}/{} bytes ⚠️".format(i, w, len(pkt)))
        tx_ms = _ticks_diff(_ticks_ms(), t0)
        print("DATA x{} 送出完成，{} 筆未完整送出，耗時 {}ms".format(count, failed, tx_ms))

        # ── 3) RESULT ──
        _poll_rx(uart, parser, rxbuf)          # 發送前讀一次
        result_pkt = nc4_pack(CMD_RESULT)
        rw = _send(uart, en_pin, result_pkt, baud)
        print("RESULT 送出 {} / {} bytes {}".format(
            rw, len(result_pkt), "✓" if rw == len(result_pkt) else "⚠️"))
        ok = _wait_report(uart, parser, rxbuf, REPORT_TIMEOUT_MS)

        # ── 4) 統計 ──
        if ok is None:
            print("RESULT 回報逾時（{}ms）→ 接收端可能未收到/未回覆".format(REPORT_TIMEOUT_MS))
            ok = 0
        sent = int(count)
        lost = sent - ok
        print("sent={}  ok={}  lost={}".format(sent, ok, lost))
        if sent > 0 and tx_ms > 0:
            thr_bps = (sent * data_size * 8 * 1000) // tx_ms
            print("有效吞吐 ~{} bit/s ({:.1f} KB/s)".format(thr_bps, thr_bps / 8192))

        _sleep_ms(500)


run()
