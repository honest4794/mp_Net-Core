# Raw SD 繞過 FAT 方案：兩階段計劃

> **用途**：效能優化計劃——繞過 MicroPython FAT（oofatfs）的 512-byte sector cache 限制，用 raw sector 直讀達成接近 SDIO 硬體上限的吞吐。
> **分類**：筆記（03_notes）
> **最後更新**：2026-08-18
> **相關**：`02_guides/01_fast_io.md`（現有 managed-area 方案，本計劃為其進化方向）

## 背景

MicroPython 的 FAT 實作（oofatfs）為了極小 RAM 佔用，將 FAT sector cache 鎖在 512 bytes，導致每次 `readblocks()` 僅請求 1 個 sector。即使上層 buffer 設為 64KB，底層仍分解為 128 次獨立呼叫，每次都要 Python→C dispatch + SD 協議交握，總 overhead 極大。實測 FAT + SDIO 4-bit 連續讀取僅 ~1.8 MB/s，遠低於 SDIO 硬體能力（~8-10 MB/s raw）。

本方案透過 `sd.readblocks()` 直接操作 raw sector，完全繞過 oofatfs，並以自訂 TOC（目錄表）取代 FAT 目錄結構。

### 現有架構中的任務分配

Core1 同時承擔多個即時任務，SD 讀取的阻塞時間直接影響 UART 輪詢頻率與命令處理延遲：

| Core1 任務 | 時間敏感度 | 受 SD 阻塞影響 |
|------------|:---:|:---:|
| `dp_manager`（SD 讀取） | 高 | — |
| `circuit`（UART 輪詢） | 高 | 延遲飆高可能溢位 FIFO |
| `bus_decode`（命令分派） | 高 | 命令處理延遲增加 |
| `network`（WiFi/WS/TCP） | 中 | ping/pong 可能逾時 |
| `display`（SPI DMA） | 高 | fire-and-forget，不影響 |
| `web_ui`（HTTP） | 低 | 可接受 |
| `log` | 低 | 可接受 |

---

## Phase 1: Raw SD Python 層 + Benchmark

### 目標

- 測量 `sd.readblocks()` raw speed，確認瓶頸是否確實在 oofatfs
- 實現 `lib/raw_sd.py`：TOC 目錄表 + raw sector 讀寫
- PC 端寫入工具
- 替換現有管線中的 FAT-based 讀取為 raw readblocks()

### 1.1 Benchmark：`sd.readblocks()` raw speed

確認繞過 FAT 後實際可達的吞吐量。使用 SDIO 4-bit mode，直接對 SDCard 物件做連續 sector 讀取。

```
測試矩陣：
  - buffer 大小：512B, 4KB, 16KB, 32KB, 64KB
  - 總讀取量：8MB
  - 同時對比 FAT-based readinto() 作為 baseline
```

期望：raw readblocks 應達到 5-8 MB/s（vs FAT 的 ~1.8 MB/s）

### 1.2 `lib/raw_sd.py` 模組

#### Raw Partition Layout

```
Sector 0 ─┬─ magic: 4 bytes  ("RAW1")
          ├─ version: 2 bytes
          ├─ entry_count: 2 bytes
          ├─ entry[0]:  name[16] | offset_sector[4] | size_sectors[4]
          ├─ entry[1]:  name[16] | offset_sector[4] | size_sectors[4]
          ├─ ...
          └─ (padding to sector boundary, 512 bytes total)

Sector X ─── entry[0] 的 pack 資料（連續，無碎片化）
Sector Y ─── entry[1] 的 pack 資料（連續）
```

TOC 固定 1 個 sector（512 bytes），支援最多 ~20 個 entry。開機時一口氣讀完，之後所有 seek 都是 O(1) 數學運算。

#### API（對齊現有 `pack_source.py` 介面）

```python
from lib.raw_sd import RawSD, RawFile

sd = SDCard(slot=0, width=4, sck=7, cmd=6, data=(15,16,4,5), freq=40_000_000)

raw = RawSD(sd, start_sector=262144)    # 128MB offset
raw.mount()                              # 讀取 TOC
f = raw.open("video_01")                # 打開 TOC entry

# seek + readinto，跟 pack_source 介面一致
f.seek(5_000_000)
n = f.readinto(buf)

# 寫入（WiFi update / 初始化）
raw.write_entry("video_02", size_bytes=50_000_000)
f = raw.open("video_02")
for chunk in wifi_stream:
    f.write(chunk)
f.close()                               # 更新 TOC 中的 final size
```

### 1.3 PC 端寫入工具

```python
# pc_raw_write.py
# Usage: python pc_raw_write.py D: video_01.jpk --offset_mb 128
# 直接寫入 SD 卡的 raw sector offset
```

### 1.4 管線替換

將現有 `pack_source.py`（FAT-based）替換為 `raw_sd.RawFile`：

```python
# 之前
pack = PackSource("/sd/video.jpk")
pack.read_next_into(dst, max_len)

# 之後
f = raw.open("video_01")
f.seek(frame_offset)
f.readinto(dst)
```

`RawFile` 實現與 `PackSource` 一致的 `read_next_into()` / `seek()` 介面，使上層管線（Core1_engine / Core0_worker）無需改動。

### 1.5 驗收標準

- raw readblocks 吞吐量 ≥ 5 MB/s
- 無 FAT 碎片化影響
- seek 延遲 O(1)（不受檔案大小影響）
- 與現有 `pack_source` API 相容

---

## Phase 2: Async SD C Module（`mp_raw_sd`）

### 前提

Phase 1 完成後，若出現以下情況則觸發 Phase 2：
- UART 實測有溢位（RX FIFO 128 bytes 在 SD 阻塞期間填滿）
- Core1 的 SD 阻塞時間影響命令處理即時性
- WiFi 吞吐受 SD 阻塞干擾
- 期望進一步釋放 Core1 做更多任務

### 目標

實現真正非阻塞的 SD 讀取——如同 `spi_dma` 之於 SPI：發起讀取後立刻 return，背景 DMA 完成後可輪詢。

### 2.1 架構

```
mp_raw_sd/                          ← 新的 User C Module repo
├── micropython.cmake
├── micropython.mk
└── esp32_src/
    └── raw_sd.c                    ← C 模組主體
```

#### 編譯

```bash
make USER_C_MODULES=../mp_raw_sd/micropython.cmake BOARD=ESP32_GENERIC_S3 all
```

### 2.2 GC 安全設計（核心難點）

MicroPython GC 可在任何時刻 compact heap，若 FreeRTOS background task 持有指向 GC heap 的裸指標，DMA 寫入已被移動的記憶體將導致記憶體損毀。

**解決方案：CAP_DMA buffer 隔離**

- 內部 DMA buffer 使用 `heap_caps_malloc(..., MALLOC_CAP_DMA)` 分配
- CAP_DMA 記憶體不在 MicroPython GC heap 上，GC compact 永遠不會觸及
- C static context（`_ctx`）完全在 GC 視野之外

```c
// raw_sd.c
typedef struct {
    sdmmc_card_t *card;
    uint8_t *dma_buf;       // CAP_DMA，GC 碰不到
    size_t sector;
    size_t count;
    bool busy;
    bool done;
    esp_err_t result;
} sd_async_ctx_t;

static sd_async_ctx_t _ctx;  // C global static
```

### 2.3 ISR 狀態機

SD 讀取協議不是純 DMA push，而是 request-response 狀態機：

```
發送 CMD17 → 等卡回應 R1 → 等 data start token (0xFE) → 啟動 DMA 接收 → DMA 完成中斷 → CRC 檢查
```

每個階段由硬體中斷驅動，ISR 推進狀態機，最終設定 `_ctx.done = true`。

```c
typedef enum {
    SD_IDLE,
    SD_CMD_SENT,        // CMD17 已發，等 R1
    SD_WAIT_TOKEN,      // R1 已收到，等 data token
    SD_DMA_RUNNING,     // DMA 正在接收
    SD_DONE,            // CRC OK
    SD_ERROR            // CRC fail / timeout
} sd_state_t;
```

### 2.4 Python API

```python
import raw_sd

sd = SDCard(slot=0, width=4, sck=7, cmd=6, data=(15,16,4,5), freq=40_000_000)

reader = raw_sd.AsyncReader(sd)
dma_buf = heap_caps.malloc(32768, heap_caps.CAP_DMA)

# 發起非同步讀取
reader.start_read(sector=262144, buf=dma_buf, count=64)

# 做其他事（UART / WiFi / 命令處理）
while not reader.done():
    circuit.poll()
    bus_decode.process()
    network.service()

# 讀取下一個 chunk
reader.start_read(sector=262144 + 64, buf=dma_buf, count=64)
```

### 2.5 Python 層封裝（lib/raw_sd.py 擴展）

將 async reader 封裝在 `RawFile` 內，保持 Phase 1 API 不變：

```python
class RawFile:
    def __init__(self, sd, offset_sector, size_sectors, *, async_mode=False):
        if async_mode:
            self._reader = raw_sd.AsyncReader(sd)
        else:
            self._reader = None

    def readinto_async(self, buf):
        # 底層用 AsyncReader，return 後仍可做其他事
        self._reader.start_read(self._cur_sector, buf, count)
```

### 2.6 驗收標準

- UART 最大輪詢間隔從 ~1-2ms 降到 ~0.1ms
- 命令處理延遲不受 SD 讀取影響
- SD 讀取吞吐量不低於 Phase 1 的同步版本
- 無記憶體損毀（GC stress test 通過）

---

## 可行性與風險

| 風險 | Phase | 等級 | 緩解措施 |
|------|:---:|:---:|------|
| raw readblocks 速度不如預期 | 1 | 中 | 先測 benchmark 再決定後續 |
| TOC 損毀導致無法讀取 | 1 | 低 | TOC 僅開機讀一次，寫入時雙寫備份 |
| ISR 狀態機 bug 導致 SD 卡 hang | 2 | 高 | ISR 內加 timeout，出錯回退到同步模式 |
| ISR 與 MicroPython VM 的競態 | 2 | 中 | CAP_DMA 隔離 + 無 FreeRTOS task，僅 ISR |
| 上游 MicroPython 升級不相容 | 2 | 低 | 獨立 C module repo，僅依賴 IDF API |

## 時間線

```
Phase 1:
  [1-2 天] Benchmark script + 實測
  [2-3 天] lib/raw_sd.py + TOC 實作
  [1 天]   PC 端寫入工具
  [1-2 天] 管線替換 + 測試

Phase 2（仅在需要时）:
  [3-5 天] mp_raw_sd C module (ISR 狀態機)
  [1-2 天] Python 層封裝 + 整合
  [2-3 天] 穩定性測試 + UART stress test
```

## 相關文件

- `02_guides/01_fast_io.md` — 現有 fast_io managed-area 方案（raw SD 的既有實作）
- `03_notes/02_buffer_architecture.md` — 多級緩衝架構（L5 輸出層 / StreamReader）
