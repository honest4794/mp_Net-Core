from machine import Pin, I2C, SPI
import neopixel
import micropython
import gc
import utime
import math
import array

# ==================== PixelController ====================
class PixelController:
    """
    精簡版 pixel 控制器 - 專為高性能流式傳輸設計
    移除多餘 buffer，直接將數據從 Source 轉換至 Hardware Buffer
    """
    def __init__(self, pixel_type, pixel_io_cfg):
        self.pixel_type = pixel_type
        self.pixel_io = pixel_io_cfg
        self.hw = pixel_io_cfg['pixel_IO']
        self.num_pixels = pixel_io_cfg['Q']

        # 停止/熄燈時填回的中性值（對齊舊專案 mp_LEDController 的 reset 語義）：
        # config 的 dStay（default Stay）是 12-bit（0-4095，舊 dArc 位深），
        # big_buffer 通道是 8-bit → >>4。燈 = 0（熄滅）；motor（UartMotor）預設 2048。
        dstay = int(pixel_io_cfg.get("dStay", 0))
        self.neutral_value = (dstay >> 4) & 0xFF

        # 內部映射: 1:WS2812, 2:APA102, 3:i2c_pixel
        type_map = {'WS2812': 1, 'APA102': 2, 'i2c_pixel': 3}
        self._tid = type_map.get(pixel_type, 0)
        
        # 色序與通道處理
        order = pixel_io_cfg.get('order', 'GRB').upper()
        self.bpp = len(order)
        self._r = order.find('R')
        self._g = order.find('G')
        self._b = order.find('B')
        self._w = order.find('W')
        
        # 單幀大小 (輸入源統一定義為 R,G,B,W 每像素 4 bytes)
        self.frame_size = self.num_pixels * 4 



    @micropython.native
    def st_load_and_convert(self, source_buffer, offset: int):
        """核心載入函數：調用 Viper 機器碼加速轉換"""
        if self.hw is None:
            return
        # 直接獲取硬體驅動的 Buffer 引用（Neopixel 存放在 .buf，其他自定義驅動通常也是）
        # 如果是 PCA9685/i2c 類型的，我們假設它有自定義 buf
        self._convert(source_buffer, offset, self.num_pixels, self._tid)

    @micropython.viper
    def _convert(self, source, offset: int, n: int, tid: int):
        src = ptr8(source)
        
        bpp = int(self.bpp)
        
        if tid == 1:  # WS2812 (RGB/GRB)
            dst = self.hw.buf
            ro = int(self._r)
            go = int(self._g)
            bo = int(self._b)
            wo = int(self._w)
            for i in range(n):
                s_idx = offset + (i << 2) # i * 4
                d_idx = i * bpp
                dst[d_idx + ro] = src[s_idx]     # R
                dst[d_idx + go] = src[s_idx + 1] # G
                dst[d_idx + bo] = src[s_idx + 2] # B
                
        elif tid == 2: # APA102 — 與 lib/hw/apa102.py 的 _convert 一致 (header 在前) + 雙緩衝
            # 🔧 雙緩衝: DMA 可能還在傳上一個 buffer, flip 切到另一個再寫,
            #    確保不覆寫正在傳輸的緩衝 (lcd_bus write 是非同步 DMA → 撕裂)
            hw = self.hw
            if hasattr(hw, 'flip'):
                hw.flip()
            dst = self.hw.spi_buffer
            ro = int(self._r)
            go = int(self._g)
            bo = int(self._b)
            wo = int(self._w)
            for i in range(n):
                s_idx = offset + (i << 2)
                d_idx = 4 + (i << 2)
                # ⚠️ APA102 規格: 每顆 4 bytes = [0xE0|亮度][B][G][R], 亮度頭部在前。
                # 頭部若放最後, APA102 會把「B 色值」當亮度頭部 — RGB 轉換時
                # B 從 0↔255, 亮度跟著暴變 → 轉色瞬間整條閃。header 在前才正確。
                dst[d_idx]     = 0xE0 | (src[s_idx + wo] >> 3)   # 亮度頭部 (5-bit)
                dst[d_idx + 1] = src[s_idx + bo]     # B
                dst[d_idx + 2] = src[s_idx + go]     # G
                dst[d_idx + 3] = src[s_idx + ro]     # R

        elif tid == 3: # i2c_pixel (PCA9685)
            # 專門提取 W 通道 (src[+3]) 給 PWM 控制器
            dst = self.hw.buf
            ro = int(self._r)
            go = int(self._g)
            bo = int(self._b)
            wo = int(self._w)
            for i in range(n):
                s_idx = offset + (i << 2)
                w = src[s_idx + 3]
                dst[i] = (w << 4) | (w >> 4)

    def st_show(self):
        """觸發硬體顯示"""
        t = self._tid
        if t == 1: self.hw.write()
        elif t == 2: self.hw.show_raw() if hasattr(self.hw, 'show_raw') else self.hw.show()
        elif t == 3: self.hw.show() if hasattr(self.hw, 'show') else self.hw.sync_buffer()

    def __len__(self):
        return self.num_pixels

# ==================== PixelStreamer ====================
class PixelStreamer:
    """
    pixel 流式傳輸管理器 - 零拷貝高性能版
    """
    def __init__(self, controllers):
        self.controllers = controllers
        self.total_bytes = sum(c.frame_size for c in controllers)
        self.big_buffer = bytearray(self.total_bytes)
        self.offsets = []
        
        # 預計算偏移量，減少循環中的算力支出
        current_offset = 0
        for c in controllers:
            self.offsets.append(current_offset)
            current_offset += c.frame_size

    def init(self):
        for c in self.controllers:
            c.st_init()
        print(f"[Streamer] Ready. Total Buffer: {self.total_bytes} bytes")

    def clear_all(self):
        """停止/熄燈：把每個 controller 的區域填回中性值。

        對齊舊專案 mp_LEDController 的 dArc 概念（reset 回到中性值）：
          - 燈（PixelController）    : RGBW 全 0（熄滅）
          - motor（UartMotor）       : W = 0x80（死區停，0 會是全速正轉！）
        每個 controller 用各自的 neutral_value（預設 0）。
        """
        buf = self.big_buffer
        for i, c in enumerate(self.controllers):
            neutral = getattr(c, "neutral_value", 0)
            off = self.offsets[i]
            for k in range(c.num_pixels):
                o = off + (k << 2)
                buf[o]     = 0
                buf[o + 1] = 0
                buf[o + 2] = 0
                buf[o + 3] = neutral
        self.show_all()

    def get_write_view(self):
        """獲取原始緩衝供外部填充數據"""
        return self.big_buffer

    @micropython.native
    def show_all(self):
        """執行一幀完整的渲染流程"""
        buf = self.big_buffer
        offs = self.offsets
        for i in range(len(self.controllers)):
            ctrl = self.controllers[i]
            # 1. 搬運與轉換
            ctrl.st_load_and_convert(buf, offs[i])
            
            # 2. 硬體輸出
            ctrl.st_show()
            
    def close(self):
        for c in self.controllers:
            c.is_active = False
        gc.collect()

# ==================== 測試腳本 ====================
if __name__ == '__main__':
    # 1. 模擬硬體初始化
    # WS2812 組 (假設 10 顆燈)
    np_io = neopixel.NeoPixel(Pin(15, Pin.OUT), 10)
    ctrl_ws = PixelController('WS2812', {'pixel_IO': np_io, 'Q': 10, 'order': 'GRB'})

    # 模擬 PCA9685 (這裡使用一個假的物件來模擬，實際使用時傳入 PCA 物件)
    class FakePCA:
        def __init__(self): self.buf = bytearray(16)
        def show(self): pass 
            
    pca_io = FakePCA()
    ctrl_pca = PixelController('i2c_pixel', {'pixel_IO': pca_io, 'Q': 16, 'order': 'W'})

    # 2. 啟動 Streamer
    streamer = PixelStreamer([ctrl_ws, ctrl_pca])
    streamer.init()

    # 3. 測試循環
    print("🚀 開始測試高性能流式循環...")
    source = streamer.get_write_view()
    angle = 0.0
    
    try:
        for frame in range(200):
            # 模擬產生算法數據 (R,G,B,W 順序)
            for i in range(len(streamer.big_buffer) // 4):
                idx = i * 4
                s = (math.sin(angle + i * 0.2) + 1) * 127
                source[idx]     = int(s)          # R
                source[idx + 1] = 0               # G
                source[idx + 2] = 255 - int(s)    # B
                source[idx + 3] = int(s)          # W (供 PCA 使用)
            
            # 使用高性能接口渲染
            streamer.show_all()
            
            angle += 0.1
            if frame % 50 == 0:
                print(f"Frame {frame} | Free Mem: {gc.mem_free()} bytes")
            utime.sleep_ms(10)
            
    except KeyboardInterrupt:
        pass

    streamer.close()
    print("🏁 測試結束")
