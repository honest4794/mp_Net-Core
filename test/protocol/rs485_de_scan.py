# -*- coding: utf-8 -*-
"""RS485 DE 使能延遲掃描 — 找出「第一個 byte 能被乾淨送出」的最小 DE settle 時間

背景
----
RS485 半雙工 ping-pong 回覆常需要把 DE（方向腳）拉高後「等一段時間」再寫資料，
否則第一個 byte 的 start bit 會被吃掉，對端 parser 失步，看起來像「回覆開頭被丟」。
`slave/driver/uart_drv.py` 目前把這段時間寫死成 `sleep_ms(20)`，太保守。

本腳本目的：在兩塊板上用「一掃一反射」量出「最小穩定 DE settle 時間」，
讓你可以把 20ms 換成實測值，縮短來回延遲。

架構（兩塊板，各接一顆 RS485 收發器，A-A / B-B / GND 共地）：
  MODE = "SCAN"     掃描端：對 SWEEP_MS 的每個 settle 值做 ROUNDS 次 ping-pong，
                    統計回覆成功率，最後印出最小穩定值。
  MODE = "REFLECT"  反射端：收到一幀就原樣回傳（settle 固定 FIXED_SETTLE_MS）。
                    反射端務必「已知是穩定的」，這樣掃到的失敗才歸因於掃描端自己。

接線（與 driver / circuit_bus 一致）：
  GPIO8 = TX → 收發器 DI、GPIO9 = RX ← 收發器 RO、GPIO7 = EN → DE+RE（active-high）

部署：兩塊板都上傳本檔，把 MODE 寫死不同值（一塊 SCAN、一塊 REFLECT）後
  改名 main.py 丟根目錄開機自動跑；或 REPL exec(open("rs485_de_scan.py").read())。

判讀：
  - 某個 settle 值 100%（ok == ROUNDS）→ 該值可穩定送出。
  - 最小的 100% 值即為「最小穩定 DE settle」。實務上再加 1ms 餘量。
  - 從 0ms 就 100% → 你的收發器不需要額外 settle（純 MAX485/SP485 通常如此）。
  - 一路到 20ms 都 < 100% → 問題不在 settle，是接線 / 極性 / 終端電阻 / 總線偏壓。

相關文件：doc/rs485_de_timing.md
"""

import time
from machine import UART, Pin

# ── 部署設定 ──
MODE = "SCAN"                  # 這塊板當 "SCAN"（掃描端）或 "REFLECT"（反射端）
BAUD = 9600                    # 兩塊板要一致
TX, RX, EN = 8, 9, 7           # DI, RO, DE+RE
UART_ID = 1
EN_ACTIVE = 1                  # 1 = 拉高發送（active-high）；0 = 拉低發送（active-low）

# ── 掃描參數（僅 SCAN 端使用） ──
SWEEP_MS = (0, 1, 2, 4, 6, 8, 10, 12, 16, 20)   # 要掃的 DE settle 值（ms）
ROUNDS = 50                    # 每個 settle 值測幾輪
ECHO_TIMEOUT_MS = 600          # 單幀等 echo 上限（10B@9600 往返 ~15ms，600 很鬆）

# ── 反射端設定（僅 REFLECT 端使用） ──
FIXED_SETTLE_MS = 2            # 反射端固定 settle（務必已知穩定）

# ── 幀格式（統一 10 位元組，與 circuit_bus 相同） ──
FRAME_LEN = 10
HEAD = 0xAC
TAIL = 0xFF


def _ticks_ms():
    return time.ticks_ms() if hasattr(time, "ticks_ms") else int(time.time() * 1000)


def _ticks_diff(a, b):
    return time.ticks_diff(a, b) if hasattr(time, "ticks_diff") else a - b


def _hex(data):
    return " ".join("{:02X}".format(b) for b in data)


# ── RS485 半雙工方向控制（settle 可變） ──
class _RS485:
    def __init__(self, uart, en_pin, baud):
        self.io = uart
        self.en = en_pin
        self.baud = int(baud)
        self.en.value(0)                       # 閒置 = 接收

    def _byte_ms(self):
        return max(1, (10 * 1000) // self.baud)

    def _wait_sent(self, nbytes):
        # txdone() 等到 shift register 排空（最精準）；沒有就退回傳輸時間估算。
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
        self.en.value(EN_ACTIVE)
        if settle_ms > 0:
            time.sleep_ms(settle_ms)           # ← 變數：DE 使能 settle
        try:
            n = self.io.write(data)
            self._wait_sent(len(data) if (n is None or n <= 0) else n)
            return n
        finally:
            self.en.value(1 if EN_ACTIVE == 0 else 0)


# ── 中央緩衝：RX byte 流 → 依 AC/FF 固定 10B 切割（head 指標，不用 del） ──
class _Assembler:
    def __init__(self, cap=64):
        self.buf = bytearray(cap)
        self.n = 0             # 有效 byte 數（存在 buf[0:n]）
        self.head = 0          # 第一個未消費 byte 的位置

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
        """回傳完整 10B 幀(bytes) 或 None。頭尾不齊/錯位自動重同步。"""
        while True:
            if self.n - self.head < 2:
                self._compact()
                return None
            idx = self.head
            while idx < self.n and self.buf[idx] != HEAD:
                idx += 1
            if idx >= self.n:
                # 沒有頭：只保留最後 9B（防頭跨段），其餘丟棄
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
            self.head += 1     # 尾不是 FF → 假頭，跳過再找


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


def _wait_echo(uart, asm, rxmv, timeout_ms):
    """不斷讀直到收到一幀 echo；逾時回 None。"""
    t0 = _ticks_ms()
    while _ticks_diff(_ticks_ms(), t0) < int(timeout_ms):
        n = 0
        try:
            if uart.any():
                n = uart.readinto(rxmv)
        except Exception:
            n = 0
        if n and n > 0:
            asm.feed(rxmv[:n])
            f = asm.next()
            while f is not None:
                if f[0] == HEAD and f[FRAME_LEN - 1] == TAIL:
                    return f
                f = asm.next()
        time.sleep_ms(1)
    return None


def run_reflect(rs, asm, rxmv):
    print("=" * 60)
    print("RS485 DE 掃描 — REFLECT 反射端 (baud={} settle={}ms)".format(BAUD, FIXED_SETTLE_MS))
    print("收到一幀就原樣回傳；Ctrl-C 停止")
    print("=" * 60)
    got = 0
    while True:
        n = 0
        try:
            if rs.io.any():
                n = rs.io.readinto(rxmv)
        except Exception:
            n = 0
        if n and n > 0:
            asm.feed(rxmv[:n])
            f = asm.next()
            while f is not None:
                if f[0] == HEAD and f[FRAME_LEN - 1] == TAIL:
                    got += 1
                    rs.write(f, FIXED_SETTLE_MS)
                    print("RECV seq={} → ECHO (total={})".format(_seq_of(f), got))
                f = asm.next()
        time.sleep_ms(1)


def run_scan(rs, asm, rxmv):
    print("=" * 60)
    print("RS485 DE 掃描 — SCAN 掃描端 (baud={} rounds={}/值)".format(BAUD, ROUNDS))
    print("byte 時間 ≈ {}ms；SWEEP={}".format(rs._byte_ms(), list(SWEEP_MS)))
    print("=" * 60)
    print("{:>8}  {:>6}  {:>6}  {}".format("settle", "ok", "fail", "結果"))
    results = []
    for settle in SWEEP_MS:
        _drain(rs.io)
        ok = 0
        t0 = _ticks_ms()
        for i in range(ROUNDS):
            seq = i & 0xFFFFFFFF
            rs.write(_build_frame(seq), settle)
            f = _wait_echo(rs.io, asm, rxmv, ECHO_TIMEOUT_MS)
            if f is not None and f[0] == HEAD and f[FRAME_LEN - 1] == TAIL and _seq_of(f) == seq:
                ok += 1
        fail = ROUNDS - ok
        dt = _ticks_diff(_ticks_ms(), t0)
        verdict = "✓ 穩定" if ok == ROUNDS else "✗ 不穩"
        print("{:>6}ms  {:>6}  {:>6}  {}  ({}ms)".format(settle, ok, fail, verdict, dt))
        results.append((settle, ok))

    print("-" * 60)
    stable = [s for s, k in results if k == ROUNDS]
    if stable:
        best = min(stable)
        print("最小穩定 settle = {}ms（建議實際使用 {}ms）".format(best, best + 1))
    else:
        print("全部 settle 值都未達 100% → 問題不在 DE settle")
        print("（查接線 / EN 極性 / 終端電阻 / 總線偏壓，或見 doc/rs485_de_timing.md 第 7 節）")
    print("-" * 60)


def run(mode=MODE, baud=BAUD, tx=TX, rx=RX, en=EN, uart_id=UART_ID):
    uart = UART(int(uart_id), baudrate=int(baud), tx=Pin(int(tx)), rx=Pin(int(rx)))
    en_pin = Pin(int(en), Pin.OUT, value=0)
    rs = _RS485(uart, en_pin, baud)
    _drain(uart)

    asm = _Assembler()
    rxbuf = bytearray(FRAME_LEN * 4)
    rxmv = memoryview(rxbuf)   # 讀取緩衝（中央，重用）

    if mode == "REFLECT":
        run_reflect(rs, asm, rxmv)
    else:
        run_scan(rs, asm, rxmv)


run()
