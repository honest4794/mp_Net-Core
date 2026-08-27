# Batch Slave OTA Update - Implementation Plan

## Goal
用戶為每個 slave 指定各自的 .bin 韌體檔案 → 前端依序上傳+更新 → 單一 slave 失敗不影響其他

---

## Architecture: Frontend-Driven Sequential Update

**核心設計決策：** 每個 slave 有不同的 firmware，且 ESP32 LittleFS 空間有限（約 1.2MB，還要放 WiFi UI）。後端不再把 slave firmware 暫存到 LittleFS，改由 master 以 PSRAM/RAM buffer 暫存當前上傳檔案，再直接透過 I2C 傳給 slave。因此採用前端驅動方案：

- **後端維持單一 slave OTA API** — `/slave_upload?slaveId=N` 行為不變，但 master 內部改用記憶體 staging
- **前端排隊** — 瀏覽器暫存所有 File 物件，依序上傳
- **每次只 stage 一個 firmware** — 不再受 LittleFS 剩餘空間限制

```
User → slave.html → 為每個 slave 選擇 .bin 檔案
                   → 點擊「開始批次更新」
                   → 前端依序執行:
                      1. POST /slave_upload?slaveId=1 (上傳 slave 1 的 firmware)
                      2. Poll /slave_status?slaveId=1 (等待 OTA 完成)
                      3. POST /slave_upload?slaveId=2 (上傳 slave 2 的 firmware)
                      4. Poll /slave_status?slaveId=2 (等待 OTA 完成)
                      5. ... repeat ...
                      6. 顯示批次結果摘要
```

---

## Feasibility: YES

| 改動 | 難度 | 風險 |
|------|------|------|
| 前端 per-slave file UI | 中 | 低 - 純 UI 改動 |
| 前端 batch queue 邏輯 | 中 | 低 - 使用既有 API |
| 後端 staging | 小 | 低 - API 不變，只把暫存位置由 LittleFS 改為 PSRAM/RAM |

**不會造成 slave 變磚** - ESP32 OTA 使用雙分區保護

---

## Why Frontend-Driven (Not Backend Batch)

| 考量 | 後端 batch (已棄用) | 前端 batch (採用) |
|------|---------------------|-------------------|
| 不同 firmware per slave | 不支援 (共用 batch.bin) | 支援 |
| LittleFS 空間 | 需同時存多個 firmware | 不使用 LittleFS 暫存 slave firmware |
| 後端改動 | 大 (新增 struct/endpoint/callback) | 小（API 不變，staging 改用 PSRAM/RAM） |
| 瀏覽器需保持開啟 | 否 | 是 |
| 複雜度 | 高 (thread safety, CRC 保留) | 低 |

---

## Current Architecture

```
User → slave.html → POST /slave_upload?slaveId=N
                  → firmware staged in master PSRAM/RAM buffer
                  → pendingSlaveOTA = N (triggers OTA task)
                  → FreeRTOS Task runs performSlaveOTA(N)
                  → cleanupStorage(N) releases staged firmware buffer
                  → Done
```

**Key Endpoints (existing, unchanged):**
- `POST /slave_upload?slaveId=N` — 上傳 firmware 並啟動 OTA
- `GET /slave_status?slaveId=N` — 查詢 OTA 進度
- `GET /available_slaves` — 取得在線 slave 列表

---

## Files Modified

### `data/html/slave.html` (唯一修改的檔案)

#### Step 1: Per-slave file assignment
```
┌────────────────────────────────────────────┐
│ Step 1: 為每個 Slave 指定韌體               │
│ [重新掃描]                                  │
│ ┌────────────────────────────────────────┐ │
│ │ Slave 1 (0x10) [選擇檔案] fw_a.bin    │ │
│ │ Slave 2 (0x11) [選擇檔案] fw_b.bin    │ │
│ │ Slave 3 (0x12) [選擇檔案] (未選擇)     │ │
│ │ Slave 4 (0x13) [選擇檔案] fw_c.bin    │ │
│ └────────────────────────────────────────┘ │
│ 已選擇 3 個 Slave 的韌體                    │
│                                            │
│ [開始批次更新 3 個 Slave]                   │
└────────────────────────────────────────────┘
```

#### Step 2: Batch progress
```
(During update):
┌────────────────────────────────────────────┐
│ 批次更新進度: 2/3                           │
│ ├─ Slave 1: 完成                           │
│ ├─ Slave 2: 上傳中 (45%) / I2C 傳輸 (67%) │
│ └─ Slave 4: 等待中                         │
│                                            │
│ [========----] 67%                         │
│ 速度: 25 KB/s | 剩餘: ~45 秒               │
└────────────────────────────────────────────┘

(Complete):
┌────────────────────────────────────────────┐
│ 批次更新完成                                │
│ 成功: 3 | 失敗: 0 | 總耗時: 2 分 15 秒     │
└────────────────────────────────────────────┘
```

---

## Frontend Data Structures

```javascript
let slaveFiles = new Map();  // slaveId → File object (browser memory)
let batchQueue = [];         // [{slaveId, file}, ...] ordered list
let batchIndex = 0;          // current position in queue
let batchResults = [];       // [{slaveId, success, error?}, ...]
let batchStartTime = 0;
let batchActive = false;
```

---

## Flow Diagram

```
[User assigns .bin files to slaves 1, 2, 4]
        |
[Click "開始批次更新"]
        |
[batchQueue = [{1, fw_a.bin}, {2, fw_b.bin}, {4, fw_c.bin}]]
        |
[processNextInBatch() → batchIndex=0]
        |
[POST /slave_upload?slaveId=1 with fw_a.bin]
        |
[Upload progress: 0-50% on progress bar]
        |
[Upload complete → poll /slave_status?slaveId=1]
        |
[I2C transfer progress: 50-100% on progress bar]
        |
[OTA complete → batchResults.push({1, true})]
        |
[processNextInBatch() → batchIndex=1]
        |
[POST /slave_upload?slaveId=2 with fw_b.bin]
        |
... repeat ...
        |
[All done → show summary: "3 成功, 0 失敗"]
```

---

## Failure Handling

| Scenario | Behavior |
|----------|----------|
| Slave N OTA fails | Record failure, continue to next slave |
| I2C timeout | Retry with adaptive clock, then fail and continue |
| All slaves fail | Show all failures in summary |
| Browser closed mid-batch | Current slave may complete, remaining queue lost |
| Upload to master fails | Record failure, skip to next slave |

### Rollback Safety
- ESP32 dual partition: failed write keeps old firmware
- Slave will not brick

---

## Backward Compatibility

- Backend API 完全不變
- `POST /slave_upload?slaveId=N` 仍然正常運作
- `GET /slave_status?slaveId=N` 仍然正常運作
- 選擇單一 slave 時，行為等同原始單一更新流程

---

## Constraints

- **瀏覽器必須保持開啟** — 前端驅動排隊，關閉瀏覽器會中斷剩餘隊列
- **每個 slave 需個別選擇 .bin 檔案** — 不支援「一個 firmware 給所有 slave」
- **依序執行** — 同一時間只有一個 slave 在更新

---

## Testing Plan

1. **Single slave:** 只為一個 slave 選擇檔案，確認行為與原始 UI 相同
2. **Multi slave:** 為 3 個 slave 選擇不同 .bin，確認依序更新完成
3. **Failure test:** 中途拔掉一個 slave 的 I2C，確認其他 slave 仍然完成
4. **UI test:** 確認每個 slave 的狀態圖示正確更新（等待/上傳/傳輸/完成/失敗）
5. **File validation:** 確認選擇非 .bin 檔案或過大/過小檔案時顯示錯誤
