# -*- coding: utf-8 -*-
"""UART 交叉直連能力測試（GPIO9=TX, GPIO8=RX）— MicroPython agent（板端）

兩塊 ESP32-S3 用 UART1 直接交叉連線：A.TX(9) → B.RX(8)、B.TX(9) → A.RX(8)、GND 共地。
無 DE 腳（3.3V TTL 直連，全雙工）。

角色：
  SENDER   跑 run_sender(baud)：每個 baud 依序測三項
           1) pingpong  10B 幀 ×100，逐幀等 echo 驗證序號 → 正確性 + RTT 統計
           2) burst     10B 幀 ×300 流水線連發（邊發邊收）→ 小幀全雙工穩定性
           3) throughput 256B 幀 ×40 流水線連發 → 有效吞吐 / baud 效率
  REFLECT  跑 run_reflect(baud, run_seconds)：收到任何資料立即原樣回傳（即時 echo）

部署：由 host 端 (uart_cross_host.py) 用 mpremote exec 上傳本檔並呼叫對應 run_*，
      兩板 baud 由 host 逐檔同步切換。亦可手動 REPL 呼叫。
"""

import time
from machine import UART, Pin

TX, RX = 9, 8
UART_ID = 1
HEAD = 0xAC
TAIL = 0xFF


class _Assembler:
    def __init__(self, framelen, cap=1024):
        self.len = framelen
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
        m = self.n - self.head
        if m > 0:
            self.buf[:m] = self.buf[self.head:self.n]
        self.n = m
        self.head = 0

    def next(self):
        L = self.len
        while True:
            if self.n - self.head < 2:
                self._compact()
                return None
            idx = self.head
            while idx < self.n and self.buf[idx] != HEAD:
                idx += 1
            if idx >= self.n:
                self.head = max(self.n - (L - 1), 0)
                self._compact()
                return None
            self.head = idx
            if self.n - self.head < L:
                self._compact()
                return None
            if self.buf[self.head + L - 1] == TAIL:
                f = bytes(self.buf[self.head:self.head + L])
                self.head += L
                self._compact()
                return f
            self.head += 1


def _drain(uart):
    tmp = bytearray(128)
    for _ in range(8):
        try:
            if uart.any():
                uart.readinto(tmp)
            else:
                break
        except Exception:
            break


def _build_frame(size, seq):
    f = bytearray(size)
    f[0] = HEAD
    f[1] = seq & 0xFF
    f[2] = (seq >> 8) & 0xFF
    f[3] = (seq >> 16) & 0xFF
    f[4] = (seq >> 24) & 0xFF
    for i in range(5, size - 1):           # payload 不含 0xFF，避免誤切幀
        f[i] = (i * 7) & 0x7F
    f[size - 1] = TAIL
    return bytes(f)


def _seq_of(f):
    return f[1] | (f[2] << 8) | (f[3] << 16) | (f[4] << 24)


def _read_frame(uart, asm, mv, timeout_ms):
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < int(timeout_ms):
        try:
            if uart.any():
                n = uart.readinto(mv)
                if n and n > 0:
                    asm.feed(mv[:n])
                    f = asm.next()
                    while f is not None:
                        if f[0] == HEAD and f[asm.len - 1] == TAIL:
                            return f
                        f = asm.next()
        except Exception:
            pass
        time.sleep_ms(1)
    return None


def _open(baud):
    uart = UART(UART_ID, baud, tx=TX, rx=RX, rxbuf=4096)
    _drain(uart)
    return uart


def _frame_time_ms(size, baud):
    return max(1, (size * 10 * 1000) // baud)


def _test_pingpong(uart, baud, rounds=100):
    """10B 幀逐幀等 echo，驗序號 + 統計 RTT"""
    asm = _Assembler(10)
    mv = memoryview(bytearray(64))
    ok = 0
    lats = []
    to = _frame_time_ms(10, baud) * 4 + 100
    for i in range(rounds):
        seq = i & 0xFFFFFFFF
        t0 = time.ticks_ms()
        uart.write(_build_frame(10, seq))
        e = _read_frame(uart, asm, mv, to)
        dt = time.ticks_diff(time.ticks_ms(), t0)
        if e is not None and _seq_of(e) == seq:
            ok += 1
            lats.append(dt)
        else:
            print("  PINGPONG MISS seq=%d dt=%d f=%s" % (seq, dt, e))
    return ok, lats


def _drain_all(uart, asm, mv, max_frames):
    """把目前 RX 裡能組出的幀全部取回（約 2ms 無新資料即停），回傳 (ok, got, serr)"""
    ok = got = serr = 0
    quiet = 0
    base = None
    while got < max_frames:
        try:
            if uart.any():
                n = uart.readinto(mv)
                if n and n > 0:
                    asm.feed(mv[:n])
                    f = asm.next()
                    while f is not None:
                        seq = _seq_of(f)
                        if base is None:
                            base = seq
                        if seq == base + got:
                            ok += 1
                        else:
                            serr += 1
                        got += 1
                        f = asm.next()
                    quiet = 0
            else:
                quiet += 1
        except Exception:
            pass
        if quiet >= 2:
            break
        time.sleep_ms(1)
    return ok, got, serr


def _test_burst(uart, baud, size=10, n=300):
    """分批流水線：一次 BATCH 幀在途（發→收），收完再發下一批 → 全雙工穩定性"""
    batch = max(1, min(50, 2048 // size))   # 在途位元組 ≤2KB，避免對端 RX 溢位
    asm = _Assembler(size)
    mv = memoryview(bytearray(1024))
    t0 = time.ticks_ms()
    ok = got = serr = 0
    sent = 0
    while sent < n:
        b = min(batch, n - sent)
        for i in range(b):
            uart.write(_build_frame(size, sent + i))
        o, g, e = _drain_all(uart, asm, mv, b)
        ok += o
        got += g
        serr += e
        sent += b
    dt = time.ticks_diff(time.ticks_ms(), t0)
    return ok, got, serr, dt


def _test_throughput(uart, baud):
    """256B 大幀流水線連發，幀數按 baud 縮放至約 4s 測試窗"""
    size = 256
    one_rt = size * 10 * 2 * 1000 // baud
    n = max(8, min(40, int(4000 / max(one_rt, 1))))
    ok, got, serr, dt = _test_burst(uart, baud, size=size, n=n)
    bytes_sent = n * size
    if dt <= 0:
        dt = 1
    kbs = bytes_sent * 1000.0 / dt / 1024.0
    eff = 100.0 * kbs * 8.0 * 1024.0 / baud
    return ok, got, serr, dt, kbs, eff


def _fmt_lats(lats):
    if not lats:
        return "n/a"
    l = sorted(lats)
    n = len(l)
    avg = sum(l) / n
    p90 = l[int(n * 0.90) - 1]
    p99 = l[min(int(n * 0.99) - 1, n - 1)]
    return "min=%d avg=%.1f max=%d p90=%d p99=%d" % (l[0], avg, l[-1], p90, p99)


def run_sender(baud):
    print("=" * 60)
    print("SENDER baud=%d (UART1 tx=%d rx=%d)" % (baud, TX, RX))
    uart = _open(baud)

    ok, lats = _test_pingpong(uart, baud)
    print("  pingpong(10Bx100): ok=%d/%d  RTT(ms) %s" % (ok, 100, _fmt_lats(lats)))

    ok, got, serr, dt = _test_burst(uart, baud, 10, 300)
    print("  burst(10Bx300): ok=%d got=%d serr=%d dt=%dms" % (ok, got, serr, dt))

    ok, got, serr, dt, kbs, eff = _test_throughput(uart, baud)
    print("  throughput(256B): ok=%d got=%d serr=%d dt=%dms  %.1f KB/s (%.0f%% of %d)" %
          (ok, got, serr, dt, kbs, eff, baud))
    print("-" * 60)
    uart.deinit()


def run_reflect(baud, run_seconds):
    """即時 echo：收到任何資料立即原樣回傳；超過 IDLE_STOP_MS 無資料提前結束"""
    print("REFLECT baud=%d echo max=%ss" % (baud, run_seconds))
    uart = _open(baud)
    buf = bytearray(512)
    n_total = 0
    t0 = time.ticks_ms()
    last_act = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < int(run_seconds * 1000):
        try:
            if uart.any():
                n = uart.readinto(buf)
                if n and n > 0:
                    uart.write(buf[:n])
                    n_total += n
                    last_act = time.ticks_ms()
        except Exception:
            pass
        if n_total > 0 and time.ticks_diff(time.ticks_ms(), last_act) > 2000:
            break
        time.sleep_ms(0)
    print("REFLECT baud=%d echo_bytes=%d" % (baud, n_total))
    uart.deinit()


# 不 auto-run：由 host 端或手動 REPL 設定參數後呼叫 run_sender / run_reflect
