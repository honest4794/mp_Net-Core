# Touch LCD ColorPicker UART 協議

本文件描述 7 寸 ESP32-S3 電容觸控螢幕如何透過 master 既有 UART 腳位控制 live ColorPicker。

核心概念：螢幕板是「遙控器」，master 是「總指揮」。螢幕板不直接控制 LED，只把觸控動作變成 UART 文字指令；master 再轉成現有 `LC:` live ColorPicker I2C 指令送給 slave。

---

## 硬體架構

```text
ESP32-S3 Touch LCD
  LVGL UI / touch
        |
        | UART 3.3V TTL, 115200 8N1
        v
Master ESP32-S3 UART GPIO 5/6
  receiveTimerUART()
        |
        | LC: live ColorPicker over I2C
        v
Slave ESP32-S3
  FastLED / PWM / motor live render
```

## 接線

```text
Touch LCD TXD  -> Master GPIO 5 RX
Touch LCD RXD  -> Master GPIO 6 TX
Touch LCD GND  -> Master GND
Touch LCD 5V   -> 自己的 USB / 5V power supply
Master 3.3V    -> 不供電給 7 寸螢幕
```

注意：

- UART 必須是 3.3V TTL，不可接 RS232 電平。
- 7 寸螢幕耗電較大，不要用 master ESP32-S3 的 3.3V 腳供電。
- 如果 Touch LCD 和原本 Timer mon 都要同時接同一組 RX/TX，硬體上不能直接兩個 TX 並聯；需要 UART switch、tri-state、或只讓其中一個裝置輸出。韌體已可分辨兩種封包，但硬體匯流排仍要避免兩個 TX 同時驅動。

## 與 Timer UART 的分流方式

Master 仍使用同一個 `Serial2`：

```cpp
#define UART_RX_PIN 5
#define UART_TX_PIN 6
```

同一條 UART stream 支援兩種格式：

| 來源 | 格式 | 判斷方式 |
|---|---|---|
| Timer mon | `[0xB4, b1, b2, b3, 0xFF]` | 第一個 byte 是 `0xB4` |
| Touch LCD / other mon | `COMMAND,args...\n` | ASCII 文字行，以 `\n` 結尾 |

Timer 原本功能保留在 `receiveTimerUART()` 裡；新的 Touch command 也在同一個 receive method 裡解析。

## Touch ASCII 指令格式

每個封包是一行 ASCII：

```text
COMMAND,arg1,arg2,arg3\n
```

規則：

- 行尾使用 `\n`，`receiveTimerUART()` 會忽略前面的 `\r`。
- 單行最長 255 字元。
- 數值超出範圍會 clamp，例如 `COLOR,300,-5,20` 會變成 `255,0,20`。
- 有效指令回覆 `OK,...` 或 `PONG`。
- 無效指令回覆 `ERR,<reason>`。

## 指令表

| 指令 | 範例 | 功能 |
|---|---|---|
| `PING` | `PING` | master 回 `PONG` |
| `ENTER` | `ENTER` | 送 `LC:enter`，進入 live ColorPicker |
| `EXIT` | `EXIT` | 送 `LC:exit`，退出 live ColorPicker |
| `TARGET` | `TARGET,all` / `TARGET,3` | 設定後續控制目標 slave |
| `STRIP` | `STRIP,RGB1` | 設定後續 RGB strip |
| `COLOR` | `COLOR,255,0,0` | 送單色 RGB |
| `BRIGHT` | `BRIGHT,180` | 設定 live brightness，範圍 `1-255` |
| `MODE` | `MODE,solid` | 設定 live 模式：`solid` / `palette` / `pattern` |
| `EFFECT` | `EFFECT,RAINBOW` | 選預設效果 |
| `SPEED` | `SPEED,80` | 設定目前 strip speed，範圍 `0-255` |
| `API` | `API,/api/pattern,strip=RGB7&name=WLED+Comet&speed=80` | V2：用 UART 傳 web ColorPicker API body |
| `STATUS?` | `STATUS?` | 回目前 target / strip / speed / live 狀態 |

## V2：Web ColorPicker API over UART

V2 的目的：讓 Touch LCD 的 full ColorPicker UI 不需要重新設計一套協議；它可以把 web ColorPicker 原本會送給 master 的 `/api/...` 和 `application/x-www-form-urlencoded` body，改成一行 UART 文字。

格式：

```text
API,<path>,<urlencoded-body>\n
```

範例：

```text
API,/api/enable,value=1
API,/api/color,target=all&strip=RGB7&r=255&g=0&b=0
API,/api/brightness,value=180
API,/api/palette,strip=RGB7&name=Fire
API,/api/mode,strip=RGB7&value=pattern
API,/api/pattern,strip=RGB7&name=WLED+Comet&speed=80&intensity=128&paletteName=Fire&trail=200&custom1=90&color=%23FF3300
API,/api/pwm,effect=flash&brightness=180&channels=pcaLed.0,pcaMotor.2,espMotor.1
API,/api/specificcolor,index=0&effect=0&r=255&g=0&b=0
API,/api/pwm_all_off,
API,/api/storymode,value=demo
API,/api/seq/stop,
API,/api/audio,active=1&source=mic
API,/api/matrix,effect=Dynamic+Flow&width=8&height=8&mapping=1&speed=4&targetStrip=RGB1
API,/api/storyparam,ns=storyMode_demo&name=brightness&value=128
```

Master 目前會把這些 API 轉成既有 `LC:` live 指令：

### Runtime Sequencer 轉發

Touch MON 可透過相同 `API,<path>,<body>` 格式控制已儲存在 Master 的 sequence：

```text
API,/api/seq/list,
API,/api/seq/play,slot=0
API,/api/seq/stop,
```

- `/api/seq/list`：Master 回 `SEQ_LIST,<slotMask>,<playing>,<currentSlot>`，MON HTTP bridge 轉成 JSON。
- `/api/seq/play`、`/api/seq/stop`：Master 回 `OK,SEQ,...`。
- `/api/seq/upload` 與 `/api/seq/get` 不經 Touch UART；timeline/JSON 可能超過 MON 的 768-byte HTTP→UART buffer。Touch web 會隱藏 upload。
- 端點完整規格見 `docs/colorpicker/sequencer.md`。

| API | Master 轉成的 `LC:` |
|---|---|
| `/api/enable` | `LC:enter` / `LC:exit` |
| `/api/brightness` | `LC:bright,<value>` |
| `/api/color` | `LC:rgb,<strip>,r,g,b` |
| `/api/palette` | `LC:pal,<strip>,palette` |
| `/api/speed` | `LC:spd,<strip>,value` |
| `/api/mode` | `LC:mode,<strip>,0/1/2` |
| `/api/stripbright` | `LC:sb,<strip>,value` |
| `/api/numleds` | `LC:nl,<strip>,value` |
| `/api/pattern` | `LC:pat,<strip>,patternId,speed,intensity,palette` + `LC:patx,<strip>,key,value` |
| `/api/pwm` | `LC:pwm,<kind>,channel,effect,duty,address,min,period,phase,stopBefore,stopAfter` |
| `/api/specificcolor` | `LC:sc` / `LC:scp` / `LC:scc` |
| `/api/pwm_all_off` | `LC:pwmoff` |
| `/api/storymode` | `LC:exit` |

`LC:pwm` 的 `address=00` 表示直接使用 `espLed[]` / `pcaLed[]` channel index；PCA address 若屬於韌體已配置的 LED PCA 板，slave 會先映射回 `pcaLed[]`，再經 channel staging 執行 `ch` effect。`min / period / phase / stopBefore / stopAfter` 對應 `chSmoothBeatsin16` 的原始參數。舊的四欄或五欄短格式仍可使用，缺少的效果參數會套用既有預設值。

Touch LCD 的 GCraft 導覽為 `Home / Zones / Scenes / Sequence`，其餘測試頁集中在 `Advanced`。以下端點可由 MON 通用 `API,` 格式送出，但實際效果取決於 master 對應 handler：

| LVGL 頁面 | API | 現況 |
|---|---|---|
| Home | `/api/enable`、`/api/brightness` | master 已支援 |
| Scenes | `/api/storymode`、`/api/seq/stop` | sequence stop 已支援；Touch UART 目前忽略 story ID，只會退出 live mode |
| Matrix | `/api/matrix` | MON 會送出完整 web 同款 body；Touch UART parser 目前回 `ERR,bad_api` |
| VU | `/api/audio`、`/api/numleds`、`/api/mode`、`/api/pattern` | 後三項已支援；`/api/audio` 目前回 `ERR,bad_api` |
| Configuration | `/api/storyparam` | Touch UART parser 目前回 `ERR,bad_api` |

Zones 沒有 `/api/state` 反向同步；LCD 使用 `kUiStrips` 顯示靜態硬體配置，live 狀態仍以手機 ColorPicker 為準。

### PCA9685 scan 補充

`/api/pwm_scan` 使用 PWM I2C bus，不使用 master/slave 控制用的 `I2C_SDA_PIN` / `I2C_SCL_PIN`。

預設腳位：

```text
PWM_SDA_PIN = 5
PWM_SCL_PIN = 6
```

使用者可在 UI 輸入 `sda` / `scl` 後按 scan。master 會向目前選到的 slave 送內部 I2C info request：

```text
INFO:PSC:<sda>,<scl>
```

舊格式 `INFO:PSC` 仍有效，slave 會用預設 `PWM_SDA_PIN` / `PWM_SCL_PIN` 掃描 `0x40-0x7F`。若沒有掃到 PCA9685，ColorPicker UI 會顯示 fallback：`0x40 pcaLed`、`4 espLed`、`4 espMotor`，讓 UI 仍可編輯與匯出設定。

### V2.1 Pattern Parameter Protocol

V2.1 會把 `/api/pattern` body 裡除了 base 欄位以外的 pattern 私有參數送到 slave。

Base 欄位：

```text
target, strip, name, idx, id, patternId, speed, intensity, palette, paletteName
```

這些欄位會合併成：

```text
LC:pat,<strip>,<patternId>,<speed>,<intensity>,<palette>
```

其他欄位會逐一送成：

```text
LC:patx,<strip>,<key>,<value>
```

範例：

```text
API,/api/pattern,strip=RGB7&name=WLED+Comet&speed=80&intensity=128&trail=200&custom1=90&color=%23FF3300

Master -> Slave:
LC:pat,RGB7,27,80,128,0
LC:patx,RGB7,trail,200
LC:patx,RGB7,custom1,90
LC:patx,RGB7,color,#FF3300
```

Slave 收到 `LC:pat` 時會切換 pattern 並清除該 strip 舊的 `patx` 參數；後續 `LC:patx` 會保存到該 strip 的 live parameter buffer。已支援立即套用的常用參數包含：

```text
color, colorR/G/B, cometColor, trail, custom1, custom2, custom3,
segments, fade, meteorSize, smooth, gradient, direction,
reverseDirection, isReverse, bpm, speedDelay, duration,
twinkleSpeed, twinkleDensity, flameHeight, sparks,
tailRange, headRange, diffusionRange, inSpeed, outSpeed,
fullDuration, fadeSpeed
```

重要限制：

- V2.1 已把 pattern 私有參數搬到 UART/I2C live 協議；不是每個舊 pattern 函式都已使用所有 key。未映射的 key 會保存在 slave buffer，但不會改變畫面。
- 每個 strip 目前保存最多 16 個 `patx` key/value。單一 key 最長 23 字元，value 最長 39 字元。
- 如果 LCD firmware 已知道 pattern id，可用 `patternId=<id>`；如果使用 web body 的 `name=WLED+Comet`，實機 master 會用 `colorpicker.cpp` 的完整 pattern 清單解析名稱。

## 目前支援的 target / strip

Target：

```text
all
1-20
```

Strip：

```text
RGB1, RGB2, RGB3, RGB4,
RGB7, RGB8, RGB9, RGB10, RGB11, RGB12, RGB13,
RGB16, RGB17, RGB18
```

## Effect mapping

| Touch 指令 | Master 轉成的 `LC:` 指令 |
|---|---|
| `EFFECT,SOLID` | `LC:mode,<strip>,0` |
| `EFFECT,RAINBOW` | `LC:pal,<strip>,0` + `LC:mode,<strip>,1` |
| `EFFECT,FIRE` | `LC:pal,<strip>,3` + `LC:mode,<strip>,1` |
| `EFFECT,COMET` | `LC:pat,<strip>,27,<speed>,128,0` |
| `EFFECT,BPM` | `LC:pat,<strip>,23,<speed>,128,0` |
| `EFFECT,OFF` | `LC:rgb,<strip>,0,0,0` |

## 範例

```text
LCD -> Master: PING
Master -> LCD: PONG

LCD -> Master: TARGET,all
Master -> LCD: OK,TARGET,all

LCD -> Master: STRIP,RGB7
Master -> LCD: OK,STRIP,RGB7

LCD -> Master: COLOR,255,0,0
Master -> LCD: OK,COLOR
Master -> Slave: LC:enter
Master -> Slave: LC:rgb,RGB7,255,0,0

LCD -> Master: SPEED,80
Master -> LCD: OK,SPEED
Master -> Slave: LC:spd,RGB7,80

LCD -> Master: EFFECT,COMET
Master -> LCD: OK,EFFECT,COMET
Master -> Slave: LC:pat,RGB7,27,80,128,0
```

## 程式驗證流程

核心概念：現在沒有 Touch LCD / mon 時，電腦可以先假裝「控制器」，從 USB Serial 丟指令給 master；master 再照正常流程送給 slave。

### 只有 master + slave，沒有 mon

先燒好 master 和 slave，確認 I2C 已接好、slave 在 master log 裡是 active。然後找 master 的 USB serial port：

```bash
ls /dev/cu.* | grep -E 'usbmodem|usbserial'
```

執行：

```bash
python3 scripts/validate_colorpicker_uart_workflow.py --master-usb-port /dev/cu.usbmodemXXXX --target all
```

這條路徑是：

```text
電腦 USB Serial
  -> Master Serial: LCUSB:<target>:LC:...
  -> Master broadcastLiveCommand()
  -> I2C
  -> Slave live ColorPicker receiver
```

腳本會確認 master 回：

```json
{"ok":true,"type":"colorpicker_usb","sent":1}
```

`sent > 0` 代表 master 有把 command 送到 active slave。因為 slave 目前沒有反向 ack，LED / PWM 是否真的動作仍要目視、看 slave log，或用 logic analyzer 確認。

如果只是想測 master USB parser、不要求 slave active，可以加：

```bash
python3 scripts/validate_colorpicker_uart_workflow.py --master-usb-port /dev/cu.usbmodemXXXX --allow-zero-sent
```

### 有 mon / Touch LCD / USB-TTL 後

接到 master GPIO 5/6 後，再測真正的 Touch UART input：

```bash
python3 scripts/validate_colorpicker_uart_workflow.py --port /dev/cu.usbserial-XXXX
```

這條路徑是：

```text
Touch LCD / mon / USB-TTL
  -> Master GPIO 5 RX / GPIO 6 TX
  -> receiveTimerUART()
  -> touchColorCommand parser
  -> LC: live ColorPicker over I2C
  -> Slave
```

## 實作位置

- Parser：`firmware/master/include/touchColorCommand.h`
- Parser implementation：`firmware/master/src/touchColorCommand.cpp`
- UART stream 分流：`firmware/master/src/uartController.cpp`
- Live ColorPicker I2C 轉發：`firmware/master/src/colorpicker.cpp`
- Parser host test：`firmware/master/tests/test_touchColorCommand.cpp`

## 測試指令

完整 workflow validator：

```bash
python3 scripts/validate_colorpicker_uart_workflow.py
```

這個 dry-run 會：

- 從 `web/script.js` 抽出 ColorPicker fallback pattern / palette 清單。
- 從 `firmware/master/src/colorpicker.cpp` 抽出 firmware pattern 清單。
- 確認 web fallback pattern 名稱可被 master firmware 解析。
- 編譯一個臨時 host test，使用真實 `touchColorCommand.cpp` parser。
- 測基本頁面 API：enable、color、brightness、palette、speed、mode、strip brightness、num leds、PWM、SpecificColor、storymode。
- 對 firmware 內全部 RGB pattern 產生 `/api/pattern` UART body，並確認會輸出 `LC:pat` + `LC:patx`。

實機 UART workflow 測試：

```bash
python3 scripts/validate_colorpicker_uart_workflow.py --port /dev/cu.usbserial-XXXX
```

如果要把全部 pattern 都送到實機：

```bash
python3 scripts/validate_colorpicker_uart_workflow.py --port /dev/cu.usbserial-XXXX --full-hardware
```

實機接法：

```text
USB-TTL TX  -> Master GPIO 5 RX
USB-TTL RX  -> Master GPIO 6 TX
USB-TTL GND -> Master GND
```

實機 validator 會檢查 master UART 回覆 `PONG` / `OK,...`。這代表：

```text
test program -> master UART parser -> master accepted command
```

Master 到 slave 的 I2C 傳送會由 master 韌體執行；目前 slave live ColorPicker 沒有反向 ack 到 master，所以「slave 真的亮燈 / PWM 真的動作」需要其中一種外部確認：

- 直接看 LED / PWM / servo 是否改變。
- 看 master USB serial log 裡的 `TOUCH_UART` / `CP_PAT` / `CP_PATX` I2C send log。
- 用 logic analyzer 量 I2C 或量 LED/PWM output。

Host parser test：

```bash
g++ -std=c++17 -I firmware/master/include \
  firmware/master/tests/test_touchColorCommand.cpp \
  firmware/master/src/touchColorCommand.cpp \
  -o /tmp/test_touchColorCommand && /tmp/test_touchColorCommand
```

Firmware build：

```bash
arch -arm64 pio run -e master
arch -arm64 pio run -e slave1 -e slave_standalone
```
