# -*- coding: utf-8 -*-
"""rs485_hd vs 純 Python DE ping-pong 對比測試（部署到板上跑）

角色:
  SENDER   發 10B 幀 (AC seq 55 55 55 BB)，等 echo，統計成功率 + 單幀來回延遲
  REFLECT  收到一幀就原樣回傳

三種模式 (MODE):
  PY_1MS   純 Python _RS485，DE settle 1ms（現 driver 行為）
  PY_0MS   純 Python _RS485，DE settle 0ms（下界對照，預期不穩）
  HD       rs485_hd.enable(1, de=7) 硬體自動控 DE

部署: 兩塊板都放本檔。SENDER 板 MODE 設要測的模式；REFLECT 板 MODE 固定 HD
      （或 PY_1MS），FIXED 端用穩定模式即可。REPL: exec(open("rs485_hd_bench.py").read())
"""

import time
from machine import UART, Pin

MODE = "PY_1MS"            # PY_1MS / PY_0MS / HD；SENDER 端要測的模式
ROLE = "SENDER"            # SENDER / REFLECT
BAUD = 9600
TX, RX, EN = 9, 8, 7           # 實際接線: GPIO9=TXD→DI, GPIO8=RXD←RO, GPIO7=EN（用戶確認）
UART_ID = 1
ROUNDS = 200               # ping-pong 幀數
ECHO_TIMEOUT_MS = 600
FRAME_LEN = 10
HEAD = 0xAC
TAIL = 0xFF


def _ticks_ms():
    return time.ticks_ms()


def _ticks_diff(a, b):
    return time.ticks_diff(a, b)


class _PyRS485:
    """純 Python DE 控制（與 uart_drv.py / rs485_de_scan.py 相同邏輯）"""
    def __init__(self, uart, en_pin, baud):
        self.io = uart
        self.en = en_pin
        self.baud = int(baud)
        self.en.value(0)

    def _byte_ms(self):
        return max(1, (10 * 1000) // self.baud)

    def _wait_sent(self, nbytes):
        if hasattr(self.io, "txdone"):
            t0 = _ticks_ms()
            try:
                while not self.io.txdone():
                    if _ticks_diff(_ticks_ms(), t0) > 2000:
                        break
                    time.sleep_ms(0)
            except Exception:
                pass
        time.sleep_ms(self._byte_ms() + 1)

    def write(self, data, settle_ms):
        self.en.value(1)
        if settle_ms > 0:
            time.sleep_ms(settle_ms)
        try:
            n = self.io.write(data)
            self._wait_sent(len(data) if (n is None or n <= 0) else n)
            return n
        finally:
            self.en.value(0)


class _Assembler:
    def __init__(self, cap=64):
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
        while True:
            if self.n - self.head < 2:
                self._compact()
                return None
            idx = self.head
            while idx < self.n and self.buf[idx] != HEAD:
                idx += 1
            if idx >= self.n:
                self.head = max(self.n - (FRAME_LEN - 1), 0)
                self._compact()
                return None
            self.head = idx
            if self.n - self.head < FRAME_LEN:
                self._compact()
                return None
            if self.buf[self.head + FRAME_LEN - 1] == TAIL:
                f = bytes(self.buf[self.head:self.head + FRAME_LEN])
                self.head += FRAME_LEN
                self._compact()
                return f
            self.head += 1


def _drain(uart):
    tmp = bytearray(64)
    for _ in range(8):
        try:
            if uart.any():
                uart.readinto(tmp)
            else:
                break
        except Exception:
            break


def _build_frame(seq):
    f = bytearray(FRAME_LEN)
    f[0] = HEAD
    f[1] = seq & 0xFF
    f[2] = (seq >> 8) & 0xFF
    f[3] = (seq >> 16) & 0xFF
    f[4] = (seq >> 24) & 0xFF
    f[5] = 0x11
    f[6] = 0x22
    f[7] = 0x33
    f[8] = 0x44
    f[9] = TAIL
    return bytes(f)


def _seq_of(f):
    return f[1] | (f[2] << 8) | (f[3] << 16) | (f[4] << 24)


def _read_frame(uart, asm, mv, timeout_ms):
    t0 = _ticks_ms()
    while _ticks_diff(_ticks_ms(), t0) < int(timeout_ms):
        n = 0
        try:
            if uart.any():
                n = uart.readinto(mv)
        except Exception:
            n = 0
        if n and n > 0:
            asm.feed(mv[:n])
            f = asm.next()
            while f is not None:
                if f[0] == HEAD and f[FRAME_LEN - 1] == TAIL:
                    return f
                f = asm.next()
        time.sleep_ms(1)
    return None


def _open_hd():
    """rs485_hd 硬體模式：先建 UART 再 enable（重要順序！）
    NOTE: enable 目前只吃 positional（de 不能寫 keyword），用 enable(1, 7)"""
    import rs485_hd
    uart = UART(UART_ID, BAUD, tx=TX, rx=RX)   # 先建 UART (install driver)
    rs485_hd.enable(UART_ID, EN)               # 再 enable (RS485 模式)
    return uart, lambda data: uart.write(data)


def _open_py(settle_ms):
    uart = UART(UART_ID, BAUD, tx=TX, rx=RX)
    en_pin = Pin(EN, Pin.OUT, value=0)
    rs = _PyRS485(uart, en_pin, BAUD)
    return uart, lambda data: rs.write(data, settle_ms)


def _open(mode):
    if mode == "HD":
        return _open_hd()
    settle = 1 if mode == "PY_1MS" else 0
    return _open_py(settle)


def run_reflect(run_seconds=None):
    print("=" * 60)
    print("REFLECT 端 (baud={}) — 收到一幀原樣回傳".format(BAUD))
    if run_seconds:
        print("(限時 {}s 自動結束)".format(run_seconds))
    print("=" * 60)
    uart, w = _open("HD")          # 反射端固定用硬體模式（穩定）
    asm = _Assembler()
    mv = memoryview(bytearray(FRAME_LEN * 4))
    got = 0
    t0 = _ticks_ms()
    while True:
        if run_seconds and _ticks_diff(_ticks_ms(), t0) > int(run_seconds * 1000):
            print("REFLECT_TIMEOUT total_recv={}".format(got))
            return
        n = 0
        try:
            if uart.any():
                n = uart.readinto(mv)
        except Exception:
            n = 0
        if n and n > 0:
            asm.feed(mv[:n])
            f = asm.next()
            while f is not None:
                if f[0] == HEAD and f[FRAME_LEN - 1] == TAIL:
                    got += 1
                    w(f)
                    print("RECV seq={} → ECHO (total={})".format(_seq_of(f), got))
                f = asm.next()
        time.sleep_ms(1)


def run_sender():
    print("=" * 60)
    print("SENDER 端 模式={} baud={} rounds={}".format(MODE, BAUD, ROUNDS))
    print("=" * 60)
    uart, w = _open(MODE)
    asm = _Assembler()
    mv = memoryview(bytearray(FRAME_LEN * 4))

    ok = 0
    lats = []
    _drain(uart)
    for i in range(ROUNDS):
        seq = i & 0xFFFFFFFF
        t0 = _ticks_ms()
        w(_build_frame(seq))
        f = _read_frame(uart, asm, mv, ECHO_TIMEOUT_MS)
        dt = _ticks_diff(_ticks_ms(), t0)
        if f is not None and _seq_of(f) == seq:
            ok += 1
            lats.append(dt)
        else:
            print("MISS seq={} dt={}ms f={}".format(seq, dt, f))
        if (i + 1) % 50 == 0:
            print("... {}/{} ok={}".format(i + 1, ROUNDS, ok))

    fail = ROUNDS - ok
    print("-" * 60)
    print("結果: ok={} fail={} 成功率={:.1f}%".format(ok, fail, 100.0 * ok / ROUNDS))
    if lats:
        lats.sort()
        n = len(lats)
        avg = sum(lats) / n
        p90 = lats[int(n * 0.90) - 1]
        p99 = lats[min(int(n * 0.99) - 1, n - 1)]
        print("單幀來回延遲(ms): min={} avg={:.1f} max={} p90={} p99={}".format(lats[0], avg, lats[-1], p90, p99))
    print("-" * 60)


# 不 auto-run：由部署端設定 ROLE/MODE 後顯式呼叫 run_reflect()/run_sender()
# （避免 import 時就誤跑，且部署端無法覆寫 ROLE）
