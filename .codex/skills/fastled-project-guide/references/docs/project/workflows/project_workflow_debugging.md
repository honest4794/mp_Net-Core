# Project Workflow 與 Debugging 筆記

本文件整理本專案常用工作流程，以及本次 Timer UART、SERVO storymode、I2C 與 brightness 問題的 debug 方法。

---

## 1. 開始任何修改前

1. 先讀：
   - `README.md`
   - `AGENTS.md`
   - 對應範圍的 `docs/*.md`
2. 先確認工作區：
   ```bash
   git status --short --branch
   ```
3. 不要覆蓋使用者未提交的檔案。若看到不相關 dirty file，只記錄並避開。
4. 若改 shared code，至少建置：
   ```bash
   arch -arm64 pio run -e master -e slave1 -e slave_standalone
   ```
5. 若只改 master-only code，可先建置：
   ```bash
   arch -arm64 pio run -e master
   ```

---

## 2. 建議修改流程

### 小修 master-only

適用：`firmware/master/src/*.cpp`、`firmware/master/include/*.h`

1. 看相關程式與協議文件。
2. 先加或更新最小測試。
3. 跑：
   ```bash
   python3 scripts/test_timer_uart_protocol.py
   git diff --check
   arch -arm64 pio run -e master
   ```

### 修改 shared code

適用：`firmware/shared/**`

1. 先確認 master、slave、standalone 是否都會編到該檔。
2. 避免 master-only 假設出現在 shared code。
3. 跑：
   ```bash
   python3 scripts/test_timer_uart_protocol.py
   git diff --check
   arch -arm64 pio run -e master -e slave1 -e slave_standalone
   ```

### 修改協議

適用：Timer UART、Video UART、I2C payload、story set bit

同一次變更要更新：

- `docs/communication/external_uart/協議規格_timerUART.md`
- `docs/motor/servo_storymode.md`
- 必要時更新 `docs/storymode/storymode目錄.md`
- 對應測試，例如 `scripts/test_timer_uart_protocol.py`

---

## 3. Timer UART Debug 流程

Timer frame 格式：

```text
[0xB4] [mode/set byte] [brightness slot] [remainSeconds] [0xFF]
```

Master 收到 Timer frame 時，應看到：

```text
[UART] RX UART received: [...]
[UART] RX SET decode: raw=... desiredSet=... modeId=... brightnessSlot=...
```

若只有看到：

```text
[UART] storyMode_X 倒數UART: [...]
```

這代表 master 正在 TX 給 Timer，不代表 Timer 有送 RX 給 master。

### mode byte

```text
bit7 = loop flag
bit6 = story set，1=SERVO，0=LED
bit5-0 = modeId
```

例子：

```text
0x06 = LED mode 6
0x41 = SERVO mode 1
0xC2 = SERVO mode 2 + loop
```

---

## 4. SERVO Storymode Debug 重點

目前 SERVO 組：

```text
mode 0 = storyMode_motor
mode 1 = storyMode_motor_reset
```

最後一個 SERVO mode 永遠視為關閉/復位模式。它正在跑時，不應被 Timer button 中斷。

預期 log：

```text
RX SET: SERVO end mode running, discard button frame modeId X
RX SET result: activeSet=SERVO currentMode=1 doStorySet=0 doMode=0 brightnessChanged=0 ackModeByte=0x41
```

從 LED 進 SERVO 時，master 會記錄來源 LED mode。SERVO 跑完後回下一個 LED mode。

例：

```text
LED mode 3 -> SERVO mode 0 -> SERVO mode 1 -> LED mode 4
```

預期 log：

```text
Servo 組入口：記錄 LED modeId 3，完成後返回 LED modeId 4
Servo 組完成一輪，自動切回 LED 組 modeId 4 (from LED modeId 3)
```

---

## 5. Master Reboot Debug 流程

若看到：

```text
assert failed: xQueueSemaphoreTake queue.c:1709 (( pxQueue ))
```

先解 backtrace：

```bash
xtensa-esp32s3-elf-addr2line -pfiaC -e .pio/build/master/firmware.elf <address1> <address2> ...
```

本次 root cause：

```text
receiveTimerUART()
-> resetModeState()
-> updateChannelStaging()
-> PWM_UPDATE_SAFE
-> xQueueSemaphoreTake(NULL, ...)
```

原因：

master 沒有跑 `initPwmTask()`，所以 `pwmBufferMutex == NULL`。shared 的 `resetModeState()` 直接呼叫 `updateChannelStaging()` 會讓 master reboot。

修法：

```cpp
if (pwmBufferMutex != NULL) {
    updateChannelStaging();
}
```

---

## 6. Brightness Debug 流程

### 現象

使用者旋鈕右轉應該增加 brightness，左轉應該降低 brightness。

Master 若真的收到 brightness frame，應看到：

```text
RX UART received: [0xB4, 0x06, 0x02, 0x0B, 0xFF]
RX SET decode ... brightnessSlot=2
更新光度： 2 -> scaled to 13
```

若沒有 `RX UART received`，代表 master 沒收到 Timer/Mac 送來的 frame。

### 本次找到的兩個問題

1. Mac 端 Python 的 encoder 沒有接到 brightness UART TX。
   - `main.py` 裡 `ControlPanelTask` 被註解。
   - `ActionTask1` 有 `set_display_state(brightness=...)`，但沒有 encoder 呼叫它。
2. Master 端原本用 `brightness` 反推 slot，會出現 rounding：
   ```text
   Timer 送 slot 2
   Master scaled brightness = 13
   Master 回報 slot 1
   ```

Master 端修法：

- 保存最後收到的 `brightnessSlot`
- ACK 和每秒倒數 UART 都回這個 slot
- 不再每次用 `brightness` 反推 slot

相關檔案：

- `firmware/master/src/uartController.cpp`
- `firmware/master/src/timerController.cpp`
- `firmware/master/include/timerController.h`
- `scripts/test_timer_uart_protocol.py`

Mac 端仍需補：

```text
encoder position 增加 -> brightnessSlot + 1 -> send UART
encoder position 減少 -> brightnessSlot - 1 -> send UART
```

---

## 7. I2C BAD PACKET 與 INVALID_STATE

常見 log：

```text
i2cWrite(): i2c_master_transmit failed: [259] ESP_ERR_INVALID_STATE
[I2C] <<< 0x14 BAD PACKET (rawLen=32, msgLen=41)
[I2C] [HEALTH] resetting I2C bus after repeated failures
```

判讀：

- 這不一定是 UART 問題。
- 若部分 slaves 尚未更新，可能會回舊格式或錯格式，造成 BAD PACKET。
- BAD PACKET 會讓 health log 很吵，也會讓 completed count 不準。
- 但本次 master reboot 的直接原因不是 I2C，而是 shared `resetModeState()` 呼叫 PWM staging。

Debug 順序：

1. 先看 UART RX 是否收到。
2. 再看 master 狀態是否改。
3. 再看 I2C 是否成功 broadcast 到 slave。
4. 最後才判斷 slave 是否正確執行。

---

## 8. 常用驗證命令

```bash
python3 scripts/test_timer_uart_protocol.py
git diff --check
arch -arm64 pio run -e master
arch -arm64 pio run -e master -e slave1 -e slave_standalone
pio device monitor -p /dev/cu.usbmodem1101
```

若本機 Python / littlefs 架構出錯，優先用：

```bash
arch -arm64 pio run ...
```

