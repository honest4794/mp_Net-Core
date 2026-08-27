# 外部影片播放裝置機制說明

## 概述

本專案支援一個**外部迷你顯示器**作為專用的影片播放裝置,能夠與 LED 燈光效果同步播放影片。該裝置透過 UART 串列通訊協定與 ESP32 主控晶片進行通訊。

---

## 1. 硬體架構

### 1.1 外部影片播放裝置規格

- **裝置類型**: 迷你顯示器 (Mini Monitor)
- **通訊協定**: UART (通用非同步收發傳輸器)
- **預設位址**: `0xEE`
- **用途**: 播放與 LED 故事模式同步的影片
- **控制方式**: 透過 UART 指令控制播放/停止

### 1.2 UART 通訊參數

```cpp
- RX 接腳: GPIO 5
- TX 接腳: GPIO 6
- 鮑率 (Baud Rate): 115200
- 資料格式: 8N1 (8 位元資料位元, 無同位檢查, 1 位元停止位元)
```

**配置位置**: `firmware/master/include/config.h` (28-33 行)

---

## 2. 通訊協定規範

### 2.1 封包格式

所有 UART 指令皆採用三位元組格式:

```
[位址位元組] [指令/模式位元組] [終止位元組]
[  0xEE   ] [   0x01-0xEE  ] [   0xFF   ]
```

### 2.2 指令定義

系統定義了以下影片控制指令 (參見 `globals.h` 215-223 行):

| 指令名稱 | 數值 | 功能說明 |
|---------|------|---------|
| `UART_VIDEO_IDLE` | `0xEE` | 待機狀態 (無影片播放) |
| `UART_VIDEO_PLAY_1` | `0x01` | 播放故事模式 0 的影片 |
| `UART_VIDEO_PLAY_2` | `0x02` | 播放故事模式 1 的影片 |
| `UART_VIDEO_PLAY_3` | `0x03` | 播放故事模式 2 的影片 |
| `UART_VIDEO_PLAY_4` | `0x04` | 播放故事模式 3 的影片 |
| `UART_VIDEO_STOP` | `0xAA` | 停止影片播放 |

### 2.3 封包範例

**播放故事模式 0 的影片**:
```
0xEE 0x01 0xFF
```

**停止影片播放**:
```
0xEE 0xAA 0xFF
```

---

## 3. 系統架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│  ESP32 主控晶片 (Master)                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  main.cpp (主程式迴圈)                                  │    │
│  │  - setup(): 初始化 UART, I2C, 計時器                    │    │
│  │  - loop(): 主執行迴圈                                   │    │
│  └────────────────────────────────────────────────────────┘    │
│           │                                                      │
│           ├───────────────┬───────────────┬──────────────┐     │
│           ▼               ▼               ▼              ▼     │
│  ┌─────────────────┐ ┌──────────────┐ ┌──────────┐ ┌──────┐  │
│  │ uartController  │ │ i2cController│ │timerCtrl │ │ WiFi │  │
│  │ (UART通訊控制) │ │ (從設備同步) │ │(倒數計時)│ │      │  │
│  └─────────────────┘ └──────────────┘ └──────────┘ └──────┘  │
│           │                     │                               │
│           │                     └─────► I2C ───► 從屬設備       │
│           │                              (Slave Devices)       │
└───────────┼──────────────────────────────────────────────────────┘
            │ UART (115200, 8N1)
            │ 接腳: RX=5, TX=6
            │
            ▼
     ┌──────────────────────┐
     │ 外部迷你顯示器        │
     │ (影片播放裝置)        │
     │ 位址: 0xEE           │
     └──────────────────────┘
```

---

## 4. 資料流程與控制邏輯

### 4.1 故事模式啟動流程

```
使用者觸發故事模式
        ↓
i2cController.cpp: 接收到故事模式指令
        ↓
setUARTVideoModeFromStoryMode(storyModeId)
        ↓
UARTVideoData = storyModeId + 1  (故事模式 0 → 影片 1)
        ↓
UARTSendImmediate = true  (立即發送旗標)
        ↓
handleUARTVideo()  (UART 處理函式)
        ↓
發送封包: [0xEE] [mode_byte] [0xFF]
        ↓
外部顯示器接收指令並開始播放對應影片
        ↓
每 5 秒重新發送一次指令 (確保連線穩定)
```

**關鍵程式碼**: `uartController.cpp` 179-183 行

### 4.2 故事模式完成流程

```
故事模式執行完畢/超時
        ↓
checkModeTimeout()  (i2cController.cpp)
        ↓
stopRunModeTimer()  (停止計時器)
        ↓
sendUARTVideoStop(true)  (發送停止指令)
        ↓
發送封包: [0xEE] [0xAA] [0xFF]
        ↓
外部顯示器停止播放影片
        ↓
sendNextModeCommand()  (準備下一個模式)
```

**關鍵程式碼**: `i2cController.cpp` 385-387 行

### 4.3 故事模式與影片指令映射

系統將內部的故事模式 ID 轉換為對應的影片播放指令:

| 故事模式 ID | 影片指令 | 指令數值 |
|-----------|---------|---------|
| 0 | UART_VIDEO_PLAY_1 | 0x01 |
| 1 | UART_VIDEO_PLAY_2 | 0x02 |
| 2 | UART_VIDEO_PLAY_3 | 0x03 |
| 3 | UART_VIDEO_PLAY_4 | 0x04 |

**轉換函式**: `setUARTVideoModeFromStoryMode()` - 將故事模式 ID 加 1

---

## 5. 初始化流程

### 5.1 主程式初始化 (main.cpp)

```cpp
void setup() {
    Serial.begin(115200);                      // 初始化主 Serial (偵錯用)
    initUART(UART_RX_PIN, UART_TX_PIN);       // 初始化 UART (影片控制用)
    initMasterI2C();                           // 初始化 I2C (從設備通訊)
    initTimer();                               // 初始化計時器
    scanForActiveSlaves();                     // 掃描連線的從設備
}
```

### 5.2 UART 初始化 (uartController.cpp)

```cpp
void initUART(int rxPin, int txPin) {
    Serial2.begin(115200, SERIAL_8N1, rxPin, txPin);
}
```

### 5.3 影片模式初始化 (i2cController.cpp)

```cpp
if (ENABLE_VIDEO_UART == 1) {
    initUARTVideoMode();  // 將影片裝置設定為待機模式 (0xEE)
}
```

---

## 6. 配置參數

### 6.1 編譯時期配置 (platformio.ini)

```ini
[env:master]
build_flags =
    -D ENABLE_VIDEO_UART=0          # 啟用/停用影片 UART 功能 (預設: 0)
    -D UART_VIDEO_ADDR=0xEE         # 影片裝置位址 (預設: 0xEE)
```

### 6.2 預設配置常數 (config.h)

```cpp
#ifndef UART_VIDEO_ADDR
#define UART_VIDEO_ADDR 0xEE        // 影片裝置位址
#endif

#ifndef ENABLE_VIDEO_UART
#define ENABLE_VIDEO_UART 0         // 預設: 停用
#endif

#define UART_RX_PIN 5               // UART 接收接腳
#define UART_TX_PIN 6               // UART 傳送接腳
```

**注意**: 目前預設為停用狀態 (`ENABLE_VIDEO_UART=0`),需手動啟用。

---

## 7. 核心 API 函式

### 7.1 影片控制函式 (uartController.h/cpp)

#### 7.1.1 設定影片模式
```cpp
void setUARTVideoMode(uint8_t mode, bool immediate = false);
```
- **功能**: 設定特定的影片模式 (0-4)
- **參數**:
  - `mode`: 影片模式編號
  - `immediate`: 是否立即發送 (預設: false)

#### 7.1.2 從故事模式設定影片
```cpp
void setUARTVideoModeFromStoryMode(uint8_t storyModeId, bool immediate = false);
```
- **功能**: 根據故事模式 ID 自動轉換並設定對應的影片模式
- **轉換邏輯**: `videoMode = storyModeId + 1`

#### 7.1.3 停止影片播放
```cpp
void sendUARTVideoStop(bool immediate = true);
```
- **功能**: 發送停止指令到影片裝置
- **預設**: 立即發送

#### 7.1.4 初始化影片模式
```cpp
void initUARTVideoMode();
```
- **功能**: 將影片裝置設定為待機狀態 (UART_VIDEO_IDLE)

### 7.2 通用 UART 發送函式

```cpp
void sendUART(uint8_t address, uint8_t *data, uint8_t dataLength) {
    Serial2.write(address);              // 發送位址位元組
    for (uint8_t i = 0; i < dataLength; i++)
        Serial2.write(data[i]);          // 發送資料位元組
    Serial2.write(0xFF);                 // 發送終止位元組
    Serial2.flush();                     // 確保資料完全發送
}
```

---

## 8. 週期性重送機制

系統實作了一個智慧型的週期性重送機制,確保影片裝置保持同步:

### 8.1 重送邏輯 (uartController.cpp 153-171 行)

```cpp
void handleUARTVideo() {
    // 如果有待發送的影片指令或已超過 5 秒
    if (UARTSendImmediate || (millis() - lastUARTSendTime > 5000)) {

        if (UARTVideoData != UART_VIDEO_IDLE) {
            // 發送影片播放指令
            sendUARTVideoMode(UARTVideoData);
        }

        lastUARTSendTime = millis();
        UARTSendImmediate = false;
    }
}
```

### 8.2 重送原理

- **初次發送**: 當 `UARTSendImmediate = true` 時立即發送
- **週期重送**: 如果影片仍在播放,每 5 秒重新發送一次指令
- **停止條件**: 當接收到停止指令時,不再重送

**目的**: 防止通訊中斷導致影片裝置失去同步

---

## 9. 計時器同步機制

除了影片控制外,系統還包含一個計時器同步機制,用於顯示剩餘時間:

### 9.1 計時器協定 (timerController.cpp)

**封包格式**:
```
[0xB4] [modeId] [brightness] [remainingSeconds] [0xFF]
```

**說明**:
- 位址 `0xB4`: 計時器裝置位址 (與影片裝置 0xEE 不同)
- 每秒更新一次剩餘秒數
- 與影片播放保持同步
- 當模式完成時協同發送停止指令

### 9.2 雙通道通訊架構

```
ESP32 Master
    ├─► UART 通道 1 (位址 0xEE) ──► 影片播放裝置
    └─► UART 通道 2 (位址 0xB4) ──► 計時器顯示裝置
```

兩個裝置獨立運作但保持同步,提供完整的視覺回饋。

---

## 10. 檔案結構總覽

| 檔案路徑 | 行數 | 功能說明 |
|---------|------|---------|
| `firmware/master/include/config.h` | 45 | 影片 UART 配置常數定義 |
| `firmware/master/include/uartController.h` | 25 | UART 介面函式宣告 |
| `firmware/master/src/uartController.cpp` | 196 | UART 影片通訊實作 |
| `firmware/master/src/i2cController.cpp` | 1001 | 從設備 I2C 同步 + 影片觸發邏輯 |
| `firmware/master/src/timerController.cpp` | 96 | 計時器同步控制 |
| `firmware/shared/include/globals.h` | 523 | 影片狀態列舉與全域變數 |
| `firmware/shared/src/globals.cpp` | 80 | 影片狀態變數初始化 |
| `firmware/master/src/main.cpp` | - | 主程式進入點與初始化 |

---

## 11. 故事模式系統整合

### 11.1 故事模式概述

系統支援 4 種主要故事模式,每種模式對應一個影片:

| 故事模式 | 配置常數 | 預設時長 | 對應影片 |
|---------|---------|---------|---------|
| 模式 0 v1 | `STORYMODE_0_V1_TOTAL_SECONDS` | 可配置 | 影片 1 (0x01) |
| 模式 0 v2 | `STORYMODE_0_V2_TOTAL_SECONDS` | 可配置 | 影片 1 (0x01) |
| 模式 1 | `STORYMODE_1_TOTAL_SECONDS` | 可配置 | 影片 2 (0x02) |
| 模式 2 | `STORYMODE_2_TOTAL_SECONDS` | 可配置 | 影片 3 (0x03) |
| 模式 3 | `STORYMODE_3_TOTAL_SECONDS` | 可配置 | 影片 4 (0x04) |

**定義位置**: `storyModeController.cpp` 103-108 行

### 11.2 同步機制

```
故事模式開始
    ├─► LED 燈光效果開始播放
    ├─► 發送 I2C 指令給所有從設備
    ├─► 發送 UART 指令給影片裝置
    └─► 啟動倒數計時器

故事模式執行中
    ├─► 每 5 秒重送影片指令 (維持同步)
    ├─► 每 1 秒更新計時器顯示
    └─► 監控模式超時

故事模式結束
    ├─► 停止 LED 燈光效果
    ├─► 發送停止指令給所有從設備
    ├─► 發送停止指令給影片裝置 (0xAA)
    └─► 重置計時器
```

### 11.3 關鍵整合點

1. **模式啟動時**: 影片指令立即發送
2. **模式執行中**: 週期性重送確保同步
3. **模式完成時**: 影片自動停止
4. **模式超時時**: 影片自動停止並清理狀態

---

## 12. 除錯與維護

### 12.1 啟用影片 UART 功能

編輯 `platformio.ini`:
```ini
[env:master]
build_flags =
    -D ENABLE_VIDEO_UART=1          # 改為 1 以啟用
```

### 12.2 監控 UART 通訊

可以在程式碼中加入 Serial 除錯訊息:
```cpp
Serial.printf("[UART] Sending video command: 0x%02X\n", mode);
```

### 12.3 常見問題排查

| 問題 | 可能原因 | 解決方案 |
|------|---------|---------|
| 影片不播放 | ENABLE_VIDEO_UART 未啟用 | 檢查 platformio.ini 配置 |
| 影片不同步 | UART 接腳接錯 | 確認 RX=5, TX=6 |
| 影片突然停止 | 通訊中斷 | 檢查接線與電源穩定性 |
| 影片延遲播放 | 鮑率設定錯誤 | 確認雙方都設定為 115200 |

---

## 13. 開發狀態

- **功能分支**: `feat/videoUART` (已合併至 dev)
- **目前狀態**: 已實作並整合完成
- **預設狀態**: 停用 (`ENABLE_VIDEO_UART=0`)
- **最近更新**:
  - 預設停用影片 UART 功能
  - 修復影片播放器 UART 問題
  - 整合影片 UART 與故事模式系統

**開發歷程**:
```
commit: 875eaef - 從 I2S 改為 LCD I80 驅動
commit: 241965a - 加入文件說明
commit: fb7d30c - [WIP] 時間 alpha 實作
```

---

## 14. 擴展可能性

### 14.1 支援更多影片模式

目前支援 4 種影片模式,若需增加:

1. 在 `globals.h` 中新增新的 `UART_VIDEO_PLAY_X` 常數
2. 在 `storyModeController.cpp` 中新增對應的故事模式
3. 更新映射邏輯以支援新模式

### 14.2 雙向通訊

目前為單向通訊 (ESP32 → 影片裝置),可擴展為雙向:

- 讀取影片播放狀態
- 接收播放完成通知
- 錯誤狀態回報

### 14.3 多影片裝置支援

可透過不同位址支援多個影片裝置:
- 裝置 1: 0xEE
- 裝置 2: 0xEF
- 裝置 3: 0xF0

---

## 15. 總結

本專案實作了一個完整的外部影片播放裝置控制系統,具備以下特點:

✅ **簡單可靠**: 三位元組協定,易於實作與除錯
✅ **同步精確**: 與 LED 燈光效果完美同步
✅ **容錯機制**: 週期性重送確保連線穩定
✅ **模組化設計**: 可選功能,不影響核心系統
✅ **可擴展性**: 易於新增更多影片模式或裝置

此機制使得整個系統能夠提供視覺與燈光的雙重互動體驗,大幅提升使用者的沈浸感。

---

**文件版本**: v1.0
**最後更新**: 2025-12-10
**作者**: Claude Code Analysis
