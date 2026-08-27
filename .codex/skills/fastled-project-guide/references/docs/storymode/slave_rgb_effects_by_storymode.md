# Story mode 的 Slave RGB 範圍

本文件記錄目前正式 story mode 的硬體邊界。核心概念很簡單：每個 Slave 只操作自己實際接上的 RGB，不能因為共用 buffer 存在就呼叫不存在的燈帶。

## 正式範圍

- 正式 story mode 使用 Slave 1–10。
- Slave 10 是新增 Foulyoupou platform；`firmware/shared/src/storymode/` 不保留 Slave 11–14 的 case、`slaveId` 條件或專屬 helper。
- 這個限制只套用 story mode；PlatformIO environment 與本機硬體設定另行管理。

## Slave 2、6、9、10 必須分開

| Slave | 本專案身份 | 程式結構 |
| --- | --- | --- |
| Slave 2 | backpack | 獨立 `case 2:` |
| Slave 6 | waist | 獨立 `case 6:` |
| Slave 9 | platform | 獨立 `case 9:` |
| Slave 10 | Foulyoupou platform（新增） | 獨立 `case 10:` |

舊專案的 Slave 2／6／9／10 weapon group 不可沿用。四者不可共用同一組 case label 或混合 effect 分支；case 排序固定為 `1 → 2 → 3 → 4/5 → 6 → 7/8 → 9 → 10`。

Slave 10 使用 RGB1–4、7–12 及 7 塊 LED PCA9685。`plasma` Stage 4 的 RGB1–4、7–8 固定組成斜線 matrix，背包路徑只可由 `10→2→3` 向下運行，到 Slave 3 後再接一條隨機手／腳路徑；`activation` 與 `trans_am` 仍使用各自既有效果，`storyMode_2` 使用 meteor，`storing_energy` 使用獨立 backward white swipe。

### Slave 9 RGB mapping

| Strip | LED 數 | 結構 | 主要效果 |
| --- | ---: | --- | --- |
| RGB1 | 455 | 65×7 platform matrix | Square Spotlight、Water Ripples、Palette Gradient Stream、Fifth Counterpoint、Plasma Lightning |
| RGB2 | 325 | 65×5 platform matrix | 與 RGB1 對應的矩陣效果 |
| RGB3 | 236 | platform strip | Comet、Chunchun、Chase、GN Wire、White Swipe |
| RGB4 | 119 | platform strip | Comet、Chunchun、Chase、GN Wire、White Swipe |
| RGB7 | 213 | platform strip | GN Wire、Chunchun、Glitter、Fireworks 1D |

- `storyMode_signals` 的 RGB1／RGB2 使用白色方形聚光，RGB3／RGB4／RGB7 關閉。
- `storyMode_0_v1`／`storyMode_0_v2` 使用 Slave 9 獨立的白色 flash／分段亮滅流程。
- `storyMode_plasma` 將 Slave 9 RGB1／RGB2 加入前段分段亮起、白爆與收光；Stage 4 只有 RGB1／RGB3 使用獨立自然 Plasma Lightning，RGB2 依實機要求註解停用。
- Slave 9 保持獨立 `case 9:`，不可與 Slave 2、6 或 10 共用 effect state。

## Slave 1 與 Slave 3

| Slave | 可用 RGB | 程式結構 |
| --- | --- | --- |
| Slave 1 | RGB1–RGB4 | 使用獨立 `case 1:`；不可與 backpack、weapon 或 leg group 共用會操作 RGB7 以上的 block。 |
| Slave 3 | RGB1–RGB4 | 使用獨立 `case 3:`；舊 RGB7–RGB16 與 RGB10 眼睛效果已移除。 |

全域初始化／結束階段可能會清除共用 RGB buffers；那是共用 staging 清理，不代表 Slave 1 或 Slave 3 有對應實體燈帶。判斷專屬硬體時，以 `case 1`、`case 3` 與 `if (slaveId == 1/3)` 內的呼叫為準。

### Slave 1 RGB mapping

| Strip | LED 數 | 硬體 | Normal routing | Repair routing |
| --- | ---: | --- | --- | --- |
| RGB1 | 56 | 盾／大炮流光 | `whiteSwipe*`／palette flow | 關閉 |
| RGB2 | 20 | 盾散氣口 | `VentEffect` | 關閉 |
| RGB3 | 9 | 大炮尾／盾細漩渦 | `turbine_v3` | 關閉 |
| RGB4 | 34 | 大炮訊號燈 | `slave1_rgb4_specificColorIndex` | `slave1_repair_rgb4_specificColorIndex` |

- RGB4 實體順序是 `LED 0–5` 六粒短段、`LED 6` 獨立一粒、`LED 7–32` 二十六粒主段、`LED 33` 獨立一粒。
- Normal 以呼吸、長亮、Navigation、橙色雙閃與紅色警示組合；Repair 以穩定長亮、呼吸及少量診斷 marker 組合。兩套都不使用 registry 6／7 的 MachineGun patterns。
- `storyMode_0_v1`／`storyMode_0_v2` 依模式設計使用 random flash，不套 Normal／Repair profile。
- Activation、Storing Energy、Mode 2、Plasma Stage 4、Trans-Am、Mode 3 與 Motor base 的 RGB4 使用 Normal profile。
- Signals 的 RGB4 使用 Repair profile；Develop 改用獨立全訊號 profile，RGB1–RGB3 保持關閉。
- Slave 1 不存在 RGB7，任何 `case 1` 專屬 block 都不可操作 `leds_RGB7` 以上。

## Slave 1／9 各 StoryMode RGB 效果對照

以下以正式 Controller 全部 LED modes 啟用時的順序為準，只列 Slave 1／9 實際接線的 RGB。`OFF` 表示程式明確關閉，或該模式沒有對這組實體 RGB 提供直接效果；不代表同一 Slave 的 PCA／motor 也一定關閉。

正式 Slave build 另有最終亮度限制：Slave 1 與 Slave 9 的 FastLED RGB 上限都是 `15/255`，所以即使下表有執行效果，肉眼仍可能很像熄滅。這個限制不影響 PCA/PWM，`STANDALONE_MODE` 也不使用此 `15/255` override。

| Mode | Slave 1 RGB1／2／3／4 | Slave 9 RGB1／2／3／4／7 | 實際 OFF 重點 |
| --- | --- | --- | --- |
| `storyMode_develop` | `OFF`／`OFF`／`OFF`／`SpecificColorPattern` Develop profile | 全部 `OFF` | Slave 9 全關；Slave 1 只開 RGB4。 |
| `storyMode_signals` | `OFF`／`OFF`／`OFF`／`SpecificColorPattern` Repair profile | RGB1／2：`runSquareSpotLight`；RGB3／4／7：`OFF` | 兩個 Slave 都只開指定訊號燈。 |
| `storyMode_0_v1` | RGB1–4：`randomFlashWithGap_multiple` → `randomLightUp` → `rgbOn` | RGB1／2／3／4／7：同類白色 random flash、密度增加及全亮流程 | 只有模式內的分段熄燈與收尾，不是整個 mode 長期關閉。 |
| `storyMode_awakening_3` | RGB1：`rgbBreath_swipe_palette_v3`；RGB2：`VentEffect`；RGB3：`turbine_v3`；RGB4：`SpecificColorPattern` | RGB1／2：`randomFillAll_V2` → `rgbBreath_swipe_palette`；RGB3／4／7：`OFF` | Slave 9 只有兩塊 matrix 開啟。 |
| `storyMode_activation` | RGB1：`whiteSwipeWithBackgroundV3`；RGB2：`randomFillAll_V2` → `VentEffect`；RGB3：`turbine_v3`；RGB4：`SpecificColorPattern` | RGB1／2：`runPaletteGradientStream`；RGB3／4：`mode_wled_chase`；RGB7：`GN_Wire_Normal` | 主要實體 RGB 都有直接效果。 |
| `storyMode_0_v2` | RGB1–4：`randomFlashWithGap_multiple` → `randomLightUp` → `rgbOn` | RGB1／2／3／4／7：同類白色 random flash、密度增加及全亮流程 | 只有模式內的分段熄燈與收尾。 |
| `storyMode_storing_energy` | Stage 1 先 `OFF`；之後 RGB1：`paletteWave_80Percent_SpecialWave`、RGB2：`VentEffect`、RGB3：`turbine_v3`、RGB4：`SpecificColorPattern` | RGB1／2：matrix `runPattern`；RGB3／4／7：`mode_wled_chunchun` | Slave 1 在最初儲能段關閉，後段才亮。 |
| `storyMode_2` | RGB1：`whiteSwipe`；RGB2：`VentEffect`；RGB3：`turbine_v3`；RGB4：`SpecificColorPattern` | RGB1／2：`runWaterRipples`；RGB3／4：`mode_wled_comet`；RGB7：`GN_Wire_Normal` | 主要實體 RGB 都有直接效果。 |
| `storyMode_plasma` | Stage 4 RGB1／2／3：各自 `RGBIndependentLightning`（每條獨立亂數方向）；RGB4：`SpecificColorPattern` | RGB1／2：前段分段亮起／白爆；Stage 4 RGB1／3：各自 `RGBIndependentLightning`，RGB2 停用；RGB4：`whiteSwipe`；RGB7：`mode_wled_fireworks_1d` | Slave 1 三條與 Slave 9 兩條啟用雷電互不共用 timing；Slave 10 RGB8→7→4→3→2→1 合成斜線 matrix，背包 cross 固定向下 `10→2→3`，其餘未連接路徑才可隨機方向。 |
| `storyMode_trans_am` | RGB1：`whiteSwipeWithBackgroundV3`；RGB2：`VentEffect`；RGB3：`turbine_v3`；RGB4：`SpecificColorPattern` | RGB1／2：`runFifthCounterpoint`；RGB3／4：`OFF`；RGB7：`mode_wled_glitter` | Slave 9 只關閉 RGB3／4。 |
| `storyMode_3` | RGB1：`whiteSwipeWithBackgroundV3`；RGB2：`VentEffect`；RGB3：`turbine_v3`；RGB4：`SpecificColorPattern` | RGB1／2：`runPaletteGradientStream`；RGB3／4：`GN_Wire_Normal`；RGB7：`OFF` | 除 Slave 9 RGB7 外，主要實體 RGB 都有直接效果。 |
| `storyMode_idle` | 全部 `OFF` | 全部 `OFF` | 這是設計上的全關模式；只有 Slave 3 眼燈保持。 |
| `storyMode_motor` | RGB1：`whiteSwipeWithBackgroundV3`；RGB2：`VentEffect`；RGB3：`turbine_v3`；RGB4：`SpecificColorPattern` | RGB1：`GN_Drive_Running`；RGB2：`VentEffect`；RGB3：`turbine_v3`；RGB4：`footplatev2`；RGB7：`GN_Drive_Running` | 9 秒前導後才進入主要 RGB base。 |
| `storyMode_motor_reset` | 實體 RGB1–4 無直接效果 | 實體 RGB1／2／3／4／7 無直接效果；目前 code 只對 RGB8／10／12 signal 與 servo 執行 reset 流程 | 兩個平台的主要 RGB 沒有專屬 reset 效果。 |

詳細 PCA、motor、servo、stage 與完整 source call 可查 `.codex/skills/project-automation-rules/references/component_storymode_matrix.md`；本表只回答 Slave 1／9 是否真的沒有 RGB 效果。

## storyMode_develop — 0083 試作機展示

Develop 將高亮輸出集中在有功能的部件，左右手與左右腳使用鏡像配置；Slave 1–8 的 RGB／PCA 估算輸出約 19.53%（規格範圍 18%–22%）。所有已接線 RGB4 訊號燈全部啟用，profile 內包含 `NavigationLight2` 與 `BlinkRedSingleLedPattern`。

| Slave | Develop RGB routing |
| --- | --- |
| 1 | RGB4 全訊號 profile；RGB1–RGB3 關閉。 |
| 2 | RGB4 全訊號 profile；RGB1–RGB3 關閉。 |
| 3 | RGB2 使用 5 秒冰藍 `smoothSineBreath`；RGB4 全訊號 profile；RGB1／RGB3 關閉。 |
| 4／5 | 左右手 RGB4 使用對應全訊號 profile；RGB1–RGB3 關閉。 |
| 6 | RGB4／RGB7／RGB8 全訊號 profiles；RGB1–RGB3／RGB9 關閉。 |
| 7／8 | 左右腳 RGB4 使用同一全訊號 profile；RGB1–RGB3／RGB7／RGB8 關閉。 |
| 9／10 | Mapping 未確認，RGB／PCA 全部關閉。 |

## Slave 3 PCA 眼燈

每個在 `storyModeController.cpp` 註冊啟用的 `bool storyMode_XX(uint8_t slaveId)`，都在函式層級執行同一組獨立眼燈：

```cpp
if (slaveId == 3) {
    // Slave 3 PWM0 CH0 (0x51) head eyes green, 2 beads - independent two-stage eye wake.
    chGundamEyeWakeTwoStage(pcaLed[PWM0 * 16 + PWM_CHANNEL_0], 3000, 1500, 100, 1200, 2400);
    // Slave 3 PWM0 CH6 (0x51) head forehead green monitor - independent two-stage eye wake.
    chGundamEyeWakeTwoStage(pcaLed[PWM0 * 16 + PWM_CHANNEL_6], 3000, 1500, 100, 1200, 2400);
}
```

這個 block 必須放在 `switch (slaveId)` 外；各 case 不可再重複呼叫 `chGundamEyeWakeTwoStage()`。RGB10 的舊眼睛效果不再使用，因為 Slave 3 只有 RGB1–RGB4。

## Controller 保留順序

`storyModes` LED list 目前依下列順序全部註冊；Develop 固定為 mode 0：

1. `storyMode_develop`
2. `storyMode_signals`
3. `storyMode_0_v1`
4. `storyMode_awakening_3`
5. `storyMode_activation`
6. `storyMode_0_v2`
7. `storyMode_storing_energy`
8. `storyMode_2`
9. `storyMode_plasma`
10. `storyMode_trans_am`
11. `storyMode_3`
12. `storyMode_idle`

`servoStoryModes` 兩項目前都啟用：

1. `storyMode_motor`
2. `storyMode_motor_reset`

`storyMode_all_off()`、`storyMode_vu()`、`storyMode_demo()`、`storyMode_dev()` 沒有加入 `storyModes`／`servoStoryModes`；`storyMode_develop()` 是正式 LED mode 0。完整 description 與 Storing Energy／Plasma timeslot 見 `docs/storymode/storymode目錄.md`。

## 修改後檢查

- Slave 1／3 的專屬 block 不得出現 `leds_RGB7` 以上或對應的 `NUM_LEDS_RGB7` 以上。
- Slave 2、6、9、10 必須分別是 backpack、waist、platform、Foulyoupou platform 的獨立分支。
- 正式 story mode 不得出現 Slave 11–14 的 case 或 `slaveId` 條件。
- 每個由 `storyModeController` 啟用的 `storyMode_XX(uint8_t slaveId)` 必須正好有兩次 `chGundamEyeWakeTwoStage()`：CH0 與 CH6；未註冊的 `storyMode_vu()` 排除。
- Shared story mode 變更至少依 `AGENTS.md` 建置受影響環境；本輪另完整建置 Slave 2–8。
