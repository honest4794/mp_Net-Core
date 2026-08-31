# Hi-Nu 黑板 motor 兩階段測試紀錄

> 最後更新：2026-08-31
> Branch：`dev_motor_effects`
> 對接：HiNu `dev_1-18_HiNu_Gundam`
> 本輪硬件：六板及 CH348 TTL channel A 已連接

---

## 2026-08-31 continuous demo loop 修正

Black Slave 1／2 的 `ProjectMode.continuous_loop=1` 令 motor demo 常駐循環
Mode 0 → Mode 1 → Mode 2。一般 `MODE_GET`／status traffic 不再退出本機 loop；
收到 `MODE_SET` 時，以共同 `started_at` 重設 mode index 與下一個 deadline。
下一 deadline 由上一 deadline 累加，不用各板實際 wake time，因此 scheduler jitter
不會逐輪累積。`MODE_STOP action=0` 只保留反向所需安全 dead-zone 過場；
`action=1` 仍會 suspend loop，直至下一個明確 `MODE_SET`。

若目前同 mode 是由本機 loop 啟動，Master 的同 mode 排程仍會接納，以完成第一次
對錶；若已由 remote deadline 啟動，後續 repair 仍按 idempotent 規則忽略，避免
重啟 sine/profile。

## 〇、一分鐘理解

本輪不用兩個 Git worktree。兩個測試共用同一份 NC4 schema、black Slave config、JSON effect 與 UART-412 encoder；拆成兩個可獨立執行的程式，避免兩套 firmware/config 漂移。

| 階段 | 程式 | 驗證範圍 | 本輪結果 |
|---|---|---|---|
| Test 1 | `tools/PC/hinu_motor_command_test.py` | black Master 產生 NC4 `MODE_SET/MODE_STOP`，black Slave1/2 以真實 schema/handler 解碼並建立共同 deadline | HOST PASS |
| Test 2 | `tools/PC/hinu_motor_sync_test.py` | 以真實 JSON、兩份 config 與 UART-412 direct-addressed frames 重播 Mode 0–3，核對四個 motor 的 logical timing | HOST PASS |
| Test 1 實機 | black Master→Slave1/2 RS485 | Master TX 成功；Slave1 raw receiver 在五幀／90 bytes 測試中收到 0 bytes | LINK FAIL（根因未落點） |
| Test 2 實機 | 兩 black Slave→四 ATtiny motor | `storyMode_motor` 使用補償後共同 absolute deadline；兩板 movement/stop offset 相同 | UART OUTPUT PASS；機械觀察待人眼確認 |

## 一、板角色與參數

| 顏色／角色 | Port | 本輪責任 |
|---|---|---|
| blue Master | `/dev/cu.usbmodem1127101` | HiNu visual StoryMode 與 scheduled start |
| blue Slave1 | `/dev/cu.usbmodem1127201` | RGB/PCA；`MOTOR_TRANSPORT_UART=0` |
| blue Slave2 | `/dev/cu.usbmodem1127401` | RGB/PCA；`MOTOR_TRANSPORT_UART=0` |
| black Master | `/dev/cu.usbmodem1127301` | motor bench NC4 command sender |
| black Slave1 | `/dev/cu.usbmodem1121301` | CID `0001`；motor address `15,19` |
| black Slave2 | `/dev/cu.usbmodem1121201` | CID `0002`；motor address `12,21` |
| CH348 TTL A | `/dev/cu.usbmodem01234567891` | HiNu Timer simulator→blue Master GPIO5/6；115200 |

共同設定以 Figma Gunpla v1 線路圖為硬件唯一真相：black Master↔Slaves 使用 RS485 UART1 GPIO10 TX→RXD／GPIO11 RX←TXD／GPIO9 EN、115200。2026-08-31 拆接 A/B 的現場對照證明：black boards 接入且 `EN=1` 時 blue Master↔Slaves 通訊中斷，拔除 black A/B 後立即恢復，因此此模組的 `EN=1` 是驅動／發送、長期保持會佔用總線；black Slave RX-only profile 必須設定 `rx_en_level=0`。black Slave→ATtiny 使用 UART2 GPIO12 TX-only、9600。Motor STOP 固定 `0x80`；`0x00` 是 Direction A 全速，不能用全零 buffer 代表停止。現場相容模式使用 direct-addressed frame，一次 `uart.write()` 串接同一 Slave 的兩個 motor；optional broadcast 與 calibration code 均保留，但兩份 HiNu black config 不啟用。

## 二、Test 1：Master command control

### 2.1 Host／offline 指令

```bash
cd '/Users/all.are.mathematics/My Documents/FastLED project/UART Design'
python3 -B tools/PC/hinu_motor_command_test.py offline --modes 0 1 2 3 --start-delay-ms 300
python3 -B tools/PC/hinu_motor_command_test.py ports
```

### 2.2 狀態與時序

| 項目 | 實測現象 | 結果 |
|---|---|---|
| Mode 0 payload | `01 00 2C 01 FF`；CID 0001/0002 都排到 `1300ms` | PASS |
| Mode 1 payload | `01 01 2C 01 FF`；CID 0001/0002 都排到 `1300ms` | PASS |
| Mode 2 payload | `01 02 2C 01 FF`；CID 0001/0002 都排到 `1300ms` | PASS |
| Mode 3 payload | `storyMode_motor`；CID 0001/0002 使用同一 scheduled deadline | PASS |
| Stop payload | `MODE_STOP 0x3106`，`action=1`；兩個 handler status 都是 `running=0` | PASS |
| NC4 handler | `start_delay_ms` 建立 deadline，不再在 RS485 handler 內 `sleep_ms()` | PASS |

### 2.3 實機 command

接回硬件後，先把 sender 放到 black Master，再送命令：

```bash
python3 -B tools/PC/hinu_motor_command_test.py deploy-master
python3 -B tools/PC/hinu_motor_command_test.py send-mode 0 --start-delay-ms 300
python3 -B tools/PC/hinu_motor_command_test.py send-mode 1 --start-delay-ms 300
python3 -B tools/PC/hinu_motor_command_test.py send-mode 2 --start-delay-ms 300
python3 -B tools/PC/hinu_motor_command_test.py send-mode 3 --start-delay-ms 3000
python3 -B tools/PC/hinu_motor_command_test.py stop
```

上述 command 只代表 black Master 已把 bytes 交給 UART。實機仍要從兩個 Slave log 確認收幀，並觀察四個 motor；UART-412 沒有 ACK。

## 三、Test 2：兩 Slave／四 motor synchronization

### 3.1 Host／offline 指令

```bash
python3 -B tools/PC/hinu_motor_sync_test.py --modes 0 1 2 3
```

### 3.2 狀態與時序

| Mode | 行為 | start skew | first-motion skew | stop skew | final | 結果 |
|---:|---|---:|---:|---:|---:|---|
| 0 | Direction A `0x00` 10s → STOP | 0ms | 0ms | 0ms | `0x80` | HOST PASS |
| 1 | Direction B `0xFF` 10s → STOP | 0ms | 0ms | 0ms | `0x80` | HOST PASS |
| 2 | C++ reference sine A/B + stop slots，6 cycles／180s | 0ms | 0ms | 0ms | `0x80` | HOST PASS |
| 3 | HiNu `storyMode_motor`：STOP prelude 9s → Hydraulic Cinematic B 15s | 0ms | 0ms | 0ms | `0x80` | HOST PASS |

Test 2 比較的是兩個 profile 的完整 logical motor history與 UART write timestamps，不只比較單一常量。現場 frame 使用 `FF address value FE` 串接；兩個 frame 在同一個 UART write 送出，在 9600 baud 下同一 Slave 的兩 motor wire skew 約 4.2ms。Mode 3 的 C++ Hydraulic profile cruise plateau 是 95%，Direction B peak 為 `0xF9`；`0xFF` 仍保留給 Mode 1 的 full-speed test。

### 3.3 2026-08-30 實機 Test 2

下表是修正 pin map 前在錯誤 GPIO17 上取得的軟件 timing trace，只能證明 timeline 計算；因實機 motor wire 是 GPIO12，這輪不得記作 motor UART output PASS：

| Board | Address | START | first motion | STOP | 結果 |
|---|---|---:|---:|---:|---|
| black Slave1 | `15,19` | `233983` | `+9041ms`（frame 452，raw `0x81`） | `+24050ms`，raw `0x80` | INVALID：舊 GPIO17 |
| black Slave2 | `12,21` | `191026` | `+9041ms`（frame 452，raw `0x81`） | `+24050ms`，raw `0x80` | INVALID：舊 GPIO17 |

兩板 start clock 相差的固定 offset已由 target 補償，timeline 相對時間相同；但 frame 沒有經實機 GPIO12，因此該輪作廢。

改用正確 GPIO12 重新部署後，兩板以補償後共同 absolute deadline 重跑 `storyMode_motor`：

| Board | Address | absolute START | first motion | STOP | UART 結果 |
|---|---|---:|---:|---:|---|
| black Slave1 | `15,19` | `480063` | `+9041ms`（frame 452，raw `0x81`） | `+24051ms`，raw `0x80` | PASS |
| black Slave2 | `12,21` | `770629` | `+9041ms`（frame 452，raw `0x81`） | `+24050ms`，raw `0x80` | PASS |

這證明兩個 ESP32-S3 在正確 GPIO12 上產生相同 UART command timeline；UART-412 沒有 ACK，因此不能單靠 log 宣稱四支 motor 已機械移動或在負載下同步，仍須現場觀察。

其後為排除現場 ATtiny transport 差異，兩板已完成：已知 address direct A/B、address `1..32` sweep、9600/19200 sweep，以及 GPIO12 self-readback。9600 readback 精確匹配 Slave1 `ff0fffff0f80`、Slave2 `ff0cffff0c80`；正式 config 已改為 direct transport，production driver 顯示 `span 0` 並對四個正式 address 跑 Direction B 全速 5 秒後 STOP。若現場仍無機械動作，應檢查 GPIO12→ATtiny PA1、共同 GND、ATtiny/motor board 供電與 motor driver，因 software/address/baud probe 已覆蓋。

## 四、Blue／black environment 流程

1. Blue repo 只保留 RGB/PCA/visual StoryMode 與 Master scheduling；blue Slave1/2 不擁有 black motor output。
2. Black repo 保存 Mode 0–3 JSON、兩份 black Slave config、GPIO12 motor UART 與 command/sync tests；Mode 3 名稱固定為 `storyMode_motor`。
3. Bench direct-ID 測試不做正式語意映射：blue LED Mode 0/1/2 照常播放各自 StoryMode；同一 NC4 `mode_id` 在 black Slaves 分別選 motor diagnostic／最快／dev sine。正式 project mapping 另行處理。
4. 接回硬件後先 build/upload blue Master/Slave1/Slave2，再部署 black Master/Slave1/Slave2。
5. 先跑 Test 1 確認控制面，再跑 Test 2 觀察同步；每輪結束必須送 `stop`。
6. 實測紀錄至少寫：時間、設備、Mode、兩 Slave 收幀、四 motor first motion、stop、是否有異音/卡死及結論。

## 五、2026-08-30 實機結果與限制

- 六個指定 USB ports 及 CH348 A–D 均出現；blue Master/Slave1/Slave2 與 black Master/Slave1/Slave2 已部署。black Slave2 的舊 CID/address config 已修正為 CID `0002`、address `12,21`。
- Blue Timer channel A 成功列出 15 個 modes，並正式鏡射 `mode_type=2, mode_id=1`；`MODE_GET` 在 10 秒時回報 `running=1, total_ms=240000`。開啟 blue native USB monitor 會 reset Master，故正式觀察只使用 TTL query。
- Blue Master I2C 掃描找到 Slave2 `0x11`，但找不到 Slave1 `0x10`；Slave1 firmware flash digest 已驗證，仍屬硬件/boot/I2C 問題。
- Black Test 1 舊結果使用錯誤 GPIO14/15/16，因此作廢。修正為 EN9/TX10/RX11 後，normal EN polarity 的 18-byte probe 在 Slave1 只見 `00 00`、Slave2 為 0 bytes；反轉 EN polarity時 Slave1 只見 `00`、Slave2 仍為 0 bytes。
- 2026-08-31 重做 Test 1：兩個 black Slave profile/runtime SHA-256 與本機一致，啟動 log 分別確認 CID1/address `19,15`、CID2/address `12,21`，`CircuitTask` online。black Master sender 加入 listen-before-talk 後，Mode 0/1/2 的每幀 `uart.write()` 均回報 18 bytes，但兩個 Slave 都沒有 `MODE_SET`。
- 繞過 NC4/runtime 的 raw isolation：black Slave1 固定 EN9=0、UART1 RX11 捕捉 6 秒；black Master 在期間連續發送五個 18-byte frame（合計 90 bytes），Slave1 結果為 `RAW_CAPTURE_BYTES 0`。反向檢查 black Master 在 RX10/11/13/14/15 各聽 1.2 秒都只見 1–2 bytes 啟動雜訊，沒有同場 blue bus 的持續流量。故目前只能判定 **RS485 link 未交付**；證據未能再區分 Master transceiver 供電／接線、Master 是否實際接入該 A/B、或線路圖外的其他實體因素，不把它誤報為 NC4/JSON failure。
- 2026-08-31 CH348 A direct-ID bench：Timer 對 blue Master 依次發 LED Mode 0/1/2；blue Master 三次均鏡射正確 `MODE_SET(type=1,id=0/1/2)`，Timer parser 累計 10 個 valid frames、0 bad CRC/version/length/timeout。同期 black Slave1/2 runtime monitor 沒有任何 `MODE_SET`，另以 black Slave1 RX11 只讀捕捉 blue bus 3 秒亦為 `BLUE_TO_BLACK_RAW_BYTES 0`。故 blue control/storyMode path PASS，但 blue→black RS485 delivery FAIL，四 motor 沒有被本輪命令啟動。
- 2026-08-31 更換新 RS485 後曾把兩個 RX-only profile 設成 `EN9=1` 重測；此測試設定其後由 A/B 拆接對照證實無效：black boards 以 EN1 接入會令原本正常的 blue Master↔Slaves 通訊中斷，拔除 black A/B 即恢復，根因是 black transceiver 長期驅動總線。三塊 black boards 已先即時拉回 EN0，正式 profile 亦回復 `rx_en_level=0`。先前 EN1 下的 0-byte RX 結果不再視為接收能力結論；black RS485 delivery 需在 RX-only EN0、black Master 只於送幀期間短暫 EN1 的條件下重驗。
- 2026-08-31 EN0 修正後六板接回同一實機：Blue Master 掃描到 Blue Slave1/2；兩個 Blue Slave 連續統計均為 `bad_frame=0`、`dropped=0`，並同步收到 `StorySet:0`／`Mode:set:0`。Black Slave1/2 均以 RX-only 收到 `TIME_SYNC`／`MODE_SET`，沒有驅動 A/B；Slave2 完整 runtime 補回並按 `boot.py → main.py` 正常啟動後，`CircuitTask online`、`Boot complete`，不再出現未初始化 `st_pixel` 錯誤。現場由使用者確認 motor 已移動，故 blue Master→black sidecar→GPIO12 UART motor 實機路徑判定 PASS。
- 2026-08-31 加入無 CLI standalone test loop：Black Slave1/2 profile 在 10 秒收不到任何有效 Master frame 後，自動執行 Mode0 diagnostic 10 秒 → `0x80 STOP` → Mode1 max 10 秒 → `0x80 STOP` → Mode2 dev sine 180 秒 → `0x80 STOP`，之後回 Mode0 循環。Master frame 恢復時先 STOP，再保留 Master 的 `MODE_SET`／deadline 立即接管。全域 `registry.auto_play` 維持 false，故只影響明確啟用 `ProjectMode.dev_mode_ids` 的兩份 black profile。板上 `pixel_task.py` 與兩份 config SHA-256 均與本機一致；六板接線下兩塊 black 均收到 Blue Mode0，而 Blue Slave1/2 維持 `bad_frame=0`、`dropped=0`。
- 2026-08-31 獨立 motor isolation（完全繞過 RS485）：逐板停止 TaskManager，UART2 GPIO12／9600 逐 address 單獨發 `A_MAX 0x00` 2s → `STOP 0x80` → `B_MAX 0xFF` 2s → `STOP`。Slave1 address 19、15 與 Slave2 address 12、21 共 16 個動作／停止 frame 均由 `uart.write()` 完整接受 4 bytes，最後每個 address 再補一幀 STOP；兩板其後恢復 `CircuitTask online`／`Boot complete`。這確認 ESP32→ATtiny UART command output；因 ATtiny/motor 沒 ACK、encoder 或 limit switch，機械移動仍須以現場觀察確認。
- Black Test 2 舊結果使用錯誤 GPIO17，因此作廢。正確 GPIO12 重跑後，兩板的 first-motion UART offset 同為 `+9041ms`，STOP offset 相差 1ms；UART output PASS。ATtiny412 沒有 ACK、encoder 或 limit switch，機械同步仍須由現場人眼／logic analyzer確認。
- 實體同步目標沿用 NC4 scheduled-start `≤5ms`；要量 motor board 電氣邊沿需 logic analyzer。
- ATtiny412 不回 ACK，motor 行程、負載、供電與機械摩擦不在 offline test 可證明範圍。
- Calibration code 保留，但本測試不載入 calibration。

## 六、結論

- 兩個獨立 host programs 已通過；Mode 0–3、STOP、dead zone、四個 address 與兩份 profile 均有覆蓋。
- black Slave 的 NC4 schedule 改為 non-blocking deadline，為兩板同步保留共同開始邊界。
- 舊 pin map 的硬件結論已撤回；以 Figma v1 修正為 motor GPIO12、RS485 EN9/TX10/RX11。正確 GPIO12 UART timeline 已通過，RS485 end-to-end 仍因收不到完整 frame 而未通過，不能宣稱整體實機驗收完成。
