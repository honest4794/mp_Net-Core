# Master↔Slave RS485 UART 規格（客戶版）

> 最後核對：2026-08-22
> Timer 參考：[`external_uart/協議規格_timerUART.md`](../external_uart/協議規格_timerUART.md)
> payload schema 定義：[`firmware/shared/schema/slave_uart_commands.json`](../../../firmware/shared/schema/slave_uart_commands.json)

---

## 〇、一分鐘了解整套通訊

| 角色 | 職責 |
|---|---|
| **Master** | 總指揮：決定播什麼、何時開始 |
| **Slave 1–20** | 執行端：本地跑燈效、motor、LED 及狀態回報 |

```text
Timer（外部面板） --UART5 bytes--> Master
Master --RS485 UART (half-duplex)--> Slave 1–20
Slave 狀態/ACK --> Master
```

**三個要點：**

1. Master 不逐格傳像素，只傳「要播什麼、何時開始、亮度參數」。
2. 全部 Slave 同時收到同一份 `MODE_SET/NEXT`，用共用 `master_start_ms` 做同步起點。
3. 本專案 tracked 設定目前選用 NC4 RS485（`SLAVE_TRANSPORT_NC4=1`）；本文件的 legacy frame 只作退路。NC4 正式規格見 `../external_uart/協議規格_NC4UART.md`。

---

## 一、硬體接線

| ESP32-S3 腳位 | RS485 模組腳位 | 說明 |
|---|---|---|
| `GPIO14`（UART TX） | RXD | ESP32 傳送到 RS485 模組，UART 交叉接線 |
| `GPIO15`（UART RX） | TXD | ESP32 接收 RS485 模組資料，UART 交叉接線 |
| `GPIO16` | EN / DE_RE | `HIGH=發送`、`LOW=接收` |
| `5V` | VCC | 目前專案使用的新 RS485 模組供電 |
| `GND` | GND | 必須共地 |

- 總線方向：Master → Slave1 → Slave2 … → Slave20（daisy chain）
- 總線連接為 `A→A`、`B→B`，再加 GND
- 正式安裝建議：Master 與最後一節點各放 120Ω 終端電阻，中間節點不放
- 開機時 `EN` 預設要保持 `LOW`（接收）

---

## 二、RS485 幀與參數

### 1. 傳輸條件

- Legacy UART baud：固定 `115200`
- NC4：平時／開機 `115200`；只在單一 Slave OTA DATA 階段協商到 `460800`，完成或失聯後回 `115200`
- 格式：`8N1`
- half-duplex，Master 與 Slave 共用同一收發線路
- master/slave 皆用同一 frame 合約

### 2. wire 形式（含前導）

```text
[0x55 × 10][0x02 0xFF] [STX][VER][ADDR][CMD][SEQ_LO][SEQ_HI][LEN][PAYLOAD][CRC32_LE][ETX]
```

- `0x55 × 10`：preamble
- `0x02 0xFF`：guard，用來幫 parser 重新對齊
- `STX=0x02`、`ETX=0x03`
- `VER=0x01`
- `LEN`：payload 長度 `0~240`
- `CRC32_LE`：frame CRC32 little-endian

計算：

- protocol frame 長度 = `12 + L`（`L = payload bytes`）
- wire 長度 = `24 + L`

### 3. Address 與回覆規則

| 欄位 | 含意 |
|---|---|
| `ADDR=0x00` | broadcast，Master 給所有 Slave，**不可回覆** |
| `ADDR=0x01..0x14` | 指定 Slave，**可回覆** |

- `SEQ` 為 `u16` transaction 序號，用來匹配 request/reply
- 重要命令（`MODE_SET`、`MODE_NEXT`、`MODE_STOP`）有重複發送保護；Slave 只做去重執行一次
- 通常 timeout `50ms`，最多重試 `3` 次

### 4. CRC 與字節序

- CRC32 算法：IEEE CRC-32，poly `0xEDB88320`
- 輸入 bytes：`VER, ADDR, CMD, SEQ_LO, SEQ_HI, LEN, PAYLOAD`
- Little-endian 是共通規則（`LEN` payload、`u16/u32/i32` 全部採 LE）

---

## 三、核心命令（縮圖）

| CMD | 方向 | 重要欄位 | 備註 |
|---|---|---|---|
| `0x01 MODE_SET` | Master→Slave | `mode_id:u8`, `master_start_ms:u32` | 指定模式並安排起點 |
| `0x02 MODE_NEXT` | Master→Slave | `mode_id:u8`, `master_start_ms:u32` | 自動前進下段 |
| `0x03 MODE_STOP` | Master→Slave | 無 | 停止並重設狀態 |
| `0x04 BRIGHTNESS` | Master→Slave | `value:u8`（1..190） | 實際亮度 |
| `0x05 STORY_SET` | Master→Slave | `set_type:u8`（0=LED,1=SERVO） | |
| `0x08 AUDIO_LEVEL` | Master→Slave | `level:u8`, `beat:u8` | |
| `0x09 AUDIO_ACTIVE` | Master→Slave | `active:u8` | |
| `0x10 STATUS_QUERY` | Master→Slave | 無 | Slave 回 `STATUS_REPORT` |
| `0x11 STATUS_REPORT` | Slave→Master | `state:u8`, `reported_mode_id:u8` | |
| `0x12 PROBE` | Master→Slave | 無 | Slave 回 `PROBE_REPLY` |
| `0x20 TIME_SYNC_REQUEST` | Master→Slave | `time_ms:u32` | 通常 broadcast |
| `0x21 TIME_SYNC_REPLY` | Slave→Master | `received_at_ms:u32` | 配對 `SEQ` |
| `0x22 TIME_OFFSET_APPLY` | Master→Slave | `offset_ms:i32` | 寫入本地 offset |
| `0x32 LIVE_TEXT` | Master→Slave | text payload | 即時調節，含 `StorySet:`、`Brightness:` 等 |
| `0x40 OTA_COMMAND` | Master→Slave | chunk payload | OTA 專用 |
| `0x41 OTA_RESPONSE` | Slave↔Master | chunk/state | OTA 回報與重試 |

> `payload` 對應欄位與長度皆以 schema 為準，實作以 generated definitions 驗證。

---

## 四、Timer UART 對 RS485 的映射

Timer 傳入 5-byte frame `[0xB4][b1][b2][b3][0xFF]` 後，Master 不會原封轉發。
Master 只會把變化內容轉成 RS485 command：

- `b1 bit6` 有變更 → `STORY_SET`
- mode 有變更 → `MODE_SET/MODE_NEXT`
- brightness 有變更 → `LIVE_TEXT: Brightness: N`（目前實作）
- `loop/remaining` 只影響 Master 本地倒數，不傳給 Slave

Mode 變更流程（實際）：

1. `TIME_SYNC_REQUEST`（broadcast）
2. `StorySet`（如有）
3. `MODE_SET / MODE_NEXT`
4. `Brightness`（如有）
5. 回報 Timer 狀態給外部面板

---

## 五、跨 Slave 同步邏輯

- Master 在轉段前先廣播一次 coarse sync，設定 `master_start_ms = now + 300`
- 每台 Slave 用自己 offset 計算：

```text
local_start_ms = master_start_ms + offset_ms
```

- Slave 不會一收到指令即開跑；會等 `scheduledLocalStartMs` 到點再重置 state 開始
- 正常目標：同段起步差 ≤5ms；超過 10ms 視為異常

### 對時方式

- 背景：round-robin 一顆一顆 `TIME_SYNC_REQUEST` / `TIME_SYNC_REPLY`（midpoint 演算法）
- 穩定時每顆約 1Hz；offset 異常時暫提升到 5Hz
- Mode 前還會有一輪 broadcast 粗校時輔助

---

## 六、Clock/Status/斷線行為

### 1. 主要狀態

- Slave 報回的 state：`UNKNOWN / IDLE / RUNNING / COMPLETED / DEV`
- Master 只採用合法 payload 的回覆；不合法 frame 直接丟棄並保留上次狀態
- 無法收到有效回覆時增加 timeout，超過閾值後將 slave 判為暫時離線

### 2. Status 取樣策略

- 平時約每 3 秒一次
- mode 轉換後前 5 秒加速到約 0.5 秒一次
- 目標是先維持可用健康度，再平衡 bus 壓力

---

## 七、OTA（RS485）

- `MOTOR` 與 `Slave` 的 OTA 仍沿用既有 OTA state machine
- 每個 DATA chunk 含 CRC、序號與 ACK；失敗可重試
- RS485 layer 限制 payload ≤240 bytes（wire 上限 264）
- 建議 chunk 以 224 bytes 送 OTA 資料，對應外層一個 frame 可含 `8-byte` 內層 OTA header/CRC
- 目標重傳策略：單一 Slave 失敗最多 2 次；`reboot_failed` 不重傳已通過 CRC 的韌體

NC4 env 另有 runtime baud 握手：

| 階段 | Baud | 規則 |
|---|---:|---|
| 開機／VERSION | 115200 | 所有 Slave 共用的正常值 |
| `0x3309/0x330A` PREPARE/READY | 舊 baud | 只單播目標 Slave，READY 送完後等 20ms |
| BEGIN／WRITE／END | 460800 | 新 Slave 快速路徑；舊 Slave 不認命令便維持 115200 |
| RESTORE／APPLY／reboot | 115200 | APPLY 前必須 normal probe 成功 |
| 快速鏈路失聯 | 5 秒內回 115200 | Slave fallback lease；Master 本機亦強制恢復 |

`0x3309/0x330A` 暫屬本專案 `fastled_custom`，不是 upstream System command。legacy `SLAVE_TRANSPORT_UART` 不使用這兩條命令。

---

## 八、實測紀錄（更新）

### 2026-08-13（參考）
- Master、Slave7、Slave3 三板實測完成，完成 EN polarity、reply delay、timeout 驗證
- 起始同步可達到 ≤5ms 目標
- 兩段現場資料顯示 status/clock/OTA 尚待完整壓力測試，但主要串接邏輯已可用

### 2026-08-17（實測摘要）
- 裝置：
  - Master `/dev/cu.usbmodem1127101`
  - Slave1 `/dev/cu.usbmodem1127201`
  - Slave20 `/dev/cu.usbmodem1127401`
- 設定：
  - `SLAVE_UART_BAUD=115200`
  - `SLAVE_UART_CONFIGURED_SLAVE_NUM=20`
  - `SLAVE_UART_CONFIGURED_SLAVE_MASK=0xFFFFF`（正式）
- clean bench（`0x80001`）結果：
  - timeout / retry / frame_error：`0`
  - RTT 約 `7–28 ms`
  - mode start 差約 `1–3 ms`
- 全量 mask 下只接兩片時會有預期 timeout（未上電 slave 的 missing reply）
- 目前已知行為偏差：Master timer 倒數與 Slave 真正開始仍有約 300ms timing 差，屬邏輯層面事項（非串流層面）

### 2026-08-21（NC4 RS485 方向速度）

- 時間：2026-08-21 03:44–04:24、09:00–10:00、14:18–14:31（Asia/Hong_Kong）
- 設備：ESP32-S3 Master、Slave1、Slave2；GPIO14／15／16；硬體 DE
- 115200 hardware RS485 現版：`300／250／200／150／100／0us` 均完成中途轉 StoryMode；`0us` 另完成 1,674 次固定壓測，新增 timeout／bad frame／dropped 全為 0
- turnaround gap 定義：Master 最後一個 request byte `flush()` 完成，到看見 Slave 第一個 response byte；不是完整 RTT
- 最快實測 turnaround gap：`2.593ms`；本輪最慢成功樣本 `40.631ms`
- `0us` 是本機極限測試值；115200 正式值維持 `SLAVE_UART_REPLY_DELAY_US=1000`，Master response timeout 維持 `50ms`
- 9600：`1000us` 的 41 筆 RTT 為 39.84–60.60ms、0 新增 timeout；`20000us` 在 30s 內至少 14 次 timeout
- 現象：`bad_frame` 仍為 0，但 Slave 回覆得太遲，Master 等滿 50ms 後便當作離線；問題在收發換向時間，不是 CRC 壞幀
- 隊友目前同樣使用 `115200`；他觀察到的 `20ms` 是另一套實機切換 RS485 收發方向的結果，`9600` 是準備再測的比較項目
- 本機另測 `9600 + 20ms` 會把總時間推過目前 50ms response timeout；兩邊需先對齊硬體、timeout 和 20ms 的插入位置才可直接比較
- 壓測設定：`NC4_RS485_TIMING_DIAGNOSTICS=1`、`NC4_RS485_STATUS_POLL_INTERVAL_MS=10`；正式輪詢間隔仍為 3000ms
- 完整表：`../external_uart/NC4_UART_實機驗收_2026-08-20.md` §4.6

### 2026-08-22（NC4 OTA 動態 baud 軟體驗證）

- 時間：2026-08-22（Asia/Hong_Kong）
- 設備：macOS host compiler、PlatformIO ESP32-S3 `master`／`slave1`／`slave2`／`slave_standalone`；未接實體硬件
- 現象：0x3309/0x330A codec、20ms 切速、5 秒 fallback、session echo、舊 Slave 115200 fallback、APPLY／中止前恢復 contract 均通過；四個 firmware 環境 build 成功
- 結論：程式與 wire contract 可建置；460800 實機 OTA 時間、SHA、slot 與 reboot 尚未驗收，不列實機 PASS

---

## 九、相容 I2C（僅參考）

當 `SLAVE_TRANSPORT_UART=0` 時改走 I2C，Master 對每顆 Slave 以 ASCII 指令傳送。
I2C 不再使用 STX/CRC/ETX frame、無 broadcast 回覆機制，使用 `Slave address` 逐顆控制。
該模式屬降階相容，正式文件仍以 RS485 為主。

---

## 十、關聯程式入口

- `firmware/master/src/slaveTransportUart.cpp`（frame send/receive）
- `firmware/shared/src/transport/slave_uart_protocol.cpp`（encode/parse/CRC）
- `firmware/slave/src/slaveTransportUart.cpp`（dispatch、offset、reply）
- `firmware/shared/schema/slave_uart_commands.json`（命令 schema）
- `firmware/shared/include/transport/generated/slave_uart_schema_generated.h`（build-time generated）
