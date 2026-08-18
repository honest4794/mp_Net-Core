# OTA 協議變更說明（舊版 vs 0x22XX）

> 比對基準：
> - 舊 I2C OTA：`協議規格_master_timer_slave_精簡版.md §二.7`（CMD 0x01~0x08）
> - 舊 RS485 OTA：`協議規格_slaveUART.md §OTA`（透過 0x40 OTA_COMMAND / 0x41 OTA_RESPONSE 子母包裝）
> - 新版 schema：`ota.json`（CMD 0x2201 ~ 0x220A，扁平指令）

---

## 一、核心設計差異總覽

| 維度 | 舊版 (兩份規格) | 新版 0x22XX |
|---|---|---|
| **指令分層** | 子母包：外層 transport CMD (I2C 0x01-0x08 / RS485 0x40) + 內層 OTA packet | **扁平 CMD**：0x2201~0x220A 每支都是獨立 top-level 指令 |
| **指令命名前綴** | START / DATA / END / VERIFY / REBOOT / STATUS / ABORT / CAPS（無統一前綴）| **全部 `OTA_` 開頭**：OTA_BEGIN、OTA_WRITE、OTA_END、OTA_ACK、OTA_ABORT、OTA_INFO_QUERY、OTA_INFO_RSP、OTA_APPLY、OTA_STATUS |
| **查詢/能力/驗證** | 三支獨立指令：`0x04 VERIFY` + `0x06 STATUS` + `0x08 CAPS` | **合併為 `OTA_INFO_QUERY → OTA_INFO_RSP` 一支查詢**：START 前打一次、END 後再打一次，Slave 依狀態自動補相關欄位 |
| **PARTITION 除錯資訊** | 隱藏在 OTA 狀態機；slaveUART 透過 polling OTA_RESPONSE 空 payload 取得 | 精簡成 5 個欄位，**直接塞在 OTA_INFO_RSP 尾端**（slot0/1 seq、slot0/1 valid、running_idx），不需要單獨指令 |
| **OTA 內層 CRC32** | 強制雙層：`[CMD][SEQ_HI][SEQ_LO][SIZE][DATA...][CRC32]` + 外層 transport CRC | 不做（**交由外層 transport 自己的 CRC / ACK 機制負責**，避免無謂的雙重校驗）|
| **per-chunk sequence** | 每包 DATA 獨立 SEQ（HI/LO 兩 byte），用於去重/亂序偵測 | 用 `offset: u32` 充當 seq，與你現有 `file.json FILE_CHUNK` 風格一致 |
| **套用 + 重啟** | `0x04 VERIFY → 0x05 REBOOT` 兩支指令 | **一支 `OTA_APPLY { restart_delay_ms }` 搞定**；特殊值 `0xFFFFFFFF` = 只 set boot partition 不重啟 |

---

## 二、指令對照表（CMD 級）

| 舊概念 | 舊版 CMD | 新版 0x22XX | 處理方式 |
|---|---|---|---|
| START（宣告開始 + 韌體基本資料）| I2C 0x01 / RS485 0x40 inner | **0x2201 OTA_BEGIN** | ✅ 1:1 對應 |
| DATA（分段傳送）| I2C 0x02 / RS485 0x40 inner | **0x2202 OTA_WRITE** | ✅ 1:1 對應；SEQ→offset |
| END（完整性檢查）| I2C 0x03 / RS485 0x40 inner | **0x2203 OTA_END** | ✅ 1:1 對應 |
| ACK / READY / SUCCESS 三態回覆 | RS485 0x41 OTA_RESPONSE + 內層狀態碼 | **0x2204 OTA_ACK** (成功) + **0x220A OTA_STATUS** (失敗/進度) | 🟰 簡化為二態：成功回 ACK，其餘一律 STATUS |
| ABORT（安全取消）| I2C 0x07 | **0x2205 OTA_ABORT** | ✅ 1:1 對應 |
| VERSION / CAPS 查詢 | I2C 0x08 CAPS / slaveUART polling 0x41(empty) | **0x2206 OTA_INFO_QUERY → 0x2207 OTA_INFO_RSP** | 🟰 **合併：VERSION + CAPS + PARTITION_STATUS + VERIFY 結果全部塞進 OTA_INFO_RSP** |
| VERIFY（重啟前再驗證一次）| I2C 0x04 | 不單獨留指令 | 🟰 `OTA_END` 後再打 `OTA_INFO_QUERY`，讀取 `verified_ok` / `verified_sha256` 欄位取代 |
| REBOOT（驗證成功後重啟）| I2C 0x05 | **0x2209 OTA_APPLY.restart_delay_ms** | 🟰 與 set_boot 合併為單一動作 |
| STATUS（查進度/UI 顯示）| I2C 0x06 / RS485 polling | **0x220A OTA_STATUS**（Slave 被動回覆；或 Master OTA_INFO_QUERY 拿資訊）| ✅ 保留 |
| PARTITION STATUS（slot seq/valid/running_idx）| 無單獨 CMD；由 C++ OTAReceiver 內部狀態重建 | **取消單獨指令；欄位直接併入 0x2207 OTA_INFO_RSP** | 🟰 |

---

## 三、0x2207 OTA_INFO_RSP 的 18 個欄位來源（為什麼這麼多）

按照「什麼時候會用到」分組：

### 3.1 START 前就會有值（等於舊版 VERSION + CAPS + PARTITION_STATUS 的組合）

| 欄位 | 型別 | 來源 | 為什麼需要 |
|---|---|---|---|
| `fw_ver` | str | `esp_app_get_description()->project_version` | 基本去重 |
| `app_sha256` | bytes[32] | `esp_ota_get_app_description()->app_elf_sha256` | **強去重：SHA 相同就跳 OTA** |
| `running_slot` | str | `esp_ota_get_running_partition()->label` | UI 顯示 ota_0/ota_1 |
| `running_seq` | u32 | otadata | bootloader 選版依據；值異常表示 otadata 損毀 |
| `free_slot` | str | `esp_ota_get_next_update_partition(NULL)->label` | 預覽將被擦寫的 slot |
| `partition_size` | u32 | partition->size | **檢查 image_size 不能超過** |
| `max_chunk_size` | u16 | config + transport + heap（舊 CAPS）| Master 每包不超過這個大小，避免 OOM / fragmentation |
| `features` | u8 bitmask | secure_boot / flash_encrypt / rollback（舊 CAPS）| Secure Boot=1 時 Master 要確認 image 有簽章 |
| `last_ota_state` | u8 | NVS/SRAM 持久化 | =5 (REBOOT_FAIL) 時不要重傳 firmware，直接報修 |
| `last_ota_sha256` | bytes[32] | NVS/SRAM 持久化 | 判斷這台上次是不是已經在傳同一份 fw |
| `slot0_seq` | u32 | otadata | 舊 PARTITION_STATUS |
| `slot0_valid` | u8 | otadata | 舊 PARTITION_STATUS |
| `slot1_seq` | u32 | otadata | 舊 PARTITION_STATUS |
| `slot1_valid` | u8 | otadata | 舊 PARTITION_STATUS |
| `running_idx` | u8 | `esp_ota_get_running_partition()` sub-type 減去 ota_0 | 舊 PARTITION_STATUS；除錯 UI 方便直接用 |

### 3.2 只有 OTA_END 之後才非零（START 前填 0/空）— 等同舊版 0x04 VERIFY

| 欄位 | 型別 | 為什麼需要 |
|---|---|---|
| `verified_ok` | u8 | 從 flash 讀回重算 SHA256 通過了沒；**1=才能 OTA_APPLY** |
| `verified_sha256` | bytes[32] | 重算後的真實值，Master 自己 double-check |
| `target_slot_seq` | u32 | OTA_APPLY 後寫入 otadata 的新 seq；非零代表 set_boot 已執行 |

### 3.3 OTA_INFO_QUERY.fields 選擇性讀取（解決成本問題）

**不是每個欄位都便宜。** 特別是 VERIFY 類的 3 個欄位需要從 flash 重算 2MB 的 SHA256，
要 **1000~2000 ms**（2MB ÷ 20MB/s flash read ≈ 100ms + SHA256 約 1200ms）。
其他欄位都是 RAM/NVS/otadata 內的小量讀取，加起來不到 10ms。

因此 `OTA_INFO_QUERY (0x2206)` 的 `fields: u8` bitmask 讓你選擇要哪些群組的欄位，
未被選取的欄位 Slave 填 0 / 空字串（SchemaCodec 仍照固定順序編碼所有 18 個欄位，不會少欄位，只是內容零）。

| bit | mask | 群組名 | 包含欄位 | 讀取成本預估 (ESP32-S3 @ 240MHz, Quad SPI 80MHz) |
|---:|---|---|---|---|
| 0 | `0x01` | BASIC | fw_ver, app_sha256, running_slot, running_seq, free_slot, partition_size | **~2 ms** |
| 1 | `0x02` | CAPS | max_chunk_size, features | **<1 ms**（menuconfig 常數 + secure boot efuse） |
| 2 | `0x04` | LAST | last_ota_state, last_ota_sha256 | **~1 ms**（NVS cached，首次冷啟 ~5ms） |
| 3 | `0x08` | PARTITION | slot0_seq, slot0_valid, slot1_seq, slot1_valid, running_idx | **~3 ms**（otadata 兩份副本各 4KB read + crc 驗證） |
| 4 | `0x10` | VERIFY | verified_ok, verified_sha256, target_slot_seq | **1000 ~ 2000 ms** ⚠️ 最貴，從 free_slot 頭到 image_size 尾整個重讀 SHA256 |
| 5–7 | — | reserved | 填 0（未來擴充：hash tree / rollback state / chip_id 等） | — |

**常用組合：**

| 情境 | fields 值 | 預估總花費 | 註解 |
|---|---|---|---|
| START 前檢查（推薦）| `0x01 \| 0x02 \| 0x04 \| 0x08` = **`0x0F`** | **~7 ms** | BASIC + CAPS + LAST + PARTITION，不跑 VERIFY |
| END 後驗證（推薦）| `0x01 \| 0x04 \| 0x10` = **`0x15`** | **~1003 ms** | BASIC + LAST + VERIFY；PARTITION 其實不需要每次拿 |
| 快速心跳看 version（例如 5s 輪詢）| `0x01` = **`0x01`** | **~2 ms** | 只要 fw_ver / app_sha256 |
| 除錯時全拿 | `0x1F` = **`0x1F`** | **1007 ~ 2007 ms** | 五群全部回來；不要在一般流程用 |
| 預設值（Master 偷懶不填）| `0x0F` | ~7 ms | Slave 收到 fields=0 時，自動視為 0x0F（故意不包含最貴的 VERIFY 避免誤觸） |

⚠️ **VERIFY 成本的備註：** 如果 image_size=0（OTA_SIZE_UNKNOWN），VERIFY 群組就必須把整個 slot（如 1.5MB）全部重讀，
花大約 **1500~2500 ms**。建議 Master 一定帶正確的 `OTA_BEGIN.image_size`，
這樣 Slave 只讀到 image_size 為止，節省 30~50% 時間。

---

## 四、長度限制（bytes_rest / payload / chunk_size）

你的 `file.json` 與 `stream.json` 都用到 `bytes_rest`，但長度限制來源其實有**三層**，OTA 剛好是最敏感的（資料量大 + flash 寫入不能中斷）。

### 4.1 三層限制對應到 OTA 的位置

```
Layer 3 ————————————————————————————————————————
  0x2202 OTA_WRITE.data (bytes_rest)
  長度 = OTA_BEGIN.chunk_size  (<= OTA_INFO_RSP.max_chunk_size)
           ↑
           由 Master 在 BEGIN 時協商，一定要 <= max_chunk_size
           預設建議：4096 (對齊 flash sector) 或 224 (RS485 舊約)

Layer 2 ————————————————————————————————————————
  你們 proto 本身的 payload 長度：
  例如 RS485 LEN=u8 → 單 frame 最多 240 bytes；
  Python WebSocket 沒限制但 RAM 有限；
  I2C slave FIFO 64 bytes → 舊版才會用 56 bytes chunk。

Layer 1 ————————————————————————————————————————
  ESP32 物理 flash 寫入：最小 4 bytes 對齊；
  esp_ota_begin 內部快取 4KB (flash sector size)。
```

### 4.2 長度違反時的建議行為

| 情況 | Slave 處理方式 | 要回什麼指令 |
|---|---|---|
| `OTA_BEGIN.image_size > OTA_INFO_RSP.partition_size` | reject BEGIN | `OTA_STATUS (last_err=3 BEGIN_FAIL)` |
| `OTA_BEGIN.chunk_size > OTA_INFO_RSP.max_chunk_size` | **silently cap**（不要失敗，Master 可能忘了先查 max_chunk_size），但寫入時每包按 max 切 | `OTA_STATUS.written` 反映真實長度 |
| `OTA_WRITE.data.length > max_chunk_size` | 只寫前 max_chunk_size bytes？**不行 — 寧可失敗也不要 partial write** | `OTA_STATUS (last_err=4 WRITE_FAIL)`，written 不會增加 |
| `OTA_WRITE.offset != session.written` | **完全不寫**（防跳位；esp_ota 是線性 stream 不能 seek）| `OTA_STATUS (state=ERROR, last_err=4)` |
| `OTA_INFO_RSP 固定長度欄位`（bytes_fixed[32], u32...） | SchemaCodec 編碼長度固定，**沒有長度問題** | — |

### 4.3 `OTA_INFO_RSP.max_chunk_size` 在不同 transport 的推薦預設值

| transport | max_chunk_size 推薦 | 推算理由 |
|---|---|---|
| RS485 UART（slaveUART.md §OTA）| **224** | 240 (RS485 LEN) − 16 (內層 OTA header/CRC) = 224；舊版實際值 |
| I2C（精簡版 §二.6）| **56** | 舊版 fast chunk 56 bytes；I2C slave FIFO 限制 |
| Python WebSocket（mp_Net-Core 現況）| **4096** | 對齊 flash sector；MicroPython RAM 正常約 200KB 可用，4KB 不會 OOM |
| 有 `OTA_INFO_RSP.features & OTA_FEAT_DIFF_OTA` (bit3) | **≤ 1024** | 增量更新時為了 hash tree 對齊，chunk 要小 |

---

## 五、常數約定（兩份規格有的沒的，我整理成單一來源）

### 5.1 OTA_STATUS.state / OTA_INFO_RSP.last_ota_state / OTA_STATUS.last_err 共用

| 值 | 名稱 | 使用時機 |
|---|---|---|
| 0 | `OTA_OK / OTA_STATE_IDLE` | 成功 / 閒置中 |
| 1 | `OTA_STATE_WRITING / OTA_ERR_ALREADY_ACTIVE` | 正在寫 / BEGIN 時已經有 session |
| 2 | `OTA_STATE_VERIFIED` | OTA_END 通過 + verified_ok=1，可 OTA_APPLY |
| 3 | `OTA_STATE_ERROR / OTA_ERR_NO_PARTITION / OTA_ERR_BEGIN_FAIL` | 任一失敗；細節看 last_err |
| 4 | `OTA_ERR_WRITE_FAIL` | 寫入失敗 (offset 錯 / flash write 錯 / chunk 太大) |
| 5 | `OTA_ERR_END_VALIDATE_FAIL` | OTA_END (esp_ota_end) 內部驗證不過 |
| 6 | `OTA_ERR_NOT_WRITING` | 在 WRITING 狀態外呼叫 WRITE / END |
| 7 | `OTA_ERR_SET_BOOT_FAIL` | OTA_APPLY 內 esp_ota_set_boot_partition 失敗 |
| 8 | `OTA_ERR_SHA_MISMATCH` | verified_sha256 != OTA_BEGIN.sha256 |
| 9 | `OTA_ERR_REBOOT_FAIL` | last_ota_state：上次重啟後沒回到 DEV / 沒連回 |
| 0xFF | `OTA_ERR_NEVER` | last_ota_state：從來沒做過 OTA |

### 5.2 OTA_INFO_RSP.features bitmask

| bit | name | 1 的意思 |
|---|---|---|
| 0 | `OTA_FEAT_SECURE_BOOT` | 需有 ECDSA/RSA 簽章的 image 才會 end 通過 |
| 1 | `OTA_FEAT_FLASH_ENCRYPT` | 寫入後 flash controller 自動加密；不要上傳已加密 bin |
| 2 | `OTA_FEAT_ROLLBACK` | 啟用 rollback；OTA 後 app 要 mark_valid 不然下次重啟跳回 |
| 3 | `OTA_FEAT_DIFF_OTA` | 支援增量更新；chunk_size 請用 ≤ 1024 |
| 4–7 | reserved | 填 0 |

### 5.3 OTA_APPLY.restart_delay_ms 特殊值

| 值 | 意思 |
|---|---|
| 0 | 立即重啟（呼叫完機器人斷線）|
| 1~0xFFFFFFFE | 延遲 N ms；Master 有時間收 ACK 然後中斷連線 |
| **0xFFFFFFFF** | **只 set boot partition，不重啟**（給先做健康檢查 / 確認所有 Slave 都 OK 後再廣播重啟）|

---

## 六、推薦流程（對應舊版 slaveUART.md §OTA 的 retry / poll / 確認原則）

```
 ┌─ 0x2206 OTA_INFO_QUERY fields=0x0F (第一次，開始前，~7ms)
 │    → BASIC: app_sha256 相同就跳 OTA；partition_size >= image_size 檢查
 │    → CAPS:  max_chunk_size 當成每包 chunk 上限；features.bit0=1 要確認 image 有簽章
 │    → LAST:  last_ota_state == 9 (REBOOT_FAIL) 不要重傳，直接報修
 │    → PARTITION: slot0/slot1 seq/valid 供 UI 顯示雙槽狀態
 │
 ├─ 0x2201 OTA_BEGIN  { image_size, chunk_size, sha256, fw_ver }
 │
 ├─ 【for each chunk】:
 │    0x2202 OTA_WRITE { offset, data(<=max_chunk_size) }
 │      ↳ OK      → 收到 0x2204 OTA_ACK
 │      ↳ 50ms TO → 同一包最多重試 3 次 (per-chunk retry，**不是全部重來**)
 │      ↳ NACK    → 收到 0x220A OTA_STATUS(state=ERROR) → 先 0x2205 ABORT 再報錯
 │
 ├─ 0x2203 OTA_END
 │
 ├─ 0x2206 OTA_INFO_QUERY fields=0x15 (第二次，END 後，~1003ms，取代舊版 0x04 VERIFY)
 │    → BASIC:   沒用但便宜，順便看 running_slot / seq
 │    → LAST:    last_ota_state 更新為 0 (OK) 或 8 (SHA_MISMATCH)
 │    → VERIFY:  verified_ok == 1 ?；verified_sha256 == OTA_BEGIN.sha256 ?
 │                (target_slot_seq 還 0 是正常，尚未 APPLY)
 │
 ├─ 0x2209 OTA_APPLY { restart_delay_ms = 200 }
 │
 └─ (等 30 秒內 reconnect 後) 再打一次 0x2206 fields=0x01 (~2ms，快速心跳)
      → fw_ver & app_sha256 與期望相同才算**真正成功**
      → slaveUART.md §OTA 要求：不能用「有收到 APPLY ACK」當成功條件
```

---

## 七、已明確選擇「不跟進」的舊版設計（附上理由）

| 舊版做法 | 為什麼新版不做 |
|---|---|
| 雙重 CRC（內層 OTA packet + 外層 transport）| 你明確說不要；且所有主流 transport (TCP/WebSocket/RS485 自訂 frame) 都已有自己的 CRC 與重試機制，雙層浪費 CPU 與 payload 空間 |
| START 指令送 2 次、END 指令每 3s poll 重送 | **Master 端流程要遵守，不屬於 schema 層**。不在 json 定義；已寫在第六節推薦流程，作為實作建議 |
| 單獨 VERIFY / REBOOT / CAPS 三個指令 | 功能都在 OTA_INFO_RSP 欄位 + OTA_APPLY 覆蓋了，減少指令數方便除錯 |
| 獨立 PARTITION_STATUS 指令 | 併入 OTA_INFO_RSP 結尾 5 個欄位；反正你會在 START 前/END 後都打一次查詢，順手拿到，不需要額外指令 |
| slot0_label / slot1_label 字串欄位（舊 PARTITION_STATUS）| 刪掉，避免多餘 str_u16len；標準 partition table 固定是 `ota_0` / `ota_1`，Master 自己補即可，節省 payload |
