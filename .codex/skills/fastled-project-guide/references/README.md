# FastLED 用戶文檔
***此專案使用 PlatformIO IDE！ 不支援ArduinoIDE***

---
## <span style="color: darkorange;">☑️ FastLED系統升級</span>

**升級日期**: 2025-11-15
**升級版本**: FastLED 3.9.6 → <span style="color: red;">3.10.3</span>
```bash
#清除舊檔案
rm -rf .pio

#重新build project（這會下載 FastLED 3.10.3）
pio run -e master -e slave1
```

## <span style="color: green;">✅ 懶人包 ✅ 新增env的checklist</span>
1. 改``UART_VIDEO_ADDR`` (如果要用mini mon)
2. 改``SLAVE_ID``
3. 改``I2C_SLAVE_ADDR`` ⚠️ **地址必須從 0x10 開始，依序遞增 (0x10, 0x11, 0x12...)**
4. 改``ACTUAL_SLAVE_NUM``
5. 選擇 Master↔Slave transport：`SLAVE_TRANSPORT_UART=1` 使用 GPIO15／14／16 RS485，`0` 使用 I2C
6. 如使用 GPIO17 ATtiny412 motor，設定 `MOTOR_TRANSPORT_UART`、`UART_DC_MOTOR_COUNT` 與 address
7. 改``WIFI_NAME``
8. 改``ACTUAL_LED_NUM_PCA``
9. 改``PWM_ADDRESS``
10. （如有可動）設定 slave env ：
   - ``ENABLE_MOTOR_ESP`` / ``ENABLE_MOTOR_PCA``：啟用 ESP32 或 PCA9685
   - ``MOTOR_NUM_ESP`` / ``MOTOR_NUM_PCA``：可動數量
   - ``MOTOR_PCA_ADDRESS``：可動 pca9685 地址（⚠️ 不可與 LED pca9685 地址重複）
   - ``MOTOR_PIN_0`` ~ ``MOTOR_PIN_7``：ESP servo GPIO 腳位 預設值 GPIO 35–42）
   - 更詳細有關可動的setting請睇：[docs/motor/motor_servo.md](../../../../docs/motor/motor_servo.md)
11. 改``NUM_LEDS_RGB1_X`` (彩色LED燈珠數目)
12. 第一次燒master晶片，記得master要行一次``pio run --target uploadfs -e master``
13. 改``DEBUG_ENABLED`` (適用於開發階段，需要睇log)
14. 改``ENABLE_POWER_CYCLE_WIFI``（是否啟用連續reboot觸發WiFi功能）
15. 到`platformio_local.ini` 更改每個storymode長度（秒數）：
```cpp
-D STORYMODE_0_V1_TOTAL_SECONDS=31
-D STORYMODE_0_V2_TOTAL_SECONDS=27
-D STORYMODE_1_TOTAL_SECONDS=176
-D STORYMODE_2_TOTAL_SECONDS=158
-D STORYMODE_3_TOTAL_SECONDS=158
```
1.  Timer螢幕的韌體也要溝通好長度，2邊storymode長度數值**必須對齊**
2.  到`config.h` 查看 `BRIGHTNESS_SLOTS` 的數值，是否與Timer螢幕的韌體一致。
---

## ESP32(S3)mini 開發板 GPIO
![Alt Text](./images/esp32s3.jpg)

## 電路圖
![Alt Text](./images/i2cDiagram.png)


### 多條RGB燈腳位
使用了 **FastLED I2S 驅動**：

- ✅ 支援最多 **16 條並行 RGB 燈帶**
- ✅ 適用於 ESP32-S3
- ✅ 需要 PSRAM（每條燈帶超過 500 顆 LED 時）

**支援的 LED 類型：**
- ✅ **Clockless LEDs**：WS2812B
- ❌ **Clocked LEDs**：APA102C

**配置標誌：** `-D FASTLED_USES_ESP32S3_I2S`（已在 platformio.ini 啟用）

----
## 前置要求
此專案主要使用 FastLED 來控制 RGB 燈光。
建議先學習 FastLED 的基礎知識。
- 教學影片：
  https://www.youtube.com/watch?v=4Ut4UK7612M&list=PLgXkGn3BBAGi5dTOCuEwrLuFtfz0kGFTC
- 文件：
  https://fastled.io/docs/

-----------

## 程式碼庫與環境
此專案包含三類 PlatformIO target：

1. **master**：
   - **env**：`master`
   - **描述**：負責整體系統運作、外部 timer/video、WiFi update；透過 I2C 或 RS485 middleware 與 Slave 溝通。
   - **進入點**：`firmware/master/src/main.cpp`
   - **命令列**：`pio run -e master -t upload`

2. **slave1–slave20**：
   - **env**：`slave1` 至 `slave20`
   - **描述**：負責燈效與 motor，經 I2C 或 RS485 與 Master 溝通；GPIO17 motor UART 是另一條 TX-only 線。
   - **進入點**：`firmware/slave/src/main_slave.cpp`
   - **命令列**：`pio run -e slave1 -t upload`

3. **slave_standalone**：
   - **env**：`slave_standalone`
   - **描述**：沒有 Master，由單板直接使用已配置的 `slaveId` 執行正式 StoryMode。
   - **進入點**：`firmware/slave/src/main_slave.cpp`

上傳`/data`裡的資料到master晶片（用於 wifi-update 網頁）：⚠️ **忽略這步將會使master無法開啓wifi網頁**
`pio run --target uploadfs -e master`
編譯並燒錄晶片：
`pio run --target upload -e master -e slave1 -e slave2`

只編譯，不燒錄 (通常用於測試程式是否有error)：
`pio run -e master -e slave1 -e slave2`

-----------

## PlatformIO 設定

###1.  `platformio.ini` - 共享配置
包含專案的基礎設定，所有開發者共用：

**[env]**：通用環境設定
- `MAX_NUM_SLAVE`：最大 slave 數量
- `DEBUG_ENABLED`：0=不需要Log，1=需要
- `LOG_TIMESTAMPS`：0=不需要log時間，1=需要

**[env:master]**
**[env:slave1-20]**
- `SLAVE_ID`：⚠️ **重要** 每個 slave 都有唯一 ID；目前使用 Slave 1–20，**不可重複！**
- `SLAVE_I2C_ADDR`：I2C 地址必須從 `0x10` 依 Slave ID 順序遞增；目前 Slave 1–20 對應 `0x10`–`0x23`。

### 2. `platformio_local.ini` - master / slave 專案配置
此檔案會進 git，用來保存本專案實際 master / slave 的硬體與編譯環境配置。它只應包含 master / slave / standalone 需要共同追蹤的設定，例如 slave 數量、LED 數量、PCA9685 位址、motor 腳位、story mode 秒數、upload / monitor port。不要在這裡放 WiFi 密碼、私人 token 或只屬於個人電腦的秘密資料。

**[env:master]**
- `WIFI_NAME`：WiFi 名稱
- `ACTUAL_SLAVE_NUM`：實際 slave 數量；目前為 `20`，Slave 19／20 是左右腳掌
- `ENABLE_VIDEO_UART`：是否需要UART螢幕播片
- `ENABLE_POWER_CYCLE_WIFI`：是否啟用連續reboot觸發WiFi功能（預設 0，在 `config.h` 可查看）
- `upload_port`：你正在使用的 Port
- `monitor_port`：與 upload_port 相同
- `STORYMODE_0_V1_TOTAL_SECONDS`: storyMode_0_v1 總時長
- `STORYMODE_0_V2_TOTAL_SECONDS`: storyMode_0_v2 總時長
- `STORYMODE_1_TOTAL_SECONDS`: storymode1 總時長
- `STORYMODE_2_TOTAL_SECONDS`: storymode2 總時長
- `STORYMODE_3_TOTAL_SECONDS`: storymode3 總時長

**[env:slave1-N]**
- `NUM_LEDS_RGB1-18`：彩色 LED 燈珠數目（依實際接線，只填有使用的 RGB strip）
- `ACTUAL_LED_NUM_PCA`：⚠️ **重要** 實際的 pca9685 數量
- `LED_PCA_ADDRESS_1-25`：LED PCA9685 位址（⚠️ **不可與 motor PCA9685 位址重複**）
- `ENABLE_MOTOR_ESP` / `MOTOR_NUM_ESP` / `MOTOR_PIN_0-7`：ESP32 原生 motor PWM 設定
- `ENABLE_MOTOR_PCA` / `MOTOR_NUM_CHANNEL_PCA` / `MOTOR_PCA_ADDRESS`：PCA9685 motor 設定
- `MOTOR_TRANSPORT_UART` / `UART_DC_MOTOR_COUNT` / `UART_DC_MOTOR_ADDR_0-15`：GPIO17 → ATtiny412 TX-only motor 設定；address 為十進制 `1–253`
- `upload_port`：你正在使用的 Port
- `monitor_port`：與 upload_port 相同

⚠️ **重要**⚠️ **如果每個slave的pca9685數量不同/燈效不同，有機會造成slave與slave之間燈效時差**

-----------

## Timer UART 設定
Timer UART 功能用於控制外部 mini monitor 顯示倒數計時。
當 Master 設備從外部計時器裝置接收到 UART 封包時，處理流程如下：

###timer UART格式：

```
[0xB4] [指令/modeId] [brightness] [remainSeconds] [0xFF]
```

--------

### Timer TX → Master

#### 1. WiFi啟動

```
發送：[0xB4, 0x47, <x>, <y>, 0xFF]
功能：打開master wifi
參數：<x>, <y> 為保留參數
master回應：[0xB4, 0x94, <x>, <y>, 0xFF]
```

#### 2. 扭扭光暗

```
發送：[0xB4, <x>, brightness, <y>, 0xFF]
功能：設定燈效光度
參數：
- modeId：故事模式ID
- brightness：亮度值 (0-35)

master回應：[0xB4, <modeId>, <updated_brightness>, <remainSeconds>, 0xFF]
說明：Master收到光暗調節後即時回應最新亮度值作確認
```

#### 3. 指定故事模式

```
發送：[0xB4, modeId, brightness, <y>, 0xFF]
功能：叫slave行下一故事模式
```


-------

### Timer RX ← Master

#### 1. WiFi確認

```
接收：[0xB4, 0x94, <x>, <y>, 0xFF]
說明：Master WiFi AP啟動成功確認
```

#### 2. storymode狀態（每秒更新）

```
接收：[0xB4, <modeId>, <brightness>, <remainSeconds>, 0xFF]

- modeId：故事模式ID
- brightness：當前亮度 (0-35)
- remainingSec：剩餘秒數 (0-255)
  
頻率：Master 會每秒腥一次更新
```

#### 3. 閒置模式（每秒更新）

```
接收：[0xB4, <modeId>, <brightness>, <remainSeconds>, 0xFF]
頻率：Master 會每秒腥一次更新
```

#### 4. 所有slaves不活躍(error)

```
接收：[0xB4, 0x77, <brightness>, 0x00, 0xFF]
說明：當所有slave沒有回應時 （error)
頻率：Master 會每秒腥一次更新
```


### 注意
- `ENABLE_VIDEO_UART` 是用於影片播放功能，與 Timer 無關 
- 若要以外部 UART 取代旋鈕/按鍵控制，請在 `platformio_local.ini` 加入：`-D DISABLE_INPUTS=1`

-----------

## 兩種Wi-Fi 啟動機制


### 方法 1：UART 指令

透過 Timer mon 發送UART 指令：


### 方法 2：reboot Master晶片

1. master 晶片**按reboot鍵**
2. 10 秒內連續reboot 3 次
3. 第 3 次開機時，WiFi 會自動啟動

-----

## Serial Monitor
用來監示晶片的log
1. **master**：`pio device monitor -p /dev/cu.usbmodem21201`
2. **slave1**：`pio device monitor -p /dev/cu.usbmodem21301`
**需要手動更改port no**

-----------

## 程式進入點
- **`main.cpp` `main_slave.cpp`**：這是專案的主要進入點。它初始化硬體、設定網頁伺服器，並處理模式執行的主迴圈。
- **`setup()`**：在程式開始時被呼叫一次。它初始化 LED 燈條、設定 Wi-Fi、網頁伺服器、I2C 等。
- **`loop()`**：在 `setup()` 初始化完成後，不斷循環執行。

---------

## Story Mode 故事模式燈效
Story Mode 是預設的燈效播放系統，允許 master 控制所有 slave 播放同步的燈效。

製作或修改 story mode 前，先讀：

- [docs/storymode/storymode製作標準.md](../../../../docs/storymode/storymode製作標準.md)：製作 workflow、timeslot 描述、general name / effect name 拆分。
- [docs/project/standards/uniform_coding_style.md](../../../../docs/project/standards/uniform_coding_style.md)：story mode、燈效、`lib/`、`patterns/` 的程式碼風格。
- [docs/storymode/storymode目錄.md](../../../../docs/storymode/storymode目錄.md)：現有 story mode 清單與備註。

### 模式介紹
系統內建 4 種燈效模式：
- **Mode 0**：亮點模式 - 隨機亮點效果
- **Mode 1**：正常模式 - 標準燈效展示
- **Mode 2**：長著模式 - 漸進式成長效果
- **Mode 3**：呼吸模式 - 呼吸燈效果
- **Dev Mode**：開發模式 - 藍紫色系漸變效果（slave 斷線時自動進入）

### 播放模式
Story Mode 有兩種播放方式：
1. **Loop Mode**（`isRepeatMode = 0`）
   - 燈效播放一次後停止，等待 master 下一個指令
   - 適合需要精確控制的場景
   
2. **Single Run Mode**（`isRepeatMode = 1`）
   - 燈效持續循環播放，不會停止
   - 適合持續展示的場景

#### 燈效時長設定
- `STORYMODE_0_V1_TOTAL_SECONDS` = 31（亮點模式_v1）
- `STORYMODE_0_V2_TOTAL_SECONDS` = 27（亮點模式）
- `STORYMODE_1_TOTAL_SECONDS` = 176（正常模式）
- `STORYMODE_2_TOTAL_SECONDS` = 158（長著模式）
- `STORYMODE_3_TOTAL_SECONDS` = 158（呼吸模式）
  
### Servo Storymode（伺服故事模式組）
除了 LED 故事模式，系統新增了一組**獨立的 servo storymode set**，可由 Timer 透過 SET 指令的 bit 6 切換（bit6=1 為 SERVO 組，bit6=0 為 LED 組）。兩組共用 `currentModeId`，切換時重置為 0。目前 servo 組只有一個 stub 模式。
架構、切換流程與如何新增 servo 模式：[docs/motor/servo_storymode.md](../../../../docs/motor/servo_storymode.md)

### Servo 可動馬達
每個 slave 可選配伺服馬達（ESP32 原生 LEDC 或 PCA9685 I2C 板），在 `platformio.ini` 用 `-D ENABLE_MOTOR_ESP=1` / `-D ENABLE_MOTOR_PCA=1` 啟用。
詳細設定與 API 參考：[docs/motor/motor_servo.md](../../../../docs/motor/motor_servo.md)

### Slave 斷線處理
- 當 slave 超過 10 秒沒有收到 master 訊號，會自動進入 Dev Mode
- Dev Mode 會顯示藍紫色系漸變效果（#00b8ff → #001eff → #bd00ff → #d600ff），方便識別斷線的 slave
- 當 master 重新連接後，slave 會自動退出 Dev Mode

-------

## Wi-Fi update功能
1. master 晶片開啓 WiFi 後，用手機或電腦，尋找 `WIFI_NAME` 所設定的 Wi-Fi 網路並連接（密碼：`12345678`）。
2. 連線後會自動彈出 captive portal picker 頁。

- `/master` 進入 master update 頁面
- `/slave` 進入 slave update 頁面
  
新程式碼（.bin 的fireware檔案）上傳成功後，晶片會自動restart並運行新的程式碼
