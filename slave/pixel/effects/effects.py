"""
effects.py — 效果生成器集中登記

pixel 子系統第二層的「py 形式」：所有效果生成器集中在此。

- 效果的 name 直接用函數名稱（fn.__name__）：函數叫 `breathing`，效果名就是 `breathing`
- 每個效果都有 id + name
- 與 effects.json（json 形式）共用同一張登記表，兩邊防撞車
- 名稱撞車時「程式優先」：生成器函數永遠由 py 提供，json 只提供 id / params
- 載入順序無關：json 先載或 py 先登記，結果一致
- id 從 1 開始，0 保留為「未指定 / 自動配發」哨兵值
- 無 engine、無「逐顆 / 整批」等模式之分：只有一個生成器，輸出位數由 pixel_n 決定
- 生成器吐 `array('H')`（0-4095），供 scatter 的 viper 用 ptr16 直接讀，零分配

不碰硬體、不碰 bus、不碰 pixel_stream。
"""

import math
from array import array as _array

# ── 效果登記表（json 與 py 共用）──────────────────────────
# name -> {"id": int|None, "make": fn|None, "params": dict|None}
_EFFECTS = {}
_IDS = {}       # id -> name


def _next_id():
    """配發下一個可用 id（從 1 開始，跳過已用）。"""
    i = 1
    while i in _IDS:
        i += 1
    return i


def _assign_id(name, eid):
    """把 id 指派給 name（含 id 衝突檢查）。"""
    if eid in _IDS and _IDS[eid] != name:
        raise ValueError("EFFECT ID CONFLICT: id={} 已被 {} 使用".format(eid, _IDS[eid]))
    _IDS[eid] = name
    _EFFECTS[name]["id"] = eid


def load_json(effects_list):
    """載入 effects.json 的 effects[]。

    只負責「id + params」；若同 name 已有 py 生成器（程式優先），不覆蓋 make。
    """
    for e in effects_list:
        eid = int(e["id"])
        name = e["name"]
        entry = _EFFECTS.setdefault(name, {"id": None, "make": None, "params": None})

        if entry["params"] is not None:
            raise ValueError("EFFECT NAME CONFLICT: name={} 在 json 重複".format(name))
        entry["params"] = e

        if entry["id"] is None:
            _assign_id(name, eid)
        elif entry["id"] != eid:
            raise ValueError("EFFECT ID CONFLICT: name={} py id={} vs json id={}".format(
                name, entry["id"], eid))


def register(fn):
    """登記一個 py 效果生成器。name = fn.__name__；同名時「程式優先」。"""
    name = fn.__name__
    entry = _EFFECTS.setdefault(name, {"id": None, "make": None, "params": None})

    if entry["make"] is not None:
        raise ValueError("EFFECT NAME CONFLICT: name={} 已登記".format(name))
    entry["make"] = fn

    # 若 json 已給 id 就用 json 的；否則自動配發
    if entry["id"] is None:
        _assign_id(name, _next_id())
    return entry["id"]


def resolve(ref):
    """ref = id(int) 或 name(str) → make 生成器函數。"""
    name = _IDS[ref] if isinstance(ref, int) else ref
    return _EFFECTS[name]["make"]


def get_params(ref):
    """ref = id 或 name → 效果參數 dict（來自 json；純 py 效果回 None）。"""
    name = _IDS[ref] if isinstance(ref, int) else ref
    return _EFFECTS[name]["params"]


def dump():
    """回傳 name -> id 對照（除錯用）。"""
    return {name: _EFFECTS[name]["id"] for name in _EFFECTS}


# ── 波形純量 generator（示範簡化版）────────────────────────
def _shape(program):
    """時間序列（program）→ 波形純量 generator，0-4095。

    真正實作對齊 LEDMathMethod.is_math_pattern_next；這裡只示範 math_now（正弦）。
    """
    t = 0
    while True:
        for seg in program:
            f = seg.get("F", 1)
            l_max = seg.get("l_max", 4095)
            l_lim = seg.get("l_lim", 0)
            phi = seg.get("phi", 0)
            end = seg.get("end_Time", 100)
            amp = (l_max - l_lim) / 2.0
            mid = (l_max + l_lim) / 2.0
            for _ in range(end):
                ang = (t * f + phi / 4095.0) * 2.0 * math.pi
                v = mid + amp * math.sin(ang)
                yield int(max(0, min(4095, v)))
                t += 1


# ── 效果生成器（名稱 = 函數名稱）──────────────────────────

def breathing(pixel_n, program=None, speed=1, reverse=False, **params):
    """breathing：呼吸（同一個波值填滿 pixel_n 個位）。"""
    if program is None:
        program = [
            {"func": "math_now", "F": 2, "l_max": 4095, "l_lim": 100, "phi": 0, "end_Time": 200},
            {"func": "square_wave_now", "F": 1, "l_max": 3000, "l_lim": 0, "phi": 1024, "end_Time": 100},
        ]
    gen = _shape(program)
    buf = _array('H', [0] * pixel_n)   # 常駐 buffer（零重複分配）
    while True:
        v = next(gen)
        for i in range(pixel_n):
            buf[i] = v
        for _ in range(speed):
            yield buf[::-1] if reverse else buf


register(breathing)   # name = "breathing"


if __name__ == "__main__":
    # ── PC 快速自檢（示範 json + py 共表、程式優先）─────
    # 模組載入時已 register(breathing)（py 先登記，自動 id=1）。
    # 這裡補載 json（對應 effects.json），名稱撞車 → 程式優先，id 保留、params 由 json 補上。
    load_json([
        {
            "id": 1, "name": "breathing", "pixel_n": 10,
            "program": [
                {"func": "math_now", "F": 2, "l_max": 4095, "l_lim": 100, "phi": 0, "end_Time": 200},
                {"func": "square_wave_now", "F": 1, "l_max": 3000, "l_lim": 0, "phi": 1024, "end_Time": 100},
            ],
            "speed": 3, "reverse": False,
        },
    ])

    print("已登記:", dump())          # {'breathing': 1}
    assert resolve(1) is breathing, "id=1 應解析到 py 的 breathing"
    assert resolve("breathing") is breathing, "name 應解析到 py 的 breathing"

    p = get_params("breathing")       # 參數來自 json
    gen = resolve(1)(p["pixel_n"], program=p["program"], speed=p["speed"], reverse=p["reverse"])
    for i in range(3):
        buf = next(gen)
        assert len(buf) == p["pixel_n"], "輸出長度必須 == pixel_n"
        assert all(0 <= v <= 4095 for v in buf), "值域必須 0-4095"
        print(buf)
