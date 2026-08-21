# cores/Core_MP4.py — MP4 播放器核心實例
#
# 核心 = 能獨立啟動的程式，靠讀 bus 拿數據，數據由另一個核心提供。
# 本核心：MP4/JPEG 影片播放，雙核心 pipeline：
#   Core1（engine）— JPEG 解碼：io_hub 讀檔 → decoder.decode_into → frame_hub
#   Core0（worker）— 讀檔 + 顯示：把 JPEG 序列讀進 io_hub，從 frame_hub 取解碼幀顯示到 LCD
#
# 整合自 mp4_testkit/Core0_worker.py + Core1_engine.py 的 pipeline 模式，
# 精簡為核心範例（保留雙核心結構 + bus 服務注入風格，去掉完整統計/參數）。
#
# 前置條件：
#   1. boot.py 已跑完（LCD / SD 已在 bus）
#   2. bus 上需有 io_hub / frame_hub / decoder 服務（由 bootstrap 建立）
#   3. bus.shared["paths"] = ["/sd/frame0.jpg", ...] 播放清單
#
# 用法（soft reboot 後，boot.py + bootstrap 已跑完）：
#   import Core_MP4
#   Core_MP4.start()

import time, _thread
from lib.sys.sys_bus import bus
from lib.sys.log_service import get_log


def start():
    """MP4 核心入口 — 啟動 Core1 解碼緒 + Core0 讀檔/顯示主迴圈。"""
    log = get_log()

    if not bus.has_lcd():
        log.info("⏭ [Core_MP4] no LCD on bus, abort")
        return

    bus.shared["engine_run"] = bus.shared.get("engine_run", True)

    # ── Core1：JPEG 解碼引擎（獨立緒）──
    log.info("🎬 [Core_MP4] starting Core1 decode engine")
    _thread.start_new_thread(_engine_decode_loop, ())

    # ── Core0：讀檔 + 顯示（阻塞主迴圈）──
    log.info("🎬 [Core_MP4] starting Core0 read+display loop")
    _worker_display_loop()


def _engine_decode_loop():
    """Core1 解碼迴圈（整合自 mp4_testkit/Core1_engine.py）。
    io_hub(讀檔緩衝) → decoder.decode_into → frame_hub(解碼幀)。"""
    log = get_log()
    io_hub = bus.get_service("io_hub")
    frame_hub = bus.get_service("frame_hub")
    decoder = bus.get_service("decoder")
    if io_hub is None or frame_hub is None or decoder is None:
        log.error("❌ [Core_MP4] engine: io_hub/frame_hub/decoder missing")
        return

    max_jpeg = int(bus.shared.get("max_jpeg_bytes", 0) or 0)
    frame_bytes = int(bus.shared.get("frame_bytes", 0) or 0)

    while bus.shared.get("engine_run", True):
        in_view = io_hub.get_read_view()
        if in_view is None:
            time.sleep_ms(0)
            continue
        tail_off = max_jpeg
        n = int.from_bytes(in_view[tail_off + 4:tail_off + 8], "little") if max_jpeg else 0
        if n <= 0:
            io_hub.release_read()
            time.sleep_ms(0)
            continue
        out_view = frame_hub.get_write_view()
        while out_view is None:
            out_view = frame_hub.get_write_view()
            time.sleep_ms(0)
        try:
            decoder.decode_into(in_view[:n], out_view[:frame_bytes])
        except Exception:
            io_hub.release_read()
            time.sleep_ms(0)
            continue
        frame_hub.commit()
        io_hub.release_read()


def _worker_display_loop():
    """Core0 讀檔+顯示迴圈（整合自 mp4_testkit/Core0_worker.py，精簡版）。
    JPEG 序列讀進 io_hub → 等 frame_hub 解碼幀 → LCD 顯示。"""
    log = get_log()
    lcd = bus.get_service("lcd")
    io_hub = bus.get_service("io_hub")
    frame_hub = bus.get_service("frame_hub")
    paths = bus.get_service("paths") or []
    if lcd is None or io_hub is None or frame_hub is None:
        log.error("❌ [Core_MP4] worker: lcd/io_hub/frame_hub missing")
        return
    if not paths:
        log.error("❌ [Core_MP4] worker: no paths (bus.service['paths'])")
        return

    max_jpeg = int(bus.shared.get("max_jpeg_bytes", 0) or 0)
    frame_bytes = int(bus.shared.get("frame_bytes", 0) or 0)
    loop_play = bool(bus.shared.get("loop_play", True))
    pace_ms = int(bus.shared.get("pace_ms", 0) or 0)

    idx = 0
    try:
        while bus.shared.get("engine_run", True):
            if idx >= len(paths):
                if not loop_play:
                    break
                idx = 0

            # 讀 JPEG 檔 → io_hub
            out_view = io_hub.get_write_view()
            while out_view is None:
                out_view = io_hub.get_write_view()
                time.sleep_ms(0)
            try:
                with open(paths[idx], "rb") as f:
                    n = f.readinto(out_view[:max_jpeg])
            except Exception as e:
                log.error("[Core_MP4] read {}: {}".format(paths[idx], e))
                idx += 1
                continue
            # 寫 tail header(frame_idx, n)
            if max_jpeg:
                out_view[max_jpeg + 0:max_jpeg + 4] = idx.to_bytes(4, "little")
                out_view[max_jpeg + 4:max_jpeg + 8] = int(n or 0).to_bytes(4, "little")
            io_hub.commit()

            # 等 frame_hub 解碼完成 → 顯示
            fview = frame_hub.get_read_view()
            while fview is None:
                fview = frame_hub.get_read_view()
                time.sleep_ms(0)
            try:
                lcd.set_window(0, 0, lcd.width - 1, lcd.height - 1)
                lcd_bus = getattr(lcd, "_bus", None)
                if lcd_bus is not None:
                    lcd_bus.write_data_async(fview[:frame_bytes])
                    lcd_bus.flush()
                else:
                    lcd.show(fview[:frame_bytes])
            except Exception as e:
                log.error("[Core_MP4] display: {}".format(e))
            frame_hub.release_read()

            idx += 1
            if pace_ms > 0:
                time.sleep_ms(pace_ms)
    except KeyboardInterrupt:
        print("[Core_MP4]👋 stopped")
    finally:
        bus.shared["engine_run"] = False


if __name__ == "__main__":
    start()
