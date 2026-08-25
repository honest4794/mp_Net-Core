import machine
import micropython
import array
import time

# ── 極簡 SPI 寫入封裝 ─────────────────────────────────────────
# APA102 只需要「把一整塊 buffer 送出去」這個動作, 但底層 SPI 有兩種:
#   • lcd_bus.SPIBus  — write() 非同步 DMA (fire-and-forget), 必須 wait_all()
#                       等 DMA 完才能改緩衝區, 否則下一幀覆寫 → 撕裂。
#   • machine.SPI    — write() 同步 (阻塞到傳完), 無 wait_all。
# 這裡獨立寫一個小 class 吸收差異, 不依賴 lib.sys.bus_adapter
# (那是 TFT 用的複雜環境; APA102 只需要 write + wait_all)。
class _SpiWriter:
    def __init__(self, spi):
        self._spi = spi
        self._wait_all = getattr(spi, "wait_all", None)

    def write(self, data):
        # async bus: 寫前先等前一筆 DMA 清空, 寫完等 DMA 完成
        if self._wait_all is not None:
            try:
                self._wait_all()
            except Exception:
                pass
        self._spi.write(data)
        if self._wait_all is not None:
            try:
                self._wait_all()
            except Exception:
                pass


class APA102:
    """
    APA102 極速驅動 - 專為 PixelController 配套設計
    特性：雙緩衝(ping-pong)、Viper 轉換、對齊 PixelController 的 buf 操作

    雙緩衝: lcd_bus SPI write() 是非同步 DMA。若 DMA 傳 A 時下一幀覆寫 A,
    會撕裂/掃描 (轉色時最明顯)。用兩個 spi_buffer A/B 交錯:
      - _convert() 寫「目前寫入 buffer」, show_raw() 送同一個,
      - 之後 flip() 切到另一個 buffer, 下一幀寫另一個。
      DMA 傳 A 時寫 B, 永遠不覆寫正在傳的 buffer。
    """
    def __init__(self, spi, num_pixels,  baudrate=8_000_000):
        self.n = num_pixels
        self.buf_length = num_pixels * 4
        
        # 1. 暴露給 PixelController 的標準緩衝區 [G, R, B, W]
        # 注意：為了符合你 PixelController 的 set_rgb 邏輯與 f.readinto 的性能
        self.buf = bytearray(self.buf_length)
        
        # 2. SPI 物理傳輸數據區 (原生 APA102 格式) — 雙緩衝 A/B
        # 整合 Start + Data + End 為單一緩衝區以避免 SPI 分段寫入造成的時序問題
        self.start_len = 4
        self.end_len = max(4, (num_pixels + 15) // 16)
        self.spi_total_len = self.start_len + self.buf_length + self.end_len
        self._spi_bufs = [
            bytearray(self.spi_total_len),
            bytearray(self.spi_total_len),
        ]
        self._active = 0      # 目前「寫入 + 送出的 buffer」index
        self.spi_buffer = self._spi_bufs[0]   # 向後相容: 預設指向 A
        
        # 3. SPI 硬體初始化 — 統一包成 _SpiWriter (async lcd_bus → write+wait_all;
        #    sync machine.SPI → 直接寫), 硬體層不需知道底層是 DMA 還是同步。
        self.spi = _SpiWriter(spi)
        
        # 初始化 SPI 緩衝區 (Start=0x00, End=0xFF, Data Header=0xE0)
        self._init_spi_buffer()
        self._init_spi_buffer(1)

    @micropython.viper
    def _init_spi_buffer(self, idx: int = 0):
        """初始化物理緩衝區 (index idx 的 buffer)：Start(0x00) + Data(0xE0) + End(0xFF)"""
        p_spi: ptr8 = ptr8(self._spi_bufs[idx])
        buf_len: int = int(self.buf_length)
        start_len: int = int(self.start_len)
        end_len: int = int(self.end_len)
        
        # 1. Start Frame (0x00)
        for i in range(start_len):
            p_spi[i] = 0x00
            
        # 2. Data Frame Headers (0xE0)
        # Data starts at offset start_len
        for i in range(0, buf_len, 4):
            p_spi[start_len + i] = 0xE0
            
        # 3. End Frame (0x00)
        # End starts at start_len + buf_len
        # 修正：使用 0x00 替代 0xFF，避免下一顆未使用的燈珠將其誤判為全亮信號 (Phantom White Pixel)
        end_start: int = start_len + buf_len
        for i in range(end_len):
            p_spi[end_start + i] = 0x00

    def flip(self):
        """切換到另一個 spi_buffer (ping-pong)。

        呼叫時機: show_raw() 送出「目前 buffer」後, 下一幀要寫入前。
        PixelController 的 _convert 會先呼叫 flip() 再寫「新 buffer」,
        確保 DMA 傳 A 時寫 B, 不覆寫正在傳輸的緩衝。
        """
        self._active = 1 - self._active
        self.spi_buffer = self._spi_bufs[self._active]

    @micropython.viper
    def _convert(self):
        """
        Viper 內核：將 PixelController 寫入的 [G, R, B, W] 轉換為 [0xE0|W, B, G, R]
        寫入到目前 active 的 spi_buffer 的中間數據區
        直接由 show() 調用
        """
        p_in: ptr8 = ptr8(self.buf)
        p_out: ptr8 = ptr8(self.spi_buffer)
        n: int = int(self.buf_length)
        offset: int = int(self.start_len) # Offset for data in spi_buffer
        
        for i in range(0, n, 4):
            # 讀取 PixelController 規範的四字節 (假設最後一字節為亮度)
            g = p_in[i]
            r = p_in[i+1]
            b = p_in[i+2]
            w = p_in[i+3]
            
            # 寫入 APA102 格式 (亮度位 0xE0 + 5-bit)
            p_out[offset + i]     = 0xE0 | (w >> 3) 
            p_out[offset + i + 1] = b
            p_out[offset + i + 2] = g
            p_out[offset + i + 3] = r

    def show_raw(self):
        """
        🚀 快車道：直接輸出目前 active 的 spi_buffer
        前提：該 buffer 已由 _convert 填好
        spi 是 _SpiWriter: async lcd_bus 會先等前一筆 DMA 清空再寫、寫完等
        DMA 完成; machine.SPI 直接寫。雙緩衝確保不會覆寫正在傳的 buffer。
        """
        self.spi.write(self.spi_buffer)
            
    def show(self):
        """物理輸出"""
        self._convert()
        self.show_raw()
        
    def write(self):
        """相容 PixelController 的調用習慣"""
        self.show_raw()

    def fill(self, color):
        """相容 neopixel 接口"""
        g, r, b = color # 預設三元組
        for i in range(0, self.buf_length, 4):
            self.buf[i] = g
            self.buf[i+1] = r
            self.buf[i+2] = b
            self.buf[i+3] = 255 # 預設滿亮度

