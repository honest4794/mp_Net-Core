# 交接說明 — RS485 DE 處理 + rs485_hd 模組（2026-08-21 夜）

## 1. 改好的東西

### A. `slave/driver/uart_drv.py` — 20ms → 1ms
- `write()` 的 `time.sleep_ms(20)` → `time.sleep_ms(self.settle_ms)`，預設 **1ms**
- `_Rs485Uart.__init__` 加 `settle_ms=1` 參數
- `init_uart` 從 config 讀 `en_settle_ms`（沒設用 1ms）
- 實測依據：DE settle 0ms 不穩（start bit 被吃）、1ms 100% 穩定（多輪驗證）
- 注意：`txdone()` 等待（`_wait_sent`）保留——那是「送完才放低 DE」的正確同步

### B. 新模組 `ext_mod/mp_rs485_hd/`（mp_Net-Core 內）
- `modrs485_hd.c`：封裝 ESP-IDF `uart_set_mode(UART_MODE_RS485_HALF_DUPLEX)`
- `micropython.cmake` / `micropython.mk`：掛載檔
- 用法（Python）：
  ```python
  import rs485_hd
  rs485_hd.enable(1, de=7)   # UART1, DE=GPIO7 → 硬體自動控 DE
  uart.write(...)            # 全自動：硬體拉 DE、送完放 DE、清回波
  rs485_hd.disable(1)        # 恢復一般 UART
  ```
- 好處：**不用手動拉 EN、不用 sleep settle、不用 txdone 輪詢**，write 一 call 走人

## 2. 編譯結果

- ✅ firmware 編譯成功：`mp_Make-Tools/build/ESP32_GENERIC_S3_2026_08_21_06_01_18.bin`
- 模組已編進 firmware（`modrs485_hd.c.obj` 存在）
- 編譯方式（mp_Make-Tools 目錄）：
  ```bash
  python3 make.py esp32s3 --no-doctor --exmod mp_rs485_hd/micropython.cmake
  ```

## 3. ⚠️ 重要：板子狀態

- **1401（`/dev/cu.usbmodem1401`）firmware 掛了**——build 自動 flash 時用它預設 port 寫入，開機後無回應（REPL 不通、esptool 也進不了 bootloader）。
- **11401（`/dev/cu.usbmodem11401`）正常**（舊版 firmware，未動）。
- 1401 需要**實體按鍵**重刷：按住 BOOT → 按 RESET → 放開 RESET → 放開 BOOT，然後：
  ```bash
  cd mp_Make-Tools/lib/micropython/ports/esp32
  python3 -m esptool --port /dev/cu.usbmodem1401 --chip esp32s3 -b 460800 --before default_reset --after hard_reset \
    write_flash --flash_mode dio --flash_size 4MB --flash_freq 80m \
    0x0 build-ESP32_GENERIC_S3/bootloader/bootloader.bin \
    0x8000 build-ESP32_GENERIC_S3/partition_table/partition-table.bin \
    0x10000 build-ESP32_GENERIC_S3/micropython.bin
  ```
  （如果板子是 8MB flash，把 `--flash_size 4MB` 改成 `8MB`）

## 4. 待驗證（1401 修好後）

- [ ] 1401 重刷後 `import rs485_hd` 是否成功
- [ ] `rs485_hd.enable(1, de=7)` 後 ping-pong 是否全自動、成功率
- [ ] 對比：無 settle（0ms）vs 1ms vs rs485_hd 模式的穩定性

## 5. 測試數據回顧（這晚做的）

| settle | 成功率 | 結論 |
|---|---|---|
| 0ms | 漂移（0%~100%）| 不穩，靠運氣 |
| 1ms | 100%（多輪）| 穩定，安全線 |
| 20ms（原 driver）| 100% | 過度保守，白等 19ms |

- 寄存器版（mem32 控 DE + TX_DONE 輪詢）**證實不可靠**（TX_DONE raw 位被 MicroPython ISR 干擾，成功率 1/100）→ 不建議走
- 純 Python `uart.txdone()` 可靠（100%），但手動管理
- `rs485_hd`（C 模組）= 全自動 + 可靠，是終極解

## 6. mp_Net-Core git 狀態

- `slave/driver/uart_drv.py`（修改，已 tracked）
- `ext_mod/mp_rs485_hd/`（新增，untracked，待你 git add）
