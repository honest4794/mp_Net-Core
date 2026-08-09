# jpeg_actions.py
# 驅動新版 media_source 播放器（JpegPlayerTask）。
# 指令透過 bus.shared 與播放引擎溝通，同時支援網絡與實體線（dispatch 不分傳輸層）：
#   bus.shared["jpeg_player"]     : {playing, paused, frame, total, source, err, pace_ms}
#   bus.shared["jpeg_source_req"] : {"source": path}  切源（folder/jpk/bin 由路徑自動判斷）
#   bus.shared["jpeg_loop"]       : bool

from lib.sys_bus import bus
from lib.proto import Proto
from lib.schema_codec import SchemaCodec


def _player():
    p = bus.shared.get("jpeg_player")
    if not isinstance(p, dict):
        p = {"playing": False, "paused": False, "frame": 0,
             "total": 0, "source": "", "err": "", "pace_ms": 33}
        bus.shared["jpeg_player"] = p
    return p


def _send_status(ctx, playing, frame, total, fps, err):
    app = ctx.get("app")
    if app is None or "send" not in ctx:
        return
    cmd_def = app.store.get(0x3106)
    payload = SchemaCodec.encode(cmd_def, {
        "playing": int(playing),
        "frame": int(frame),
        "total": int(total),
        "fps": int(fps or 0),
        "err": str(err or ""),
    })
    ctx["send"](Proto.pack(0x3106, payload))


def _status_reply(ctx):
    p = _player()
    playing = 1 if (p.get("playing") and not p.get("paused")) else 0
    _send_status(ctx, playing, int(p.get("frame", 0)),
                 int(p.get("total", 0)), int(p.get("fps", 0)), p.get("err", ""))


def on_jpeg_player_ctl(ctx, args):
    """0x3101 — 播放控制：action 0=stop, 1=play, 2=pause"""
    action = int(args.get("action", 0) or 0)
    seek_frame = int(args.get("seek_frame", 0) or 0)
    p = _player()

    if action == 0:        # stop
        p["playing"] = False
        p["paused"] = False
        print("⏹ [JPEG] Stopped")
    elif action == 1:      # play
        p["playing"] = True
        p["paused"] = False
        # seek_frame > 0：重新切源並請求由該幀起播（播放器若支援會生效）
        if seek_frame > 0:
            req = dict(bus.shared.get("jpeg_source_req") or {})
            if req.get("source") or p.get("source"):
                req.setdefault("source", p.get("source", ""))
                req["start_frame"] = seek_frame
                bus.shared["jpeg_source_req"] = req
        print("▶️ [JPEG] Play")
    elif action == 2:      # pause
        p["paused"] = True
        print("⏸ [JPEG] Paused")

    _status_reply(ctx)


def on_jpeg_source_set(ctx, args):
    """0x3107 — 切源：只傳路徑，folder/jpk/bin 由副檔名/路徑自動判斷"""
    source = str(args.get("source", "") or "").strip()
    if not source:
        _send_status(ctx, 0, 0, 0, 0, "empty source")
        return
    bus.shared["jpeg_source_req"] = {"source": source}
    p = _player()
    p["playing"] = True
    p["paused"] = False
    p["err"] = ""
    print("🎬 [JPEG] Source -> {}".format(source))
    _status_reply(ctx)


def on_jpeg_player_params(ctx, args):
    """0x3103 — 播放參數：pace_ms / loop"""
    p = _player()
    pace_ms = int(args.get("pace_ms", 0) or 0)
    loop = int(args.get("loop", 255) or 255)

    if pace_ms > 0:
        p["pace_ms"] = pace_ms
        print("⚙ [JPEG] pace_ms={}".format(pace_ms))
    if loop != 255:
        bus.shared["jpeg_loop"] = bool(loop)
        print("⚙ [JPEG] loop={}".format(bool(loop)))

    _status_reply(ctx)


def on_jpeg_status_get(ctx, args):
    """0x3105 — 查詢播放狀態"""
    _status_reply(ctx)


def register(app):
    app.disp.on(0x3101, on_jpeg_player_ctl)
    app.disp.on(0x3103, on_jpeg_player_params)
    app.disp.on(0x3105, on_jpeg_status_get)
    app.disp.on(0x3107, on_jpeg_source_set)
    print("✅ [Action] JPEG actions registered")
