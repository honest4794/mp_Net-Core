"""
pixel_task.py — pixel 子系統統一管理任務（PixelTask）

四層資料：
  1. effects  : pixel/effects/（effects.json + effects.py 生成器，py 優先）
  2. mapping  : pixel/map/*.json（每套一套群組，自帶 id/name）
  3. modes    : pixel/modes/*.json（模式 = 效果 × 群組配對 + 播放參數）
  4. registry : pixel/registry.json（播放清單 + auto_play）

on_start 依序初始化：硬體（st_pixel）→ effects → mapping（PixelLayout）→ modes → registry。
loop() = 播放端：大隊列（registry.list）依序播放，show 循環；mode 的播放參數
（play_count / play_interval）控制每輪出現與否，單位全用 frame。

硬體 order/counts 一律從播放器（PixelStreamer.controllers）推導，不自己設定
（硬體真值）。registry.json 只用來選擇「播什麼 / 開不開自動播放」。

指令介面（bus.shared，指令層寫入、本任務消費）：
  pixel_play   → 開始/重啟 show
  pixel_stop   → 停止（熄燈）
  pixel_pause  → 暫停 / 恢復
"""

import time
import json
from lib.task import Task
from lib.sys_bus import bus
from lib.log_service import get_log
from lib.pixel_layout import PixelLayout

EFFECTS_JSON = "/pixel/effects/effects.json"
MAP_DIR = "/pixel/map"
MODES_DIR = "/pixel/modes"
REGISTRY_JSON = "/pixel/registry.json"

# 硬體 controller 型別 → registry 統一 key（單一真源）
TYPE_MAP = {"APA102": "apa102", "WS2812": "ws2812", "i2c_pixel": "pca9685"}

WRITE_WHITELIST = ("r", "g", "b", "w", "ww", "rgb", "rgbw", "wwww")


def _list_json(d):
    """目錄下 *.json 檔的完整路徑清單（目錄不存在 → []）。"""
    import os
    try:
        return [d.rstrip("/") + "/" + f for f in os.listdir(d) if f.endswith(".json")]
    except OSError:
        return []


class PixelTask(Task):
    """pixel 管理 + 播放端：初始化四層資料，並執行大隊列自動播放。"""

    def __init__(self, name, ctx):
        super().__init__(name, ctx)
        self._st = None
        self._lay = None
        self._gens = {}
        self._modes = {}
        self._show = {"auto_play": False, "list": []}
        self._show_list = []
        self._playing = False
        self._paused = False
        self._pass = 1       # 目前 show 的輪次（第 1 輪起）
        self._mode_idx = 0
        self._cur = None
        self._interval_us = 25000
        self._next_tick_us = 0

    # ── 啟動：依序初始化 ──────────────────────────
    def on_start(self):
        super().on_start()
        try:
            self._init_hw()
            self._init_effects()
            self._init_layout()
            self._init_modes()
            self._init_show()
            if self._show["auto_play"] and self._show_list:
                self._start()
        except Exception as e:
            get_log().error("[Pixel] 初始化失敗: {}".format(e))

    def _init_hw(self):
        """確保 st_pixel 存在（播放器 = 硬體真值）；順便兜底 pixel_stream hub。"""
        st = bus.get_service("st_pixel")
        if st is None:
            from driver.pixel_drv import init_pixel
            try:
                init_pixel(bus)
                st = bus.get_service("st_pixel")
            except Exception as e:
                get_log().error("[Pixel] init_pixel 失敗: {}".format(e))
        if st is None:
            get_log().warn("[Pixel] 無 st_pixel（pixel 硬體未接）— 僅載入設定")
            return
        self._st = st

        if bus.get_service("pixel_stream") is None:
            try:
                from lib.buffer_hub import AtomicStreamHub
                frames = bus.shared.get("System", {}).get("buffer_frames", 1)
                bus.register_service("pixel_stream", AtomicStreamHub(st.total_bytes * frames))
            except Exception as e:
                get_log().error("[Pixel] pixel_stream hub 建立失敗: {}".format(e))

        fps = bus.shared.get("System", {}).get("local_fps", 40)
        self._interval_us = (1000 // fps) * 1000

    def _init_effects(self):
        """py register + 載 effects.json → bus.shared["pixel_gens"]（存 cls/params，播放時建 Effect）。"""
        from pixel.effects import effects
        try:
            with open(EFFECTS_JSON) as f:
                effects.load_json(json.load(f).get("effects", []))
        except OSError:
            get_log().warn("[Pixel] 找不到 {}，僅用 py 效果".format(EFFECTS_JSON))
        except Exception as e:
            get_log().error("[Pixel] 載入 {} 失敗: {}".format(EFFECTS_JSON, e))

        gens = {}
        for name, eid in effects.dump().items():
            gens[name] = {
                "id": eid,
                "name": name,
                "cls": effects.resolve(eid),
                "params": effects.get_params(eid),
            }
        self._gens = gens
        bus.shared["pixel_gens"] = gens
        # 開機預計算波表：掩蓋首次播放的計算成本（同 effect 之後零重算）
        n_wave = effects.warm_up()
        get_log().info("[Pixel] effects: {} 個（波表預算 {} 個）".format(len(gens), n_wave))

    def _init_layout(self):
        """從播放器推導 order/counts，載入 map/*.json 註冊全部 mapping → pixel_layout。"""
        st = self._st
        order = []
        counts = {}
        if st:
            for c in st.controllers:
                t = TYPE_MAP.get(getattr(c, "pixel_type", ""))
                if t is None:
                    get_log().warn("[Pixel] 未知 controller 型別: {!r}".format(c.pixel_type))
                    continue
                if t not in counts:
                    counts[t] = 0
                    order.append(t)
                counts[t] += c.num_pixels
        if not order:
            get_log().warn("[Pixel] 播放器無可辨識 controller — order 為空")

        lay = PixelLayout(order, counts)
        for fn in _list_json(MAP_DIR):
            try:
                with open(fn) as f:
                    m = json.load(f)
                self._warn_missing_types(lay, m)
                lay.register_mapping(m["id"], m["name"], m.get("groups", []))
                get_log().info("[Pixel] mapping {}（{}）: {} group(s)".format(
                    m["id"], m["name"], len(m.get("groups", []))))
            except ValueError as e:
                get_log().warn("[Pixel] 跳過 mapping {}: {}".format(fn, e))
            except Exception as e:
                get_log().warn("[Pixel] 載入 {} 失敗: {}".format(fn, e))

        self._lay = lay
        bus.shared["pixel_layout"] = lay

    @staticmethod
    def _warn_missing_types(lay, m):
        """warn 群組引用到未接硬體的型別（誠實反映為空段）。"""
        for g in m.get("groups", []):
            for seg in g.get("sel", []):
                t = seg["type"]
                if isinstance(t, int):
                    continue  # 以 order index 引用，無法預檢
                if t not in lay.counts:
                    get_log().warn("[Pixel] mapping {} group {} 引用無硬體型別 {!r}（空段）".format(
                        m["name"], g["name"], t))

    def _init_modes(self):
        """載入 modes/*.json → bus.shared["pixel_maps"]。解析失敗只 warn 跳過該項。"""
        modes = {}
        for fn in _list_json(MODES_DIR):
            try:
                with open(fn) as f:
                    d = json.load(f)
                self._parse_mode(d, modes)
            except Exception as e:
                get_log().warn("[Pixel] 載入 {} 失敗: {}".format(fn, e))
        self._modes = modes
        bus.shared["pixel_maps"] = modes
        get_log().info("[Pixel] modes: {} 個".format(len(modes)))

    def _parse_mode(self, d, modes):
        mid = int(d["id"])
        name = d["name"]
        if mid in modes:
            get_log().warn("[Pixel] mode id 重複 {}（{}）— 跳過".format(mid, name))
            return
        for other in modes.values():
            if other["name"] == name:
                get_log().warn("[Pixel] mode name 重複 {} — 跳過".format(name))
                return
        lay = self._lay
        if lay is None:
            get_log().warn("[Pixel] mode {} 載入前無 pixel_layout — 跳過".format(name))
            return

        default_map = d.get("mapping")
        entries = []
        seen = set()
        for it in d.get("map", []):
            gref = it["group"]
            mref = default_map
            if isinstance(gref, str) and "." in gref:
                mref, gref = gref.split(".", 1)
            try:
                rmid, rgid = lay.resolve_group(mref, gref)
            except (KeyError, ValueError, TypeError):
                get_log().warn("[Pixel] mode {} 引用未知群組 {!r} — 跳過該項".format(name, it["group"]))
                continue
            key = (rmid, rgid)
            if key in seen:
                get_log().warn("[Pixel] mode {} 群組 {!r} 重複 — 只保留第一項".format(name, it["group"]))
                continue
            seen.add(key)

            eff = self._find_effect(it["effect"])
            if eff is None:
                get_log().warn("[Pixel] mode {} 引用未知效果 {!r} — 跳過該項".format(name, it["effect"]))
                continue
            write = it["write"]
            if write not in WRITE_WHITELIST:
                get_log().warn("[Pixel] mode {} 未知寫法 {!r} — 跳過該項".format(name, write))
                continue
            entries.append({
                "mref": rmid, "gref": rgid, "write": write,
                "cls": eff["cls"], "name": eff["name"], "params": eff["params"],
            })

        modes[mid] = {
            "id": mid,
            "name": name,
            "index": d.get("index", mid),
            "play_count": d.get("play_count", 1),
            "play_interval": d.get("play_interval", 1),
            "entries": entries,
        }

    def _find_effect(self, ref):
        if isinstance(ref, int):
            for g in self._gens.values():
                if g["id"] == ref:
                    return g
            return None
        return self._gens.get(ref)

    def _init_show(self):
        """載入 registry.json（播放清單 + auto_play）→ bus.shared["pixel_show"]。"""
        show = {"auto_play": False, "list": []}
        try:
            with open(REGISTRY_JSON) as f:
                d = json.load(f)
            show["auto_play"] = bool(d.get("auto_play", False))
            show["list"] = d.get("list", [])
        except OSError:
            get_log().warn("[Pixel] 找不到 {} — 關閉自動播放".format(REGISTRY_JSON))
        except Exception as e:
            get_log().error("[Pixel] 載入 {} 失敗: {}".format(REGISTRY_JSON, e))
        self._show = show
        bus.shared["pixel_show"] = show

        lst = []
        for ref in show["list"]:
            m = self._find_mode(ref)
            if m is None:
                get_log().warn("[Pixel] 播放清單引用未知 mode {!r} — 跳過".format(ref))
                continue
            lst.append(m)
        self._show_list = lst
        get_log().info("[Pixel] show: auto_play={} list={} 個".format(show["auto_play"], len(lst)))

    def _find_mode(self, ref):
        if isinstance(ref, int):
            return self._modes.get(ref)
        for m in self._modes.values():
            if m["name"] == ref:
                return m
        return None

    # ── 播放端：大隊列 show ───────────────────────
    def _start(self):
        self._playing = True
        self._paused = False
        self._pass = 1
        self._mode_idx = 0
        self._release_player(self._cur)
        self._cur = None
        self._next_tick_us = time.ticks_us()
        get_log().info("[Pixel] ▶ show 開始（{} mode(s)）".format(len(self._show_list)))

    def _stop(self):
        self._playing = False
        self._release_player(self._cur)
        self._cur = None
        if self._st:
            buf = self._st.big_buffer
            for i in range(len(buf)):
                buf[i] = 0
            self._st.show_all()
        get_log().info("[Pixel] ■ show 停止")

    def _consume_cmds(self):
        if bus.shared.pop("pixel_stop", None) is not None:
            self._stop()
        if bus.shared.pop("pixel_play", None) is not None:
            self._start()
        if bus.shared.pop("pixel_pause", None) is not None:
            self._paused = not self._paused
            get_log().info("[Pixel] ⏸ paused={}".format(self._paused))

    def _should_play(self, mode):
        """這一輪（pass）這個 mode 是否要播。"""
        pc = mode["play_count"]
        if pc == 0:
            return False                       # 永遠跳過
        if pc > 0 and self._pass > pc:
            return False                       # 開頭段：只在前 N 輪出現
        if (self._pass - 1) % mode["play_interval"] != 0:
            return False                       # 週期性：每隔 N 輪出現一次
        return True                            # -1 = 常駐每輪

    def _find_next(self):
        """掃一圈找下一個要播的 mode；沒有 → _cur 保持 None（空輪，pass 已推進）。"""
        lst = self._show_list
        for _ in range(len(lst)):
            mode = lst[self._mode_idx]
            self._mode_idx += 1
            if self._mode_idx >= len(lst):
                self._mode_idx = 0
                self._pass += 1
            if self._should_play(mode):
                self._cur = self._make_player(mode)
                return

    def _make_player(self, mode):
        """mode → 播放器：每個 entry 一個 fresh generator（每次播放都重建）。"""
        return [{
            "mref": e["mref"], "gref": e["gref"], "write": e["write"],
            "gen": self._instantiate(e["cls"], e["name"], e["params"]),
            "done": False,
        } for e in mode["entries"]]

    @staticmethod
    def _instantiate(cls, name, params):
        """依 json 參數建立 Effect 實例（有 __next__/restart/seek）。"""
        return cls(name, params)

    @staticmethod
    def _release_player(player):
        """off 即丟：釋放每個 entry 的 effect 波緩衝（Effect.release()）。"""
        if player:
            for e in player:
                gen = e.get("gen")
                if gen is not None and hasattr(gen, "release"):
                    gen.release()

    def _tick_player(self, player):
        """播放器推進一幀。回傳 True = 還在播；False = 全部 entry 耗盡（mode 結束）。"""
        lay = self._lay
        buf = self._st.big_buffer
        alive = False
        for e in player:
            if e["done"]:
                continue
            try:
                vals = next(e["gen"])
            except StopIteration:
                e["done"] = True
                continue
            lay.scatter(buf, e["mref"], e["gref"], vals, e["write"])
            alive = True
        if not alive:
            return False
        self._st.show_all()
        return True

    def loop(self):
        if not self.running:
            return
        self._consume_cmds()
        if not self._playing or self._paused or self._st is None:
            return
        now = time.ticks_us()
        if time.ticks_diff(now, self._next_tick_us) < 0:
            return
        self._next_tick_us = time.ticks_add(self._next_tick_us, self._interval_us)
        if self._cur is None:
            self._find_next()
            if self._cur is None:
                return
        if not self._tick_player(self._cur):
            self._release_player(self._cur)
            self._cur = None

    def on_stop(self):
        super().on_stop()
        self._playing = False
        self._release_player(self._cur)
        self._cur = None
