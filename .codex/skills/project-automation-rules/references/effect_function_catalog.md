# Effect Function Catalog

> PGU `dev_PGU_V2` 是目前標準。此檔由公開 header 產生；完整參數以 Signature 為準，例子列出全部 argument，不省略。
> `PGU consumers` 只表示目前程式有直接呼叫；`available` 不代表可自行套入 storyMode。

## SpecificColorPattern signal design

`RGB4／SpecificColorPattern` 是訊號燈分派器：registry ID／名稱是 profile 合約，sub-function 是可共用的目前實作；Normal／Repair／Develop 必須用各自參數組。ID 1、11、12、13 共用 `BlinkBurstSingleLedPattern`，由 `BlinkTwiceState` 調整閃爍次數、ON、gap、idle、顏色與亮度；不要為只差時序或顏色的 profile 新增重複 pattern。其他常用 sub-pattern 包括 `BreathGreenSingleLedPattern`、`BlinkBlueSingleLedPattern`、`MachineGunSingleLedPattern`、`LongTurnOnSingleLedPattern`、`SolidOnSingleLedPattern`。每燈 state 依實際 `numLeds` 動態配置。

<!-- API:AmbulanceRedSingle -->
### `AmbulanceRedSingle`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void AmbulanceRedSingle(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
AmbulanceRedSingle(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:AmbulanceSingleLedPattern -->
### `AmbulanceSingleLedPattern`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void AmbulanceSingleLedPattern(CRGB* led, int ledIndex, void* state, unsigned long now);`
- General／Component: RGB signal／marker；由 profile namespace 與 sub-pattern 決定逐粒功能。
- Parameter groups: LED target／range、state／lifecycle
- Complete example call:

```cpp
AmbulanceSingleLedPattern(led, ledIndex, state, now);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:BlinkBlueSingleLedPattern -->
### `BlinkBlueSingleLedPattern`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void BlinkBlueSingleLedPattern(CRGB* led, int ledIndex, void* state, unsigned long now);`
- General／Component: RGB signal／marker；由 profile namespace 與 sub-pattern 決定逐粒功能。
- Parameter groups: LED target／range、state／lifecycle
- Complete example call:

```cpp
BlinkBlueSingleLedPattern(led, ledIndex, state, now);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:BlinkBurstSingleLedPattern -->
### `BlinkBurstSingleLedPattern`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void BlinkBurstSingleLedPattern(CRGB* led, int ledIndex, void* state, unsigned long now);`
- General／Component: RGB signal／marker；由 profile namespace 與 sub-pattern 決定逐粒功能。
- Parameter groups: LED target／range、state／lifecycle
- Complete example call:

```cpp
BlinkBurstSingleLedPattern(led, ledIndex, state, now);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:BlinkRedSingleLedPattern -->
### `BlinkRedSingleLedPattern`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void BlinkRedSingleLedPattern(CRGB* led, int ledIndex, void* state, unsigned long now);`
- General／Component: RGB signal／marker；由 profile namespace 與 sub-pattern 決定逐粒功能。
- Parameter groups: LED target／range、state／lifecycle
- Complete example call:

```cpp
BlinkRedSingleLedPattern(led, ledIndex, state, now);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:BlinkTwiceSingleLedPattern -->
### `BlinkTwiceSingleLedPattern`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void BlinkTwiceSingleLedPattern(CRGB* led, int ledIndex, void* state, unsigned long now);`
- General／Component: RGB signal／marker；由 profile namespace 與 sub-pattern 決定逐粒功能。
- Parameter groups: LED target／range、state／lifecycle
- Complete example call:

```cpp
BlinkTwiceSingleLedPattern(led, ledIndex, state, now);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:BoosterFadeSingleLedPattern -->
### `BoosterFadeSingleLedPattern`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void BoosterFadeSingleLedPattern(CRGB* led, int ledIndex, void* state, unsigned long now);`
- General／Component: RGB signal／marker；由 profile namespace 與 sub-pattern 決定逐粒功能。
- Parameter groups: LED target／range、brightness／fade、state／lifecycle
- Complete example call:

```cpp
BoosterFadeSingleLedPattern(led, ledIndex, state, now);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:BreathGreenSingleLedPattern -->
### `BreathGreenSingleLedPattern`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void BreathGreenSingleLedPattern(CRGB* led, int ledIndex, void* state, unsigned long now);`
- General／Component: RGB signal／marker；由 profile namespace 與 sub-pattern 決定逐粒功能。
- Parameter groups: LED target／range、state／lifecycle
- Complete example call:

```cpp
BreathGreenSingleLedPattern(led, ledIndex, state, now);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:ColorSpinner -->
### `ColorSpinner`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void ColorSpinner(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbColorSpinnerParams& params, const RgbColorSpinnerContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
ColorSpinner(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:DestinyWing -->
### `DestinyWing`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void DestinyWing(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbDestinyWingParams& params, const RgbDestinyWingContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
DestinyWing(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:GN_Capacitor_Normal -->
### `GN_Capacitor_Normal`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/storing_energy.h`
- Signature: `void GN_Capacitor_Normal(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGnCapacitorParams& params, const RgbGnCapacitorNormalContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
GN_Capacitor_Normal(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_3.cpp`, `firmware/shared/src/storymode/storyMode_storing_energy.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:GN_Capacitor_TransAM -->
### `GN_Capacitor_TransAM`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/storing_energy.h`
- Signature: `void GN_Capacitor_TransAM(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGnCapacitorParams& params, const RgbGnCapacitorTransAMContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
GN_Capacitor_TransAM(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:GN_Drive_Normal -->
### `GN_Drive_Normal`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/gn.h`
- Signature: `void GN_Drive_Normal(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGnDriveParams& params, const RgbGnDriveContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
GN_Drive_Normal(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_activation.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:GN_Drive_Running -->
### `GN_Drive_Running`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/gn.h`
- Signature: `void GN_Drive_Running(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGnDriveParams& params, const RgbGnDriveRunningContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
GN_Drive_Running(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_motor.cpp`, `firmware/shared/src/storymode/storyMode_trans_am.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:GN_Drive_TransAM -->
### `GN_Drive_TransAM`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/gn.h`
- Signature: `void GN_Drive_TransAM(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGnDriveTransAMParams& params, const RgbGnDriveTransAMContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
GN_Drive_TransAM(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:GN_Shield_Normal -->
### `GN_Shield_Normal`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/gn.h`
- Signature: `void GN_Shield_Normal(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGnShieldParams& params, const RgbGnShieldContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
GN_Shield_Normal(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:GN_Shield_TransAM -->
### `GN_Shield_TransAM`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/gn.h`
- Signature: `void GN_Shield_TransAM(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGnShieldParams& params, const RgbGnShieldContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
GN_Shield_TransAM(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:GN_Sword_Normal -->
### `GN_Sword_Normal`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/gn.h`
- Signature: `void GN_Sword_Normal(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGnSwordNormalParams& params, const RgbGnSwordNormalContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
GN_Sword_Normal(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:GN_Sword_Pulse -->
### `GN_Sword_Pulse`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/gn.h`
- Signature: `void GN_Sword_Pulse(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGnSwordPulseParams& params, const RgbGnSwordPulseContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
GN_Sword_Pulse(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:GN_Sword_Pulse_Color -->
### `GN_Sword_Pulse_Color`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/gn.h`
- Signature: `void GN_Sword_Pulse_Color(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGnSwordPulseColorParams& params, const RgbGnSwordPulseColorContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
GN_Sword_Pulse_Color(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_0_v1.cpp`, `firmware/shared/src/storymode/storyMode_0_v2.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:GN_Sword_TransAM -->
### `GN_Sword_TransAM`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/gn.h`
- Signature: `void GN_Sword_TransAM(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGnSwordTransAMParams& params, const RgbGnSwordTransAMContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
GN_Sword_TransAM(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:GN_Wire_Normal -->
### `GN_Wire_Normal`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/gn.h`
- Signature: `void GN_Wire_Normal(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, uint32_t brightnessRampUpMs, const RgbGnWireNormalContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
GN_Wire_Normal(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, brightnessRampUpMs, context);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_storing_energy.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:GN_Wire_TransAM -->
### `GN_Wire_TransAM`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/gn.h`
- Signature: `void GN_Wire_TransAM(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGnWireTransAMParams& params, const RgbGnWireTransAMContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
GN_Wire_TransAM(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_trans_am.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:GunFirePattern -->
### `GunFirePattern`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/weapon.h`
- Signature: `void GunFirePattern(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGunFirePatternParams& params, RgbGunFirePatternContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
GunFirePattern(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:GundamEyeWakeSingleLedPattern -->
### `GundamEyeWakeSingleLedPattern`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void GundamEyeWakeSingleLedPattern(CRGB* led, int ledIndex, void* state, unsigned long now);`
- General／Component: RGB signal／marker；由 profile namespace 與 sub-pattern 決定逐粒功能。
- Parameter groups: LED target／range、state／lifecycle
- Complete example call:

```cpp
GundamEyeWakeSingleLedPattern(led, ledIndex, state, now);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:InvertedMachineGunSingleLedPattern -->
### `InvertedMachineGunSingleLedPattern`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void InvertedMachineGunSingleLedPattern(CRGB* led, int ledIndex, void* state, unsigned long now);`
- General／Component: RGB signal／marker；由 profile namespace 與 sub-pattern 決定逐粒功能。
- Parameter groups: LED target／range、state／lifecycle
- Complete example call:

```cpp
InvertedMachineGunSingleLedPattern(led, ledIndex, state, now);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:KampferGrenade -->
### `KampferGrenade`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/weapon.h`
- Signature: `void KampferGrenade(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbKampferGrenadeParams& params, const RgbKampferGrenadeContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
KampferGrenade(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:LongTurnOnSingleLedPattern -->
### `LongTurnOnSingleLedPattern`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void LongTurnOnSingleLedPattern(CRGB* led, int ledIndex, void* state, unsigned long now);`
- General／Component: RGB signal／marker；由 profile namespace 與 sub-pattern 決定逐粒功能。
- Parameter groups: LED target／range、state／lifecycle
- Complete example call:

```cpp
LongTurnOnSingleLedPattern(led, ledIndex, state, now);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:MachineGunSingleLedPattern -->
### `MachineGunSingleLedPattern`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void MachineGunSingleLedPattern(CRGB* led, int ledIndex, void* state, unsigned long now);`
- General／Component: RGB signal／marker；由 profile namespace 與 sub-pattern 決定逐粒功能。
- Parameter groups: LED target／range、state／lifecycle
- Complete example call:

```cpp
MachineGunSingleLedPattern(led, ledIndex, state, now);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:Machine_Gun -->
### `Machine_Gun`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/weapon.h`
- Signature: `void Machine_Gun(CRGB* leds, int NUM_LEDS, uint16_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbMachineGunParams& params, const RgbMachineGunContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
Machine_Gun(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:Machine_Gun_RedAstrayLimited -->
### `Machine_Gun_RedAstrayLimited`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/weapon.h`
- Signature: `void Machine_Gun_RedAstrayLimited(CRGB* leds, int NUM_LEDS, uint16_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbMachineGunRedAstrayParams& params, const RgbMachineGunRedAstrayContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
Machine_Gun_RedAstrayLimited(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:Missile_Launcher -->
### `Missile_Launcher`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/weapon.h`
- Signature: `void Missile_Launcher(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbMissileLauncherParams& params, RgbMissileLauncherContext context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
Missile_Launcher(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:Missile_Launcher_F16 -->
### `Missile_Launcher_F16`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/weapon.h`
- Signature: `void Missile_Launcher_F16(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbMissileLauncherF16Params& params, RgbMissileLauncherContext context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
Missile_Launcher_F16(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:Missile_Launcher_breath -->
### `Missile_Launcher_breath`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/weapon.h`
- Signature: `void Missile_Launcher_breath(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbMissileLauncherBreathParams& params, RgbMissileLauncherContext context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
Missile_Launcher_breath(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:OrangeAmbulanceTwiceSingleLedPattern -->
### `OrangeAmbulanceTwiceSingleLedPattern`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void OrangeAmbulanceTwiceSingleLedPattern(CRGB* led, int ledIndex, void* state, unsigned long now);`
- General／Component: RGB signal／marker；由 profile namespace 與 sub-pattern 決定逐粒功能。
- Parameter groups: LED target／range、state／lifecycle
- Complete example call:

```cpp
OrangeAmbulanceTwiceSingleLedPattern(led, ledIndex, state, now);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:RGBBreath -->
### `RGBBreath`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/breath.h`
- Signature: `void RGBBreath(CRGB* leds, int numLeds, int hue, BreathWhiteSwipeInstance* instance);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette
- Complete example call:

```cpp
RGBBreath(leds, numLeds, hue, instance);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:RGBBreathPalette -->
### `RGBBreathPalette`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/breath.h`
- Signature: `void RGBBreathPalette(CRGB* leds, int numLeds, BreathWhiteSwipeInstance* instance, uint8_t* paletteIndex, CRGBPalette16 Palette);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、state／lifecycle
- Complete example call:

```cpp
RGBBreathPalette(leds, numLeds, instance, paletteIndex, Palette);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:RGBIndependentLightning -->
### `RGBIndependentLightning`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/independent_lightning.h`
- Signature: `bool RGBIndependentLightning( CRGB* leds, int numLeds, unsigned long startTime, uint32_t totalDurationMs, CRGB boltColor, const RgbIndependentLightningParams& params, RgbIndependentLightningContext& context, uint8_t combinationIndex = 0xFF);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、timing／speed、state／lifecycle
- Complete example call:

```cpp
RGBIndependentLightning(leds, numLeds, startTime, totalDurationMs, boltColor, params, context, combinationIndex);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:RandomFlashFadeout -->
### `RandomFlashFadeout`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/randomFlash.h`
- Signature: `bool RandomFlashFadeout(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbRandomFlashFadeoutParams& params, const RgbRandomFlashFadeoutContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
RandomFlashFadeout(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:SignalLightEffect -->
### `SignalLightEffect`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void SignalLightEffect(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbSignalLightParams& params, RgbSignalLightContext context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
SignalLightEffect(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:SingleRippleEffect -->
### `SingleRippleEffect`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`
- Signature: `void SingleRippleEffect(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbSingleRippleParams& params, RgbPaletteIndexContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
SingleRippleEffect(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:SingleRippleEffect_V2 -->
### `SingleRippleEffect_V2`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void SingleRippleEffect_V2(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbSingleRippleV2Params& params, const RgbSingleRippleV2Context& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
SingleRippleEffect_V2(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:SolidOnSingleLedPattern -->
### `SolidOnSingleLedPattern`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void SolidOnSingleLedPattern(CRGB* led, int ledIndex, void* state, unsigned long now);`
- General／Component: RGB signal／marker；由 profile namespace 與 sub-pattern 決定逐粒功能。
- Parameter groups: LED target／range、state／lifecycle
- Complete example call:

```cpp
SolidOnSingleLedPattern(led, ledIndex, state, now);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:SpecificColorPattern -->
### `SpecificColorPattern`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void SpecificColorPattern(CRGB* leds, int numLeds, const ColorPattern* registry, uint8_t numPatterns, const uint8_t* ledColorIndex, const CRGB* overrideColors = nullptr, void* const* overrideStates = nullptr);`
- General／Component: RGB signal／marker；由 profile namespace 與 sub-pattern 決定逐粒功能。
- Parameter groups: LED target／range、color／palette、state／lifecycle
- Complete example call:

```cpp
SpecificColorPattern(leds_RGB4, NUM_LEDS_RGB4,
                     storyMode_2_params::specificColor_registry,
                     storyMode_2_params::specificColorPatternCount,
                     storyMode_2_params::slave1_rgb4_specificColorIndex);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_2.cpp`, `firmware/shared/src/storymode/storyMode_3.cpp`, `firmware/shared/src/storymode/storyMode_activation.cpp`, `firmware/shared/src/storymode/storyMode_develop.cpp`, `firmware/shared/src/storymode/storyMode_motor.cpp`, `firmware/shared/src/storymode/storyMode_motor_reset.cpp`, `firmware/shared/src/storymode/storyMode_parameter.cpp`, `firmware/shared/src/storymode/storyMode_plasma.cpp`, `firmware/shared/src/storymode/storyMode_signals.cpp`, `firmware/shared/src/storymode/storyMode_storing_energy.cpp`, `firmware/shared/src/storymode/storyMode_trans_am.cpp`, `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:VentEffect -->
### `VentEffect`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/vent.h`
- Signature: `void VentEffect(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbVentEffectParams& params, RgbVentEffectContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
VentEffect(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_2.cpp`, `firmware/shared/src/storymode/storyMode_3.cpp`, `firmware/shared/src/storymode/storyMode_activation.cpp`, `firmware/shared/src/storymode/storyMode_motor.cpp`, `firmware/shared/src/storymode/storyMode_storing_energy.cpp`, `firmware/shared/src/storymode/storyMode_trans_am.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:WarmWhitePalette -->
### `WarmWhitePalette`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `bool WarmWhitePalette(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbWarmWhitePaletteParams& params, const RgbWarmWhitePaletteContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
WarmWhitePalette(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:ambulancePulseSingleLedPattern -->
### `ambulancePulseSingleLedPattern`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void ambulancePulseSingleLedPattern(CRGB* led, int /*ledIndex*/, void* state, unsigned long now);`
- General／Component: RGB signal／marker；由 profile namespace 與 sub-pattern 決定逐粒功能。
- Parameter groups: LED target／range、state／lifecycle
- Complete example call:

```cpp
ambulancePulseSingleLedPattern(led, ledIndex, state, now);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:applyBoosterEffect -->
### `applyBoosterEffect`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/common.h`
- Signature: `void applyBoosterEffect(CRGB* leds, int NUM_LEDS, CRGB bg, CRGB boosterColor, uint8_t boosterBrightness, uint8_t ledBrightness);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade
- Complete example call:

```cpp
applyBoosterEffect(leds, NUM_LEDS, bg, boosterColor, boosterBrightness, ledBrightness);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:applyRgbLibOutput -->
### `applyRgbLibOutput`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/common.h`
- Signature: `void applyRgbLibOutput(CRGB* leds, int numLeds, uint8_t brightnessMin, uint8_t brightnessMax, WLED_DirectionMode directionMode);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、brightness／fade、geometry／direction
- Complete example call:

```cpp
applyRgbLibOutput(leds, numLeds, brightnessMin, brightnessMax, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:applyTurbinePattern -->
### `applyTurbinePattern`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/turbine.h`
- Signature: `void applyTurbinePattern(CRGB* leds, int numLEDs, TurbineInstance_v2* instance);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range
- Complete example call:

```cpp
applyTurbinePattern(leds, numLEDs, instance);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:atomicBreath -->
### `atomicBreath`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/weapon.h`
- Signature: `void atomicBreath(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbAtomicBreathParams& params, const RgbAtomicBreathContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
atomicBreath(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:axe -->
### `axe`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/weapon.h`
- Signature: `void axe(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbAxeParams& params, const RgbAxeContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
axe(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:calculateBoosterBrightness -->
### `calculateBoosterBrightness`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/common.h`
- Signature: `uint8_t calculateBoosterBrightness(BoosterCycleState* cycleState, unsigned long boosterElapsed);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: brightness／fade、state／lifecycle
- Complete example call:

```cpp
calculateBoosterBrightness(cycleState, boosterElapsed);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:calculateBoosterFadeBrightness -->
### `calculateBoosterFadeBrightness`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/common.h`
- Signature: `uint8_t calculateBoosterFadeBrightness(unsigned long elapsed, unsigned long fadeInDuration, unsigned long fadeOutDuration, uint8_t finalBrightness);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: brightness／fade、timing／speed
- Complete example call:

```cpp
calculateBoosterFadeBrightness(elapsed, fadeInDuration, fadeOutDuration, finalBrightness);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:chProgressiveFlash -->
### `chProgressiveFlash`

- Library／Source: PCA channel patterns — `firmware/shared/include/patterns/patterns_channel.h`
- Signature: `void chProgressiveFlash(uint16_t channelId, uint16_t high, uint16_t low, int totalDuration, int stopSecond);`
- General／Component: PCA 散氣、內構、推進或漸進閃；功能需要時可以保持 OFF。
- Parameter groups: channel target、brightness／fade、timing／speed
- Complete example call:

```cpp
chProgressiveFlash(pcaLed[PWM0 * 16 + PWM_CHANNEL_3],
                   chBrightnessFlashHigh, chBrightnessFlashLow,
                   totalDuration, stopSecond);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_2.cpp`, `firmware/shared/src/storymode/storyMode_3.cpp`, `firmware/shared/src/storymode/storyMode_activation.cpp`, `firmware/shared/src/storymode/storyMode_awakening_3.cpp`, `firmware/shared/src/storymode/storyMode_idle.cpp`, `firmware/shared/src/storymode/storyMode_motor.cpp`, `firmware/shared/src/storymode/storyMode_plasma.cpp`, `firmware/shared/src/storymode/storyMode_storing_energy.cpp`, `firmware/shared/src/storymode/storyMode_trans_am.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:chValcanGun -->
### `chValcanGun`

- Library／Source: PCA channel library — `firmware/shared/include/lib/lib_channel.h`
- Signature: `void chValcanGun(uint16_t channelId, uint16_t maxBrightness, uint16_t minBrightness, int speed, uint8_t& flashCount, bool& isOn, unsigned long& lastUpdate, int pauseTime, int flashTime, int fadeOutTimeMs = 0);`
- General／Component: PCA 火神炮／Vulcan；只有部件功能明確是武器時使用。
- Parameter groups: channel target、brightness／fade、timing／speed、state／lifecycle
- Complete example call:

```cpp
chValcanGun(pcaLed[PWM0 * 16 + i], chBeaconFastFlashBrightness,
            chBeaconFlashMin, chBeaconFastFlashOn2, flashCount_pwm0[i],
            isOnArr_pwm0[i], lastUpdateArr_pwm0[i], chGunBurstRestMs,
            chGunBurstCount, chGunFadeOutMs);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_2.cpp`, `firmware/shared/src/storymode/storyMode_activation.cpp`, `firmware/shared/src/storymode/storyMode_awakening_3.cpp`, `firmware/shared/src/storymode/storyMode_demo.cpp`, `firmware/shared/src/storymode/storyMode_motor.cpp`, `firmware/shared/src/storymode/storyMode_motor_reset.cpp`, `firmware/shared/src/storymode/storyMode_storing_energy.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:comet -->
### `comet`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`
- Signature: `bool comet(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbCometParams& params, RgbCometContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
comet(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:cometIronMan -->
### `cometIronMan`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void cometIronMan(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbCometIronManParams& params, RgbCometIronManContext context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
cometIronMan(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:cometReverse -->
### `cometReverse`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `bool cometReverse(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbCometReverseParams& params, RgbCometReverseContext context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
cometReverse(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:cometReverse2 -->
### `cometReverse2`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `bool cometReverse2(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbCometReverseParams& params, RgbCometReverseContext context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
cometReverse2(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:cometReverse4a -->
### `cometReverse4a`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `bool cometReverse4a(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbCometReverse4aParams& params, RgbCometReverse4aContext context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
cometReverse4a(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:computeOneTwinkle -->
### `computeOneTwinkle`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `CRGB computeOneTwinkle(uint32_t ms, uint8_t salt, CRGBPalette16 palette, uint8_t twinkleSpeed, uint8_t twinkleDensity);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、timing／speed
- Complete example call:

```cpp
computeOneTwinkle(ms, salt, palette, twinkleSpeed, twinkleDensity);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:confetti -->
### `confetti`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/signal.h`
- Signature: `void confetti(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbConfettiParams& params, RgbNoContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
confetti(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:createDefaultWledDnaInstance -->
### `createDefaultWledDnaInstance`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/2D_Matrix.h`
- Signature: `WLED_MatrixParams createDefaultWledDnaInstance();`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range
- Complete example call:

```cpp
createDefaultWledDnaInstance();
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:createDefaultWledDnaSpiralInstance -->
### `createDefaultWledDnaSpiralInstance`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/2D_Matrix.h`
- Signature: `WLED_MatrixParams createDefaultWledDnaSpiralInstance();`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range
- Complete example call:

```cpp
createDefaultWledDnaSpiralInstance();
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:createDefaultWledHiphoticInstance -->
### `createDefaultWledHiphoticInstance`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/2D_Matrix.h`
- Signature: `WLED_MatrixParams createDefaultWledHiphoticInstance();`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range
- Complete example call:

```cpp
createDefaultWledHiphoticInstance();
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:createDefaultWledLissajousInstance -->
### `createDefaultWledLissajousInstance`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/2D_Matrix.h`
- Signature: `WLED_MatrixParams createDefaultWledLissajousInstance();`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range
- Complete example call:

```cpp
createDefaultWledLissajousInstance();
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:createDefaultWledMatrixInstance -->
### `createDefaultWledMatrixInstance`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/2D_Matrix.h`
- Signature: `WLED_MatrixParams createDefaultWledMatrixInstance();`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range
- Complete example call:

```cpp
createDefaultWledMatrixInstance();
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:createDefaultWledOctopusInstance -->
### `createDefaultWledOctopusInstance`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/2D_Matrix.h`
- Signature: `WLED_MatrixParams createDefaultWledOctopusInstance();`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range
- Complete example call:

```cpp
createDefaultWledOctopusInstance();
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:createDefaultWledPsChaseInstance -->
### `createDefaultWledPsChaseInstance`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/2D_Matrix.h`
- Signature: `WLED_MatrixParams createDefaultWledPsChaseInstance();`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range
- Complete example call:

```cpp
createDefaultWledPsChaseInstance();
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:createDefaultWledPsGeqNovaInstance -->
### `createDefaultWledPsGeqNovaInstance`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/2D_Matrix.h`
- Signature: `WLED_MatrixParams createDefaultWledPsGeqNovaInstance();`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range
- Complete example call:

```cpp
createDefaultWledPsGeqNovaInstance();
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:createDefaultWledPsGhostRiderInstance -->
### `createDefaultWledPsGhostRiderInstance`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/2D_Matrix.h`
- Signature: `WLED_MatrixParams createDefaultWledPsGhostRiderInstance();`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range
- Complete example call:

```cpp
createDefaultWledPsGhostRiderInstance();
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:createDefaultWledPsVortexInstance -->
### `createDefaultWledPsVortexInstance`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/2D_Matrix.h`
- Signature: `WLED_MatrixParams createDefaultWledPsVortexInstance();`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range
- Complete example call:

```cpp
createDefaultWledPsVortexInstance();
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:createDefaultWledRotozoomerInstance -->
### `createDefaultWledRotozoomerInstance`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/2D_Matrix.h`
- Signature: `WLED_MatrixParams createDefaultWledRotozoomerInstance();`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range
- Complete example call:

```cpp
createDefaultWledRotozoomerInstance();
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:createDefaultWledTartanInstance -->
### `createDefaultWledTartanInstance`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/2D_Matrix.h`
- Signature: `WLED_MatrixParams createDefaultWledTartanInstance();`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range
- Complete example call:

```cpp
createDefaultWledTartanInstance();
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:createDefaultWledWaterfallInstance -->
### `createDefaultWledWaterfallInstance`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/2D_Matrix.h`
- Signature: `WLED_MatrixParams createDefaultWledWaterfallInstance();`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range
- Complete example call:

```cpp
createDefaultWledWaterfallInstance();
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:discreteBreathWave -->
### `discreteBreathWave`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/breath.h`
- Signature: `void discreteBreathWave(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbDiscreteBreathWaveParams& params, RgbDiscreteBreathWaveContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
discreteBreathWave(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:drawSwipeEffect -->
### `drawSwipeEffect`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void drawSwipeEffect(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbDrawSwipeEffectParams& params, const RgbDrawSwipeEffectContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
drawSwipeEffect(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:drawTwinkles -->
### `drawTwinkles`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void drawTwinkles(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbTwinklesParams& params, RgbNoContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
drawTwinkles(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:dualSwipeWithTimeModulation -->
### `dualSwipeWithTimeModulation`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void dualSwipeWithTimeModulation(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbDualSwipeTimeModulationParams& params, const RgbDualSwipeTimeModulationContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
dualSwipeWithTimeModulation(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:dynamicPalette -->
### `dynamicPalette`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`
- Signature: `void dynamicPalette(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbDynamicPaletteParams& params, RgbPaletteIndexContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
dynamicPalette(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:dynamicRainbow -->
### `dynamicRainbow`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`
- Signature: `void dynamicRainbow(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, RgbHueContext& context, uint8_t deltahue);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
dynamicRainbow(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, context, deltahue);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:fadeInOut -->
### `fadeInOut`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/fade_in_out.h`
- Signature: `bool fadeInOut(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbFadeInOutParams& params, RgbFadeInOutContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
fadeInOut(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:fadeInOutPalette -->
### `fadeInOutPalette`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/fade_in_out.h`
- Signature: `bool fadeInOutPalette(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbFadeInOutParams& params, RgbFadeInOutContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
fadeInOutPalette(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:fadeInOutPartial -->
### `fadeInOutPartial`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/fade_in_out.h`
- Signature: `bool fadeInOutPartial(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbFadeInOutPartialParams& params, RgbFadeInOutContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
fadeInOutPartial(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:fire -->
### `fire`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`
- Signature: `void fire(CRGB* leds, int NUM_LEDS, uint8_t* colorIndex);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、state／lifecycle
- Complete example call:

```cpp
fire(leds, NUM_LEDS, colorIndex);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:flame -->
### `flame`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`
- Signature: `void flame(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbFlameParams& params, RgbHeatContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
flame(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:footplate -->
### `footplate`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/footplate.h`
- Signature: `void footplate(CRGB* leds, int NUM_LEDS, FootplateInstance* instance);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range
- Complete example call:

```cpp
footplate(leds, NUM_LEDS, instance);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:footplatev2 -->
### `footplatev2`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/footplate.h`
- Signature: `void footplatev2(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbFootplateV2Params& params, const RgbFootplateV2Context& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
footplatev2(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_2.cpp`, `firmware/shared/src/storymode/storyMode_3.cpp`, `firmware/shared/src/storymode/storyMode_activation.cpp`, `firmware/shared/src/storymode/storyMode_awakening_3.cpp`, `firmware/shared/src/storymode/storyMode_motor.cpp`, `firmware/shared/src/storymode/storyMode_plasma.cpp`, `firmware/shared/src/storymode/storyMode_signals.cpp`, `firmware/shared/src/storymode/storyMode_storing_energy.cpp`, `firmware/shared/src/storymode/storyMode_trans_am.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:getAverageBrightness -->
### `getAverageBrightness`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/common.h`
- Signature: `uint8_t getAverageBrightness(CRGB* leds, int numLeds);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、brightness／fade
- Complete example call:

```cpp
getAverageBrightness(leds, numLeds);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:gradientDynamicPalette -->
### `gradientDynamicPalette`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`
- Signature: `void gradientDynamicPalette(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGradientDynamicPaletteParams& params, RgbPaletteIndexContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
gradientDynamicPalette(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_dev.cpp`, `firmware/shared/src/storymode/storyMode_parameter.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:gradientDynamicPalette_V2 -->
### `gradientDynamicPalette_V2`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`
- Signature: `void gradientDynamicPalette_V2(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGradientDynamicPaletteV2Params& params, RgbPaletteIndexContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
gradientDynamicPalette_V2(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:gradientDynamicRainbow -->
### `gradientDynamicRainbow`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`
- Signature: `void gradientDynamicRainbow(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, RgbHueContext& context, uint8_t deltahue);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
gradientDynamicRainbow(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, context, deltahue);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:gradientRainbowSwipe -->
### `gradientRainbowSwipe`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`
- Signature: `void gradientRainbowSwipe(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGradientRainbowSwipeParams& params, const RgbGradientRainbowSwipeContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
gradientRainbowSwipe(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:gradientRainbowThunder -->
### `gradientRainbowThunder`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`
- Signature: `void gradientRainbowThunder(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGradientRainbowThunderParams& params, RgbGradientRainbowThunderContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
gradientRainbowThunder(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:gradientVentPalette -->
### `gradientVentPalette`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/vent.h`
- Signature: `void gradientVentPalette(CRGB* leds, int NUM_LEDS, int speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGradientVentPaletteParams& params, const RgbGradientVentPaletteContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
gradientVentPalette(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_2.cpp`, `firmware/shared/src/storymode/storyMode_3.cpp`, `firmware/shared/src/storymode/storyMode_activation.cpp`, `firmware/shared/src/storymode/storyMode_awakening_3.cpp`, `firmware/shared/src/storymode/storyMode_signals.cpp`, `firmware/shared/src/storymode/storyMode_storing_energy.cpp`, `firmware/shared/src/storymode/storyMode_trans_am.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:gradualFill -->
### `gradualFill`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/fade_in_out.h`
- Signature: `bool gradualFill(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGradualFillParams& params, RgbGradualFillContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
gradualFill(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:gradualFillInOut -->
### `gradualFillInOut`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/fade_in_out.h`; patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `bool gradualFillInOut(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGradualFillInOutParams& params, RgbGradualFillInOutContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
gradualFillInOut(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:gradualFillInOutPalette -->
### `gradualFillInOutPalette`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/fade_in_out.h`; patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `bool gradualFillInOutPalette(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGradualFillInOutParams& params, RgbGradualFillInOutContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
gradualFillInOutPalette(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:gunStoringEnergy -->
### `gunStoringEnergy`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/storing_energy.h`
- Signature: `bool gunStoringEnergy(CRGB* leds, int NUM_LEDS, int speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGunStoringEnergyParams& params, const RgbGunStoringEnergyContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
gunStoringEnergy(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_motor.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:gundamEyeWake -->
### `gundamEyeWake`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/gn.h`
- Signature: `void gundamEyeWake(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbGundamEyeWakeParams& params, const RgbGundamEyeWakeContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
gundamEyeWake(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:gunfire -->
### `gunfire`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/weapon.h`
- Signature: `bool gunfire(CRGB* leds, int NUM_LEDS, GunfireInstance* instance);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range
- Complete example call:

```cpp
gunfire(leds, NUM_LEDS, instance);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:hsv2rgb -->
### `hsv2rgb`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `CRGB hsv2rgb(uint8_t h, uint8_t s, uint8_t v);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: control／configuration
- Complete example call:

```cpp
hsv2rgb(h, s, v);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:initMissileLauncherState -->
### `initMissileLauncherState`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/weapon.h`
- Signature: `void initMissileLauncherState(MissileLauncherStateInternal* state, int numLeds, CRGB color, CRGB rapidSwipeColor, CRGB burstColor, unsigned long lightingInterval, unsigned long breathingDuration, unsigned long rapidSwipeDuration, unsigned long blinkInterval, unsigned long burstMoveInterval, unsigned long burstShakeDuration, unsigned long burstFadeDuration, unsigned long waitDuration, uint8_t shakeIntensity, unsigned long now);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、state／lifecycle
- Complete example call:

```cpp
initMissileLauncherState(state, numLeds, color, rapidSwipeColor, burstColor, lightingInterval, breathingDuration, rapidSwipeDuration, blinkInterval, burstMoveInterval, burstShakeDuration, burstFadeDuration, waitDuration, shakeIntensity, now);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:initZoidsTailState -->
### `initZoidsTailState`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/weapon.h`
- Signature: `void initZoidsTailState(ZoidsTailStateInternal* state, uint8_t numStrips, const int* numLedsPerStrip, const CRGB* stripColors, const CRGB* cometColors, unsigned long lightingInterval, uint16_t cometSpeed, uint8_t cometTailLength, uint8_t cometHeadLength, unsigned long waitDuration, unsigned long now);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
initZoidsTailState(state, numStrips, numLedsPerStrip, stripColors, cometColors, lightingInterval, cometSpeed, cometTailLength, cometHeadLength, waitDuration, now);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:juggle -->
### `juggle`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`; patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void juggle(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbJuggleParams& params, RgbNoContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
juggle(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:meteorShower -->
### `meteorShower`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void meteorShower(CRGB* leds, int NUM_LEDS, byte ledsX[][3], uint8_t* hue, int& idex, int& colorTIP, int& loopCount, int& timeframe);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、timing／speed、state／lifecycle
- Complete example call:

```cpp
meteorShower(leds, NUM_LEDS, ledsX, hue, idex, colorTIP, loopCount, timeframe);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_android -->
### `mode_wled_android`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_android(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_android(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_aurora -->
### `mode_wled_aurora`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_aurora(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_aurora(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_blends -->
### `mode_wled_blends`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_blends(CRGB* leds, int NUM_LEDS, WLED_BlendsParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_blends(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_blurz -->
### `mode_wled_blurz`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_blurz(CRGB* leds, int NUM_LEDS, WLED_BlurzParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_blurz(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_bouncing_balls -->
### `mode_wled_bouncing_balls`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_bouncing_balls(CRGB* leds, int NUM_LEDS, WLED_BouncingBallsParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_bouncing_balls(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_bpm -->
### `mode_wled_bpm`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_bpm(CRGB* leds, int NUM_LEDS, WLED_BPMParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_bpm(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_candle_multi -->
### `mode_wled_candle_multi`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_candle_multi(CRGB* leds, int NUM_LEDS, WLED_CandleMultiParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_candle_multi(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_chase -->
### `mode_wled_chase`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_chase(CRGB* leds, int NUM_LEDS, WLED_ChaseParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_chase(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_chase_enhanced -->
### `mode_wled_chase_enhanced`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_chase_enhanced(CRGB* leds, int NUM_LEDS, WLED_ChaseEnhancedParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_chase_enhanced(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_chase_flash_rnd -->
### `mode_wled_chase_flash_rnd`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_chase_flash_rnd(CRGB* leds, int NUM_LEDS, WLED_ChaseFlashRndParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_chase_flash_rnd(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_chase_rainbow -->
### `mode_wled_chase_rainbow`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_chase_rainbow(CRGB* leds, int NUM_LEDS, WLED_ChaseRainbowParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_chase_rainbow(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_chunchun -->
### `mode_wled_chunchun`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_chunchun(CRGB* leds, int NUM_LEDS, WLED_ChunchunParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_chunchun(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_colortwinkles -->
### `mode_wled_colortwinkles`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_colortwinkles(CRGB* leds, int NUM_LEDS, WLED_ColortwinklesParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_colortwinkles(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_colorwaves -->
### `mode_wled_colorwaves`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_colorwaves(CRGB* leds, int NUM_LEDS, WLED_ColorwavesParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_colorwaves(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_comet -->
### `mode_wled_comet`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_comet(CRGB* leds, int NUM_LEDS, int comet1Length, int comet2Length, WLED_CometParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_comet(leds, NUM_LEDS, comet1Length, comet2Length, params, palette, brightness, speed, directionMode);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_dancing_shadows -->
### `mode_wled_dancing_shadows`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_dancing_shadows(CRGB* leds, int NUM_LEDS, WLED_DancingShadowsParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_dancing_shadows(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_dissolve -->
### `mode_wled_dissolve`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_dissolve(CRGB* leds, int NUM_LEDS, WLED_DissolveParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_dissolve(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_djlight -->
### `mode_wled_djlight`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_djlight(CRGB* leds, int NUM_LEDS, WLED_DJLightParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_djlight(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_dynamic_smooth -->
### `mode_wled_dynamic_smooth`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_dynamic_smooth(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_dynamic_smooth(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_fire_2012 -->
### `mode_wled_fire_2012`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_fire_2012(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_fire_2012(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_fireworks -->
### `mode_wled_fireworks`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_fireworks(CRGB* leds, int NUM_LEDS, WLED_FireworksParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_fireworks(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_fireworks_1d -->
### `mode_wled_fireworks_1d`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_fireworks_1d(CRGB* leds, int NUM_LEDS, WLED_Fireworks1DParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_fireworks_1d(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_fireworks_starburst -->
### `mode_wled_fireworks_starburst`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_fireworks_starburst(CRGB* leds, int NUM_LEDS, WLED_FireworksStarburstParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_fireworks_starburst(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_flow -->
### `mode_wled_flow`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_flow(CRGB* leds, int NUM_LEDS, WLED_FlowParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_flow(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_flow_stripe -->
### `mode_wled_flow_stripe`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_flow_stripe(CRGB* leds, int NUM_LEDS, WLED_FlowStripeParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_flow_stripe(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_freqmatrix -->
### `mode_wled_freqmatrix`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_freqmatrix(CRGB* leds, int NUM_LEDS, WLED_FreqmatrixParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_freqmatrix(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_freqpixels -->
### `mode_wled_freqpixels`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_freqpixels(CRGB* leds, int NUM_LEDS, WLED_FreqpixelsParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_freqpixels(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_freqwave -->
### `mode_wled_freqwave`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_freqwave(CRGB* leds, int NUM_LEDS, WLED_FreqwaveParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_freqwave(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_glitter -->
### `mode_wled_glitter`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_glitter(CRGB* leds, int NUM_LEDS, WLED_GlitterParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_glitter(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_gradient -->
### `mode_wled_gradient`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_gradient(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_gradient(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_gravcentric -->
### `mode_wled_gravcentric`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_gravcentric(CRGB* leds, int NUM_LEDS, WLED_GravcentricParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_gravcentric(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_juggles -->
### `mode_wled_juggles`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_juggles(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_juggles(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_lake -->
### `mode_wled_lake`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_lake(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_lake(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_lighthouse -->
### `mode_wled_lighthouse`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_lighthouse(CRGB* leds, int NUM_LEDS, WLED_LighthouseParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_lighthouse(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_lightning -->
### `mode_wled_lightning`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_lightning(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_lightning(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_matripix -->
### `mode_wled_matripix`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_matripix(CRGB* leds, int NUM_LEDS, WLED_MatripixParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_matripix(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_metaballs -->
### `mode_wled_metaballs`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_metaballs(CRGB* leds, int NUM_LEDS, WLED_MetaballsParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_metaballs(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_meteor -->
### `mode_wled_meteor`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_meteor(CRGB* leds, int NUM_LEDS, WLED_MeteorParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_meteor(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_midnoise -->
### `mode_wled_midnoise`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_midnoise(CRGB* leds, int NUM_LEDS, WLED_MidnoiseParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_midnoise(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_noise1 -->
### `mode_wled_noise1`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_noise1(CRGB* leds, int NUM_LEDS, WLED_Noise1Params* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_noise1(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_noise2 -->
### `mode_wled_noise2`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_noise2(CRGB* leds, int NUM_LEDS, WLED_Noise2Params* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_noise2(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_noise3 -->
### `mode_wled_noise3`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_noise3(CRGB* leds, int NUM_LEDS, WLED_Noise163Params* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_noise3(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_noisemeter -->
### `mode_wled_noisemeter`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_noisemeter(CRGB* leds, int NUM_LEDS, WLED_NoisemeterParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_noisemeter(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_oscillate -->
### `mode_wled_oscillate`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_oscillate(CRGB* leds, int NUM_LEDS, WLED_OscillateParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_oscillate(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_pacifica -->
### `mode_wled_pacifica`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_pacifica(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_pacifica(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_phased -->
### `mode_wled_phased`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_phased(CRGB* leds, int NUM_LEDS, WLED_PhasedParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
mode_wled_phased(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_phased_noise -->
### `mode_wled_phased_noise`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_phased_noise(CRGB* leds, int NUM_LEDS, WLED_PhasedParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
mode_wled_phased_noise(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_plasma -->
### `mode_wled_plasma`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_plasma(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_plasma(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_pride_2015 -->
### `mode_wled_pride_2015`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_pride_2015(CRGB* leds, int NUM_LEDS, WLED_Pride2015Params* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_pride_2015(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_ps_springy -->
### `mode_wled_ps_springy`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_ps_springy(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_ps_springy(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_railway -->
### `mode_wled_railway`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_railway(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_railway(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_rain -->
### `mode_wled_rain`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_rain(CRGB* leds, int NUM_LEDS, WLED_RainParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_rain(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_running -->
### `mode_wled_running`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_running(CRGB* leds, int NUM_LEDS, WLED_RunningParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_running(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_running_dual -->
### `mode_wled_running_dual`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_running_dual(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_running_dual(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_saw -->
### `mode_wled_saw`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_saw(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_saw(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_scanner -->
### `mode_wled_scanner`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_scanner(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_scanner(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_scanner_dual -->
### `mode_wled_scanner_dual`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_scanner_dual(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_scanner_dual(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_shimmer -->
### `mode_wled_shimmer`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_shimmer(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_shimmer(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_sinelon -->
### `mode_wled_sinelon`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_sinelon(CRGB* leds, int NUM_LEDS, WLED_SinelonParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_sinelon(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_sinelon_dual -->
### `mode_wled_sinelon_dual`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_sinelon_dual(CRGB* leds, int NUM_LEDS, WLED_SinelonParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_sinelon_dual(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_stream -->
### `mode_wled_stream`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_stream(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_stream(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_strobe_mega -->
### `mode_wled_strobe_mega`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_strobe_mega(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_strobe_mega(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_sunrise -->
### `mode_wled_sunrise`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_sunrise(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_sunrise(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_tetrix -->
### `mode_wled_tetrix`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_tetrix(CRGB* leds, int NUM_LEDS, WLED_TetrixParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_tetrix(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_theater -->
### `mode_wled_theater`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_theater(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_theater(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_twinklefox -->
### `mode_wled_twinklefox`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_twinklefox(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_twinklefox(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:mode_wled_wipe -->
### `mode_wled_wipe`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `bool mode_wled_wipe(CRGB* leds, int NUM_LEDS, WLED_ExtraParams* params, const CRGBPalette16* palette = nullptr, uint8_t brightness = 255, int speed = -1, WLED_DirectionMode directionMode = WLED_DIR_FORWARD);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
mode_wled_wipe(leds, NUM_LEDS, params, palette, brightness, speed, directionMode);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:navigationLight2 -->
### `navigationLight2`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void navigationLight2(CRGB* led, int /*ledIndex*/, void* state, unsigned long now);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、state／lifecycle
- Complete example call:

```cpp
navigationLight2(led, ledIndex, state, now);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:paletteFlow -->
### `paletteFlow`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`; patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void paletteFlow(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbPaletteFlowParams& params, RgbPaletteFlowContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
paletteFlow(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:paletteLightdim -->
### `paletteLightdim`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `bool paletteLightdim(CRGB* leds, int NUM_LEDS, WarmWhiteParams* instance);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette
- Complete example call:

```cpp
paletteLightdim(leds, NUM_LEDS, instance);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:paletteWave -->
### `paletteWave`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `bool paletteWave(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbPaletteWaveParams& params, const RgbPaletteWaveContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
paletteWave(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:paletteWave_80Percent_SpecialWave -->
### `paletteWave_80Percent_SpecialWave`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/storing_energy.h`
- Signature: `bool paletteWave_80Percent_SpecialWave(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbPaletteWaveSpecialParams& params, const RgbPaletteWaveSpecialContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
paletteWave_80Percent_SpecialWave(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_storing_energy.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:paletteWave_StoringEnergy -->
### `paletteWave_StoringEnergy`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/storing_energy.h`
- Signature: `bool paletteWave_StoringEnergy(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbPaletteWaveStoringParams& params, const RgbPaletteWaveStoringContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
paletteWave_StoringEnergy(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:paletteWave_V2 -->
### `paletteWave_V2`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `bool paletteWave_V2(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbPaletteWaveParams& params, const RgbPaletteWaveContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
paletteWave_V2(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:plasmaCombinationOrder -->
### `plasmaCombinationOrder`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/independent_lightning.h`
- Signature: `void plasmaCombinationOrder( uint32_t loopIndex, uint8_t order[PLASMA_COMBINATION_COUNT]);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: state／lifecycle
- Complete example call:

```cpp
plasmaCombinationOrder(loopIndex, PLASMA_COMBINATION_COUNT);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:plasmaCombinationStrikeMask -->
### `plasmaCombinationStrikeMask`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/independent_lightning.h`
- Signature: `uint8_t plasmaCombinationStrikeMask(uint32_t loopIndex, uint8_t sequenceIndex);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: state／lifecycle
- Complete example call:

```cpp
plasmaCombinationStrikeMask(loopIndex, sequenceIndex);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:plasmaVariationForBlock -->
### `plasmaVariationForBlock`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/independent_lightning.h`
- Signature: `uint8_t plasmaVariationForBlock(uint32_t seed, uint8_t blockIndex);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: state／lifecycle
- Complete example call:

```cpp
plasmaVariationForBlock(seed, blockIndex);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_plasma.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:plasmaVariationOrder -->
### `plasmaVariationOrder`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/independent_lightning.h`
- Signature: `void plasmaVariationOrder( uint32_t seed, uint8_t order[PLASMA_VARIATION_COUNT]);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: state／lifecycle
- Complete example call:

```cpp
plasmaVariationOrder(seed, PLASMA_VARIATION_COUNT);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:plasmaVariationStrikeMask -->
### `plasmaVariationStrikeMask`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/independent_lightning.h`
- Signature: `uint8_t plasmaVariationStrikeMask(uint8_t variationIndex, uint32_t cycleIndex, uint8_t strikeIndex);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: state／lifecycle
- Complete example call:

```cpp
plasmaVariationStrikeMask(variationIndex, cycleIndex, strikeIndex);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:platform -->
### `platform`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void platform(CRGB** ledGroups, const int* numLeds, int numPlatforms, PlatformInstance* instance);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range
- Complete example call:

```cpp
platform(ledGroups, numLeds, numPlatforms, instance);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:rainbow_breath -->
### `rainbow_breath`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/breath.h`
- Signature: `bool rainbow_breath(CRGB* leds, int NUM_LEDS, uint8_t* colorIndex, CRGBPalette16 palette, uint8_t* patternIndex, int increments, unsigned long duration, int speed, unsigned long* lastUpdate, uint16_t speedDelay, RainbowBreathInstance* instance);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、timing／speed、state／lifecycle
- Complete example call:

```cpp
rainbow_breath(leds, NUM_LEDS, colorIndex, palette, patternIndex, increments, duration, speed, lastUpdate, speedDelay, instance);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:randomBreath -->
### `randomBreath`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/breath.h`
- Signature: `bool randomBreath(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbRandomBreathParams& params, RgbRandomBreathContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
randomBreath(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:randomColorFill -->
### `randomColorFill`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`; patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void randomColorFill(CRGB* leds, int NUM_LEDS, uint16_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbRandomColorFillParams& params, RgbRandomColorFillContext& context);` / `void randomColorFill(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbRandomColorFillParams& params, RgbRandomColorFillContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
randomColorFill(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:randomFillAllMultiStage -->
### `randomFillAllMultiStage`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/vent.h`
- Signature: `bool randomFillAllMultiStage(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbRandomFillAllMultiStageParams& params, RgbRandomFillAllMultiStageContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
randomFillAllMultiStage(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:randomFillAll_V2 -->
### `randomFillAll_V2`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/vent.h`
- Signature: `bool randomFillAll_V2(CRGB* leds, int NUM_LEDS, int speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbRandomFillAllParams& params, RgbRandomFillAllContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
randomFillAll_V2(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_2.cpp`, `firmware/shared/src/storymode/storyMode_3.cpp`, `firmware/shared/src/storymode/storyMode_activation.cpp`, `firmware/shared/src/storymode/storyMode_awakening_3.cpp`, `firmware/shared/src/storymode/storyMode_motor.cpp`, `firmware/shared/src/storymode/storyMode_signals.cpp`, `firmware/shared/src/storymode/storyMode_storing_energy.cpp`, `firmware/shared/src/storymode/storyMode_trans_am.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:randomFlashFixedCount_multiple -->
### `randomFlashFixedCount_multiple`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/randomFlash.h`
- Signature: `void randomFlashFixedCount_multiple(CRGB* leds[], const int ledCounts[], uint8_t stripCount, int speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbRandomFlashFixedCountParams& params, const RgbRandomFlashFixedCountContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
randomFlashFixedCount_multiple(leds, ledCounts, stripCount, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_0_v1.cpp`, `firmware/shared/src/storymode/storyMode_0_v2.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:randomFlashWithGap_multiple -->
### `randomFlashWithGap_multiple`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/randomFlash.h`
- Signature: `void randomFlashWithGap_multiple(CRGB* leds, int NUM_LEDS, int speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbRandomFlashWithGapParams& params, const RgbRandomFlashWithGapContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
randomFlashWithGap_multiple(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_0_v1.cpp`, `firmware/shared/src/storymode/storyMode_0_v2.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:randomFlash_multiple -->
### `randomFlash_multiple`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/randomFlash.h`
- Signature: `void randomFlash_multiple(CRGB* leds, int NUM_LEDS, int speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbRandomFlashParams& params, RgbRandomFlashContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
randomFlash_multiple(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:randomFlash_single -->
### `randomFlash_single`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/randomFlash.h`
- Signature: `void randomFlash_single(CRGB* leds, int NUM_LEDS, int speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbRandomFlashParams& params, RgbRandomFlashContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
randomFlash_single(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:randomLightUp -->
### `randomLightUp`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`
- Signature: `void randomLightUp(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbRandomLightUpParams& params, const RgbRandomLightUpContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
randomLightUp(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_0_v1.cpp`, `firmware/shared/src/storymode/storyMode_0_v2.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:renderRhythmicEffect -->
### `renderRhythmicEffect`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/rhythmic.h`
- Signature: `void renderRhythmicEffect(RgbRhythmicEffectKind kind, CRGB* leds, int numLeds, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbRhythmicEffectParams& params, RgbRhythmicEffectContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
renderRhythmicEffect(kind, leds, numLeds, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:resetRandomFillAllInstance -->
### `resetRandomFillAllInstance`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/vent.h`
- Signature: `void resetRandomFillAllInstance(RandomFillAllInstance& instance, unsigned long* lastUpdate = nullptr);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: state／lifecycle
- Complete example call:

```cpp
resetRandomFillAllInstance(instance, lastUpdate);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_2.cpp`, `firmware/shared/src/storymode/storyMode_activation.cpp`, `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:resetRgbIndependentLightning -->
### `resetRgbIndependentLightning`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/independent_lightning.h`
- Signature: `void resetRgbIndependentLightning(RgbIndependentLightningContext& context, uint32_t seed);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: control／configuration
- Complete example call:

```cpp
resetRgbIndependentLightning(context, seed);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:resetWledExtraParams -->
### `resetWledExtraParams`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `void resetWledExtraParams(WLED_ExtraParams* params);`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range
- Complete example call:

```cpp
resetWledExtraParams(params);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:resetWledOutputFrames -->
### `resetWledOutputFrames`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_wled/1D_strip.h`
- Signature: `void resetWledOutputFrames();`
- General／Component: WLED-derived RGB effect；使用前確認 instance state 與 strip geometry。
- Parameter groups: LED target／range
- Complete example call:

```cpp
resetWledOutputFrames();
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:rgb10CityRender -->
### `rgb10CityRender`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void rgb10CityRender(CRGB* leds, int numLeds, uint8_t matrixBrightness = 180, bool swapRB = true);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、brightness／fade
- Complete example call:

```cpp
rgb10CityRender(leds, numLeds, matrixBrightness, swapRB);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:rgbBreath_swipe -->
### `rgbBreath_swipe`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/breath.h`
- Signature: `void rgbBreath_swipe(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbBreathSwipeParams& params, const RgbBreathSwipeContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
rgbBreath_swipe(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:rgbBreath_swipe_palette -->
### `rgbBreath_swipe_palette`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/breath.h`
- Signature: `void rgbBreath_swipe_palette(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbBreathSwipeParams& params, const RgbBreathSwipeContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
rgbBreath_swipe_palette(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:rgbBreath_swipe_palette_v2 -->
### `rgbBreath_swipe_palette_v2`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/breath.h`
- Signature: `void rgbBreath_swipe_palette_v2(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbBreathSwipeParams& params, const RgbBreathSwipeContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
rgbBreath_swipe_palette_v2(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:rgbBreath_swipe_palette_v3 -->
### `rgbBreath_swipe_palette_v3`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/breath.h`
- Signature: `void rgbBreath_swipe_palette_v3(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbBreathSwipeV3Params& params, const RgbBreathSwipeContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
rgbBreath_swipe_palette_v3(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:rgbLibColor -->
### `rgbLibColor`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/common.h`
- Signature: `CRGB rgbLibColor(CRGB color, const CRGBPalette16* palette, uint8_t paletteIndex);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: color／palette、state／lifecycle
- Complete example call:

```cpp
rgbLibColor(color, palette, paletteIndex);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:rgbLibScaleBpmBySpeed -->
### `rgbLibScaleBpmBySpeed`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/common.h`
- Signature: `uint16_t rgbLibScaleBpmBySpeed(uint16_t bpm, uint8_t speed);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: timing／speed
- Complete example call:

```cpp
rgbLibScaleBpmBySpeed(bpm, speed);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:rgbOff -->
### `rgbOff`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/common.h`
- Signature: `void rgbOff(CRGB* leds, int NUM_LEDS);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range
- Complete example call:

```cpp
rgbOff(leds, NUM_LEDS);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_0_v1.cpp`, `firmware/shared/src/storymode/storyMode_0_v2.cpp`, `firmware/shared/src/storymode/storyMode_2.cpp`, `firmware/shared/src/storymode/storyMode_3.cpp`, `firmware/shared/src/storymode/storyMode_activation.cpp`, `firmware/shared/src/storymode/storyMode_all_off.cpp`, `firmware/shared/src/storymode/storyMode_awakening_3.cpp`, `firmware/shared/src/storymode/storyMode_develop.cpp`, `firmware/shared/src/storymode/storyMode_idle.cpp`, `firmware/shared/src/storymode/storyMode_motor.cpp`, `firmware/shared/src/storymode/storyMode_motor_reset.cpp`, `firmware/shared/src/storymode/storyMode_plasma.cpp`, `firmware/shared/src/storymode/storyMode_signals.cpp`, `firmware/shared/src/storymode/storyMode_storing_energy.cpp`, `firmware/shared/src/storymode/storyMode_trans_am.cpp`, `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:rgbOn -->
### `rgbOn`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/common.h`
- Signature: `void rgbOn(CRGB* leds, int NUM_LEDS, CRGB color);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette
- Complete example call:

```cpp
rgbOn(leds, NUM_LEDS, color);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_0_v1.cpp`, `firmware/shared/src/storymode/storyMode_0_v2.cpp`, `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:rgb_breath -->
### `rgb_breath`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/breath.h`
- Signature: `bool rgb_breath(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbBreathParams& params, RgbBreathContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
rgb_breath(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:rgb_breath_swipeOn -->
### `rgb_breath_swipeOn`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/breath.h`
- Signature: `bool rgb_breath_swipeOn(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbBreathParams& params, RgbBreathContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
rgb_breath_swipeOn(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:rgb_fadeOut -->
### `rgb_fadeOut`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/common.h`
- Signature: `bool rgb_fadeOut(CRGB* leds, int NUM_LEDS, uint8_t fadeSpeed);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、brightness／fade、timing／speed
- Complete example call:

```cpp
rgb_fadeOut(leds, NUM_LEDS, fadeSpeed);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_0_v1.cpp`, `firmware/shared/src/storymode/storyMode_0_v2.cpp`, `firmware/shared/src/storymode/storyMode_2.cpp`, `firmware/shared/src/storymode/storyMode_3.cpp`, `firmware/shared/src/storymode/storyMode_activation.cpp`, `firmware/shared/src/storymode/storyMode_awakening_3.cpp`, `firmware/shared/src/storymode/storyMode_trans_am.cpp`, `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:rippleCenterOut -->
### `rippleCenterOut`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `bool rippleCenterOut(CRGB* leds, int NUM_LEDS, CRGBPalette16 palette, RippleCenterOutInstance* instance);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette
- Complete example call:

```cpp
rippleCenterOut(leds, NUM_LEDS, palette, instance);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runBlurSinDuet -->
### `runBlurSinDuet`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runBlurSinDuet(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, CHSV color1, CHSV color2, uint8_t bpm = 40, uint8_t blurAmount = 150, GradientDirection axis = GRADIENT_HORIZONTAL);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、color／palette、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
matrixPattern.runBlurSinDuet(leds, NUM_RGBS, updateInterval, lastUpdate, color1, color2, bpm, blurAmount, axis);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runChevrons -->
### `runChevrons`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runChevrons(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, CRGB chevronColor, CRGB bgColor = CRGB::Black);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、color／palette、timing／speed、state／lifecycle
- Complete example call:

```cpp
matrixPattern.runChevrons(leds, NUM_RGBS, updateInterval, lastUpdate, chevronColor, bgColor);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runControlledGradientStream -->
### `runControlledGradientStream`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runControlledGradientStream(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, CRGBPalette16 palette, uint8_t speed, bool reverse = false, uint8_t brightness = 255);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
matrixPattern.runControlledGradientStream(leds, NUM_RGBS, updateInterval, lastUpdate, palette, speed, reverse, brightness);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runDiagonalComet -->
### `runDiagonalComet`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runDiagonalComet(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, CRGBPalette16 basePalette, CRGBPalette16 cometPalette, uint8_t baseSpeed = 1, uint8_t cometSpeed = 2, uint8_t cometLength = 5, bool reverse = false);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、color／palette、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
matrixPattern.runDiagonalComet(leds, NUM_RGBS, updateInterval, lastUpdate, basePalette, cometPalette, baseSpeed, cometSpeed, cometLength, reverse);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runDiagonalGradient -->
### `runDiagonalGradient`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runDiagonalGradient(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, CRGBPalette16 palette, uint8_t speed, bool reverse);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、color／palette、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
matrixPattern.runDiagonalGradient(leds, NUM_RGBS, updateInterval, lastUpdate, palette, speed, reverse);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runFifthCounterpoint -->
### `runFifthCounterpoint`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runFifthCounterpoint(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, uint16_t bodyPeriodMs = 5000);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、timing／speed、state／lifecycle
- Complete example call:

```cpp
matrixPattern.runFifthCounterpoint(leds, NUM_RGBS, updateInterval, lastUpdate, bodyPeriodMs);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runGNWireNormalSnake -->
### `runGNWireNormalSnake`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runGNWireNormalSnake(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, CRGBPalette16 basePalette, CRGBPalette16 snakePalette, uint8_t speed = 2, uint16_t snakeLength = 5);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、color／palette、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
matrixPattern.runGNWireNormalSnake(leds, NUM_RGBS, updateInterval, lastUpdate, basePalette, snakePalette, speed, snakeLength);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runGNWireTransAMSnake -->
### `runGNWireTransAMSnake`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runGNWireTransAMSnake(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, CRGBPalette16 basePalette, CRGBPalette16 snakePalette, uint8_t speed = 2, uint16_t snakeLength = 5);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、color／palette、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
matrixPattern.runGNWireTransAMSnake(leds, NUM_RGBS, updateInterval, lastUpdate, basePalette, snakePalette, speed, snakeLength);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runHoneycombGradient -->
### `runHoneycombGradient`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runHoneycombGradient(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, CRGBPalette16 palette, uint8_t speed, uint8_t cellSize);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、color／palette、timing／speed、state／lifecycle
- Complete example call:

```cpp
matrixPattern.runHoneycombGradient(leds, NUM_RGBS, updateInterval, lastUpdate, palette, speed, cellSize);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runOctaveResonance -->
### `runOctaveResonance`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runOctaveResonance(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, uint16_t bodyPeriodMs = 5000, uint8_t globalScalePct = 40);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、timing／speed、state／lifecycle
- Complete example call:

```cpp
matrixPattern.runOctaveResonance(leds, NUM_RGBS, updateInterval, lastUpdate, bodyPeriodMs, globalScalePct);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runPaletteGradientStream -->
### `runPaletteGradientStream`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runPaletteGradientStream(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, CRGBPalette16 palette, uint8_t speed);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、color／palette、timing／speed、state／lifecycle
- Complete example call:

```cpp
matrixPattern.runPaletteGradientStream(leds, NUM_RGBS, updateInterval, lastUpdate, palette, speed);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runPattern -->
### `runPattern`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runPattern(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, int decreasingBrightness, int paletteSpeed, int radius, unsigned long* lastUpdate, CRGBPalette16 palette);` / `bool runPattern(CRGB* leds, int NUM_LEDS, unsigned long updateInterval, unsigned long* lastUpdate, CRGB color, CRGB colorTrail);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
matrixPattern.runPattern(leds, NUM_RGBS, updateInterval, decreasingBrightness, paletteSpeed, radius, lastUpdate, palette);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_storing_energy.cpp`, `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runPhotosynthesisDawn -->
### `runPhotosynthesisDawn`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runPhotosynthesisDawn(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, uint16_t bodyPeriodMs = 5000);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、timing／speed、state／lifecycle
- Complete example call:

```cpp
matrixPattern.runPhotosynthesisDawn(leds, NUM_RGBS, updateInterval, lastUpdate, bodyPeriodMs);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runRippleEffect -->
### `runRippleEffect`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runRippleEffect(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, CRGBPalette16 palette, uint8_t speed, uint8_t numRipples);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、color／palette、timing／speed、state／lifecycle
- Complete example call:

```cpp
matrixPattern.runRippleEffect(leds, NUM_RGBS, updateInterval, lastUpdate, palette, speed, numRipples);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runScanlineGradient -->
### `runScanlineGradient`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runScanlineGradient(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, CRGBPalette16 palette, uint8_t speed, uint8_t scanWidth);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、color／palette、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
matrixPattern.runScanlineGradient(leds, NUM_RGBS, updateInterval, lastUpdate, palette, speed, scanWidth);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runSequentialChevron -->
### `runSequentialChevron`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runSequentialChevron(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, CRGB ledColor, CRGB fillColor, CRGB chevronColor, CRGB bgColor = CRGB::Black, bool reverse = false, unsigned long phase2Interval = 0);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、color／palette、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
matrixPattern.runSequentialChevron(leds, NUM_RGBS, updateInterval, lastUpdate, ledColor, fillColor, chevronColor, bgColor, reverse, phase2Interval);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runSequentialLight -->
### `runSequentialLight`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runSequentialLight(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, CRGB ledColor, CRGB fillColor, CRGB bgColor = CRGB::Black, bool reverse = false);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、color／palette、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
matrixPattern.runSequentialLight(leds, NUM_RGBS, updateInterval, lastUpdate, ledColor, fillColor, bgColor, reverse);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runSequentialOn -->
### `runSequentialOn`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `bool runSequentialOn(CRGB** ledGroups, const int* numLeds, size_t groupCount, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbRunSequentialOnParams& params, const RgbRunSequentialOnContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
runSequentialOn(ledGroups, numLeds, groupCount, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runSquareSpotLight -->
### `runSquareSpotLight`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `void runSquareSpotLight(CRGB* leds, int NUM_RGBS, CRGB spotColor, CRGB bgColor = CRGB::Black);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、color／palette
- Complete example call:

```cpp
matrixPattern.runSquareSpotLight(leds, NUM_RGBS, spotColor, bgColor);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runStandingWaveResonance -->
### `runStandingWaveResonance`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runStandingWaveResonance(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, uint16_t bodyPeriodMs = 5000, uint8_t antinodeCount = 4);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、timing／speed、state／lifecycle
- Complete example call:

```cpp
matrixPattern.runStandingWaveResonance(leds, NUM_RGBS, updateInterval, lastUpdate, bodyPeriodMs, antinodeCount);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runSympatheticHeartbeat -->
### `runSympatheticHeartbeat`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runSympatheticHeartbeat(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, uint16_t totalDuration = 2000, uint8_t brightness = 255, uint8_t heartbeatSpace = 10, CRGB bgColor = CRGB(35, 0, 0), CRGB heartbeatColor = CRGB(255, 0, 0), uint16_t radius = 20, uint8_t speed = 30);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
matrixPattern.runSympatheticHeartbeat(leds, NUM_RGBS, updateInterval, lastUpdate, totalDuration, brightness, heartbeatSpace, bgColor, heartbeatColor, radius, speed);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runWaterRipples -->
### `runWaterRipples`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runWaterRipples(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, CRGBPalette16 palette, uint8_t speed, uint8_t intensity, uint32_t centerChangeMs = 3000);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、state／lifecycle
- Complete example call:

```cpp
matrixPattern.runWaterRipples(leds, NUM_RGBS, updateInterval, lastUpdate, palette, speed, intensity, centerChangeMs);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:runWaveGradient -->
### `runWaveGradient`

- Library／Source: patterns_matrix — `firmware/shared/include/patterns/patterns_matrix.h`
- Signature: `bool runWaveGradient(CRGB* leds, int NUM_RGBS, unsigned long updateInterval, unsigned long* lastUpdate, CRGBPalette16 palette, uint8_t speed, uint8_t waveCount);`
- General／Component: Matrix RGB effect；使用前確認 mapping、width、height 與方向。
- Parameter groups: LED target／range、color／palette、timing／speed、state／lifecycle
- Complete example call:

```cpp
matrixPattern.runWaveGradient(leds, NUM_RGBS, updateInterval, lastUpdate, palette, speed, waveCount);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:shoppingMallLight_V2 -->
### `shoppingMallLight_V2`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void shoppingMallLight_V2(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbTwinklesParams& params, RgbNoContext context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
shoppingMallLight_V2(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:signalPalette -->
### `signalPalette`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/signal.h`
- Signature: `void signalPalette(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbSignalPaletteParams& params, RgbSignalPaletteContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
signalPalette(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:sinelon -->
### `sinelon`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`; patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void sinelon(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbSinelonParams& params, RgbNoContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
sinelon(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:sinelonRainbow -->
### `sinelonRainbow`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`; patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void sinelonRainbow(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbSinelonRainbowParams& params, RgbHueContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
sinelonRainbow(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:smoothSineBreath -->
### `smoothSineBreath`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/breath.h`
- Signature: `void smoothSineBreath(CRGB* leds, int numLeds, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, CRGB color);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed
- Complete example call:

```cpp
smoothSineBreath(leds, numLeds, brightnessMin, brightnessMax, cycleDurationMs, color);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_develop.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:theaterChaseRainbow -->
### `theaterChaseRainbow`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`; patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void theaterChaseRainbow(CRGB* leds, int NUM_LEDS, uint16_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbTheaterChaseRainbowParams& params, RgbTheaterChaseRainbowContext& context);` / `void theaterChaseRainbow(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbTheaterChaseRainbowParams& params, RgbTheaterChaseRainbowContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
theaterChaseRainbow(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:tunnelFire -->
### `tunnelFire`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void tunnelFire(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbTunnelFireParams& params, RgbTunnelFireContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
tunnelFire(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:tunnelFireOff -->
### `tunnelFireOff`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void tunnelFireOff(CRGB* leds, int numLeds, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbTunnelFireParams& params, RgbTunnelFireContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
tunnelFireOff(leds, numLeds, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:turbine -->
### `turbine`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/turbine.h`
- Signature: `void turbine(CRGB* leds, int NUM_LEDS, TurbineInstance* instance);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range
- Complete example call:

```cpp
turbine(leds, NUM_LEDS, instance);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:turbine_v3 -->
### `turbine_v3`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/turbine.h`
- Signature: `void turbine_v3(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbTurbineV3Params& params, const RgbTurbineV3Context& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
turbine_v3(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_2.cpp`, `firmware/shared/src/storymode/storyMode_3.cpp`, `firmware/shared/src/storymode/storyMode_activation.cpp`, `firmware/shared/src/storymode/storyMode_awakening_3.cpp`, `firmware/shared/src/storymode/storyMode_motor.cpp`, `firmware/shared/src/storymode/storyMode_signals.cpp`, `firmware/shared/src/storymode/storyMode_storing_energy.cpp`, `firmware/shared/src/storymode/storyMode_trans_am.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:turbine_v3_sound -->
### `turbine_v3_sound`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/turbine.h`
- Signature: `bool turbine_v3_sound(CRGB* leds, int NUM_LEDS, uint8_t initialSpeed, uint8_t finalSpeed, uint8_t brightnessMin, uint8_t brightnessMax, WLED_DirectionMode directionMode, const RgbTurbineV3SoundParams& params, const RgbTurbineV3SoundContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
turbine_v3_sound(leds, NUM_LEDS, initialSpeed, finalSpeed, brightnessMin, brightnessMax, directionMode, params, context);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_motor.cpp`, `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:twoColorGradientFill -->
### `twoColorGradientFill`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`; patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void twoColorGradientFill(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbTwoColorGradientParams& params, const RgbNoContext& context);` / `void twoColorGradientFill(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbTwoColorGradientParams& params, RgbNoContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
twoColorGradientFill(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:twoSideComet -->
### `twoSideComet`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`; patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void twoSideComet(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbTwoSideCometParams& params, const RgbNoContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
twoSideComet(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:updateBoosterCycle -->
### `updateBoosterCycle`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/common.h`
- Signature: `void updateBoosterCycle(BoosterCycleState* cycleState, unsigned long boosterElapsed, uint8_t boosterBrightnessBaseMin, uint8_t boosterBrightnessBaseMax, uint8_t boosterBrightnessVariation, unsigned long boosterIntervalMin, unsigned long boosterIntervalMax);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: brightness／fade、timing／speed、state／lifecycle
- Complete example call:

```cpp
updateBoosterCycle(cycleState, boosterElapsed, boosterBrightnessBaseMin, boosterBrightnessBaseMax, boosterBrightnessVariation, boosterIntervalMin, boosterIntervalMax);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:updateCenterLight -->
### `updateCenterLight`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/turbine.h`
- Signature: `void updateCenterLight(TurbineInstance_v2* instance, uint8_t centerIndex, CRGB* leds);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、state／lifecycle
- Complete example call:

```cpp
updateCenterLight(instance, centerIndex, leds);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:updateMissileLauncherBurst -->
### `updateMissileLauncherBurst`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/weapon.h`
- Signature: `void updateMissileLauncherBurst(CRGB* leds, MissileLauncherStateInternal* state, unsigned long now);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、state／lifecycle
- Complete example call:

```cpp
updateMissileLauncherBurst(leds, state, now);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:whiteComet -->
### `whiteComet`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/breath.h`
- Signature: `void whiteComet(CRGB* leds, int NUM_LEDS, unsigned long* whiteSwipeCounter, unsigned long firstWhiteSwipe, unsigned long secondWhiteSwipe, unsigned long thirdWhiteSwipe, uint8_t swipeBrightness, int dropFirstBrightness, int dropSecondBrightness, int dropThirdBrightness, bool direction);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、brightness／fade、state／lifecycle、geometry／direction
- Complete example call:

```cpp
whiteComet(leds, NUM_LEDS, whiteSwipeCounter, firstWhiteSwipe, secondWhiteSwipe, thirdWhiteSwipe, swipeBrightness, dropFirstBrightness, dropSecondBrightness, dropThirdBrightness, direction);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:whiteSwipe -->
### `whiteSwipe`

- Library／Source: lib_rgb/ — `firmware/shared/include/lib/lib_rgb/flow.h`
- Signature: `void whiteSwipe(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbWhiteSwipeParams& params, RgbWhiteSwipeContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
whiteSwipe(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: `firmware/shared/src/storymode/storyMode_motor.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:whiteSwipeComet -->
### `whiteSwipeComet`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `bool whiteSwipeComet(CRGB* leds, int NUM_LEDS, int speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbWhiteSwipeCometParams& params, const RgbWhiteSwipeCometContext& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
whiteSwipeComet(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:whiteSwipeWithBackgroundV3 -->
### `whiteSwipeWithBackgroundV3`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void whiteSwipeWithBackgroundV3(CRGB* leds, int NUM_LEDS, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbWhiteSwipeWithBackgroundV3Params& params, const RgbWhiteSwipeWithBackgroundV3Context& context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
whiteSwipeWithBackgroundV3(leds, NUM_LEDS, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:whiteSwipeWithBackgroundV3_synced -->
### `whiteSwipeWithBackgroundV3_synced`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/flow.h`
- Signature: `void whiteSwipeWithBackgroundV3_synced(CRGB* leds, int NUM_LEDS, bool direction, unsigned long* startTime, unsigned long cycleDuration, unsigned long totalLoopDuration, CRGB color, int trailLength, bool hasHeadTrail, SwipeEffectInstance* instance, CRGBPalette16 BGpalette, int* cycleCount);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、timing／speed、state／lifecycle、geometry／direction
- Complete example call:

```cpp
whiteSwipeWithBackgroundV3_synced(leds, NUM_LEDS, direction, startTime, cycleDuration, totalLoopDuration, color, trailLength, hasHeadTrail, instance, BGpalette, cycleCount);
```

- PGU consumers: `firmware/shared/src/recorder/firmware_effect_runtime.cpp`
- Consumer status: CURRENT PGU direct consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。

<!-- API:zoidsTail -->
### `zoidsTail`

- Library／Source: patterns_rgb/ — `firmware/shared/include/patterns/patterns_rgb/weapon.h`
- Signature: `void zoidsTail(CRGB** ledStrips, const int* numLedsPerStrip, uint8_t numStrips, uint8_t speed, uint8_t brightnessMin, uint8_t brightnessMax, uint32_t cycleDurationMs, uint32_t totalDurationMs, WLED_DirectionMode directionMode, CRGB color, CRGBPalette16 palette, const RgbZoidsTailParams& params, RgbZoidsTailContext context);`
- General／Component: RGB effect／support API；實際部件由 PGU consumer 與接線表決定。
- Parameter groups: LED target／range、color／palette、brightness／fade、timing／speed、geometry／direction
- Complete example call:

```cpp
zoidsTail(ledStrips, numLedsPerStrip, numStrips, speed, brightnessMin, brightnessMax, cycleDurationMs, totalDurationMs, directionMode, color, palette, params, context);
```

- PGU consumers: none found
- Consumer status: available API；目前 PGU storyMode 無直接 consumer
- Off／reset: 由 StoryMode 明確清黑／reset state；不得把未指定 consumer 自動視為 ON。
