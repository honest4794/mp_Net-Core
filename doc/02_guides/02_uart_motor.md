# UART 電機控制器（uart_motor）

> **用途**：透過 UART 控制多顆電機推桿（如 `0xFF 11 0x80 0xFE` 這類 frame 協定）。
> **分類**：使用教學（02_guides）
> **最後更新**：2026-08-18
> **位置**：`slave/lib/hw/uart_motor.py`（裝置端以 `from lib.hw.uart_motor import ...` 匯入）
> **校準工具**：`tools/ESP/calibrate_motor.py` / `calib_loader.py`（測試/校準工具，位於頂層 `tools/`，不進入 `slave/` 的獨立系統）

本函式庫提供兩層介面，疊在同一個統一緩衝區之上：

1. **原始速度模式** —— 直接控制速度 byte（`0x00`～`0xFF`）。
2. **行程模式** —— 用「位置 `0..4095` + 速度 `0..128`」描述動作，底層自動轉成速度 byte，並以「速度 × 時間」做開迴路位置估算。

---

## 目錄

- [1. 檔案結構](#1-檔案結構)
- [2. 快速開始](#2-快速開始)
- [3. 核心概念](#3-核心概念)
- [4. 初始化與 Config 參考](#4-初始化與-config-參考)
- [5. 原始速度模式 API](#5-原始速度模式-api)
- [6. 行程模式 API](#6-行程模式-api)
- [7. 校準：三檔速度點](#7-校準三檔速度點)
- [8. 完整使用範例](#8-完整使用範例)
- [9. 常數參考](#9-常數參考)
- [10. 注意事項與限制](#10-注意事項與限制)

---

## 1. 檔案結構

```
mp_Net-Core/
├── slave/
│   └── lib/
│       └── hw/
│           └── uart_motor.py        # 核心：UartMotor 類別 + 常數 + 版本分派
├── tools/
│   ├── PC/                         # PC 端工具
│   └── ESP/
│       ├── calibrate_motor.py      # 校準工具：量三檔速度的全程時間（限位開關自動偵測）
│       └── calib_loader.py         # 讀回校準 JSON 檔，填入 UartMotor
├── test/
│   ├── motor/
│   │   ├── test_uart_motor.py      # 核心 frame / 速度模式 / 行程模式 測試
│   │   └── test_calibrate.py       # 校準工具 / 內插 / calib config 測試
│   └── ...
└── doc/
    └── 02_guides/
        └── 02_uart_motor.md        # 本文檔
```

`slave/lib/hw/uart_motor.py` 同時相容 MicroPython 與 CPython：
- MicroPython 上使用 `@micropython.viper` 加速 frame 編碼。
- CPython（PC 測試）走純 Python fallback，且時鐘自動退回 `time.monotonic_ns()`。

---

## 2. 快速開始

```python
from machine import UART
from lib.hw.uart_motor import UartMotor, SPEED_MAX, SPEED_MED

uart = UART(0, baudrate=9600)   # baud 依硬體文件

motor = UartMotor({
    "version": 1,               # 指令方法標記，預設 1，可省略
    "addresses": [11, 12],      # 我控制的全部台
    "uart": uart,               # 必填
    "calib": {                  # 校準（選項）：{address: {speed: 全程ms}}
        11: {128: 3000},
        12: {24: 24000, 64: 12000, 128: 6000},
    },
})

# 起動兩個目標（只改 buffer，不發送）
motor.move_to(11, 4095, SPEED_MAX)   # 11 全速伸到底
motor.move_to(12, 2048, SPEED_MED)   # 12 中速伸到半程
motor.show_all()                     # 一次 uart.write 送出整幀

# 主迴圈：週期結算，到達的台自動停
while True:
    motor.update()                   # 重算位置；到達目標/邊界 → 停（改 buffer）
    motor.show_all()                 # 把停止幀推送出去

    p11 = motor.position(11)         # 讀估算位置 0..4095
    p12 = motor.position(12)
    # ... 依 p11/p12 做上層邏輯 ...
```

---

## 3. 核心概念

### 3.1 統一緩衝區 buffer

- `motor.buffer` 是**唯一權威狀態**，型別 `bytearray`。
- 長度 = 最大的 address（`[11, 12]` → 長度 12；位置 1～10 是未控制的，恆為停車）。
- 索引 `addr - 1` 對應第 `addr` 台：address 11 → `buffer[10]`。
- **改 buffer 不發送**；發送由 `show_all()` / `send()` / `send_all()` / `stop_all()` 統一處理。

### 3.2 兩層模式

| 模式 | 你給的單位 | 底層 |
|---|---|---|
| 原始速度模式 | 速度 byte `0x00`～`0xFF` | 直接進 buffer |
| 行程模式 | 位置 `0..4095` + 速度 `0..128` | 換算成速度 byte 進 buffer |

兩層共用同一條 UART、同一個 buffer，可混用。行程模式本質是「速度控制 + 位置估算」，**不會**也不能把「行程」直接塞進 frame——硬體只認速度 byte。

### 3.3 位置與速度的單位

**位置（pos）**：整數 `0..4095`（12-bit），`0` = 全收、`4095` = 全伸、`2048` = 半程。全程就是 `0x0FFF`。

**速度（speed）**：整數 `0..128`，`128` = 全速、`64` = 中速、`0` = 停。方向由目標位置自動決定，不需手算正反。

> 速度 `0..128` 與速度 byte 的對應（v1 格式）：
> - 伸出（正轉）：`byte = 0x80 - speed`，所以 `128→0x00`、`64→0x40`。
> - 縮回（反轉）：`byte = 0x80 + speed`，所以 `128→0xFF`、`64→0xC0`。

### 3.4 定點整數（無浮點）

內部位置用**定點整數**表示，小數位數 `_Q = 12`：

```
內部值 = 對外位置 × 2^12
對外位置 = 內部值 >> 12   （範圍 0..4095）
```

例如位置 1000 格 → 內部 `1000 << 12 = 4096000`。全程 4095 格 → 內部 `4095 << 12 = 16773120`。

這讓「速率 × 時間」的乘積全程是整數運算，**沒有浮點、沒有累積捨入誤差**。

---

## 4. 初始化與 Config 參考

```python
UartMotor(cfg)
```

| 鍵 | 型別 | 必填 | 說明 |
|---|---|---|---|
| `uart` | UART 實例 | ✅ | 共用同一條 UART；缺漏會 `ValueError` |
| `addresses` | `int` 或 list | ✅ | 控制的台；會排序去重、驗證 1～255 |
| `version` | `int` | ❌ | 指令方法標記，預設 1 |
| `sync_broadcast_span` | `int` | ❌ | `1..32`；啟用固定長度 UART-412 broadcast，值必須涵蓋最大 address。未設定則沿用單台 frame 串接 |
| `sync_tx_interval_ms` | `int` | ❌ | 同步 broadcast 最短發送間隔；只保留最新值，轉入 Stop 不受節流影響。預設 0 |
| `calib` | dict | ❌ | 校準資料，格式 `{address: {speed: 全程ms}}`，正反同值 |
| `t_full_ms` | `int` | ❌ | 全速全程 ms 的**預設值**（全部台同值），預設 3000 |
| `t_full_fwd_ms` | `int` 或 `{addr: ms}` | ❌ | 伸出全速全程 ms，逐台覆蓋 |
| `t_full_rev_ms` | `int` 或 `{addr: ms}` | ❌ | 縮回全速全程 ms，逐台覆蓋 |
| `clock` | callable | ❌ | 時鐘來源，預設 `time.ticks_ms`（CPython 用 `monotonic`）；測試注入用 |
| `clock_diff` | callable | ❌ | 時鐘差值，預設 `time.ticks_diff`；測試注入用 |

### `calib` 校準格式（唯一格式）

```python
"calib": {
    11: {128: 3000},                         # 只給全速一項 → 線性正比
    12: {24: 24000, 64: 12000, 128: 6000},   # 低/中/高三點 → 分段內插
}
```

- 值是「**走完全程的毫秒數**」。
- **正反同值**（伸縮預設一致，不須分開填）。
- 每台可給**任意數量的速度點**（一項也行、三項也行）。
- `speed = 128` 那一點會順便同步該台的全速全程時間（`t_full`）。
- 缺漏的台／速度點，用線性模型自動補。

### 校準優先順序

```
calib（明確速度點）  >  t_full_fwd_ms / t_full_rev_ms / t_full_ms（全速點）
```

`calib` 若給了 `128`，會覆蓋 `t_full_*` 的同一台同方向值。

---

## 5. 原始速度模式 API

### `set(addr, value)`
設定單台目標 byte（**不發送**）。`addr` 必須在 `addresses` 內，否則 `ValueError`。

### `set_all(value)`
全部台設為同一 byte（**不發送**）。

### `set_many(values)`
批量設定（**不發送**）。
- `dict` → `{addr: value}` 只更新指定台。
- `list` → 長度必須等於 `num_devices`，逐位填（含未控制位置）。

### `get_write_view()`
零拷貝入口，回傳 `memoryview(self.buffer)`，供外部直接寫 buffer。

### `show_all()`
單次 `uart.write` 推送全部：

- 有設定 `sync_broadcast_span`：送固定長度 broadcast；未控制 address 固定填 `0x80` Stop。相同狀態不重送，快速變化按 `sync_tx_interval_ms` 只送最新值。
- 未設定：送各受控 address 的單台 frame 串接，保留 address `33..255` 相容性。

UART-412 broadcast 沒有 byte escaping，payload 中的 `0xFE` 會被誤認為 frame
結尾；同步模式會把命令值 `0xFE` 提升成同方向相鄰值 `0xFF`，避免較高 address
漏收。buffer 本身仍保留原始值，只有 wire encoding 會作此安全轉換。

### `send(addr, value)`
`set` + 立即發送**單台 frame**（同時更新 buffer）。

### `send_all(value)`
`set_all` + `show_all`，立即廣播全部同值。

### `stop_all()`
全部停止（`send_all(STOP)`）。

### 速度 byte 常數

| 常數 | 值 | 意義 |
|---|---|---|
| `STOP` | `0x80` | 停 |
| `FWD` | `0x40` | 正轉中速 |
| `FWD_FS` | `0x00` | 正轉全速 |
| `REV` | `0xC0` | 反轉中速 |
| `REV_FS` | `0xFF` | 反轉全速 |

### Frame 格式（v1）

- 單台：`FF addr value FE`
- 廣播：`FF 00 V1 V2 ... VN FE`（`N = sync_broadcast_span`，UART-412 上限 32）

---

## 6. 行程模式 API

### `move_to(addr, target, speed=SPEED_MAX)`
以指定速度移動到**絕對位置** `target`（0..4095），方向由 `target` 自動決定。
- 只更新 buffer，**不發送**；配合 `show_all()` 一次推送。
- `speed=0` 或已到目標 → 直接停。

### `move(addr, delta, speed=SPEED_MAX)`
以指定速度**相對位移** `delta`（單位 = 全程的 1/4095，可正可負）。

### `position(addr)`
讀取一台的**估算位置**（0..4095），讀前自動結算。

### `update()`
**週期呼叫**：重算全部位置，到達目標/邊界的台自動停（改 buffer 為 `STOP`）。
- **非阻塞**、無 sleep、無 timer。
- 只改 buffer，**不發送**；之後再 `show_all()` 把停止幀推送出去。

### `set_t_full(addr, direction, ms)`
設定某台全速走完全程 ms。`direction >= 0` 伸、`< 0` 縮。

### `calibrate(addr, direction, speed, elapsed_ms)`
記錄某台某速度下實測的「走完全程 ms」，寫入該台校準表。重複呼叫覆蓋舊值。

### 位置估算的運作方式

每台記錄四個欄位（索引 `addr-1`，與 buffer 同構，皆為整數）：

| 欄位 | 意義 |
|---|---|
| `_pos` | 目前估算位置（定點） |
| `_pos0` | 本次移動啟動時位置（定點） |
| `_t0` | 本次移動啟動時間（ticks） |
| `_rate` | 本次速率（含正負號；0 = 停） |
| `_target` | 目標位置（定點；`None` = 只跑不停） |

每次結算用**閉式公式**重算（非逐 tick 累加）：

```
pos = pos0 + rate × elapsed
```

同一段等速移動內只有一次乘法，沒有累積捨入誤差。

---

## 7. 校準：三檔速度點

### 7.1 為什麼要校準

「行程 = 速度 × 時間」是開迴路估算，準不準取決於「速度 byte → 實際速度」這條曲線。它**不是平均線性**：

- **低速死區**：佔空比太低，扭力打不贏靜摩擦＋負載 → 根本不動。
- **中段**：大致線性，但整條線有偏移。
- **近飽和**：電壓到頂、負載下掉速。

所以不能只用一個「全速全程時間」就套用到所有速度。用**低/中/高三個實測點**做分段內插，才能同時抓住「死區下界」與「非線性」。

### 7.2 三點內插演算法

**不是**擬合一條直線（不假設三點共線），而是**分段線性內插**：每相鄰兩點連一條線，查詢時只取包住目標速度的那一段。

先反轉：全程時間 `ms` 不是線性的（它是 `1/速度`），先轉成**速率**：

```
rate(speed) = (4095 << 12) // ms
```

範例（`address=12`，全程格數 = 16773120）：

| speed | ms | rate（每 ms 格數，定點） |
|---|---|---|
| 24 | 24000 | 16773120 // 24000 ≈ 699 |
| 64 | 12000 | 16773120 // 12000 ≈ 1398 |
| 128 | 6000 | 16773120 // 6000 ≈ 2796 |

查詢 `speed = 44`（落在 24～64）：

```
rate = 699 + (1398 - 699) × (44 - 24) / (64 - 24) = 1048
```

**邊界規則**：

| 情況 | 結果 |
|---|---|
| 命中量測點 | 直接查表 |
| 落在兩點之間 | 線性內插 |
| 只給一項（如 `{128:3000}`） | 從原點線性正比 `rate_full × speed / 128`（無死區） |
| 低於最低量測點 | 回 **0（死區）**，視為停 |
| 高於最高點（≤128） | 內插到全速端點（128 → rate_full 永遠存在），不會被錯 clamp |

**效能**：`_lookup_rate` 只在**下指令**（`move_to`/`move`）時跑一次，純整數、O(點數)。每個週期真正跑的是 `_recompute` 的單一乘法 `pos = pos0 + rate × elapsed`，與內插無關，成本極低。

### 7.3 校準工具 `tools/ESP/calibrate_motor.py`

這是**測試/校準工具**（位於 `tools/ESP/`，不屬於 `slave/` 的獨立系統）。在硬體校準台上跑，用**限位開關自動偵測**到達，量每個速度點的全程時間。

```python
from lib.hw.uart_motor import UartMotor
from tools.calibrate_motor import MotorCalibrator, report

motor = UartMotor({"version": 1, "addresses": [11], "uart": uart})

cal = MotorCalibrator(
    motor, 11,
    extend_pin=4,      # 伸到頭接的 GPIO
    retract_pin=5,     # 縮到頭接的 GPIO
    timeout_ms=30000,  # 超時 = 該速度推不動（死區）
)
results = cal.run([24, 64, 128])   # 低 / 中 / 高
report(results)                     # 印出是否線性的報告
cal.save(results, "/calib")         # 寫 JSON
```

**每個速度點的流程**：`home`（全速縮回對齊起點）→ 該速度伸出計時 → 該速度縮回計時。

**限位開關假設**（需依實物調整）：
- 伸到頭接 `extend_pin`、縮到頭接 `retract_pin`。
- 預設低電平觸發（導通 = `value()==0`），可用 `active_high=True` 反轉。

**`report(results)` 會告訴你「是否線性」**：計算每個速度點的「等效全速時間」`ms × speed / 128`，若各點接近 → 線性；偏差超過 15% → 回報「非線性」（通常是低速偏慢）。

**JSON 檔格式**（`save()` 產生，每速度一檔 `speed_XXX.json`）：

```json
{"address": 11, "speed": 24, "forward_ms": 16000, "reverse_ms": 17000}
```

`forward_ms` / `reverse_ms` 為 `null` 表示該方向死區。

### 7.4 讀回 `tools/ESP/calib_loader.py`

```python
from tools.calib_loader import load_calibration

load_calibration(motor, "/calib")   # 讀整個目錄的 *.json
# 或 load_calibration(motor, ["/calib/speed_024.json", ...])
```

依檔內 `address` 分台填入 `calibrate()`；`null` 的速度點跳過；`speed=128` 同步該台 `t_full`。

---

## 8. 完整使用範例

```python
from machine import UART
from lib.hw.uart_motor import UartMotor, SPEED_MAX, SPEED_MED, POS_MAX
from tools.calibrate_motor import MotorCalibrator, report
from tools.calib_loader import load_calibration

uart = UART(0, baudrate=9600)

# ── 第一階段：校準（拿到三檔數據）──
motor = UartMotor({"version": 1, "addresses": [11, 12], "uart": uart})

cal11 = MotorCalibrator(motor, 11, extend_pin=4, retract_pin=5)
res11 = cal11.run([24, 64, 128])
report(res11)
cal11.save(res11, "/calib")

cal12 = MotorCalibrator(motor, 12, extend_pin=6, retract_pin=7)
res12 = cal12.run([24, 64, 128])
cal12.save(res12, "/calib")

# ── 第二階段：正式使用 ──
motor = UartMotor({"version": 1, "addresses": [11, 12], "uart": uart})
load_calibration(motor, "/calib")   # 一次讀回，依 address 分台

# 或直接寫進 config：
# motor = UartMotor({
#     "version": 1, "addresses": [11, 12], "uart": uart,
#     "calib": {
#         11: {128: 3000},
#         12: {24: 24000, 64: 12000, 128: 6000},
#     },
# })

motor.move_to(11, POS_MAX, SPEED_MAX)
motor.move_to(12, 2048, SPEED_MED)
motor.show_all()

while True:
    motor.update()
    motor.show_all()
    p11 = motor.position(11)
    p12 = motor.position(12)
    # 上層邏輯：到達後下新指令等
```

---

## 9. 常數參考

| 名稱 | 值 | 說明 |
|---|---|---|
| `HEADER` | `0xFF` | 幀頭 |
| `ENDING` | `0xFE` | 幀尾 |
| `STOP` | `0x80` | 停 |
| `FWD` | `0x40` | 正轉中速 |
| `REV` | `0xC0` | 反轉中速 |
| `FWD_FS` | `0x00` | 正轉全速 |
| `REV_FS` | `0xFF` | 反轉全速 |
| `SPEED_MAX` | `128` | 行程模式全速 |
| `SPEED_MED` | `64` | 行程模式中速 |
| `SPEED_MIN` | `1` | 最慢可用速度（含以下視為停） |
| `SPEED_STOP` | `0` | 行程模式停 |
| `POS_MAX` | `0x0FFF`（4095） | 滿行程 |
| `DEFAULT_T_FULL_MS` | `3000` | 全速全程 ms 預設值（需校準） |

### 模組層級函數

- `speed_to_byte(speed, direction)` —— 速度 + 方向 → 速度 byte。
- `register_command_method(version, build_broadcast, build_single)` —— 註冊新的協定版本編碼器。

---

## 10. 注意事項與限制

1. **`set` / `move_to` / `set_many` 都不發送**。`show_all()` 是統一整批發送口；`send` / `send_all` / `stop_all` 才立即寫 UART。
2. **address 必須在初始化列表內**，否則 `ValueError`。
3. **位置是估算值**：這是「速度 × 時間」的開迴路估算，精度取決於校準準不準，且會隨**電壓 / 負載 / 溫度**漂移。要精確定位需加上限位開關（home）或編碼器閉環，本函式庫目前只做開迴路估算。
4. **啟動/停止暫態**：馬達加減速與滑行會造成短行程誤差，比「速度是否線性」更影響短行程精度。
5. **正反速度通常不同**：本函式庫 `calib` 預設正反同值；若實測差異大，用 `calibrate(addr, direction, ...)` 分開餵。
6. **MicroPython 上 `save()` / `load_calibration()` 需要可寫的 Flash 或 SD**，路徑如 `/calib` 須有寫入權限。
7. `t_full_ms` 預設 3000 只是佔位，**實際一定要校準過**才準。
8. 同步 broadcast 只消除同一 frame 內逐 address 的下令先後差；開迴路摩打的實際行程仍可能因機械負載、電壓和個體速度而不同。那部分才需要 Calibration。

## 相關文件

- `03_notes/02_buffer_architecture.md` — 多級緩衝架構（L0 DMA 分配慣例）
- `01_protocol/02_command_index.md` — 完整指令索引（UART 幀協定的相關指令）

---

## Hi-Nu Black JSON motor 測試模式

共用 mapping：`slave/pixel/map/hi_nu_uart_motor_test.json`。每塊 Slave 控制自己
`config.json` 內的全部 UART motor：

| Slave profile | UART motor address |
|---|---|
| `ports/S3/ESP32-S3_1_18_hinu_black/slave13/config.json` | `45`, `46`, `48`, `49` |
| `ports/S3/ESP32-S3_1_18_hinu_black/slave20/config.json` | `60`, `61`, `70`, `71` |

兩個 profile 均使用 `frame_interval_ms=20`（50 FPS），所以 500 frame = 10 秒。
兩者的 `uartMotor.GPIO.uart` 都是 list index `1`，對應第二個 UART（`id=2`、9600 baud）。
兩者都使用 GPIO12 TX、9600 baud 與原始 direct motor frame，不依賴 optional
broadcast parser。Stop 轉換仍會即時發送。
RenderTask 的 `is_streaming`／`is_ready`／`is_paused` 控制旗標不經 500ms cache，
MODE_SET 到達後不會因兩塊 Slave 各自的 cache 到期相位而相差一個 render frame。

目前 Hi-Nu 測試 profile **沒有 `calib` 欄位**，所以八台收到相同 raw command，
不作逐台速度補償；`calibrate()`、`calib` loader 及所有校準程式碼仍完整保留，
日後實測需要時可直接啟用。

| Mode ID | 名稱 | UART motor 行為 |
|---:|---|---|
| `0` | `motor_diagnostic` | Direction A，effect marker `0x01` 轉 raw `0x00` 真全速，10 秒後保持 `0x80` Stop |
| `1` | `motor_max_open` | Direction B/Open，raw `0xFF` 真正最高速度，10 秒後保持 Stop |
| `2` | `motor_max_close` | Direction A/Close，全部 motor 立即以 raw `0` 最快關閉，10 秒後保持 Stop |

Mode 0 定義直接內嵌於 `slave/pixel/registry.json.modes`，不另建
`pixel/modes/motor_diagnostic.json`；registry `list` 引用 `motor_diagnostic`，部署時
保持 `auto_play=false`，待兩塊 Slave 都 ready 後才同步觸發，避免上電次序變成測試誤差。

Mode 0 的 JSON 使用非零 W=`0x01` 作明確 marker；Pixel motor 安全層把 marker 轉成
UART-412 raw `0x00`，即 Direction A 真正最高速度。全零 big buffer 仍視為未寫入並
轉成 `0x80` Stop，所以開機、清畫面或 effect 空值不會 accidental full-speed。

ATtiny412 `updateMotor()` 是 dead-zone 真源：raw `0x00` 是 Direction A 最大
（IN1 PWM 254），raw `0xFF` 是 Direction B 最大（IN2 PWM 254）；只有 raw
`0x7F` 與 `0x80` 令兩個輸出 PWM 都為 0。本系統統一以 `0x80` 表示 Stop。

Mode 2 逐 frame 對齊 Hi-Nu `patterns_uart_dc_motor.cpp`／`storyMode_dev.cpp`：先算
`round(sin(pi * progress) * 100)` motion-profile percent，再套 dev 的 Sine speed
curve `round(sin(pi/2 * percent/100) * 100)`，最後用 C++ 的整數四捨五入公式轉
Direction A/B raw byte。JSON 的 `direction`、`speed_percent`、`speed_curve` 和累加
`end_Time` 仍是效果／時間真源。Mode 2 使用 `rgbw` 傳輸，R=`0xFF` 作明確 raw
旗標，W 保留完整 `0x00..0xFF`；因此峰值 raw `0x00` 和鄰近 raw `0x01` 不會與
空白 big-buffer W=`0` 混淆。

以下是 2026-08-29 舊 Slave1／2 profiles 的四摩打歷史實機結果，不代表目前
Slave13／20 八 motor 已完成實機驗證：Host 對兩塊 motor board 的
`play()` trigger 相差 `31.167 us`；Slave 1 地址 `15/19` 運行 `10002.314 ms`，
Slave 2 地址 `12/21` 運行 `10002.279 ms`。兩板均以 raw `0x00` 開始並以 raw
`0x80` 停止。這證明命令開始／停止同步；開迴路推桿若仍有行程差，來源是個體
速度、供電或負載，需 calibration／feedback 才能補償。

PC 驗證：

```bash
python3 -B test/pixel/test_uart_motor_storymodes.py
```
