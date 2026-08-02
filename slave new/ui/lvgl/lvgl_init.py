# ui/lvgl/lvgl_init.py — LVGL display 一次初始化 + bus reuse
#
# 對齊 driver/i80_drv.py、driver/tft_drv.py 的 lazy-init-once 模式:
#   get_platform() 開頭先 bus.get_service("lvgl_disp");已存在就直接 return。
#
# 為什麼這樣做:
#   - soft-reboot 後 LVGL C 層狀態殘留,重複 deinit/init 再 display_create
#     會解到 garbage(MemoryError 要求配置數百 MB)→ LVGL 只能初始化一次。
#   - LVGL display + draw buffer 只該配一次,放 bus 後 reuse,避免記憶體碎片。
#
# 螢幕方向(完全對齊 mp_LVGL/ui/lvgl_shared.py 參考版的做法):
#   - LVGL 自己送 MADCTL(0x60 橫屏 / 0x00 直屏),讓 ST7789 framebuffer 旋轉。
#   - LVGL 用旋轉後尺寸(橫屏 320×240)。
#   - show 用 bus adapter 的 set_window(繞過 ST7789.set_window 的 x/y swap),
#     因為 MADCTL 0x60 已讓 framebuffer 本身是橫屏,座標直接送即可。
#   - 重要:config TFT.rotation 必須維持 0(driver 不送 MADCTL、不 swap),
#     否則會跟 LVGL 送的 MADCTL double-rotate。
import lvgl as lv
from lib.sys_bus import bus

_LINES = 40    # PARTIAL draw buffer 行數
_BPP = 2       # RGB565
_SERVICE = "lvgl_disp"
_MADCTL = 0x60  # 橫屏 MV|MX(ST7789);改 0x00 為直屏

_W = 320
_H = 240


class LvglDisp:
    """LVGL display + slave new LCD 平台。構造一次後放 bus reuse。
    提供 app 要的 platform 介面:{tick, take, show, enc_delta, confirm, exit}。"""

    def __init__(self):
        self.lcd = bus.get_service("lcd")
        if self.lcd is None:
            raise RuntimeError("lcd not on bus — 先跑 boot.py")
        self._bus = getattr(self.lcd, "_bus", None)
        if self._bus is None:
            raise RuntimeError("lcd service missing _bus (adapter)")

        self.W = _W
        self.H = _H
        self._dirty = []

        # 送 MADCTL(讓 framebuffer 橫屏)。bus adapter 的 write_cmd_data 直接達 ST7789。
        self._bus.write_cmd_data(0x36, bytes([_MADCTL]))

        # LVGL 初始化:soft-reboot 殘留時先 deinit。只在此做一次;reuse 不再走這裡。
        if lv.is_initialized():
            try:
                lv.deinit()
            except Exception:
                pass
        lv.init()
        self._disp = lv.display_create(self.W, self.H)
        self._disp.set_color_format(18)  # RGB565
        buf = bytearray(self.W * _LINES * _BPP)
        self._disp.set_buffers(buf, None, len(buf), 0)  # PARTIAL
        self._disp.set_flush_cb(self._flush_cb)
        print("[lvgl_init] {}x{} MADCTL=0x{:02X} PARTIAL lines={}".format(
            self.W, self.H, _MADCTL, _LINES))

    def _flush_cb(self, disp_drv, area, color_p):
        """LVGL 渲染一塊 → 拷貝到 bytes(PARTIAL 單緩衝必須拷貝)+ 立即 flush_ready。"""
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
        # 直接用 bus adapter 的 set_window(繞過 ST7789.set_window 的 swap)。
        # MADCTL 0x60 已讓 framebuffer 橫屏,LVGL 座標直接送。
        self._bus.set_window(x1, y1, x2, y2)
        self._bus.write_data_async(data)
        self._bus.flush()

    def enc_delta(self):
        return 0   # 預設;encoder 由 board 覆寫

    def confirm(self):
        return False   # 預設;confirm 由 board 覆寫

    def exit(self):
        return False


def get_platform():
    """取得 LVGL 平台(bus service "lvgl_disp")。
    已初始化過就 reuse;沒有就建立一次並註冊進 bus。"""
    existing = bus.get_service(_SERVICE)
    if existing is not None:
        return existing
    plat = LvglDisp()
    bus.register_service(_SERVICE, plat)
    return plat


def is_ready():
    """LVGL 是否已初始化並在 bus 上。"""
    return bus.get_service(_SERVICE) is not None
