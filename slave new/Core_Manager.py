# Core_Manager.py
# TaskManager 模式 — 取代舊的 main.py launcher()
#
# 對照 slave/main.py::launcher() 的結構
# 負責：App 建立、TaskManager 初始化、Task 註冊、雙核心啟動

import machine, time, _thread, ubinascii
from app import App
from lib.sys_bus import bus
from lib.buffer_hub import AtomicStreamHub
from lib.task_manager import TaskManager
from lib.log_service import get_log

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

    st_LED = bus.get_service("st_LED")

    bus.slave_id = ubinascii.hexlify(machine.unique_id()).decode().upper()
    bus.shared["engine_run"] = True
    bus.shared["spi_busy"] = False
    bus_sys = bus.shared["System"]

    if st_LED:
        hub = AtomicStreamHub(st_LED.total_bytes * bus_sys["buffer_frames"])
        bus.register_service("pixel_stream", hub)

    app = App()

    ctx = {
        "app": app,
        "st_LED": st_LED,
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

    # ── Layer 0: 網路 + 通訊 + FS 掃描，最先啟動 ──
    tm.register_task("log", LogTask, default_affinity=(1, 0), layer=0)
    tm.register_task("network", NetworkTask, default_affinity=(1, 0), layer=0)
#     tm.register_task("cpanel", ControlPanelTask, default_affinity=(1, 0), layer=1)
    tm.register_task("motor", ActionTask1, default_affinity=(1, 0), layer=0)
#     tm.register_task("action", ActionTask, default_affinity=(1, 0), layer=0)
    tm.register_task("circuit", CircuitTask, default_affinity=(1, 0), layer=0)
    tm.register_task("bus_decode", BusDecodeTask, default_affinity=(1, 0), layer=0)
    tm.register_task("web_ui",  WebUITask,   default_affinity=(1, 0), layer=0)
    tm.register_task("fs_scan", FsScanTask,  default_affinity=(0, 1), layer=0)

    # ── Layer 1: JPEG 播放器 ──
    from tasks.jpeg_player_task import JpegPlayerTask
#     tm.register_task("jpeg_player", JpegPlayerTask, default_affinity=(0, 1), layer=1)

    # ══════════════════════════════════════════════════════
    # 臨時播放參數（之後會移到 config.json）
    # ══════════════════════════════════════════════════════
    bus_sys["player_width"]  = 240
    bus_sys["player_height"] = 240
    bus_sys["player_pixel_format"] = "RGB565_LE"
    bus.shared["jpeg_loop"] = True
    bus.shared["jpeg_player"] = {
        "playing": True,
        "paused":  False,
        "frame":   0,
        "total":   0,
        "source":  "",
        "err":     "",
        "pace_ms": 33,
    }
    bus.shared["jpeg_source_req"] = {
        "source": "/jpeg/background",
    }
    bus.shared.setdefault("_stream_source", "/jpeg/background")

    tm.finalize()

    try:
        log.info("✨ Starting Core 1 Runner...")
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
        if st_LED:
            st_LED.big_buffer = bytearray(st_LED.total_bytes)
            st_LED.show_all()
        print("[CoreManager]🏁 Clean Exit.")
