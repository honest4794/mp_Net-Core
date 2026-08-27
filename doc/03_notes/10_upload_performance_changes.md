# 上傳效能改動清單與回滾指南（分批消化用）

> **用途**：逐項列出本輪對源碼做的所有改動，以及測試結果、如何開關、如何回滾。**所有優化預設關閉，不會影響現有行為**。
> **分類**：筆記（03_notes）
> **最後更新**：2026-08-27
> **相關文件**：`09_upload_performance_diagnosis.md`（診斷與數據）
> **狀態**：設備已還原（`master_port=8005`、`debug_level=1`、排程關閉、無 `net_rx_slots`），並已重連回 NetBusMaster

---

## 0. 總覽：改了哪些檔

`git diff` 確認的實際改動（11 個追蹤檔，共 +41 / -4 行）：

| # | 檔案 | 改動 | 目的 |
|---|---|---|---|
| 1 | `slave/lib/sys/net_bus.py` | recv 緩衝 `+8`；`net_rx_slots` 上限 4→64 | 修 WS 幀拆包 bug；解除插槽深度限制 |
| 2 | `slave/lib/sys/task.py` | Task 加 `interval_ms` 屬性 + `_next_run_ms` | 排程降頻的基礎欄位 |
| 3 | `slave/lib/sys/task_manager.py` | runner 加「時間未到就跳過」邏輯 | 協作式降頻（config 開關） |
| 4~11 | 8 個 task 檔 | 各加 `interval_ms = N` | 標記哪些是 standby 任務 |

> ⚠️ `tools/slave_map.json` 另有一處 `last_sha` 被改（`ad3d…→dccc…`）——這**不是我的改動**，是跑著的 NetBusMaster 重連時自動重新 hash 並回寫的。與效能無關，可忽略或自行還原。

---

## 1. 三組改動，分開消化

### 批次 A：chunk 大小（已生效，無需動程式）

現況：`upload_chunk_size` 在 `tools/slave_map.json` 與 `NetBusMaster.py` 的 DEFAULT_CONFIG 都是 **4096**（已提交的 HEAD 也是 4096，本輪無實質 diff）。

- 效果：停等吞吐 70 → ~240KB/s（1KB→4KB）
- 這是你已確認「1 已生效」的那一項
- 若想改回：把兩處 `upload_chunk_size` 改回 1024 即可

### 批次 B：recv 緩衝 bug 修復（建議保留）

`slave/lib/sys/net_bus.py`：`self._buf = bytearray(buf_size + 8)`（原 `buf_size`）。

- 修的是「4KB 幀被 TCP 拆成 4115+4 兩段」的 bug
- 實測：CHUNK_ACK RTT 16.87→15.11ms
- **無副作用**（只是 recv 緩衝多 8 bytes），建議保留
- 回滾：`git checkout slave/lib/sys/net_bus.py`（會連同插槽上限改動一起回滾，見 C）

### 批次 C：排程降頻 + 插槽深度（預設關閉，需 config 才啟動）

這組是「改了程式但不啟動」，靠 config 的 `Buffer.sched_interval_enable=1` 開關：

| 檔 | 改動 | 回滾方式 |
|---|---|---|
| `task.py` | 加 `interval_ms` + `_next_run_ms` | `git checkout slave/lib/sys/task.py` |
| `task_manager.py` | 加跳過邏輯 | `git checkout slave/lib/sys/task_manager.py` |
| 8 個 task 檔 | 各加 `interval_ms = N` | `git checkout slave/tasks/` |
| `net_bus.py` | 插槽上限 4→64 | 見批次 B |

**啟用方式**（想試才做）：slave `config.json` 的 `Buffer` 區塊加一行，重開機：

```json
"Buffer": {
    "sched_interval_enable": 1
}
```

**回滾方式**：`git checkout` 上述檔；config 那行刪掉即可。

---

## 2. 排程降頻的 interval 值（供你審視是否合理）

| task | interval_ms | 理由 |
|---|---|---|
| network | 0（每輪跑） | 延遲敏感，不能降 |
| bus_decode | 0（每輪跑） | 同上 |
| circuit | 1ms | UART 輪詢，1ms 足夠 |
| web_ui | 5ms | 網頁伺服器，5ms 響應足夠 |
| now | 5ms | ESP-NOW，5ms 足夠 |
| hw_sample | 5ms | 輸入採樣，5ms 足夠（人操作） |
| render | 10ms | 內部已有 50fps 節拍，外部再省一層 |
| log | 100ms | 純 log，100ms 綽綽有餘 |
| fs_scan | 100ms | 背景掃描，偶爾跑 |

> 這些值是我拍的，**沒有逐個真機驗證各功能的實際響應是否受影響**。若要正式上，建議逐個 task 確認降頻後功能仍正常（尤其 web_ui / hw_sample / render）。

---

## 3. 測試結果彙總（整晚自動化，每窗 5 次取中位數，sha 全過）

chunk=4096，單位 KB/s：

| 階段 | 窗 1（停等） | 窗 2 | 窗 4 | 窗 8 |
|---|---|---|---|---|
| BASELINE（原始） | 230 | 360 | 521 | 507 |
| A 排程 | 256 | 453 | **598** | 591 |
| B 插槽 | 229 | 370 | 506 | 505 |
| C 結合 | 253 | 450 | 578 | 566 |

**結論**：
1. **排程降頻有效**：單獨 +15~17%（窗 4 521→598）。
2. **插槽幾乎無效**：這板消費端夠快，2 槽已夠，加大無感。
3. **結合無加乘**：排程是主瓶頸，插槽不是。

---

## 4. 測試腳本位置（test/protocol/）

| 腳本 | 用途 |
|---|---|
| `upload_bench.py` | 停等吞吐基準（chunk 對比） |
| `upload_pipeline_bench.py` | 滑動視窗吞吐基準 |
| `probe_flush.py` | 寫入/statvfs 成本量測 |
| `probe_reply_path.py` | 收→解碼→回 ACK 各段成本 |
| `probe_sched2.py` | 各 task touch vs success（空轉率） |
| `probe_rtt2.py` / `measure_fix.py` | 每包 RTT 量測（含 bug 修復前後） |
| `overnight_test.py` | 整晚四階段自動化測試（含自動還原） |
| `deploy_multi.py` / `deploy_manifest.txt` | 多檔部署（已被 mpremote cp 取代，可刪） |

---

## 5. 下一步建議（供下個視窗決定）

1. **是否保留批次 B（recv bug 修復）**：低風險、真 bug，建議保留。
2. **是否上線批次 C（排程降頻）**：需先逐 task 驗證降頻不影響功能，再決定。
3. **滑動視窗（治本，未做）**：把 `NetBusMaster._upload_bytes()` 從「發一包等一個 ACK」改成「連發 4~8 包再等」，純 master 端改動，能到 ~520KB/s。這是把 70→500KB/s 真正落地的一步。
4. **下一道牆（520KB/s 之後）**：slave 端批量化寫入（收集 N chunk 才 flush 一次），風險較高，暫緩。
