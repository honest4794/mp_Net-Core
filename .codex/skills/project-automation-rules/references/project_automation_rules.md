# Project Automation Notes

這份 Markdown 是未來每個新 project 都先給 Codex / AI / Agent 看的固定 notes。

重點：這不是「做 project 時才建立 notes」。這份文件本身就要包含固定的 storyMode notes、常用時序、哪種燈先開、通常用哪幾款 function、Excel 怎樣轉 code、以及 coding workflow。

核心概念：

```text
Excel / 接線表 = 硬體位置來源
StoryMode Notes = 每個 mode 的固定流程參考
timeslot = 什麼時間先開什麼燈
case slaveId = 每個 slave 自己的工作區
effect function = 實際燈效動作
```

## Hi-Nu 20-Slave 現行分組（最高優先）

本文件後面的 PGU Slave 1–10 內容只保留作效果來源與歷史參考；本專案的 routing、
case order 與硬體身份一律以下列 Hi-Nu 定義為準：

| Slave | 部位／用途 | Story Mode 寫法 |
| --- | --- | --- |
| 1 | 頭 | 獨立 `case 1:` |
| 2 | 身體 | 獨立 `case 2:` |
| 3／5 | 左／右手上段 | `case 3: case 5:` 共用一份 code，不使用 `if (slaveId ...)` 分流 |
| 4／6 | 左／右手下段 | `case 4: case 6:` 共用一份 code，不使用 `if (slaveId ...)` 分流 |
| 7 | 腰甲 | 獨立 `case 7:` |
| 8／10 | 左／右腿上段 | `case 8: case 10:` 共用一份 code，不使用 `if (slaveId ...)` 分流 |
| 9／11 | 左／右腿下段 | `case 9: case 11:` 共用一份 code，不使用 `if (slaveId ...)` 分流 |
| 12 | 背包 | 獨立 `case 12:` |
| 13–17 | 5 段 Funnel Gun | 分別使用舊 PGU Slave 10 RGB1／2／3／4／7／8 |
| 19／20 | 左／右腳掌 | `case 19: case 20:` 共用一份 code，不使用 `if (slaveId ...)` 分流；只有 RGB1–RGB4 |

Slave 13–17 每個硬體 target 都必須明確保留非零的 `NUM_LEDS_RGB1`、`RGB2`、
`RGB3`、`RGB4`、`RGB7`、`RGB8`。上表的分別對應只決定目前搬移哪一條 PGU
Story Mode 效果，不代表可把其餘五條硬體 RGB 設成 0 或省略。

固定 case order：

```text
1 -> 2 -> 3/5 -> 4/6 -> 7 -> 8/10 -> 9/11
-> 12 -> 13 -> 14 -> 15 -> 16 -> 17 -> 19/20
```

三條部位 branch 各自推進；RGB 與已確認啟用的 PCA channel 都依同一部位順序執行：

```text
Branch 1: S1 -> S2 -> S3/S5 -> S4/S6
Branch 2: S1 -> S2 -> S7 -> S8/S10 -> S9/S11 -> S19/S20
Branch 3: S1 -> S2 -> S12 -> S14/S15 -> S16/S17 -> S13
```

每個功能 stage 都不可一次把全機同類 RGB／PCA 全部打開；必須由共用根部
`S1 -> S2` 開始，再讓三條 branch 各自按部位向外推進。不同 branch 不互相等待；
共用的 `S1／S2` 只執行一次。結束時，各 branch 先由末端向根部反序關閉，三條
branch 的下游部位都完成後，才關閉共用的 `S2 -> S1`。

本專案沒有 platform。只搬 PGU RGB 效果；PCA、PWM、GPIO 單色燈、motor 與 servo
在硬體確認前保持關閉。舊 PGU Slave 1／9 platform 效果與 brightness cap 不搬。

### Reference routing

- Effect function signature、參數群、完整 example call、PGU consumers：`effect_function_catalog.md`
- 元件在各正式 StoryMode 的 ON／OFF／STAGED、SpecificColorPattern profile、brightness 與完整 record ID：`component_storymode_matrix.md`
- PGU current call、非正式 mode 參考與舊專案正式 active 槍效：`project_call_archive.md`

PGU `dev_PGU_V2` 是 RGB 效果來源 authority，不是本專案 Slave grouping
authority。`dev_Red_Astray_Honest` 只提供 gun effect 先例，**不可複製其
brightness contrast**。

### Complete call filing contract

`project_call_archive.md` 是 complete call-site register，不是只放幾個 example call
的摘要。PGU 正式 12 LED + 2 servo StoryModes 必須採用
one record per source call site；不合併不同 Slave、stage、target、source line 的相同呼叫。

收錄範圍是 RGB、PCA、motor、servo、GPIO、ON/OFF、fade、reset 等硬體與效果
call；排除 `millis()`、`min()`、`fill_solid()` 等一般程式工具。Loop call
只保留原 source call 一筆，保留 loop context，不展開成每個 channel。

每個 call 都必須有 component description。只能使用 source 已確認的硬體註解；
若 source 沒有足夠資料，必須寫 `UNCONFIRMED COMPONENT`，不可用顏色猜測部件。
每筆同時保留原始完整 call、參數群、參數名與 definition path/line。

Red Astray 只保存 Controller 正式啟用 modes 的 active gun calls；排除注解、demo、
未註冊 mode 與非 gun call，並永遠不作 brightness authority。

`project_call_archive.md` 和 `component_storymode_matrix.md` 必須由同一份掃描結果
產生。修改 storyMode 硬體／效果呼叫後執行：

```bash
python3 .codex/skills/project-automation-rules/scripts/generate_project_call_filing.py
```

產生後必須執行 completeness contract tests，確認 archive 與 matrix 的 record IDs
完全一致、沒有 duplicate，且 Red Astray 只有核准的 active gun calls。

---

## 1. 使用方式

每次新 project 開始時，先讀這份文件。

Codex / claude 必須照這個順序工作：

1. 第一件事先確認 `Project slave 定義與分組`，不要先寫 effect。
2. 再讀本文件的 `StoryMode Notes Library`；需要元件狀態或完整呼叫時，依上方 routing 讀對應 reference。
3. 再讀 Excel / 接線表，確認 slave、RGB pin、PWM board、PWM channel。
4. 用本文件的 storyMode notes 判斷 stage 順序；effect function 以目前需求或已確認設計為準。
5. 把 Excel 的硬體位置放入正確 `case X:`。
6. 寫 code 時使用累積時間門檻 `if (time >= X)`。
7. 每個 RGB / PWM / motor 呼叫前都要有硬體註解。
8. 驗證時只需要隨機抽 1 個修改過的 slave，從 Excel 對到 code 完整檢查。

---

## 1.1 Project slave 定義與分組

開始任何新 project 前，agent 必須先確認本節，不可以沿用舊 project 的 slave 分組。

核心原則：slave number 不是通用身份。`slave 2` 在舊 project 可能是 weapon，但在新 project 可以是 backpack；所以第一步一定是重新定義 slave。

### PGU 來源專案分組（只作歷史效果參考）

| slave | 分組 | 定義 | 寫 code 規則 |
| --- | --- | --- | --- |
| `slave 1` | platform | 平台，獨立 group；只使用 RGB1–RGB4 | 獨立 `case 1:`，不要和武器或背包共用 helper |
| `slave 9` | platform | 平台，獨立 group | 獨立 `case 9:` |
| `slave 10` | Foulyoupou platform | 新增富麗優品平台；獨立 group | 獨立 `case 10:`；不加入 Slave 2–8 的 cross topology |
| `slave 2` | backpack | 背包 | 獨立 `case 2:`，以 backpack 接線表為準 |
| `slave 3` | chest | 胸口；只使用 RGB1–RGB4 | 獨立 `case 3:`；PCA 眼燈在函式層級獨立更新 |
| `slave 4` + `slave 5` | paired body group | 左右對稱，程式邏輯相同 | `case 4:` / `case 5:` 可以使用相同效果呼叫；兩邊 `RGB7` 都要跑 |
| `slave 6` | independent body group | 獨立 body / waist group | 獨立 `case 6:` |
| `slave 7` + `slave 8` | leg group | 左右腳 | `case 7:` / `case 8:` 是 L/R leg group；cross RGB 可用同一個 virtual group 同步 |

### storyMode case 排序標準

所有 `switch (slaveId)` 內的 case 順序使用目前 project 的 grouping，不使用舊 project grouping。

固定順序：

```text
case 1:
case 2:
case 3:
case 4:
case 5:
case 6:
case 7:
case 8:
case 9:
case 10:
default:
```

語意順序：

```text
platform slave 1
-> backpack slave 2
-> chest slave 3
-> paired body slave 4/5
-> independent slave 6
-> leg slave 7/8
-> platform slave 9
-> Foulyoupou platform slave 10
```

`case 4` / `case 5` 可以連續放在同一段，因為它們是 paired body group。

`case 7` / `case 8` 可以連續放在同一段，因為它們是 L/R leg group。

`case 2`、`case 6`、`case 9` 不可以再寫成同一組，因為目前 project 中它們不是同一類：

```cpp
// Wrong for this project.
case 2:
case 6:
case 9: {
    ...
} break;
```

應改成各自獨立：

```cpp
case 2: {
    // Backpack.
} break;

case 6: {
    // Independent body / waist group.
} break;

case 9: {
    // Platform.
} break;
```

### Regrouping SOP

當從舊 project 或其他 branch 取回 storyMode code 時，照以下順序整理：

1. 先確認目前 project 實際存在的 slave 範圍。本 project 使用 `slave 1-20`。
2. 刪除 storyMode 內不屬於本 project 的 slave 分支，例如 `case 11` 到 `case 14`。
3. 找出舊分組，例如 `case 2 / case 6 / case 9` weapons group、`case 1 / case 12 / case 13 / case 14` platform group、`case 11` backpack。
4. 依目前 project 分組重拆 case，不要沿用舊 weapons/platform/backpack 身份。
5. 排序每個 `switch (slaveId)`：`1 -> 2 -> 3 -> 4/5 -> 6 -> 7/8 -> 9 -> 10`。
6. 每個保留下來的 case 都要能從註解看出目前 project 的硬體身份，例如 backpack、chest、platform、leg。
7. 無法由目前接線表確認的舊 PCA block 先移除，不要複製到另一個獨立 slave。

### 舊 project 分組，只能當歷史參考

舊 storyMode 分組如下，不能直接套到目前新 project：

| 舊分組 | slaves |
| --- | --- |
| weapons | `slave 2`, `slave 6`, `slave 9`, `slave 10` |
| platform | `slave 1`, `slave 12`, `slave 13`, `slave 14` |
| backpack | `slave 11` |

若新 project 的 Excel / 接線表和本節不同，必須先更新本節，再開始寫 storyMode。不要讓 agent 在 code 中猜 slave 用途。

---

## 2. StoryMode Notes Library

正式清單、Controller 狀態、設定時長與完整演出 description，以 `docs/storymode/storymode目錄.md` 為唯一來源。本章只保存 migration／coding notes；只涵蓋 `storyModeController.cpp` LED／servo arrays 內的 modes，未註冊的 VU、demo/dev 入口與工具函式不列入。

目前正式 LED order 是 `storyMode_develop`、`storyMode_signals`、`storyMode_0_v1`、`storyMode_awakening_3`、`storyMode_activation`、`storyMode_0_v2`、`storyMode_storing_energy`、`storyMode_2`、`storyMode_plasma`、`storyMode_trans_am`、`storyMode_3`、`storyMode_idle`。正式 servo order 是 `storyMode_0_v2`、`storyMode_motor`、`storyMode_motor_reset`。`storyMode_all_off` 是清場工具，不佔 mode ID。

### 2.0 常用單燈和 RGB function 對照

這一節是所有 storyMode 共用的 function 字典，後面的 storyMode notes 只寫時序和燈種；遇到相同稱呼時，先查這裡。

#### RGB pin 習慣對應

這是本 project 的 storyMode RGB SOP。除非 Excel / 接線表明確寫不同功能，先用這個表判斷 RGB1-RGB4 要放什麼效果。

| RGB pin | 本 project 常見功能 | storyMode 常用 function | 使用時機 |
| --- | --- | --- | --- |
| `RGB1` / pin 1 | 主體 base / 流光 / 呼吸主燈帶 | `whiteSwipe`, `whiteSwipeWithBackgroundV3`, `rgbBreath_swipe_palette_v2`, `rgbBreath_swipe_palette_v3`, `GN_Drive_Running`, `mode_wled_meteor` | 長著、啟動、呼吸、Trans-Am、跨 slave RGB base |
| `RGB2` / pin 2 | 散氣 / vent / 內構能量 | `randomFillAll_V2`, `gradientVentPalette`, `VentEffect` | 散氣、啟動後維持、儲能、Trans-Am |
| `RGB3` / pin 3 | 漩渦 / GN drive / turbine | `turbine_v3`, `GN_Drive_Normal`, `GN_Wire_Normal`, `gradientDynamicPalette` | 胸口、背包、腰部或推進器的旋轉 / GN 能量 |
| `RGB4` / pin 4 | 訊號燈 / marker / 細節燈 | `SpecificColorPattern`, `chFlashAlternative` 類 PWM 邏輯 | signal mode、長著後段、motor 開合提示 |
| `RGB5` / pin 5 | SDA | 通常保留，不自動套一般 RGB 效果 |
| `RGB6` / pin 6 | SCL | 通常保留，不自動套一般 RGB 效果 |
| `RGB7+` | 特殊燈，例如腳底燈 | `footplatev2` 或依 Excel |

### RGB signal profile 分離 SOP

`SpecificColorPattern` 的 registry 可供多個 Slave 使用，但每組 index／override color arrays
代表一份具體硬體設計。核心做法是：共用 effect 定義，不共用不相同的硬體配置。

#### 設計原則

1. **硬體先於效果**：先從 PDF、圖片、零件描述、Excel／接線表確認 Slave、RGB pin、實際燈數及 `index 0..N-1`，再選 pattern。
2. **Slave 邊界**：每個獨立 Slave 使用自己的 profile；只有專案明確定義的 paired group 才能共用。
3. **模式邊界**：同一 Slave 的 Normal、Repair、Motor 等語意若不同，使用不同 index／override arrays。
4. **Pattern 與顏色分離**：pattern ID 決定動作與時序，override color 決定 R/G/B；不可只憑顏色反推效果。
5. **明確 routing**：每個 story mode 在對應 `case slaveId` 明確引用 profile，不靠模糊名稱猜用途。
6. **實際數量一致**：array 長度、`NUM_LEDS_RGBx` 與 `SpecificColorPattern` 的處理數量必須符合實際燈數。
7. **引用稽核**：修改前後都搜尋所有 consumers，避免連帶改變未要求的 story mode、motor 或其他 Slave。

#### `SpecificColorPattern` profile 設計邏輯

核心不是「每顆燈都要有動畫」，而是讓每顆燈符合部件功能。正確設計順序是：

```text
實體 LED index／部位
  -> 功能狀態（運作、警示、等待、停用）
  -> 期望動作與節奏
  -> registry pattern ID
  -> override color
  -> story mode routing
```

必須先選動作，再選顏色；不可因為燈是紅色，便直接假設它要閃爍。`off` 也是
正式、可接受的功能狀態：若該部位應停用、等待、避免誤啟動或降低供電，就應使用
index `0`，不可為了讓每顆燈都有變化而硬加效果。

##### Index 與 override color 語意

- `ledColorIndex` 使用 1-based ID：`1` 對應 `registry[0]`，依此類推。
- `0` 是關燈；超出 `1..numPatterns` 是無效輸入並輸出黑色，不可用來代表新效果。
- 非黑色 override color 只改變色相，並保留原 pattern 的亮度曲線與時序。
- `CRGB::Black` 表示不覆寫顏色、沿用 registry 原色，不是關燈；要關燈必須使用 index `0`。
- index 與 override arrays 必須使用相同實體 LED 次序，長度等於實際 render count。

目前 `storyMode_2_params::specificColor_registry` 的設計字典如下。ID／名稱是 profile
合約；sub-function 是目前實作，可以由多個 ID 共用。實際 code 是唯一來源：

| ID | Registry 名稱 | 目前 sub-function | 主要參數／用途 |
| --- | --- | --- | --- |
| `1` | `BlinkRed` | `BlinkBurstSingleLedPattern` | 單閃；紅色，ON 300ms、idle 300ms、`blinkTimes=1` |
| `2` | `BreathGreen` | `BreathGreenSingleLedPattern` | Normal；科技綠 `(0,255,100)`、24 BPM、最大亮度 64 |
| `3` | `BlinkBlue` | `BlinkBlueSingleLedPattern` | Development；科技藍 `(0,120,255)`、ON／OFF 120ms、最大亮度 64 |
| `4` | `OrangeTwice` | `ambulancePulseSingleLedPattern` | 原有橙色雙脈衝；可 override 顏色 |
| `5` | `GundamEyeWake` | `GundamEyeWakeSingleLedPattern` | 眼燈／部件覺醒 |
| `6` | `MachineGun` | `MachineGunSingleLedPattern` | 快速射擊／高速脈衝 |
| `7` | `InvertedMachineGun` | `InvertedMachineGunSingleLedPattern` | 反相高速脈衝 |
| `8` | `LongTurnOn` | `LongTurnOnSingleLedPattern` | 漸亮後保持 |
| `9` | `NavigationLight2` | `navigationLight2` | 導航／位置標示慢脈衝 |
| `10` | `SolidOn` | `SolidOnSingleLedPattern` | 穩定長亮 |
| `11` | `RedBlinkTwice` | `BlinkBurstSingleLedPattern` | 紅色雙閃；ON 100ms、gap 50ms、idle 250ms、`blinkTimes=2` |
| `12` | `Maintenance` | `BlinkBurstSingleLedPattern` | 維修；琥珀橙 `(255,140,0)`、180/120/1200ms、最大亮度 64 |
| `13` | `Combat` | `BlinkBurstSingleLedPattern` | 戰鬥；琥珀紅 `(255,35,5)`、150/100/1100ms、最大亮度 128 |

ID 1、11、12、13 共用 `BlinkBurstSingleLedPattern`，由 `BlinkTwiceState` 的
`blinkTimes`、ON、gap、idle、color、brightness 分別控制。新增只差閃爍次數、顏色或
時序的 Signal profile 時，先新增 state／參數並沿用這個 sub-function，不另開重複 pattern。
`BlinkRedSingleLedPattern` 與 `BlinkTwiceSingleLedPattern` 只保留給舊 caller 相容，不是
目前上述四個 registry entry 的實作。

`MachineGun／InvertedMachineGun` 只有敘事或功能明確需要快速射擊／高速警示時才使用；
不可只為增加變化而放進一般平台、導航或維修 profile。

##### Normal／Repair 的功能設計

- Normal 是正常運作狀態：依部件職責安排長亮、漸亮、呼吸、導航與少量警示；不要求全部點亮。
- Repair 是診斷／維修狀態：用警示、工作長亮、正常／異常狀態或明確關燈表達維修流程；不應運作的武器、推進或高熱部件可用 index `0` 關閉。
- Repair 不可只把 Normal 換色；功能改變時，pattern ID、節奏與 off 狀態也要重新設計。
- 已確認的 Excel 功能欄、劇情需求與實機安全優先；本表只提供選擇方法，不取代硬體資料。

例如 4 顆燈依序是「左導航、能源狀態、右導航、武器狀態」，Normal 可用
`{9, 2, 9, 0}`：導航慢脈衝、能源呼吸，未啟用的武器保持 off。Repair 可依診斷功能
改為 `{4, 10, 3, 0}`，而不是只複製 Normal 再換成紅／藍色。

##### Registry 與 state 穩定性

- Registry ID 是所有既有 profiles 的合約。新增 pattern 必須 append 到尾端；不可重排或刪除既有 registry entry。
- Stateful pattern 預設由 lazy pool 提供每顆 LED 的 state，避免不相關 LED 共用可變狀態。
- 只有需要自訂每燈時序／參數時才用 `overrideStates`；每個 entry 對應同一 LED index，且 state 生命週期必須足夠長。
- Stateful pattern 的 lazy pool 依每次呼叫的實際 `numLeds` 動態配置，不設沿用舊專案的固定燈數上限。
- 增加較長燈帶後，必須建置並檢查 standalone RAM；不可直接加入大型 file-scope state arrays。

#### Profile 類型：Normal／Repair／Develop

- Normal profile：正式啟動、儲能、長亮、Plasma、Trans-Am、呼吸等一般演出使用。
- Repair profile：屬於 `storyMode_signals_params`，只表達維修／訊號模式，不可當作一般演出 profile。
- Develop profile：屬於獨立的 `storyMode_develop_params`，是第三種新類型，只由 `storyMode_develop.cpp` 使用。
- Develop profile 不可引用 Normal 或 Repair 的 index／override arrays；即使 pattern ID、顏色及燈數暫時相同，也要保留獨立 arrays。
- 三種類型可以共用 `storyMode_2_params::specificColor_registry`；共用 registry 只代表共用 effect 定義，不代表共用硬體 profile。
- 合法 paired group 只可在同一 profile 類型、硬體配置與模式行為完全相同時共用 arrays。

#### 操作步驟

1. 確認目前專案的 Slave 定義與合法 grouping。
2. 從硬體來源列出每個 index 的部件、顏色、期望動作及實際總燈數。
3. 對照 `SpecificColorPattern` registry，分別決定每顆燈的 pattern ID 與 override color。
4. 依 `slave/group + profile purpose + RGB pin` 建立清楚、獨立的陣列名稱。
5. 在指定 story mode 的對應 `case slaveId` 明確 routing；不要用 wrapper 隱藏 Slave 或 RGB pin。
6. 用以下命令搜尋既有 array 的全部引用，再決定重用或新增：

   ```bash
   rg -n "<array-name>" firmware/shared/src/storymode firmware/shared/include/storymode
   ```

7. 隔離未列入需求的 consumer；停用或未註冊的 mode 也保留原行為，除非使用者明確要求修改。
8. 加入合約測試，驗證燈數、陣列內容、mode routing，以及其他 Slave／mode 沒有借用新 profile。

#### 何時可以共用

| 項目 | 可否共用 | 條件 |
| --- | --- | --- |
| `specificColor_registry` | 可以 | 使用同一組 effect 定義與 registry ID |
| index／override arrays | 通常不可以 | 只有合法 paired group、實際燈數、index 配置與模式行為全部相同 |
| 同一 Slave 的 Normal profile | 可以 | 多個指定 story modes 確實使用同一設計 |
| Normal 與 Repair profile | 不可以 | 模式語意或每燈 pattern 不同便拆成兩組 |
| 不同獨立 Slave | 不可以 | 即使顏色及 pattern 暫時相同，也保留各自硬體邊界 |

#### Slave 3 Normal／Repair 範例

- Normal 使用 `storyMode_2_params::slave3_rgb4_specificColorIndex` 與對應 override array，供 activation、storing energy stage 3、storyMode 2、plasma、trans-am、storyMode 3。
- Repair 使用 `storyMode_signals_params::slave3_repair_rgb4_specificColorIndex` 與對應 override array，只由 `storyMode_signals` 的 `case 3` 呼叫。
- 既有 `slave3_signals_rgb4_*` 若仍被 `storyMode_motor`／`storyMode_motor_reset` 使用，必須保留；不要直接改成 Repair。
- Slave 4、5、7/8 繼續使用各自 signal arrays，不 alias 到 Slave 3。
- index 6–7 即使同為綠色呼吸 `CRGB(15, 255, 25)`，也不代表可以跨 Slave 或跨 profile 共用陣列。

#### 常見錯誤

- 看到名稱含 `signals` 便直接修改，沒有先找出 motor 等其他 consumers。
- 因兩個 Slave 暫時使用相同 R/G/B，便讓它們引用同一組 arrays。
- 只縮短 array，沒有同步確認 `NUM_LEDS_RGBx`、呼叫長度及所有 consumers。
- 用 override color 選 effect；顏色相同不代表呼吸、長亮或閃爍動作相同。

#### Profile 驗證 checklist

- [ ] 實際燈數與 index 範圍已由硬體來源確認。
- [ ] Pattern ID 與 override color 已分開設計。
- [ ] 每顆 LED 已按功能決定長亮、漸亮、呼吸、警示或 off；沒有為了變化而強迫點亮。
- [ ] 所有 index 都是 `0..numPatterns`；`0` 與 `CRGB::Black` override 的語意沒有混用。
- [ ] Registry 既有順序未改動；新增 pattern 只 append 到尾端。
- [ ] 新增較長燈帶的 stateful profile 已確認 state 獨立性與 standalone RAM。
- [ ] 每個獨立 Slave／模式用途有自己的 profile arrays。
- [ ] 所有新增 routing 都在正確 `case slaveId`。
- [ ] 修改前後已用 `rg` 搜尋所有 array consumers。
- [ ] 未列入需求的 consumer、其他 Slave 與停用模式維持原行為。
- [ ] Contract tests 已驗證陣列內容、routing 與隔離邊界。
- [ ] Shared 變更已建置 master、受影響 Slave、standalone，並檢查 RAM。

#### storyMode 常用 RGB call example

新 project 的範例必須使用目前 slave 定義與 case 順序；Slave 10 是目前正式 Foulyoupou platform，不可當成舊 project 武器分組。

```cpp
switch (slaveId) {
case 1: {
    // Slave 1 platform RGB1 — platform base / flow.
    whiteSwipe(leds_RGB1, NUM_LEDS_RGB1, ...);
} break;

case 2: {
    // Slave 2 backpack RGB1 — backpack base flow.
    whiteSwipeWithBackgroundV3(leds_RGB1, NUM_LEDS_RGB1, ...);

    // Slave 2 backpack RGB2 — vent / energy.
    gradientVentPalette(leds_RGB2, NUM_LEDS_RGB2, ...);

    // Slave 2 backpack RGB3 — turbine / GN drive.
    turbine_v3(leds_RGB3, NUM_LEDS_RGB3, ...);

    // Slave 2 backpack RGB4 — signal / marker.
    SpecificColorPattern(leds_RGB4, NUM_LEDS_RGB4, ...);
} break;

case 3: {
    // Slave 3 chest RGB1 — chest base / breath.
    rgbBreath_swipe_palette_v3(leds_RGB1, NUM_LEDS_RGB1, ...);

    // Slave 3 chest RGB2 — vent.
    gradientVentPalette(leds_RGB2, NUM_LEDS_RGB2, ...);

    // Slave 3 chest RGB3 — turbine / GN drive.
    turbine_v3(leds_RGB3, NUM_LEDS_RGB3, ...);

    // Slave 3 chest RGB4 — signal.
    SpecificColorPattern(leds_RGB4, NUM_LEDS_RGB4, ...);
} break;

case 4:
case 5: {
    // Slave 4/5 paired body RGB1 — left/right body base.
    whiteSwipe(leds_RGB1, NUM_LEDS_RGB1, ...);

    // Slave 4/5 paired body RGB2 — vent.
    gradientVentPalette(leds_RGB2, NUM_LEDS_RGB2, ...);

    // Slave 4/5 paired body RGB3 — turbine / GN drive.
    turbine_v3(leds_RGB3, NUM_LEDS_RGB3, ...);

    // Slave 4/5 paired body RGB4 — signal.
    SpecificColorPattern(leds_RGB4, NUM_LEDS_RGB4, ...);

    // Slave 4/5 paired body RGB7 — both sides must run when enabled by Excel.
    footplatev2(leds_RGB7, NUM_LEDS_RGB7, ...);
} break;

case 6: {
    // Slave 6 independent RGB1 — body / waist base.
    mode_wled_meteor(leds_RGB1, NUM_LEDS_RGB1, ...);

    // Slave 6 independent RGB2 — vent.
    gradientVentPalette(leds_RGB2, NUM_LEDS_RGB2, ...);

    // Slave 6 independent RGB3 — turbine / GN drive.
    turbine_v3(leds_RGB3, NUM_LEDS_RGB3, ...);

    // Slave 6 independent RGB4 — signal.
    SpecificColorPattern(leds_RGB4, NUM_LEDS_RGB4, ...);
} break;

case 7:
case 8: {
    // Slave 7/8 leg RGB1 — L/R leg base, often synced by cross RGB group.
    rgbBreath_swipe_palette_v3(leds_RGB1, NUM_LEDS_RGB1, ...);

    // Slave 7/8 leg RGB4 or RGB9 — leg signal, depends on Excel.
    SpecificColorPattern(leds_RGB4, NUM_LEDS_RGB4, ...);
} break;

case 9: {
    // Slave 9 platform RGB1 — platform base.
    whiteSwipe(leds_RGB1, NUM_LEDS_RGB1, ...);
} break;

case 10: {
    // Slave 10 Foulyoupou platform — independent platform effect.
    GN_Drive_Running(leds_RGB1, NUM_LEDS_RGB1, ...);
} break;

default:
    break;
}
```

這個範例只表示 SOP 方向，不代表每個 slave 一定有 RGB1-RGB4。實作時一定要回 Excel / 接線表確認該 slave 實際有哪幾條 RGB。

#### 單燈 / PWM 習慣對應

| 功能 | 常用 function |
| --- | --- |
| 眼 | `chGundamEyeWake` |
| 明確標示火神炮 / Vulcan gun（主要為橙色武器燈） | `chValcanGun` |
| 散氣口 / 內構 | `chProgressiveFlash` |
| 長亮 / 長著 | `chOn` |
| 呼吸 | `chSmoothBeatsin16` |
| 推進 | `chProgressiveFlash` |
| 漩渦燈 | `turbine_v3` |
| 訊號 | `SpecificColorPattern` |
| 閃 | `chProgressiveFlash` |

這個表只按「功能描述」選 function。顏色只描述硬體，不能單獨決定 effect；同一顏色可以是長亮、呼吸、閃爍或其他已指定效果。若資料只有顏色，必須回查目前需求、story mode 設計或已確認程式，不可自行套用效果。

`chValcanGun` 判定規則：

- 火神炮主要是橙色武器燈，但必須由部件名稱、功能欄或已確認需求明確標示為「火神炮／Vulcan gun」，不可只看顏色。
- 黃色燈不等於火神炮；黃色 channel 應依實際用途選擇長亮、呼吸、訊號、閃爍或其他效果。
- 不是所有橙色燈都使用 `chValcanGun`；橙色也可能是 marker、signal、長亮或其他已指定效果。
- 「炮」是過於寬泛的描述。若無法確認是火神炮，先回查 Excel／接線表、零件名稱與 story mode 規格，不可自動套用 `chValcanGun`。

#### case / slave 放置

- slave X 的內容永遠放 `case X:`，例如 slave 6 放 `case 6:`、slave 7 放 `case 7:`、slave 8 放 `case 8:`。
- 如果 storyMode 有 `switch (slaveId)`，每個 slave 都放自己的 case。
- 本 project 使用 `slave 1-20`；Slave 19／20 是左右腳掌，接在 Branch 2 末端。
- 不要用舊 project 的 grouping。尤其不要把 `slave 2 / 6 / 9` 當成同一組 weapons。
- 只有需求明確指定獨立更新的 channel，才可放在函式層級、`switch (slaveId)` 外；其餘 PCA 呼叫都留在對應的 `case X:`。
- 這些規則是全部 storyMode 都要遵守，不是 `storyMode_2` 專用。

### 2.1 storyMode_develop

- Controller 狀態：正式 LED mode 0，不是 `storyMode_dev` 的縮寫。
- 目的：0083 試作機開發展示；以約 20% 輸出顯示核心 RGB／PCA 功能群。
- 固定時序：

| 時間 | state | 行為 |
| --- | --- | --- |
| `0:00` | `MODE_DEVELOP_INIT` | 重置 state，全部 RGB 先關閉 |
| `0:00–0:02` | `MODE_DEVELOP_WHITEBG` | 等待正式展示起點 |
| `0:02–0:32` | `MODE_DEVELOP_OPEN_LEGS` | 依 `slaveId` 播放 Develop RGB／PCA 配置 |
| `0:32` | `MODE_DEVELOP_END` | 全部 RGB 關閉並完成 mode |

- `SpecificColorPattern` 必須使用獨立 `storyMode_develop_params` index／override arrays；可共用 registry，不可共用 Normal／Repair 硬體 arrays。
- 需求若寫「全部正式 StoryModes」或「某 Slave 跨 StoryModes 更新」，清單必須明列 `storyMode_develop.cpp`；只有使用者明確排除才可不改。
- 新 Slave／RGB／PCA 沒有接線表時保持 off 並標記待確認；不可因其他 StoryMode 已有該 Slave 就自動套 effect。
- 驗證時必須分開檢查：`storyMode_develop` 的 mode 0 routing／32 秒結束，以及 `storyMode_dev` 的非正式進入條件；兩者不共用驗收結論。

### 2.2 storyMode_all_off

- Controller 狀態：不再註冊，不佔用正式 LED mode ID；只保留作清場工具。
- 目的：
  - 全部關燈，作為 reset / idle / mode 切換前的乾淨狀態。
- 時序：
  - `0:00`：所有 RGB / PWM / signal 類燈關閉。
- 先開哪種燈：
  - 不開燈，全部 off。
- 通常 function：
  - RGB：`rgbOff`
  - PWM/PCA：`chInitialStateAll()` 或個別 off function
- notes：
  - 這個 mode 不是表演效果，是清空狀態。
  - 不要在這裡加裝飾燈效。

### 2.3 storyMode_signals

- 目的：
  - 訊號燈模式。先清空，再開白底 / signal base，最後進入各 slave 的 signal pattern。
- 固定時序：

| 時間 | state | 先開哪種燈 | 通常 function |
| --- | --- | --- | --- |
| `0:00` | `MODE_SIGNALS_INIT` | 全部 signal / RGB 先關 | `rgbOff`, `chInitialStateAll()` |
| `0:00-0:02` | `MODE_SIGNALS_WHITEBG` | 白底、低亮 marker、PCA signal base | `chOn`, low brightness marker |
| `0:02-0:32` | `MODE_SIGNALS_OPEN_LEGS` | 各 slave 訊號燈開始跑 | `SpecificColorPattern`, `chValcanGun`, `chFlashAlternativeV2` |
| `0:32` | `MODE_SIGNALS_END` | 關閉 / reset | `rgbOff`, `chInitialStateAll()` |

- 常用 RGB：
  - Slave 3 RGB4：`SpecificColorPattern`
  - Slave 4/5 RGB4：`SpecificColorPattern`
  - Slave 2/6/9：依各自接線的 signal RGB 使用 `SpecificColorPattern`
  - Slave 7 RGB4、Slave 8 RGB9：`SpecificColorPattern`
- 常用 PWM：
  - marker / 白底：`chOn`
  - 火神炮 / 快閃：`chValcanGun`
  - 紅綠或兩組交替：`chFlashAlternativeV2`
- notes：
  - signal mode 優先使用 `SpecificColorPattern`。
  - 如果是 PWM 訊號，才用 `chFlashAlternative` / `chFlashAlternativeV2`。
  - signal RGB 通常不是流光，而是每顆燈有自己的 pattern。

### 2.4 storyMode_0_v1

- 目的：
  - 開場閃燈 / 啟動前的快速分段閃爍。
- 已知時長：
  - code 約 `30.2s`，timer 約 `31s`。
- 時序 notes：

| 階段 | 大約時間 | 先開哪種燈 | 通常 function |
| --- | --- | --- | --- |
| init | `0s` | 先全部關閉 | `rgbOff` |
| start / white swipe | 約 `2s-3.5s` | 白色 swipe / wire 類效果 | `GN_Wire_Normal`, white palette |
| all / third on | 中段 | 多數 RGB 白燈打開 | `rgbOn(..., white)` |
| final flash | 後段 | 快速分段閃爍 | `rgbOn`, `rgbOff` |
| end | 結尾 | 關閉 | `rgbOff` |

- 常用 RGB：
  - `GN_Wire_Normal(..., whiteSwipePalette)`
  - `rgbOn(..., white)`
  - `rgbOff`
- notes：
  - 這類 mode 是「白燈啟動 / 快速閃」。
  - 不要加入散氣、漩渦、腳底燈，除非 Excel 或需求明確寫。

#### storyMode_0_v1／v2 PCA 時序規則

- 所有 Slave 的專屬 PCA 效果只能從 `MODE_0_FLASH` 或之後開始；更早的 states 不可執行專屬 PCA 呼叫。
- PCA 呼叫直接寫在合法 state 的 `switch (slaveId)` → 對應 `case`；`MODE_0_INIT` 的共用 `chOffAll()` 只算初始化例外。
- `chRandomFlash` 的 mask 只能把接線表標示為「白／純白」的 channel 設為 `true`；暖白、黃色及其他顏色必須設為 `false`。
- Slave 2 背包 PCA 接線表沒有純白 channel，因此 `storyMode_0_v1`／`storyMode_0_v2` 的 Slave 2 不可呼叫 `chRandomFlash`。
- Slave 2 的 `MODE_0_START_FLASH` 統一使用 `randomFlashFixedCount_multiple` 控制 RGB1–RGB4，不再使用 `randomFlashWithGap_multiple`。

### 2.5 storyMode_0_v2

- 目的：
  - 第二版開場閃燈，比 v1 更細分 fraction stage。
- 已知時長：
  - code 約 `26.6s`，timer 約 `27s`。
- 時序 notes：

| 階段 | 大約時間 | 先開哪種燈 | 通常 function |
| --- | --- | --- | --- |
| `MODE_0_INIT` | `0s` | 全部關閉 | `rgbOff` |
| `MODE_0_START_FLASH` | 前 `5s` | 開場 flash / 低亮灰白；Slave 2 RGB1–RGB4 固定數量白閃 | `fill_solid`, `randomFlashWithGap_multiple`, `randomFlashFixedCount_multiple` |
| fraction stages | 中段 | 依 1/4、1/2、3/4 分段亮 | `rgbOn`, `rgbOff` |
| `MODE_0_ALL` | 後段 | 所有指定 RGB 短亮 | `rgbOn(..., white)` |
| final | 結尾 | 最後亮起後關閉 | `rgbOff` |

- 常用 RGB：
  - `randomFlashWithGap_multiple`
  - `randomFlashFixedCount_multiple`
  - `rgbOn(..., white)`
  - `rgbOff`
  - `GN_Sword_Pulse_Color`
  - `fill_solid(CRGB(...))`
- notes：
  - 這個 mode 主要是「分段白閃」。
  - 如果 Excel 寫一般 RGB 啟動閃，優先參考這個 mode。

### 2.6 storyMode_awakening_3

- 目的：
  - 覺醒 / 慢慢喚醒。先以 cross swipe 掃入，再持續全體呼吸，最後 fade out。
- 時序 notes：

| 階段 | 先開哪種燈 | 通常 function |
| --- | --- | --- |
| `MODE_AWAKENING_BREATH_ALL` | RGB1 cross swipe 掃入後全身呼吸 | `RGBBreathSwipePaletteV3Cross` |
| `MODE_AWAKENING_TRANSITION_BREATH_TO_SWIPE` | 呼吸轉流動 | `rgb_fadeOut`, swipe 類 RGB |
| `MODE_AWAKENING_FADEOUT_3` | 全部淡出 | `rgb_fadeOut`, `rgbOff` |

- 常用 RGB：
  - RGB1：`RGBBreathSwipePaletteV3Cross`
  - GN wire / 細線：`GN_Wire_Normal`
  - platform / 裝飾：`shoppingMallLight_V2`
- notes：
  - 這個 mode 的第一印象是「呼吸」，不是火神炮、不是 signal。
  - 如果使用者說覺醒、呼吸、慢慢亮，優先從這個模式找邏輯。
  - RGB1 使用固定綠色 `CRGB(15,255,25)`、local `15–210`、global `90/255`。
  - 保留 6 秒 swipe 與 6 秒 breath cycle；V3Cross 呼吸核心與 `smoothSineBreath` 相同，模式結束恢復一般 global `60/255`。

### 2.7 storyMode_activation

- 目的：
  - 啟動後持續運作,從呼吸 / 背景光進入 GN drive、散氣、漩渦、訊號。
- 時序 notes：

| 階段 | 先開哪種燈 | 通常 function |
| --- | --- | --- |
| continue / base | RGB1 背景流動先開始 | `whiteSwipeWithBackgroundV3`, `rgbBreath_swipe_palette_v2` |
| vent | 散氣口開始動 | `randomFillAll_V2`, `gradientVentPalette`, `VentEffect` |
| turbine / GN | 漩渦與 GN drive 持續跑 | `turbine_v3`, `GN_Drive_Normal`, `GN_Wire_Normal` |
| signal | 訊號燈加入 | `SpecificColorPattern` |

- 常用 RGB：
  - RGB1：`whiteSwipeWithBackgroundV3`
  - RGB2：`randomFillAll_V2` + `gradientVentPalette` 或 `VentEffect`
  - RGB3：`turbine_v3` / `GN_Drive_Normal`
  - RGB4：`SpecificColorPattern`
- notes：
  - 這是「啟動後 base running」類模式。
  - 如果 Excel 寫流光、散氣、漩渦一起維持，常參考這個 mode。

### 2.8 storyMode_storing_energy

- 目的：36 秒六階段跨 Slave 儲能；完整視覺與 timeslot 見 `docs/storymode/storymode目錄.md`。
- Stage 1 拓撲（Hi-Nu 三分支）：`1 → 2 → {3,5} → {4,6}`、`1 → 2 → 7 → {8,10} → {9,11} → {19,20}` 與 `1 → 2 → 12 → {14,15} → {16,17} → {13}`。三分支共用 comet cadence，但各自按長度填充；每 3 顆 comet 鎖定 1 個 5-LED block；S1 頭是 source，最後填滿。

| Timeslot | State | Coding note |
| --- | --- | --- |
| `0:00–0:20` | `MODE_STORING_ENERGY_STORING` | `paletteWave_StoringEnergyCross` 負責 comet 與 Tetris 填充；不可讓各 Slave 獨立直接 fill。 |
| `0:20–0:22` | `MODE_STORING_ENERGY_DIM_5` | 用效果函式淡至 5%，不修改 global brightness。 |
| `0:22–0:32` | `MODE_STORING_ENERGY_POWER_UP` | 設 global brightness `90/255`；用累積門檻逐秒加入訊號、白色 PCA、散熱、長亮、呼吸及閃燈／火神炮。 |
| `0:32–0:33` | `MODE_STORING_ENERGY_DROP_50` | RGB/PCA 降至 50%；global brightness 維持 `90/255`。 |
| `0:33–0:36` | `MODE_STORING_ENERGY_FULL_POWER` | global brightness 設為 `140/255`；RGB 過渡到 80%，PCA 80% 常亮。 |
| `0:36` | `MODE_STORING_ENERGY_END` | RGB/PCA 立即全關。 |

- 只有 `POWER_UP` 與 `FULL_POWER` 可以修改 FastLED global brightness。
- 各 Stage 的實際 effect 必須依目前程式與需求，不可把舊 `ACCELERATE／80_PERCENT／60_PERCENT` states 搬回來。

### 2.9 storyMode_2

- 目的：
  - 標準長著／啟動 SOP。每個功能 layer 都沿 Hi-Nu 三條部位 branch 逐段亮起，
    不可一次把全機同類 RGB／PCA 全部打開；結束時按功能 layer 及部位 branch
    雙重反序關閉。
- 這是本文件最重要的範例。
- 開啟功能順序：

```text
眼＋監視器（RGB／PCA）
-> Vent／散氣
-> RGB／PCA 白色長亮
-> 光暗／呼吸
-> Signal
-> 武器／推進器
```

- 各功能 layer 的部位開啟順序：

```text
Branch 1: S1 -> S2 -> S3/S5 -> S4/S6
Branch 2: S1 -> S2 -> S7 -> S8/S10 -> S9/S11 -> S19/S20
Branch 3: S1 -> S2 -> S12 -> S14/S15 -> S16/S17 -> S13
```

- 開啟 stage 與常用 function；實際時間門檻以目前 story mode 規格為準：

| 順序 | general description | RGB／PCA 行為與常用 function |
| --- | --- | --- |
| 1 | 眼＋監視器 | 眼用 `chGundamEyeWake`；監視器依已確認硬體使用 RGB／PCA 啟動效果 |
| 2 | Vent／散氣 | RGB 用 `VentEffect`；PCA 散氣／內構用 `chProgressiveFlash` |
| 3 | 白色長亮 | RGB 白色 base 用 `rgbOn(..., CRGB::White)` 或既有白色長亮效果；PCA 用 `chOn` |
| 4 | 光暗／呼吸 | RGB 使用既有 breath 效果；PCA 用 `chSmoothBeatsin16` |
| 5 | Signal | RGB 用 `SpecificColorPattern`；PCA 使用該 signal channel 已確認的 `ch*` 效果 |
| 6 | 武器／推進器 | 明確是火神炮才用 `chValcanGun`；明確是推進器才用 `chProgressiveFlash` |

- 關閉順序必須同時反轉功能及部位：

```text
武器／推進器
-> Signal
-> 光暗／呼吸
-> 白色長亮
-> Vent／散氣
-> 眼＋監視器

Branch 1: S4/S6 -> S3/S5 -> S2 -> S1
Branch 2: S19/S20 -> S9/S11 -> S8/S10 -> S7 -> S2 -> S1
Branch 3: S13 -> S16/S17 -> S14/S15 -> S12 -> S2 -> S1
```

- 三條 branch 的末端可各自按自己的進度反序關閉；共用 `S2／S1` 必須等三條
  branch 的下游部位都關閉後，才依 `S2 -> S1` 收尾。

時序只決定效果何時加入，不按顏色自動分配 effect。同一個 channel 若在後段轉換效果，必須確認後面的呼叫是有意取代前面的輸出。

#### RGB pin 習慣對應

共用參考：見 `2.0 常用單燈和 RGB function 對照` 的 `RGB pin 習慣對應`。

#### 單燈 / PWM 習慣對應

共用參考：見 `2.0 常用單燈和 RGB function 對照` 的 `單燈 / PWM 習慣對應`。

#### case / slave 放置

共用參考：見 `2.0 常用單燈和 RGB function 對照` 的 `case / slave 放置`。

### 2.10 storyMode_plasma

- 目的：90 秒五階段跨 Slave 綠色電漿；完整 physical strip、亮度與 timeslot 見 `docs/storymode/storymode目錄.md`。
- RGB1 sequential-on／爆光順序（Hi-Nu ring，由外向內）：`{19,20} → {9,11} → {4,6,8,10,13-17} → {3,5,7,12} → {2} → {1}`。
- Stage 4 lightning 五路 topology：背包 `S13-17 → S12 → S2 → S1`；左右手 `S2 → S3 → S4`／`S2 → S5 → S6`；左右腳 `S2 → S7 → S8 → S9 → S19`／`S2 → S7 → S10 → S11 → S20`。
- Stage 3 才把 global brightness 提升至 `200/255`；一般 stages 使用 `160/255`。
- signals 只在 Stage 4 執行；Stage 5 依 logical groups 分段收光。
- 不可把 Plasma 簡化成單一 Slave 或各 Slave 獨立 random lightning，否則跨接縫與同步節奏會斷開。

### 2.11 storyMode_trans_am

- 目的：
  - Trans-Am / 高能戰鬥狀態。多數部位進入高強度持續運作。
- 時序 notes：

| 階段 | 先開哪種燈 | 通常 function |
| --- | --- | --- |
| continue | 主體流光 / GN drive 先跑 | `GN_Drive_Running`, `whiteSwipeWithBackgroundV3` |
| vent | 散氣維持 | `VentEffect`, `randomFillAll_V2` |
| turbine | 漩渦維持 | `turbine_v3` |
| signal | 訊號維持 | `SpecificColorPattern` |
| footplate | 腳底維持 | `footplatev2` |

- 常用 RGB：
  - RGB1 / RGB7 / RGB9 / RGB11：`GN_Drive_Running`
  - RGB2：`VentEffect`
  - RGB3：`turbine_v3`
  - RGB4：`SpecificColorPattern` 或 `footplatev2`
- notes：
  - 這個 mode 比 storyMode_2 更激烈。
  - 如果使用者說 Trans-Am、戰鬥、全開狀態，優先參考這個 mode。

### 2.12 storyMode_3

- 目的：
  - 呼吸 / war robot yellow 類狀態。常見黃系、呼吸、GN wire、漩渦、腳底。
- 時序 notes：

| 階段 | 先開哪種燈 | 通常 function |
| --- | --- | --- |
| `MODE_3_INIT` | 全部先關 | `rgbOff` |
| `MODE_3_EYE` / `MODE_3_CONTINUE` | 黃系 base / 呼吸 / GN wire 開始 | `whiteSwipeWithBackgroundV3`, `gradientDynamicPalette`, `GN_Wire_Normal` |
| continue | 漩渦、腳底、訊號維持 | `turbine_v3`, `footplatev2`, `SpecificColorPattern`, `GN_Drive_Running` |
| `MODE_3_FADEOUT` | 淡出 | `rgb_fadeOut` |
| `MODE_3_END` | 關閉 | `rgbOff` |

- 常用 RGB：
  - `whiteSwipeWithBackgroundV3(..., warRobotYellowPalette)`
  - `gradientDynamicPalette(warRobotYellowPalette)`
  - `GN_Wire_Normal(..., warRobotYellowPalette)`
  - `turbine_v3`
  - `footplatev2`
  - `SpecificColorPattern`
- notes：
  - 如果使用者說「呼吸模式」、「黃系」、「war robot」，優先參考這個 mode。
  - Story Mode 3 第二輪 global `128/255` 已通過；第三輪暫用 global `90/255` 配合 V3Cross local `15–210` 實機測試，模式結束時仍恢復一般 global `60/255`。

#### War Robot 橙黃呼吸實機門檻

- 實測日期：2026-07-19。
- 測試條件：Standalone RGB1、`warRobotGradYellowPalette` index `90`、原版 `smoothSineBreath`、最高亮度 140、FastLED 全域亮度 128、`RGB_FREQUENCY=60`。
- 結果：最低亮度 `1–7` 全部不合格，低光時偏紅；最低亮度 `8` 通過，可維持橙黃色與呼吸效果。
- Global A/B：固定最低亮度 8 後，`128／90／60／50／40／30` 全部通過，均未變紅；正式選用 Story Mode 3 global `128/255`。
- 第三輪測試設定：V3Cross 使用實測色 `CRGB(180,65,0)`、local `15–210`、global `90/255`；預計 actual brightness 約為 `5–74`，其他 local 255 RGB 的最高輸出由 global 128 時的 128 降至 90。結果待實機確認。
- 設計規則：`RGBBreathSwipePaletteV3Cross` 三個 overload 以 `smoothSineBreath(color)` 為核心，統一使用 16-bit 正弦曲線並由最低亮度開始；只保留原本的 swipe-in 時序、comet 與跨 Slave virtual-strip／branching routing。V3Cross 的掃入、呼吸與 comet 基色全部直接取同一個 `CRGB color`，不再取樣 palette。Story Mode 3 使用實測色 `CRGB(180,65,0)`，每 frame 要求 global `90/255`，結束時還原 `60/255`。更換 LED、固定色或電源條件後必須重新實測。

### 2.13 storyMode_idle

- 目的：
  - idle / 空閒狀態。
- 時序：
  - `MODE_IDLE_INTERVAL`：全部或大部分 RGB 關閉。
- 通常 function：
  - `rgbOff`
- notes：
  - 不要在 idle 自動加高亮效果。

### 2.14 storyMode_motor

- Controller：Servo StoryMode 1，`storyMode_motor`；負責 servo／motor 開啟演出。
- 本節只保存演出語意與 routing 規則；GPIO、UART address、燈數及其他硬體設定以 PlatformIO environment 與接線表為準，不抄入 StoryMode description。

#### 固定演出順序

1. 眼睛與監視器先啟動。
2. 流光以外的燈依 `storyMode_2` 相同部件的功能規格進入正常運作；訊號燈顯示綠色，代表部位安全。
3. 全身白色流光播放兩次；Slave grouping 與跨 Slave branch topology 必須沿用 `storyMode_0_v1`，不可另建第二套 grouping。
4. 白色流光完成後轉為綠色 `GN_Drive_Running`，各部位訊號燈繼續顯示安全狀態。
5. Motor choreography 以 Slave 為動作單位：該 Slave 任一 motor 開始前 `0.5s`，同部位訊號燈轉為紅色閃爍；motor 開始時恢復綠色安全狀態。
6. Motor 開始時，同部位散熱口播放開甲排氣：使用 `VentEffect` 產生氣流紋理，再套用一次性 brightness envelope，先快速升亮，之後緩慢降至很暗。

#### 實作合約

- 「流光」指 `storyMode_0_v1` routing 內為該 Slave 指定的 FastLED RGB strip，不是 `LED_ESP_PIN_*` 單色 GPIO；RGB4 永遠不參與流光。
- RGB4 是訊號燈專用 strip，綠色安全狀態及紅色預警都必須使用 `SpecificColorPattern`，不可用 `fill_solid()`、`rgbOn()` 或其他效果繞過 per-LED profile。
- 非流光 RGB／PCA／GPIO 效果以 `storyMode_2` 的同 Slave、同部件 routing 為基準；只有 Motor choreography 明確覆寫的訊號與散熱效果可以不同。
- 同一 Slave stage 內先寫 motor／servo，再寫 RGB／PWM；同時動作的 motors 共用同一個 `motorStartMs`，完成後明確 STOP。
- Motor signal lead 與 vent envelope 使用 `storyMode_parameter` 參數；不要在各 motor call site 重複 magic number。
- `VentEffect` 已提供散熱氣流紋理；Motor Mode 直接加亮度 envelope，不新增只包住 `VentEffect` 的同義 wrapper。
- `storyMode_motor_reset` 的 close sequence 保持獨立，不混入本模式。

### 2.15 storyMode_motor_reset

- 目的：
  - servo / motor 回收、關閉 sequence。
- 已知時長：
  - `36s`，四段各 9 秒。
- 固定時序 notes：

| 階段 | 先做什麼 | 通常 function |
| --- | --- | --- |
| close top | 上半部先關 / signal 指示 | `SpecificColorPattern`, `rgbOff` |
| close mid | 中段關閉 | `SpecificColorPattern`, `rgbOff` |
| close skirt | 裙甲關閉 | `SpecificColorPattern`, `rgbOff` |
| close legs | 腳部關閉 | `SpecificColorPattern`, `rgbOff` |
| end | 全部 reset | `rgbOff`, `chInitialStateAll()` |

- notes：
  - 這是 servo 組 mode 2。
  - 順序是 top -> mid -> skirt -> legs。
  - 主要用 signal 提示，不是大規模 RGB 表演。

---

## 3. Excel 欄位解讀

Excel 是接線表。它回答：「這個零件接到哪個 slave、哪個 RGB pin、哪個 PWM channel」。

### 3.1 `All_Data` 欄位

| 欄位 | 意思 | 寫 code 時用途 |
| --- | --- | --- |
| `B` | item number | 追蹤資料來源 |
| `C` | 零件大分類 | 註解用 |
| `D` | 零件描述 | 註解用 |
| `E` | 圖片或參考 | 需要時看外觀 |
| `I:J:K` | LED 數量 | 填入註解與確認 `NUM_LEDS_RGBx` |
| `L` | RGB 類型 / 顏色 / 功能 | 顏色供硬體註解；明確功能才用於決定 effect |
| `M` | 總 LED 數 | 驗證數量 |
| `N:O` | 左側 chip / pin | 判斷 channel |
| `P:Q` | 右側 chip / pin | 判斷 channel |
| `R:S` | 中間 chip / pin | 判斷 channel |
| `T` | 備註 | 補充規則 |

### 3.2 slave sheet 欄位

| 欄位 | 意思 | 寫 code 時用途 |
| --- | --- | --- |
| `A1:B1` | slave 編號 | 決定 `case X:` |
| `A2:B2` | PWM list | 決定此 slave 有哪些 PWM board |
| `C` | type | RGB / PWM / motor |
| `D` | channel | RGB pin 或 PWM channel |
| `F` | 最大 LED 數 | 驗證 LED 數 |
| `G` | 零件描述 | 複製成 code 註解 |
| `H` | 功能註解 | 決定 effect |
| `J` 之後 | storyMode 欄位 | 決定該 storyMode 要不要啟用 |

### 3.3 Excel 到 code 的判斷流程

```text
找到 slave
  -> 決定 case X

找到 type
  -> RGB 用 leds_RGBx
  -> PWM 用 pcaLed[PWMn * 16 + PWM_CHANNEL_x]
  -> motor/servo 用 espMotor[x] 或既有 motor API

找到 channel
  -> RGB pin 1 = leds_RGB1
  -> RGB pin 2 = leds_RGB2
  -> PWM 0PWM CH4 = pcaLed[PWM0 * 16 + PWM_CHANNEL_4]

找到零件描述
  -> 放到註解

找到功能 / effect 需求 / storyMode 欄
  -> 決定 effect function 和 timeslot

找到顏色
  -> 只補硬體註解，不單獨決定 effect
```

### 3.4 PWM 範例

#### Excel／接線表 mapping

1. `slaveX` 決定 `case X:`。
2. `0PWM`、`1PWM` 轉成 `PWM0`、`PWM1`。
3. `CH x` 轉成 `PWM_CHANNEL_x`；連續 channel loop 才使用 `i`。
4. I2C address 只寫入硬體註解，不可寫成 `pcaLed[0xNN * 16 + channel]`。
5. 顏色只描述硬體，不能單獨決定 effect；同一顏色可以使用不同效果。
6. effect、brightness、period、burst count 與 idle 必須來自目前功能需求或 StoryMode 設計，不沿用舊 project 數值。

完整火神炮呼叫：

```cpp
chValcanGun(pcaLed[PWM0 * 16 + i], chBeaconFastFlashBrightness,
            chBeaconFlashMin, chBeaconFastFlashOn2, flashCount_pwm0[i],
            isOnArr_pwm0[i], lastUpdateArr_pwm0[i], chGunBurstRestMs,
            chGunBurstCount, chGunFadeOutMs);
```

參數群依序是 channel target、max/min brightness、flash interval、per-channel burst state、rest time、burst count、optional fade-out time。fade-out 為 0 時保持原本瞬間關燈行為。只有部件功能明確是火神炮／Vulcan 才使用；黃色或橙色本身都不構成判定。

完整漸進閃呼叫：

```cpp
chProgressiveFlash(pcaLed[PWM0 * 16 + PWM_CHANNEL_3],
                   chBrightnessFlashHigh, chBrightnessFlashLow,
                   totalDuration, stopSecond);
```

參數群依序是 channel target、high/low brightness、total duration、stop point。適用於需求明確指定的散氣、內構、推進或漸進閃；若功能應停用，保持 off 是正確設計。

PCA channel 註解固定使用以下格式：

```text
// Slave {id} PWM{board} CH{channel/range} (0x{address}) {繁體中文部件描述}。
```

- `Slave`、`PWM`、`CH`、`(0xNN)` 保持 ASCII，順序不可更換。
- 部件描述直接沿用 Excel / 接線表的繁體中文，包含部位、顏色與已知燈珠數，不翻譯成英文。
- 只有實際硬體描述完全相符的 channel 才能合併；合併後要正確整合部位與總燈珠數。
- 註解只描述 PCA channel 硬體，不附加 effect function 名稱。

Excel：

```text
slave4 PWM 5A
0PWM
CH 0
胸口 暖白 1 燈
```

Code：

```cpp
case 4: {
    // Slave 4 PWM0 CH0 (0x5A) 胸口，暖白，1粒。
    chOn(pcaLed[PWM0 * 16 + PWM_CHANNEL_0], chBrightnessOnLow);
} break;
```

合併 channel 範例：

```cpp
// Slave 8 PWM2 CH12-13 (0x49) 右膝頭內側／外側電容，黃，2粒。
```

---

## 4. case / slave 放置規則

規則：slave 幾，就放在 `case 幾`。

| Excel / 接線表 | code 放置位置 |
| --- | --- |
| slave 2 | `case 2:` |
| slave 3 | `case 3:` |
| slave 4 | `case 4:` |
| slave 5 | `case 5:` |
| slave 6 | `case 6:` |
| slave 7 | `case 7:` |
| slave 8 | `case 8:` |
| slave 9 | `case 9:` |

如果兩個 slave 完全一樣，才可以共用：

```cpp
case 4:
case 5: {
    // Slave 4/5 RGB2 散氣口 - VentEffect
    VentEffect(leds_RGB2, NUM_LEDS_RGB2, ...);
} break;
```

不可以：

- 把 slave 6 的效果放到 `case 5:`。
- 用 helper / macro / lambda 隱藏 channel。
- 把很多 slave 混在一起，導致看不出哪個硬體被控制。

---

## 5. Coding Workflow

### 5.1 寫 code 前

先確認：

- 要改哪個 `storyMode_*.cpp`。
- 要改哪個 storyMode function。
- 這次會影響哪些 slave。
- 是否會動到 shared code。
- 是否需要改 `storyMode_parameter.h` / `storyMode_parameter.cpp`。
- 是否需要新增 state / context。
- 是否需要更新 docs。

### 5.2 code 結構

標準結構：

```cpp
if (time >= stageStartMs) {
    switch (slaveId) {
    case X: {
        // Slave X RGBn / PWMn CHx 零件名稱 LED數 - effectName
        effectFunction(...);
    } break;
    default:
        break;
    }
}
```

多個 stage：

```cpp
if (time >= 0) {
    // stage 1
}

if (time >= 2000) {
    // stage 2
}

if (time >= 4000) {
    // stage 3
}
```

### 5.3 參數放置規則

- 優先使用既有 `storyMode_parameter`。
- 如果沒有，新增到 `storyMode_parameter.h` / `storyMode_parameter.cpp`。
- 效果專用 channel list、group size 與可調參數放在 `storyMode_parameter.h/.cpp`；story mode 內只保留清楚呼叫。
- 不要把大量 magic number 散落在 `storyMode_*.cpp`。
- 不要在 storyMode `.cpp` 建一堆 local config struct。
- context / state 要沿用既有 namespace 和既有 instance pool。

### 5.4 不要做的 coding 行為

- 不看 Excel 就猜 channel。
- 把 slave 放錯 case。
- 把 RGB pin 寫錯，例如 Excel 是 RGB3 但 code 寫 `leds_RGB2`。
- 把 PWM board 寫錯，例如 Excel 是 `1PWM` 但 code 寫 `PWM0`。
- 新增不必要 helper、macro、lambda。
- 隱藏 channel mapping。
- 在時序敏感 code 加大量 `Serial.print`。
- 改不相關 storyMode。
- 留下假參數或未完成 skeleton。

---

## 5.5 Story Mode 亮度對比與供電預算標準

亮度對比的核心不是「整機一起加亮」，而是依部件用途調整 local brightness，
讓觀眾一眼看出能源核心、維修工作燈或正在動作的機構，同時控制電源負載。

### 核准的 global brightness

- Storing global `90/140` 已核准，必須保持原值。
- Plasma global `160/200` 已核准，必須保持原值。
- Story Mode 3 第二輪 global `128/255` 已通過；第三輪測試暫用 global `90/255` 與 V3Cross local `15–210`（actual 約 `5–74`），結束時必須恢復一般 `60/255`。
- 其他 Story Modes 不可新增或修改 global brightness；不得用
  `FastLED.setBrightness()` 代替每個 effect 的 local `brightnessMax`。
- `storyMode_0_v1` 與 `storyMode_0_v2` 不在本輪亮度調整範圍，保持原樣。

### Slave 1／9／10 FastLED RGB 亮度上限

這是正式 story frame 的 RGB 輸出政策，不是硬體 grouping，也不是把兩個 Slave
合併成同一個 effect group。每個 story mode 仍先算自己的 requested brightness，
最後才套用指定 Slave 的輸出上限：

```text
finalRgbBrightness = min(requestedStoryBrightness, perSlaveCap, powerCap)
```

- `Slave 1`、`Slave 9` 的 FastLED RGB 最終亮度上限固定為 `10/255`。
- 這個上限適用於全部正式 story mode，包含會自行設定 global brightness 的
  `storyMode_plasma` 與 `storyMode_storing_energy`。
- Storing `90/140` 與 Plasma `160/200` 的 stage 設定保持原值；`Slave 1`、
  `Slave 9` 在 `FastLED.show()` 前套用 per-slave cap。
- `Slave 10` 的 FastLED RGB 最終亮度上限固定為 `42/255`，不跟隨 Story Mode
  requested global brightness 比例變化；Normal、Awakening、Storing、Plasma 都不超過 `42`。
- 這條規則只限制 FastLED RGB；PCA/PWM 單色燈維持各 story mode 原本亮度。
- 不可把這些 per-slave cap 無條件套到全部 Slave，避免連帶改變
  `Slave 2–8` 的輸出。
- 實作時使用 `POWER_DEBUG_SLAVE1_BRIGHTNESS`、
  `POWER_DEBUG_SLAVE9_BRIGHTNESS`、`POWER_DEBUG_SLAVE10_BRIGHTNESS`
  與正式 story frame 的最終政策；不可逐一修改各 effect 的 local brightness。
- 最終限幅必須放在每個正式 frame 完成效果計算後、`FastLED.show()` 前；這樣
  一般模式及自行呼叫 `FastLED.setBrightness()` 的特殊模式都會套用同一政策。
- `runStoryModeAll()` 與 `runStoryModeSingle()` 都必須對 Slave 1、9、10 執行
  最終政策；未註冊的
  `storyMode_dev`／`storyMode_demo` 測試入口維持原行為。

### RGB local brightness 規則

`localBrightness` 不是最終輸出亮度。每個計畫與驗證表必須同時列出：

```text
actualBrightness = effectiveGlobalBrightness × localBrightness / 255
```

1. 每個 RGB effect 依部件角色使用自己的 local `brightnessMax`，並換算
   `actualBrightness`；不可把 local 數字直接當成肉眼可見的最終亮度。
2. `localBrightness = 255` 只代表保留全部 global brightness，不能突破 global 上限。
3. 能源核心、GN drive、眼燈或劇情主效果可以是該 stage 最亮部件。
4. 主體燈、散熱口、訊號與裝飾必須至少分成主角／輔助／背景三層。
5. 想增加對比時，優先降低次要部件的 `brightnessMax`；不要先提高全部上限。
6. 修改後逐 stage 計算 `LED 數 × actualBrightness` 總和，必須不得高於修改前。
7. 沒有自行設定 global 的 mode，必須先記錄 mode 入口的 effective global，再換算
   actual；不可假設前一個 mode 已還原 global，也不可為了湊數字新增 `setBrightness()`。
8. 參數放在對應 story mode namespace；不可修改 shared
   `storyMode::universalBrightnessMin/Max` 影響其他 consumers。

### PCA brightness 規則

PCA brightness 必須依機械／劇情用途決定，不可只按顏色或 channel 順序套值。

| 部件用途 | 亮度層級 | 合理原因 |
| --- | --- | --- |
| 能源核心、眼燈 | 主角 | 表示能量來源或機體狀態，必須最容易辨識。 |
| Repair 暖白內構工作燈 | 主角 | 維修人員需要看清內部結構。 |
| 正在移動／回收的 joint、position light | 主角 | 作為機械動作安全標示，指出目前動作位置。 |
| 紅／綠狀態燈、主體外框 | 輔助 | 需要可見，但不應搶過工作燈、核心或動作標示。 |
| 裝飾、背景、非當前機構 | 背景／關閉 | 保留輪廓並降低同時供電負載。 |
| 武器、散熱、推進系統在 Repair mode | 關閉 | 維修狀態不應誤啟動戰鬥或高熱部件。 |

每個 stage 要比較修改前後「同時啟用 PCA channel 的 peak brightness 總和」；
修改後必須不得高於修改前。若某個機械主角需要更亮，必須同步降低或關閉
同 stage 的次要 PCA 部件。

需要三層同時可見時，第一輪 PCA raw brightness 對比目標為：主角至少為輔助的
`4 倍`，輔助至少為背景的 `3 倍`；不需要辨識的背景應直接關閉。這是起始校正
目標，仍須依 `channelMap` 極性、LED 實際光效與實機 A/B 微調，且不得突破 stage
修改前的 PCA peak budget。

### 調整流程

1. 先從 Excel／接線表確認 Slave、RGB/PWM、部件名稱、顏色與機械用途。
2. 列出該 stage 修改前的 RGB 與 PCA peak brightness 預算。
3. 指定唯一主角或少量主角，並寫出「為何它在此 mode 應更亮」。
4. 調整 local `brightnessMax` 與 PCA brightness；不改 effect、時序或 routing。
5. 驗證修改後 RGB／PCA peak 預算均不高於修改前。
6. 實機 A/B 檢查主角可辨識、背景不洗白，且沒有掉壓、重啟或異常閃爍。
7. Shared code 依規則建置 master、受影響 slave 與 standalone。

### 禁止模式

- 不可用「更有氣勢」作為唯一理由把全部部件加亮。
- 不可把另一個 story mode 或另一個 Slave 的 brightness 數值直接複製過來。
- 不可同時提高主角、輔助與背景，造成對比不變但電流增加。
- 不可把 RGB 顏色值當成 PCA 單色燈的顏色控制；PCA 顏色由實體燈珠決定。
- 不可忽略 PCA channel map 極性；實機確認數值增加是否真的代表更亮。

---

## 6. 驗證流程

只需要隨機抽 1 個修改過的 slave 做完整驗證。

抽查範例：抽 slave 6。

1. 到 Excel / slave sheet 找 slave 6。
2. 記下 slave 6 的 RGB pin、PWM board、PWM channel。
3. 到 code 找 `case 6:`。
4. 確認 `RGB3` 是否真的寫 `leds_RGB3`。
5. 確認 `0PWM CH14` 是否真的寫 `pcaLed[PWM0 * 16 + PWM_CHANNEL_14]`。
6. 確認註解有零件名稱和 LED 數量。
7. 確認 effect 對應正確。
8. 確認時間門檻是累積式 `if (time >= X)`。
9. 確認沒有把 slave 6 的效果寫到其他 case。

### 6.1 effect 對應檢查

先核對 general description 或明確效果需求，再核對 function；不要從 LED 顏色反推效果。

| general description | 應該看到的 function |
| --- | --- |
| 眼 | `chGundamEyeWake` |
| 散氣 | `chProgressiveFlash` / `VentEffect` |
| 長亮 / 長著 | `chOn` |
| 呼吸 | `chSmoothBeatsin16` |
| 訊號 | `SpecificColorPattern` / `chFlashAlternative` |
| 明確標示火神炮 / Vulcan gun（主要為橙色武器燈） | `chValcanGun` |
| 漩渦燈 | `turbine_v3` |
| 腳底燈 | `footplatev2` |

黃色不代表火神炮，橙色也不必然使用 `chValcanGun`；必須先由部件名稱、功能欄或已確認需求判斷實際用途。

### 6.2 Build

如果改 storyMode 或 shared code，建置 master 與受影響的 slave：

```bash
pio run -e master -e <affected-slave>
```

只有任務包含 standalone 或使用者明確要求時才加入 `slave_standalone`；使用者指定驗證範圍時以該範圍為準。

---

## 7. 最終交付 checklist

- [ ] 已讀本文件的 `StoryMode Notes Library`。
- [ ] 已依對應 storyMode 判斷「哪種燈先開」。
- [ ] 已依明確功能需求選擇 function，沒有只憑顏色猜效果。
- [ ] 已讀 Excel / 接線表。
- [ ] 已把 slave X 放進 `case X:`。
- [ ] 已把 RGB pin 對到正確 `leds_RGBx`。
- [ ] 已把 PWM board/channel 對到正確 `pcaLed[PWMn * 16 + PWM_CHANNEL_x]`。
- [ ] PCA channel 註解符合 `Slave → PWM → CH → (0xNN) → 繁體中文部件描述`。
- [ ] 每個硬體呼叫前都有註解。
- [ ] 使用累積時間門檻 `if (time >= X)`。
- [ ] 沒有新增不必要 helper / macro / lambda。
- [ ] motor/servo 呼叫排在 RGB/PWM 前面。
- [ ] 至少隨機抽 1 個 slave 從 Excel 對到 code。
- [ ] 已按任務範圍 build master 與受影響 slave。

---

## 8. 下次給 Codex 的短指令

```text
請先讀 .codex/skills/project-automation-rules/SKILL.md，並依 reference routing 讀主規則、函式目錄、元件 StoryMode 矩陣與 project call archive。
請依目前 PGU 的 StoryMode Notes Library 判斷時序、哪種燈先開及常用 function，再讀 Excel / 接線表，把硬體位置放進正確 case。
寫 code 時照 Coding Workflow：用累積 if (time >= X)，每個 slave 放自己的 case X，每個 RGB/PWM/motor 呼叫前要有硬體註解。
驗證時只需要隨機抽 1 個修改過的 slave，從 Excel 對到 code 完整檢查。
```
