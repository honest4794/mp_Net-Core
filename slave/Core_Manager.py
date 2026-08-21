# Core_Manager.py
# TaskManager 模式 — 取代舊的 main.py launcher()
#
# 對照 slave/main.py::launcher() 的結構
# 負責：App 建立、TaskManager 初始化、Task 註冊、雙核心啟動

import machine, time, _thread, ubinascii
from app import App
from lib.sys.sys_bus import bus
from lib.sys.buffer_hub import AtomicStreamHub
from lib.sys.task_manager import TaskManager
from lib.sys.log_service import get_log

from tasks.network import NetworkTask
from tasks.circuit import CircuitTask
from tasks.bus_decode import BusDecodeTask
from tasks.fs_scan_task import FsScanTask
from tasks.log_task import LogTask
from tasks.web_ui import WebUITask
from tasks.control_panel import ControlPanelTask
from tasks.action_task_1 import ActionTask1
from tasks.action_task import ActionTask


def launcher():
    log = get_log()
    log.info("📂 [CoreManager] TaskManager Mode")

    st_pixel = bus.get_service("st_pixel")

    bus.slave_id = ubinascii.hexlify(machine.unique_id()).decode().upper()
    bus.shared["engine_run"] = True
    bus.shared["spi_busy"] = False
    bus_sys = bus.shared["System"]

    if st_pixel:
        # pixel_stream hub：slot = 一幀大小（total_bytes），num_buffers 預設 3（雙緩衝+備援）
        hub = AtomicStreamHub(st_pixel.total_bytes)
        bus.register_service("pixel_stream", hub)

    app = App()

    ctx = {
        "app": app,
        "st_pixel": st_pixel,
        "bus": bus,
    }

    tm = TaskManager(ctx)

    bus.register_service("log", get_log())

    sys_cfg = bus.shared.get("System", {})
    interval = sys_cfg.get("log_interval_ms")
    if interval is None:
        log_cfg = sys_cfg.get("Log")
        if log_cfg is None:
            log_cfg = bus.shared.get("Log", {})
        interval = log_cfg.get("print_interval_ms", 1000)
    bus.shared["log_print"] = True
    bus.shared["log_print_interval_ms"] = int(interval or 1000)
    bus.shared["log_print_levels"] = ["info", "warn", "error", "immediate"]
    bus.shared["log_subscribe"] = []

    # ── Layer 0: 網路 + 通訊 + FS 掃描 + 硬體採樣，最先啟動 ──
    # 核心分工（定案）:
    #   core0(主線程) = 通訊 + UI:network / web_ui / circuit / bus_decode /
    #     log / lvgl / motor。通訊任務單一呼叫鏈淺(<8KB,探針實測),
    #     與 LVGL 共用主線程 16KB stack 沒有壓力。
    #   core1(_thread) = 重活:fs_scan / hw_sample / pixel。
    tm.register_task("log", LogTask, default_affinity=(1, 0), layer=0)
    tm.register_task("network", NetworkTask, default_affinity=(1, 0), layer=0)
    # 裝置角色互斥(見 temp/cp 面板 vs temp/motor 執行,兩份各自 flash):
    #   - 本樹 = 面板裝置(LCD+encoder+按鍵):ControlPanelTask + LvglTask。
    #     cpanel 兩模式分層:LVGL 在跑(_ui_active)→ 不發 vbtn,改轉發
    #     LVGL 的 _display_cmd 成 0x1501;LVGL 沒跑 → 原按鈕模式發 vbtn。
    #   - 執行裝置(無 LCD):在 temp/motor 的 Core_Manager 啟用 motor。
    tm.register_task("cpanel", ControlPanelTask, default_affinity=(1, 0), layer=1)
#     tm.register_task("motor", ActionTask1, default_affinity=(1, 0), layer=0)
#     tm.register_task("action", ActionTask, default_affinity=(1, 0), layer=0)
    tm.register_task("circuit", CircuitTask, default_affinity=(1, 0), layer=0)
    tm.register_task("bus_decode", BusDecodeTask, default_affinity=(1, 0), layer=0)
    tm.register_task("web_ui",  WebUITask,   default_affinity=(1, 0), layer=0)
    tm.register_task("fs_scan", FsScanTask,  default_affinity=(0, 1), layer=0)
    from tasks.hw_sample_task import HwSampleTask
    tm.register_task("hw_sample", HwSampleTask, default_affinity=(0, 1), layer=0)

    # ── pixel 子系統（雙核播放）：
    #   core1（計算核）PixelTask：初始化 effects/mapping/modes/registry + 效果計算 → pixel_stream hub
    #   core0（播放核）RenderTask：固定 fps（20ms/50fps）從 hub 取幀推硬體（tasks/render.py）──
    from tasks.pixel_task import PixelTask
    from tasks.render import RenderTask
    tm.register_task("pixel", PixelTask, default_affinity=(0, 1), layer=0)
    tm.register_task("render", RenderTask, default_affinity=(1, 0), layer=0)

    # ── Layer 1: LVGL UI（依賴 TFT/LCD，沒 LCD 整段跳過）──
    # affinity=(1,0)=CPU0: LVGL 完整 UI 不能在 _thread(CPU1)裡跑
    # (MicroPython threading 限制:完整 UI 的 widget 操作在 thread 裡會崩潰)。
    # CPU1 跑其他 task(採樣等)。
    if bus.has_lcd():
        from tasks.lvgl_task import LvglTask
        tm.register_task("lvgl", LvglTask, default_affinity=(1, 0), layer=1)
    else:
        log.info("⏭ [CoreManager] lvgl skipped — no LCD/TFT on bus")

    tm.finalize()

    try:
        log.info("✨ Starting Core 1 Runner...")
        # stack 統一 16KB（與主線程 MICROPY_TASK_STACK_SIZE 同級）：
        #   thread_stack_probe 實測 core1 任務群(fs_scan/hw_sample 等)
        #   單一呼叫鏈 <8KB，16KB 有餘裕；ESP32 預設只有 5KB 必崩。
        #   將來 core1 若加 C 解碼等深鏈任務再調大。
        _thread.stack_size(16 * 1024)
        _thread.start_new_thread(tm.runner_loop, (1,))

        log.info("✨ NetBus System Online: {}".format(bus.slave_id))
        log.info("✨ Starting Core 0 Runner...")
        tm.runner_loop(0)

    except KeyboardInterrupt:
        print("[CoreManager]👋 User stop requested.")
    except Exception as e:
        print("[CoreManager]❌ System Error: {}".format(e))
    finally:
        bus.shared["engine_run"] = False
        print("[CoreManager]🛑 All cores stopping...")
        time.sleep_ms(500)
        if st_pixel:
            st_pixel.big_buffer = bytearray(st_pixel.total_bytes)
            st_pixel.show_all()
        print("[CoreManager]🏁 Clean Exit.")
