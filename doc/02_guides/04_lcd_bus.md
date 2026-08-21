# lcd_bus — LCD 總線模組（C 層 + Python 統一層）

> **用途**：LCD panel I/O 的「bus」物件總覽。C 層 `lcd_bus` 提供四種實體總線（SPI/I80/I2C/RGB）；Python 層 `lcd_bus.py` 統一 API + 非同步 DMA 排隊。
> **分類**：使用教學（02_guides）
> **最後更新**：2026-08-18（合併原 `lcd.md` 舊版 API 與 `mp_heap_caps.md` 新版 API；新版以本文件為準）
> **位置**：User C Module（`ext_mod/mp_lcd_bus/`）；Python 層 `lcd_bus.py` 隨 firmware 提供

> ⚠️ **舊文件 `doc/lcd.md` 描述的舊版 API（`init/tx_param/tx_color`）已過時**。最新 firmware 的 API 見 `05_tft_usage.md`（`write/wait/pending/wait_all` 風格）。本文件為模組總覽，兩代 API 都列出，標明新舊。

---

## 0. 模組一覽（新版）

| 模塊 | 層級 | 功能 |
|---|---|---|
| `heap_caps` | C | DMA/PSRAM 記憶體分配與查詢（見 `03_memory_management.md`） |
| `spi_dma` | C | SPI 非同步 DMA（1/2/4/8 線自動檢測） |
| `i80_dma` | C | I80 並行總線非同步 DMA |
| `rgb_dma` | C | RGB 並行總線非同步 DMA（VSYNC 回調） |
| `lcd_bus`（C 層） | C | `SPIBus` / `I2CBus` / `I80Bus` / `RGBBus` 四種 type（ESP-IDF `esp_lcd` 底層） |
| `lcd_bus.py`（Python 層） | Python | 統一總線 API（`SpiBus`/`I2cBus`/`I80Bus`/`RgbBus`），自動檢測多線模式 |

### 架構

```
┌──────────────────────────────────────┐
│  Panel Driver (管理 DC/CS 時序)       │
│  dc.low() → bus.write(cmd)           │
│  dc.high() → bus.write(pixels)       │
├──────────────────────────────────────┤
│  lcd_bus.py  (純 Python)             │
│  SpiBus / I2cBus / I80Bus / RgbBus   │
├──────┬──────┬──────┬─────────────────┤
│spi   │(i2c) │i80   │rgb              │
│_dma  │      │_dma  │_dma             │
│.c    │ mach-│.c    │.c               │
│      │ ine  │      │                 │
│      │.I2C) │      │                 │
├──────┴──────┴──────┴─────────────────┤
│  ESP-IDF GDMA 硬體                   │
│  queue_trans → DMA → get_trans_result│
└──────────────────────────────────────┘
```

### 設計原則（新版）

- **DC/CS 不由總線管理** — 交給上層 panel driver
- **data tuple 自動決定線數** — `data=(mosi,)` → 1線, `data=(d0..d3)` → 4線 (Quad), `data=(d0..d7)` → 8線 (Octal)
- **write / readinto / write_readinto 全部非同步** — 返回 `trans_id`，用 `wait()` 查完成
- **隊列深度**: SPI 4級 / I80 4級 / RGB 2級
- **GC 安全**: `ref_bufs[]` 持有 buffer 引用，`wait()` 時釋放

---

## 1. 新版 API：非同步 DMA bus（`spi_dma` / `i80_dma` / `rgb_dma`）

### 1.1 spi_dma

```python
import spi_dma

# 1 線 標準 SPI
spi_dma.init(data=(35,), clk=36, freq=40_000_000)

# 4 線 Quad SPI  (auto-detect from data length)
spi_dma.init(data=(35, 36, 37, 38), clk=39, freq=80_000_000)

# 8 線 Octal SPI
spi_dma.init(data=(d0, d1, d2, d3, d4, d5, d6, d7), clk=..., freq=80_000_000)
```

| 方法 | 非同步 | 返回 | 說明 |
|---|---|---|---|
| `init(data, clk, freq, host)` | — | — | 初始化 SPI 總線 |
| `write(buf)` | ✅ | `trans_id` | fire-and-forget 寫入 |
| `readinto(buf, write_val=0)` | ✅ | `trans_id` | 非同步讀取 |
| `write_readinto(wbuf, rbuf)` | ✅ | `trans_id` | 全雙工非同步 |
| `is_busy()` | — | `bool` | 隊列是否有未完成傳輸 |
| `pending()` | — | `int` | 隊列中等待數 |
| `wait(trans_id, timeout_ms=-1)` | 阻塞 | `bool` | 等待特定傳輸完成 |
| `wait_all(timeout_ms=-1)` | 阻塞 | — | 等待全部完成 + 主動 GC |
| `lane_count()` | — | `int` | 數據線數量 |
| `deinit()` | — | — | 釋放資源 |

**多線自動檢測**：`data` tuple 長度決定 SPI 傳輸模式：

| data 長度 | 模式 | SPI_TRANS_MODE |
|---|---|---|
| 1 | 標準 SPI | (default) |
| 2 | Dual SPI | `SPI_TRANS_MODE_DIO` |
| 4 | Quad SPI | `SPI_TRANS_MODE_QIO` |
| 8 | Octal SPI | `SPI_TRANS_MODE_OCT` |

**readinto 原理**：`readinto` 用一個預分配的 32KB `zero_buf` 當 tx_buffer（共用，只讀不寫）。多個排隊的讀事務安全共存。rx buffer 被 `ref_bufs[]` pin 住直到 `wait()` 釋放。

### 1.2 i80_dma

僅在 ESP32-S3/P4（支援 `SOC_LCD_I80_SUPPORTED`）上可用。

```python
import i80_dma

# 8-bit I80
i80_dma.init(data=(d0, d1, d2, d3, d4, d5, d6, d7), wr=10, cs=11, freq=10_000_000)

# 16-bit I80
i80_dma.init(data=(d0, d1, ..., d15), wr=10, freq=10_000_000)
```

與 `spi_dma` 一致的 API（`write`, `is_busy`, `pending`, `wait`, `wait_all`, `lane_count`, `deinit`）。不支援 `readinto` / `write_readinto`（I80 是單向輸出）。完成信號來自 ESP-IDF 的 `on_color_trans_done` 回調。

### 1.3 rgb_dma

僅在 ESP32-S3/P4（支援 `SOC_LCD_RGB_SUPPORTED`）上可用。

```python
import rgb_dma

rgb_dma.init(
    data=(d0, d1, d2, d3, d4, d5, d6, d7),
    hsync=12, vsync=13, de=14, pclk=15,
    width=480, height=272, freq=9_000_000,
    hsync_front_porch=2, hsync_back_porch=40, hsync_pulse_width=41,
    vsync_front_porch=2, vsync_back_porch=10, vsync_pulse_width=10,
)
```

| 方法 | 非同步 | 返回 | 說明 |
|---|---|---|---|
| `write(buf, x, y, w, h)` | ✅ | `trans_id` | 寫入像素區域 (預設全螢幕) |
| `is_busy` / `pending` / `wait` / `wait_all` | — | — | 同上 |
| `lane_count` / `deinit` | — | — | — |

不支援 `readinto` / `write_readinto`。完成信號來自 VSYNC 中斷回調。隊列深度為 2（雙緩衝由 VSYNC 速律限制）。

---

## 2. 新版 API：Python 統一層（`lcd_bus.py`）

```python
from lcd_bus import SpiBus, I2cBus, I80Bus, RgbBus
```

### 四種總線 — 統一 API

```python
# SPI: data=(mosi,), clk
bus = SpiBus(data=(35,), clk=36, freq=40_000_000)

# I2C: data=(sda_pin,), clk=scl_pin, addr
bus = I2cBus(data=(sda,), clk=scl, addr=0x3C, freq=400_000)

# I80: data=(d0..d7), wr
bus = I80Bus(data=(0,1,2,3,4,5,6,7), wr=10)

# RGB: data=(d0..d7), hsync, vsync, de, pclk, width, height
bus = RgbBus(
    data=(0,1,2,3,4,5,6,7),
    hsync=12, vsync=13, de=14, pclk=15,
    width=480, height=272,
)
```

### 統一方法

| 方法 | SPI | I2C | I80 | RGB |
|---|---|---|---|---|
| `write(buf)` | ✅ | ✅ | ✅ | ✅ |
| `readinto(buf)` | ✅ | ✅ | ❌ | ❌ |
| `write_readinto(w, r)` | ✅ | ✅ | ❌ | ❌ |
| `is_busy()` | ✅ | ✅ | ✅ | ✅ |
| `pending()` | ✅ | ✅ | ✅ | ✅ |
| `wait(tid)` | ✅ | ✅ | ✅ | ✅ |
| `wait_all()` | ✅ | ✅ | ✅ | ✅ |
| `lane_count` | ✅ | ✅ | ✅ | ✅ |
| `deinit()` | ✅ | ✅ | ✅ | ✅ |

### 使用模式（雙緩衝）

```python
from lcd_bus import SpiBus
import heap_caps

bus = SpiBus(data=(35,), clk=36, freq=40_000_000)
buf_a = heap_caps.malloc(FRAME_SIZE, heap_caps.CAP_DMA)
buf_b = heap_caps.malloc(FRAME_SIZE, heap_caps.CAP_DMA)

while True:
    render(buf_a)
    bus.write(buf_a)               # 發射 A
    render(buf_b)
    bus.write(buf_b)               # 發射 B
    if bus.pending() >= 2:         # 回來看看排隊情況
        bus.wait_all()

bus.deinit()
heap_caps.free([buf_a, buf_b])
```

---

## 3. 舊版 API：C 層 `lcd_bus`（`init/tx_param/tx_color`）

> ⚠️ 舊版 API，最新 firmware 已改用上述新 API；以下保留供讀舊程式碼對照。

MicroPython 中 `import lcd_bus`，提供 `lcd_bus.SPIBus`、`lcd_bus.I80Bus`、`lcd_bus.I2CBus`、`lcd_bus.RGBBus` 四種 type。ESP32 使用 ESP-IDF `esp_lcd`；非 ESP32 為 stub（部分丟 `NotImplementedError`）。

### 共用方法（多數 bus type）

| 方法 | 說明 |
|---|---|
| `init(width, height, bpp, buffer_size, rgb565_byte_swap)` | 初始化底層 bus I/O；`bpp==16` 時保存 swap 設定。失敗丟 `OSError` |
| `deinit()` / `__del__` | 釋放資源。失敗丟 `ValueError` |
| `get_lane_count()` | lane 數（SPI 1/2/4，I80/RGB 為 bus width） |
| `register_callback(cb)` | 設定傳輸完成 callback（ISR context 呼叫，保持精簡） |
| `tx_param(cmd, params=None)` | 送命令 + 可選參數 buffer。不支援 → `OSError` |
| `rx_param(cmd, data)` | 讀參數到可寫 buffer。不支援 → `OSError` |
| `tx_color(cmd, data, x0, y0, x1, y1)` | 送像素資料。無 callback 時 busy-wait |

### 建構（ESP32）

```python
# SPIBus
lcd_bus.SPIBus(dc, host, sclk, freq, mosi, *, miso=-1, cs=-1, wp=-1, hd=-1,
               quad_spi=False, tx_only=False, cmd_bits=8, param_bits=8,
               dc_low_on_data=False, sio_mode=False, lsb_first=False, cs_high_active=False,
               spi_mode=0)

# I2CBus
lcd_bus.I2CBus(sda, scl, addr, *, host=0, control_phase_bytes=1, dc_bit_offset=6,
               freq=10_000_000, cmd_bits=8, param_bits=8, dc_low_on_data=False,
               sda_pullup=True, scl_pullup=True, disable_control_phase=False)

# I80Bus
lcd_bus.I80Bus(dc, wr, data0..data7, *, data8..data15=-1, cs=-1, freq=10_000_000,
               dc_idle_high=False, dc_cmd_high=False, dc_dummy_high=False, dc_data_high=True,
               cmd_bits=8, param_bits=8, cs_active_high=False, reverse_color_bits=False,
               swap_color_bytes=False, pclk_active_low=False, pclk_idle_low=False)

# RGBBus
lcd_bus.RGBBus(hsync, vsync, de, disp, pclk, data0..data7, *, data8..data15=-1,
               freq=8_000_000, bb_size_px=0, hsync_front_porch=0, hsync_back_porch=0,
               hsync_pulse_width=0, hsync_idle_low=False, vsync_front_porch=0,
               vsync_back_porch=0, vsync_pulse_width=1, vsync_idle_low=False,
               de_idle_high=False, pclk_idle_high=False, pclk_active_neg=False,
               disp_active_low=False, refresh_on_demand=False, bb_inval_cache=False)
```

- 非 ESP32：`I2CBus` / `RGBBus` 一律丟 `NotImplementedError`；SPI/I80 需要 port 提供 `mp_hal_pin_output`。
- ESP32 RGBBus 方法可用性：有 `get_lane_count`/`register_callback`/`tx_color`/`init`/`deinit`/`__del__`；沒有 `tx_param`/`rx_param`。
- `rgb565_byte_swap=True` 時送出路徑會**就地** byte swap buffer（可寫 buffer）。

### 舊版範例

```python
from lcd_bus import SPIBus

bus = SPIBus(21, 1, 18, 40_000_000, 23, miso=-1, cs=5)
bus.init(width=240, height=240, bpp=16, buffer_size=240 * 240 * 2, rgb565_byte_swap=False)
bus.tx_param(0x36, b"\x00")
frame = bytearray(240 * 240 * 2)
bus.tx_color(0x2C, frame, 0, 0, 240, 240)
bus.deinit()
```

---

## 4. Panel Driver 範例（ST7789 + SpiBus，新版）

```python
from machine import Pin
from lcd_bus import SpiBus
import heap_caps

dc = Pin(37, Pin.OUT)     # DC 由上層管理
cs = Pin(38, Pin.OUT)

bus = SpiBus(data=(35,), clk=36, freq=40_000_000)

cs.low()
dc.low()
bus.write(b'\x11')        # SLPOUT
bus.wait_all()

dc.high()
fb = heap_caps.malloc(240 * 320 * 2, heap_caps.CAP_DMA)
bus.write(fb)

bus.deinit()
heap_caps.free(fb)
```

---

## 5. 構建

### CMake（ESP32 / ESP-IDF）

`micropython.cmake` 已包含所有源碼：

- `esp32_src/heap_caps.c`
- `esp32_src/spi_dma.c`
- `esp32_src/i80_dma.c`
- `esp32_src/rgb_dma.c`

會自動獲取 `esp_lcd` 的 include 路徑。非 ESP32 平台僅 `heap_caps` 模塊可用（功能有限）。

### 注意事項

- **DC/CS** 不由總線管理，需上層自行操作 GPIO
- **`heap_caps.free()`** 必須手動調用，不受 GC 管理
- **I2C** 無 DMA 支援，傳輸為阻塞模式；其餘三種總線均支援非同步 DMA
- **RGB** `write()` 的 `x, y, w, h` 預設為 `(0, 0, panel_w, panel_h)`
- **完成時間**: SPI 可用 `wait()` 阻塞等待，I80/RGB 使用忙等輪詢 `done_flags[]`
- **I80/RGB** 僅 ESP32-S3/P4 可用；其他晶片 import 會得到空模塊

---

## 6. 快速測試 + 速度測試

```python
import test_bus
test_bus.run_all()
```

### 功能測試

| # | 測試 | 項目 |
|---|---|---|
| 1 | `heap_caps` | 分配/釋放、capability 常數、堆統計 |
| 2 | `SpiBus` | 寫入、4級排隊、隊列滿防護、deinit |
| 3 | SPI 多線 | 1/2/4/8 線自動檢測 |
| 4 | `I2cBus` | 初始化、寫入 |
| 5 | `I80Bus` | 排隊、deinit |
| 6 | `RgbBus` | 全螢幕/區域寫入 |
| 7 | 壓力 | init → write → deinit 循環 3 次 |

### 速度測試（測試 8）

| 測試項 | 內容 |
|---|---|
| 8a | SPI 1線 40MHz — 256B/1KB/4KB/16KB/32KB |
| 8b | SPI 1線 — 10/20/40/60/80MHz (32KB) |
| 8c | SPI Quad 4線 40MHz — 4KB/16KB/32KB |
| 8d | SPI Quad 4線 80MHz — 32KB |
| 8e | SPI Octal 8線 40MHz — 32KB |
| 8f | I80 8-bit 10MHz — 16KB/32KB |
| 8g | RGB 8-bit 9MHz — 全螢幕 |
| 8h | 速度摘要 — 各總線 32KB 吞吐量對比 |

輸出格式範例：

```
  test         │   size │         fire (queue) │          wait (done) │                    total
  ─────────────┼────────┼───────────────────────┼──────────────────────┼────────────────────────
  32KB 1線 40M │  32768B │     42us   763 MB/s │   4500us   7282 KB/s │   4542us   7215 KB/s
  32KB 4線 40M │  32768B │     38us   862 MB/s │   1150us  28494 KB/s │   1188us  27578 KB/s
  32KB 4線 80M │  32768B │     35us   936 MB/s │    590us  55539 KB/s │    625us  52429 KB/s
```

## 相關文件

- `03_memory_management.md` — heap_caps 記憶體分配
- `05_tft_usage.md` — 最新 TFT + lcd_bus 使用指南（ST7789 driver 包裝）
- `03_notes/02_buffer_architecture.md` — 多級緩衝架構（L5 輸出層）
- `03_notes/05_psram_zero_block_plan.md` — PSRAM framebuffer 零阻塞計劃
