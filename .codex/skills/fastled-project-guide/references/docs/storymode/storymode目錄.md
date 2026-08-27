# Story Mode 目錄

快速查詢所有 Story Mode 在各分支的位置。

製作新 story mode 前，先讀：

- `docs/storymode/storymode製作標準.md`：workflow、文件標準、general name / effect name 分工。
- `docs/project/standards/uniform_coding_style.md`：實際程式碼展開方式與避免的 wrapper/macro 寫法。

## 目前硬體範圍

- 正式 story mode 目前分派 Slave 1–10；Slave 10 是新增的 Foulyoupou platform，Slave 11–14 仍非本專案正式範圍。
- Slave 1 與 Slave 3 的專屬分支只可操作 RGB1–RGB4；RGB7 以上屬其他 Slave，不可放進 `case 1` 或 `case 3`。
- 指定模式在函式層級用 `if (slaveId == 3)` 更新 PCA0 `0x51` CH0、CH6 的 `chGundamEyeWakeTwoStage()`；protected output 會在 PWM buffer copy 前最後套用，避免 `chOff()`、`chOffAll()`、`chOffLeds()`、整板 random flash 或其他 channel effect 中斷眼燈。
- 上述限制只清理 story mode；PlatformIO environment 與本機硬體設定不在此文件範圍。


## 正式 Controller Story Modes

以下清單以 `storyModeController.cpp` 的 LED 與 servo arrays 為準。目前 LED list 的 12 個 entries 全部註冊；`storyMode_develop` 為 LED mode 0，`storyMode_all_off` 不再註冊。

| Story Mode | 名稱 | Controller 狀態 | 設定時長 | Description |
| --- | --- | --- | --- | --- |
| `storyMode_develop` | 開發模式 | **LED mode 0，已啟用** | 32 秒 | 0083 試作機展示；Slave 3 RGB2 使用 5 秒 `smoothSineBreath` 冰藍呼吸；所有 RGB4 訊號燈全部啟用。Slave 4–8 只選主要 PCA 白／暖白部位，每組約 8–11 粒，平均分佈於肩／手腕、前裙甲、腳掌、膝部及內構；Slave 1–8 估算輸出約 17%，Slave 9／10 mapping 未確認保持全關。 |
| `storyMode_signals` | 訊號模式 | **LED mode 1，已啟用** | 32 秒 | 先清空 RGB 並等待 2 秒，再持續播放各 Slave 的 RGB／PCA 訊號；Slave 4–8 彩色訊號效果保留，白／暖白燈沿用 Develop 的主要部位平衡配置，每組約 8–11 粒；不包含 motor／servo sequence。 |
| `storyMode_0_v1` | 亮點模式 v1 | **LED mode 2，已啟用** | 31 秒 | 眼燈以 two-stage 0.85π sine 經過 1200／2400 peak 後保持；RGB1 白色 comet 由 Slave 3 胸口掃入，於 virtual index 50 分流到腰腿（6→7/8）、背包（2）與左右手臂（4/5）；由 `MODE_0_FLASH` 起 global brightness 降至 `40/255`，收尾還原一般亮度。 |
| `storyMode_awakening_3` | 蘇醒模式 3 | **LED mode 3，已啟用** | 63 秒 | RGB1 使用 FastLED global 90/255、local 15–210 與固定綠色 `CRGB(15,255,25)`；以 6 秒 branching V3Cross 由 Slave 3 胸口掃入，胸口完成後分流至背包、手臂及腰部，腰部完成立即接左右腿；之後以 `smoothSineBreath` 同款 16-bit 曲線持續呼吸，comet 為純白色、size `3`，不使用黑色核心；60 秒後淡出並恢復一般 global 60/255。其他 RGB 保持關閉，PCA 維持較低亮度蘇醒演出。 |
| `storyMode_activation` | 覺醒模式 | **LED mode 4，已啟用** | 60 秒 | RGB1 使用 branching cross effect：取消開場 fade-in，立即顯示 8% 暗綠背景與 1→5 個 `CRGB(15,255,25)` comet；速度由 7 秒／圈平滑加快至 3 秒／圈，每圈明確由 virtual index 0 重啟。胸口後分流至背包、手臂及腰部，腰部完成立即接雙腿；57 秒後淡出。Slave 4 RGB7 純紅常亮。 |
| `storyMode_0_v2` | 亮點模式 v2 | **LED mode 5，已啟用** | 27 秒 | Two-stage 眼燈在起始閃、亂閃、分段全亮／全暗期間保持 protected；由 `MODE_0_FLASH` 起 global brightness 降至 `40/255`，最後 500ms sine fade-out 並還原一般亮度。 |
| `storyMode_storing_energy` | 儲氣模式 | **LED mode 6，已啟用** | 36 秒 | 六階段儲能：跨 Slave comet／Tetris 填充 → 5% 暗伏 → 90/255 power-up → 50% 回落 → 140/255 full power；眼燈獨立保持至最後 500ms sine fade-out，再全關。 |
| `storyMode_2` | 長著模式 | **LED mode 7，已啟用** | 87 秒 | 2 秒眼燈後進入 75 秒 base state；Slave 1–20 全部以 RGB1 播放白色 branching `RGBSeqOnV3` meteor：S1 頭 → S2 身體後分流至左右手臂、腰甲／雙腿及背包；背包 branch 再依序通過 S13 → S14 → S15 → S16 → S17 → S18 六支 Funnel Gun，並持續循環。其他 RGB／PCA 分段效果維持，眼燈保持 protected，最後 500ms sine fade-out。 |
| `storyMode_plasma` | 電漿模式 | **LED mode 8，已啟用** | 90 秒 | 5-stage 電影式電漿演出：PCA 前導 → RGB1 分組亮起 → 全白爆光及擦除 → Stage 4A 大雷前導 → Stage 4B 五套不重複綠雷編舞與獨立平台雷電 → 分組收光。 |
| `storyMode_trans_am` | 轉換模式 | **LED mode 9，已啟用** | 78 秒 | 不重播 sequential-on；Slave 3–8 的 RGB1 統一使用綠色 `GN_Drive_Running`，並維持高能 Trans-Am RGB／PCA 效果 75 秒，再整體淡出。 |
| `storyMode_3` | 呼吸模式 | **LED mode 10，已啟用** | 153 秒 | 第三輪測試使用 FastLED global 90/255；2 秒眼燈後，Slave 2–8 RGB1 以實測固定色 `CRGB(180,65,0)`、local 亮度 15–210（actual 約 5–74）的 branching V3Cross 由 Slave 3 胸口掃入，胸口完成後分流至背包、手臂及腰部，腰部完成立即接左右腿，之後以 `smoothSineBreath` 同款 16-bit 曲線持續同色呼吸，黑色 comet size 固定為 `40`，不再取樣 palette；其他 RGB／PCA／PWM 維持原戰鬥演出，150 秒後淡出並恢復一般 global 60/255。 |
| `storyMode_idle` | 閒置模式 | **LED mode 11，已啟用** | 60 秒 | RGB 與其他 PCA LED 維持關閉；Slave 3 頭眼／額頭 CH0、CH6 持續保持 second-stage `0.85π` settle brightness。 |

正式 Story Mode 每幀輸出前，Slave 1／9 FastLED RGB 最終 cap 為 `10/255`；Slave 10 固定最高 `42/255`，不跟隨 Story Mode requested global brightness 比例變化。PCA/PWM 不受此 RGB policy 影響。
| `storyMode_motor` | 可動模式 | **Servo mode 0，目前啟用** | 240 秒 | Slave 8／10 腿部先淡入 20%、綠色訊號及白色 cross ×2，再依 motor index `0 → 1/2 → 3`、每組相隔 5 秒開甲；其他 Slave 保留既有 sequence。 |
| `storyMode_motor_reset` | 復位模式 | **Servo mode 1，目前啟用** | 36 秒 | 依 top → mid → skirt → legs，每段 9 秒回收伺服馬達；完成後清理輸出並返回 LED mode 流程。 |

## Slave 1 地台／武器／盾

- RGB1：盾／大炮流光，共 56 粒；高能模式使用 white swipe／palette flow。
- RGB2：盾散氣口，共 20 粒；Normal 模式使用 `VentEffect`。
- RGB3：大炮尾與盾細漩渦，共 9 粒；Normal 模式使用 `turbine_v3`。
- RGB4：大炮訊號燈，共 34 粒，實體分段為 `6+1+26+1`；Signals 使用 Repair profile，其餘 Normal 模式使用 `SpecificColorPattern` Normal profile，兩套均不使用 MachineGun patterns。
- Slave 1 只有 RGB1–RGB4，不操作 RGB7 以上。PCA 為 `0x56–0x60` 五片；只有 `0x58 CH3` 是火神炮紅燈並可使用 `chValcanGun`。

## Slave 10 Foulyoupou platform（新增）

- Routing：`SLAVE_ID=10`、I2C `0x19`；master 的 `ACTUAL_SLAVE_NUM=20`。
- RGB：RGB1–4、RGB7–8 各 62 粒，RGB9 25 粒，RGB10/11/12 為 4/50/4 粒。
- PCA：7 塊 LED PCA9685；目前新增 story mode 效果使用 PWM0–5 的 CH0–9。
- `storyMode_signals`：RGB1–4、7–9 關閉，PWM0–5 CH0–9 低亮長亮。
- `storyMode_0_v1` / `storyMode_0_v2`：RGB1–4、7–9 播放白色 swipe、fixed-count／random flash 與分段全亮流程。
- `storyMode_awakening_3`：RGB1–4、7–9 保持關閉。
- `storyMode_activation`：RGB1 播放專用 branching multi-comet cross effect；RGB2–4、7–8 保留各 Slave 效果，RGB9 播放 `randomFillAll_V2`，PWM0–5 CH0–9 長亮。
- `storyMode_plasma` Stage 4：RGB1–4、RGB7–8 組成斜線 matrix，固定由上至下 `RGB8→RGB7→RGB4→RGB3→RGB2→RGB1`，再接 `Slave 2→Slave 3`；抽中背包時必須再接至少一條手／腳路徑，不可反向跑成 `3→2→10`。五條身體路徑每雷仍只會出現 1、2 或全部 5 路。RGB9 與 PCA 保留原有效果。
- `storyMode_2`：RGB1/3/4/7 反向 meteor，RGB2/8 中央向外 meteor，RGB9 為 `randomFillAll_V2`，PWM0–5 CH0–9 長亮。
- `storyMode_storing_energy`：不加入 Slave 2–8 cross topology；RGB1–4、7–9 使用獨立反向 `whiteSwipe`，full-power 段加入 PWM0–5 CH0–9 長亮。
- `storyMode_3`：RGB1–4、7–8 關閉，RGB9 播放 `randomFillAll_V2`，PWM0–5 CH0–9 長亮。

## Slave 9 platform RGB

- RGB1／RGB2：455／325 粒，分別使用 65×7／65×5 matrix mapping。
- RGB3／RGB4／RGB7：236／119／213 粒 platform strip。
- Signals：RGB1／RGB2 白色方形聚光；RGB3／RGB4／RGB7 關閉。
- Awakening／Activation／Mode 2／Mode 3：依模式使用 random fill、palette stream、Water Ripples、Comet、Chase 與 GN Wire。
- Storing Energy：RGB1／RGB2 使用 matrix palette pattern；RGB3／RGB4／RGB7 使用 Chunchun。
- Plasma：Stage 2／3 的 RGB1／RGB2 保留分段亮起與白爆；Stage 4 的 RGB1／RGB3 為獨立自然雷電，RGB2 依實機要求註解停用，RGB4 為 White Swipe，RGB7 為 Fireworks 1D。
- Trans-Am：RGB1／RGB2 使用 Fifth Counterpoint，RGB3／RGB4 關閉，RGB7 使用 dim cyber Glitter。

## storyMode_storing_energy — 六階段儲能

Stage 1 的 RGB1 被視為由 S1 頭經 S2 身體分流的三條 Hi-Nu 虛擬燈帶：`1 → 2 → {3,5} → {4,6}`、`1 → 2 → 7 → {8,10} → {9,11} → {19,20}` 與 `1 → 2 → 12 → {13-18}`。三條分支使用相同 comet cadence，但各自按實際長度填充；每 3 顆 comet 鎖定 1 個 5-LED block，第 1／2 顆先顯示該 block 的 1/3、2/3 進度。S14–18 Funnel Gun 以各自專屬 RGB pin（RGB2／3／4／7／8）渲染同一條 Branch 3。

| Timeslot | State | Description |
| --- | --- | --- |
| `0:00–0:20` | `MODE_STORING_ENERGY_STORING` | 20-LED palette wave 由 S1 頭經 S2 身體流向三條分支。各分支末端（S4/6、S19/20、S13-18）由 virtual strip 尾端先填，填滿後才輪到上游（S3/5、S8/10 再 S7、S12）；S2 身體等最慢的腿部分支完成後回填。所有 downstream 完成後，S1 頭在最後 15% 時間填滿。 |
| `0:20–0:22` | `MODE_STORING_ENERGY_DIM_5` | 已填滿的 RGB1 在 2 秒內淡至 5%；不修改 FastLED global brightness。 |
| `0:22–0:32` | `MODE_STORING_ENERGY_POWER_UP` | global brightness 設為 `90/255`。Stage 開始即加入 base RGB 與 RGB／PCA 訊號；1 秒白色 PCA、2 秒散熱／內構、3 秒長亮、4 秒呼吸、5 秒閃燈／火神炮，之後保持至 Stage 3 共 10 秒完成。 |
| `0:32–0:33` | `MODE_STORING_ENERGY_DROP_50` | RGB effects 在 1 秒內降至 50%，PCA 設為 50%；global brightness 維持 `90/255`。 |
| `0:33–0:36` | `MODE_STORING_ENERGY_FULL_POWER` | global brightness 突然升至 `140/255`；RGB 由 50% 過渡到 80%，PCA 以 80% 常亮，其他既有 RGB effects 繼續運作。 |
| `0:36` | `MODE_STORING_ENERGY_END` | RGB 與 PCA 立即全關並完成 story mode。 |

只有 Stage 3 與 Stage 5 修改 FastLED global brightness；Stage 2／4 只改 effect output。

## storyMode_plasma — 五階段電漿

Hi-Nu cross topology 的 RGB 實體總數是 1342 LEDs（S1–S12 RGB1、S19／S20 腳掌 RGB1 各 70 粒，加六支 Funnel Gun 各 62 粒）。Stage 4 有五個抽選 bit：背包入口與左手、右手、左腳、右腳。背包入口固定為六支 Funnel Gun `S18→S17→S16→S15→S14→S13`（terminalBit 0–5，各 62 粒、virtual start `0–5` 斜線錯格）→ S12 背包 `67–96` → S2 身體 `97–146` → S1 頭 `147–196`；抽中時一定再接另一個隨機部位。未抽中背包時，則由 S2 身體 hub 直接接 `2→3→4`、`2→5→6`、`2→7→8→9→19` 或 `2→7→10→11→20`。

| Timeslot | State | Description |
| --- | --- | --- |
| `0:00–0:03` | `PLASMA_S1_EYE` | 其他 RGB 保持黑；Slave 3 的獨立眼燈呼叫及頭／胸 PCA 前導持續更新。global brightness 為 `160/255`。 |
| `0:03–0:08` | `PLASMA_S2_SEQON` | RGB1 依 Hi-Nu ring `{19,20} → {9,11} → {4,6,8,10,13-18} → {3,5,7,12} → {2} → {1}` 分組亮起；每組以 5% 綠色 `CRGB(1,13,3)` 淡入 0.5 秒，step 間隔 1.125 秒；S14–18 以專屬 RGB pin 執行同一 sequence。 |
| `0:08–0:11.05` | `PLASMA_S3_FLASH` | global brightness 提升至 `200/255`；全部 RGB1 在 50ms 內爆成白光並保持至 Stage 3 flash 完成。 |
| `0:11.05–0:11.70` | `PLASMA_S3_FADEOUT` | 維持 `255/255`；依同一分組，用 130ms step 從燈帶尾端向上擦除，共 650ms。 |
| `0:11.70–1:27` | `PLASMA_S4A`／`PLASMA_S4_TRANSITION`／`PLASMA_S4B` | global brightness 回到 `160/255`。S4A 第一雷強制五路大雷，之後三次小雷；1.2 秒後用 300ms fade-out 降至非零 `48/255`，S4B 立即以五路大雷接上。S4B 的 73.8 秒平均分成五個 14.76 秒段落，以 master start time 同步洗牌且不重複播放 Random Thunder、Domino Accelerate、Cross Pair、Heartbeat、Storm Crescendo；每套必定覆蓋背包、左右手及左右腳。全部身體路徑固定正向，背包固定 top-down 並至少連接一條手／腳路徑。S1 頭與 S9／S11 腿下段已併入五路 cross topology；signals 只在 Stage 4 執行。 |
| `1:27–1:30` | `PLASMA_S5_FADEOUT` | 依 Hi-Nu ring `{1} → {2} → {3,5,7,12} → {4,6,8,10,13-18} → {9,11} → {19,20}`，每組 750ms 分段收光；1:30 全關並恢復一般 global brightness。 |

## 非正式 Controller 入口

| 函式／檔案 | 狀態 | Description |
| --- | --- | --- |
| `storyMode_all_off` | 不再註冊；保留為清場工具 | 清空 RGB、PCA LED 與輸出狀態，不佔用正式 LED mode ID。 |
| `storyMode_demo` | 未註冊；`runPattern()` demo block 已註解 | Global brightness 實機測試已完成並清除；正常 standalone loop 已恢復，結果保留於下方紀錄。 |
| `storyMode_dev` | 由 `runStoryModeDev()` 直接呼叫，未註冊 | 開發測試入口；全部已配置 `espLed[]` 與 `pcaLed[]` 以 `1000/4095` 低亮長著，並播放 RGB／測試可動效果。內容可隨當前測試目標改變，不視為正式演出。 |
| `storyMode_vu` | 未註冊 | Audio／VU 測試模式，不納入正式 story mode description、slave grouping 或 PCA 眼燈檢查。 |
| `storyMode_struct`／`storyMode_timing` | 工具，不是 mode | 提供 effect state／同步時間輔助，不可列為可播放 story mode。 |
| `storyMode_sleeping` | 無目前實作 | 舊文件名稱；目前沒有對應 source，也沒有加入 Controller。 |

## storyMode_motor — Slave 8／10 腿部開甲

Slave 8 詳細硬體、燈效及 `24 → 25/26 → 27` 時序見 `docs/storymode/slave8_storymode_motor.md`。Slave 10 與 Slave 8 使用固定配對 `case 8: case 10:`，但燈數及 UART address 仍由各自 PlatformIO environment 提供。

## storyMode_motor — 其他 Slave 0／3／6 秒燈光前導

`storyMode_motor` 在 0 秒先點亮既有 body white PCA，3 秒加入 RGB4 訊號，6 秒加入 Slave 1 地台／槍／盾 PCA，9 秒進入 motor sequence。Slave 3 CH0、CH6 眼燈不依附前導段，而是在整個函式中獨立更新。

| Slave | Body White PCA 內容 |
|------|----------------------|
| slave1 | 6 秒起：PWM0 CH0-7、PWM1 CH0-15、PWM2 CH0-2/4、PWM3 CH0-7、PWM4 CH0-15；PWM2 CH3 火神炮在前導段保持關閉 |
| slave3 | PWM1 CH0-8 白燈；PCA0 CH0/CH6 眼燈獨立更新 |
| slave4 / slave5 | PWM0 CH12-15 白燈 |
| slave7 / slave8 | PWM0 CH0/1/4/5/7/8 白色 marker |

## Servo StoryMode Set

透過 Timer UART 的 SET 指令 b1 的 bit 6 切換 set（絕對狀態）：bit6=1 → SERVO set、bit6=0 → LED set。Master 從 LED 切入 SERVO 時會記錄來源 LED mode，SERVO 組完整跑完後回到來源 LED mode 的下一個 mode；若正在跑 SERVO 最後一個復位 mode，Timer button frame 會被忽略，避免中斷伺服馬達關閉流程。詳見 `docs/communication/external_uart/協議規格_timerUART.md`。

| 編號 | 函式 | 名稱 | 預設秒數 |
|------|------|------|----------|
| 0 | `storyMode_motor` | 可動模式 | 240s |
| 1 | `storyMode_motor_reset` | 復位模式 | 36s |

## War Robot 橙黃呼吸實機紀錄

測試日期：2026-07-19。測試使用 standalone RGB1（256 粒）、`warRobotGradYellowPalette` index `90`、原版 `smoothSineBreath`、最高亮度 140、FastLED 全域亮度 128、`RGB_FREQUENCY=60`。

- 失敗：最低亮度 `1–7`，低光時偏紅，無法維持橙黃色。
- 通過：最低亮度 `8`，可維持橙黃色與呼吸效果。
- 結論：此硬體與參數組合的 `brightnessMin` 正式門檻為 `8`。

測試完成後已清除 RGB 呼吸測試程式、移除專用測試檔、註解 `runStoryModeDemo()` 測試入口，並恢復 `runStandaloneLoop()`。`storyMode_demo.cpp` 保留測試前的 PCA Inverse Disney demo 內容；Test A temporal dithering 維持禁用。

第二輪實機結果：保持相同 palette、最低亮度 8、最高亮度 140 與 60 FPS 時，FastLED 全域亮度 `128／90／60／50／40／30` 全部通過，所有級別均未變紅。最終選用 `128/255` 作為 Story Mode 3 global brightness；暫時測試已再次清理。

第三輪待測設定：`RGBBreathSwipePaletteV3Cross` 使用實測固定色 `CRGB(180,65,0)`、local `15–210`、global `90/255`、60 FPS 與 `smoothSineBreath` 同款 16-bit 正弦曲線；原 swipe-in、comet 及跨 Slave branching routing 保留，但 V3Cross 不再取樣 palette。預計 actual brightness 約為 `5–74`；其他 local 255 RGB 的最高輸出限制在約 90。結果待實機確認。

### 歷史 WLED FX playlist 設計

`storyMode_demo` 在 RGB1 上輪播全部已移植的 WLED 燈效，作硬體比對測試用：

- playlist 包含 WLED effects 與 `zoidsTail`，共 40 個。
- 每個 effect 固定執行 `sm_demo::fxSlotMs = 15000ms`，循環 `sm_demo::fxCount = 40` 個。
- demo 啟動時從 index 28 `Phased Noise (FX106)` / `mode_wled_phased_noise` 開始，之後照 playlist 循環。
- `storyMode_demo` 只負責 RGB1 playlist，不包含 motor demo 或 debug logging。
- 目前順序：Bouncing Balls (FX91) → Chase → Chase Flash Random → Chase Rainbow → Chunchun → Colortwinkles (FX74) → Dissolve → Fireworks (FX42) → Fireworks Starburst → Flow → Freqpixels → Gravcentric (FX157) → Meteor → Midnoise (FX135) → Noise 1 → Noise 2 → Pride 2015 → Lighthouse (FX41) → Oscillate (FX62) → Fireworks 1D → Blends → Blurz → BPM → Candle Multi → Flow Stripe (FX179) → Chase Enhanced → Comet → Phased (FX105) → Phased Noise (FX106) → Rain (FX43) → Dancing Shadows (FX173) → DJ Light (FX174) → Glitter (FX87) → Matripix (FX134) → Noise 3 (FX72) → Noisemeter (FX136) → Tetrix (FX116) → Freqmatrix (FX137) → Freqwave (FX138)。

参數放置（依 coding style）：

- **效果參數模板**：`wled*Instances`（`createDefault*` + `InstanceArray`）放 `storyMode_struct`，demo 直接取 `[0]`。
- **playlist 控制 static**（slot 計時、index）：放 `storyMode_parameter` 的 `namespace sm_demo`，包含 `fxSlotMs`、`fxIndex`、`fxPrevIndex` 與 `fxSlotStart`。
- effect 函式本體放 `firmware/shared/src/patterns/patterns_wled/1D_strip.cpp`；demo 只決定何時在 RGB1 呼叫哪個效果。

### WLED 效果移植慣例

- 效果由 WLED `wled00/FX.cpp` 逐函式忠實移植：`SEGMENT`/`SEGENV` 狀態改存進對應 `WLED_*Params` struct；`SEGLEN`→`NUM_LEDS`、`strip.now`→`millis()`、`SEGCOLOR(1)`（背景）→黑、`color_from_palette`→`getPaletteById(paletteId)` + `ColorFromPalette`。
- **`fade_out(rate)` 不等於 `fadeToBlackBy(rate)`**：WLED `fade_out` 淡得很輕（`r=(255-rate)>>1; 每幀淡 1/(r+1)`）。用 `wledFadeOut()` 還原其幅度，不要直接 `fadeToBlackBy(rate)`。
- **Audio-reactive 效果**（Gravcentric、Midnoise、DJ Light、Matripix）：WLED 沒接 mic 時用 `simulateSound()` 產生假音訊驅動。本專案以 `wledSimulateSound(simId, &audio)` 移植該函式，`volumeSmth` 為 **0–255**（不是 0–1）、`fftResult[16]`、`volumeRaw`。soundSim：BeatSin(0) 用於多數，WeWillRockYou(1) 用於 Matripix。
- 無 mic 時這些效果會跟著 `simulateSound` 的 perlin/beatsin 律動，與你 flash 的非 audio-reactive WLED app 行為一致。
- FFT 類效果（Freqmatrix、Freqwave）讀 `FFT_MajorPeak`，由 `wledSimulateSound` 以 `21 + volumeSmth²/8` 還原。

### 注意：lighthouse 命名

WLED 的「Lighthouse」其實是 `mode_comet` 的顯示名（`_data_FX_MODE_COMET = "Lighthouse..."`）。現在 `mode_wled_lighthouse` 是純 WLED `mode_comet` 移植：單端 comet + WLED `fade_out` 拖尾。舊有的 `whiteSwipeComet` 是自訂 3-trial comet，**不是**這個 WLED Lighthouse。

### Standalone demo 硬體測試入口

- 保留 `standaloneController.cpp::runStandaloneLoop()` 內的 `updateRunModeTimer()`、timeout 與模式輪播程式，不要刪除或改寫。
- 只在 `ledController.cpp::runPattern()` 最前面的既有 `STANDALONE_MODE` demo test block 取消註解 `runStoryModeDemo();` 與 `return;`；測完重新註解兩行。
- 目前測試效果直接寫在 `storyMode_demo()` 的 `STANDALONE_MODE` 分支，只操作 RGB1。
- 實機測試完成後，重新註解 demo test block，恢復 `runStandaloneLoop()`。
