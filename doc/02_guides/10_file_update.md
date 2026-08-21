# 檔案更新流程 — 上傳 / 下載 / 兩段式 commit / 斷點續傳

> **用途**：說明 `FILE_* 0x20xx` 檔案傳輸指令群的完整用法——怎麼上傳、怎麼下載、同名覆蓋怎麼確認/復原、斷線怎麼續傳。
> **分類**：使用教學（02_guides）
> **最後更新**：2026-08-21
> **位置**：`slave/action/file_actions.py`（handler）、`slave/lib/sys/fs_manager.py`（核心）、`slave/schema/file.json`（schema 唯一真相）
> **設計前提**：接收端完全被動、傳輸無關——TCP/WS、UART、ESP-NOW 送進來的幀都走同一條解碼路徑，Slave 照指令執行，不認得底層是什麼連線。

---

## 一、指令總表

| CMD | 名稱 | 方向 | Payload | 用途 |
|---|---|---|---|---|
| 0x2001 | FILE_BEGIN | 發 → 收 | `file_id(u16)` `total_size(u32)` `chunk_size(u16)` `sha256(bytes_fixed 32)` `path(str)` | 開始傳輸；同 path+size+sha 且存在 `.tmp` 時自動斷點續傳 |
| 0x2002 | FILE_CHUNK | 發 → 收 | `file_id(u16)` `offset(u32)` `data(bytes_rest)` | 傳輸塊 |
| 0x2003 | FILE_END | 發 → 收 | `file_id(u16)` | 傳輸完成 → 驗 sha → 兩段式 commit |
| 0x2004 | FILE_ACK | 收 → 發 | `file_id(u16)` `offset(u32)` | 逐 chunk 確認（offset 回聲） |
| 0x2005 | FILE_QUERY | 發 → 收 | `path(str)` | 查詢檔案 |
| 0x2006 | FILE_QUERY_RSP | 收 → 發 | `exists(u8)` `sha256(bytes_fixed 32)` `size(u32)` `path(str)` `free(u32)` `pending(u8)` | 檔案資訊 + 卷剩餘空間 + 待確認覆蓋 |
| 0x2007 | FILE_READ | 發 → 收 | `path(str)` `offset(u32)` `length(u16)` | 讀取片段（下載） |
| 0x2008 | FILE_CONFIRM | 發 → 收 | `path(str)` | 確認覆蓋：刪 `.bak` + 清 pending |
| 0x2009 | FILE_DELETE | 發 → 收 | `path(str)` | 刪除檔案 |
| 0x200A | FILE_UNDO | 發 → 收 | `path(str)` | 復原覆蓋：刪新檔 + `.bak` 改回 + 清 pending |
| 0x200B | FILE_SCAN | 發 → 收 | `target(u8)` | 掃描（0=本地 flash、1=SD） |
| 0x200D | FILE_MOVE | 發 → 收 | `src(str)` `dst(str)` | 通用改名/移動（走 manifest，不碰 delta；限同卷） |
| 0x200E | FILE_PARTIAL_QUERY | 發 → 收 | `path(str)` | 查詢斷點續傳進度 |
| 0x200F | FILE_PARTIAL_RSP | 收 → 發 | `partial(u8)` `written(u32)` `total_size(u32)` `sha256(bytes_fixed 32)` `path(str)` | 續傳進度（partial=1 才有效） |
| 0x2010 | FILE_ERROR_RSP | 收 → 發 | 7 個 `err_*` bool + `failed_offset(u32)` `written_up_to(u32)` `path(str)` | 失敗回覆（schema 自描述） |

> `FILE_ERROR_RSP` 錯誤 bool 群：`err_no_space` / `err_write_fail` / `err_offset_mismatch` / `err_id_mismatch` / `err_sha_mismatch` / `err_not_active` / `err_busy`。讀欄位名即知問題，不需查 enum。

> **chunk_size 參考值**：實測 sweet point = **4096**；其他 transport 參考值 RS485≈224 / I2C≈56。

---

## 二、資料結構（兩份 manifest + 一份 delta journal）

### 2.1 manifest 分離（依卷存放，不融合）

| 卷 | manifest 位置 | 內容 | 維護者 |
|---|---|---|---|
| 本地 flash | `/manifest.json` | 非 `/sd` 的檔案 | boot 掃描（跳過 /sd）+ FILE_* write-through |
| SD | `/sd/.manifest.json` | `/sd/...` 的檔案 | FILE_* write-through + `FILE_SCAN(target=1)` |

- 所有 FILE_* 指令對路徑的寫入/改名/刪除都會**同步更新對應卷的 manifest**（write-through），因此 manifest 本身就是紀錄，正常流程不需要全盤掃描。
- `FILE_QUERY` 依路徑前綴查對應卷的 manifest；cache miss 才 `os.stat` + 現場算 sha256。

### 2.2 delta journal（`/sd/.delta.json`，存 SD）

```json
{
  "partial": {
    "/sd/foo.bin": { "tmp": "/sd/foo.bin.tmp", "total_size": 12345, "sha256": "abc…" }
  },
  "pending": {
    "/sd/foo.bin": { "bak": "/sd/foo.bin.bak", "old_sha": "def…", "old_size": 1000, "new_sha": "abc…" }
  }
}
```

- **partial**：傳輸中（斷點續傳用），記「暫存檔路徑 + 目標大小 + 期望 sha」。`written` 不每包落盤，靠 `os.stat(.tmp)` 或 session 值導出。
- **pending**：已覆蓋待確認，記「備份路徑 + 新舊 sha + 舊大小」。

> 兩者皆**被動暴露**，Slave 開機不自動處理（設計為全被動 + 手動確認）。

---

## 三、上傳流程（寫入，需兩段式 commit + 斷點續傳）

```
【前置檢查】
  FILE_QUERY(path)
    → FILE_QUERY_RSP {exists, sha256, size, free, pending}
      sha 相同            → 跳過（不上傳）
      free < total + 餘量 → 中止（前置發現容量不足）

【續傳檢查】（斷線後重傳前）
  FILE_PARTIAL_QUERY(path)
    → FILE_PARTIAL_RSP {partial, written, total_size, sha256}
      partial=1 且 total_size+sha256 與本機一致 → 從 offset=written 續傳

【傳輸】
  FILE_BEGIN {file_id, total_size, chunk_size, sha256, path}
    → slave 若發現同 path+size+sha 的 .tmp，自動 seek(written) 續寫
  逐 chunk: FILE_CHUNK {file_id, offset, data}
    → 成功: FILE_ACK {file_id, offset}
    → 失敗: FILE_ERROR_RSP (err_no_space / err_write_fail / err_offset_mismatch / err_id_mismatch)
  中途斷線 → .tmp 留在 SD + partial 紀錄在案；重連後回到「續傳檢查」續傳
  FILE_END {file_id}
    → slave: 驗 sha → 兩段式 commit → 回 FILE_QUERY_RSP {pending}

【重啟 + 人工驗證】（由使用者操作，協議不需指令）

【收尾】
  成功: FILE_CONFIRM {path} → 刪 .bak + 清 pending
  失敗: FILE_UNDO    {path} → 刪新檔 + .bak 改回 + 清 pending
```

### 兩段式 commit（同名覆蓋）

FILE_END 驗 sha 通過後，slave 自動執行（initiator 不需、也不該額外下指令）：

```
1. 寫 pending delta
2. 舊檔 path → rename 成 path.bak   （舊檔絕不直接刪）
3. 新檔 .tmp → rename 成 path
4. 更新 manifest
```

- **全新檔案**（無舊檔）單段式：`.tmp → path`，無 pending。
- 覆蓋後 `FILE_QUERY_RSP.pending=1`，直到收到 CONFIRM 或 UNDO 才清掉。

---

## 四、下載流程（讀取，不需要 delta）

```
FILE_QUERY(path) → FILE_QUERY_RSP {sha256, size}
循環 FILE_READ {path, offset, length}
  → 回 FILE_CHUNK(file_id=0) {offset, data}
本地算 sha256 比對 = 檢查狀態
```

- 讀取不落盤、不改 manifest、不產生覆蓋問題，所以**不需要兩段式 commit / delta / 續傳**。
- 傳輸層 CRC32 已保證每幀內容正確。
- **檢查狀態**：只想確認檔案有沒有正確到位，`FILE_QUERY_RSP.sha256` 比對就夠，不需下載整份；要看內容/驗功能才用 FILE_READ。

---

## 五、通用操作

### FILE_MOVE（改名/移動）

```python
FILE_MOVE {src, dst}   # 只支援同卷（sd→sd 或 local→local），跨卷拒絕
```

- 走 manifest（舊條目搬到新鍵），**不碰 delta**——這不是覆蓋，沒有 confirm/undo 語義。

### FILE_SCAN（掃描）

```python
FILE_SCAN {target=0}   # 掃本地 flash（跳過 /sd）
FILE_SCAN {target=1}   # 掃 SD（重算 sha256，更新 /sd/.manifest.json）
```

- 這是安全網，供手動 REPL 寫入的檔案、老舊檔案、manifest 遺失/損壞時補救。正常流程靠 write-through，不需掃描。

### FILE_DELETE（刪除）

- 統一刪除：依路徑前綴路由，同步更新 manifest；RAM / SD-raw / FAT 各自更新 table。

---

## 六、容量不足的處理

**前置發現為主，中途報錯為安全網**：

- 前置：`FILE_QUERY_RSP.free` 比 `total_size + 餘量`（建議固定 64KB 或 config 可調），不夠就**根本不發**。
- 中途：`write_chunk` 真的寫失敗時回 `FILE_ERROR_RSP(err_no_space)`，initiator 乾淨中止。這是保險，不當主力。

---

## 七、斷線續傳的正確性保證

- partial 紀錄（`written`/`total_size`/`sha256`）只是「從哪個 offset 續傳」的**效能提示，不是正確性依據**。
- 正確性由 **FILE_END 對整份檔案重算 sha256、跟 FILE_BEGIN 帶的期望值比對**保證。就算 partial 記錯、續傳從錯誤位置開始、或某 chunk 寫壞，最後 sha 一定對不上 → 丟掉重傳。
- 最壞結果只是「多傳一次」，**永遠不會靜默留下壞檔**。

---

## 八、自測（loopback，單機即可）

`tools/selftest_file.py` 利用解碼器把「發起端」和「接收端」接在一起，同一顆 MCU 自己當 master 又當 slave：

```python
exec(open("/tools/selftest_file.py").read())
run_all()
```

涵蓋 5 個場景：全新上傳+下載+刪除、同名覆蓋+confirm/undo、sha 不符拒絕落地、斷點續傳、FILE_MOVE。真機（ESP32-S3, MicroPython 3.4.0）已驗證 **17 通過、0 失敗**。

---

## 相關文件

- `01_protocol/02_command_index.md` §8 — 指令索引（本文件指令表的收錄處）。
- `01_protocol/03_ota_protocol.md` — OTA 0x22xx（合作方合同，與 FILE_* 是不同鏈路）。
- `02_guides/01_fast_io.md` — SD 卡 raw 高速儲存（`fast_io.py`，與 `fs_manager.py` 是不同層）。
- `todo/01_file_update.md` — 檔案更新流程的測試追蹤清單。
