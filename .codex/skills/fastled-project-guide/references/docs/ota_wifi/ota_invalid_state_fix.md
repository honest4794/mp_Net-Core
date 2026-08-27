# Slave OTA 卡死問題調查與修復紀錄

**日期：** 2026-06-03
**分支：** `feat/wifi-update`
**影響檔案：** `firmware/master/src/i2cController.cpp`（master 端，零協議變更）

---

## 1. 症狀

實機批次 OTA 時觀察到兩種卡死：

### 症狀 A — master 卡在 readiness 檢查、無任何 log
```
[450342] [OTA] Checking if slave 2 is ready for OTA   ← 之後完全靜默
```
必須**手動重啟 slave** 才能恢復。

### 症狀 B — 傳到一半 I2C 進入 INVALID_STATE、狂噴錯誤不恢復
```
[954609] [OTA] OTA progress for slave 2: 31%
[955941][E] i2cRead(): i2c_master_receive failed: [259] ESP_ERR_INVALID_STATE
[955956] [OTA] WARN: No OTA response from slave 0x11
... (無限重複) ...
```

---

## 2. 根因

### 根因 A：`waitForSlaveReady` 無限迴圈 + 零長度誤判

- `waitForSlaveReady()` 原本是 `while(true)`，**無 timeout、不可取消**。
- slave 上一次 OTA 被中斷後卡在 `OTA_RX_STATE_RECEIVING`（沒回 IDLE）。
- 此時 slave 的 `requestEvent`（`firmware/slave/src/i2cController.cpp:304-307`）對 readiness ping **回零長度**（`writePaddedResponse(nullptr, 0)`）。
- master 端只接受「非空且非 SETUP 字串」，讀到 `length==0` 就跳過 → 永遠空轉、連 log 都不印。
- **諷刺點：** 能解卡的 `abortSlaveOTA()` + `OTA_CMD_START`（slave `handleStartCommand` 對 RECEIVING/ERROR 會自動 `reset()`）被擋在這個過不了的 readiness 檢查後面 → 只能手動重啟。

### 根因 B：`transferFirmwareChunk` 缺少 INVALID_STATE 復原（regression）

- ESP32 Arduino Core 3.x 在 400kHz 高速、密集 `requestFrom` 下，master I2C 周邊會進入 `ESP_ERR_INVALID_STATE`。
- 修復方式應為 `resetI2CBus()`（`Wire.end()` + 9 clock pulses + `Wire.begin()`）完整重初始化；單純改 clock 無效。
- 我們分支的 transfer poll 迴圈**沒有**這個復原 → 一旦進入 INVALID_STATE 就永遠卡住。

#### Regression 歷史（精準追到 commit）

`transferFirmwareChunk` 內 `resetI2CBus` 次數時間軸：

| commit | 日期 | transfer 內 reset 次數 | 說明 |
|---|---|---|---|
| `0a4f4515` / `7906fd` | kampfer, 5/18 | 1 | 原始修復「Fix I2C bus not recovering from ESP_ERR_INVALID_STATE」 |
| `ac13ab9` | 我們分支, 5/20 16:00 | **1 ✅** | 正確 port 0a4f4515 進 `feat/wifi-update` |
| `4914b66` | 我們分支, 5/20 16:24 | **0 ❌** | 「Port adaptive I2C（0dc57ddb）」時**覆蓋並刪掉**了那段 reset ← regression 發生點 |
| HEAD | — | 0 | 一直缺到本次修復 |

`4914b66` 的 diff 鐵證：
```diff
-        LOG_WARN("No OTA response for chunk %d, resetting I2C bus and retrying", chunkNumber);
-        resetI2CBus();
-        Wire.setClock(otaManager.getCurrentI2CFrequency());
+        if (sawNonOTAResponse) { ... }            // 0dc57ddb 的 adaptive 邏輯
+        LOG_WARN("No OTA response for chunk %d, treating as NACK and retrying", chunkNumber);
         return otaManager.handleSlaveResponse(OTA_RESP_NACK, chunkNumber);
```
即：adaptive I2C（sawNonOTA/corrupt）邏輯蓋上去時，順手刪掉了 INVALID_STATE 復原。kampfer v4/v5/v6 也是同樣方式弄丟（只有 `dev_Kampfer_v1` 的最終檔案保住）。

---

## 3. 本次修復（全在 `firmware/master/src/i2cController.cpp`）

1. **`waitForSlaveReady` 加 30s timeout** — 逾時 `return false`，不再無限卡死。
2. **`waitForSlaveReady` 零長度放行** — `length==0`（slave 活著但 OTA 卡非 IDLE）直接 `return true`，讓後續 `abortSlaveOTA()` + `OTA_CMD_START` 自動把 slave reset 回 IDLE → **免手動重啟**。
3. **`startSlaveOTA` 接收 `waitForSlaveReady` 回傳值** — false 就 `return false` → `performSlaveOTA` 判失敗 → 前端跳下一台（符合批次「單一失敗不影響其他」）。
4. **`transferFirmwareChunk` 重新接回 INVALID_STATE 復原** — 真正零回應時 `resetI2CBus()` + 重設 clock 再重試；同時**保留** 4914b66 的 adaptive 邏輯（`sawNonOTAResponse` legacy / `corruptOTAResponses`），只在「真的完全沒回應」時 reset，slave 還活著（legacy/corrupt）時不誤重置。比原始 0a4f4515 更精準。
5. **`performSlaveOTA` 四個錯誤出口加 `resetI2CBus()`** — 失敗的 slave 把乾淨 bus 交給批次下一台。

> `downshiftI2CClock` 的 `resetI2CBus` 本來就在（ac13ab9 port 時保住了）。

**驗證：** `pio run -e master` 編譯成功。實機測試待進行（重現症狀 A/B 確認自動恢復）。

---

## 4. 與 kampfer 分支比對結論

| 修復 | kampfer 現況 |
|---|---|
| `waitForSlaveReady` timeout + 零長度 + 接回傳值 | **任何分支都沒有**，本次全新 |
| `transferFirmwareChunk` INVALID_STATE 復原 | `0a4f4515`/`7906fd` 修過，但只剩 `dev_Kampfer_v1` 最終保住；v3/v4/v5/v6 與我們都被 `0dc57ddb` 覆蓋弄丟 |
| concurrent OTA task（`fc379465`）、adaptive telemetry（`0dc57ddb`）、jQuery bundle（`be25d`）、wifi init（`f06887`）| 已在我們分支 |
| SPIFFS format-retry（`2fb4e622`）| **不移植**：SPIFFS 專屬（我們用 LittleFS）、與本 bug 無關，且 `LittleFS.format()` 會連帶清掉同分割區的 web UI（`/html/*`），危險。**佐證：** `23d1e0`（已在本分支）遷移 LittleFS 時已**刻意刪除**此 format-and-retry 區塊 |

**結論：merge 任何 kampfer 分支都拿不到完整修復**（reset 已遺失 + `waitForSlaveReady` 那組根本沒有）。維持本分支自行修復。

---

## 5. 待決事項（與本 bug 無關，另案處理）

### `b2d022`「hotfix」— sticky dev mode

- 內容：新增 `devModeSticky`，讓「post-OTA 開機進 dev mode」與明確「`Mode: dev`」不被 master poll 踢出。
- **無法直接移植**：我們分支的 dev mode **只有 master-timeout fallback 一個進入點**（`ledController.cpp:109`），沒有「post-OTA→dev mode」也沒有「`Mode: dev` 指令」。b2d022 的 2 個 hunk 在我們分支找不到目標。
- 真要這個行為，須先把 kampfer 的「post-OTA→dev mode + `Mode: dev`」整套功能移植過來（獨立任務、範圍較大）。
- b2d022 另含 `FORCE_WIFI_ON` 測試 build flag（`powerCycleDetector.cpp` `#ifdef`，自包覆可單獨移植）與 `platformio_local.ini` 一行註解（本機設定，不照搬）。

**決議：** 待使用者選擇 —（a）整套 port post-OTA dev mode 功能、（b）只加 FORCE_WIFI_ON、或（c）暫不處理。
