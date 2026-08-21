# mp_Net-Core

ESP32-S3 MicroPython slave 專案 — 高效能 Server ⇄ MCU 傳輸控制系統（NC4 二進位協議 + 雙核心架構）。

## 文件索引

全部文件已按主題分成三類，入口在 [doc/README.md](doc/README.md)：

### 協議層（`doc/01_protocol/`）— 對接 / 新增指令 / 寫工具的人

- [NC4 封包協議（唯一真相）](doc/01_protocol/01_nc4_protocol.md) — 封包格式 / CRC32 / Schema payload / 傳輸層
- [完整指令索引](doc/01_protocol/02_command_index.md) — 全部指令域的單一查詢表
- [OTA 0x22xx](doc/01_protocol/03_ota_protocol.md) — 韌體 OTA 設計（合作方合同）
- [Pixel 0x31xx](doc/01_protocol/04_pixel_protocol.md) — 模式播放（MODE_LIST/GET/SET/STOP/DETAIL）
- [協議整合總規格](doc/01_protocol/05_integration_overview.md) — 與 master_timer_slave 統一合約
- [網路 + 協議性能基準](doc/01_protocol/08_performance_benchmark.md) — 吞吐 / 甜蜜點 / 瓶頸

### 使用教學（`doc/02_guides/`）— 寫功能 / 用模組的人

- [SD 卡中央儲存管理器（fast_io）](doc/02_guides/01_fast_io.md)
- [UART 電機控制器（uart_motor）](doc/02_guides/02_uart_motor.md)
- [heap_caps DMA 記憶體分配](doc/02_guides/03_memory_management.md)
- [lcd_bus 總線模組](doc/02_guides/04_lcd_bus.md)
- [TFT + lcd_bus 使用指南](doc/02_guides/05_tft_usage.md)
- [LVGL UI 使用指南](doc/02_guides/06_lvgl_ui.md)
- [JPEG 模組](doc/02_guides/07_jpeg.md)
- [pixel 子系統](doc/02_guides/08_pixel_subsystem.md)
- [cores 核心實例](doc/02_guides/09_cores.md)
- [檔案更新流程](doc/02_guides/10_file_update.md) — 上傳/下載/兩段式 commit/斷點續傳

### 筆記（`doc/03_notes/`）— 維護者 / 想了解設計脈絡的人

- [多級緩衝架構](doc/03_notes/02_buffer_architecture.md) — 資料從網路/SD 到 DMA 輸出的五層緩衝設計
- [更新紀錄](doc/03_notes/01_changelog.md) — 遠端更新鏈路 / 臨時提速 / lib 三級分類 / 解碼性能
- [RS485 DE 時序調查與交接](doc/03_notes/04_rs485_de_timing.md)
- [PSRAM 零阻塞計劃](doc/03_notes/05_psram_zero_block_plan.md)
- [Raw SD 計劃](doc/03_notes/06_raw_sd_plan.md)

> 舊版文件保留在 `doc/_archive/`，內容以分類目錄下的新版為準。

## Skills（AI 開發輔助）

- `Skills/buffer-conventions` — 緩衝層使用規範（alloc_dma / AtomicStreamHub / DMA）
- `Skills/mp-netcore` — slave 新增功能模組完整流程（schema / action / task / config）
