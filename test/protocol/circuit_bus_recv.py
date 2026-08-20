# -*- coding: utf-8 -*-
"""CircuitBus 接收器（回應機）— 接收 AC...FF 10B 幀，把 FF 前的數值原樣返回（自包含，上傳即跑）

協議（統一 10 位元組）：
  幀 = [0xAC] + 8B 內容 + [0xFF]
        ├ 0xAC = 頭
        ├ 8B   = 內容（前 4B = 序號 u32 LE，後 4B = 填充 11 22 33 44，可改隨機）
        └ 0xFF = 尾

流程：
  收到「完整一幀」（頭 AC + 尾 FF 都齊、10B 湊滿）後，
  把「FF 前面的數值」原樣回傳（echo 整幀）給主機，主機就能確認往返內容一致。

處理方式（中央緩衝、避免 GC）：
  - 每次讀取把所有可讀 byte 一次讀完（uart.any()），丟進中央緩衝「排列」。
  - 用 head 指標切割：可能收到「只有頭沒有尾 / 只有尾沒有頭 / 雜訊」，
    一律等湊滿 10B 且頭尾正確才算數；不完整就留著拼，錯位就重同步。
  - 不用 del、不逐幀建新物件（rxbuf / 緩衝 / echo 都重用）。

接線（每塊板一顆 RS485 收發器）：
  GPIO8 = TX → 收發器 DI     (MCU 送出)
  GPIO9 = RX ← 收發器 RO     (MCU 收到)
  GPIO7 = EN → 收發器 DE+RE  (active-high：1=發送, 0=接收)
  匯流排 A-A、B-B，兩板 GND 共地。

部署：本檔改名 main.py 丟根目錄 → 開機自動跑；或 REPL exec(open("circuit_bus_recv.py").read())。
對應主機：circuit_bus_host.py（每秒送一幀）。
"""

import time
from machine import UART, Pin

BAUD = 9600                    # 與主機一致
TX, RX, EN = 8, 9, 7           # DI, RO, DE+RE
UART_ID = 1
FRAME_LEN = 10                 # 統一 10 位元組
HEAD = 0xAC
TAIL = 0xFF

# 自動切 baud 順序（需與主機 bench_run 的 BENCH_BAUDS 一致）
BENCH_BAUDS = (9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600)
BAUD_DWELL_MS = 12000          # 每檔停留多久（主機 BENCH_MS 要 < 此值，保證重疊）

# 半雙工規則：接收器「收集一批 → 一批結束 → 整批回覆」，不逐幀 echo。
BENCH_BATCH = 20               # 一批幾幀（主機每批發的幀數，兩邊要一致）
BATCH_GAP_MS = 0               # 依 baud 動態算：3×幀傳輸時間（min 10ms）


# ── RS485 半雙工方向控制（與 driver._Rs485Uart 同一套時序） ──
class _RS485:
    def __init__(self, uart, en_pin, baudrate):
        self.io = uart
        self.en = en_pin
        self.baud = int(baudrate)
        self.en.value(0)                       # 閒置 = 接收

    def _wait_sent(self, nbytes):
        # ping-pong 半雙工：DE 過晚放下會吃掉「對端 echo」的開頭。
        # 舊公式 (nbytes+6)*10bit/baud + 4 對連續發送是保險，但對一發一收太保守
        # （10B@9600 實傳 10.4ms，舊公式等 20ms → 錯過 echo 開頭）。
        # 改成精確傳輸時間 + 2ms 餘量。
        time.sleep_ms(max(2, (nbytes * 10 * 1000) // self.baud + 2))

    def write(self, data):
        self.en.value(1)
        time.sleep_ms(2)                       # 驅動器使能穩定
        try:
            n = self.io.write(data)
            self._wait_sent(len(data) if (n is None or n <= 0) else n)
            return n
        finally:
            self.en.value(0)                   # 送完才回接收

    def readinto(self, buf):
        return self.io.readinto(buf)


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
                self.head = max(self.n - 9, 0) if self.n >= 9 else 0
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


def _ticks_ms():
    return time.ticks_ms() if hasattr(time, "ticks_ms") else int(time.time() * 1000)


def _ticks_diff(a, b):
    return time.ticks_diff(a, b) if hasattr(time, "ticks_diff") else a - b


def _sleep_ms(ms):
    if hasattr(time, "sleep_ms"):
        time.sleep_ms(ms)
    else:
        time.sleep(ms / 1000.0)


def _hex(data):
    return " ".join("{:02X}".format(b) for b in data)


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


def run(baud=BAUD, tx=TX, rx=RX, en=EN, uart_id=UART_ID):
    uart = UART(int(uart_id), baudrate=int(baud), tx=Pin(int(tx)), rx=Pin(int(rx)))
    rs = _RS485(uart, Pin(int(en), Pin.OUT, value=0), baud)
    _drain(uart)

    asm = _Assembler()
    rxbuf = bytearray(FRAME_LEN * 4)
    rxmv = memoryview(rxbuf)   # 讀取緩衝（中央，重用）

    print("=" * 56)
    print("CIRCUIT_BUS 接收器 (baud={} tx={} rx={} en={})".format(baud, tx, rx, en))
    print("格式: AC + 8B + FF；收完整幀就把 FF 前的數值原樣回傳")
    print("=" * 56)

    got = echoed = bad = 0
    t_report = _ticks_ms()
    while True:
        n = 0
        try:
            if uart.any():
                n = rs.readinto(rxbuf)
        except Exception:
            n = 0
        if n and n > 0:
            asm.feed(rxmv[:n])
            f = asm.next()
            while f is not None:
                if f[0] == HEAD and f[FRAME_LEN - 1] == TAIL:
                    got += 1
                    seq = f[1] | (f[2] << 8) | (f[3] << 16) | (f[4] << 24)
                    print("RECV seq={} hex={}".format(seq, _hex(f)))
                    rs.write(f)              # 原樣回傳（FF 前的數值送回）
                    echoed += 1
                    print("  -> ECHO 回整幀 ({}B)".format(FRAME_LEN))
                else:
                    bad += 1
                    print("RECV 壞幀 hex={}".format(_hex(f)))
                f = asm.next()

        if _ticks_diff(_ticks_ms(), t_report) >= 10000:
            print("-- 狀態: 完整幀={} echo={} 壞幀={}".format(got, echoed, bad))
            t_report = _ticks_ms()
        _sleep_ms(1)


def run_test(baud=BAUD, tx=TX, rx=RX, en=EN, uart_id=UART_ID):
    """連續測試模式（配合主機 bench_run 掃 baud）：收到完整一幀就立刻 echo，
    每 5 秒印一次狀態；echo 幀內含對端看到的 seq，主機可對驗。"""
    uart = UART(int(uart_id), baudrate=int(baud), tx=Pin(int(tx)), rx=Pin(int(rx)))
    rs = _RS485(uart, Pin(int(en), Pin.OUT, value=0), baud)
    _drain(uart)

    asm = _Assembler()
    rxbuf = bytearray(FRAME_LEN * 4)
    rxmv = memoryview(rxbuf)

    print("=" * 56)
    print("CIRCUIT_BUS 接收器 TEST mode (baud={} tx={} rx={} en={})".format(baud, tx, rx, en))
    print("收到完整 AC...FF 幀 → 立即原樣 echo")
    print("=" * 56)

    got = echoed = bad = 0
    t_report = _ticks_ms()
    while True:
        n = 0
        try:
            if uart.any():
                n = rs.readinto(rxbuf)
        except Exception:
            n = 0
        if n and n > 0:
            asm.feed(rxmv[:n])
            f = asm.next()
            while f is not None:
                if f[0] == HEAD and f[FRAME_LEN - 1] == TAIL:
                    got += 1
                    rs.write(f)              # 立即 echo
                    echoed += 1
                else:
                    bad += 1
                f = asm.next()
            # 有資料就連續處理，不 sleep，跟上主機的發送節奏
        if _ticks_diff(_ticks_ms(), t_report) >= 5000:
            print("RECV TEST baud={}  rx={} echoed={} bad={}".format(baud, got, echoed, bad))
            t_report = _ticks_ms()


def run_auto_bench(tx=TX, rx=RX, en=EN, uart_id=UART_ID):
    """接收器自動模式（半雙工批次規則）：照主機同一順序切 baud。

    規則：主機「發送一批 → 停止 → 等回覆」，所以接收器
      - 接收模式：收集整批幀，不逐幀 echo（半雙工不能一邊收一邊回）
      - 一批結束：收到 BENCH_BATCH 幀，或總線安靜超過 gap（3×幀傳輸時間）
      - 回覆模式：把整批原樣回送，回完清掉自己發送期間採樣到的垃圾
    接收器無法打指令 → 上傳即自動跑。
    """
    uart = UART(int(uart_id), baudrate=int(BENCH_BAUDS[0]), tx=Pin(int(tx)), rx=Pin(int(rx)))
    rs = _RS485(uart, Pin(int(en), Pin.OUT, value=0), BENCH_BAUDS[0])
    asm = _Assembler()
    rxbuf = bytearray(FRAME_LEN * 4)
    rxmv = memoryview(rxbuf)
    batch_buf = bytearray(BENCH_BATCH * FRAME_LEN)   # 批次緩衝（中央，重用）

    print("=" * 56)
    print("CIRCUIT_BUS 接收器 AUTO-BENCH (tx={} rx={} en={})".format(tx, rx, en))
    print("規則: 收集一批({}幀)→整批回覆；自動切 baud: {}".format(BENCH_BATCH, list(BENCH_BAUDS)))
    print("=" * 56)

    while True:
        for baud in BENCH_BAUDS:
            baud = int(baud)
            try:
                uart.init(baudrate=baud)
            except Exception:
                pass
            rs.baud = baud
            _drain(uart)
            # gap：總線安靜超過此值就算「一批結束」開始回覆
            frame_tx_ms = (FRAME_LEN * 10 * 1000) // baud
            gap_ms = max(10, 3 * frame_tx_ms)
            print("RECV switch baud={}  gap={}ms".format(baud, gap_ms))

            got = echoed = bad = 0
            batch_n = 0
            last_rx = _ticks_ms()
            t_phase = _ticks_ms()
            t_report = _ticks_ms()
            while _ticks_diff(_ticks_ms(), t_phase) < BAUD_DWELL_MS:
                # ── 接收模式：收集整批 ──
                n = 0
                try:
                    if uart.any():
                        n = rs.readinto(rxbuf)
                except Exception:
                    n = 0
                if n and n > 0:
                    asm.feed(rxmv[:n])
                    f = asm.next()
                    while f is not None:
                        if f[0] == HEAD and f[FRAME_LEN - 1] == TAIL:
                            got += 1
                            if batch_n < BENCH_BATCH:
                                # 存進批次緩衝（原樣保留，回覆時整批送出）
                                off = batch_n * FRAME_LEN
                                batch_buf[off:off + FRAME_LEN] = f
                                batch_n += 1
                            last_rx = _ticks_ms()
                        else:
                            bad += 1
                        f = asm.next()

                # ── 批次結束判斷：收到 N 幀 或 總線安靜超過 gap ──
                if batch_n > 0 and (batch_n >= BENCH_BATCH
                                    or _ticks_diff(_ticks_ms(), last_rx) >= gap_ms):
                    # ── 回覆模式：整批原樣回送（半雙工，此刻只有我發） ──
                    for i in range(batch_n):
                        off = i * FRAME_LEN
                        rs.write(batch_buf[off:off + FRAME_LEN])
                        echoed += 1
                    _drain(uart)                 # 清自己發送期間採樣到的垃圾
                    batch_n = 0

                if _ticks_diff(_ticks_ms(), t_report) >= 5000:
                    print("RECV baud={}  rx={} echoed={} bad={}".format(baud, got, echoed, bad))
                    t_report = _ticks_ms()
            print("RECV baud={} 段結束  rx={} echoed={} bad={}".format(baud, got, echoed, bad))


# 接收器端「無法打指令」：上傳後必須照預設自動跑。
# 預設 = 自動切 baud 模式（配合主機 bench_run 全掃）。
run_auto_bench()
