# storyMode_motor_reset 設計規格

## 目標

新增 `storyMode_motor_reset` 作為 servo storymode 組的最後一個模式。`storyMode_motor` 完成後會先進入此 reset 模式；當 Timer UART 發送 bit6=0（要求切回 LED 組）時，也會先跳到此 reset 模式，以漸進式收回所有 servo 位置，再由既有 auto-switch-back 邏輯切回 LED 組。

## 行為

### State Machine

```
MOTOR_RESET_INIT -> MOTOR_RESET_CLOSE_TOP -> MOTOR_RESET_CLOSE_MID -> MOTOR_RESET_CLOSE_SKIRT -> MOTOR_RESET_CLOSE_LEGS -> MOTOR_RESET_END
```

- **INIT**：所有 RGB off，所有 servo hold 到展開位置（`MOTOR_FWD_LIMIT`），確保收回起點一致。使用獨立 state 變數 `modeMotorResetState`，不碰 `modeSignalsState`。
- **CLOSE_TOP ~ CLOSE_LEGS**：在 `storyMode_motor_reset.cpp` 內直接展開 close sequence 渲染邏輯（包含各 slave 的 servo fade-out、RGB、PWM LED）。每段使用 `stage_totalMs`。
- **END**：所有 RGB off、`chOriginMotors()`、`return true`。

### 總時長

30 秒（`STORYMODE_MOTOR_RESET_TOTAL_SECONDS`）。

## 切換觸發

`uartController.cpp` 中，當 `desiredSet == STORY_SET_LED` 且 `activeStorySet == STORY_SET_SERVO` 時：
- 不直接切換 `activeStorySet`
- 把 `currentModeId` 設為 `servoStoryModeCount - 1`（即 motor_reset 的 index）
- 啟動該 mode 的 timer
- motor_reset 跑完後，既有的 auto-switch-back 邏輯（`i2cController.cpp:496`）自動切回 LED 組

## 檔案變更清單

### 新增
- `firmware/shared/include/storymode/storyMode_motor_reset.h`
- `firmware/shared/src/storymode/storyMode_motor_reset.cpp`

### 修改
- `firmware/shared/include/globals.h` — 新增 `STORYMODE_MOTOR_RESET_TOTAL_SECONDS` 預設值
- `firmware/shared/src/storymode/storyModeController.cpp` — include + 註冊到 `servoStoryModes` 陣列
- `firmware/shared/src/storymode/storyModeController.cpp` — `resetModeState()` 加入 `modeMotorResetState` 重置
- `firmware/master/src/uartController.cpp` — bit6=0 切換時跳到 motor_reset 而非直接切 LED
- `docs/motor/servo_storymode.md` — 更新文件
- `docs/storymode/storymode目錄.md` — 更新文件
