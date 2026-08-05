# main.py
# 雙核心模式啟動器 — 只負責選擇和路由
#
#   taskmanager  → Core_Manager.launcher()
#   worker_engine → Core0.worker_start() + Core1.engine_start()
#
# 硬件初始化已由 boot.py 完成

from lib.sys_bus import bus


def main():
    raw = bus.shared.get("System", {}).get("dual_core_mode", 0)

    # 支援字串 ("taskmanager" / "worker_engine") 和數字 (0 / 1)
    if isinstance(raw, int):
        mode = int(raw)
    else:
        s = str(raw).strip().lower()
        mode = 1 if s in ("worker_engine", "1") else 0

    if mode == 1:
        _launch_worker_engine()
    else:
        _launch_taskmanager()


def _launch_taskmanager():
    from Core_Manager import launcher
    launcher()


def _launch_worker_engine():
    import _thread
    from Core0 import worker_start
    from Core1 import engine_start

    # _thread 預設 stack 只有 5KB(4KB+1KB)，JPEG 解碼鏈會 overflow。
    # 統一 16KB（與主線程同級）。
    _thread.stack_size(16 * 1024)
    _thread.start_new_thread(engine_start, ())
    worker_start()


if __name__ == "__main__":
    main()
