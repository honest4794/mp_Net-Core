"""
pixel_gen_tasks.py — pixel 生成器 task

開機時把所有 effect 轉成 generator 列表，存入 bus.shared["pixel_gens"]，
供渲染迴圈 / 指令層取用。

第一步：只做「全量建立 generator」。如何套到群組、套哪種寫入方法（rgb/w/ww）
由渲染迴圈（PixelLayout.scatter）決定，這裡不處理。
"""
from lib.task import Task
from lib.sys_bus import bus
from lib.log_service import get_log


EFFECTS_JSON = "/pixel/effects/effects.json"


class PixelGenTask(Task):
    """把所有 effect 建立成 generator，存進 bus.shared["pixel_gens"]。"""

    def __init__(self, name, ctx):
        super().__init__(name, ctx)
        self._gens = {}

    def on_start(self):
        super().on_start()
        self._build_gens()
        get_log().info("[PixelGen] 已建立 {} 個 effect generator".format(len(self._gens)))

    def _load_json(self, effects):
        """載入 effects.json（id / params）；py 生成器已在 import 時登記（程式優先）。"""
        import json
        try:
            with open(EFFECTS_JSON) as f:
                data = json.load(f)
            effects.load_json(data.get("effects", []))
        except OSError:
            get_log().warn("[PixelGen] 找不到 {}，僅用 py 效果".format(EFFECTS_JSON))
        except Exception as e:
            get_log().error("[PixelGen] 載入 {} 失敗: {}".format(EFFECTS_JSON, e))

    def _build_gens(self):
        from pixel.effects import effects

        self._load_json(effects)

        gens = {}
        for name, eid in effects.dump().items():
            make = effects.resolve(eid)
            params = effects.get_params(eid)
            gens[name] = {
                "id": eid,
                "gen": self._instantiate(make, params),
            }

        bus.shared["pixel_gens"] = gens
        self._gens = gens

    @staticmethod
    def _instantiate(make, params):
        """依 json 參數建立 generator。純 py 效果（無 json）先給 pixel_n=1 佔位。"""
        if params:
            return make(
                params.get("pixel_n", 1),
                program=params.get("program"),
                speed=params.get("speed", 1),
                reverse=params.get("reverse", False),
            )
        return make(1)

    def loop(self):
        # 暫無週期工作
        pass

    def on_stop(self):
        super().on_stop()
        self._gens = {}
        if "pixel_gens" in bus.shared:
            del bus.shared["pixel_gens"]
