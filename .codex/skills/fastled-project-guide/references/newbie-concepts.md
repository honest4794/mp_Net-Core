# 新手概念說明

這份說明用最簡單的繁體中文解釋本專案。

## 這個專案是什麼

這是一套 ESP32-S3 燈光與可動控制韌體。

- RGB LED：彩色燈帶，用 FastLED 控制。
- PCA9685：外接 PWM 板，用來控制很多白燈、呼吸燈或其他 PWM channel。
- Motor / Servo：可動機構，例如開合、旋轉、推桿。
- Master：主控晶片。
- Slave：負責實際燈效與馬達的晶片。

簡單講：

```text
Timer / Video / WiFi
        ↓
      Master
        ↓ I2C 或 RS485
   Slaves 1–20
        ↓
 RGB / PCA / GPIO17 Motor
```

## Master 是什麼

Master 是「總指揮」。

它負責：

- 收 timer screen 指令。
- 控制 video UART 播片。
- 開 WiFi update 頁面。
- 用 I2C 或 RS485 叫 slave 播 story mode。

Master 通常不直接控制所有燈，它主要負責分派命令。

## Slave 是什麼

Slave 是「執行者」。

它負責：

- 收 master 的 I2C 指令。
- 跑 RGB 燈效。
- 控制 PCA9685 的 PWM channel。
- 控制 motor / servo。

每個 slave 都要有唯一的 `SLAVE_ID`；使用 I2C 時亦要有唯一 I2C address。

Master↔Slave RS485 使用 GPIO14 TX → module RXD、GPIO15 RX ← module TXD、GPIO16 EN。GPIO17 則是每個 Slave
自己送指令到 ATtiny412 motor board 的另一條 TX-only UART，兩者不是同一條線。

## Master-Slave 與 Standalone

- `master-slave`：Master 像總指揮，Slave 按自己的 `slaveId` 執行工作。
- `slave_standalone`：沒有 Master，單一板直接用已配置的 `slaveId` 跑正式 StoryMode。

修改 effect 前先確認是哪一種 project。Standalone 直接沿用正式 StoryMode 時序，
不需要另外用 macro 建一套 timeslot。

## Story Mode 是什麼

Story mode 是一段按時間播放的表演。

例如：

```text
0s：眼睛亮
3s：訊號燈變綠
6s：平台燈開始
9s：腳部馬達打開
```

程式通常用 `if (time >= x)` 判斷現在要開始哪一段。

## 為什麼用累積時間門檻

如果寫：

```cpp
if (time >= 0 && time < 2000) {
    // A 效果
}
if (time >= 2000 && time < 4000) {
    // B 效果
}
```

時間到 2000ms 後，A 效果就停止了。

如果 A 要繼續，就應該寫：

```cpp
if (time >= 0) {
    // A 效果會一直更新
}
if (time >= 2000) {
    // B 效果從 2000ms 開始加入
}
```

這就是本專案 story mode 的標準寫法。

## 為什麼 motor 要先寫

同一個 slave 裡，順序要像這樣：

```cpp
// 先寫 motor buffer
chServoHold(espMotor[0], MOTOR_DUTY_MAX);

// 再寫 RGB / PCA 效果
whiteSwipe(leds_RGB1, NUM_LEDS_RGB1, ...);
chOn(pcaLed[PWM0 * 16 + 0], 500);
```

原因很簡單：

- Motor 開啟是 stage 的主動作。
- RGB / PCA 是跟著 motor 狀態出現的效果。
- 這樣讀程式時，會先看到「機構做什麼」，再看到「燈怎樣配合」。

## RGB、PWM、Motor 差別

- RGB：一整條彩色燈帶，例如 `leds_RGB1`。
- PWM / PCA：單一 channel 的亮度，例如 `pcaLed[PWM0 * 16 + 3]`。
- Motor / Servo：可動輸出，例如 `espMotor[0]`。

## 常見檔案

- `platformio.ini`：共用建置設定。
- `platformio_local.ini`：本機硬體設定，不一定適合別人的機器。
- `firmware/master/src/main.cpp`：master 入口。
- `firmware/slave/src/main_slave.cpp`：slave 入口。
- `firmware/shared/src/storymode/`：story mode 程式。
- `firmware/shared/src/patterns/`：可重用燈效。
- `docs/`：協議、硬體、story mode 文件。

## 新手改 code 前先做什麼

1. 確認 project 是 master-slave 還是 slave_standalone，再確認要改 master、slave，還是 shared。
2. 確認會不會影響 I2C、UART、WiFi、OTA、motor。
3. 先讀對應 docs。
4. 改小範圍，不做 unrelated refactor。
5. 可行時跑 PlatformIO build。
