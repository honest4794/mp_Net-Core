# Servo Storymode（伺服故事模式組）

本文件說明新增的 **servo storymode set**：一組與既有 LED storymode 並列、可由 Timer 切換的獨立故事模式。供開發者了解架構與新增方式。

---

## 1. 概念

系統現在有**兩組** storymode：

| 組別 | 陣列 | 用途 |
|------|------|------|
| LED 組（預設） | `storyModes` | 既有彩色 LED 燈效 |
| SERVO 組 | `servoStoryModes` | 伺服馬達動作為主的故事模式 |

由全域變數 `activeStorySet`（型別 `StorySetType`）決定目前作用中的組別。所有 storymode 的取用都透過 helper：

```cpp
StoryModeAndName* getActiveStoryModes();   // 回傳目前作用組的陣列
uint8_t           getActiveStoryModeCount(); // 回傳目前作用組的數量
```

兩組共用同一個 `currentModeId`；LED → SERVO 時會重置為 SERVO mode 0，並記錄當時的 LED mode。SERVO 組完整跑完後會回到下一個 LED mode。

> 目前狀態：`servoStoryModes` 有 2 個項目：`storyMode_motor`（可動模式，240 秒 / 4 分鐘）與 `storyMode_motor_reset`（復位模式）。最後一個 mode 永遠視為關閉/復位模式；它正在執行時會忽略 Timer button frame，避免中斷伺服馬達關閉流程。

---

## 2. 相關檔案

| 檔案 | 角色 |
|------|------|
| `firmware/shared/include/globals.h:9` | `enum StorySetType { STORY_SET_LED, STORY_SET_SERVO };` |
| `firmware/shared/include/globals.h` | `STORYMODE_MOTOR_TOTAL_SECONDS` 與 `STORYMODE_MOTOR_RESET_TOTAL_SECONDS` 預設 |
| `firmware/shared/src/globals.cpp` | `activeStorySet` 預設 `STORY_SET_LED` |
| `firmware/shared/src/storymode/storyModeController.cpp` | `servoStoryModes` 陣列、`servoStoryModeCount` |
| `firmware/shared/src/storymode/storyModeController.cpp` | `getActiveStoryModes()` / `getActiveStoryModeCount()` |
| `firmware/shared/src/storymode/storyMode_motor.cpp` | 目前 servo 組的可動模式實作 |
| `firmware/shared/src/storymode/storyMode_motor_reset.cpp` | servo 組復位模式，內建 top → mid → skirt → legs close sequence |

---

## 3. 切換流程（Timer → Master → Slave）

1. **Timer**：在 SET 指令的 `b1` 以 **bit 6** 帶組別（bit6=1→SERVO，bit6=0→LED），絕對狀態。詳見 [docs/communication/external_uart/協議規格_timerUART.md](../communication/external_uart/協議規格_timerUART.md)。
2. **Master**（`uartController.cpp`）：bit6 與目前組別不同時切換 `activeStorySet`。LED → SERVO 時從 modeId 0 開始，並記錄來源 LED mode；SERVO 完成後回到來源 LED mode 的下一個 mode。SERVO → LED 時不會直接切 LED，而是先跳到 servo 組最後一個 mode（`storyMode_motor_reset`），完成後才由 auto-switch-back 回 LED 組。
3. **Slave**（`i2cController.cpp`）：在 I2C receive ISR **即時**套用 `activeStorySet`；mode 指令則延後到 mode 邊界才執行。實際跑的故事由 `getActiveStoryModes()[currentModeId]` 在執行當下解析，因此 set 與 mode 收斂到同一真實來源、無 ordering race。

---

## 4. 如何新增一個 servo story mode

依專案慣例，新增 story mode 需同步更新「宣告、定義、註冊、時長、文件」：

1. **建立實作檔**：
   - `firmware/shared/include/storymode/servoStoryMode_1.h`（宣告 `bool servoStoryMode_1(uint8_t slaveId);`）
   - `firmware/shared/src/storymode/servoStoryMode_1.cpp`（實作；**完成時回傳 `true`**，未完成回傳 `false`）
2. **註冊到陣列**（`storyModeController.cpp` 的 `servoStoryModes`）：
   ```cpp
   StoryModeAndNameList servoStoryModes = {
       {storyMode_motor, "可動模式", STORYMODE_MOTOR_TOTAL_SECONDS},
       {servoStoryMode_1, "Servo 模式 1", SERVO_STORYMODE_1_TOTAL_SECONDS},  // 新增
       {storyMode_motor_reset, "復位模式", STORYMODE_MOTOR_RESET_TOTAL_SECONDS},
   };
   ```
   `servoStoryModeCount` 由 `sizeof` 自動計算，不需手動改。
3. **新增時長預設**（`globals.h`，比照 `STORYMODE_MOTOR_TOTAL_SECONDS`），並在 `platformio_local.ini` 可覆寫。
4. **時長對齊**：Timer 端顯示的倒數秒數必須與此處一致。
5. **modeId 上限**：bit5-0 → 每組最多 64 個 mode（0–63）。
6. **更新文件**：本檔與 [docs/storymode/storymode目錄.md](../storymode/storymode目錄.md)。

> 函式簽章 `bool story(uint8_t slaveId)`：每個 loop 被呼叫一次，回傳 `true` 代表該 mode 已播放完成（master 收到後推進下一 mode）。

---

## 5. 相關文件
- [docs/communication/external_uart/協議規格_timerUART.md](../communication/external_uart/協議規格_timerUART.md)：Timer UART bit6 切換協議。
- [docs/storymode/storymode目錄.md](../storymode/storymode目錄.md)：所有 story mode 清單。
- [docs/motor/motor_servo.md](motor_servo.md)：伺服馬達、PWM、PCA9685 / LEDC 資源限制與 API。
