# 檔案更新流程（FILE_* 0x20xx）

> **用途**：追蹤檔案更新流程的測試進度——上傳/下載/兩段式 commit/斷點續傳/manifest 分離。
> **最後更新**：2026-08-21
> **相關文件**：`doc/02_guides/10_file_update.md`、`doc/01_protocol/02_command_index.md` §8

## 已完成（loopback 自測，真機 ESP32-S3 / MicroPython 3.4.0）

`tools/selftest_file.py` 通過（17/17）：

- [x] A. 全新上傳 → sha/size 正確 → FILE_READ 下載片段 → FILE_DELETE
- [x] B. 同名覆蓋 → pending=1 → FILE_CONFIRM 保留新檔 → 再覆蓋 → FILE_UNDO 復原舊檔
- [x] C. sha 不符 → FILE_ERROR_RSP(err_sha_mismatch) → 檔案未落地
- [x] D. 斷點續傳 → partial_query 回 written → 重 BEGIN 續傳 → 完成後 partial 清空
- [x] E. FILE_MOVE 改名 → 原路徑消失、新路徑 sha 正確

## 待跟進（實測，非 loopback）

- [ ] **真實 MCU ↔ MCU 傳輸**（需先定送出通道：UART / ESP-NOW）
- [ ] **跨重啟斷點續傳**：傳到一半「重啟裝置」→ 開機後 FILE_PARTIAL_QUERY 能否回正確 written → 續傳完成
- [ ] **兩段式 commit 中途斷電**：舊檔→`.bak` 完成、`.tmp`→正式檔之前斷電，開機後 pending 紀錄狀態是否一致、能否 UNDO
- [ ] **大檔傳輸**（多 MB）記憶體壓力 + 吞吐量量測
- [ ] **容量不足**：前置 `free` 檢查中止 + 中途 `err_no_space` 報錯
- [ ] **跨卷 FILE_MOVE** 拒絕（sd→local 應回 err_write_fail）
- [ ] **manifest 分離驗證**：本地 `/manifest.json` 與 SD `/sd/.manifest.json` 各自獨立、互不污染
- [ ] **SD raw 模式**（`/sd/alloc.json` 存在時）下 FILE_* 走 FAT 區行為是否正常
- [ ] **pending 狀態跨重啟查詢**：覆蓋後重啟，FILE_QUERY_RSP.pending 仍 =1

## 已知問題 / 待決

- [ ] **回覆定址**：Slave 回應幀仍走廣播（`Proto.pack` 不帶 addr）。多節點 MCU↔MCU 需補「來源位址 + 回給來源」，建議單獨一輪做。
- [ ] **主動上傳腳本**：選 id → 選檔 → 驅動上傳 → 驗證 → confirm/undo，尚待定送出通道後實作。

## 筆記

- chunk_size sweet point = **4096**（實測）。
- 斷線續傳的正確性由 FILE_END 整檔 sha256 保證，partial 紀錄只是續傳 offset 提示。
