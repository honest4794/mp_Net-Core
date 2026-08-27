# UART DC Motor（GPIO17 → ATtiny412）Codex Agent Handoff

日期：2026-08-13

狀態：HiNu GPIO17 driver、三款 pattern 與 ColorPicker live control 已實作；硬件仍屬 open-loop，沒有 ATtiny ACK

閱讀者：下一個負責 HiNu Gundam UART DC motor 的 Codex agent

## 1. 一句話目標

ESP32-S3-Tiny 的 Slave 使用獨立 `GPIO17 TX`，以 9600 baud 將 3-byte UART
指令直接送到 ATtiny412 motor boards。

## 2. 固定 GPIO17 motor path

這份文件只負責以下 motor path：

```text
Slave（ESP32-S3-Tiny）
        │ 普通 UART TX-only：GPIO17、9600 8-N-1
        ▼
  多塊 ATtiny412 motor boards
        │ PA2 / PA3 PWM
        ▼
      DC motors
```

Motor path 的完整責任只有：

| Sender | Wire | Receiver | Protocol |
|---|---|---|---|
| ESP32-S3-Tiny Slave | GPIO17 TX + common GND | 每塊 ATtiny412 PA1 | `0xFF, address, value` |

硬性規則：

- GPIO17 本身沒有 ACK 或 RTT；motor timeline 仍要使用外部同步服務提供的校正時間。
- 本設計不使用 standalone UART。
- Motor UART 必須使用自己的 `HardwareSerial` instance。
- USB debug `Serial` 不可當作 GPIO17 motor UART。
- Master↔Slave 通訊與 OTA 由其他 spec 負責；本文件不定義其 GPIO、frame 或 function。

## 3. UART_Learning session 總結

來源 project 將每份 assignment 分成獨立 root branch：

| Assignment | Branch | 完成內容 |
|---|---|---|
| 1 | `assignment-1-conversion` | decimal／hex／binary conversion 基礎 |
| 2 | `assignment-2-uart-string` | Device 1 傳 string、Device 2 回 ACK |
| 3 | `assignment-3-rtt-button` | GPIO2 button、持續 send、每秒 log、Success/Fail、RTT |
| 4 | `assignment-4-dc-motor` | 簡單直接的 ATtiny motor UART 控制 |
| 4 Part 2 | `assignment-4-part-2` | CRC packet、ring buffer、ACK、RTT、watchdog、多 motor、linear VALUE profile |

Assignment 4 Part 2 最後形成兩層通訊：

```text
Device 1 ↔ Device 2：可靠 duplex packet
Device 2 → ATtiny：簡單 3-byte TX-only motor frame
```

HiNu project 只應借用以下部分：

- ATtiny412 的 direct motor frame。
- address／direction／speed 到 raw VALUE 的轉換。
- 非阻塞 `millis()` linear OPEN → HOLD → CLOSE profile。
- startup Mode 0 homing、reboot／OTA STOP、安全 log 語意。

HiNu GPIO17 motor link不應複製以下 Device 1↔Device 2 功能：

- `0xAA 0x55` packet header。
- CRC-16 packet。
- sequence number。
- ACK／RTT。
- RX ring buffer／packet parser。

那些功能是 duplex ESP-to-ESP link 的責任，不是 ATtiny motor wire protocol。

## 4. ATtiny412 是唯一 motor protocol 依據

參考 firmware 是 UART_Learning project 的 `reference/UART-412.ino`。不要搬移或
修改該 `.ino` 來遷就 HiNu；ESP32 sender 必須相容它現有的接收方式。

### 4.1 ATtiny412 pins

```text
//   ----\_/----
//  | VCC   GND |
//  | PA6   PA3 |  PA3 = IN2 motor PWM
//  | PA7   PA0 |
//  | PA1   PA2 |  PA1 = UART input, PA2 = IN1 motor PWM
//   -----------
```

| ATtiny pin | 用途 |
|---|---|
| `PA1` | `PWM_INPUT_PIN`，實際上是 software UART RX input |
| `PA2` | Motor IN1 direction/PWM |
| `PA3` | Motor IN2 direction/PWM |

### 4.2 UART electrical/timing settings

ATtiny code 使用：

```cpp
#define F_CPU 20000000UL
#define PERIOD 102  // 9600 baud
```

ESP32 sender 必須設定：

```text
Baud：9600
Data bits：8
Parity：None
Stop bits：1
方向：ESP32 TX-only → ATtiny PA1
```

即 Arduino 寫法：

```cpp
motorSerial.begin(9600, SERIAL_8N1, -1, 17);
```

`RX pin = -1`，因為 motor board 不會回資料。

ATtiny `getValue()` 的工作方式：

1. 等 PA1 由 idle HIGH 轉成 start bit LOW。
2. 等約 1.5 bit time，去到第一個 data bit 中心。
3. 每隔一個 bit time sample 一次，共讀 8 bits。
4. UART data 是 LSB-first；shift 邏輯最後重建一個 `uint8_t`。

它沒有檢查 parity、framing error 或 stop bit，也不會回 ACK。

### 4.3 每塊板的 address

原始 `UART-412.ino` 參考檔使用：

```cpp
#define ADDR 21  // decimal 21 = 0x15
```

HiNu 實機改用以下 decimal addresses；每塊 ATtiny firmware 要有唯一 `ADDR`：

```text
Slave 17 motor board 1：ADDR 19 decimal = 0x13
Slave 17 motor board 2：ADDR 15 decimal = 0x0F
Slave 18 motor board：ADDR 21 decimal = 0x15
```

注意：以上地址都是十進制。`19` 會傳成 `0x13`；`15` 會傳成 `0x0F`；
`21` 會傳成 `0x15`。

所有 motor board 的 PA1 可以並聯到同一條 Slave GPIO17 TX。每塊板都會看見所有
frame，但只有 address 相同的板才更新輸出。

### 4.4 Direct frame：正式建議使用

格式固定 3 bytes：

```text
[HEADER 0xFF] [ADDRESS] [VALUE]
```

例子：

```text
停止 decimal address 21：0xFF → 0x15 → 0x80
Direction A Close 全速：0xFF → 0x15 → 0x00
Direction B Open 全速： 0xFF → 0x15 → 0xFF
```

Direct frame 沒有 `0xFE` ending。三個 bytes 送完就是完整 command。

### 4.5 Broadcast frame：先保留，不作第一版主要介面

ATtiny 也支援：

```text
0xFF → 0x00 → value(address 1) → ... → value(address 32) → 0xFE
```

每塊板按照自己的 address 取對應位置。這條 frame 較長、較難 debug；第一版建議
逐個 address 傳 direct frame。兩個 motor 的 direct frames 在 9600 baud 只需約
6.25 ms，遠低於 100 ms send interval。

## 5. VALUE、方向與 PWM

ATtiny 的 `VALUE` 不是普通 0–255 brightness。`128` 是中心 STOP；中心兩側代表
相反方向。

ATtiny 實際程式：

```cpp
if (motorValue < 128) {
  analogWrite(IN2_PIN, 0);
  analogWrite(IN1_PIN, (127 - motorValue) * 2);
} else {
  analogWrite(IN1_PIN, 0);
  analogWrite(IN2_PIN, (motorValue - 128) * 2);
}
```

對照表：

| VALUE | IN1 PWM | IN2 PWM | 結果 |
|---:|---:|---:|---|
| `0` | `254` | `0` | 方向 A，接近全速 |
| `64` | `126` | `0` | 方向 A，約半速 |
| `126` | `2` | `0` | 方向 A，極慢 |
| `127` | `0` | `0` | STOP |
| `128` | `0` | `0` | STOP；全 project 統一使用這個值 |
| `129` | `0` | `2` | 方向 B，極慢 |
| `192` | `0` | `128` | 方向 B，約半速 |
| `255` | `0` | `254` | 方向 B，接近全速 |

一般機械的「開／關」取決於 motor 接線；Hi-Nu 實機方向已由下節固定，不再交換。

### 5.1 Hi-Nu 實機方向確認（2026-08-14）

Slave 17（ATtiny412 decimal address `19`）及 Slave 18（decimal address `21`）以
GPIO17 實機測試後，兩邊方向一致：

| Direction | Hi-Nu 機械動作 |
|---|---|
| `Direction A` | **Close／收回** |
| `Direction B` | **Open／打開** |

端點測試流程為：Direction A 100% 10 秒 → STOP 2 秒 → Direction B 100% 10 秒
→ final STOP；兩個 motor 均完成相同動作。正式 StoryMode／Pattern 必須使用以上
語意，不可再以未確認方向處理。

### 5.2 Beginner-facing percentage mapping

公開 interface 應收 direction + `0..100%`，由 module 計算 VALUE：

```text
speed = 0：VALUE = 128
Direction A：VALUE = 128 - round(128 × speed / 100)
Direction B：VALUE = 128 + round(127 × speed / 100)
```

結果：

| Input | VALUE |
|---|---:|
| A, 100% | `0` |
| A, 50% | `64` |
| A, 1% | `127` |
| 任一方向, 0% | `128` |
| B, 1% | `129` |
| B, 50% | `192` |
| B, 100% | `255` |

### 5.3 Dead zone

ATtiny comment 不等於真正實作了 45%–55% dead zone。現有 code 明確輸出零 PWM
的 raw values 只有 `127` 和 `128`。

Motor 在 `120..136` 附近可能因摩擦、負載或供電而不動，這是物理 dead zone，
不是 firmware 保證。Linear profile 應照樣逐步通過這些 VALUE，不要暗中由 STOP
跳到 10% 或其他 minimum speed。

## 6. Linear motor profile

目標曲線：

```text
OPEN：  VALUE 128 線性走到 direction peak
HOLD：  保持 peak；motor 仍然通電／運轉
CLOSE：由 peak 線性返回 VALUE 128
STOP：  繼續送 VALUE 128
```

### 6.1 Hi-Nu 機械動作 Pattern

`patterns_uart_dc_motor` 提供三款非阻塞速度曲線。三款都使用相同安全流程：

```text
Direction A Close 歸零 → STOP 2 秒
→ Direction B Open（曲線速度）→ STOP 2 秒
→ Direction A Close（同款曲線）→ final STOP
```

| Pattern | 動作感覺 | 建議 Open／Close 時間 |
|---|---|---:|
| `Sine` | 最柔順；慢 → 快 → 慢 | 各 15.7 秒 |
| `SmoothMechanical` | 起步較有力，中段穩定，尾段慢速定位 | 各 13.4 秒 |
| `HydraulicCinematic` | 短暫解鎖、主行程、慢速落位 | 各 15 秒 |

時間比原本 100% 固定速度的 10 秒長，是因為變速曲線的平均速度較低；目標是保留
近似相同行程，而不是提早換方向。Pattern 不強制最低速度，讓實機摩擦／負載的
dead zone 可以直接觀察，再按機構逐款調校。

三款效果各有一個函式，不再加第四個 effect wrapper：

```cpp
uartDcMotorSineCommand(address, speedPercent, speedCurve,
                       elapsedMs, durationMs,
                       &direction, &value);
uartDcMotorSmoothMechanicalCommand(address, speedPercent, speedCurve,
                                   elapsedMs, durationMs,
                                   &direction, &value);
uartDcMotorHydraulicCinematicCommand(address, speedPercent, speedCurve,
                                     elapsedMs, durationMs,
                                     &direction, &value);
```

`direction` 先由呼叫端設為 A 或 B；函式驗證 decimal address、計算曲線 speed，並將
ATtiny raw `VALUE` 寫入 `value`。Story Mode 再直接把該 VALUE staging 到已配置 motor。
`speedPercent` 是最高速度；`speedCurve` 可選 `Linear`、`Sine` 或 `Logarithmic`。
效果參數放在 `storyMode_parameter`，不放入 PlatformIO `-D` build flags。

Slave 19／20 的 `storyMode_dev` 使用以下非阻塞測試循環：

```text
Direction A Close / Sine effect + Sine speed curve 10 秒 → VALUE 128 STOP 3 秒
→ Direction B Open / Sine effect + Sine speed curve 10 秒 → VALUE 128 STOP 3 秒 → loop
```

Slave 19 使用既有 `UART_DC_MOTOR_ADDR_0=22`；Slave 20 使用既有
`UART_DC_MOTOR_ADDR_0=21`。Master 恢復或收到正式 Mode command 時必須立即
`uartDcMotorStopAll(true)`，不可保留 Dev Mode 最後一次 movement VALUE。

### 6.2 Direction A/B 換向的 20 ms 待驗證下限（2026-08-20）

現場回報在 `9600 baud` 測試時，Direction A/B 來回切換要預留約 `20 ms` 才穩定。
這裡的「切換方向」是 **motor Direction A ↔ Direction B**，不是 UART TX/RX turnaround：
GPIO17 motor link 固定為 TX-only、`RX=-1`，沒有 ATtiny ACK 或回傳方向。

候選安全序列：

```text
Direction A → STOP（VALUE 128）→ wait ≥ 20 ms → Direction B
Direction B → STOP（VALUE 128）→ wait ≥ 20 ms → Direction A
```

`20 ms` 目前只是單次實測的候選下限，不是已定案的 protocol constant。3-byte frame
在 9600 8-N-1 約需 `3.125 ms`；額外時間可能來自 ATtiny control loop、H-bridge
dead time 或機械反應，必須用 logic analyzer／scope 配合實機重複測試確認。

現行 `uartDcMotorService()` 每 `100 ms` 重送，正式 Pattern 的 STOP dwell 為數秒，均已
大於 20 ms；不可把既有 2／3／5 秒機械停頓縮短成 20 ms。若新增 direct／live 快速換向
路徑，必須明確送 VALUE 128 並通過下方換向矩陣後才可交付。

State machine 應是 non-blocking。Mode 0 完成前，任何 Story Mode motor request 都只可
排隊或被拒絕，不可提早輸出：

```text
Mode0ClosingB → Mode0Stopped → Mode0Ready
                               ↓
                   Opening → Holding → Closing → Stopped → Opening ...
```

使用 rollover-safe elapsed time：

```cpp
if (nowMs - phaseStartedAtMs >= durationMs) {
  // next phase
}
```

不要使用 `delay(10000)`。HiNu RGB/story frame 必須繼續更新。

Linear interpolation 要用 elapsed time，不用 loop count：

```text
progress = min(elapsedMs, durationMs)
value = startValue + (targetValue - startValue) × progress / durationMs
```

Direction A 計算會向下走，實作應使用 signed／足夠寬的 intermediate，避免 unsigned
underflow。Exact phase boundary 必須得到 exact target VALUE。

## 7. `write`、`read`、`push`、`pop`

### 7.1 `HardwareSerial.write()`

Motor TX path 真正需要的是 `write()`：

```cpp
uint8_t frame[3] = {0xFF, address, value};
const size_t accepted = motorSerial.write(frame, sizeof(frame));
const bool queued = accepted == sizeof(frame);
```

白話：`write()` 把 bytes 交給 ESP32 UART TX driver，driver 再逐 bit 送到 GPIO17。

在 9600 8-N-1：

```text
每 byte = 1 start + 8 data + 1 stop = 10 bits
3 bytes = 30 bits
30 / 9600 ≈ 3.125 ms
```

`write()` 回傳 3，只代表三個 bytes 已被 ESP32 TX 接受；不代表 ATtiny 已正確收到，
更不代表 motor 已動。Log 應寫 `QUEUED`／`TX OK`，不能假稱 `APPLIED` 或 `ACK`。

`flush()` 會等待 TX wire 真正送完，屬 blocking call。正常每 100 ms send 不必每次
flush；在準備 reboot／OTA 的最後 STOP frame，可用一次 `flush()` 確保 STOP 已離開
ESP32，成本約數毫秒。

### 7.2 `HardwareSerial.read()`

`read()` 從 UART RX driver 取走最舊的一個 byte：

```cpp
if (uart.available() > 0) {
  int byte = uart.read();
}
```

GPIO17 motor link是 TX-only，`RX=-1`，所以這條路徑不應呼叫 `read()`。如果其他
module 有雙向 UART，它應在自己的 spec 說明 RX 與 parser，不應把該 code 放入 motor
module。

### 7.3 `push()`／`pop()` 是 software queue，不是 UART methods

Arduino `HardwareSerial` 沒有本 project 所說的公開 `uart.push()`／`uart.pop()`。
UART_Learning 的 `push/pop` 是自訂 fixed-size FIFO ring buffer：

```text
wire → uart.read() → queue.push(byte)
                     queue.pop(byte) → parser
```

- `push(byte)`：把新 byte 放到 queue 尾部；queue full 時回 `false`。
- `pop(byte)`：取出並刪除 queue 最前面的 byte；queue empty 時回 `false`。
- FIFO：First In, First Out。先 push 的 byte 必定先 pop。

Ring buffer 以 `readIndex`、`writeIndex`、`count` 工作：

```text
push：寫入 writeIndex → writeIndex 繞圈前進 → count + 1
pop：  讀取 readIndex  → readIndex 繞圈前進  → count - 1
```

使用場景：

| Link | `read` | software `push/pop` | `write` |
|---|---|---|---|
| GPIO17 → ATtiny motor | 不需要 | 不需要 | 需要 |
| USB log | 可收 console command | 通常不需要自訂 ring buffer | 需要 |

不要為了「保留 UART_Learning 功能」而將 RX queue、CRC parser 塞入 TX-only motor
module。這會增加 code，但不會增加 motor link 的可靠性。

## 8. Motor UART module 建議 seam

這是一個真正的 hardware adapter，不是只包一行效果的 story-mode wrapper。

建議位置：

```text
firmware/shared/include/motor_uart/UartDcMotor.h
firmware/shared/src/motor_uart/UartDcMotor.cpp
```

建議由 compile flag 只在有 UART DC motor 的 Slave 啟用：

```ini
-D MOTOR_TRANSPORT_UART=1
-D UART_DC_MOTOR_PORT=2
-D UART_DC_MOTOR_TX_PIN=17
-D UART_DC_MOTOR_BAUD=9600
-D UART_DC_MOTOR_SEND_INTERVAL_MS=100
```

建議配置概念：

```text
HardwareSerial motor serial：獨立 port，TX17 / RX disabled
USB CDC Serial：debug log
```

實作前要核對實際 ESP32-S3-Tiny board definition 及目前 UART instance 使用情況，
然後以 compile-time／startup validation 阻止其他 module 使用 GPIO17 或相同 UART port。

Motor module 應隱藏：

- direction/speed → VALUE conversion。
- 3-byte direct-frame encoding。
- 100 ms output schedule。
- startup／STOP state。
- per-address latest requested VALUE。
- OPEN/HOLD/CLOSE elapsed-time profile。

Story mode call site仍直接顯示 address、direction、speed 及硬件註解，不要新增多層
`renderMotor...()` wrapper。

### 8.1 現行實作位置

現行 code 按功能放入 `motor_uart/`，Pattern 則依專案規則放在 `patterns/`：

```text
firmware/shared/include/motor_uart/UartDcMotor.h
firmware/shared/src/motor_uart/UartDcMotor.cpp
firmware/shared/include/motor_uart/UartDcMotorLiveCommand.h
firmware/shared/src/motor_uart/UartDcMotorLiveCommand.cpp
firmware/shared/include/patterns/patterns_uart_dc_motor.h
firmware/shared/src/patterns/patterns_uart_dc_motor.cpp
firmware/slave/src/uartDcMotorLiveControl.cpp
```

其中 `patterns_uart_dc_motor.cpp` 是所有 Sine／Smooth Mechanical／Hydraulic Cinematic
曲線的唯一效果實作位置。Web UI 不複製 motor 曲線，只傳 pattern 名稱、速度及地址。

## 9. 多 motor send schedule

每 100 ms，對每個 configured address 發一個 direct frame：

```text
t = 0 ms:   FF 0C 80, FF 0F 80
t = 100 ms: FF 0C 7A, FF 0F 86
t = 200 ms: FF 0C 73, FF 0F 8D
...
```

兩個 address 要用同一個 `nowMs` 計算 phase/progress，然後先 staging 全部 values，
再逐個寫 frame，避免其中一個 motor 先進下一 phase。

### 9.1 RTT 與同步時間

RTT（Round-Trip Time）對 Master／Slave 對時很重要：雙向通訊層記錄 request 發出時間
與 reply 返回時間，計算 `RTT = replyAt - requestAt`，再用同步演算法估算 Slave clock
offset。這個 RTT 必須保留，不能因為 motor link 是 TX-only 就刪掉。

但 RTT 屬外部雙向通訊層，不是 GPIO17 motor wire 的 RTT。ATtiny412 firmware 沒有回傳
byte，ESP32 無法知道它何時收到 frame。Motor module 應接收同步層已換算好的本機開始
時間，而不是自行假造 ACK：

```cpp
runUartMotorTimingAt(MOTOR_OPEN_MS,
                     MOTOR_HOLD_MS,
                     MOTOR_CLOSE_MS,
                     synchronizedStartLocalMs);
```

同步規則：

- 同一 Slave 上全部 motor addresses 使用同一個 `synchronizedStartLocalMs` 和同一次
  `nowMs` snapshot。
- 不同 Slaves 由外部同步層把同一個 Master start time 換算成各自 local start time。
- Loop 遲到時按 elapsed time 直接計算正確 VALUE，不可按 loop 次數慢慢追。
- RTT 只用作 clock sync／link health；不可把 RTT 數值再加到 GPIO17 的 100 ms send
  interval。

USB log 可以每 1000 ms 顯示一次 snapshot；log interval 不可改動 100 ms motor send
schedule。避免在 timing-sensitive loop 做大量 blocking `Serial.printf()`。

建議 log：

```text
UART MOTOR ADDR 19 (0x13) | DIR A | SPEED 42% | VALUE 74 | TX OK
UART MOTOR ADDR 21 (0x15) | DIR B | SPEED 42% | VALUE 181 | TX OK
SYNC | UPSTREAM RTT 10970 us | CLOCK OK
```

Motor 行可顯示 `TX OK`，但不應出現 motor `SUCCESS/APPLIED`。RTT 若要顯示，必須標成
`UPSTREAM RTT` 或 `SYNC RTT`，不可令人誤會是 ATtiny motor ACK。

## 10. Startup Mode 0、STOP、reboot 與 OTA safety

ATtiny firmware 沒有 command timeout watchdog。它收到某個 moving VALUE 後，會一直
保持該 PWM，直到收到下一個有效 frame或失電。

`VALUE 128` 只表示停止 PWM，不表示機構已在原位。Hi-Nu 實機已確認 Direction A
= Close、Direction B = Open。因此最低安全流程必須包含 Mode 0 homing。

### 10.1 Slave boot

```text
初始化 GPIO17 motor UART
→ Mode 0：全部 configured motors 先以 Direction A、MOTOR_HOME_SPEED Close
→ 持續 MOTOR_HOME_RUN_MS
→ 對全部 motors 送 VALUE 128，真正停止
→ 暫停 MOTOR_HOME_STOP_MS，讓機構穩定
→ 標記 Mode0Ready
→ 才允許 story motor movement
```

以上必須用 `millis()` state machine，不可用 `delay()`。所有 motors 共用同一個 Mode 0
時間基準，確保同步關閉及同步進入 ready。若 motor 行程時間不同，應把每個 address 的
home duration 明確放在 user-facing config，再以最慢的一個作 fleet barrier。

實作可以在 UART begin 後先送一次 `128` 清除 ATtiny 可能保留的舊輸出，但這個 safety
STOP **不可**當作 homing 完成；隨後仍必須執行 Direction A 的完整 Close 時間和停止暫停時間。

Motor UART 應早於 Story Mode movement 初始化。若 config 無效，應對仍能辨認的合法
addresses 發 STOP，並保持 movement gate 關閉。

### 10.2 Story stop／power off／fault

立即將全部 configured addresses staging 為 `128`。停止狀態仍每 100 ms重送 STOP，
確保某一個遺失 frame 後仍有後續機會停止。

### 10.3 OTA 或 intentional reboot

```text
關閉新 movement request
→ 對全部 motor 送 VALUE 128
→ motorSerial.flush()
→ 才開始 OTA flash／reboot
```

新 firmware boot 後重新執行完整 Mode 0；不能因為 OTA 前已送 STOP 就假設位置仍然正確。

### 10.4 無法由 ESP32 software 完全解決的情況

如果 ESP32 freeze、GPIO17 wire 斷線或 ATtiny 收不到 STOP，現有 ATtiny firmware 不會
自行 timeout。真正 fail-safe 需要未來其中一項：

- ATtiny 加 command watchdog，超時自動 `updateMotor(128)`；或
- Motor power 由可獨立切斷的 safety circuit 控制；或
- limit switch／current protection／mechanical stop。

這份 handoff 不授權修改 `UART-412.ino`；以上只是必須記錄的硬件限制。

### 10.5 ColorPicker live lease

ColorPicker live motor 命令屬 side-channel，不停止 RGB story。Master 將
`POST /api/uart_motor` route 成 `LC:um,...`，Slave 收到有效 drive／pattern 後啟動
1 秒 lease：

```text
browser keepalive：每 300 ms
Slave lease timeout：1000 ms
timeout／LC:um,stop：所有 live addresses 立即送 VALUE 128
```

頁面離開、隱藏、失焦及 WiFi request 失敗都會嘗試發 STOP；但真正 fail-safe 邊界是
Slave lease，不依賴瀏覽器最後一個 packet 必定送達。新 live session 開始前亦會先停止
上一批 runtime addresses，避免使用者改地址後舊 motor 繼續運行。

## 11. OTA boundary：GPIO17 只提供 motor safety hook

OTA 的 transport、GPIO、frame、chunk、CRC、ACK、retry 與 reboot verification 全部由
另一份 OTA spec 負責。這份 motor spec 不重複定義它們，也不把 GPIO17 當作 firmware
傳輸線。

GPIO17 motor module 提供以下 integration hooks：

```cpp
bool stopAllUartMotorsAndFlush();  // OTA／reboot 前呼叫
void beginUartMotorMode0(uint32_t nowMs); // 新 firmware boot 時開始 Direction A Close homing
void updateUartMotorMode0(uint32_t nowMs);
bool uartMotorMode0Ready();
```

第一個 hook 必須關閉新 movement、對所有 configured motor addresses 發送 raw VALUE
`128`，並等待 UART TX 完成。只有它成功後，外部 OTA controller 才可開始寫 flash 或
reboot。OTA 完成後，Slave boot 必須以 `beginUartMotorMode0()` 開始 Direction A Close
homing，並在
`uartMotorMode0Ready()` 成為 true 前封鎖其他 motor functions。

## 12. Open-loop position limitation

ATtiny frame 只有 address + output VALUE，沒有 encoder、limit switch、position feedback
或 ACK。因此系統知道的是「要求 motor 朝某方向以某輸出運行」，不是「motor 已到某
位置」。

斷電後要求「還原 original position」若只靠固定運行時間，屬 open-loop homing：

- 負載／電壓變化會令位置有誤差。
- 撞到機械盡頭後繼續 HOLD 會堵轉、發熱及增加電流。
- `HOLD peak` 是繼續驅動，不是停止。

需要準確原點時，應另加 limit switch／encoder，再建立 feedback protocol。不要把固定
秒數描述成已確認位置。

## 13. 實作與驗證順序

目前實作按以下分層完成；後續修改仍應維持每步的完成條件：

1. **GPIO17/UART audit**

   列出 relevant Slave 的 GPIO17 motor UART port 與 USB CDC；完成條件是 GPIO17
   沒有被其他 module 使用，而且 USB debug 不共用 motor `HardwareSerial`。

2. **Pure motor codec tests**

   測試 address `1..32`、STOP 128、A/B percentage mapping，以及 exact direct frames；
   完成條件包含 decimal address 19 的 `FF 13 80`，以及 decimal address 21 的
   `FF 15 80`、`FF 15 00`、`FF 15 FF` exact-byte assertions。

3. **TX-only motor adapter**

   初始化 `9600 8-N-1, RX=-1, TX=17`，並以 `write(frame, 3)` 發送；完成條件是
   module 無 `read()`、CRC、ACK、RTT 或其他 transport dependency。

4. **Mode 0 homing／STOP safety**

   boot/reboot 先讓全地址以 Direction A 執行 user-configurable homing，再送 128 並等待
   `MOTOR_HOME_STOP_MS`；完成條件是 `Mode0Ready` 前任何其他 motor function 都不能輸出。
   fault、story stop與 power off仍立即對全地址送 128。

5. **Linear profile**

   使用 `millis()` 完成 OPEN/HOLD/CLOSE；完成條件是 exact start/midpoint/end、dead-zone
   values、late loop及 `UINT32_MAX` rollover tests 全通過。

6. **RTT-synchronized start contract**

   接收外部同步層提供的 `synchronizedStartLocalMs`，所有 address 用同一時間計算；
   完成條件包括不同 loop arrival time仍得到相同 phase/value，以及 stale/invalid clock
   時保持 STOP，不會自行開始。

7. **Story Mode integration**

   在正確 `switch (slaveId)` case 直接放每個 address call；每個實際 call 前寫 GPIO17、
   address、機構部位與動作註解。Motor staging 先於 RGB/PCA effects。

8. **OTA safety hook integration**

   把 `stopAllUartMotorsAndFlush()` 接到外部 OTA／reboot 流程；完成條件是 flash write
   前 motor STOP 已離開 GPIO17；新 firmware boot 後完整 Mode 0 未完成前，Story Mode
   movement gate保持關閉。

9. **Build verification**

   shared code 至少 build Master、relevant Slave與 `slave_standalone`，即使 standalone
   不啟用 motor UART，也要證明 compile guard 沒破壞它。

## 14. 最低測試矩陣

| Test | Expected |
|---|---|
| Encode STOP for decimal address 19 | `FF 13 80` |
| Encode STOP for decimal address 21 | `FF 15 80` |
| Encode A 100% | VALUE `00` |
| Encode B 100% | VALUE `FF` |
| Encode A/B 1% | `7F` / `81` |
| OPEN midpoint | 時間與 VALUE 都在線性中點 |
| CLOSE endpoint | exact `128` |
| Two addresses | 同一 phase、同一 `nowMs` staging |
| Valid synchronized start | 全地址按同一 local start time 進入 phase |
| Invalid/stale clock | 保持 VALUE 128，不開始 story movement |
| Missing/duplicate address call | movement gate 關閉，全 motor STOP |
| Boot/reboot | Direction A Close homing → VALUE 128 → stop dwell；完成前不接受其他 movement |
| Safety STOP before Mode 0 | 不得把一次 VALUE 128 誤當成已回原位 |
| A→STOP→B／B→STOP→A | 分別測 5／10／15／20／30 ms，各至少 100 次；記錄最小穩定間隔、GPIO17 exact bytes 與 motor 現象 |
| OTA START | STOP + TX flush 完成後才寫 flash |
| GPIO17 wire removed | Log 只能顯示 TX queued；不可假稱 motor applied |
| millis rollover | phase及100 ms schedule 正常 |

## 15. Hardware wiring checklist

```text
ESP32-S3-Tiny Slave GPIO17 TX ──> 所有 ATtiny412 PA1 / orange signal wire
ESP32-S3-Tiny Slave GND       ──> 所有 motor boards GND / black wire
Motor board VCC               ──> 已確認容量的 motor supply

```

確認事項：

- 所有 motor board 與 Slave 必須共地。
- Motor supply 要承受所有 motor startup/stall current，不應由 ESP32 GPIO供電。
- 確認 ESP32 3.3V TX 與 5V ATtiny input 的 VIH 相容性。
- ATtiny `PA1` 使用 `INPUT_PULLUP`；若 ATtiny VCC 是 5V，應核對是否需要 level
  shifter／buffer，避免 5V pull-up/backfeed 到 ESP32 GPIO17。
- 多塊 PA1 並聯前確認 fan-out、線長、雜訊及 ground quality。
- GPIO17 只接 ATtiny412 PA1，不接任何其他通訊 bus。

## 16. 完成定義

此功能只有同時滿足以下條件才算完成：

- GPIO17 只輸出 ATtiny direct motor frames。
- 每個 motor address 可獨立設定 direction及 peak speed。
- 全 motor 共用 linear OPEN/HOLD/CLOSE timeline。
- 外部 RTT clock sync有效後才可按 synchronized local start time開始 timeline。
- STOP 永遠使用 raw VALUE 128。
- startup及 reboot 都先完成 fleet-wide Direction A Close Mode 0 homing，再開放其他 functions。
- fault、power off及 OTA 都有 fleet-wide STOP path。
- Log 不會把 TX queue success 說成 motor ACK／APPLIED。
- 外部 OTA／reboot 流程必須通過 GPIO17 motor STOP + flush safety gate。
- Native/static tests與相關 PlatformIO environments 全部通過。
- 實機以 logic analyzer／scope 看見 GPIO17 的 9600 8-N-1 exact bytes，然後才接 motor。

## 17. 本文件沒有做的事

仍未由 software 解決的項目：

- 沒有修改或複製 `UART-412.ino`。
- 沒有在本文件定義 Master↔Slave transport 或 OTA protocol。
- GPIO17 是 TX-only，沒有 motor ACK、encoder 或 limit switch；log 只能證明 frame 已送出。
- ColorPicker Servo Motor／Stepping Motor 分頁未實作控制功能。
