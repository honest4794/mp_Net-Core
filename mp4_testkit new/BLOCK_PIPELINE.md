# Block Streaming Pipeline 架構說明

> **注意：此架構需要 SPI queue（`pending/is_busy/wait_all`）支援。**
> 預設 `config.json` 已設定 `jpeg.block: false`，使用全幀解碼（`decode_into`）+
> 32KB chunked LCD write 路徑。若要啟用 block streaming，需：
> 1. `jpeg.block: true`
> 2. SPI bus 需支援 `pending()/is_busy()/wait_all()`

## 架構總覽

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            ESP32-S3                                      │
│                                                                          │
│  Core1                                  Core0                            │
│  ┌───────────────────┐                  ┌───────────────────────────────┐│
│  │ SD → io_hub(讀)   │                  │ block_hub → 32KB Accum Buf   ││
│  │   ↓               │                  │   ↑                           ││
│  │ jpeg.decode()     │  ──block_hub──→  │ accumulate 8 blocks (32KB)   ││
│  │   ↓ (逐塊 4KB)     │    2×4KB DMA    │   ↓                          ││
│  │ viper_copy         │                  │ set_window (1次/8塊)         ││
│  │   → block_hub      │                  │ spi_dma.write(32KB)          ││
│  └───────────────────┘                  │   ↓ fire-and-forget          ││
│                                         │ ══ SPI DMA 3.5ms/6.8ms ═→ LCD││
│                                         └───────────────────────────────┘│
│                                                                          │
│  Block 0-7:  [Core1 decode 8×1.35ms=10.8ms] → [1×set_window+32K DMA]   │
│  Block 8-15:                                 [Core1 decode 10.8ms]      │
│                                                     ↓                   │
│  SPI 成本可大幅隱藏（32KB DMA: 80M≈3.5ms / 40M≈6.8ms < 10.8ms）          │
│  set_window 呼叫 = 4次/幀 (30 blocks / 8 = 4 batches)                   │
└──────────────────────────────────────────────────────────────────────────┘
```

## 為什麼是 32KB Batch？

來自 SPI 1線 DMA throughput 實測（最新版本；`total_us` 含 fire+wait）：

### 40MHz

| size | total_us | throughput |
|------|----------|------------|
| 256B | 112us | 2.2 MB/s |
| 1024B | 269us | 3.6 MB/s |
| 4096B | 891us | 4.4 MB/s |
| 16384B | 3381us | 4.6 MB/s |
| 32768B | 6812us | 4.6 MB/s |

### 80MHz

| size | total_us | throughput |
|------|----------|------------|
| 256B | 73us | 3.3 MB/s |
| 1024B | 169us | 5.8 MB/s |
| 4096B | 481us | 8.1 MB/s |
| 16384B | 1742us | 9.0 MB/s |
| 32768B | 3527us | 8.9 MB/s |

### 關鍵觀察

- **4KB 以上吞吐進入平台期，<=1KB 主要被固定開銷吃掉**
- **16KB/32KB 幾乎同速，選 32KB 主要是減少 set_window 次數（1/8）並攤平 per-transfer overhead**
- 堆疊 4KB × 8 次 DMA：40M = 891us × 8 = 7128us ≈ 6812us（單次 32KB）；80M = 481us × 8 = 3848us ≈ 3527us（單次 32KB）

### 積累策略

```
Core1 decode() block 模式 → 逐塊 4KB 產出 → block_hub (2×4KB DMA)
                                                   ↓
Core0 從 block_hub 逐塊讀取 → 積累到 32KB DMA 池緩衝
                                ↓ 積滿 8 塊 (或最後一塊)
                            set_window(batch_start, batch_end)   ← wait_all 同步
                            spi_dma.write(32KB)                   ← fire-and-forget
                                 ↓
                            ══ 背景 DMA ~600us ══→ LCD
                            Core1 繼續解碼下一批
```

- 解碼速度保持 **24.65 FPS**（`decode()` block 模式，不解碼全幀）
- DMA 吞吐保持 **32KB 最優**（單次大塊傳輸）
- `set_window` 每 8 塊才呼叫一次，開銷最小化

## 記憶體佈局

以 240×240 RGB565 為例：

| 層級 | 組件 | 數量 | 單元大小 | 總計 | 記憶體類型 | 備註 |
|------|------|------|---------|------|-----------|------|
| 輸入層 | `io_hub` | 3 buf | ~32KB | ~96KB | bytearray (PSRAM) | JPEG 原始數據 |
| 轉換層 | `block_hub` | 2 buf | ~4KB | ~8KB | heap_caps CAP_DMA | 逐塊傳遞 |
| 輸出層 | `spi_pool` | 2 buf | **32KB** | **64KB** | heap_caps CAP_DMA | 積累 8 塊後一次性 DMA |
| 預載 | `jpeg_cache` | 16 幀 | ~32KB | ~512KB | bytearray (PSRAM) | 可選，消除 SD 抖動 |
| **合計（含預載）** | | | | **~680KB** | | |
| **合計（無預載）** | | | | **~168KB** | | |

### 與全幀模式對比

| 組件 | 全幀模式 | 32KB Batch 模式 | 節省 |
|------|---------|----------------|------|
| frame_hub / block_hub | 3×115KB = 345KB | 2×4KB = 8KB | **-337KB** |
| spi_pool | 3×115KB = 345KB | 2×32KB = 64KB | **-281KB** |
| **合計節省** | | | **-618KB** |

## 為什麼不直接用 32KB block_hub？

| 方案 | 優點 | 缺點 |
|------|------|------|
| block_hub=4KB, spi_pool=32KB (當前) | block_hub 保持最小延遲，Core1 不等待 | 多一次 CPU copy |
| block_hub=32KB, spi_pool=無 | 省一個 copy | Core1 需等 Core0 清空 32KB 才能寫入 |

選擇 block_hub=4KB 是因為 Core1 (解碼) 是瓶頸，不能讓它等 Core0。4KB 的 block_hub 保證 Core1 寫入永不阻塞。

## 預載緩存策略 (jpeg_cache)

當不使用 `.jpk` 打包檔時，系統可將前 N 張 JPEG 預載到記憶體：

```
config.json:
  "player": {
    "pipeline": {
      "preload": 16,              ← 預載 16 幀
      "preload_limit_bytes": 0    ← 0=自動計算 (25% free heap)
    }
  }
```

### 自動計算邏輯

```
limit = min( 25% × gc.mem_free(),  max_jpeg_bytes × io_hub_buffers × 16 )
```

- `max_jpeg_bytes` ≈ 32KB（單張 JPEG 最大體積）
- `gc.mem_free()` ≈ PSRAM 可用量（ESP32-S3 通常 4-8MB）
- 25% cap 保證不耗盡 heap

### 何時用預載？

| 情境 | 建議 |
|------|------|
| SD 卡讀取抖動大 | ✅ 開預載，完全消除抖動 |
| PSRAM 緊張 | ❌ 關預載，或設 `preload: 2` |
| 使用 .jpk | ❌ 自動禁用（.jpk 已有內部緩衝） |
| 循環播放短序列 | ✅ 全載入，零 I/O |

### 控制緩存上限

每張 JPEG 約 20-32KB。預載 `preload: 16` = 約 512KB。控制上限：

```json
"preload_limit_bytes": 102400   ← 上限 100KB，約 3 張 JPEG
```

## 同步機制

`lcd.set_window()` 在 `_spi_q` 路徑下會先 `wait_all()`：

```
batch fire:
  lcd.set_window(batch_start, batch_end)
    → spi.wait_all()         ← 等前一 batch DMA 完成
    → 發送 CASET / RASET     ← 設定新窗口
    → 發送 RAMWR (0x2C)
    → 保持 CS=0, DC=1
  lcd.write_data(32KB)
    → spi.write(buf)          ← fire-and-forget
    → 立即返回
```

天然的同步點：每個 batch 的 `set_window` 確保前一 batch 的 DMA 完全傳輸完畢。

## 延遲分析

以 240×240 / 30 blocks / 4 batches 的一個完整幀為例：

```
舊架構（全幀）:
  Core1 解碼        ████████████████████████ 46ms  (decode_into full)
  Core0 SPI DMA                         ██████ 4.5ms (阻塞等完成!)
  總耗時: 46ms + DMA 阻塞

4KB 逐塊發送:
  Block 0: [解碼 1.35ms] → [DMA fire 50us] → [══ DMA 384us ══]
  Block 1:                [解碼 1.35ms] → [DMA] → [══ DMA ══]
  ...
  總耗時: 30 × 1.35ms = 40.5ms
  SPI 隱藏: ✅  但 set_window × 30 次

32KB Batch（當前）:
  Batch 0:  [解碼 8×1.35ms=10.8ms] → [1×set_window] → [══ 32K DMA 600us ══]
  Batch 1:                           [解碼 10.8ms]   → [set_window] → [══ DMA ══]
  Batch 2:                                             [解碼 10.8ms] → ...
  Batch 3:                                                              ...
  總耗時: 30 × 1.35ms = 40.5ms
  SPI 隱藏: ✅  DMA 吞吐最大  ✅  set_window 僅 4 次  ✅
  FPS: 24.65
```
