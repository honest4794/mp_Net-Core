# 統一 Coding Style

本文件用於規範 agent 之後新增或修改 story mode 燈效時的寫法。目標是讓程式碼可以直接對照硬體接線、slave、RGB strip、PWM channel 與 motor pin。

製作流程與每個 story mode 應如何拆解、描述、記錄，先讀 `docs/storymode/storymode製作標準.md`；本文件只規範實際程式碼風格。

## 先確認 Project Topology

- 動 StoryMode 或 effect 前，先由 PlatformIO env、入口檔與 `STANDALONE_MODE` 確認 project 是 `master-slave`、`slave_standalone`，或同一 repo 同時支援兩者。
- `master-slave` 使用既有 transport/routing，StoryMode 依 `switch (slaveId)` 分派。
- 獨立 standalone project 直接使用已配置或使用者指定的 `slaveId` 執行同一套正式 StoryMode；target 只保留 standalone 所需入口與硬體路徑，不帶入 master routing。
- 同一 repo 同時支援兩種 topology 時，用既有 compile flags 隔離；不可為方便 standalone 而刪除另一個正式 target 的程式碼。
- Standalone 時序直接沿用 StoryMode 的累積 `if (time >= ...)`。不可用 macro、wrapper 或另一套 timeslot 重建相同演出。

## 新燈效位置

- 如果是新的可重用燈效，應寫在 `firmware/shared/src/lib/` 或 `firmware/shared/src/patterns/`，並在對應 header 宣告。
- 新燈效本身也要遵守本文件的可讀性要求：清楚、直接、容易追蹤硬體，不要為了少幾行而增加難讀的抽象。
- Story mode 只負責決定「哪個 slave、哪條 RGB strip、哪個 PWM channel、哪個 motor pin、何時使用哪個效果」。

## Story Mode 寫法

- 新生成燈效要直接寫在對應 `case slaveId` 裡。
- 每條 RGB、每個 PWM channel、每個 motor pin 按硬體順序逐一寫出。
- 實際 pin / strip 呼叫要在 `storyMode_*.cpp` 內清楚展開，不要藏到另一層 wrapper。
- 可以使用真正的底層效果函式，例如 `whiteSwipe(...)`、`gradientVentPalette(...)`、`GN_Wire_Normal(...)`。
- 參數仍放在 `storyMode_parameter`，但 story mode 內要清楚看到每條 strip / pin 如何使用這些參數。
- 中間流程與註解應優先寫 timeslot / stage / general description，例如「0:02-0:04 散氣口漸入」；effect name 只放在實際呼叫或旁邊註解。
- 註解格式建議同時保留中文部位與 effect name，例如 `// RGB2 散氣口 - gradientVentPalette / VentEffect`。
- 若同一 story mode 有兩段不同演出，例如 Breath All 與 Dynamic Flow，應在 state / case / 註解上清楚分段，不要混成一段長註解。

## 累積時間門檻與 Motor 順序

- 同一個 story mode state 內，若前一段效果需要持續，不要寫 close gate，例如不要寫 `if (time >= a && time < b)` 造成下一段開始後前段停止。
- 使用累積門檻寫法：`if (time >= 0) { ... }`、`if (time >= 2000) { ... }`、`if (time >= 4000) { ... }`。後面的 block 只新增下一組 slave / 下一段演出，前面的 block 會繼續每 frame 更新。
- 不要為了避免重複而新增 `renderBaseEffects`、lambda、macro 或 wrapper。需要持續的 RGB / PCA / motor 呼叫，直接留在該 slave 所屬的 open-ended block 裡。
- 對同一個 slave stage，先執行會寫入 `espMotor` buffer 的 `chServo*` / `chFadeIn` / `chFadeOut` / DC motor 呼叫，再接該 slave 的 RGB / PCA base effects。
- 分 stage 只表示「何時開始」，不表示「何時結束」。除非使用者明確要求 fade out / all off，否則下一 stage 不應自動關閉前一 stage 的效果。
- 若要把 helper 展開到 story mode 內，例如 `renderStoryModeInternalStructure(...)`，應直接寫底層 `chInternalStructure(...)` 與所需 state buffer，並保留每個 channel 的硬體註解。

## GPIO 呼叫註解標準

- 每個 RGB / PWM / motor / GPIO 實際呼叫前，都要有一行硬體註解。
- 註解內容優先從 Excel / 接線表複製，避免 agent 自行猜部位名稱。
- 格式應包含：channel、燈珠數或 channel index、部位、general description、effect name。
- 如果下一行有安全理由或 array 尺寸假設，應緊接寫在硬體註解後面。
- 範例：

```cpp
// RGB4 (12) 大腿-膝-小腿-腳掌 訊號 — SpecificColorPattern per-LED dispatch
// sm2::specificColor_ledColorIndex is sized 15, so 12-LED RGB4 is safely covered.
SpecificColorPattern(leds_RGB4, NUM_LEDS_RGB4,
                     specificColor_registry, specificColor_numPatterns,
                     specificColor_ledColorIndex);
```

## 避免的寫法

- 避免新增只包住效果的 helper / wrapper，例如 `renderSlave14PlatformStoryMode2Rgb(...)` 這類。
- 避免新增 macro render，例如 `RENDER_SLAVE2_SIGNAL_OPEN_STAGE(...)` 這類。
- 避免新增或沿用只為了隱藏 story mode 呼叫細節的 base effect gate，例如 `renderBaseEffects`、`renderMotorBaseEffects`、`renderStoryModeInternalStructure(...)`。
- 舊有 wrapper / macro 先保留，不主動重寫；本規則主要限制之後 agent 生成新效果時的寫法。
- 不可假設每個 slave 都有同樣 RGB strip。必須依 `platformio_local.ini` 的 LED strip 數量與 slave 硬體設定撰寫。
- 不要只寫「套用 SOP」或「同上」。每個 slave 的 strip / channel 必須能從程式碼直接看出。
- 不要在 story mode 內新增大範圍 unrelated refactor；重構只處理這次 story mode 需要的可讀性與時序問題。

## Story Mode 參數標準

- `platformio_local.ini` 負責本機硬體與 story mode 總秒數，不要把這些值當成通用設定。
- `storyMode_parameter.h` 放宣告、struct、instance 與 array。
- `storyMode_parameter.cpp` 放實際預設值與可調參數。
- 效果參數**模板**（如 WLED FX 的 `createDefault*` 工廠與 `InstanceArray<...>`）放 `storyMode_struct`；story mode 直接取用該 instance（例如 `wledOscillateInstances[0]`），不要在 story mode `.cpp` 內另外宣告一份 static 效果參數。
- 純屬某個 story mode 的**控制 static**（如 playlist slot 計時、目前 index）放 `storyMode_parameter` 的 `namespace sm_<modename>`，不要放成 story mode `.cpp` 內的檔案 static。
- Story mode 內不要為了組裝效果而新增 wrapper（例如 `renderDemoFxPlaylist()`）；playlist／切換邏輯直接寫在 story mode 內，每條 strip 的效果呼叫前保留硬體註解。
- 常見參數要命名清楚：速度、亮度、色盤、方向、cycle duration、fade in/out。
- 需要把多個參數傳入效果時，可使用 Pointer `*` 與 Reference `&`，但呼叫點仍要看得出參數來源。

## RGB Frame Rate 標準

- Story mode 的 RGB frame rate 由 `firmware/shared/include/globals.h` 的 `RGB_FREQUENCY` 控制，目前目標為 `60` FPS。
- `runStoryModeAll()` / `runStoryModeSingle()` / dev run loop 由 `storyModeController.cpp` 的 `showStoryFrame(frameStartMs)` 統一呼叫 `FastLED.show()`，並用整個 frame 已花費時間補足 `1000 / RGB_FREQUENCY` ms。
- 不要在 story mode 或 effect 內再直接呼叫 `FastLED.show()`；RGB、PWM、motor 呼叫只更新 buffer / staging，由 controller 在 frame 結尾統一輸出。
- 燈效速度必須用 `millis()`、duration、interval 或 `deltaTime` 控制，不要假設「每一 frame 加一次」等於固定速度。這樣把 FPS 從 50 改成 60 時，視覺速度不會變慢或變快，只會更新更平滑。
- 如果舊 effect 使用 per-frame counter 控制移動或淡入淡出，調整 FPS 時要同步檢查 `frameTimeMs`、step size 或改成時間差計算，避免高 FPS 造成動畫速度改變。
- 時序敏感路徑避免 `delay()`、heap allocation 與大量 logging；若某個 frame 實際運算超過目標 frame time，controller 不會補 delay，視覺上會掉幀。

## 建議格式

```cpp
case 1: {
    // RGB1 流光主燈帶 — whiteSwipe
    whiteSwipe(leds_RGB1, NUM_LEDS_RGB1, true, &whiteSwipeCounter[0],
               actualSwipeTime,
               CRGB(swipeBrightness, swipeBrightness, swipeBrightness),
               dropFirstBrightness);

    // RGB2 散氣口 — gradientVentPalette / VentEffect
    gradientVentPalette(leds_RGB2, NUM_LEDS_RGB2, &paletteIndex[1], scramableSpeed,
                        VentPalette, &lastScramable_palette[1], &scrambledValue[1],
                        lastUpdate_palette[1], fadeStateArr[1], &brightnessVent[1],
                        VentMaxBrightness[1], VentMinBrightness[1], cycleDuration, rangeOfIndex);

    // RGB3 漩渦 / GN Drive — GN_Wire_Normal
    GN_Wire_Normal(leds_RGB3, NUM_LEDS_RGB3, 2, false, white_gold2_palette);

    // RGB4 訊號 / 細節燈 — whiteSwipe
    whiteSwipe(leds_RGB4, NUM_LEDS_RGB4, true, &whiteSwipeCounter[4],
               actualSwipeTime,
               CRGB(swipeBrightness, swipeBrightness, swipeBrightness),
               dropFirstBrightness);
} break;
```
