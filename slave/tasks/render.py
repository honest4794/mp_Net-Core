import time
from lib.sys.task import Task
from lib.sys.sys_bus import bus
from lib.sys.log_service import get_log

class RenderTask(Task):
    def __init__(self, name, ctx):
        super().__init__(name, ctx)
        self.st_pixel = ctx['st_pixel']
        self.frame_interval_ms = 20   # 幀間隔（ms），直接控制；config: System.frame_interval_ms
        self.stream_fps = 0           # 0x3001 收到的原始 fps（只存不換算，變化時才換算一次）
        self.hub = None

        self._played_frames = 0
        self.interval_us = 0
        self.next_tick_us = 0

    @staticmethod
    def _resolve_interval_ms(sys_cfg):
        """幀間隔（ms）：直接讀儲存的 System.frame_interval_ms（原始數字，不換算）。"""
        iv = sys_cfg.get("frame_interval_ms")
        if iv:
            return int(iv)
        return 20

    def on_start(self):
        super().on_start()

        while self.hub is None:
            self.hub = bus.get_service("pixel_stream")
            if self.hub is None:
                time.sleep_ms(5)

        bus.register_provider("played_frames", lambda: self._played_frames)   # 已播放幀號（每 show_all 一次 +1）

        bus_sys = bus.shared.get("System", {})
        self.frame_interval_ms = self._resolve_interval_ms(bus_sys)
        self.interval_us = self.frame_interval_ms * 1000
        self.next_tick_us = time.ticks_us()

        get_log().info("🔥 [RenderTask] Engine Online | {} ms/幀".format(self.frame_interval_ms))

    def loop(self):
        if not self.running: return

        # 🔧 0x3001 主動同步：slave 只存原始 fps（stream_actions），此處變化時才換算一次節拍
        fps_ov = bus.shared.get("stream_fps_override")
        if fps_ov and fps_ov != self.stream_fps:
            self.stream_fps = int(fps_ov)
            self.interval_us = (1000 // self.stream_fps) * 1000   # 只在此時算，熱路徑不碰
            get_log().info("🔥 [RenderTask] stream fps override -> {} fps".format(self.stream_fps))

        # MODE_SET / MODE_STOP 是跨 Slave 同步邊界，不能用 500ms fcache；
        # 否則兩塊板會按各自 cache 到期相位相差一個或以上 render frame。
        is_streaming = bus.shared.get("is_streaming", False)
        if not is_streaming:
            is_ready = bus.shared.get("is_ready", False)
            if is_ready == False:
                # 停止/熄燈：填中性值（燈=0 熄滅，motor=0x80 死區停），
                # 不能全清 0 —— UART-412 的 0 = 全速正轉！
                self.st_pixel.clear_all()

            if time.ticks_diff(time.ticks_us(), self.next_tick_us) < 0:
                return

            self.next_tick_us = time.ticks_add(time.ticks_us(), 100000)
            self._played_frames = 0
            return

        is_paused = bus.shared.get("is_paused", False)
        if is_paused:
            if time.ticks_diff(time.ticks_us(), self.next_tick_us) < 0:
                return
            self.next_tick_us = time.ticks_add(time.ticks_us(), 50000)
            self._played_frames = 0
            return

        now = time.ticks_us()
        if time.ticks_diff(now, self.next_tick_us) > 200000:
             self.next_tick_us = now

        if time.ticks_diff(now, self.next_tick_us) >= 0:
            if self.hub.read_into(self.st_pixel.big_buffer):
                self.st_pixel.show_all()
                self._played_frames += 1
                self.success += 1

            # 用 ticks_add 推進節拍（會 wrap），不能用 `+=`：
            # `+=` 會讓 next_tick_us 變成不 wrap 的普通整數，而 now=ticks_us() 會 wrap，
            # 兩者相位錯開後 ticks_diff 永遠為負 → RenderTask 靜默停止取幀（燈停、無 log）。
            self.next_tick_us = time.ticks_add(self.next_tick_us, self.interval_us)
        else:
            return

    def on_stop(self):
        super().on_stop()
        get_log().info("RenderTask Stopped")
