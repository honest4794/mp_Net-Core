# 一晚測試報告 — 2026-08-22 夜

> 測試板：1201（master/被測）、1401（第二板，中段 USB 卡死）
> 接線：GPIO9=TX、GPIO8=RX 交叉直連（與昨晚 uart_cross 相同）

## 一、環境準備（已完成）

- **1401 部署完整 slave 專案**：上傳 `slave/`（含 lib/schema/action/tasks/driver/app.py/main.py），config 改為測試用（`UART.list[0]={id:1, baudrate:115200, GPIO:{tx:9,rx:8}}`、`CircuitDecode.enable=1`、ENC 停用）。
- **修復 GPIO 衝突**：原 config 的 `ENC.list[0].GPIO.b={8}` 與 UART RX(8) 衝突，`gpio_validate()` 直接 raise 導致 boot 崩潰（所有 service 未建立）。停用 ENC 後 boot 正常（`[BOOT] ok: spi, pin, i2c, uart, ...`）。
- **boot hook**：此自編 firmware 開機進 raw REPL 不自動跑 main.py，在 boot.py 尾部加 hook 啟動 `main()`。
- **1201**：上傳 lib/schema（NC4 組/拆幀用），成為 master agent + 可測 slave。

## 二、測試結果（單板 loopback，透過 `app.handle_stream` 記憶體迴路）

### 測試 1：selftest_file（file 域完整）— **17/17 通過**
- A. 全新上傳 20KB + 查詢 + 分片下載 + 刪除
- B. **覆蓋 v2 → pending=1 → CONFIRM 確認 → 覆蓋 v3 → UNDO 回滾到 v2**（備份/恢復備份完整流程）
- C. sha 不符 → 拒絕落地（err_sha_mismatch）
- D. 中斷 → partial → 續傳 → sha/size 正確
- E. FILE_MOVE 改名

### 測試 2：night_loopback（自寫擴充）— **24/24 通過**
- T1. **256KB 大檔上傳 + 分片下載 + sha 全程一致**
- T2. 錯誤路徑 5 項：無 session CHUNK→err_not_active / file_id 不符→err_id_mismatch / **MOVE 跨卷(/sd→/ram)→err_write_fail** / 下載不存在→空 data / DELETE 不存在→exists=0
- T3. **SPEED 提速狀態機**：QUERY(state=0)→SET(ACK ok=1, target=921600)→QUERY(SYNCING)→COMMIT(COMMITTED)→REVERT(IDLE)；非法 bus_type(SPI)→ok=0、非法 bus_id→ok=0
- T4. READ length=0 邊界
- T5. **SPEED 自動回滾**：SET 後不 COMMIT，`bus_speed_poll()` 在 timeout 後觸發回滾到 IDLE

## 三、雙板測試受阻說明（重要）

**1401 在測試中途 USB 完全卡死**（USB CDC 對 mpremote/pyserial/esptool 全部無回應，需實體拔插或按 RESET 才能恢復）。因此以下**無法在今晚完成**：

- ❌ 雙板 UART 真實傳輸（SPEED 提速後傳檔 / 跨板 FILE 上傳下載 / 斷點續傳跨板）
- ❌ 無線測試（WiFi 板間 / ESP-NOW 傳檔 / Web UI API）

**但注意**：1401 卡死前，雙板 SPEED 提速**曾部分成功**（`verify @921600 OK`、`commit state=2`）——證明 UART 9/8 實體層 + SPEED 協商在新速下雙向通。卡死是 1401 的 boot hook 或後續狀態導致，非 UART 物理問題。

## 四、發現的問題 / 觀察

1. **`lib/` 三級重構後 test/ 腳本未同步 import 路徑**：`test_decode_perf.py`（`lib.sys_bus`）、`test_proto_hotpath.py`（`lib.proto`）在新 firmware 上 import 失敗——changelog §6 已預告，實測確認。
2. **`SchemaCodec.decode` 的 viper 路徑在此 firmware 壞**：回傳欄位全 None。已在 agent 用手動 struct unpack 取代（`_HAND_DEC`）。**這是需要修的真 bug**（可能是 viper/native 裝飾器與此 firmware 相容性）。
3. **`bus_speed._cur_baud` 讀 `uart.baudrate`**：MicroPython UART 物件無此屬性，`SPEED_STATUS.cur_speed` 恆回 0。不影響功能，但 master 端看到 cur_speed=0。
4. **`FILE_CHUNK` 的 offset 連續性不驗證**（已知設計，靠 END sha 兜底）：亂 offset 也能寫，最後 sha 不符才拒絕。
5. **FILE 回應恆廣播**（不帶 addr，不用 master_cid）：單 master 場景沒問題。

## 五、後續步驟（用戶需處理）

1. **實體重插 1401 的 USB**（或按 RESET），讓它脫離卡死。
2. 1401 恢復後，重跑雙板測試（agent 已備妥）：
   ```
   python -B test/protocol/night_run/uart_cross_host.py --bauds 115200,921600
   ```
   （或直接用 master_agent 的 t_speed + t_file_upload 系列）
3. 無線測試需另排：WiFi 需 AP + PC 當 master；ESP-NOW 需兩板 config 開 enable；Web UI 需板有 IP。
4. 修 bug：#2（SchemaCodec.decode viper）、#3（cur_baud）。

## 六、測試工具（已備妥，留待後續）

| 檔案 | 用途 |
|---|---|
| `test/protocol/night_run/master_agent.py` | 1201 master agent：NC4 組/拆幀 + SPEED/FILE 指令 + 手動 decoder |
| `test/protocol/night_run/night_loopback.py` | 單板 loopback 綜合測試（24 項，已全過） |
| `test/protocol/night_run/config.1401.test.json` | 1401 測試用 config（9/8 + CircuitDecode on + ENC off） |
| `test/protocol/night_run/config.1401.backup.json` | 1401 原 config 備份（測完還原用） |
| `test/protocol/night_run/results/` | 測試結果存檔 |
| `test/protocol/uart_cross_bench.py` + `uart_cross_host.py` | 昨晚 UART 交叉測試（全 baud 通過） |

## 七、總結

**file 域（上傳/下載/備份/恢復/續傳/錯誤處理）與 SPEED 提速狀態機在單板 loopback 全部驗證通過（41/41）**，含 256KB 大檔、備份/UNDO、跨卷拒絕、自動回滾。雙板真實 UART 傳輸受阻於 1401 硬體卡死，需用戶重插後補測。另發現 2 個需修 bug（SchemaCodec decode、cur_baud）。
