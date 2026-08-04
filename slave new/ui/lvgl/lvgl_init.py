# ui/lvgl/lvgl_init.py — LVGL display 一次初始化 + bus reuse
#
# DIRECT mode — LVGL 直接渲染進 framebuffer(C 層),flush_cb 只記 dirty area。
# show() 從自己保留的 framebuffer 切 dirty region 送 SPI(純 Python→C)。
#
# 為什麼用 DIRECT(不用 PARTIAL):
#   PARTIAL 的 flush_cb 在 C→Python callback 裡做 __dereference__ + bytes() 拷貝,
#   在 _thread + 雙核心環境下不穩定(CPU1 跑完整 UI 時崩潰)。
#   DIRECT 的 flush_cb 只記座標(輕量),SPI 操作在 callback 外做 → 跨核穩定。
#   代價:整個螢幕 framebuffer(320×240×2 = 150KB,PSRAM 配置)。
#   (參考 lvgl-micropython 專案:MicroPython Python 層預設只用一核,
#    CPU1 的工作在 C 層做。DIRECT mode 讓 Python callback 最小化。)
#
# 對齊 driver/i80_drv.py、driver/tft_drv.py 的 lazy-init-once 模式:
#   get_platform() 開頭先 bus.get_service("lvgl_disp");已存在就直接 return。
#
# 螢幕方向:
#   - LVGL 自己送 MADCTL(0x60 橫屏),讓 ST7789 framebuffer 旋轉。
#   - show 用 bus adapter 的 set_window(繞過 ST7789.set_window 的 x/y swap)。
#   - 重要:config TFT.rotation 必須維持 0,否則 double-rotate。
import lvgl as lv
from lib.sys_bus import bus

_BPP = 2              # RGB565
_SERVICE = "lvgl_disp"
_MADCTL = 0x60        # 橫屏 MV|MX(ST7789);改 0x00 為直屏
_RENDER_MODE_DIRECT = 1   # LVGL enum: PARTIAL=0, DIRECT=1, FULL=2

_W = 320
_H = 240


class LvglDisp:
    """LVGL display + slave new LCD 平台(DIRECT mode)。構造一次後放 bus reuse。
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

        # ── DIRECT mode:整個螢幕 framebuffer(PSRAM 優先)──
        # LVGL C 層直接渲染進這個 buffer;flush_cb 只記 dirty area。
        # show() 從這個 buffer 切 dirty region 送 SPI(在 callback 外,純 Python→C)。
        self._fb = self._alloc_fb(self.W * self.H * _BPP)
        self._disp.set_buffers(self._fb, None, len(self._fb), _RENDER_MODE_DIRECT)
        self._disp.set_flush_cb(self._flush_cb)
        print("[lvgl_init] {}x{} MADCTL=0x{:02X} DIRECT fb={}KB".format(
            self.W, self.H, _MADCTL, len(self._fb) // 1024))

    def _alloc_fb(self, size):
        """PSRAM 優先,否則 heap bytearray。"""
        try:
            import heap_caps
            buf = heap_caps.malloc(size, heap_caps.CAP_SPIRAM)
            if buf is not None:
                return buf
        except Exception:
            pass
        return bytearray(size)

    def _flush_cb(self, disp_drv, area, color_p):
        """DIRECT mode flush_cb:只記 dirty area + flush_ready。
        不做 __dereference__/swap/SPI — 消除 callback 內的重量操作(跨核穩定)。
        實際像素在 framebuffer 裡(C 層已渲染),show() 從 fb 切。"""
        self._dirty.append((area.x1, area.y1, area.x2, area.y2))
        disp_drv.flush_ready()

    # ---- platform 介面(app.step 用) ----
    def tick(self):
        lv.tick_inc(5)
        lv.task_handler()
        lv.refr_now(self._disp)

    def take(self):
        rects = self._dirty
        self._dirty = []
        return rects

    def show(self, x1, y1, x2, y2):
        """從 framebuffer 切 dirty region 送 SPI(純 Python→C,跟 JPEG player 同構)。
        DIRTY region 在 fb 裡按行排列;整行連續一次送,否則逐行切。"""
        w = x2 - x1 + 1
        h = y2 - y1 + 1
        off = (y1 * self.W + x1) * _BPP
        stride = self.W * _BPP
        self._bus.set_window(x1, y1, x2, y2)
        if w == self.W:
            # 整行連續,一次送
            chunk = memoryview(self._fb)[off:off + w * h * _BPP]
            self._bus.write_data_async(chunk)
        else:
            # 逐行切(每行 offset = off + row * stride)
            row_len = w * _BPP
            for row in range(h):
                row_off = off + row * stride
                self._bus.write_data_async(memoryview(self._fb)[row_off:row_off + row_len])
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
