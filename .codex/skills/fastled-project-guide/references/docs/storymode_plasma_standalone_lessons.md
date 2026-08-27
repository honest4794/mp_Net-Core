# StoryMode Plasma 與 Standalone 測試經驗

這份文件整理 Plasma 五階段調光、跨 slave 分組、PCA9685 effect 傳送與 standalone demo 測試時最容易誤解的地方。修改相關程式前，先確認使用者目前要求的 build 範圍與測試入口。

## 對話需求演變

本次工作由下列需求逐步收斂：

1. Build 範圍由 `master + slave7/8`，加入 `slave6`，最後限定為 `master、slave6、slave7`。
2. 暫時只測 `storyMode_plasma`，其他正式 story mode 不應因測試而永久改變 ID 或 routing。
3. Plasma Stage 2/3/4 經多次硬體觀察調整亮度、方向、分組、雷電速度與休息節奏。
4. 後續改用 `slave_standalone` 測試 PCA0 `0x40` CH0、CH6 的 Gundam eye wake。
5. Standalone demo 必須使用既有 `runStoryModeDemo()` 測試入口，不刪除 timer／timeout／模式輪播流程。

## 先判斷變更規模

- 小型變更：暫時註解或恢復 mode array、單一 build flag、地址、文字與註解。直接修改，再做基本 diff／語法檢查；不需要另寫 plan 或測試程式。
- 中型變更：單一 story mode 的 stage、亮度、顏色、速度或 group 調整。先確認硬體語意，修改後 build 受影響環境。
- 大型變更：shared API、跨 slave grouping、UART/I2C payload、記憶體配置。先列出影響面，再 build master、相關 slave 與 standalone。
- 使用者縮小 build 範圍後，以最新範圍為準，不沿用較早的環境清單。

## Plasma 五階段定案

### Stage 2

- 使用 `CRGB(5, 51, 10)` 的低亮綠色感，語意為約 5% 色彩。
- 使用 `RGBSeqOn()`，不是 `RGBSeqOnSteps()`。
- Fade-in 要短，但仍保持平滑。
- 分組順序：`{7,8} -> {6} -> {4,5} -> {3} -> {2}`。

### Stage 3

- 使用 `CRGB(255, 255, 255)`，形成與 Stage 2 明顯的亮度反差。
- 白色到最大亮度後 hold 3 秒。
- Fade-out 不是整台 slave 同時淡出，而是依 group 逐段 swipe out。
- Swipe 方向是燈帶尾端向 top。
- Plasma Stage 3 全域 brightness 使用 200/255，其餘 stage 使用 160/255；不要把 RGB 顏色值與 FastLED global brightness 混為一談。

### Stage 4A / 4B

- Stage 4 base color 為原色的 50% dim。
- Stage 4A：Stage 3 完成後立即讓五條身體路徑同步爆大雷，再行數個小雷。
- Transition：Stage 4A 用 300ms 短 fade-out 收尾。
- Stage 4B：73.8 秒平均分成五個 14.76 秒段落，同步洗牌播放 Random Thunder、Domino Accelerate、Cross Pair、Heartbeat、Storm Crescendo；每套都必定覆蓋全部五條身體路徑。
- 雷電不能看起來像固定速度的快速 comet，也不能所有燈帶同步。
- 每套編舞使用不同速度、亮度、持續時間與間隔；最快速度為原本上限，慢速要足以看見綠色 comet 的移動方向。
- 不要為了讓 comet 可見而額外加入短白色 moving head；需求只要求調低速度。
- 雷電與休息節奏使用動態範圍，避免固定「2.3 秒演出＋2.7 秒休息」反覆循環。
- Hi-Nu S1–S12 保留 cross 雷擊時間，由 S2 身體 hub 分成背包（含 S1 頭）、左手、右手、左腳、右腳五條路徑；只改次序與群組，每套不可遺漏部位。
- 六支 Funnel Gun S13–18 全部參與斜線 matrix，各自在 case 內以專屬 RGB pin 呼叫 cross；terminalBit top-down 順序為 `S18→S17→S16→S15→S14→S13`（terminalBit 0–5），再接 `S12 背包→S2 身體→S1 頭`。此背包路徑固定向下，抽中後一定接至少一條手／腳路徑。
- 五套 Stage 4B 身體編舞全部固定正向。

## 跨 slave group 寫法

當效果需要動態 grouping，使用 slave ID array 與 `RgbSeqStep` 表達，不把 group 隱藏在 helper：

```cpp
const RgbSeqStep plasmaStage2Steps[] = {
    {plasmaStepLowerLegs, 2},
    {plasmaStepRing2, 10},
    {plasmaStepRing1, 4},
    {plasmaStepBody, 1},
    {plasmaStepHead, 1},
};
```

Stage 4 branching cross 使用 `RgbVirtualBranchSegment` 的重疊 virtual start 表達
五條身體路徑；六支 Funnel Gun terminal rows 則依 top-down 次序串接：

```text
S2 身體: 0–49
├─ S3 左手上段: 50–99 → S4 左手下段: 100–149
├─ S5 右手上段: 50–99 → S6 右手下段: 100–149
├─ S13–18 Funnel (terminalBit 5–0): starts 5–0 → S12 背包: 67–96 → S2: 97–146 → S1 頭: 147–196
├─ S7 腰甲: 50–69 → S8 左腿上段: 70–189 → S9 左腿下段: 190–309
└─ S7 腰甲: 50–69 → S10 右腿上段: 70–189 → S11 右腿下段: 190–309
```

共用 API 需要知道目前 slave、group 內 slave IDs、LED buffers、LED 數量與 group count：

```cpp
uint8_t currentSlaveId,
const uint8_t* slaveIds,
CRGB* const* ledGroups,
const int* numLeds,
size_t groupCount
```

## Standalone storyMode_demo 正確測試入口

保留 `standaloneController.cpp::runStandaloneLoop()` 內所有正式流程，包括：

- `updateRunModeTimer()`
- `isStorymodeTimeout()`
- mode advance
- `resetPattern()` / `resetModeState()`
- `startRunModeTimer()`
- `runStoryModeAll(SLAVE_ID)`

不要為了測 demo 而刪除或改寫上述流程。

只在 `firmware/shared/src/ledController.cpp::runPattern()` 最前面的既有 `STANDALONE_MODE` 測試區塊暫時啟用：

```cpp
runStoryModeDemo();
return;
```

測試完成後重新註解這兩行。不要把 `storyMode_demo` 塞進正式 `storyModes` array，也不要為了符合 `StoryMode(uint8_t)` callback 而加入無用途的 `slaveId`。

Standalone PCA eye test 寫在 `storyMode_demo()` 的 `STANDALONE_MODE` 分支。PCA0 `0x40` CH0、CH6 使用：

```cpp
chGundamEyeWakeTwoStage(channelId,
                        eyeWakeCycleMs,
                        eyeWakeHoldMs,
                        eyeWakeMinBrightness,
                        eyeWakeStage1Brightness,
                        eyeWakeStage2Brightness);
```

目前效果為第一段 0.85 半正弦波在局部 0.5 升至 50% 峰值、於局部 0.85 回落後 hold 500 ms；第二段由該亮度升至 100% 峰值，再於第二個局部 0.85 亮度保持。參數放在 `storyMode_parameter` 的 `storyMode_demo_params`。

## PCA9685 effect 編號錯誤的根因

Arduino `String` 直接接 `uint8_t` 時，可能把值當成單一字元，而不是十進位數字。以下寫法會令 `LC:pwm` 的 channel/effect payload 損壞：

```cpp
command += ch;
command += effect;
```

正確寫法：

```cpp
command += String(ch);
command += String(effect);
```

若全部 `pcaLed` effects 都播放錯誤，先查看實際傳出的 `LC:pwm` 字串，再檢查 effect enum、address mapping 或效果函式；不要一開始就逐個重寫效果。

## AI 本次實際犯過／容易再犯的錯誤

以下不是假設案例，而是本次對話中 AI 實際出現或已走向錯誤方向的行為。後續 agent 遇到相同任務時應先檢查本表。

| 容易犯的錯誤 | 正確做法 |
| --- | --- |
| 把 thunder 做成固定速度 comet | 雷電使用不規則速度、亮度、密度與休息 |
| 所有 strip 雷電同步 | 每次 strike 使用獨立或可變 timing |
| 「速度 -400%/-500%」理解成加快 | 使用者語意是降低速度，讓移動方向可見 |
| Stage 2 使用 `RGBSeqOnSteps()` | 明確使用 `RGBSeqOn()` |
| Stage 3 整台 slave 同時 fade out | 依 `{7,8}->{6}->{4,5}->{3}->{2}` swipe out |
| 把 demo 加入正式 mode array | 使用 `runStoryModeDemo()` 測試 hook |
| 刪除 standalone timer 流程來跑 demo | 保留流程，只在 `ledController` 暫時 early return |
| 為 standalone demo 新增 `slaveId` | 保留原本 `bool storyMode_demo()` |
| 加入 `-USLAVE_ID` | Standalone 測試不需要取消或重定義 `SLAVE_ID` |
| 看到 PCA effect 錯就重寫所有 effect | 先 trace `LC:pwm` payload 與數字字串轉換 |
| 先懷疑 effect enum、address mapping、所有效果參數 | 先驗證共同傳送入口，找能一次解釋「全部效果錯誤」的根因 |
| 小修改先寫長 plan | 先量度規模；小修改直接做基本檢查 |
| 使用較早的 build 清單蓋過最新要求 | 每次執行 build 前重新確認使用者最後指定的 environment |
| Patch 後未看附近程式 | 立即執行 `git diff --check` 並查看修改區段 |

## 完成前檢查

- 確認最新 build 範圍，不使用過期要求。
- 確認 `storyMode_demo()` 沒有不必要的 `slaveId`。
- 確認 standalone timer／timeout／輪播程式仍完整存在。
- 確認 demo test hook 測完可以用兩行註解還原。
- 確認 PCA channel/effect 使用數字字串傳送。
- 修改 shared code 後，依使用者指定範圍執行 PlatformIO build。
- Standalone 若開 WiFi，RAM 使用率應維持約 76% 以下。
- 執行 `git diff --check`，並確認沒有 `}z` 等編輯 typo。
