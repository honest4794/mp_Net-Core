# cores/Core_Comm.py — 通訊核心實例
#
# 核心 = 能獨立啟動的程式，靠讀 bus 拿數據，數據由另一個核心提供。
# 本核心：純通訊雙核心（網路 + 實體線），無 LCD 依賴。
#   Core0 — 指令線路收發：NetworkTask / CircuitTask / BusDecodeTask / LogTask
#   Core1 — 無（通訊核心單核即可，此範例展示最小可運作通訊核心）
#
# 整合自 slave/main.py（舊通訊核心）的 TaskManager 註冊結構，精簡為核心範例。
# 與 slave new/Core0.py(worker_start) 同風格：直接驅動任務，免 TaskManager 調度開銷。
#
# 前置條件：
#   boot.py 已跑完（network / uart / pin 已在 bus）
#
# 用法（soft reboot 後，boot.py 已跑完）：
#   import Core_Comm
#   Core_Comm.start()

import machine, time, ubinascii
from lib.sys_bus import bus
from lib.log_service import get_log
from app import App
from tasks.network import NetworkTask
from tasks.circuit import CircuitTask
from tasks.bus_decode import BusDecodeTask
from tasks.log_task import LogTask
from tasks.hw_sample_task import HwSampleTask


def start():
    """通訊核心入口 — 指令線路上線 + 阻塞主迴圈。"""
    log = get_log()
    log.info("📡 [Core_Comm] communication core starting")

    bus.slave_id = ubinascii.hexlify(machine.unique_id()).decode().upper()
    bus.shared["engine_run"] = True
    bus.shared["spi_busy"] = False

    app = App()
    bus.register_service("log", log)

    # 日誌輸出設定
    sys_cfg = bus.shared.get("System", {})
    interval = sys_cfg.get("log_interval_ms")
    if interval is None:
        log_cfg = sys_cfg.get("Log") or bus.shared.get("Log", {})
        interval = log_cfg.get("print_interval_ms", 1000)
    bus.shared["log_print"] = True
    bus.shared["log_print_interval_ms"] = int(interval or 1000)
    bus.shared["log_print_levels"] = ["info", "warn", "error", "immediate"]
    bus.shared["log_subscribe"] = []

    ctx = {"app": app, "st_LED": None, "bus": bus}

    # 指令線路任務 + 硬體採樣（直接驅動）
    tasks = [
        LogTask("log", ctx),
        NetworkTask("network", ctx),
        CircuitTask("circuit", ctx),
        BusDecodeTask("bus_decode", ctx),
        HwSampleTask("hw_sample", ctx),
    ]

    for t in tasks:
        try:
            t.on_start()
        except Exception as e:
            log.error("[Core_Comm] {} on_start failed: {}".format(t.name, e))

    log.info("📡 [Core_Comm] online: {} (net + circuit + hw_sample)".format(bus.slave_id))

    try:
        while bus.shared.get("engine_run", True):
            for t in tasks:
                try:
                    t.loop()
                except Exception as e:
                    log.error("[Core_Comm] {} loop err: {}".format(t.name, e))
    except KeyboardInterrupt:
        print("[Core_Comm]👋 stopped")
    finally:
        bus.shared["engine_run"] = False
        for t in tasks:
            try:
                t.on_stop()
            except Exception:
                pass
        print("[Core_Comm]🛑 stopped.")


if __name__ == "__main__":
    start()
