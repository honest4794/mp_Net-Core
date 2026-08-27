
## <span style="color: green;">✅ 懶人包 ✅ 編輯storymode留意事項checklist</span>

1. 到`platformio_local.ini` 更改每個storymode長度（秒數）：
```cpp
-D STORYMODE_0_V1_TOTAL_SECONDS=31
-D STORYMODE_0_V2_TOTAL_SECONDS=27
-D STORYMODE_1_TOTAL_SECONDS=176
-D STORYMODE_2_TOTAL_SECONDS=158
-D STORYMODE_3_TOTAL_SECONDS=158
```
2. Timer螢幕的韌體也要溝通好長度，2邊數值**必須對齊**
3. 到`config.h` 查看 `BRIGHTNESS_SLOTS` 的數值，是否與Timer螢幕的韌體一致。
4. 若需要某個 storymode 循環播放，Timer 發送 modeId 時將 bit 7 設為 1（例如 modeId 1 循環 → 發送 0x81）
5. b1 的 bit 6 選擇故事模式組：bit6=1 為 SERVO 組，bit6=0 為 LED 組；modeId 範圍為 0-63（bit5-0）

-----

timer UART格式：

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
- brightness：亮度值 (0-31)

master回應：[0xB4, <modeId>, <updated_brightness>, <remainSeconds>, 0xFF]
說明：Master收到光暗調節後即時回應最新亮度值作確認
```

#### 3. 指定故事模式

```
發送：[0xB4, modeId, brightness, <y>, 0xFF]
功能：叫slave行下一故事模式

modeId byte 格式：
  bit 7      = loop flag (1: 循環該 mode 直到收到新指令, 0: 正常播完進下一 mode)
  bit 6      = story set (1: SERVO 組, 0: LED 組)
  bit 5-0    = 實際 modeId (0-63)

範例：
  0x02  = LED 組, modeId 2，正常播放
  0x40  = SERVO 組, modeId 0，正常播放
  0x42  = SERVO 組, modeId 2，正常播放
  0xC2  = SERVO 組, modeId 2，循環播放

注意：b1 的 bit7=loop、bit6=set，modeId 僅佔 bit5-0。未來新增 Timer→Master 保留指令碼必須先做指令過濾，且應避開會被誤判的範圍（bit7 → loop、bit6 → SERVO set）。
```

#### 4. 切換 servo/LED 故事模式組

```
切換方式：在 SET 指令的 b1 byte 中以 bit 6 表示（絕對狀態，非 toggle）
  bit 6 = 1 → SERVO 組
  bit 6 = 0 → LED 組

說明：Master 收到 SET 指令時，若 bit6 與當前 activeStorySet 不同，
      LED → SERVO 會切到 SERVO 組 modeId 0，該指令 bit5-0 帶的
      modeId 會被忽略，Master 會記錄當時 LED mode，等 SERVO 組跑完後
      回到下一個 LED mode（例：從 LED mode 3 進入 SERVO，完成後回 LED mode 4）。
      SERVO → LED 不會立即切 LED，而是先停留在 SERVO 組並跳到最後一個
      mode（`storyMode_motor_reset`）執行復位；reset 完成後才自動切回 LED 組。
      若已在 SERVO 最後一個 mode，Master 會忽略新的 SET frame，避免中斷關閉馬達。
      進入同一組後，後續 SET 指令再用
      bit5-0 選 mode。無需獨立切換指令——每次 SET 指令均帶有組別狀態。

byte 範例：
  0x40 = 切到 SERVO 組（從 modeId 0 起；bit5-0 此時忽略）
  0x42 = 切到 SERVO 組時 → 仍從 modeId 0 起；
         已在 SERVO 組時 → 跑 modeId 2，正常播放
  0xC2 = 已在 SERVO 組時 → modeId 2，循環播放
  0x02 = 已在 LED 組時   → modeId 2，正常播放
  0x02 = 已在 SERVO 組時 → 先跑 `storyMode_motor_reset`，完成後回 LED 組
  0x42 = 已在 SERVO 最後一個 mode 時 → 忽略，維持最後一個 mode 到完成
```

-------

### Timer RX ← Master

> ⚠️ **重要：保留指令碼**
> Master TX 給 Timer 時，第 2 個 byte 可能是以下「保留指令碼」之一，**必須先做指令過濾再做 bit 解析**：
> - `0x94` = WiFi 啟動確認 (bit 7=1，但**不是** loop flag)
> - `0x77` = slaves 不活躍 error (bit 7=0，但**不是** modeId)
>
> Timer 端解析流程建議：
> ```
> if (b1 == 0x94) → WiFi ACK
> else if (b1 == 0x77) → slaves error
> else → 一般 storymode 狀態：loop = (b1 & 0x80), set = (b1 & 0x40), modeId = (b1 & 0x3F)
> ```

#### 1. WiFi確認

```
接收：[0xB4, 0x94, <x>, <y>, 0xFF]
說明：Master WiFi AP啟動成功確認
```

#### 2. storymode狀態（每秒更新）

```
接收：[0xB4, <modeId>, <brightness>, <remainSeconds>, 0xFF]

- modeId byte 格式：
    bit 7      = loop flag (1: master 正在 loop 該 mode, 0: 正常)
    bit 6      = story set (1: SERVO 組, 0: LED 組)
    bit 5-0    = 實際 modeId (0-63)
- brightness：當前亮度 (0-31)
- remainingSec：剩餘秒數 (0-255)

注意：bit5-0 = 0x3F (63) 為保留值，代表 master 目前無 active mode
      （開機尚未起 mode 等）。Timer 收到越界 modeId 應忽略、維持現狀，
      不要更新顯示。

頻率：Master 會每秒腥一次更新
```

#### 3. 閒置模式（每秒更新）

```
接收：[0xB4, <modeId>, <brightness>, <remainSeconds>, 0xFF]
（modeId byte 格式同上：bit 7 = loop flag, bit 6 = set, bit 5-0 = modeId）
頻率：Master 會每秒腥一次更新
```

#### 4. 所有slaves不活躍(error)

```
接收：[0xB4, 0x77, <brightness>, 0x00, 0xFF]
說明：當所有slave沒有回應時 （error)
頻率：Master 會每秒腥一次更新
```

-------

### 注意
- `ENABLE_VIDEO_UART` 是用於影片播放功能，與 Timer 無關
- 若要以外部 UART 取代旋鈕/按鍵控制，請在 `platformio_local.ini` 加入：`-D DISABLE_INPUTS=1`
