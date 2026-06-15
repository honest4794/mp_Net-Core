# Core1.py
# Worker/Engine（極速）模式 — Core 1 渲染引擎核
#
# 核心理念：簡單、快速、專注播放（極速模式）。
# 職責：統一播放引擎 — 透過 media_source 播放三種模式：
#   - folder : 資料夾多 JPEG（整幀解碼）
#   - jpk    : JPK1 打包檔（整幀解碼）
#   - bin    : 定長 raw 像素（免解碼直接 DMA）
#   - 所有流程直接寫在 Core1，不依賴 tasks / 額外 worker lib
# 讀取 bus.shared['jpeg_player']（play/pause）與 ['jpeg_source_req']（切源），
# 由 Core0 指令線路寫入。
#
# 由 main.py 在 worker_engine 模式下以 _thread 啟動 engine_start()。

import time

from lib.sys_bus import bus
from lib.log_service import get_log


def _log_info(msg):
    if bus.shared.get("verbose_print"):
        print(msg)
    else:
        get_log().info(msg)


def _log_error(msg):
    if bus.shared.get("verbose_print"):
        print(msg)
    else:
        get_log().error(msg)


def _player():
    p = bus.shared.get("jpeg_player")
    if not isinstance(p, dict):
        p = {
            "playing": True,
            "paused": False,
            "frame": 0,
            "total": 0,
            "source": "",
            "fps": 0,
            "err": "",
            "pace_ms": 33,
            "mode": 0,
        }
        bus.shared["jpeg_player"] = p
    p.setdefault("mode", 0)
    return p


def _alloc_framebuffer(size):
    try:
        import heap_caps

        buf = heap_caps.malloc(size, heap_caps.CAP_SPIRAM)
        if buf is not None:
            return buf
    except Exception:
        pass
    try:
        import heap_caps

        buf = heap_caps.malloc(size, heap_caps.CAP_DMA)
        if buf is not None:
            return buf
    except Exception:
        pass
    return bytearray(size)


def _apply_source_req(st, req):
    source = str(req.get("source", "") or "").strip()
    if not source:
        return

    if st["source"] is not None:
        try:
            st["source"].close()
        except Exception:
            pass
        st["source"] = None

    try:
        from lib import media_source

        loop = bool(bus.shared.get("jpeg_loop", True))
        st["source"] = media_source.open_source(
            source,
            decoder=st["decoder"],
            bpp=st["bpp"],
            loop=loop,
            frame_size=req.get("frame_size"),
            width=int(req.get("width", st["w"]) or st["w"]),
            height=int(req.get("height", st["h"]) or st["h"]),
            max_jpeg=req.get("max_jpeg"),
            range_start=int(req.get("range_start", 0) or 0),
            range_end=req.get("range_end"),
        )
        st["total_frames"] = int(st["source"].count)
        p = _player()
        p["total"] = st["total_frames"]
        p["source"] = source
        p["err"] = ""

        mode = int(req.get("mode", 0) or 0)
        if mode <= 0:
            mode = 1 if source.endswith(".jpk") else 2
        p["mode"] = mode

        start = int(req.get("start_frame", 0) or 0)
        if start > 0 and hasattr(st["source"], "read_frame_into"):
            try:
                st["source"].read_frame_into(st["fb"], start)
                st["frame"] = start
                p["frame"] = start
            except Exception:
                pass

        kind = "bin" if st["source"].is_raw else "jpeg"
        _log_info("🎬 [JpegPlayer] {} source: {} ({} frames)".format(
            kind, source, st["total_frames"]))
    except Exception as e:
        _player()["err"] = str(e)
        st["source"] = None


def _fill_next_frame(st):
    if st["source"] is None:
        return False
    try:
        idx, n = st["source"].read_into(st["fb"])
    except Exception as e:
        _player()["err"] = str(e)
        return False
    if idx is None or not n:
        return False
    st["frame"] = int(idx)
    _player()["frame"] = st["frame"]
    return True


def engine_start():
    """Core 1 入口 — 極速渲染引擎主迴圈（在獨立 thread 執行）"""
    _log_info("⚡ [Core1] Worker/Engine Mode — render engine")

    waited = 0
    while "jpeg_player" not in bus.shared and waited < 3000:
        time.sleep_ms(10)
        waited += 10

    if bus.shared.get("tft_diag"):
        _log_info("🔧 [Core1] Running TFT diagnostics...")
        try:
            import tft_test_tool

            tft_test_tool.config(
                bus.shared.get("tft_width", 240),
                bus.shared.get("tft_height", 320),
            )
            tft_test_tool.all()
            _log_info("🔧 [Core1] TFT diagnostics done")
        except Exception as e:
            _log_error("[Core1] TFT diag failed: {}".format(e))

    lcd = bus.get_service("lcd") or bus.get_service("tft")
    if lcd is None:
        _log_error("❌ [JpegPlayer] LCD not found")
        return
    bus_obj = getattr(lcd, "_bus", None)
    if bus_obj is None:
        _log_error("❌ [JpegPlayer] bus adapter not found")
        return

    w = getattr(lcd, "width", 240)
    h = getattr(lcd, "height", 320)
    sys_cfg = bus.shared.get("System", {})
    bpp = int(sys_cfg.get("player_bpp", 2))
    fb_size = w * h * bpp
    fb = _alloc_framebuffer(fb_size)
    if fb is None:
        _log_error("❌ [JpegPlayer] framebuffer alloc failed")
        return

    decoder = None
    try:
        import jpeg

        fmt = str(sys_cfg.get("player_pixel_format", "RGB565_BE"))
        decoder = jpeg.Decoder(
            pixel_format=fmt,
            rotation=0,
            block=True,
            return_bytes=False,
        )
    except Exception as e:
        get_log().info("⚠ [JpegPlayer] no jpeg module — test pattern only: {}".format(e))

    old = _player()
    bus.shared["jpeg_player"] = {
        "playing": True,
        "paused": False,
        "frame": 0,
        "total": 0,
        "source": "",
        "fps": 0,
        "err": "",
        "pace_ms": int(old.get("pace_ms", 33)),
        "mode": int(old.get("mode", 0)),
    }

    st = {
        "lcd": lcd,
        "bus": bus_obj,
        "decoder": decoder,
        "fb": fb,
        "fb_size": fb_size,
        "bpp": bpp,
        "w": w,
        "h": h,
        "source": None,
        "total_frames": 0,
        "frame": 0,
        "fps_count": 0,
        "fps_t0": 0,
        "frame_t0": 0,
        "last_frame_ms": 0,
        "_first_frame": False,
        "_frame_us": 0,
    }

    _log_info("🖼 [JpegPlayer] {}x{} fb={} KB".format(w, h, fb_size // 1024))
    _log_info("⚡ [Core1] Render engine online")

    try:
        while bus.shared.get("engine_run", True):
            try:
                if bus.shared.get("jpeg_test_hub"):
                    _hub = bus.get_service("frame_hub")
                    if _hub is not None:
                        r = _hub.get_read_view()
                        if r is not None:
                            st["lcd"].set_window(0, 0, st["w"] - 1, st["h"] - 1)
                            _t0 = time.ticks_us()
                            st["lcd"].show_frame(r[:st["fb_size"]])
                            _t1 = time.ticks_us()
                            _hub.release_read()
                            _fu = time.ticks_diff(_t1, _t0)
                            st["_frame_us"] = (st.get("_frame_us", 0) + _fu) // 2 if st.get("_frame_us", 0) else _fu
                            if not st["_first_frame"]:
                                print("[Hub] first frame: {}us ({}B)".format(_fu, st["fb_size"]))
                                st["_first_frame"] = True
                            st["fps_count"] += 1
                            now = time.ticks_ms()
                            if st["fps_t0"] == 0:
                                st["fps_t0"] = now
                            dt = time.ticks_diff(now, st["fps_t0"])
                            if dt >= 1000:
                                fps = st["fps_count"] * 1000 // dt
                                total = st["fb_size"]
                                mbps = total * st["fps_count"] / dt * 1000 / (1024 * 1024)
                                fu = st.get("_frame_us", 0)
                                print("[Hub] FPS={} frame={} {:.1f}ms/f {:.1f}MB/s frame={}us".format(
                                    fps, st["fps_count"],
                                    1000.0 / fps if fps else 0, mbps, fu))
                                st["fps_t0"] = now
                                st["fps_count"] = 0
                                st["_frame_us"] = 0
                    time.sleep_ms(0)
                    continue

                _hub = bus.get_service("frame_hub")
                if _hub is not None:
                    r = _hub.get_read_view()
                    if r is not None:
                        st["lcd"].set_window(0, 0, st["w"] - 1, st["h"] - 1)
                        st["lcd"].show_frame(r[:st["fb_size"]])
                        _hub.release_read()
                        continue

                if st["decoder"] is None:
                    time.sleep_ms(1)
                    continue

                req = bus.shared.pop("jpeg_source_req", None)
                if req is not None:
                    _apply_source_req(st, req)

                if st["source"] is None:
                    time.sleep_ms(1)
                    continue

                player = _player()
                pace_ms = int(player.get("pace_ms", 0) or 0)
                if pace_ms > 0 and st["last_frame_ms"]:
                    now = time.ticks_ms()
                    if time.ticks_diff(now, st["last_frame_ms"]) < pace_ms:
                        time.sleep_ms(1)
                        continue

                if not player.get("playing", True):
                    time.sleep_ms(1)
                    continue
                if player.get("paused", False):
                    time.sleep_ms(1)
                    continue

                if not _fill_next_frame(st):
                    player["playing"] = False
                    time.sleep_ms(1)
                    continue

                st["lcd"].set_window(0, 0, st["w"] - 1, st["h"] - 1)
                st["lcd"].show_frame(memoryview(st["fb"])[:st["fb_size"]])

                st["fps_count"] += 1
                now = time.ticks_ms()
                if st["fps_t0"] == 0:
                    st["fps_t0"] = now
                    st["frame_t0"] = now
                else:
                    dt = time.ticks_diff(now, st["fps_t0"])
                    if dt >= 1000:
                        fps = st["fps_count"] * 1000 // dt
                        player["fps"] = fps
                        if bus.shared.get("verbose_print"):
                            print("[JpegPlayer] fps={} frame={}".format(fps, st["frame"]))
                        st["fps_t0"] = now
                        st["fps_count"] = 0

                st["last_frame_ms"] = time.ticks_ms()
            except Exception as e:
                if bus.shared.get("verbose_print"):
                    print("[Core1] player loop err: {}".format(e))
                else:
                    get_log().error("[Core1] player loop err: {}".format(e))
            time.sleep_ms(1)
    finally:
        try:
            if st["fb"] is not None:
                try:
                    import heap_caps
                    heap_caps.free(st["fb"])
                except Exception:
                    pass
                st["fb"] = None
            if st["source"] is not None:
                try:
                    st["source"].close()
                except Exception:
                    pass
                st["source"] = None
        finally:
            _log_info("[Core1] Render engine stopped.")
