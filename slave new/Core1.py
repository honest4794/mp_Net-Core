# Core1.py
# Worker/Engine 模式 — Core 1 Engine 迴圈
#
# 對應 mp4_testkit new/Core1_engine.py 的 task_loop()
# 職責：從 io_hub 讀 JPEG → 解碼（block / fullframe）→
#       DMA 寫 LCD 或寫 block_hub / frame_hub
#
# 由 main.py 在 worker_engine 模式下以 _thread 啟動 engine_start()

from lib.sys_bus import bus


def engine_start():
    """Core 1 入口 — Engine 主迴圈（在獨立 thread 執行）

    TODO: 移植 mp4_testkit new/Core1_engine.py task_loop() 的完整邏輯
          包括 JPEG decode (block/fullframe)、jpeg_cache 快取、
          DMA 寫 LCD、block_hub 輸出等。
    """
    pass
