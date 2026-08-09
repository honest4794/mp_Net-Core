# test/lvgl_cpu1_isolated_test.py — LVGL 完全獨立 @ CPU1 測試
#
# 核心原則:CPU1 只接觸 TFT + 輸入硬體,不碰任何 CPU0 共享的 Python 狀態。
#
# CPU1 取得硬體的方式:
#   bus.get_service("lcd")       → 拿 lcd 物件指標(讀 service dict 一次,拿完不再碰)
#   bus.get_service("enc_list")  → 拿 encoder 物件指標(同上)
#   bus.get_service("pin_by_label") → 拿 Pin 物件指標(同上)
#   之後所有操作都在 CPU1 的本地變數上,不再 get_service、不碰 bus.shared。
#
# CPU1 不碰的東西:
#   ❌ bus.shared["_hw_inputs"]   ← CPU0 採樣寫的 dict(改自己直接讀 encoder/pin)
#   ❌ bus.register_service       ← 不寫進 service dict
#   ❌ hw_manager.get_input/sample_inputs
#   ❌ board._make_inputs / board.run
#
# 唯一共享:硬體本身(SPI controller/GPIO/LCD panel)——物理共享無法避免,
# 但 SPI host 已由 boot.py 初始化,CPU1 只透過取得的 spi 物件指標操作,不再建 SPIBus。
#
# 用法(soft reboot 後,boot.py 已跑完,確保 LVGL task 沒跑):
#   import lvgl_cpu1_isolated_test
#   lvgl_cpu1_isolated_test.start()

import _thread, time, gc
import lvgl as lv
from lib.sys_bus import bus

_W = 320
_H = 240
_BPP = 2
_MADCTL = 0x60
_LINES = 40


class IsolatedLvgl:
    """CPU1 獨立 LVGL。__init__ 取硬體指標後,之後完全不碰 bus。"""

    def __init__(self):
        # ── 取硬體物件指標(只讀 service dict 這一次)──
        self.lcd = bus.get_service("lcd")
        if self.lcd is None:
            raise RuntimeError("lcd not on bus")
        self._bus = getattr(self.lcd, "_bus", None)
        if self._bus is None:
            raise RuntimeError("lcd missing _bus")

        enc_list = bus.get_service("enc_list") or []
        self._enc = enc_list[0] if enc_list else None
        self._enc_last = self._enc.value() if self._enc else 0

        pin_by_label = bus.get_service("pin_by_label") or {}
        self._confirm_pin = pin_by_label.get("encC")
        self._exit_pin = pin_by_label.get("btn")
        self._c_last = self._confirm_pin.value() if self._confirm_pin else 1
        self._e_last = self._exit_pin.value() if self._exit_pin else 1

        print("[iso] hw: lcd=ok enc={} encC={} btn={}".format(
            "ok" if self._enc else "none",
            "ok" if self._confirm_pin else "none",
            "ok" if self._exit_pin else "none"))

        self._dirty = []
        self._frame = 0

        # ── MADCTL(橫屏)──
        self._bus.write_cmd_data(0x36, bytes([_MADCTL]))

        # ── LVGL 首次初始化(boot 沒碰過 LVGL,不需 deinit)──
        lv.init()
        self._disp = lv.display_create(_W, _H)
        self._disp.set_color_format(18)  # RGB565
        buf = bytearray(_W * _LINES * _BPP)
        self._disp.set_buffers(buf, None, len(buf), 0)  # PARTIAL
        self._disp.set_flush_cb(self._flush_cb)
        print("[iso] {}x{} PARTIAL fb={}KB".format(_W, _H, len(buf) // 1024))

    def _flush_cb(self, disp_drv, area, color_p):
        w = area.x2 - area.x1 + 1
        h = area.y2 - area.y1 + 1
        data = color_p.__dereference__(w * h * _BPP)
        lv.draw_sw_rgb565_swap(data, w * h)
        self._dirty.append((area.x1, area.y1, area.x2, area.y2, bytes(data)))
        disp_drv.flush_ready()

    # ── 輸入:直接讀硬體(不過 bus.shared)──
    def enc_delta(self):
        if self._enc is None:
            return 0
        v = self._enc.value()
        d = v - self._enc_last
        self._enc_last = v
        return d

    def confirm(self):
        if self._confirm_pin is None:
            return False
        v = self._confirm_pin.value()
        edge = (self._c_last == 1 and v == 0)
        self._c_last = v
        return edge

    def exit_pressed(self):
        if self._exit_pin is None:
            return False
        v = self._exit_pin.value()
        edge = (self._e_last == 1 and v == 0)
        self._e_last = v
        return edge

    def step(self):
        self._frame += 1
        lv.tick_inc(5)
        lv.task_handler()
        lv.refr_now(self._disp)
        while self._dirty:
            x1, y1, x2, y2, data = self._dirty.pop(0)
            self._bus.set_window(x1, y1, x2, y2)
            self._bus.write_data_async(data)
            self._bus.flush()


# ══════════════════════════════════════════════════════
# UI + CPU1 主迴圈
# ══════════════════════════════════════════════════════

def _cpu1_main():
    """CPU1 完全獨立主迴圈。"""
    try:
        disp = IsolatedLvgl()

        # 簡單 UI
        scr = lv.obj(None)
        scr.set_style_bg_color(lv.color_hex(0x1A2B3C), 0)
        title = lv.label(scr)
        title.set_text("CPU1 Isolated LVGL")
        title.set_style_text_color(lv.color_hex(0x4FC3F7), 0)
        info = lv.label(scr)
        info.set_text("enc:0  ok:0  exit:0\nframe:0")
        info.set_style_text_color(lv.color_hex(0xFFFFFF), 0)
        try:
            title.set_pos(50, 30)
            info.set_pos(50, 80)
        except Exception:
            pass
        lv.screen_load(scr)
        print("[iso] UI built")

        time.sleep_ms(300)
        print("[iso] ⚡ loop started")

        enc_t = 0
        ok_c = 0
        ex_c = 0
        t0 = time.ticks_ms()

        while True:
            d = disp.enc_delta()
            if d:
                enc_t += d
            if disp.confirm():
                ok_c += 1
            if disp.exit_pressed():
                ex_c += 1

            if disp._frame % 5 == 0:
                info.set_text("enc:{}  ok:{}  exit:{}\nframe:{}".format(
                    enc_t, ok_c, ex_c, disp._frame))

            disp.step()
            time.sleep_ms(5)

            if disp._frame % 200 == 0:
                dt = time.ticks_diff(time.ticks_ms(), t0)
                fps = disp._frame * 1000 // dt if dt > 0 else 0
                print("[iso] frame={} fps={} free={}KB".format(
                    disp._frame, fps, gc.mem_free() // 1024))

    except Exception as e:
        print("[iso] ❌ CPU1 error: {}".format(e))


def start():
    print("=" * 55)
    print("[iso] LVGL 完全獨立 @ CPU1")
    print("[iso] 只 get_service 取硬體指標,之後不碰 bus.shared")
    print("=" * 55)

    if not bus.has_lcd():
        print("[iso] ❌ no LCD")
        return

    gc.collect()
    print("[iso] free mem: {} KB".format(gc.mem_free() // 1024))
    _thread.start_new_thread(_cpu1_main, ())
    print("[iso] ✅ dispatched to CPU1 — 觀察螢幕 + 旋鈕/按鈕")


if __name__ == "__main__":
    start()
