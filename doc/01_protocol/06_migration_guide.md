# 對方指令遷移對照（人讀版）

> **用途**：對方（fastLED master_timer_slave）**每一條指令**變成我們（mp_Net-Core）整合後的哪一條指令、參數怎麼對、架構怎麼理解。
> **分類**：協議層（01_protocol）
> **最後更新**：2026-08-18
> **基準**：`slave/schema/*.json` 為權威定義；細節見 `03_ota_protocol.md`、`04_pixel_protocol.md`。

---

## 怎麼讀這份文件

每一條對方指令都標一個結果：

| 標記 | 意思 |
|---|---|
| ✅ | 已整合：有明確對應的新指令 |
| 🔀 | 併入：多條舊指令合併成一條新指令 |
| ❌ | 移除：不需要了 |
| ⏸ | 未整合：待決，暫時保留對方原有做法 |
| 🗑 | 不整合：我方明確不建立 |

---

## 1. 架構怎麼變了（先看這節，才看得懂後面的對照）

### 1.1 通訊架構

```text
對方（三層）                          我方（兩層）
Timer（面板）                           Server（面板 / 控制端）
   │ UART 5-byte 幀                        │ NC4 封包
Master（指揮）                             │ 五種 transport：
   │ RS485 或 I2C                         │  WS / UDP / TCP / UART / ESP-NOW
Slave 1–20（執行）                       Slave（執行）
```

- 對方的「Timer→Master」與「Master→Slave」是**兩段不同協議**；我方合併成「Server⇄Slave」一段，用同一套 NC4 封包。
- 對方 Master 這層的「轉譯」工作（把 Timer 按鍵翻譯成模式指令）移到我方 Server 端軟體。

### 1.2 封包格式

| | 對方 RS485 frame | 我方 NC4 封包 |
|---|---|---|
| 開頭 | `0x55×10` preamble + `0x02 0xFF` guard | `"NC"` 2 bytes |
| 版本 | `VER=0x01` | `VER=4` |
| 位址 | 1 byte（0=broadcast, 1–20=Slave ID） | 2 bytes（`0xFFFF`=廣播） |
| 指令 | 1 byte CMD | 2 bytes CMD |
| 序號 | SEQ_LO/SEQ_HI | 無（必要時 payload 內自帶，如 OTA offset） |
| 長度 | 1 byte（0–240） | 2 bytes |
| 檢查 | CRC32（frame 層） | CRC32（`binascii.crc32`，範圍 VER..DATA） |
| 結尾 | `ETX 0x03` | 無（長度欄已知） |

### 1.3 指令空間

- 對方：CMD 只有 1 byte，`0x00~0x71` **一個平面清單**，靠人記住編號。
- 我方：CMD 2 bytes，**按功能分域**，看數字前兩碼就知道是哪一類：

| 域 | 用途 | 域 | 用途 |
|---|---|---|---|
| `0x10xx` | 系統（discover/wifi/task/**時鐘同步**） | `0x22xx` | **OTA**（韌體更新） |
| `0x11xx` | 狀態 | `0x30xx` | Stream（串流） |
| `0x12xx` | 心跳 | `0x31xx` | **PIXEL**（模式播放） |
| `0x13xx` | ESP-NOW | `0x20xx` | File（檔案傳輸） |
| `0x14xx` | 硬體 | | |
| `0x15xx` | WTT（待清理） | | |
| `0x18xx` | RAM 測試 | | |

### 1.4 三個心智模型（理解整套新指令的捷徑）

1. **動作指令 vs 查詢/回覆對**：改狀態用動作指令（`MODE_SET`、`OTA_BEGIN/WRITE/END`）；看狀態用「QUERY → RSP」一對（`MODE_GET → MODE_GET_RSP`、`OTA_VERSION_QUERY → OTA_VERSION_RSP`）。
2. **失敗有統一回覆**：OTA 域任何動作失敗，Slave 一律回 `OTA_ERROR_RSP`，裡面是 11 個**具名 bool**——不用再查「錯誤碼 5 是什麼」。
3. **能自描述的絕不查表**：對方的 bitmask／enum／magic number 全部拆成具名 bool 或獨立欄位（見 §9 OTA）。

---

## 2. 播放控制（→ 0x31xx PIXEL）

| 對方 | 變成 | 參數對應 |
|---|---|---|
| `0x01 MODE_SET` | ✅ `0x3105 MODE_SET` | `mode_id:u8` → `mode_type:u8 + mode_id:u8`（新增 `mode_type` 選組別）；`master_start_ms:u32` → `start_delay_ms:u16`（**語義改變**，見下）；新增 `brightness:u8`（0–30，`0xFF`=不設置） |
| `0x02 MODE_NEXT` | 🔀 併入 `0x3105 MODE_SET` | 兩條 payload 原本就完全相同，只是語義「外部指定 vs 自動前進」；新架構 Master 反正都指定 mode_id，不需要分開 |
| `0x03 MODE_STOP` | ✅ `0x3106 MODE_STOP (action=0)` | 空 payload → `action:u8=0`（暫停） |
| `0x06 POWER_OFF` | 🔀 併入 `0x3106 MODE_STOP (action=1)` | 空 payload → `action:u8=1`（全關閉＋省電） |
| `0x07 POWER_ON` | ❌ 移除 | 新架構「恢復」一律重新下 `MODE_SET`，沒有「恢復舊模式」語義 |
| `0x04 BRIGHTNESS` | ✅ 併入 `0x3105 MODE_SET.brightness` | 對方 `value:u8`（1–190）→ 我方 `brightness:u8`（0–30），`0xFF`=不設置 |
| `0x05 STORY_SET` | 🔀 併入 `0x3105 MODE_SET.mode_type` | `set_type`（0=LED, 1=SERVO）→ `mode_type`（1=LED, 2=SERVO），不再有獨立指令 |

> 模式名稱等細節不再放進列表：`0x3101/0x3102 MODE_LIST_*` 只回 ID + 總時間，
> 名稱用新增的 `0x3107/0x3108 MODE_DETAIL_*` 逐個模式查（對方沒有的新指令，見下）。

**`master_start_ms` → `start_delay_ms` 是整份整合最重要的語義改變：**

```text
以前：Master 下達「絕對開始時間」= 自己 millis() + 300ms，
      Slave 要靠時鐘同步的 offset 換算成自己的本地時間 → 沒對時就不知道何時開始。

現在：Master 下達「收到後延遲 N ms 開始」（相對時間），
      Slave 收到後自己倒數 N ms 就開跑。廣播時大家都同時收到、
      同時延遲、同時開始 → 不需要時鐘同步也能同步起步。
```

另外新增兩條對方沒有的指令：

| 新指令 | 用途 |
|---|---|
| `0x3101/0x3102 MODE_LIST_QUERY/RSP` | 查**指定組別**嘅模式清單（數量、每套模式的 ID 與總時間）。`MODE_LIST_QUERY` 帶 `mode_type`（0=全部、1=LED、2=SERVO），`MODE_LIST_RSP` 回音 `mode_type`。一次查詢、一次回覆。 |
| `0x3107/0x3108 MODE_DETAIL_QUERY/RSP` | 逐個查**單一模式**細節（總時間、名稱 UTF-8）。名稱唔入列表，避免列表 payload 變大 |

`MODE_LIST_RSP` 的 `entries` 是自訂子格式（schema 沒有 list 型別）；每筆 entry 固定 6 bytes，可直接原樣丟進 `MODE_SET`（0x3105）或 `MODE_DETAIL_QUERY`（0x3107）：

```text
每筆 entry = mode_type:u8 + mode_id:u8 + total_ms:u32   (固定 6 bytes)
```

---

## 3. 狀態（STATUS → MODE_GET）

| 對方 | 變成 | 參數對應 |
|---|---|---|
| `0x10 STATUS_QUERY`（空 payload） | ✅ `0x3103 MODE_GET`（空 payload） | 一樣是「問目前狀態」 |
| `0x11 STATUS_REPORT` | ✅ `0x3104 MODE_GET_RSP` | 見下 |

```text
對方回：state:u8 (五態) + reported_mode_id:u8
我方回：mode_type:u8 + mode_id:u8 + elapsed_ms:u32 + total_ms:u32 + running:u8
```

**state 五態 → 新欄位**（這是理解上最容易混淆的地方）：

| 對方 state | 意義 | 新架構怎麼表達 |
|---|---|---|
| `UNKNOWN`（0） | 無有效狀態 | `mode_type=0, mode_id=0` |
| `DEV`（4） | 失聯，進本機測試模式 | `mode_type=0, mode_id=1` |
| `RUNNING`（2） | 正在執行 | `mode_type=1 或 2, running=1`（LED=1 / SERVO=2） |
| `IDLE`（1） | 沒在播（我方不存在此狀態） | `mode_type=1, mode_id=預設0, running=0` |
| `COMPLETED`（3） | 播完了 | `running=0` 且 `elapsed_ms >= total_ms`（由 Master 推得） |

> 重點：新架構**沒有「沒有模式」的狀態**，預設就是 mode 0。五態被拆成兩個維度：
> 「哪一類／哪一組模式」（`mode_type`：0=系統、1=LED、2=SERVO）+「跑不跑」（`running`）。
> 原 `STORY_SET`（LED/SERVO 組別）也一併收進 `mode_type`，不再有獨立指令。

---

## 4. 時鐘同步（→ 0x10xx SYNC，選用，已併入 sys.json）

| 對方 | 變成 | 參數對應 |
|---|---|---|
| `0x20 TIME_SYNC_REQUEST` | ✅ `0x100A TIME_SYNC` | `time_ms:u32` → `master_time_ms:u32`（同義） |
| `0x21 TIME_SYNC_REPLY` | ✅ `0x100B TIME_SYNC_RSP` | `received_at_ms:u32`（同義） |
| `0x22 TIME_OFFSET_APPLY` | ✅ `0x100C TIME_OFFSET_APPLY` | `offset_ms:i32` → `offset_sign:u8 + offset_ms:u32`（拆兩欄，因 runtime 無 i32 型別） |

**地位改變（重要）：**

```text
以前：時鐘同步是起步的必備前置（MODE_SET 的 master_start_ms 要靠它換算）。
現在：起步用 start_delay_ms（相對延遲），跟時鐘同步無關。
      時鐘同步變成「選用」，只做兩件事：
      1. 讓跨 Slave 的 elapsed_ms 可以互相比較
      2. 未來若要絕對時間排程，有地基在
```

---

## 5. 在線確認（PROBE → 我方既有功能）

| 對方 | 變成 | 說明 |
|---|---|---|
| `0x12 PROBE` | ✅ 我方既有 `0x1001 DISCOVER` | 功能等價：確認在線。我方 Server 開機時主動 discover，對方是 Master 主動 poll，方向相反但目的相同 |
| `0x13 PROBE_REPLY` | ✅ 我方既有 `0x1002 SLAVE_ANNOUNCE` | 我方回覆帶 `slave_id / pixel_count / hw_version`，資訊比對方多 |

不需要新指令。

---

## 6. 維修與 Live（INFO / LIVE：不整合）

| 對方 | 結果 | 說明 |
|---|---|---|
| `0x30 INFO_QUERY` / `0x31 INFO_REPLY` | 🗑 不整合 | 查硬體資料（`INFO:PWR / RGB / IPC / PSC` 等）。我方不建立，硬體資訊由我方 `0x14xx HW_*` 另案處理 |
| `0x32 LIVE_TEXT` / `0x33 LIVE_REPLY` | 🗑 不整合 | `LC:` 即時調色文字指令通道，我方不建立 |

---

## 7. 音訊（不整合）

| 對方 | 結果 | 說明 |
|---|---|---|
| `0x08 AUDIO_LEVEL` | 🗑 不整合 | 我方**明確不建立** audio 指令 |
| `0x09 AUDIO_ACTIVE` | 🗑 不整合 | 同上 |

（對方端此系列視為非主線；若未來要，再另案開 `0x3xxx` 域。）

---

## 8. 診斷與錯誤回報（移除：Slave 被動）

| 對方 | 結果 | 說明 |
|---|---|---|
| `0x70 DIAGNOSTIC` | ❌ 移除 | Slave 被動、不主動推送；診斷資料改由查詢指令（如 `MODE_GET`、`HW_*`）被動取回 |
| `0x71 ERROR_REPORT` | ❌ 移除 | 同上；錯誤改由各查詢回覆或 `OTA_ERROR_RSP` 承載 |

---

## 9. OTA（0x40/0x41 + 內層 0x01~0x08 → 0x22xx）

這是改變最大的部分，不只換編號，**整個運作概念都換了**。

### 9.1 外層包裝

```text
以前：0x40 OTA_COMMAND / 0x41 OTA_RESPONSE 子母包
      （一個 RS485 指令，裡面再包一層 OTA packet）
現在：扁平 top-level 指令 0x22xx，直接就是 OTA 動作 / 查詢
```

### 9.2 內層指令逐條對照

| 對方內層 | 變成 | 參數對應 |
|---|---|---|
| `0x01 START` | ✅ `0x2201 OTA_BEGIN` | 見 9.3 |
| `0x02 DATA` | ✅ `0x2202 OTA_WRITE` | `seq_hi/seq_lo` → `offset:u32`；`data` → `data` |
| `0x03 END` | ✅ `0x2203 OTA_END` | 空 payload |
| `0x04 VERIFY` | ✅ `0x2216 OTA_VERIFY` | 驗證動作保留，回覆拆成 3 個失敗原因 bool（見 9.4） |
| `0x05 REBOOT` | ✅ `0x2220 OTA_APPLY` | 拆成 `set_boot_only:u8 + restart_delay_ms:u32`；不再有「`0xFFFFFFFF`=不重啟」的 magic number |
| `0x06 STATUS` | 🔀 拆成 `0x221A OTA_STATE_QUERY` + `0x2218 OTA_PROGRESS_QUERY` | 狀態與進度分開查，不再混在一起 |
| `0x07 ABORT` | ✅ `0x2205 OTA_ABORT` | 空 payload |
| `0x08 CAPS` | ✅ `0x2210 OTA_CAPS_QUERY` | 能力查詢保留，回覆拆成 4 個 bool（見 9.4） |

**新增（對方沒有的）：**

| 新指令 | 用途 |
|---|---|
| `0x2204 OTA_ACK` | 每塊寫入成功的 per-chunk 回覆（`offset` + `written`） |
| `0x2206/0x2207 OTA_VERSION_QUERY/RSP` | 查韌體版本 + 執行中/空閒 slot + 分割區大小 |
| `0x2212/0x2213 OTA_LAST_QUERY/RSP` | 上次 OTA 的結果（7 個 bool：never/ok/begin_fail/write_fail/end_fail/sha_mismatch/reboot_fail） |
| `0x2214/0x2215 OTA_PARTITION_STATUS` | 雙 slot 的 seq / valid / running_idx |
| `0x221C OTA_ERROR_RSP` | 統一失敗回覆：11 個具名 bool + `failed_offset / written_up_to / target_slot` |

### 9.3 START 的 metadata 完全換掉

```text
以前（OTAStartMetadata）：
  magic "miniboot"(8) + imageSize:u32 + imageCrc32:u32 + buildTimestamp:u32
  + versionMajor/Minor/Patch:u16 + reserved + headerCrc32:u32

現在（0x2201 OTA_BEGIN）：
  image_size:u32 + chunk_size:u16 + sha256[32] + fw_ver:str
```

| 概念 | 以前 | 現在 |
|---|---|---|
| 完整性檢查 | **CRC32**（imageCrc32） | **SHA256**（app 層，檔層完整度更高） |
| 版本 | 3 個 u16 拆開 + buildTimestamp | 一個 `fw_ver` 字串 |
| 內層 packet CRC | 每個 DATA chunk 帶 CRC32 | 取消（外層 transport 已有 CRC） |
| 序號 | `seq_hi/seq_lo` 遞增 | `offset:u32`（跟 File 域同一風格） |
| 分割區 | 沒有 A/B 概念，靠 CRC/timestamp 判重 | **A/B 雙 slot**：running/free slot、seq、rollback、partition_size |

### 9.4 常數約定全部拆成 bool（「自描述」原則）

| 以前要查表的 | 現在 |
|---|---|
| `state:u8`（0=IDLE, 1=WRITING…） | `OTA_STATE_RSP` 4 個 bool：`state_idle / state_writing / state_verified / state_error` |
| `features` bitmask（bit0=SECURE_BOOT…） | `OTA_CAPS_RSP` 4 個 bool：`secure_boot / flash_encrypt / rollback_support / diff_ota_support` |
| `last_err:u8`（0=OK, 5=REBOOT_FAIL…） | `OTA_ERROR_RSP` 11 個具名 bool，直接讀欄位名 |
| `last_ota_state`（0xFF=NEVER…） | `OTA_LAST_RSP` 7 個具名 bool |
| `verified_ok`（0/1） | `OTA_VERIFY_RSP`：`verify_ok` + 3 個失敗原因 bool（sha/header/crc） |

### 9.5 推薦流程（對方韌體要照這個重寫）

```text
1. 前置查詢：VERSION → CAPS → LAST → (PARTITION)
2. OTA_BEGIN { image_size, chunk_size, sha256, fw_ver }
3. 迴圈 OTA_WRITE { offset, data } → 每塊收 OTA_ACK (offset, written)
   ── 50ms timeout、同塊最多重試 3 次；失敗 → OTA_ERROR_RSP → 先 ABORT
4. OTA_END → 失敗回 OTA_ERROR_RSP (err_end_*)
5. OTA_STATE_QUERY / OTA_VERIFY → verify_ok 才繼續
6. OTA_APPLY { set_boot_only=0, restart_delay_ms=200 } → 重啟
7. 重連後 VERSION_QUERY 確認 fw_ver & sha256 一致 → 才算成功
```

---

## 10. 理解捷徑（FAQ）

**Q：為什麼 MODE_NEXT 要併進 MODE_SET？**
A：兩條指令 payload 完全相同（`mode_id + 時間`），而且 Master 反正都指定了 mode_id，沒有「只前進不指定」的用法。多一條只是多一個字串分支（對方 slave 端也只是 `"set"` vs `"next"` 的差別）。

**Q：為什麼 master_start_ms（絕對時間）改成 start_delay_ms（相對延遲）？**
A：絕對時間需要時鐘同步才能解讀（Slave 要知道 Master 的「300ms 後」等於自己什麼時刻）。相對延遲只需要「同時收到」——廣播一次全部同時開跑，省掉整個時鐘同步的複雜度。代價是同步精度只到傳輸 jitter（對方實測 mode start 差 1–3ms，可接受）。

**Q：state 五態跑去哪了？**
A：拆成兩維度：`mode_type`（0=系統/UNKNOWN/DEV、1=LED、2=SERVO）+ `running`（0/1）。IDLE 用「預設 mode 0 + running=0」表達，COMPLETED 用「running=0 + elapsed≥total」由 Master 推得。

**Q：為什麼 OTA 要大改？**
A：三點：① 對方是舊式「單一分割區 + CRC32 + 子母包」，我方是「A/B 雙 slot + SHA256 + 扁平指令」；② 我方連 File 傳輸（0x20xx）都改用 `offset` 取代序號，OTA 跟進保持一致；③ 「常數約定零依賴」——不要讓工程師查表才知道 `state=5` 是什麼意思。

**Q：誰是權威？**
A：`slave/schema/ota.json`、`pixel.json`、`sys.json`。文件（含本份）只是說明，實作以 schema 為準。

---

## 11. 附錄：對方完整 catalog 一頁總表

| 對方 CMD | 名稱 | 方向 | 結果 | 變成 |
|---:|---|---|---|---|
| `0x00` | UNKNOWN | reserved | — | 保留（未知指令） |
| `0x01` | MODE_SET | M→S | ✅ | `0x3105 MODE_SET` |
| `0x02` | MODE_NEXT | M→S | 🔀 | `0x3105 MODE_SET` |
| `0x03` | MODE_STOP | M→S | ✅ | `0x3106 (action=0)` |
| `0x04` | BRIGHTNESS | M→S | ⏸ | 未整合（亮度範圍待統一） |
| `0x05` | STORY_SET | M→S | 🔀 | 併入 `0x3105 MODE_SET.mode_type` |
| `0x06` | POWER_OFF | M→S | 🔀 | `0x3106 (action=1)` |
| `0x07` | POWER_ON | M→S | ❌ | 移除（恢復＝重新 MODE_SET） |
| `0x08` | AUDIO_LEVEL | M→S | 🗑 | 不整合 |
| `0x09` | AUDIO_ACTIVE | M→S | 🗑 | 不整合 |
| `0x10` | STATUS_QUERY | M→S | ✅ | `0x3103 MODE_GET` |
| `0x11` | STATUS_REPORT | S→M | ✅ | `0x3104 MODE_GET_RSP` |
| `0x12` | PROBE | M→S | ✅ | 我方既有 `0x1001 DISCOVER` |
| `0x13` | PROBE_REPLY | S→M | ✅ | 我方既有 `0x1002 SLAVE_ANNOUNCE` |
| `0x20` | TIME_SYNC_REQUEST | M→S | ✅ | `0x100A TIME_SYNC`（選用） |
| `0x21` | TIME_SYNC_REPLY | S→M | ✅ | `0x100B TIME_SYNC_RSP`（選用） |
| `0x22` | TIME_OFFSET_APPLY | M→S | ✅ | `0x100C TIME_OFFSET_APPLY`（選用） |
| `0x30` | INFO_QUERY | M→S | 🗑 | 不整合 |
| `0x31` | INFO_REPLY | S→M | 🗑 | 不整合 |
| `0x32` | LIVE_TEXT | M→S | 🗑 | 不整合（LC: 通道） |
| `0x33` | LIVE_REPLY | S→M | 🗑 | 不整合 |
| `0x40` | OTA_COMMAND | M→S | ✅ | `0x22xx` 全組（扁平） |
| `0x41` | OTA_RESPONSE | 雙向 | ✅ | `OTA_ACK / OTA_ERROR_RSP / 各 *_RSP` |
| `0x70` | DIAGNOSTIC | S→M | ❌ | 移除（Slave 被動） |
| `0x71` | ERROR_REPORT | S→M | ❌ | 移除（Slave 被動） |

> 另外：對方「Timer↔Master」的 5-byte UART 幀（`[0xB4][b1][b2][b3][0xFF]`）是**面板通道**，不在本對照內。我方也有相同幀格式，但 bit6/bit7 語義與對方衝突，屬另一條待決線（見 `07_merge_comparison.md §5.1`）。

## 相關文件

- `05_integration_overview.md` — 整合總規格（三組指令總表 + 取代對照）
- `03_ota_protocol.md` — OTA 0x22xx 完整設計
- `04_pixel_protocol.md` — PIXEL 0x31xx 完整定義
