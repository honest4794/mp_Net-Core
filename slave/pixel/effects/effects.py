"""
effects.py — 效果目錄 + Effect 類別（12-bit 整數、免查表、可 restart/seek）

- 效果 name = 類別名（cls.__name__）
- 每個效果有 id + name；id 從 1 起，0 保留為哨兵
- json 與 py 共用登記表，名稱撞車時「程式（py）優先」；載入順序無關
- 數學核心在 lib.PixelMathMethod（@micropython.viper 整數多項式，0-4095）
- Effect 實例：有 __next__ / restart / seek，供 PixelTask 播放端每次播放重建
- 空間分布：frame(t) 把時間波攤到 pixel_n 顆（step × 時間步進 + 像素序 × spacing + offset）

不碰硬體、不碰 bus、不碰 pixel_stream。
"""

from array import array as _array
from lib.PixelMathMethod import mt

try:
    import micropython
    _MP = True
except ImportError:
    _MP = False
    micropython = None


# ── 播放迴圈（viper / 純 Python 雙路徑）：波緩衝 index + 乘轉加 ──
# wave 已預先算好（array('H')，長度 total），frame 熱路徑只做：讀波 + 加法 + 單次減法取模。
# g 進入時已正規化到 [0,total)，spacing 已 < total → g+spacing 最多 < 2*total，
# 單次 `if g>=total: g-=total` 即完成取模（避免 MicroPython 昂貴的 %）。

if _MP:

    @micropython.viper
    def _fill_fwd(buf, wave, n: int, g: int, spacing: int, total: int):
        pb = ptr16(buf)
        pw = ptr16(wave)
        for i in range(n):
            pb[i] = pw[g]
            g += spacing
            if g >= total:
                g -= total

    @micropython.viper
    def _fill_rev(buf, wave, n: int, g: int, spacing: int, total: int):
        pb = ptr16(buf)
        pw = ptr16(wave)
        for i in range(n):
            pb[n - 1 - i] = pw[g]
            g += spacing
            if g >= total:
                g -= total

else:

    def _fill_fwd(buf, wave, n, g, spacing, total):
        for i in range(n):
            buf[i] = wave[g]
            g += spacing
            if g >= total:
                g -= total

    def _fill_rev(buf, wave, n, g, spacing, total):
        for i in range(n):
            buf[n - 1 - i] = wave[g]
            g += spacing
            if g >= total:
                g -= total


# ── 效果登記表（json 與 py 共用）──────────────────────────
# name -> {"id": int|None, "cls": class|None, "params": dict|None}
_EFFECTS = {}
_IDS = {}       # id -> name


def _next_id():
    i = 1
    while i in _IDS:
        i += 1
    return i


def _assign_id(name, eid):
    if eid in _IDS and _IDS[eid] != name:
        raise ValueError("EFFECT ID CONFLICT: id={} 已被 {} 使用".format(eid, _IDS[eid]))
    _IDS[eid] = name
    _EFFECTS[name]["id"] = eid


def load_json(effects_list):
    """載入 effects.json 的 effects[]。只補 id + params；同 name 已有 py 類別不覆蓋。"""
    for e in effects_list:
        eid = int(e["id"])
        name = e["name"]
        entry = _EFFECTS.setdefault(name, {"id": None, "cls": None, "params": None})
        if entry["params"] is not None:
            raise ValueError("EFFECT NAME CONFLICT: name={} 在 json 重複".format(name))
        entry["params"] = e
        if entry["id"] is None:
            _assign_id(name, eid)
        elif entry["id"] != eid:
            raise ValueError("EFFECT ID CONFLICT: name={} py id={} vs json id={}".format(
                name, entry["id"], eid))


def register(cls):
    """登記一個效果類別。name = cls.__name__；同名時「程式優先」。"""
    name = cls.__name__
    entry = _EFFECTS.setdefault(name, {"id": None, "cls": None, "params": None})
    if entry["cls"] is not None:
        raise ValueError("EFFECT NAME CONFLICT: name={} 已登記".format(name))
    entry["cls"] = cls
    if entry["id"] is None:
        _assign_id(name, _next_id())
    return entry["id"]


def resolve(ref):
    """ref = id(int) 或 name(str) → 效果類別。"""
    name = _IDS[ref] if isinstance(ref, int) else ref
    return _EFFECTS[name]["cls"]


def get_params(ref):
    """ref = id 或 name → 效果參數 dict（來自 json；純 py 效果回 None）。"""
    name = _IDS[ref] if isinstance(ref, int) else ref
    return _EFFECTS[name]["params"]


def make(ref):
    """ref = id 或 name → 建立 Effect 實例（每次播放都該重建一份）。"""
    name = _IDS[ref] if isinstance(ref, int) else ref
    return _EFFECTS[name]["cls"](name, _EFFECTS[name]["params"])


def dump():
    """回傳 name -> id 對照（除錯用）。"""
    return {name: _EFFECTS[name]["id"] for name in _EFFECTS}


# ── 波表快取（module 層）：儲存每個效果的波表，首次算好後共享 ──
# 舊方法常駐一張 65536 點 sin 全表（128KB）；現在只需存效果自己的波表
# （end_Time × 2B，eyes 才 640B）。同 name + 同 program 只算一次，重啟/重建零重算。
_WAVE_CACHE = {}   # name -> {"key": repr(program), "total": int, "wave": array('H')}


def _wave_key(program):
    return repr(program)


def _get_or_build_wave(name, program):
    """取 name 的波表；program 沒變就命中快取，變了就重算。回傳 (wave, total)。"""
    key = _wave_key(program)
    entry = _WAVE_CACHE.get(name)
    if entry is not None and entry["key"] == key:
        return entry["wave"], entry["total"]
    comp = mt.compile(program)
    total = comp[-1][1] if comp else 0
    if total > 0:
        wave = _array('H', [mt.value_at(comp, x) for x in range(total)])
    else:
        wave = _array('H', [0])
    _WAVE_CACHE[name] = {"key": key, "total": total, "wave": wave}
    return wave, total


def warm_up():
    """開機預計算：把已登記效果的波表先算好，掩蓋首次播放的計算成本。

    之後 frame 只做 index 讀取、零重算；重啟/重建 effect 直接命中快取。
    回傳已預算的波表數。
    """
    for name, entry in _EFFECTS.items():
        params = entry.get("params")
        if params is not None:
            program = params.get("program")
        else:
            cls = entry.get("cls")
            program = getattr(cls, "DEFAULT_PROGRAM", []) if cls else None
        if program:
            _get_or_build_wave(name, program)
    return len(_WAVE_CACHE)


def clear_wave_cache():
    """清空波表快取（例如 effects.json 重載後需要重新預算）。"""
    _WAVE_CACHE.clear()


# ── Effect 類別 ──────────────────────────────────────────
class Effect:
    """效果基類：時間波形 + 空間分布 → 一整幀 array('H')（0-4095）。

    子類可覆寫 DEFAULT_PROGRAM 提供純 py 時的預設波形（json 有 params 時優先）。
    frame(t) 是決定性、無狀態的：每顆 pixel i 的值 = pattern_value_at(program, 相位)。
    相位 = (t // speed) * step + i * spacing + offset（對齊舊 wave_list_assign_next）。
    """
    DEFAULT_PROGRAM = []

    def __init__(self, name, params=None):
        self.name = name
        params = params or {}
        self.id = params.get("id")
        self.program = params.get("program") or list(self.DEFAULT_PROGRAM)
        self.pixel_n = int(params.get("pixel_n", 1))
        self.step = int(params.get("step", 1))
        self.spacing = int(params.get("spacing", 1))
        self.offset = int(params.get("offset", 0))
        self.speed = int(params.get("speed", 1))
        self.reverse = bool(params.get("reverse", False))
        self._t = 0
        self._buf = _array('H', [0] * self.pixel_n)
        # 波表：module 層快取（同 name + 同 program 只算一次），開機 warm_up() 已預先算好。
        self._wave, self._total = _get_or_build_wave(self.name, self.program)
        self._spacing_mod = self.spacing % self._total if self._total else 0

    def release(self):
        """off 時丟棄實例的波表引用（波表本身在 module 快取，重啟/重建零重算）。"""
        self._wave = None

    def frame(self, t):
        """回傳第 t 幀（array('H')，pixel_n 個值，全 0-4095）。決定性、無狀態。

        熱路徑只做：index 讀波 + 加法 + 單次減法取模（乘數轉加數，無 sin / 無除法 / 無 %）。
        """
        total = self._total
        if total <= 0:
            return self._buf
        buf = self._buf
        n = self.pixel_n
        g = ((int(t) // self.speed) * self.step + self.offset) % total
        if self.reverse:
            _fill_rev(buf, self._wave, n, g, self._spacing_mod, total)
        else:
            _fill_fwd(buf, self._wave, n, g, self._spacing_mod, total)
        return buf

    def restart(self):
        self._t = 0

    def seek(self, t):
        self._t = int(t)

    def __next__(self):
        b = self.frame(self._t)
        self._t += 1
        return b


# ── 內建效果（名稱 = 類別名）──────────────────────────────

class breathing(Effect):
    """呼吸：全像素同值（spacing=0 由 json 給），波形 = 正弦 + 方波兩段。"""
    DEFAULT_PROGRAM = [
        {"type": "math_now", "F": 2, "l_max": 4095, "l_lim": 100, "phi": 0, "end_Time": 200},
        {"type": "square_wave_now", "F": 1, "l_max": 3000, "l_lim": 0, "phi": 1024, "end_Time": 300},
    ]


class eyes(Effect):
    """眼睛（舊專案 eyes_start）：多段正弦爬升 + spacing 空間分布。"""
    DEFAULT_PROGRAM = [
        {"type": "keep",     "F": 1, "l_max": 0,    "l_lim": 0,   "phi": 0,    "end_Time": 60},
        {"type": "math_now", "F": 5, "l_max": 100,  "l_lim": 20,  "phi": 3071, "end_Time": 100},
        {"type": "math_now", "F": 5, "l_max": 1023, "l_lim": 100, "phi": 3071, "end_Time": 200},
        {"type": "math_now", "F": 5, "l_max": 1023, "l_lim": 200, "phi": 1023, "end_Time": 320},
    ]


register(breathing)
register(eyes)


if __name__ == "__main__":
    # ── PC 快速自檢（不依賴硬體）────────────────────────
    import math
    from lib.PixelMathMethod import _wave01_q12

    # 1. 多項式逼近準確率（math.sin 只用於測試對照，正式運算路徑無浮點）
    max_err = 0.0
    for phase in range(0, 65536, 64):
        ideal = (math.sin(2 * math.pi * phase / 65536.0) + 1.0) / 2.0 * 4095.0
        approx = _wave01_q12(phase)
        err = abs(ideal - approx)
        if err > max_err:
            max_err = err
    print("多項式逼近最大誤差: {:.2f} / 4095".format(max_err))
    assert max_err < 60, "多項式逼近誤差過大"

    # 2. 補載 json（對齊 effects.json），名稱撞車 → 程式優先，params 由 json 補上
    load_json([
        {
            "id": 1, "name": "breathing", "pixel_n": 64,
            "program": [
                {"type": "math_now", "F": 2, "l_max": 4095, "l_lim": 100, "phi": 0, "end_Time": 200},
                {"type": "square_wave_now", "F": 1, "l_max": 3000, "l_lim": 0, "phi": 1024, "end_Time": 300},
            ],
            "step": 1, "spacing": 0, "offset": 0, "speed": 3, "reverse": False,
        },
        {
            "id": 2, "name": "eyes", "pixel_n": 64,
            "program": [
                {"type": "keep",     "F": 1, "l_max": 0,    "l_lim": 0,   "phi": 0,    "end_Time": 60},
                {"type": "math_now", "F": 5, "l_max": 100,  "l_lim": 20,  "phi": 3071, "end_Time": 100},
                {"type": "math_now", "F": 5, "l_max": 1023, "l_lim": 100, "phi": 3071, "end_Time": 200},
                {"type": "math_now", "F": 5, "l_max": 1023, "l_lim": 200, "phi": 1023, "end_Time": 320},
            ],
            "step": 1, "spacing": 10, "offset": 0, "speed": 1, "reverse": False,
        },
    ])

    print("已登記:", dump())
    assert dump() == {"breathing": 1, "eyes": 2}
    assert resolve(1) is breathing
    assert resolve("eyes") is eyes

    # 3. make + frame：長度 == pixel_n，值域 0-4095
    for name in ("breathing", "eyes"):
        eff = make(name)
        assert eff.pixel_n == 64
        for _ in range(5):
            buf = next(eff)
            assert len(buf) == 64, "輸出長度必須 == pixel_n"
            assert all(0 <= v <= 4095 for v in buf), "值域必須 0-4095"
        print("{}: frame[0] 前 8 值 =".format(name), list(next(eff))[:8])

    # 4. restart / seek（決定性）
    eff = make("eyes")
    f0 = list(next(eff))
    f1 = list(next(eff))
    eff.seek(0)
    f0_seek = list(next(eff))
    assert f0 == f0_seek, "seek(0) 後應重現 frame 0"
    eff.restart()
    f0_restart = list(next(eff))
    assert f0 == f0_restart, "restart 後應重現 frame 0"
    assert f0 != f1, "frame 0 與 frame 1 應不同（eyes 有空間分布）"

    # breathing 全像素同值（spacing=0）
    eff = make("breathing")
    b0 = next(eff)
    assert all(v == b0[0] for v in b0), "breathing 應全像素同值"

    print("OK — effects（class 化 + 整數多項式 + restart/seek + 值域）驗證通過")
