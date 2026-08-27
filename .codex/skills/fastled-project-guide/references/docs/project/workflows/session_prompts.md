# Session Prompts 筆記

本文件整理本次 debug session 中有用的 prompt 模板，方便之後重複使用。

---

## 1. 要求用簡單語言解釋 commit

```text
could you explain it to me in simplest language:
<commit message> <commit hash>
<commit message> <commit hash>
```

用途：

- 快速理解每個 commit 改了什麼。
- 特別適合 I2C / UART / semaphore crash 這類硬體問題。

---

## 2. 檢查外部 UART sender 專案

```text
could you read the whole directory of '<path>',
this is the directory that sends UART signals for changing storyMode set, mode, brightness, or whether to enter servoStoryModes.
Our hiNu branch receives the UART signals from this program.
First find the root cause, then add debug log when receive the signals, and write the test program to verify send and receive processing.
```

用途：

- 同時檢查 sender 與 receiver。
- 適合找「sender 有送，但 receiver 沒反應」的問題。

本次結果：

- Mac sender 主要邏輯在 `tasks/action_task_1.py`。
- `ControlPanelTask` 讀 encoder，但在 `main.py` 被註解。
- `ActionTask1` 有 UART TX/RX，但沒有把 encoder delta 轉成 brightness。

---

## 3. 回報 master reboot log

```text
when I press the button that changes the storyMode to servoStoryMode, the master reboot?
master log:
<paste full crash log and backtrace>
```

用途：

- 讓 agent 從 log 找 reboot 位置。
- 若有 backtrace，應要求解碼。

建議後續 prompt：

```text
please decode this backtrace with the current master ELF and identify the exact function chain.
Do not guess from the log only.
```

---

## 4. 要求先 commit 某個檔案

```text
auto git uartController.cpp first
```

用途：

- 當工作區有多個不同目的的修改時，先提交某一類改動。

注意：

- 提交前要先 `git status --short --branch`。
- 不要混入 unrelated dirty files。

---

## 5. 判斷 log 是否成功

```text
very good, this log mean success?
<paste log>
```

用途：

- 快速判斷功能是否真的成功。

判斷方式：

- 先看是否 reboot。
- 再看狀態是否正確切換。
- 最後看 I2C/Slave 是否只是版本不一致造成 noise。

---

## 6. SERVO 結束模式需求

```text
servo storyMode_1 is the fadeout mode.
Set the last mode of servoStoryModes as the end of servo storyModes.
Discard the button message in this mode because it relates to the close of servo motors.
When the user presses the button, continue to run storyMode_1.
Record which storyMode of runStoryModeAll jumped into servoStoryModes.
After finishing servoStoryModes, continue the LED storyModes from the next mode.
For example: jump from Mode 3, finish servo, then start from Mode 4.
```

用途：

- 清楚描述 SERVO mode lifecycle。

本次實作重點：

- SERVO 最後 mode 忽略 button frame。
- LED -> SERVO 時記錄來源 LED mode。
- SERVO 完成後回來源 LED mode 的下一個 mode。

---

## 7. 更新 required Markdown

```text
could you update the required md file
```

用途：

- 提醒協議或行為改動後要同步文件。

本次需要更新：

- `docs/communication/external_uart/協議規格_timerUART.md`
- `docs/motor/servo_storymode.md`
- `docs/storymode/storymode目錄.md`

---

## 8. Brightness 旋鈕不敏感

```text
could you know why brightness is insensitive when rotate the button, no log changes?
log here:
<paste log>
```

用途：

- 分辨是 sender 沒送、master 沒收、還是 master 回報錯。

檢查順序：

1. 有沒有 `RX UART received`。
2. 有沒有 `RX SET decode ... brightnessSlot=X`。
3. 有沒有 `更新光度： X -> scaled to Y`。
4. Master 倒數 UART 是否把同一個 slot 回報出去。

本次 root cause：

- Mac encoder 沒接 brightness UART。
- Master slot 反推有 rounding 問題。

---

## 9. 要求先讀 Mac Python

```text
read the python code(Mac directory) first
```

用途：

- 避免只修 master，先確認 sender 是否真的送出 frame。

本次重要發現：

```python
# main.py
# tm.register_task("cpanel", ControlPanelTask, default_affinity=(1, 0), layer=1)
tm.register_task("motor", ActionTask1, default_affinity=(1, 0), layer=0)
```

`ControlPanelTask` 沒啟動，所以 encoder 沒有正常進入 brightness 流程。

---

## 10. 執行 master brightness slot 修正

```text
execute:
master remembers the last received brightnessSlot.
ACK and countdown UART should use this slot.
Do not convert brightness back to slot every second.
```

用途：

- 修正 master 回報 slot 不穩。

驗證：

```bash
python3 scripts/test_timer_uart_protocol.py
git diff --check
arch -arm64 pio run -e master
```

---

## 11. 最小有效 log 格式

貼 log 時，最好包含：

```text
[UART] RX UART received: [...]
[UART] RX SET decode: ...
[UART] RX SET result: ...
[UART] TX 亮度ACK: [...]
[UART] storyMode_X 倒數UART: [...]
[I2C] related errors if any
crash backtrace if reboot
```

這樣可以判斷：

- Timer/Mac 是否有送。
- Master 是否有收。
- Master 是否有改 state。
- Master 是否有 ACK。
- I2C/slave 是否另有問題。

