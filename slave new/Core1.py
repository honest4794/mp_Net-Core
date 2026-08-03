# Core1.py
# Worker/Engine（極速）模式 — Core 1 渲染引擎核
#
# 核心理念：簡單、快速、專注播放（極速模式）。
# 職責：統一播放引擎 — 透過 media_source 播放三種模式：
#   - folder : 資料夾多 JPEG（整幀解碼）
#   - jpk    : JPK1 打包檔（整幀解碼）
#   - bin    : 定長 raw 像素（免解碼直接 DMA）
# 讀取 bus.shared['jpeg_player']（play/pause）與 ['jpeg_source_req']（切源），
# 由 Core0 指令線路寫入。
#
# 由 main.py 在 worker_engine 模式下以 _thread 啟動 engine_start()。

from lib.sys_bus import bus
from lib.log_service import get_log

# JpegPlayerTask 依賴 TFT/LCD。沒有 LCD 時不 import,讓雙核心仍能正常啟動。
if bus.has_lcd():
    from tasks.jpeg_player_task import JpegPlayerTask
else:
    JpegPlayerTask = None


def engine_start():
    """Core 1 入口 — 極速渲染引擎主迴圈（在獨立 thread 執行）"""
    log = get_log()

    # 沒有 LCD → 整個渲染引擎跳過(Core0 控制核仍正常運作)
    if JpegPlayerTask is None:
        log.info("⏭ [Core1] render engine skipped — no LCD/TFT on bus")
        return

    log.info("⚡ [Core1] Worker/Engine Mode — render engine")

    # 等待 Core0 初始化播放器共享狀態（避免啟動競態）
    import time
    waited = 0
    while "jpeg_player" not in bus.shared and waited < 3000:
        time.sleep_ms(10)
        waited += 10

    st_LED = bus.get_service("st_LED")
    ctx = {"app": None, "st_LED": st_LED, "bus": bus}

    player = JpegPlayerTask("jpeg_player", ctx)
    try:
        player.on_start()
    except Exception as e:
        log.error("[Core1] player on_start failed: {}".format(e))
        return

    log.info("⚡ [Core1] Render engine online")

    try:
        while bus.shared.get("engine_run", True):
            try:
                player.loop()
            except Exception as e:
                log.error("[Core1] player loop err: {}".format(e))
    finally:
        try:
            player.on_stop()
        except Exception:
            pass
        print("[Core1]🛑 Render engine stopped.")
