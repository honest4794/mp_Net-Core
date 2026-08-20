# -*- coding: utf-8 -*-
"""CircuitBus 連線診斷 — 一發一收（最簡、自包含、上傳即跑）

用「一個發、一個收」來驗證 RS485 實線的單向能力，逐步隔離問題。

兩塊板都上傳同一支檔案，只差最上面的 MODE 寫死不同：

  Board A:  MODE = "TX"   → 每 INTERVAL_MS 送一筆 "PING <計數>\n"，並印出送了什麼
  Board B:  MODE = "RX"   → 一直收，把「收到的任何 byte」用 hex + 文字印出來，
                            每 5 秒印一次心跳（總共收了多少 byte，證明它活著）

為什麼這樣能找出問題：RX 端「印原始 byte」而不是「認封包」——
  只要線上有任何東西（正確資料或雜訊），你都看得到；
  認不到封包會一片空白，原始 byte 則會顯示「有電位跳動但內容是亂碼」。
  這一步完全不碰 frame / CRC / echo 時序，把變數降到最少。

接線（每塊板各接一顆 RS485 收發器，如 ZY-SP485 / MAX485）：
  GPIO8 = TX → 收發器 DI     (MCU 送出)
  GPIO9 = RX ← 收發器 RO     (MCU 收到)
  GPIO7 = EN → 收發器 DE+RE  (active-high：1=發送, 0=接收)
  匯流排 A-A、B-B，兩板 GND 共地。

測試順序（驗證雙向）：
  Phase 1  Board A 設 TX，Board B 設 RX → 看 B 有沒有印出 "PING 1/2/3..."
  Phase 2  兩塊板 MODE 對調（A=RX, B=TX）→ 看 A 有沒有印出
  判讀：
    - 收得到正確 "PING N" → 這個方向 OK（TX 腳 + A/B + GND + EN 全對）
    - 收得到但亂碼 → 線有動，是 baud 對不準 / 終端電阻 / 雜訊
    - 完全收不到（心跳 0 byte）→ 這方向的接線或 EN 極性有問題

EN 極性：預設 active-high（EN=1 發送、0 接收，與 driver/_Rs485Uart 一致）。
  若你的收發器是 active-low，把下面的 EN_ACTIVE 改成 0。

⚠️ 執行前：確認 config.json 的 UART.enable = 0（否則 boot 會先佔住 UART1）。
  或直接把本檔改名 main.py 放根目錄，開機自動跑。
"""

import time
from machine import UART, Pin

MODE = "RX"                    # 寫死：這塊板當 "TX"（發）或 "RX"（收）
BAUD = 9600                    # 兩塊板要一致
TX, RX, EN = 8, 9, 7           # DI, RO, DE+RE
UART_ID = 1
EN_ACTIVE = 1                  # 1 = 拉高發送（active-high）；0 = 拉低發送（active-low）
INTERVAL_MS = 500              # TX 每隔多久送一筆


def _send(uart, en, data):
    """RS485 半雙工發送：拉 EN → 等使能 → 寫 → 等送完 → 放 EN 回接收。"""
    en.value(EN_ACTIVE)
    time.sleep_ms(2)                          # 半自動方向模組需 ~2ms 完全使能
    try:
        uart.write(data)
        # 等資料離開 shift register 再放低 DE，避免截斷尾 byte（min 4ms）
        time.sleep_ms(max(4, (len(data) + 6) * 10 * 1000 // BAUD + 4))
    finally:
        en.value(1 if EN_ACTIVE == 0 else 0)  # 送完回接收（與 EN_ACTIVE 相反）


def _ticks_ms():
    return time.ticks_ms() if hasattr(time, "ticks_ms") else int(time.time() * 1000)


def _ticks_diff(a, b):
    if hasattr(time, "ticks_diff"):
        return time.ticks_diff(a, b)
    return a - b


def _drain(uart):
    for _ in range(8):
        try:
            if uart.any():
                uart.read(uart.any())
            else:
                break
        except Exception:
            break


def run_tx(uart, en):
    print("CIRCUIT_BUS LINK — TX mode  (baud={}, tx={} en={})".format(BAUD, TX, EN))
    print("每 {}ms 送一筆 'PING <n>'".format(INTERVAL_MS))
    n = 0
    while True:
        n += 1
        data = "PING {}\n".format(n).encode()
        _send(uart, en, data)
        print("TX -> {}".format(data.decode().strip()))
        time.sleep_ms(INTERVAL_MS)


def _print_line(seg):
    """把一段 byte 用文字印出；有不可列印字元就加印 hex。"""
    try:
        text = seg.decode("utf-8")
    except Exception:
        text = None
    printable = text is not None and all((b == 9) or (32 <= b < 127) for b in seg)
    if printable:
        print("RX line: {!r}".format(text))
    else:
        print("RX line: hex={}  text={!r}".format(
            "".join("{:02X}".format(b) for b in seg),
            text if text is not None else "?"))


def run_rx(uart, en):
    en.value(0)                       # 接收端：DE+RE 永遠保持在接收
    print("CIRCUIT_BUS LINK — RX mode  (baud={}, rx={} en={})".format(BAUD, RX, EN))
    print("開始收，重組成完整一行印出；每 5 秒印心跳...")
    total = 0
    t0 = _ticks_ms()
    line = bytearray()
    while True:
        n = 0
        try:
            n = uart.any()
        except Exception:
            n = 0
        if n:
            try:
                raw = uart.read(n)
            except Exception:
                raw = None
            if raw:
                total += len(raw)
                line.extend(raw)
                # 拆行：遇到 \n 就印出完整一行（用 find + slice，不用 del）
                while True:
                    i = line.find(b"\n")
                    if i < 0:
                        break
                    seg = bytes(line[:i])
                    line = line[i + 1:]
                    _print_line(seg)
        # 5 秒心跳，證明 RX 端還活著、且這段時間收了多少 byte
        if _ticks_diff(_ticks_ms(), t0) >= 5000:
            print("RX alive ... total={}B  partial={!r}".format(total, bytes(line)))
            t0 = _ticks_ms()
        time.sleep_ms(1)


def run(mode=MODE, baud=BAUD, tx=TX, rx=RX, en=EN, uart_id=UART_ID):
    uart = UART(int(uart_id), baudrate=int(baud), tx=Pin(int(tx)), rx=Pin(int(rx)))
    en_pin = Pin(int(en), Pin.OUT, value=0)
    _drain(uart)
    if mode == "TX":
        run_tx(uart, en_pin)
    else:
        run_rx(uart, en_pin)


run()
