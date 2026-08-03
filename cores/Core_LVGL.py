# cores/Core_LVGL.py — LVGL 核心實例（核心模式輕量入口）
#
# 核心 = 能獨立啟動的程式，靠讀 bus 拿數據，數據由另一個核心提供。
# 本核心：跑 LVGL UI，輸入透過 hw_manager 快照（HwSampleTask 統一採樣）。
#
# 前置條件：
#   1. boot.py 已跑完（LCD / encoder / pin 已在 bus）
#   2. HwSampleTask 已在跑（產生 bus.shared["_hw_inputs"] 快照）
#      → 可由另一個核心的 TaskManager 跑，或本核心自帶採樣（見下方註解）
#
# 用法（soft reboot 後，boot.py 已跑完）：
#   import Core_LVGL
#   Core_LVGL.start()
#
# 與 slave new/Core1.py(engine_start) 同風格：獨立啟動、阻塞主迴圈。
# 整合自 slave new/ui/lvgl/board.py + Core1.py 的結構。

import machine, ubinascii
from lib.sys_bus import bus
from lib.log_service import get_log


def start():
    """LVGL 核心入口 — 初始化 + 阻塞主迴圈。

    與 jpeg_player 互斥（共用 LCD）。輸入讀 hw_manager 快照，
    不碰硬體 → 可跨核心（採樣由另一核心負責）。
    """
    log = get_log()

    # ── bus 基本狀態（若由 Core_Manager 帶起則已就緒，這裡補保險）──
    if "engine_run" not in bus.shared:
        bus.slave_id = ubinascii.hexlify(machine.unique_id()).decode().upper()
        bus.shared["engine_run"] = True

    # ── 前置閘門：LCD 必須在 bus 上 ──
    if not bus.has_lcd():
        log.info("⏭ [Core_LVGL] no LCD on bus, abort")
        return

    # ── 前置：hw_manager 快照必須有來源（HwSampleTask）──
    # 若本核心是唯一在跑的核心，需自帶採樣；否則快照由另一核心提供。
    if bus.shared.get("_hw_inputs") is None:
        log.info("⚠ [Core_LVGL] _hw_inputs snapshot not found — starting local sampler")
        _start_local_sampler()

    from ui.lvgl import board
    log.info("🖼 [Core_LVGL] starting LVGL UI core")
    board.run()   # = _setup() + while _loop_once()


def _start_local_sampler():
    """若沒有外部 HwSampleTask，本核心自帶一條採樣緒。
    雙核心時通常另一個核心的 TaskManager 已在跑 HwSampleTask，這裡就不需要。"""
    import _thread
    from lib.hw_manager import sample_inputs

    def _sampler_loop():
        sample_inputs()   # 首次建立基準
        while bus.shared.get("engine_run", True):
            sample_inputs()

    _thread.start_new_thread(_sampler_loop, ())


if __name__ == "__main__":
    start()
