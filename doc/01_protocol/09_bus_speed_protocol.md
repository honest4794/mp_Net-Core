# 臨時提速（bus_speed）協商流程

> **用途**：傳輸大檔案前臨時拉高 UART baud，傳完還原；用 `hw` 群指令（0x1403-0x1408）。
> **分類**：協議層（01_protocol）
> **最後更新**：2026-08-21
> **位置**：`slave/lib/sys/bus_speed.py`（狀態機）、`slave/action/hw_actions.py`（handler）、`slave/tasks/circuit.py`（超時回滾檢查）。

## 同步流程（同步點 = SPEED_ACK 0x1404）

```
1. [舊速] master 發 SPEED_SET(0x1403: bus_type, bus_id, speed, timeout_ms)
2. slave 記 old_baud / target / timeout_at → 回 SPEED_ACK(0x1404, 舊速)
3. slave 送出 0x1404 後「同一 handler 內立即」uart.init(baudrate=target) 切速
   master 收到 0x1404 後立即切速
4. [新速] master 用既有 STATUS_GET(0x1101) / IDENTIFY_REQ(0x100D) 敲門驗證
5. 驗證 OK → SPEED_COMMIT(0x1405) 鎖定(取消回滾)
   ; 否則 timeout_at 到 → 自動回滾 config 舊速 → IDLE
6. 傳輸完成 → SPEED_REVERT(0x1406) 還原 old_baud
```

## 指令表（hw 群）

| CMD | 名稱 | 方向 | Payload |
|---|---|---|---|
| 0x1403 | SPEED_SET | M→S | `bus_type(u8)` `bus_id(u8)` `speed(u32)` `timeout_ms(u32)` |
| 0x1404 | SPEED_ACK | S→M | `ok(u8)` `bus_type(u8)` `bus_id(u8)` `cur_speed(u32)` `target_speed(u32)` |
| 0x1405 | SPEED_COMMIT | M→S | `bus_type(u8)` `bus_id(u8)` |
| 0x1406 | SPEED_REVERT | M→S | `bus_type(u8)` `bus_id(u8)` |
| 0x1407 | SPEED_QUERY | M→S | `bus_type(u8)` `bus_id(u8)` |
| 0x1408 | SPEED_STATUS | S→M | `state(u8)` `bus_type(u8)` `bus_id(u8)` `cur_speed(u32)` `target_speed(u32)` `remain_ms(u32)` |

- `state`: 0=IDLE, 1=SYNCING(已切、待 COMMIT), 2=COMMITTED(鎖定)。
- `bus_type` 沿用 `hw_manager.HW` 常數:UART=7, SPI=2, I2C=3。
- `speed` 用 u32(baudrate 如 921600 超 u16)。
- `timeout_ms` 是「沒 COMMIT 就回滾」的保險,不是 apply delay。

## 語意要點

- 唯一的「等待」是 `timeout_ms`(超時未定案就回滾 config 舊速),**沒有 apply_delay**。
- 「亂碼不回覆」是切速瞬間外部 bus 的自然現象,**本架構不偵測亂碼、不 auto-baud**。
- 回滾 = 純時間檢查,由 `CircuitTask.loop` 每輪呼叫 `bus_speed_poll()`;
  即使新速下收不到有效幀,loop 照跑、照樣回滾(解掉「收不到指令→惰性檢查不觸發」死結)。
- 第一階段**僅實作 UART**(bus_type=7);SPI/I2C 介面預留,`bus_speed_set` 回 `ok=0`(not supported)。

## 擴充 SPI / I2C（後續）

- 擴充 `bus_speed._get_uart` 為依 `bus_type` 分派到 `spi_list`/`i2c_list`。
- SPI/I2C 需 deinit + 重建(非 `.init` 一鍵),重建時保留原 GPIO/polarity/phase/addr 等建構參數(從 `bus.shared["SPI"]`/`["I2C"]` 讀)。
- 注意 SPI 為 TFT/SD 共用,提速期間需考量對顯示的影響。

## 相關文件

- `02_command_index.md` — 完整指令索引（本文件指令表收錄處）
- `03_notes/01_changelog.md` — 更新紀錄（本次提速更新的整合說明）
