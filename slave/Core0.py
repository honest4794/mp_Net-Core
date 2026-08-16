# Core0.py
# Worker/Engine（極速）模式 — Core 0 控制核
#
# 核心理念：簡單、快速、專注完成任務（極速模式），不追求最大靈活性。
# 職責：統一指令線路（網絡 + 實體線）收發 + dispatch。
#   - NetworkTask  : WS / UDP / ESP-NOW 等網絡 bus
#   - CircuitTask  : UART 實體線 bus
#   - BusDecodeTask: poll 所有 bus → 解析封包 → app.disp 分發
#   - LogTask      : 日誌輸出
# 指令（play / pause / 切源）由 action 層寫入 bus.shared，Core1 播放引擎讀取。
#
# 由 main.py 在 worker_engine 模式下呼叫 worker_start()（阻塞於本核心）。

import machine, time, ubinascii
from app import App
from lib.sys_bus import bus
from lib.log_service import get_log

from tasks.network import NetworkTask
from tasks.circuit import CircuitTask
from tasks.bus_decode import BusDecodeTask
from tasks.log_task import LogTask


def _init_player_shared():
    """初始化播放器共享狀態（與 Core_Manager 一致）"""
    bus_sys = bus.shared.setdefault("System", {})
    bus_sys.setdefault("player_width", 240)
    bus_sys.setdefault("player_height", 240)
    bus_sys.setdefault("player_pixel_format", "RGB565_LE")
    bus.shared.setdefault("jpeg_loop", True)
    if "jpeg_player" not in bus.shared:
        bus.shared["jpeg_player"] = {
            "playing": True, "paused": False, "frame": 0, "total": 0,
            "source": "", "err": "", "pace_ms": 33,
        }
    bus.shared.setdefault("jpeg_source_req", {"source": "/jpeg/background"})


def worker_start():
    """Core 0 入口 — 極速控制核主迴圈（阻塞）"""
    log = get_log()
    log.info("⚡ [Core0] Worker/Engine Mode — control core")

    st_pixel = bus.get_service("st_pixel")

    bus.slave_id = ubinascii.hexlify(machine.unique_id()).decode().upper()
    bus.shared["engine_run"] = True
    bus.shared["spi_busy"] = False

    app = App()
    bus.register_service("log", log)

    # 日誌輸出設定（與 Core_Manager 一致）
    sys_cfg = bus.shared.get("System", {})
    interval = sys_cfg.get("log_interval_ms")
    if interval is None:
        log_cfg = sys_cfg.get("Log") or bus.shared.get("Log", {})
        interval = log_cfg.get("print_interval_ms", 1000)
    bus.shared["log_print"] = True
    bus.shared["log_print_interval_ms"] = int(interval or 1000)
    bus.shared["log_print_levels"] = ["info", "warn", "error", "immediate"]
    bus.shared["log_subscribe"] = []

    _init_player_shared()

    ctx = {"app": app, "st_pixel": st_pixel, "bus": bus}

    # 指令線路任務（直接驅動，免 TaskManager 調度開銷）
    tasks = [
        LogTask("log", ctx),
        NetworkTask("network", ctx),
        CircuitTask("circuit", ctx),
        BusDecodeTask("bus_decode", ctx),
    ]

    for t in tasks:
        try:
            t.on_start()
        except Exception as e:
            log.error("[Core0] {} on_start failed: {}".format(t.name, e))

    log.info("⚡ [Core0] Command line online (net + circuit): {}".format(bus.slave_id))

    try:
        while bus.shared.get("engine_run", True):
            for t in tasks:
                try:
                    t.loop()
                except Exception as e:
                    log.error("[Core0] {} loop err: {}".format(t.name, e))
    except KeyboardInterrupt:
        print("[Core0]👋 User stop requested.")
    finally:
        bus.shared["engine_run"] = False
        for t in tasks:
            try:
                t.on_stop()
            except Exception:
                pass
        print("[Core0]🛑 Control core stopped.")
