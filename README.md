# mp_Net-Core

ESP32-S3 MicroPython slave 專案 — 高效能 Server ⇄ MCU 傳輸控制系統（NC4 二進位協議 + 雙核心架構）。

## 核心文件

- [多級緩衝架構 (Multi-Level Buffering)](doc/multi_level_buffer.md) — 資料從網路/SD 到 DMA 輸出的五層緩衝設計
- [NC4 封包協議說明](doc/protocol_nc4.md) — 封包格式 / CRC32 / Schema payload / 完整指令集
- [fast_io SD 卡中央儲存管理器](doc/fast_io.zh-TW.md)
- [UART 電機控制器 (uart_motor)](doc/uart_motor.md)
- [RS485 半雙工 DE 使能時序（20ms GAP 分析）](doc/rs485_de_timing.md)
- [LVGL UI 使用指南](doc/lvgl_ui_usage_latest.md)
- [TFT / LCD 使用指南](doc/tft_lcd_usage_latest.md)

## Skills（AI 開發輔助）

- `Skills/buffer-conventions` — 緩衝層使用規範（alloc_dma / AtomicStreamHub / DMA）
- `Skills/mp-netcore` — slave 新增功能模組完整流程（schema / action / task / config）
