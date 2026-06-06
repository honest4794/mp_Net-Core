# Core0.py
# Worker/Engine 模式 — Core 0 Worker 迴圈
#
# 對應 mp4_testkit new/Core0_worker.py 的 task_loop()
# 職責：讀取 JPEG → 寫入 io_hub → poll Core1 frame_done → FPS 統計 →
#        backlight、comm、network、webui poll → seek / source 切換
#
# 由 main.py 在 worker_engine 模式下呼叫 worker_start()

from lib.sys_bus import bus


def worker_start():
    """Core 0 入口 — Worker 主迴圈（阻塞）

    TODO: 移植 mp4_testkit new/Core0_worker.py task_loop() 的完整邏輯
          包括 io_hub 填滿、pack/folder 雙模式、range play、
          stats 窗口統計、backlight 控制等。
    """
    pass
