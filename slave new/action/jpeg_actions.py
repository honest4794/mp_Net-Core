# jpeg_actions.py
# 統一播放器控制層。
# JPEG 與 MP4 命令本質上都操作同一個播放器狀態，只是協議編號與回包格式不同。
#   bus.shared["jpeg_player"]     : {playing, paused, frame, total, source, err, pace_ms, mode}
#   bus.shared["jpeg_source_req"] : {"source": path, "start_frame": n, "range_start": a, "range_end": b}
#   bus.shared["jpeg_loop"]       : bool

from lib.sys_bus import bus
from lib.proto import Proto
from lib.schema_codec import SchemaCodec

MODE_AUTO = 0
MODE_PACK = 1
MODE_FOLDER = 2


def _player():
    p = bus.shared.get("jpeg_player")
    if not isinstance(p, dict):
        p = {"playing": True, "paused": False, "frame": 0,
             "total": 0, "source": "", "fps": 0, "err": "",
             "pace_ms": 33, "mode": 0}
        bus.shared["jpeg_player"] = p
    p.setdefault("mode", 0)
    return p


def _detect_mode(source):
    source = str(source or "").strip().lower()
    return MODE_PACK if source.endswith(".jpk") else MODE_FOLDER


def _send_jpeg_status(ctx, playing, frame, total, fps, err):
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


def _send_mp4_status(ctx, playing, paused, mode, frame, total, source, err):
    app = ctx.get("app")
    if app is None or "send" not in ctx:
        return
    cmd_def = app.store.get(0x3204)
    payload = SchemaCodec.encode(cmd_def, {
        "playing": int(playing),
        "paused": int(paused),
        "mode": int(mode),
        "frame": int(frame),
        "total": int(total),
        "source": str(source or ""),
        "err": str(err or ""),
    })
    ctx["send"](Proto.pack(0x3204, payload))


def _jpeg_status_reply(ctx):
    p = _player()
    playing = 1 if (p.get("playing") and not p.get("paused")) else 0
    _send_jpeg_status(ctx, playing, int(p.get("frame", 0)),
                      int(p.get("total", 0)), int(p.get("fps", 0)), p.get("err", ""))


def _mp4_status_reply(ctx):
    p = _player()
    _send_mp4_status(
        ctx,
        1 if p.get("playing") else 0,
        1 if p.get("paused") else 0,
        int(p.get("mode", 0) or 0),
        int(p.get("frame", 0) or 0),
        int(p.get("total", 0) or 0),
        p.get("source", ""),
        p.get("err", ""),
    )


def _set_source_request(source, start_frame=0, mode=None, range_start=0, range_end=None):
    req = {"source": source}
    if start_frame:
        req["start_frame"] = int(start_frame)
    if mode is not None:
        req["mode"] = int(mode)
    if range_start:
        req["range_start"] = int(range_start)
    if range_end is not None:
        req["range_end"] = int(range_end)
    bus.shared["jpeg_source_req"] = req


def _set_player_source(source, mode=None):
    p = _player()
    p["source"] = str(source or "")
    p["mode"] = int(_detect_mode(source) if mode is None or int(mode) == MODE_AUTO else mode)
    p["playing"] = True
    p["paused"] = False
    p["err"] = ""
    return p


def on_jpeg_player_ctl(ctx, args):
    """0x3101 — 播放控制：action 0=stop, 1=play, 2=pause"""
    action = int(args.get("action", 0) or 0)
    seek_frame = int(args.get("seek_frame", 0) or 0)
    p = _player()
    p["err"] = ""

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

    _jpeg_status_reply(ctx)


def on_jpeg_source_set(ctx, args):
    """0x3107 — 切源：只傳路徑，folder/jpk/bin 由副檔名/路徑自動判斷"""
    source = str(args.get("source", "") or "").strip()
    if not source:
        _send_jpeg_status(ctx, 0, 0, 0, 0, "empty source")
        return
    _set_source_request(source)
    _set_player_source(source)
    print("🎬 [JPEG] Source -> {}".format(source))
    _jpeg_status_reply(ctx)


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

    _jpeg_status_reply(ctx)


def on_jpeg_status_get(ctx, _args):
    """0x3105 — 查詢播放狀態"""
    _jpeg_status_reply(ctx)


def on_mp4_player_ctl(ctx, args):
    action = int(args.get("action", 0) or 0)
    value = int(args.get("value", 0) or 0)
    p = _player()
    p["err"] = ""

    if action == 0:
        p["playing"] = False
        p["paused"] = False
        _mp4_status_reply(ctx)
        return

    if action == 1:
        p["playing"] = True
        p["paused"] = False
        _mp4_status_reply(ctx)
        return

    if action == 2:
        p["paused"] = bool(value)
        if not value:
            p["playing"] = True
        _mp4_status_reply(ctx)
        return

    if action == 3:
        source = str(p.get("source", "") or "").strip()
        if source:
            _set_source_request(
                source,
                start_frame=value,
                mode=p.get("mode", _detect_mode(source)),
            )
            p["playing"] = True
            p["paused"] = False
        _mp4_status_reply(ctx)


def on_mp4_source_set(ctx, args):
    source = str(args.get("source", "") or "").strip()
    mode = int(args.get("mode", MODE_AUTO) or MODE_AUTO)
    start = int(args.get("start", args.get("range_start", 0)) or 0)
    raw_range = args.get("range", None)

    if not source:
        _send_mp4_status(ctx, 0, 0, 0, 0, 0, "", "empty source")
        return

    if mode not in (MODE_AUTO, MODE_PACK, MODE_FOLDER):
        mode = MODE_AUTO
    resolved_mode = _detect_mode(source) if mode == MODE_AUTO else mode

    range_end = None
    if raw_range is not None:
        span = int(raw_range or 0)
        if span != 0xFFFFFFFF and span > 0:
            range_end = start + span - 1
        else:
            range_end = 0xFFFFFFFF

    _set_source_request(
        source,
        start_frame=start,
        mode=resolved_mode,
        range_start=start,
        range_end=range_end,
    )
    _set_player_source(source, resolved_mode)
    _mp4_status_reply(ctx)


def on_mp4_status_get(ctx, _args):
    _mp4_status_reply(ctx)



def register(app):
    app.disp.on(0x3101, on_jpeg_player_ctl)
    app.disp.on(0x3103, on_jpeg_player_params)
    app.disp.on(0x3105, on_jpeg_status_get)
    app.disp.on(0x3107, on_jpeg_source_set)
    app.disp.on(0x3201, on_mp4_player_ctl)
    app.disp.on(0x3202, on_mp4_source_set)
    app.disp.on(0x3203, on_mp4_status_get)
    print("✅ [Action] Player actions registered")
