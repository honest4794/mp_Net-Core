# ui/lvgl/ui_space.py — 控制平面核心（bus 空間管理）
#
# 三類空間(對齊 slave new 既有慣例):
#   1. switch bitfield  bus.shared["_ui_switch_state/ctrl"]  byte(bit N = 第 N 個 switch)
#   2. int i32 陣列     bus.shared["_ui_int_state/ctrl"]     byte(N*4, LE i32)
#   3. 變長/字串/事件   bus.shared["_ui_var"]                dict(低頻)
#
# 方向規則(不拆同一信號的 read/write,而是「實際值」與「期望值」兩個不同信號):
#   state 陣列:LVGL 唯寫(每幀把 widget 實際值打包進去);action/查詢方唯讀。
#   ctrl  陣列:action/外部唯寫(UI_SET 寫期望值);LVGL 唯讀後套用。
#   每個 bytearray 單一 writer → byte/i32 寫原子 → 雙核免鎖。
#
# slot 採靜態攤平:所有 page 的 widget 在 alloc 時拿固定全域 idx,
# 運行中不漂移,_ui_decl 映射終身有效、可快取、可整包 dump 持久化。
#
# enum 用 int+options 表示;list/source 動態綁 _ui_var;
# action/event 走 _ui_var 事件佇列(UI append / 外部 pop)。
import json
from lib.sys_bus import bus

# 全域 bus key
K_DECL = "_ui_decl"
K_INT_ST = "_ui_int_state"
K_INT_CT = "_ui_int_ctrl"
K_SW_ST = "_ui_switch_state"
K_SW_CT = "_ui_switch_ctrl"
K_VAR = "_ui_var"

# ── 內部狀態 ──
_decl = {}              # page_id → [widget_meta, ...](完整宣告 + read/apply 綁定)
_pages_done = []        # 已 begin_page 過的頁順序(描述用)
_counters = None        # {"sw":已用 bit 數, "int":已用 i32 數}
_alloced = False        # alloc_from_decl 是否已完成


# ══════════════════════════════════════════════════════
# 宣告階段(build 時呼叫,由 ui_common.begin_page / declare 轉發)
# ══════════════════════════════════════════════════════

def begin_page(page_id):
    """清該頁舊 widget 暫存,準備重新宣告。
    注意:read/apply lambda 是 build() 時閉包綁定的,每次 rebuild 要重綁,
    所以這裡要清掉舊 entry 但『不』退還已分配的 idx(idx 靜態攤平,終身固定)。
    """
    if page_id not in _decl:
        _decl[page_id] = []
        _pages_done.append(page_id)
    else:
        # 保留 meta(含 idx),清掉舊 lambda(底下 declare 會重新填)
        for m in _decl[page_id]:
            m["_read"] = None
            m["_apply"] = None


def declare(page_id, id, type, label, dir="r", read=None, apply=None,
            options=None, source=None, event=None, scale=1, **extra):
    """宣告一個 widget。alloc 後 idx 固定;rebuild 時只更新 read/apply lambda。"""
    if page_id not in _decl:
        begin_page(page_id)
    plist = _decl[page_id]

    # 找既有 entry(同 page+id)
    meta = None
    for m in plist:
        if m["id"] == id:
            meta = m
            break

    if meta is None:
        # 首次宣告:決定 arr/idx。alloc 前先記需求,alloc 時配 idx。
        meta = {
            "id": id, "type": type, "label": label, "dir": dir,
            "options": options, "source": source, "event": event,
            "scale": scale, "extra": extra,
            "arr": None, "idx": None,
            "_read": read, "_apply": apply if dir == "rw" else None,
        }
        plist.append(meta)
        if _counters is not None:
            _assign_slot(meta)
    else:
        # rebuild:更新可變欄位,重新綁 lambda
        meta["type"] = type
        meta["label"] = label
        meta["dir"] = dir
        meta["options"] = options
        meta["source"] = source
        meta["event"] = event
        meta["scale"] = scale
        meta["extra"] = extra
        meta["_read"] = read
        meta["_apply"] = apply if dir == "rw" else None


def _assign_slot(meta):
    """依 type 配 arr/idx。同型打包:switch→bitfield,數值類→int i32。
    list/str/action 不配打包陣列(走 _ui_var dict)。"""
    t = meta["type"]
    if t == "switch":
        meta["arr"] = "switch"
        meta["idx"] = _counters["sw"]
        _counters["sw"] += 1
    elif t in ("list", "str", "action"):
        # 不佔打包陣列;存在 _ui_var dict(source/event 指向)
        meta["arr"] = None
        meta["idx"] = None
    else:
        # display/slider/enum 都走 int i32
        meta["arr"] = "int"
        meta["idx"] = _counters["int"]
        _counters["int"] += 1


# ══════════════════════════════════════════════════════
# 配置階段(board 啟動時,所有 page 第一次 import 後呼叫)
# ══════════════════════════════════════════════════════

def alloc_from_decl():
    """掃所有已宣告 widget,計數後一次性配固定大小 bytearray 進 bus.shared。
    對齊 TaskManager 預分配慣例:啟動時全配,運行中不漂移。"""
    global _counters, _alloced
    if _alloced:
        return
    _counters = {"sw": 0, "int": 0}
    # 第一次掃描:配 idx
    for pid in _pages_done:
        for meta in _decl.get(pid, []):
            if meta["arr"] is None:
                _assign_slot(meta)
    n_sw = _counters["sw"]
    n_int = _counters["int"]
    # bitfield 至少 4 byte(32 bit,預留);i32 陣列照數量
    sw_bytes = max(4, (n_sw + 7) // 8)
    int_bytes = max(4, n_int) * 4
    bus.shared[K_SW_ST] = bytearray(sw_bytes)
    bus.shared[K_SW_CT] = bytearray(sw_bytes)
    bus.shared[K_INT_ST] = bytearray(int_bytes)
    bus.shared[K_INT_CT] = bytearray(int_bytes)
    if not isinstance(bus.shared.get(K_VAR), dict):
        bus.shared[K_VAR] = {}
    # 清空 ctrl(state 由 LVGL 每幀寫,不需要預清)
    _alloced = True
    print("[ui_space] alloc: switch={}bit int={}i32 (sw{}B int{}B)".format(
        n_sw, n_int, sw_bytes, int_bytes))


# ══════════════════════════════════════════════════════
# 讀寫原語(仿 HW.set/get)
# ══════════════════════════════════════════════════════

def _bit_get(buf, idx):
    return (buf[idx >> 3] >> (idx & 7)) & 1


def _bit_set(buf, idx, v):
    b = idx >> 3
    if v:
        buf[b] = buf[b] | (1 << (idx & 7))
    else:
        buf[b] = buf[b] & ~(1 << (idx & 7))


def _i32_get(buf, idx):
    o = idx * 4
    return buf[o] | (buf[o + 1] << 8) | (buf[o + 2] << 16) | (buf[o + 3] << 24)


def _i32_set(buf, idx, v):
    # 兼容負數(Python int → 兩補碼 LE)
    if v < 0:
        v = v + (1 << 32)
    o = idx * 4
    buf[o] = v & 0xFF
    buf[o + 1] = (v >> 8) & 0xFF
    buf[o + 2] = (v >> 16) & 0xFF
    buf[o + 3] = (v >> 24) & 0xFF


# ══════════════════════════════════════════════════════
# 每幀同步(LVGL 是唯一摸 widget 的人,thread-safe)
# ══════════════════════════════════════════════════════

def sync():
    """每幀呼叫:LVGL 讀 ctrl→套 widget,讀 widget→寫 state。
    本函式只由 board 的主迴圈呼叫(跑在 LVGL 那核)。"""
    sw_st = bus.shared.get(K_SW_ST)
    sw_ct = bus.shared.get(K_SW_CT)
    int_st = bus.shared.get(K_INT_ST)
    int_ct = bus.shared.get(K_INT_CT)
    if not _alloced or sw_st is None:
        return
    for pid in _pages_done:
        for meta in _decl.get(pid, []):
            _sync_one(meta, sw_st, sw_ct, int_st, int_ct)


def _sync_one(meta, sw_st, sw_ct, int_st, int_ct):
    t = meta["type"]
    # list/str/action 不走打包陣列(走 _ui_var),sync 不處理
    if t in ("list", "str", "action"):
        return
    # 1. ctrl → widget(rw 才有 apply)
    if meta["dir"] == "rw" and meta["_apply"] is not None and meta["idx"] is not None:
        try:
            if t == "switch":
                v = _bit_get(sw_ct, meta["idx"])
                meta["_apply"](bool(v))
            else:
                v = _i32_get(int_ct, meta["idx"])
                meta["_apply"](v)
        except Exception as e:
            print("[ui_space] apply fail:", meta["id"], e)
    # 2. widget → state(read)
    if meta["_read"] is not None and meta["idx"] is not None:
        try:
            val = meta["_read"]()
            if t == "switch":
                _bit_set(sw_st, meta["idx"], 1 if val else 0)
            else:
                _i32_set(int_st, meta["idx"], int(val or 0))
        except Exception as e:
            print("[ui_space] read fail:", meta["id"], e)


# ══════════════════════════════════════════════════════
# 外部介面(action handler / 查詢方呼叫;不碰 widget)
# ══════════════════════════════════════════════════════

def describe(page_id=None):
    """回傳 _ui_decl 空間映射(查詢=查空間在哪)。不碰 widget 物件。
    enum 回傳 options;list 回傳 _ui_var[source] 目前內容;action 回傳 event 鍵。"""
    var = bus.shared.get(K_VAR) or {}
    out_pages = []
    targets = [page_id] if page_id else _pages_done
    for pid in targets:
        if pid not in _decl:
            continue
        ctrls = []
        for m in _decl[pid]:
            c = {
                "id": m["id"], "type": m["type"], "label": m["label"],
                "dir": m["dir"], "arr": m["arr"], "idx": m["idx"],
            }
            if m["type"] == "enum":
                c["options"] = m["options"]
            if m["type"] == "list":
                c["source"] = m["source"]
                c["items"] = var.get(m["source"], [])
            if m["type"] == "action":
                c["event"] = m["event"]
            if m["scale"] != 1:
                c["scale"] = m["scale"]
            if m["extra"]:
                c.update(m["extra"])
            ctrls.append(c)
        out_pages.append({
            "id": pid, "title": _page_title(pid),
            "controls": ctrls,
        })
    return {"pages": out_pages}


def _page_title(pid):
    """從 registry 拿 title(若有)。"""
    try:
        from ui.lvgl import registry
        meta = registry.get(pid)
        if meta:
            return meta.get("title", pid)
    except Exception:
        pass
    return pid


def set_value(page_id, widget_id, value):
    """UI_SET 入口:外部寫期望值進 ctrl 陣列(或 _ui_var)。
    直寫 buffer,繞過 LVGL,跨核安全、零延遲。LVGL 下幀套用。"""
    if not _alloced:
        return False
    meta = _find_meta(page_id, widget_id)
    if meta is None:
        return False
    # action/list/str 不走打包陣列(無 idx),不能由外部 set
    # action 由 UI post 事件;list/str 是唯讀顯示
    if meta["type"] in ("action", "list", "str") or meta["idx"] is None:
        return False
    t = meta["type"]
    try:
        if t == "switch":
            sw_ct = bus.shared.get(K_SW_CT)
            _bit_set(sw_ct, meta["idx"], 1 if value else 0)
        else:
            int_ct = bus.shared.get(K_INT_CT)
            _i32_set(int_ct, meta["idx"], int(value))
        return True
    except Exception as e:
        print("[ui_space] set_value fail:", page_id, widget_id, e)
        return False


def get_value(page_id, widget_id):
    """讀單一 widget 的目前實際值(讀 state 陣列)。查詢方用。
    list/str/action 走 _ui_var。"""
    if not _alloced:
        return None
    meta = _find_meta(page_id, widget_id)
    if meta is None:
        return None
    t = meta["type"]
    try:
        if t in ("list", "str", "action"):
            var = bus.shared.get(K_VAR) or {}
            return var.get(meta["source"] or meta["event"])
        if t == "switch":
            return _bit_get(bus.shared.get(K_SW_ST), meta["idx"])
        return _i32_get(bus.shared.get(K_INT_ST), meta["idx"])
    except Exception:
        return None


def _find_meta(page_id, widget_id):
    plist = _decl.get(page_id)
    if not plist:
        return None
    for m in plist:
        if m["id"] == widget_id:
            return m
    return None


def dump_persistent():
    """把 switch + int state 陣列整包序列化(bytes),供持久化用。
    可直接寫進 /sd/ui_state.bin。"""
    if not _alloced:
        return b""
    sw = bytes(bus.shared.get(K_SW_ST) or b"")
    ints = bytes(bus.shared.get(K_INT_ST) or b"")
    return sw + ints


def restore_persistent(data):
    """從 dump_persistent 的資料還原 state(只還原 state,不動 ctrl)。"""
    if not _alloced or not data:
        return
    sw_st = bus.shared.get(K_SW_ST)
    int_st = bus.shared.get(K_INT_ST)
    if sw_st and len(data) >= len(sw_st):
        sw_st[:] = data[:len(sw_st)]
    if int_st:
        off = len(sw_st)
        rest = data[off:off + len(int_st)]
        if len(rest) == len(int_st):
            int_st[:] = rest
