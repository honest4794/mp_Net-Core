# 可動（Servo Motor）說明

---

實際示範請參考 [`firmware/shared/src/storymode/storyMode_dev.cpp`](../../../../../../firmware/shared/src/storymode/storyMode_dev.cpp) — 同時驅動 8 個 ESP 馬達與 2 個 PCA 馬達的 breath 模式：

```cpp
#include "lib/lib_channel.h"

bool storyMode_dev()
{
    switch (modeDevState)
    {
    case MODE_DEV_START:
        // RGB addressable LED 背景漸層（不影響馬達）
        gradientDynamicPalette(leds_RGB1, NUM_LEDS_RGB1, &paletteIndex1, 2, devModePalette);
        // ... (RGB2/3/4 同上)

        // ESP LEDC 馬達：8 個 channel，逐個用不同 BPM 擺動
        chBreath(espMotor[0], 5);     // GPIO 35，5 BPM
        chBreath(espMotor[1], 10);    // GPIO 36，10 BPM
        chBreath(espMotor[2], 15);    // GPIO 37，15 BPM
        chBreath(espMotor[3], 20);    // GPIO 38，20 BPM
        chBreath(espMotor[4], 25);    // GPIO 39，25 BPM
        chBreath(espMotor[5], 30);    // GPIO 40，30 BPM
        chBreath(espMotor[6], 35);    // GPIO 41，35 BPM
        chBreath(espMotor[7], 40);    // GPIO 42，40 BPM

        // PCA9685 馬達板：2 個 channel
        chBreath(pcaMotor[0], 5);     // PCA9685 chip ch0，5 BPM
        chBreath(pcaMotor[1], 10);    // PCA9685 chip ch1，10 BPM
        return false;
    default:
        return false;
    }
}
```

> **重點：**
> - `storyMode_dev()` 只寫入 `channelStaging`，不需直接呼叫 `updateChannelStaging()` — 由 `storyModeController` 統一在 frame loop 結束時觸發複製。
> - 同一個函式裡同時操作 **RGB LED**（`gradientDynamicPalette`）、**ESP 馬達**（`espMotor[0..7]`）、**PCA 馬達**（`pcaMotor[0..1]`）互不干擾。
> - 要啟用此 dev mode，需在 `platformio.ini` 對應 slave env 加上 `-D ENABLE_MOTOR_ESP=1`（及 `-D ENABLE_MOTOR_PCA=1` 若使用 PCA 馬達）。

其他常見 API（即時跳位、速度控制）：

```cpp
chSetPosition(espMotor[0], MOTOR_DUTY_MAX, 2,  15);    // ESP ch0，~3 秒掃到 180°
chSetPosition(pcaMotor[5], MOTOR_DUTY_MAX, 10, 500);   // PCA9685 ch5，~20.5 秒
chOn(espMotor[0], MOTOR_DUTY_MAX);                     // ESP ch0 → 即時跳到 180°
chOn(pcaMotor[1], MOTOR_DUTY_MAX);                     // PCA9685 ch1 → 即時跳到 180°
```

> `lib_channel` 現已是 branch 內唯一的 PWM / servo 控制層。舊 `lib_pwm` / `patterns_pwm` helper 已整合為 `ch*` API，`initPWM()` / `pwmArray` 舊路徑亦已移除。

---

##### Channel Group Accessors

使用 `espMotor[n]`、`pcaMotor[n]`、`espLed[n]`、`pcaLed[n]` 存取 channel，取代手動計算 offset：

| Accessor | 說明 | 對應 channel（預設 MOTOR_NUM_ESP=8，ENABLE_LED_ESP=0）|
|---|---|---|
| `espMotor[0..7]` | ESP32 原生 PWM 可動 | 0–7 |
| `pcaMotor[0..15]` | PCA9685 可動 | 8–23 |
| `espLed[0..N-1]` | ESP32 原生 PWM LED（需 `ENABLE_LED_ESP=1`） | 緊接 pcaMotor 後，與 espMotor 共用 LEDC（合計 ≤ 8） |
| `pcaLed[0..]` | PCA9685 LED | `espLed` 段之後 |

> 各段大小由編譯開關決定，自動調整 offset，無需修改任何數值。如 `ENABLE_MOTOR_ESP=0`，`pcaMotor` 從 channel 0 開始；如 `ENABLE_LED_ESP=0`（預設），`espLed` 段大小為 0，`pcaLed` 緊接 `pcaMotor` 之後，與原本完全相同。

---

## 啟用（於 `platformio.ini` 設定）

> **重要：** 所有 per-env 的啟用旗標、servo 數量、GPIO 腳位，**一律在 `platformio.ini` 對應 slave env 的 `build_flags` 中設定**。請勿直接修改 `configMotor.h`（該檔只保留全域預設值；實際範例見 `platformio.ini` 的 `[env:slave1]` / `[env:slave2]` 區塊）。

```ini
[env:slaveX]
build_flags =
    ${env:slaveX_base.build_flags}
    ; ---------- 可動設定 ----------
    -D ENABLE_MOTOR_ESP=1        ; ESP32 LEDC（channel 0..MOTOR_NUM_ESP-1）
    -D ENABLE_MOTOR_PCA=1        ; PCA9685 I2C chip（channel MOTOR_NUM_ESP..）
    -D MOTOR_NUM_ESP=8           ; 啟用的 ESP servo 數量（≤8）
    -D MOTOR_NUM_CHANNEL_PCA=16          ; 啟用的 PCA servo 數量（≤16）
    -D MOTOR_PCA_ADDRESS=0x4B    ; PCA9685 可動板 I2C 地址
    ; ---------- 可動 ESP GPIO 腳位 ----------
    -D MOTOR_PIN_0=35
    -D MOTOR_PIN_1=36
    -D MOTOR_PIN_2=37
    -D MOTOR_PIN_3=38
    -D MOTOR_PIN_4=39
    -D MOTOR_PIN_5=40
    -D MOTOR_PIN_6=41
    -D MOTOR_PIN_7=42
```

> 需要不同的 GPIO？直接在上面覆蓋 `-D MOTOR_PIN_N=<pin>` 即可，**不要**改 `configMotor.h`。

---

## 設定參數（`configMotor.h` — 僅全域預設值）

> **請勿直接修改 `configMotor.h` 的 `MOTOR_PIN_*` / `MOTOR_NUM_*`。** 此檔只定義「若 `platformio.ini` 沒設定時的 fallback 預設」，所有 per-slave 的腳位與數量，都應在 `platformio.ini` 的 slave env 用 `-D` 覆蓋。

檔案位置：`firmware/shared/include/config/configMotor.h`

```cpp
// 共用頻率
#define MOTOR_FREQUENCY         50      // PWM 頻率（Hz）

// 原生 ESP LEDC — 預設值（per-env 請在 platformio.ini 覆蓋）
#define MOTOR_NUM_ESP           8       // ESP 可動數量（最多 8，對應 PIN_0–7）
#define MOTOR_PIN_0             35      // Servo 0 GPIO pin（預設；用 platformio.ini 覆蓋）
#define MOTOR_PIN_1             36
#define MOTOR_PIN_2             37
#define MOTOR_PIN_3             38
#define MOTOR_PIN_4             39
#define MOTOR_PIN_5             40
#define MOTOR_PIN_6             41
#define MOTOR_PIN_7             42
#define MOTOR_ESP_RES           12      // 解析度 bits

// PCA9685
#define MOTOR_NUM_CHANNEL_PCA           16      // PCA9685 可動數量（最多 16）
#define MOTOR_PCA_ADDRESS       0x60    // I2C 地址預設值（platformio.ini 可覆蓋）

// Compile-time guards（超出限制會 build 失敗，只在對應 ENABLE_MOTOR_* 啟用時生效）
#if ENABLE_MOTOR_ESP
static_assert(MOTOR_NUM_ESP <= 8,  "MOTOR_NUM_ESP max is 8 (only 8 pins defined)");
#endif
#if ENABLE_MOTOR_PCA
static_assert(MOTOR_NUM_CHANNEL_PCA <= 16, "MOTOR_NUM_CHANNEL_PCA max is 16 (PCA9685 chip limit)");
#endif

// 共用 duty cycle 範圍
#define MOTOR_DUTY_MIN          102     // 對應 0°
#define MOTOR_DUTY_MAX          512     // 對應 180°
#define MOTOR_ORIGIN            MOTOR_DUTY_MIN
```

> 所有 `#define` 均以 `#ifndef` 包裝，可在 `platformio.ini` 用 `-D` 旗標覆蓋。

---

#### Channel 對應表

PCA 的起始 channel 由 `MOTOR_NUM_ESP` 決定：

| Channel | 後端 | 硬件 | 需要啟用 |
|---|---|---|---|
| 0 … `MOTOR_NUM_ESP-1` | 原生 ESP LEDC | GPIO PIN_0 … PIN_N | `ENABLE_MOTOR_ESP=1` |
| `MOTOR_NUM_ESP` … `MOTOR_NUM_ESP+MOTOR_NUM_CHANNEL_PCA-1` | PCA9685 | I2C chip channel 0–N | `ENABLE_MOTOR_PCA=1` |
| `CH_LED_ESP_START` … `+LED_NUM_ESP-1` | 原生 ESP LEDC | GPIO `LED_ESP_PIN_0..N`（與 espMotor 共用，合計 ≤ 8） | `ENABLE_LED_ESP=1` |
| `CH_LED_START` … | PCA9685 LED | LED 板（1000Hz） | 永遠啟用 |

預設（`MOTOR_NUM_ESP=8`，`MOTOR_NUM_CHANNEL_PCA=16`）對應：

| Channel | 後端 | 硬件 |
|---|---|---|
| 0 | ESP | GPIO 35 |
| 1 | ESP | GPIO 36 |
| 2 | ESP | GPIO 37 |
| 3 | ESP | GPIO 38 |
| 4 | ESP | GPIO 39 |
| 5 | ESP | GPIO 40 |
| 6 | ESP | GPIO 41 |
| 7 | ESP | GPIO 42 |
| 8–23 | PCA9685（0x4B） | I2C chip channel 0–15 |
| 24+ | PCA9685 LED 板 | LED channel（60Hz） |

---

## PWM 脈衝與角度

可動馬達的角度透過 **PWM 訊號的脈衝寬度（pulse width）** 控制。  
在 **50Hz** 下，每個 cycle = **20ms**：

```
0.5ms ÷ 20ms = 2.5%   → 對應 0°
2.5ms ÷ 20ms = 12.5%  → 對應 180°
```

| PWM 脈衝 | 對應角度 |
|---|---|
| 0.5ms | 0°（最小） |
| 1.5ms | 90°（中間） |
| 2.5ms | 180°（最大） |

ESP LEDC 與 PCA9685 均使用 **12-bit 解析度**，duty cycle 數值相同：

| 解析度 | 最小值（0°） | 90° | 最大值（180°） |
|---|---|---|---|
| **12-bit（0–4095）** | **102** | **307** | **512** |

換算公式：
```
102 = 0.5 ÷ 20 × 4096  （0°）
307 = 1.5 ÷ 20 × 4096  （90°）
512 = 2.5 ÷ 20 × 4096  （180°）
```

| 參數 | 數值 | 意思 |
|---|---|---|
| `MOTOR_DUTY_MIN` | 102 | 對應 0.5ms 脈衝 → 0° |
| `MOTOR_DUTY_MAX` | 512 | 對應 2.5ms 脈衝 → 180° |
| `MOTOR_ORIGIN` | 102 | 原點（等同 `MOTOR_DUTY_MIN`） |

---

### `chOn(channelId, duty)` — 即時跳位

直接設定 duty cycle，立即生效。

| 參數 | 類型 | 說明 |
|---|---|---|
| `channelId` | `uint16_t` | 使用 `espMotor[n]` 或 `pcaMotor[n]` |
| `duty` | `uint16_t` | Duty cycle 數值（102–512） |

```cpp
chOn(espMotor[0], MOTOR_ORIGIN);   // ESP ch0 → 0°（即時）
chOn(pcaMotor[4], 450);            // PCA9685 ch4 → 450（即時）
```

---

### `chSetPosition(channelId, target, step, intervalMs)` — 速度控制

每次呼叫移動一步，需在每個 loop 中持續呼叫直至返回 `true`。

| 參數 | 類型 | 說明 |
|---|---|---|
| `channelId` | `uint16_t` | 使用 `espMotor[n]` 或 `pcaMotor[n]` |
| `target` | `uint16_t` | 目標 duty cycle（102–512） |
| `step` | `uint16_t` | 每步移動量（duty units）；0 自動視為 1 |
| `intervalMs` | `uint16_t` | 每步間隔（毫秒） |
| 返回值 | `bool` | `true` = 已到達目標 |

```cpp
// 每 loop 呼叫，到達目標後返回 true
if (chSetPosition(espMotor[0], MOTOR_DUTY_MAX, 1, 1000)) {
    // 已到達 180°，可轉換狀態
}
```

**速度參考（0°→180°，距離 = 410 duty units）：**

公式：`時間(ms) = (|target - current| ÷ step) × intervalMs`

| step | intervalMs | 0°→180° 所需時間 |
|---|---|---|
| 1 | 1000ms | ~6.8 分鐘 |
| 10 | 500ms | ~20.5 秒 |
| 1 | 20ms | ~8 秒 |
| 2 | 15ms | ~3 秒 |
| 10 | 20ms | ~0.8 秒 |

---

### `chBreath(channelId, freq)` — 來回擺動

讓伺服在 `MOTOR_DUTY_MIN`（0°）與 `MOTOR_DUTY_MAX`（180°）之間平滑振盪。每次 loop 呼叫即可，內部以 `beatsin16(freq, ...)` 驅動，無需額外狀態變數。

```cpp
chBreath(espMotor[1], 5);   // 以 5 BPM 來回擺動
```

亦可指定範圍：
```cpp
chBreath(espMotor[1], 5, 150, 400);  // 只在 150–400 之間振盪
```

> **完整示範：** 參見 [`storyMode_dev.cpp`](../../../../../../firmware/shared/src/storymode/storyMode_dev.cpp) — 以 5/10/15/…/40 BPM 同時驅動 8 個 ESP 馬達 + 2 個 PCA 馬達，搭配 RGB addressable LED 背景。

---

### `chOff(channelId)` / `chOffLeds()` / `chOffAll()` — 歸零

```cpp
chOff(espMotor[0]);   // 該 channel 關：馬達→0（斷電放鬆）、LED→0
chOffMotors();        // 所有馬達斷電放鬆（不影響 LED）
chOffLeds();          // 所有 LED 關（不影響馬達）
chOffAll();           // 全部關：LED→0、馬達→0（斷電放鬆）
chOriginMotors();     // 馬達回 0° 並通電 hold（要「通電停 0°」用這個，不是 chOff）
```

> **「off」對馬達 = 斷電(0)：** `chOff` / `chOffAll` / `chOffMotors` 對馬達都寫 `0`（斷電放鬆、停原地）。要馬達**通電停在 0°**，請用 `chOriginMotors()`。

---

### `chOffMotors()` — 斷電放鬆（停在當前位置）

| API | duty | 行為 |
|---|---|---|
| `chOriginMotors()` | 102 | 回 0° 並通電 hold |
| `chOffMotors()` | 0 | 斷電、停在當前位置，省 holding current |

```cpp
chOffMotors();   // 馬達斷電放鬆（不影響 LED）
```

> ⚠️ 寫 `0` = 無脈衝 = 失電：**無負載**才停得住，**有負載會垂下**（斷電與頂住負載互斥）。`102` 是「命令回 0°」會通電，要停在原地必須寫 `0`。
>
> 全關模式（`storyMode_all_off`）呼叫 `chOffAll()`，對馬達即為斷電放鬆。

---

## FreeRTOS 架構說明

fastLED 的 slave 端使用 FreeRTOS 雙核心發送。可動控制整合在現有的 pwmTask 中：

```
Story mode（Core 1）
  ├─ chXxx(espMotor[n], ...)    → 寫入 channelStaging[]（馬達）
  ├─ chXxx(pcaLed[n], ...)      → 寫入 channelStaging[]（LED）
  └─ updateChannelStaging()     → 觸發複製（必須呼叫）[PWM_UPDATE_SAFE mutex]
       └─ channelStaging → channelBuffer

pwmUpdateTask（Core 0，每 20ms）
  └─ channelBuffer → channelBufferCopy（mutex 快照）
       └─ dispatchChannels()
            ├─ PCA9685 馬達板 → setPWM_all（50Hz）
            ├─ PCA9685 LED 板 → setPWM_all（1000Hz）
            └─ ESP LEDC        → ledcWrite（50Hz）
```

**關鍵：** 每次 loop 必須呼叫 `updateChannelStaging()` 才會更新至硬體。現有 story mode 已包含此呼叫。

---

## 馬達 off 語意：off = relax（斷電放鬆）

本分支採「off = 斷電放鬆」語意（對齊 dev_Ariel 線）。`chOff`/`chOffAll`/`chOffMotors`
對馬達 channel **一律寫 `0` duty（停脈衝、失電）**，馬達停在當前位置（不回 0°）。
要「回 0° 並通電 hold」必須改用 `chOriginMotors()`。

| API | 馬達 duty | 行為 |
|---|---|---|
| `chOffMotors()` | `0` | **斷電放鬆**、停在當前位置，省 holding current/降溫 |
| `chOff(ch)` / `chOffAll()` | 馬達 `0`、LED `rangeMin` | off=放鬆馬達 + 關 LED |
| `chOriginMotors()` | `rangeMin`（102） | 命令回 0° 並**通電 hold** |

```cpp
chOffMotors();     // 只放鬆馬達 channel（[0, CH_LED_START)），不影響 LED
chOriginMotors();  // 馬達回 0° 並通電 hold（需要定位/頂負載時）
```

> ⚠️ 寫 `0` = 無脈衝 = 失電：**無負載**才停得住，**有負載會因失去保持扭力而垂下**
> （斷電與頂住負載本質互斥）。所有 `chOffAll()`（含 story mode 內）皆會放鬆馬達；
> 若該段需要馬達保持位置，請改呼叫 `chOriginMotors()`。

### 全關（`Power: off`）

「全關」入口是 master 送的 **`Power: off`** I2C 指令（`firmware/slave/src/i2cController.cpp`）：
清 LED 後呼叫 `chOffMotors()` 斷電放鬆，並手動 `updateChannelStaging()` 觸發傳遞
（因 `isPowerSaveMode` 後 `runPattern()` 會提早 return、不再複製 staging）。

> ⚠️ 承重伺服在全關時會失電垂下。若某台機構不允許，請改在該 handler 用 `chOriginMotors()`。

---

## 相關檔案

| 檔案 | 職責 |
|---|---|
| `firmware/shared/include/config/configMotor.h` | 馬達硬體參數、duty range、GPIO 腳位 |
| `firmware/shared/include/config/configChannel.h` | Channel ID 排列、`TOTAL_CHANNELS`、group accessors |
| `firmware/shared/include/lib/lib_channel.h` | 公開 API 宣告 |
| `firmware/shared/src/lib/lib_channel.cpp` | 完整實作 |
| `platformio.ini` | 各 slave env 的 `ENABLE_MOTOR_*` 旗標 |
