# RGB Effect 撰寫與轉換標準

本文件整理本 session 訂下的 RGB effect 規則。核心概念很簡單：effect 像一台機器，ColorPicker 和 storyMode 都只是調旋鈕；旋鈕名稱、旋鈕數值、機器實際反應必須一致。

## 適用範圍

適用於：

- `firmware/shared/include/lib/lib_rgb.h`
- `firmware/shared/src/lib/lib_rgb.cpp`
- `firmware/shared/include/patterns/patterns_rgb.h`
- `firmware/shared/src/patterns/patterns_rgb.cpp`
- `firmware/slave/src/slave_live_colorpicker.cpp`
- `web/script.js`
- storyMode 中呼叫 RGB effect 的位置

不包含：

- `SpecificColorPattern`
- `SpecificColorPattern` 的 12 個 single-LED sub functions
- 純 helper / calculator / init function

## Function Signature 標準

轉換後的 public effect 不保留舊簽名，也不新增 inline legacy wrapper。

標準簽名形狀：

```cpp
void exampleEffect(CRGB* leds, int NUM_LEDS,
                   int speed,
                   uint8_t brightnessMin,
                   uint8_t brightnessMax,
                   uint32_t cycleDurationMs,
                   uint32_t totalDurationMs,
                   WLED_DirectionMode directionMode,
                   CRGB color,
                   CRGBPalette16 palette,
                   const RgbExampleParams& params,
                   RgbExampleContext& context);
```

若 effect 回傳完成狀態，可用 `bool`：

```cpp
bool exampleSwipe(CRGB* leds, int NUM_LEDS,
                  int speed,
                  uint8_t brightnessMin,
                  uint8_t brightnessMax,
                  uint32_t cycleDurationMs,
                  uint32_t totalDurationMs,
                  WLED_DirectionMode directionMode,
                  CRGB color,
                  CRGBPalette16 palette,
                  const RgbExampleSwipeParams& params,
                  RgbExampleSwipeContext& context);
```

## 三層參數模型

### Universal 參數

所有 RGB effects 優先支援這些通用控制：

- `speed`：速度，建議用 `int`，有效範圍 `0..65535`。數值越高，動畫通常越快；數值越低，動畫越慢。
- `brightnessMin` / `brightnessMax`：亮度範圍。調低會更暗，調高會更亮。
- `cycleDurationMs`：一輪效果的時間。數值越高，一輪越慢。
- `totalDurationMs`：整個效果或階段總時間。數值越高，整段演出越長。
- `directionMode`：方向。必須用 `WLED_DirectionMode` enum，不用 bool。
- `color`：主色。設定後應能覆蓋或影響主要可見顏色。
- `palette`：色盤。適合流光、漸層、多色變化。

### Effect Params

`RgbXxxParams` 放該 effect 自己的可調參數，例如：

- 拖尾長度
- comet head / tail 長度
- 閃爍間隔
- fade amount
- 火花密度
- GN / weapon 顏色
- palette index range

這些值會出現在 ColorPicker submenu，所以命名要穩定、好懂。

### Context

`RgbXxxContext` 只放 runtime state 或 pointer，例如：

- instance pointer
- palette index pointer
- last update time pointer
- hue pointer
- per-strip state buffer

Context 不放使用者會調的外觀值。外觀值放 universal 或 params。

## StoryMode Call 標準

storyMode call 必須清楚、可追蹤、參數不互搶。

正確方向：

```cpp
// RGB2 散氣口 — exampleEffect
exampleEffect(leds_RGB2, NUM_LEDS_RGB2,
              sm_signals::exampleEffectSpeed,
              sm_signals::exampleEffectBrightnessMin,
              sm_signals::exampleEffectBrightnessMax,
              sm_signals::exampleEffectCycleDurationMs,
              sm_signals::exampleEffectTotalDurationMs,
              sm_signals::exampleEffectDirectionMode,
              sm_signals::exampleEffectColor,
              sm_signals::exampleEffectPalette,
              sm_signals::exampleEffectParams,
              exampleContexts[slaveId][1]);
```

重要規則：

- storyMode `.cpp` 不直接建立 local config struct。
- 預設值放在 `storyMode_parameter.cpp`。
- 宣告放在 `storyMode_parameter.h`。
- 只屬於某個 storyMode 的 RGB 參數放在該 storyMode namespace，例如 `sm_signals::...`、`sm_trans_am::...`；不要放進泛用 `sm_rgb`。
- 通用參數要在 call site 展開成原本的 effect signature，不要用 `RgbXxxConfig` 把 universal 與 effect params 包成一整包。
- context / instance pool 放在 `storyMode_struct.h` 或既有 state 檔。
- 同一個 effect 用在不同 strip 時，context 要分開。
- call site 不塞裸數字；可讀的數字預設值放在 `storyMode_parameter.cpp`，call site 使用有名字的參數。

## ColorPicker 標準

每個可調參數都要完成整條鏈：

```text
web slider -> API key -> slave_live_colorpicker patternParam* -> effect params -> 實際畫面變化
```

需要同步：

- submenu slider
- info icon 文案
- output JSON
- standalone live render case
- validator

若底層參數是 `int` 或需要大範圍調整，UI slider 的 `min/max/step/default` 也要同步放大。不要讓 firmware 已支援 `0..65535`，但 ColorPicker 仍只送 `0..255`。

info icon 文案要短，直接描述調高/調低會看到什麼。例：

```text
拖尾就是光點後面留下多長的尾巴。數值越高，尾巴越長，看起來更像流星。
```

避免深技術描述，避免使用者看不懂的內部演算法名。

## 避免 Hardcode

不可把使用者會想調的值藏在 effect function 裡：

- 固定亮度
- 固定顏色
- 固定速度
- 固定方向
- 固定 duration
- 固定尾巴長度
- 固定閃爍次數或間隔

可以保留：

- array bound guard
- safety clamp
- `CRGB::Black` 清 buffer
- 不影響外觀的內部索引保護

## Direction 標準

direction 使用 enum：

```cpp
WLED_DIR_FORWARD
WLED_DIR_BACKWARD
WLED_DIR_CENTER_OUT
WLED_DIR_CENTER_IN
```

不要新增或保留 `bool direction` public signature。Forward / backward / center mode 的行為要在 effect 內或共用 helper 內清楚處理，不能靠外層重複 remap 造成中心方向反掉。

## 功能等價驗收

更新 storyMode call 後，要用這些問題檢查：

- 原本的顏色是否一樣？
- 原本的速度是否一樣？
- 原本的亮度是否一樣？
- 原本的方向是否一樣？
- 多條 strip 是否各自有獨立 state？
- ColorPicker slider 是否真的改變畫面？
- UI key、output JSON key、firmware key 是否一致？

只要其中一項不成立，就不算完成轉換。

## 最小驗證

本 session 指定只 build standalone：

```bash
python3 scripts/validate_rgb_full_param_inventory.py
python3 scripts/validate_rgb_colorpicker_params.py
python3 scripts/validate_pattern_info_icons.py
git diff --check
arch -arm64 pio run -e slave_standalone
```

若之後不是本 session 限制，shared code 變更應至少補 build master、一個 slave 與 standalone。
