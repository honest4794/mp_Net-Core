# PLAN #2 — PSRAM framebuffer 零阻塞直送（decode/DMA 完全重疊）

> **用途**：效能優化計劃——把「fire 一幀 PSRAM framebuffer」的 12ms CPU 阻塞壓到 <1ms，使 decode 與 DMA 傳輸完全重疊（frame time ≈ max(decode, transfer)）。
> **分類**：筆記（03_notes）
> **狀態**：PLANNED（暫緩實作，先驗收現況）
> **前置**：PLAN #1（lcd_bus 硬化 + 效能修復）已完成
> **相關**：`02_guides/05_tft_usage.md`（pipeline 手法）、`02_guides/04_lcd_bus.md`（lcd_bus 模組）

---

## 一、現況驗收（本計畫的出發點，已實測確認）

| 指標 | 數值 | 說明 |
|---|---|---|
| SPI 純傳輸 | ~16.7ms/frame（60fps） | 240x320 RGB565 @80MHz 單線，理論 15.36ms |
| 每幀 GC 成本 | 195ms（900KB heap） | 已修：wait_all 不再無條件 gc_collect |
| decode/DMA 重疊 | **已生效**（wait≈0） | DMA 全程藏進 decode 20ms |
| pipeline work=20 | ~32ms（31fps） | = fire 12ms + decode 20ms + wait 0ms |
| serial work=20 | ~39ms（25fps） | = decode 20ms + 傳輸 19ms（無重疊） |
| 螢幕 | ✅ 全滿、不撕裂 | present 結構（begin_display + RAMWR + async fire） |

**結論：重疊結構已成立（省 7ms），剩餘瓶頸是 fire 階段的 PSRAM→內部 copy。**

---

## 二、瓶頸根因（已定位）

`spi_bus.c` 已改 async 直送，但實測單筆 32KB PSRAM write = **2320us**。

根因：v5.5 SPI driver 的 `esp_ptr_dma_capable()`（esp_memory_utils.h:224）只認內部 SRAM（`SOC_DMA_LOW..SOC_DMA_HIGH`），**PSRAM 永遠回 false** → driver 在 ISR（`setup_priv_desc`）內同步 `heap_caps_aligned_alloc + memcpy`（PSRAM→內部）。所以：

- 單筆 32KB = ISR 內同步 copy 32KB ≈ 2.3ms
- 一幀 5×32KB = fire 阻塞 12ms（全部是 CPU copy，不是等 DMA）

S3 硬體其實支援 PSRAM DMA 直讀（`SOC_PSRAM_DMA_CAPABLE=1`、`SOC_AHB_GDMA_SUPPORT_PSRAM=1`），但 v5.5 SPI master 驅動的 API 不提供 PSRAM 對齊/DMA 直讀的途徑（舊版曾有 `psram_trans_align`，v5.1 後移除）。

---

## 三、兩個方案（都要照做照寫，擇一實作）

### 方案 A：C 層自握 GDMA descriptor 指向 PSRAM（真零 copy）

**原理**：不走 `spi_device_queue_trans` 的 TX buffer 路徑（它會強制 copy），改為直接操作 `spi_hal`/GDMA descriptor 鏈，讓 DMA 直接讀 PSRAM 位址。S3 硬體支援（`SOC_PSRAM_DMA_CAPABLE`），只是 v5.5 SPI driver 不給 API。

**設計**（spi_bus.c）：
1. `spi_write()` 對 PSRAM buffer 走新路徑：`spi_device_get_trans_result` + 手動 `spi_hal_setup_trans` / GDMA desc 鏈（參考 esp-idf `components/esp_driver_spi/src/gpspi/spi_hal.c` 的 descriptor 設置）
2. 或改走 `esp_lcd` 的 SPI panel IO（`esp_lcd_new_panel_io_spi`，esp_lcd 層有 `psram_trans_align` 支援）——但會失去自訂 queue API
3. **必須手動 cache 同步**：PSRAM 是 write-back cache，DMA 直讀前要 `esp_cache_msync(ptr, len, ESP_CACHE_MSYNC_FLAG_DIR_C2M)`，讀完（rx）要 M2C。S3 無 `SOC_CACHE_INTERNAL_MEM_VIA_L1CACHE`，driver 自動 msync 不會觸發 → 這步是成敗關鍵

**預期**：fire ≈ 0.5ms → pipeline work=20 ≈ **20.5ms**（47fps）

**風險**：高（手動 GDMA + cache 同步，花屏風險）；需逐 chunk 驗證。

### 方案 B：decode 直寫內部 DMA buffer（block pipeline，終極）

**原理**：不讓 PSRAM 當 DMA 來源。改為 decode 分 32KB block 直接寫進內部 `CAP_DMA` buffer（S3 內部 DMA 有 161KB free，1 幀 150KB 可放），fire 零 copy、零 cache 問題。

**設計**（Python 層 jpeg_player + C 輔助）：
1. 內部 2×32KB DMA buffer（`heap_caps.malloc(CAP_DMA)`）
2. `jpeg.Decoder.decode_into` 改為 block 模式：解一 32KB block → 送一 block（C 已支援單筆 32KB 內部 buffer async 直送，fire <100us）
3. decode(block N+1) 與 DMA(block N) 重疊 → 整幀「邊解邊送」
4. 現有 `bus_adapter.write_frame_dma()` 已具備 chunk queue 雛形

**預期**：無 fire 阻塞；pipeline ≈ **max(decode, 16.7ms)**，理論上限由 decode 速度決定（>30fps 若 decode <33ms）

**風險**：中（要改 jpeg player 為 block pipeline + 內部 buffer 管理）；內部 SRAM 只剩 161KB，需確認不與其他任務衝突。

---

## 四、執行步驟（選定方案後）

1. **方案 A**：
   a. 讀 esp-idf `esp_driver_spi/src/gpspi/spi_hal.c` descriptor 設置
   b. spi_bus.c 加 PSRAM 直送路徑 + `esp_cache_msync` C2M
   c. 重編 → 單筆 32KB PSRAM write 測速（目標 <500us）
   d. 花屏驗證：`tft_pipeline_visual.run(work_ms=0)` 彩虹 + 肉眼
   e. probe 回歸：fire 應 <1ms，pipeline work=20 ≈ 20.5ms

2. **方案 B**：
   a. 確認內部 DMA free（`heap_caps.get_free_size(CAP_DMA)` ≥ 150KB）
   b. jpeg_player_task 改 block pipeline（decode_into block + fire block）
   c. 真 jpeg 播放實測 fps（預期 >30fps）
   d. probe 回歸：fire ≈ 0，pipeline ≈ max(decode, 16.7)

---

## 五、驗收標準

- 單筆 32KB PSRAM write < 500us（方案 A）
- pipeline work=20 < 25ms（方案 A：20.5 / 方案 B：20）
- 螢幕全滿、無花屏、無撕裂
- `tft_pipeline_profile`：fire < 1ms、wait ≈ 0

---

## 六、非目標（本計畫不做）

- QSPI 多線升級（lane_count=2/4）——另案
- RGB/DSI 面板（esp_lcd 已內建 PSRAM 支持，無此問題）
- 真 jpeg decode 優化本身（假設 decode 是既定成本）

## 相關文件

- `02_guides/05_tft_usage.md` — TFT pipeline 手法（decode/DMA 重疊）
- `02_guides/04_lcd_bus.md` — lcd_bus 模組（PSRAM fire 代價）
- `02_guides/07_jpeg.md` — JPEG `decode_into`（block 模式）
