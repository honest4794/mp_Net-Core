# Pixel / Mode 指令整合規格（0x31XX）

> 兩邊共同閱讀與執行之合約文件。
> 基準：**mp_Net-Core（本專案）** 之 schema 與 NC4 封包為準，對方（fastLED master_timer_slave）遷就我方實作。
> 狀態：草案 v0.2 — 2026-08-18
> 對應 schema：`slave/schema/pixel.json`（時鐘同步見 `slave/schema/sys.json`）

---

## 0. 一分鐘結論

整合後，模式播放控制統一收斂為 6 個指令（0x3101 ~ 0x3106），取代對方 RS485 的
`MODE_SET / MODE_NEXT / MODE_STOP / POWER_OFF / POWER_ON / STATUS_QUERY / STATUS_REPORT / STORY_SET` 整組。

| 我方新指令 | 取代對方 |
|---|---|
| `MODE_LIST_QUERY/RSP` | 無（新增，對方原本沒有模式清單查詢） |
| `MODE_GET/RSP` | `STATUS_QUERY / STATUS_REPORT`（取回 mode_type、mode_id、時間與運行狀態） |
| `MODE_SET` | `MODE_SET` + `MODE_NEXT` + `STORY_SET`（`mode_type` 欄位同時選組別） |
| `MODE_STOP` | `MODE_STOP` + `POWER_OFF`（`action` 欄位區分暫停／全關閉） |

`MODE_SET.start_delay_ms` 用「相對延遲」做**開始同步**（Slave 收到後延遲 N ms 統一開始）。
時鐘同步（`TIME_SYNC_*`）**併入 `sys.json`（0x10xx）**，見 §4，屬選用。

---

## 1. 指令總表

| CMD | 名稱 | 方向 | Payload |
|---:|---|---|---|
| `0x3101` | `MODE_LIST_QUERY` | Master → Slave | (空) |
| `0x3102` | `MODE_LIST_RSP` | Slave → Master | `count:u8`, `entries:bytes_rest` |
| `0x3103` | `MODE_GET` | Master → Slave | (空) |
| `0x3104` | `MODE_GET_RSP` | Slave → Master | `mode_type:u8`, `mode_id:u8`, `elapsed_ms:u32`, `total_ms:u32`, `running:u8` |
| `0x3105` | `MODE_SET` | Master → Slave | `mode_type:u8`, `mode_id:u8`, `start_delay_ms:u16` |
| `0x3106` | `MODE_STOP` | Master → Slave | `action:u8` |

---

## 2. 指令詳細定義

### 2.1 `mode_type` 語義（全指令共用）

> **設計意圖**：`mode_type` 與 `mode_id` **兩欄綁定**，合起來才是模式的唯一識別碼
> （等同一個 16-bit key 拆成高／低兩欄，避免直接用 u16）。凡是提到「模式 ID」，
> 都是指 `(mode_type, mode_id)` 這一對；單獨一個 `mode_id` 沒有意義。

| mode_type | 意義 | mode_id 語義 |
|---:|---|---|
| `0` | 系統模式（自檢、UNKNOWN、DEV） | `0`=UNKNOWN、`1`=DEV |
| `1` | LED 組模式（原 `STORY_SET.set_type=0`） | LED 模式表內索引 |
| `2` | SERVO 組模式（原 `STORY_SET.set_type=1`） | SERVO 模式表內索引 |
| 3–255 | 保留 | — |

- `mode_type=0` 只出現在 `MODE_GET_RSP`（Slave 回報 DEV／UNKNOWN）；Master **不能**用 `MODE_SET` 指定它。
- 原 `STORY_SET`（LED/SERVO 切換）已併入：LED=`1`、SERVO=`2`，不再有獨立指令。
- `mode_id` 空間是 per-mode_type 的：`(1, 0)` 與 `(2, 0)` 是不同模式，互不衝突。

### 2.2 `MODE_LIST_QUERY`（0x3101）／`MODE_LIST_RSP`（0x3102）

查**模式列表**：有多少套模式、每套的完整 ID、總時間、名稱。一次查詢、一次回覆，不分段。

```json
{ "cmd": "0x3101", "name": "MODE_LIST_QUERY", "payload": [] }
{ "cmd": "0x3102", "name": "MODE_LIST_RSP", "payload": [
  {"name": "count",   "type": "u8"},
  {"name": "entries", "type": "bytes_rest"}
]}
```

- **一次回覆全部可播放模式**（LED 組 + SERVO 組），不分組查詢、不逐個查詢。
- 每個 entry 同時含綁定的 `(mode_type, mode_id)`、時間、名稱，順序一致，不需另外對齊三個表。
- `entries` 自訂子格式（schema 無 list 型別）：

```text
entries = concat( entry[0..count-1] )
entry:
  mode_type: u8     綁定 key 高位（1=LED、2=SERVO）
  mode_id:   u8     綁定 key 低位（該組內索引，0 起）
  total_ms:  u32    little-endian，模式總時間（毫秒）
  name_len:  u16    little-endian，名稱長度（bytes）
  name:      utf8   name_len bytes，模式名稱（可為中文）
```

- Master 拿到任一筆的 `(mode_type, mode_id)`，可直接原樣丟進 `MODE_SET`。
- `count` 上限 64。名稱可為空（`name_len=0`）。
- 以對方 fastLED 而言：LED 組 `storyModes` 約 12 個燈效、SERVO 組 `servoStoryModes` 2 個機械模式，全部合併於一次回覆。
- 範例（2 個模式）：
  `02 | 01 | 00 | 00 00 00 00 | 0C 00 | "預設模式(12B)" | 02 | 00 | 01 00 00 00 | 1E 00 | "復位模式"`

### 2.3 `MODE_GET`（0x3103）／`MODE_GET_RSP`（0x3104）

查目前執行狀態。

```json
{ "cmd": "0x3103", "name": "MODE_GET", "payload": [] }
{ "cmd": "0x3104", "name": "MODE_GET_RSP", "payload": [
  {"name": "mode_type", "type": "u8"},
  {"name": "mode_id",   "type": "u8"},
  {"name": "elapsed_ms","type": "u32"},
  {"name": "total_ms",  "type": "u32"},
  {"name": "running",   "type": "u8"}
]}
```

**`running` 語義：**

| running | 意義 |
|---:|---|
| `0` | 模式未在執行（未開始、暫停中、已播完等待） |
| `1` | 模式正在執行（`elapsed_ms` 持續增加） |

- `elapsed_ms`：Slave 本機時鐘自本次模式開始以來的毫秒數，**不會超過 `total_ms`**。
- `total_ms`：目前模式總時間（=`MODE_LIST_RSP.total_ms`）。`0` 表示不設限（如 DEV／常駐模式）。
- 播完判定：`running=0` 且 `elapsed_ms >= total_ms`（由 Master 推得，見 §5 待決）。
- **沒有「無模式」狀態**：開機／未收到任何指令的預設回覆為
  `mode_type=1, mode_id=0, elapsed_ms=0, total_ms=<mode0總長>, running=0`。
- 進入 DEV：`mode_type=0, mode_id=1`。

### 2.4 `MODE_SET`（0x3105）

指定模式與開始時間。**唯一**的模式切換指令（MODE_NEXT、STORY_SET 皆已併入）。

```json
{ "cmd": "0x3105", "name": "MODE_SET", "payload": [
  {"name": "mode_type",      "type": "u8"},
  {"name": "mode_id",        "type": "u8"},
  {"name": "start_delay_ms", "type": "u16"}
]}
```

- `mode_type`：`1`=LED、`2`=SERVO（與 `mode_id` 綁定，合起來指定唯一模式）。
- `mode_id`：與 `mode_type` 綁定，該組內模式索引；`(mode_type, mode_id)` 須在 `MODE_LIST_RSP` 清單內；超出 → Slave 忽略並維持原模式。
- `start_delay_ms`：**收到指令後延遲多少毫秒開始**（相對時間，`0`=立即）。
  Master 廣播時全部 Slave 同時收到、同時延遲、同時開始，同步度只取決於傳輸 jitter，
  **不需要時鐘同步即可起步**（時鐘同步為選用，見 §4）。
- 收到 `MODE_SET` 即離開 DEV、離開省電、解除暫停；若在暫停中則**重頭開始**播放新模式。
- Slave 執行後回 `MODE_GET_RSP` 作為 ACK。

### 2.5 `MODE_STOP`（0x3106）

停止目前模式，取代 `MODE_STOP` 與 `POWER_OFF`。

```json
{ "cmd": "0x3106", "name": "MODE_STOP", "payload": [
  {"name": "action", "type": "u8"}
]}
```

| action | 意義 | 行為 |
|---:|---|---|
| `0` | 暫停（Pause） | 停止目前模式燈效與馬達，保留模式狀態（`running=0`）；恢復＝再下 `MODE_SET`（重頭開始） |
| `1` | 全關閉（Power Off） | 停止 + 清燈 + 進入省電；開 WiFi／OTA 前 Master 必下此動作 |

- 其他值保留。執行後回 `MODE_GET_RSP` 作為 ACK。

---

## 3. 行為約定（雙方共同遵守）

1. **預設狀態**：不存在「no-mode」；預設為 `mode_type=1, mode_id=0, running=0`。
2. **DEV**：Slave 連續約 10 秒收不到有效通訊 → 進入本機測試模式；
   `MODE_GET_RSP` 回 `mode_type=0, mode_id=1`。收到 `MODE_SET`／`MODE_STOP` 即離開 DEV。
3. **UNKNOWN**：Master 收不到回覆、或收到非法 payload → 視為 `mode_type=0, mode_id=0`，
   保留上次有效狀態，不據此跳段。
4. **模式範圍**：`MODE_SET` 的 `(mode_type, mode_id)` 超出清單 → 忽略；`MODE_LIST_RSP` 是唯一 ID 來源。
5. **暫停恢復**：暫停後一律用 `MODE_SET` 恢復，**重頭開始**（無續播約定）。
6. **名字編碼**：`MODE_LIST_RSP.name` 為 UTF-8（可含中文）。
7. **Broadcast**：`MODE_SET`／`MODE_STOP` 支援廣播（ADDR=0 ／ NC4 `0xFFFF`）；
   廣播時 Slave 不回覆；`MODE_GET`／`MODE_LIST_QUERY` 為指定單播，必回覆。
8. **Slave 被動原則**：Slave 不主動推送任何資料；所有回覆都是回應 Master 的查詢／動作。

---

## 4. 時鐘同步（選用，已併入 `sys.json` 0x10xx）

時鐘同步不負責「同時開始」（那是 `MODE_SET.start_delay_ms` 的事），只負責：**讓所有 Slave
的時鐘對齊到 Master**，用於跨 Slave 的 `elapsed_ms` 一致性，以及未來絕對時間排程的地基。

| CMD | 名稱 | 方向 | Payload |
|---:|---|---|---|
| `0x100A` | `TIME_SYNC` | Master → Slave（可廣播） | `master_time_ms:u32` |
| `0x100B` | `TIME_SYNC_RSP` | Slave → Master | `received_at_ms:u32` |
| `0x100C` | `TIME_OFFSET_APPLY` | Master → Slave | `offset_sign:u8`, `offset_ms:u32` |

- `master_time_ms`：Master 送出此指令當下的 `millis()`。
- `received_at_ms`：Slave 收到 `TIME_SYNC` 當下的本機 `millis()`。
- `offset_sign`：`0`=正（Slave 快於 Master）、`1`=負（Slave 慢於 Master）；`offset_ms`=偏移絕對值。
- 用「符號 + 量值」兩欄（runtime schema 無 `i32` 型別）。

**流程：**

```text
Master 定期(約 1Hz，異常時 5Hz) round-robin 對每顆 Slave:
  1. TIME_SYNC { master_time_ms }
  2. Slave 收到 → 本機存 offset = 收到時機(millis) - master_time_ms → 回 TIME_SYNC_RSP
  3. Master 收 RSP，量 RTT；若 offset 異常，回 TIME_OFFSET_APPLY 覆寫 Slave 端 offset
```

- 此組為**選用**：若只用 `start_delay_ms` 起步、`elapsed_ms` 純顯示，可完全不呼叫。

---

## 5. 待決事項（整合會議拍板）

| # | 問題 | 現況 | 影響 |
|---|---|---|---|
| 1 | 播完（COMPLETED）如何表達 | 草案：`running=0` + `elapsed>=total` 由 Master 輪詢推得 | 對方原「全部 slave 播完 → 提早跳段」機制退化成輪詢式 |
| 2 | `mode_type=2+` 是否留給 COMPLETED 等 | 目前 SERVO=2 已用；3+ 保留 | 若要「播完當下主動通知」，需新值或新指令 |
| 3 | 亮度（brightness）走哪條通道 | 暫不併入 `MODE_SET` | 沿用現有亮度指令（對方 `BRIGHTNESS`／我方 `WTT_CTL`），另案統一 |
| 4 | 暫停後續播 | 目前一律重頭開始 | 若要續播，`MODE_SET` 需加 `resume_from_ms` 欄位 |

---

## 6. 對方（fastLED）實作對照

| 我方欄位 | 對方現成資料來源 |
|---|---|
| `MODE_LIST_RSP` entries | `storyModes` + `servoStoryModes` 的 `STORY_MODE_ENTRY(fn, name, seconds)` 兩表合併；entry 的 `mode_type` 由所屬表決定（LED=1 / SERVO=2）；`total_ms = seconds × 1000` |
| `MODE_GET_RSP.mode_id` | `currentModeId` |
| `MODE_GET_RSP.mode_type` | 由 `activeStorySet` 反推（LED=1 / SERVO=2）；DEV 時回 0 |
| `MODE_GET_RSP.elapsed_ms` | 模式開始時記錄一次 `millis()`，差值即 elapsed |
| `MODE_GET_RSP.total_ms` | `STORYMODE_*_TOTAL_SECONDS × 1000` |
| `MODE_GET_RSP.running` | `enableRunStory`（＋暫停旗標，若實作暫停） |
| `MODE_GET_RSP.mode_type=0, mode_id=1` | `isInDevMode` |
| `MODE_SET.mode_type` | 取代 `STORY_SET`（`set_type`） |
| `MODE_STOP action=1` 等價行為 | 現有 `Power: off` 處理（停 story + 清燈 + `isPowerSaveMode`） |
| `start_delay_ms` | 現有 `scheduledLocalStartMs` 機制（改以「收到後 N ms」計算，取代 masterStart+offset） |

對方**需要刪除或降級**：`MODE_NEXT`（併入 SET）、`STORY_SET`（併入 SET.mode_type）、`POWER_ON`（無對應）、
`STATUS_QUERY/REPORT`（由 MODE_GET 取代）。`TIME_SYNC_*` 保留但改為選用（僅時鐘對齊，不再綁定 MODE_SET 起步）。

---

## 7. 我方（mp_Net-Core）落地步驟

1. ✅ `slave/schema/pixel.json` 已建立（0x3101~0x3106，含 `mode_type`）。
2. ✅ `slave/schema/sys.json` 已併入時鐘同步（0x100A~0x100C）。
3. 新增 `slave/action/pixel_actions.py`：
   - 註冊 `MODE_LIST_QUERY / MODE_GET / MODE_SET / MODE_STOP` 四個 handler。
   - 串接現有播放控制（WTT／PixelController／story 排程）作為真實模式執行體。
4. `slave/action/sys_actions.py` 加入 `TIME_SYNC / TIME_SYNC_RSP / TIME_OFFSET_APPLY`（選用）。
5. `slave/action/registry.py` 加入 `pixel_actions.register(app)`。
6. Server 端 UI／排程改用 `MODE_LIST_QUERY` 取得模式清單、`MODE_GET` 輪詢狀態。
