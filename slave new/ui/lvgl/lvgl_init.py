# ui/lvgl/lvgl_init.py — LVGL display 一次初始化 + bus reuse
#
# 對齊 driver/i80_drv.py、driver/tft_drv.py 的模式:
#   config() 開頭先 bus.get_service("lvgl_disp");已存在就直接 return,不重複初始化。
#
# 為什麼這樣做:
#   - soft-reboot 後 LVGL C 層狀態殘留,重複 deinit/init 再 display_create
#     會解到 garbage(MemoryError 要求配置數百 MB)。
#   - LVGL display + draw buffer 只該配一次,放 bus 後 reuse,避免記憶體碎片。
#   - boot.py 跑完後 LVGL 不會自動起;這裡是「需要時才起,起一次就用到底」。
#
# bus service 名稱:"lvgl_disp"(放 LvglDisp 平台物件,含 lcd/bus/disp + platform 介面)
#
# 用法:
#   from ui.lvgl.lvgl_init import get_platform
#   plat = get_platform()       # 已起就 reuse,沒起就初始化
#   plat.tick(); rects = plat.take(); plat.show(*rects[0])
import lvgl as lv
from lib.sys_bus import bus

_W = 320
_H = 240
_LINES = 40
_BPP = 2
_SERVICE = "lvgl_disp"


class LvglDisp:
    """LVGL display + slave new LCD 平台。
    構造一次後放 bus.service("lvgl_disp"),reuse。
    提供 app 要的 platform 介面:{tick, take, show, enc_delta, confirm, exit}。
    """

    def __init__(self):
        self.lcd = bus.get_service("lcd")
        if self.lcd is None:
            raise RuntimeError("lcd not on bus — 先跑 boot.py")
        self._bus = getattr(self.lcd, "_bus", None)
        if self._bus is None:
            raise RuntimeError("lcd service missing _bus (adapter)")
        self._dirty = []

        # LVGL 初始化:soft-reboot 殘留時先 deinit。
        # 注意:只在此處做一次;reuse 時不會再走這裡。
        if lv.is_initialized():
            try:
                lv.deinit()
            except Exception:
                pass
        lv.init()
        self._disp = lv.display_create(_W, _H)
        self._disp.set_color_format(18)  # RGB565
        buf = bytearray(_W * _LINES * _BPP)
        self._disp.set_buffers(buf, None, len(buf), 0)  # PARTIAL
        self._disp.set_flush_cb(self._flush_cb)
        # 切橫屏:boot 預設 MADCTL=0x00 直向,LVGL 用 320×240 橫屏座標 → 必須重設
        self._bus.write_cmd_data(0x36, bytes([0x60]))  # MV|MX 橫屏

    # ---- LVGL flush:存髒區,由主迴圈 show ----
    def _flush_cb(self, disp_drv, area, color_p):
        w = area.x2 - area.x1 + 1
        h = area.y2 - area.y1 + 1
        data = color_p.__dereference__(w * h * _BPP)
        lv.draw_sw_rgb565_swap(data, w * h)
        self._dirty.append((area.x1, area.y1, area.x2, area.y2, bytes(data)))
        disp_drv.flush_ready()

    # ---- platform 介面(app.step 用) ----
    def tick(self):
        import time
        time.sleep_us(5000)
        lv.tick_inc(5)
        lv.task_handler()
        lv.refr_now(self._disp)

    def take(self):
        rects = self._dirty
        self._dirty = []
        return rects

    def show(self, x1, y1, x2, y2, data):
        self.lcd.set_window(x1, y1, x2, y2)
        self._bus.write_data_async(data)
        self._bus.flush()

    def enc_delta(self):
        # 預設 0;encoder 由 board 覆寫(本輪不接)
        return 0

    def confirm(self):
        # 預設 False;confirm 由 board 覆寫
        return False

    def exit(self):
        return False


def get_platform():
    """取得 LVGL 平台(bus service "lvgl_disp")。
    已初始化過就 reuse;沒有就建立一次並註冊進 bus。
    對齊 i80_drv.config() / tft_drv 的 lazy-init-once 模式。"""
    existing = bus.get_service(_SERVICE)
    if existing is not None:
        return existing
    plat = LvglDisp()
    bus.register_service(_SERVICE, plat)
    print("[lvgl_init] LVGL display ready ({}x{} madctl=0x60 PARTIAL lines={})".format(
        _W, _H, _LINES))
    return plat


def is_ready():
    """LVGL 是否已初始化並在 bus 上。"""
    return bus.get_service(_SERVICE) is not None
