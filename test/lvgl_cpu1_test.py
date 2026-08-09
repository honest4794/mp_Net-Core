# test/lvgl_cpu1_test.py — 完整 LVGL UI 在 CPU1 運行測試
#
# 目的:用最簡單的方式,把現有完整 LVGL(board.run + 全部頁面)放 CPU1 跑。
#       不碰 TaskManager、不加複雜邏輯,純粹驗證「完整 LVGL 能否穩定跑 CPU1」。
#
# 架構:
#   CPU0: hw_manager 採樣緒(encoder + 按鈕 → bus.shared["_hw_inputs"])
#   CPU1: board.run()(完整 LVGL:_setup + while _loop_once,含全部頁面)
#
# 輸入:LVGL 透過 _make_inputs() 讀 _hw_inputs 快照(不直接碰 GPIO)。
#
# 用法(soft reboot 後,boot.py 已跑完,確保 LVGL task 沒跑):
#   import lvgl_cpu1_test
#   lvgl_cpu1_test.start()
#
# 觀察:
#   - 螢幕顯示完整 UI + 旋鈕/按鈕可操作 = 通過
#   - 崩潰/watchdog = CPU1 跑完整 LVGL 有問題

import _thread, time
from lib.sys_bus import bus
from lib.hw_manager import sample_inputs


def _sampler_loop():
    """CPU0 採樣緒:持續採樣輸入硬體 → bus.shared['_hw_inputs']。"""
    sample_inputs()   # 首次(建立基準)
    while bus.shared.get("engine_run", True):
        sample_inputs()
        time.sleep_ms(5)


def start():
    """啟動完整 LVGL @ CPU1。"""
    print("=" * 50)
    print("[lvgl_cpu1] 完整 LVGL UI @ CPU1 測試")
    print("=" * 50)

    if not bus.has_lcd():
        print("[lvgl_cpu1] ❌ no LCD on bus")
        return

    bus.shared["engine_run"] = True

    # ── CPU0:採樣緒(輸入來源)──
    _thread.start_new_thread(_sampler_loop, ())
    print("[lvgl_cpu1] ✅ CPU0 採樣緒 started")

    # ── CPU1:完整 LVGL ──
    from ui.lvgl import board
    print("[lvgl_cpu1] ⚡ starting board.run() on CPU1...")

    # board.run() 會阻塞(while _loop_once),在 CPU1 跑
    _thread.start_new_thread(board.run, ())

    print("[lvgl_cpu1] ✅ board.run() dispatched to CPU1")
    print("[lvgl_cpu1] 觀察螢幕 — Ctrl-C 停止")


def stop():
    """停止(Ctrl-C 後 REPL 呼叫)。"""
    bus.shared["engine_run"] = False
    print("[lvgl_cpu1] 🛑 stopping...")


if __name__ == "__main__":
    start()
