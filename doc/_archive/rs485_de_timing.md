# RS485 半雙工 DE 使能時序 — 20ms GAP 分析

記錄 RS485 半雙工來回回覆（ping-pong）時「需要等 20ms 才能收到回覆」的調查結論、
根因，以及如何用 `test/protocol/rs485_de_scan.py` 量出真正需要的最小延遲。

---

## 目錄

- [1. 問題](#1-問題)
- [2. 結論（先講重點）](#2-結論先講重點)
- [3. 20ms 到底在哪](#3-20ms-到底在哪)
- [4. UART 傳送不是 DMA](#4-uart-傳送不是-dma)
- [5. 方向腳控制的正確語意（txdone）](#5-方向腳控制的正確語意txdone)
- [6. codebase 裡互相矛盾的延遲值](#6-codebase-裡互相矛盾的延遲值)
- [7. 真正的根因：硬體使能時間](#7-真正的根因硬體使能時間)
- [8. 解決方案](#8-解決方案)
- [9. 測試腳本使用說明](#9-測試腳本使用說明)
- [10. 參考檔案](#10-參考檔案)

---

## 1. 問題

兩塊板透過 RS485 半雙工做性能測試（一來一回的指令回覆）。測試時發現：

> 送出指令後，**無法立刻收到回覆，需要等 20ms 才能收到**，而 20ms 對來回延遲而言太長。

最初懷疑是「UART 用 DMA 傳送，DMA 與 DE 拉高拉低的時序打架」，但追完原代碼後確認
**與 DMA 無關**，也不是 MicroPython 的錯。真正的 20ms 是一段寫死的延遲（見 [第 3 節](#3-20ms-到底在哪)）。

## 2. 結論（先講重點）

1. **`machine.UART` 不是 DMA 傳送**，是 FIFO + 中斷（見 [第 4 節](#4-uart-傳送不是-dma)）。
2. 20ms 來自 `slave/driver/uart_drv.py:76` 的 `time.sleep_ms(20)`，是**寫死的魔法數字**。
3. 同一顆收發器在 codebase 裡出現 **2ms / 10ms / 20ms 三種「使能穩定」延遲**，彼此矛盾，
   證明 20ms 是某次實驗未收斂後被保守釘死，並非硬體底線（見 [第 6 節](#6-codebase-裡互相矛盾的延遲值)）。
4. 真正需要的是「DE 拉高後、第一個 byte 被乾淨送出」的**硬體使能時間**，量級取決於
   收發器模組的型態（光耦隔離／自動方向／總線偏壓），不是軟體能憑空消除的。
5. 根治方案：改用 ESP-IDF 原生 RS485 半雙工（硬體自動控 DE，軟體延遲歸零）；
   快速方案：把 20ms 改成 config 可設定，並用掃描腳本量出最小穩定值。

## 3. 20ms 到底在哪

回覆路徑：

```
bench_actions._send_report → CircuitBus.write → io.write = _Rs485Uart.write()
```

`slave/driver/uart_drv.py:70-85` 的 `_Rs485Uart.write()`：

```python
def write(self, data):
    self._wait_bus_quiet()     # 先等 ~3ms（3 個 byte 時間）
    self.en.value(1)
    time.sleep_ms(20)          # ← 就是它，uart_drv.py:76
    try:
        n = self.io.write(data)
        self._wait_sent(...)   # ← 這行是對的（txdone），不用改
        return n
    finally:
        self.en.value(0)
```

每一次回覆，在「真正開始發送」之前就白等 **20ms + `_wait_bus_quiet` 的 ~3ms ≈ 23ms**。
以 9600 baud 為例（1 byte ≈ 1.04ms），等於白白停了大約 **19 個 byte 的時間**，
之後才開始送那 ~13 bytes 的回覆封包（~13.5ms）。這就是來回延遲偏慢的主因。

## 4. UART 傳送不是 DMA

`machine.UART` 走標準 ESP-IDF UART driver：

| 呼叫鏈 | 位置 |
|---|---|
| `mp_machine_uart_write()` | `ports/esp32/machine_uart.c:701` |
| → `uart_write_bytes()` | `lib/esp-idf/.../esp_driver_uart/src/uart.c:1629` |
| → `uart_tx_all()` | `lib/esp-idf/.../esp_driver_uart/src/uart.c:1565` |

`uart_tx_all()` 的實作是把資料塞進 **TX FIFO / ring buffer**，靠 **中斷**
（`TXFIFO_EMPTY` / `TX_DONE`）持續填充，**不是 DMA**。整個 `esp_driver_uart` 裡 GDMA
只出現在 `uhci.c`（UHCI 週邊，與 `machine.UART` 無關）。

所以「DMA 和拉高拉低的時序問題」這個前提本身不成立。

## 5. 方向腳控制的正確語意（txdone）

兩個 Python 方法的語意不同，這是方向腳時序的關鍵：

| 方法 | 語意 | 時機 |
|---|---|---|
| `uart.write(buf)` | 資料**排進** FIFO/ring buffer | 立刻返回，**不代表送完** |
| `uart.txdone()` | FSM 回到 idle，最後 1 bit 已離開 shift register | **真的送完** |

- `txdone()` 底層是 `uart_wait_tx_done(0)`（`machine_uart.c:553`），對應 ESP-IDF 的
  `UART_INTR_TX_DONE` 中斷（`uart.c:1437`），等的是 shift register 清空。
- 正確的 RS485 流程是：拉高 DE → 寫資料 → **等 `txdone()`** → 放低 DE 回接收。
  `_Rs485Uart._wait_sent()` 已經這樣做，這部分是對的，不用改。

`machine.UART` 目前**沒有** `de=` / `rs485=` 參數（kwarg 只有 `baudrate/bits/parity/stop/
tx/rx/rts/cts/txbuf/rxbuf/timeout/timeout_char/invert/flow`），所以方向腳只能靠 Python 手動
拉高拉低。底層 ESP-IDF 其實有 `uart_set_mode(RS485_HALF_DUPLEX)`，只是 MicroPython 沒包出來。

## 6. codebase 裡互相矛盾的延遲值

同樣的接線、同樣的「使能穩定」延遲，寫了 4 個不同版本：

| 檔案 | 使能延遲 | 註解 |
|---|---|---|
| `slave/driver/uart_drv.py:76`（生產用） | **20ms** | 「20ms 才穩定，10ms 丟回覆開頭」 |
| `test/protocol/bench_tx.py:210` | 10ms | 「掃描 20→2ms，8ms 以上全通、6ms 以下才開始丟」 |
| `test/protocol/circuit_bus_host.py:60` | 2ms | 「驅動器使能穩定」 |
| `test/protocol/circuit_bus_recv.py:66` | 2ms | 同上 |
| `test/protocol/circuit_bus_link.py:52` | 2ms | 「半自動方向模組需 ~2ms」 |

兩句註解互相打架：driver 說「10ms 會丟回覆開頭」，bench_tx 說「8ms 以上全通、10ms 安全」。
同一個東西，一個說 20、一個說 8。這代表 20ms 是當時某次實驗沒收斂、後來被保守釘死的值，
不是硬體真正的下限。

## 7. 真正的根因：硬體使能時間

一個裸的 MAX485 / SP485，DE 使能時間約 **100ns～2μs**，根本不需要 ms 級。
你的模組需要 2～20ms 這種量級，幾乎可以肯定是以下其中一種：

1. **光耦隔離型 RS485 模組**：隔離電源要建立、光耦要導通，ms 級延遲是物理事實，
   軟體救不了，只能量出真實值。
2. **「自動方向」模組**（code 註解寫 ZY-SP485 是半自動）：它內部本來就會偵測 TX 線自動切方向。
   這種模組**不該再手動拉 EN**，手動 EN 會跟內部自動電路打架，表現出來就是「拉不夠久會丟開頭」。
3. **總線偏壓電阻太大 / 線太長**：bus 回正（turnaround）慢，DE 提早釋放或太晚建立都會吃掉開頭。

「10ms 會丟回覆開頭」的真正機制不是 MicroPython 慢，而是 DE 使能時間不夠 → 收發器還沒真正
驅動總線 → 回覆第一個 byte 的 start bit 沒被乾淨送出 → 對端 parser 失步 → 看起來像「回覆開頭被吃掉」。

## 8. 解決方案

### 方案 A — ESP-IDF 原生 RS485 半雙工（根治，軟體延遲歸零）

在 `machine_uart.c` 加一個 `rs485=True`（或 `de=`）參數，內部呼叫
`uart_set_mode(RS485_HALF_DUPLEX)`，並把 DE 腳接成 RTS。ESP32 硬體會在**第一個 bit 前
自動拉 RTS、在 `TX_DONE` 中斷自動放低**（`uart.c:1449-1452`，與 `txdone()` 同一個中斷），
還會順便 `rxfifo_rst` 清掉自己的回波。

這樣 `sleep_ms(20)`、`_wait_bus_quiet`、`_wait_sent` 全部可以刪掉，DE 時序由硬體精準控制。
前提：模組若是光耦隔離型，物理使能延遲仍在，但至少軟體這 20ms 會消失。

### 方案 B — config 可設定 + 掃描最小穩定值（最快，純 Python）

把 `sleep_ms(20)` 換成讀 config 的值，並用 `test/protocol/rs485_de_scan.py` 在真實硬體上
從 0ms 往上掃，取「最小 100% 穩定值 + 1ms 餘量」。你已有 2ms 能跑的證據（circuit_bus），
實際值應遠小於 20ms。

### 方案 C — 確認模組類型

- 半自動模組：試試**完全不接／不驅動 EN**（讓它自己偵測 TX），或確認 EN 極性。
- 隔離模組：量真實 enable 延遲，接受它或換模組。

## 9. 測試腳本使用說明

`test/protocol/rs485_de_scan.py` — 兩塊板「一掃一反射」，量出最小穩定 DE settle。

**接線**（每塊板各接一顆 RS485 收發器，A-A / B-B / GND 共地）：

```
GPIO8 = TX → 收發器 DI     (MCU 送出)
GPIO9 = RX ← 收發器 RO     (MCU 收到)
GPIO7 = EN → 收發器 DE+RE  (active-high：1=發送, 0=接收)
```

**部署**：兩塊板都上傳同一支檔案，把最上面的 `MODE` 寫死不同值：

- `MODE = "SCAN"` — 掃描端：對 `SWEEP_MS` 的每個 settle 值做 `ROUNDS` 次 ping-pong，
  統計回覆成功率，最後印出「最小 100% 穩定值」。
- `MODE = "REFLECT"` — 反射端：收到一幀就原樣回傳（settle 固定 `FIXED_SETTLE_MS`）。
  **反射端務必已知穩定**，這樣掃到的失敗才歸因於掃描端自己的 settle。

改名 `main.py` 丟根目錄開機自動跑，或 REPL `exec(open("rs485_de_scan.py").read())`。

**判讀**：

- 某個 settle 值 `ok == ROUNDS`（100%）→ 該值可穩定送出。
- 最小的 100% 值即為「最小穩定 DE settle」，實務上加 1ms 餘量。
- 從 0ms 就 100% → 收發器不需要額外 settle（純 MAX485/SP485 通常如此）。
- 一路到 20ms 都 < 100% → 問題不在 settle，是接線／極性／終端電阻／總線偏壓。

## 10. 參考檔案

- `slave/driver/uart_drv.py` — `_Rs485Uart` 方向控制（含寫死的 20ms）
- `test/protocol/rs485_de_scan.py` — DE settle 掃描腳本（本文檔第 9 節）
- `test/protocol/bench_tx.py`、`circuit_bus_host.py`、`circuit_bus_recv.py`、`circuit_bus_link.py` — 各版本使能延遲
- `lib/micropython/ports/esp32/machine_uart.c` — UART 的 MicroPython 綁定
- `lib/esp-idf/components/esp_driver_uart/src/uart.c` — ESP-IDF UART driver（FIFO/中斷、RS485 模式）
- `lib/esp-idf/components/esp_driver_uart/include/driver/uart.h` — `uart_set_mode` / `uart_set_rts`
