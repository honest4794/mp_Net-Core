# OTA 機制設計參考（IDF C 版）

> **用途**：釐清 ESP-IDF 的 partition OTA 完整機制（寫入 → 確認 → 失敗回退），作為本專案設計自己 OTA 指令時的參考底稿。
> **分類**：筆記（03_notes）
> **整理時間**：2026-08-18
> **對應協議**：`01_protocol/03_ota_protocol.md`（0x22xx 指令設計）

---

## 0. 一句話結論

IDF OTA = 「把編譯好的 binary 依序寫進一個**固定分區**（不是檔名），寫完改**序號**，
bootloader 下次開機自動開序號大的那顆；新版本要**自己確認 OK**，沒確認就掛掉時，
bootloader 下次自動退回上一版。」

「能不能隨便寫檔名」不取決於語言，取決於你更新的是**檔案**還是**韌體**：

| 更新對象 | 機制 | 能不能指定檔名 |
|---|---|---|
| 檔案（素材/設定/`.py`） | 檔案系統寫入 | ✅ 可以 |
| 韌體（編譯好的 image） | partition OTA | ❌ 只能寫進固定 slot |

---

## 1. 核心概念：partition table + otadata + 序號

OTA 要能 ping-pong 更新，partition table 必須先規劃成這樣（編譯/燒錄前定死）：

```text
# Name,     Type, SubType, Offset,  Size
nvs,        data, nvs,     0x9000,  0x6000,
factory,    app,  factory, 0x10000, 1M,
ota_0,      app,  ota_0,   0x110000,1M,
ota_1,      app,  ota_1,   0x210000,1M,
otadata,    data, ota,     0x310000,0x2000,
```

| 區 | 作用 |
|---|---|
| `factory` | 出廠版本，最底線 |
| `ota_0` / `ota_1` | 兩顆輪流更新 |
| `otadata` | 記錄每顆 slot 的 **`ota_seq`（序號）** |

**切換版本 = 改序號，不是改檔名。**

Bootloader 每次開機只做一件事：

```text
讀 otadata → 比較 ota_0 和 ota_1 的序號 → 開序號最大的那顆
```

---

## 2. 完整流程（寫入只要 data，但前後各有一行關鍵呼叫）

```c
#include "esp_ota_ops.h"

// 1. 自動挑「不是目前正在跑的那顆」slot（不用自己選）
const esp_partition_t *target = esp_ota_get_next_update_partition(NULL);

// 2. 開始 = 把該 slot 整顆擦掉，拿到 handle
esp_ota_handle_t h;
esp_ota_begin(target, OTA_SIZE_UNKNOWN, &h);

// 3. 迴圈寫 data（「直接寫 data 就夠」的這一步）
while (還有資料)
    esp_ota_write(h, buf, n);

// 4. 結束 = 驗證映像（header magic + 分段 checksum，可選簽章）
esp_ota_end(h);

// 5. 把這顆的序號設成「目前跑的 + 1」（還沒重啟，不生效）
esp_ota_set_boot_partition(target);

// 6. 重啟，bootloader 開序號大的新版本
esp_restart();
```

「選哪顆 slot」由 `esp_ota_get_next_update_partition()` 自動決定；
「送給哪顆 Slave」由 frame header 的 `ADDR` 決定。兩者是不同維度：

| 維度 | 誰決定 | 說明 |
|---|---|---|
| 送給誰（哪顆板） | frame header `ADDR` | 任何指令共用，不是 OTA 專用 |
| 寫進哪個區（該顆內部） | partition table + 函式 | 自動挑閒置 slot，程式不用管 |

---

## 3. 失敗處理：寫入階段天然安全

**關鍵設計：`esp_ota_set_boot_partition()` 之前，序號完全沒動。**

| 失敗點 | 後果 | 重試方式 |
|---|---|---|
| 寫到一半斷線/斷電 | slot 是擦掉狀態，但**序號沒變** → 下次仍開舊版 | 重新 `esp_ota_begin`（再擦一次）→ 重寫 |
| `esp_ota_end` 驗不過（CRC 錯） | 映像作廢，**序號沒變** → 仍開舊版 | 同上，整顆重來 |

> 只要還沒成功 `set_boot_partition`，失敗就「好像沒發生過」，舊版照跑，重傳重寫即可。

---

## 4. 確認成功：分兩個層次

| 層次 | 誰做 | 時機 |
|---|---|---|
| 映像完整性 | `esp_ota_end` | 寫完當下，驗 header/checksum |
| 運行是否正常 | **新程式自己呼叫** `esp_ota_mark_app_valid_cancel_rollback()` | 重啟後，新程式通過自檢才叫 |

> 映像驗過 ≠ 跑起來沒問題（可能連不上網、卡死）。
> 所以 IDF 要求「新程式自己舉手說：我 OK 了」。

---

## 5. 下次啟動失敗 → 回上一個版本（rollback）

必須開啟選項：`CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE = y`

```text
更新 → 重啟 → 新版本（序號 2）開機，但狀態是「待驗證 pending」
                    │
        ┌───────────┴───────────┐
        │ 新程式自檢通過         │ 新程式 panic / watchdog / 斷電
        │ 呼叫 mark_app_valid    │ （還沒喊「我 OK」就掛了）
        ▼                       ▼
   取消 rollback，正式上線      bootloader 下次開機發現「pending 沒通過」
        │                        → 把序號退回 → 開上一版（序號 1）
        ▼
     從此開新版本
```

**回退一句話：新版本「先試跑、要自己確認」，沒確認就掛掉，bootloader 下次自動改開舊版。**

---

## 6. 容易踩的坑

1. **沒開 rollback 選項**：壞掉的新版因「序號最大」被永遠優先開機 = 變磚。
   只能靠 `CONFIG_BOOTLOADER_FACTORY_RESET` 指定 GPIO 觸發 factory reset 救回。
2. **確認動作不能省**：新程式一定要在「確定能正常運作」後才呼叫 `esp_ota_mark_app_valid_cancel_rollback()`，否則一上電就 crash 會一直被判定失敗。
3. **反降級（anti-rollback）是另一回事**：用 efuse 燒 security version，防止降回有漏洞的舊版。與「失敗回退」是兩個獨立功能，別混。

---

## 7. 與本專案（MicroPython）對照

| 面向 | IDF（C） | 本專案（MicroPython） |
|---|---|---|
| 寫入 | `begin/write/end` 包住 | 檔案層級，更簡單 |
| 選 slot | `esp_ota_get_next_update_partition()` 自動 | 無（沒有 partition OTA） |
| 選 Slave | frame header `ADDR` | NC4 封包 `ADDR` |
| 失敗回舊版 | rollback + `otadata` 序號 | 無（靠手動還原檔案） |
| 現況 | — | `slave/` 無任何 partition OTA 程式碼；只有 `FILE_* 0x20xx` 檔案傳輸 |

### 決策點：我們要不要引進 partition OTA？

取決於一件事：「更新程式」要維持**覆蓋 `.py` 檔案**，還是改成**刷整份韌體 binary**。

| 方向 | 做法 | 備註 |
|---|---|---|
| 維持覆蓋 `.py` | 用現有 `FILE_*`（任意 path + sha256 + 斷點續傳） | 不需引進 partition OTA |
| 改刷韌體 binary | 引進上述整套機制（固定 slot + 驗證 + rollback） | MicroPython 韌體一樣「不能隨便寫檔名」 |

---

## 8. 設計指令時要決定的項目（草稿）

若要做 partition OTA，指令設計至少要覆蓋以下語義（對照 IDF API）：

| 語義 | IDF API | 指令設計要點 |
|---|---|---|
| 開始更新 | `esp_ota_begin` | 帶韌體大小/版本/簽章資訊 |
| 寫入 chunk | `esp_ota_write` | 帶 seq、offset、data；要有 retry 與 ACK |
| 結束驗證 | `esp_ota_end` | 帶完整 sha256；驗不過整個作廢 |
| 切換啟動 | `esp_ota_set_boot_partition` | 切換後才重啟 |
| 查進度/狀態 | `esp_ota_get_state_partition` | 供 UI 顯示 |
| 中止取消 | （擦掉重來即可） | 出錯時安全取消並清理 |
| 新程式自檢 | `esp_ota_mark_app_valid_cancel_rollback` | 重啟後回報「我 OK 了」 |
| 回退 | bootloader 自動 | 不需指令，靠 otadata 序號 |

---

## 9. 附註：對方協議的工程化程度

對方文件（`協議規格_slaveUART.md`）部分內容與實作脫節，例如：

- `MODE_SET` / `MODE_NEXT` 兩條重複（文件自述「排程相同，只為區分外部/自動」）。
- `STORY_SET`(0x05)、`BRIGHTNESS`(0x04) 的 native API 存在但實際走 `LIVE_TEXT` 文字通道。
- `AUDIO_LEVEL` / `AUDIO_ACTIVE` 無對應硬體。
- `INFO_QUERY` 與 `LIVE_TEXT` 功能重疊（都是文字透傳）。

正式對齊時這批應標註「棄用」，只保留真正有實作的語義。

## 相關文件

- `01_protocol/03_ota_protocol.md` — OTA 0x22xx 指令設計（本參考底稿的產物）
- `01_protocol/05_integration_overview.md` — 協議整合總規格
