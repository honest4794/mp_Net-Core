import array
import micropython
import time
import gc

# ============================================================
# 完整優化版 RGB ↔ HSV 雙向轉換測試套件
# ============================================================

class RGBHSVOptimizedBenchmark:
    """RGB ↔ HSV 雙向轉換完整測試 - 優化版 vs 原版對比"""
    
    def __init__(self):
        self.results = {}
    
    # ============================================================
    # 原版函數 (基準版本)
    # ============================================================
    @micropython.viper
    def hsv2rgb_baseline(self, h: int, s: int, v: int, buf: ptr8):
        """HSV轉RGB - 基準版"""
        if s > 4095:
            s = 4095
        
        if s == 0:
            lum = v >> 4
            buf[0] = lum
            buf[1] = lum
            buf[2] = lum
            return
            
        h = h % 360
        region = h // 60
        remainder = (h - (region * 60)) * 4095 // 60
        
        p = (v * (4095 - s)) >> 12
        q = (v * (4095 - ((s * remainder) >> 12))) >> 12
        t = (v * (4095 - ((s * (4095 - remainder)) >> 12))) >> 12
        
        v = v >> 4
        p = p >> 4
        q = q >> 4
        t = t >> 4
        
        if region == 0:
            r, g, b = v, t, p
        elif region == 1:
            r, g, b = q, v, p
        elif region == 2:
            r, g, b = p, v, t
        elif region == 3:
            r, g, b = p, q, v
        elif region == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q
            
        buf[0] = int(g)
        buf[1] = int(r)
        buf[2] = int(b)
    
    @micropython.viper
    def rgb2hsv_baseline(self, buf: ptr8, hsv_out: ptr16):
        """RGB轉HSV - 基準版"""
        r = int(buf[1])
        g = int(buf[0])
        b = int(buf[2])
        
        max_val = r if r > g else g
        max_val = max_val if max_val > b else b
        min_val = r if r < g else g
        min_val = min_val if min_val < b else b
        
        delta = int(max_val - min_val)
        v = (int(max_val) << 4) | (int(max_val) >> 4)
        
        if delta == 0 or max_val == 0:
            hsv_out[0] = 0
            hsv_out[1] = 0
            hsv_out[2] = v
            return
        
        s = (delta << 12) // max_val
        if s > 4095:
            s = 4095
        
        h = 0
        if max_val == r:
            h = (60 * (int(g) - int(b))) // delta
            if h < 0:
                h += 360
        elif max_val == g:
            h = (60 * (int(b) - int(r))) // delta + 120
        else:
            h = (60 * (int(r) - int(g))) // delta + 240
        
        if h >= 360:
            h -= 360
        
        hsv_out[0] = h
        hsv_out[1] = s
        hsv_out[2] = v
    
    # ============================================================
    # 優化版函數 (高精度版本)
    # ============================================================
    @micropython.viper
    def hsv2rgb_optimized(self, h: int, s: int, v: int, buf: ptr8):
        """HSV轉RGB - 優化版"""
        if s > 4095:
            s = 4095
        if v > 4095:
            v = 4095
        
        if s == 0:
            # 優化: 精確轉換 (四捨五入)
            lum = (v * 255 + 2047) // 4095
            if lum > 255:
                lum = 255
            buf[0] = lum
            buf[1] = lum
            buf[2] = lum
            return
        
        h = h % 360
        region = h // 60
        remainder = (h - (region * 60)) * 4095 // 60
        
        p = (v * (4095 - s)) >> 12
        q = (v * (4095 - ((s * remainder) >> 12))) >> 12
        t = (v * (4095 - ((s * (4095 - remainder)) >> 12))) >> 12
        
        # 優化: 四捨五入轉8位
        v_8 = (v * 255 + 2047) // 4095
        p_8 = (p * 255 + 2047) // 4095
        q_8 = (q * 255 + 2047) // 4095
        t_8 = (t * 255 + 2047) // 4095
        
        if v_8 > 255: v_8 = 255
        if p_8 > 255: p_8 = 255
        if q_8 > 255: q_8 = 255
        if t_8 > 255: t_8 = 255
        
        if region == 0:
            r, g, b = v_8, t_8, p_8
        elif region == 1:
            r, g, b = q_8, v_8, p_8
        elif region == 2:
            r, g, b = p_8, v_8, t_8
        elif region == 3:
            r, g, b = p_8, q_8, v_8
        elif region == 4:
            r, g, b = t_8, p_8, v_8
        else:
            r, g, b = v_8, p_8, q_8
        
        buf[0] = int(g)
        buf[1] = int(r)
        buf[2] = int(b)
    
    @micropython.viper
    def rgb2hsv_optimized(self, buf: ptr8, hsv_out: ptr16):
        """RGB轉HSV - 優化版"""
        r = int(buf[1])
        g = int(buf[0])
        b = int(buf[2])
        
        max_val = r if r > g else g
        max_val = max_val if max_val > b else b
        min_val = r if r < g else g
        min_val = min_val if min_val < b else b
        
        delta = int(max_val - min_val)
        
        # 優化: 精確V擴展 (四捨五入)
        v = (int(max_val) * 4095 + 127) // 255
        if v > 4095:
            v = 4095
        
        if delta == 0 or max_val == 0:
            hsv_out[0] = 0
            hsv_out[1] = 0
            hsv_out[2] = v
            return
        
        # 優化: 精確S計算
        s = (delta * 4095 + (max_val >> 1)) // max_val  # 四捨五入
        if s > 4095:
            s = 4095
        
        h = 0
        if max_val == r:
            h = (60 * (int(g) - int(b))) // delta
            if h < 0:
                h += 360
        elif max_val == g:
            h = (60 * (int(b) - int(r))) // delta + 120
        else:
            h = (60 * (int(r) - int(g))) // delta + 240
        
        if h >= 360:
            h -= 360
        
        hsv_out[0] = h
        hsv_out[1] = s
        hsv_out[2] = v
    
    # ============================================================
    # 批量版本 - 基準
    # ============================================================
    @micropython.viper
    def hsv2rgb_batch_baseline(self, h_buf: ptr16, s_buf: ptr16, v_buf: ptr16,
                                rgb_buf: ptr8, count: int):
        """批量HSV轉RGB - 基準版"""
        for i in range(count):
            h = int(h_buf[i])
            s = int(s_buf[i])
            v = int(v_buf[i])
            buf_idx = i * 3
            
            if s > 4095:
                s = 4095
            
            if s == 0:
                lum = v >> 4
                rgb_buf[buf_idx] = lum
                rgb_buf[buf_idx + 1] = lum
                rgb_buf[buf_idx + 2] = lum
                continue
                
            h = h % 360
            region = h // 60
            remainder = (h - (region * 60)) * 4095 // 60
            
            p = (v * (4095 - s)) >> 12
            q = (v * (4095 - ((s * remainder) >> 12))) >> 12
            t = (v * (4095 - ((s * (4095 - remainder)) >> 12))) >> 12
            
            v_8 = v >> 4
            p_8 = p >> 4
            q_8 = q >> 4
            t_8 = t >> 4
            
            if region == 0:
                r, g, b = v_8, t_8, p_8
            elif region == 1:
                r, g, b = q_8, v_8, p_8
            elif region == 2:
                r, g, b = p_8, v_8, t_8
            elif region == 3:
                r, g, b = p_8, q_8, v_8
            elif region == 4:
                r, g, b = t_8, p_8, v_8
            else:
                r, g, b = v_8, p_8, q_8
                
            rgb_buf[buf_idx] = int(g)
            rgb_buf[buf_idx + 1] = int(r)
            rgb_buf[buf_idx + 2] = int(b)
    
    @micropython.viper
    def rgb2hsv_batch_baseline(self, rgb_buf: ptr8, h_buf: ptr16, s_buf: ptr16, 
                                v_buf: ptr16, count: int):
        """批量RGB轉HSV - 基準版"""
        for i in range(count):
            buf_idx = i * 3
            r = int(rgb_buf[buf_idx + 1])
            g = int(rgb_buf[buf_idx])
            b = int(rgb_buf[buf_idx + 2])
            
            max_val = r if r > g else g
            max_val = max_val if max_val > b else b
            min_val = r if r < g else g
            min_val = min_val if min_val < b else b
            
            delta = int(max_val - min_val)
            v = (int(max_val) << 4) | (int(max_val) >> 4)
            
            if delta == 0 or max_val == 0:
                h_buf[i] = 0
                s_buf[i] = 0
                v_buf[i] = v
                continue
            
            s = (delta << 12) // max_val
            if s > 4095:
                s = 4095
            
            h = 0
            if max_val == r:
                h = (60 * (int(g) - int(b))) // delta
                if h < 0:
                    h += 360
            elif max_val == g:
                h = (60 * (int(b) - int(r))) // delta + 120
            else:
                h = (60 * (int(r) - int(g))) // delta + 240
            
            if h >= 360:
                h -= 360
            
            h_buf[i] = h
            s_buf[i] = s
            v_buf[i] = v
    
    # ============================================================
    # 批量版本 - 優化
    # ============================================================
    @micropython.viper
    def hsv2rgb_batch_optimized(self, h_buf: ptr16, s_buf: ptr16, v_buf: ptr16,
                                 rgb_buf: ptr8, count: int):
        """批量HSV轉RGB - 優化版"""
        for i in range(count):
            h = int(h_buf[i])
            s = int(s_buf[i])
            v = int(v_buf[i])
            buf_idx = i * 3
            
            if s > 4095:
                s = 4095
            if v > 4095:
                v = 4095
            
            if s == 0:
                lum = (v * 255 + 2047) // 4095
                if lum > 255:
                    lum = 255
                rgb_buf[buf_idx] = lum
                rgb_buf[buf_idx + 1] = lum
                rgb_buf[buf_idx + 2] = lum
                continue
            
            h = h % 360
            region = h // 60
            remainder = (h - (region * 60)) * 4095 // 60
            
            p = (v * (4095 - s)) >> 12
            q = (v * (4095 - ((s * remainder) >> 12))) >> 12
            t = (v * (4095 - ((s * (4095 - remainder)) >> 12))) >> 12
            
            v_8 = (v * 255 + 2047) // 4095
            p_8 = (p * 255 + 2047) // 4095
            q_8 = (q * 255 + 2047) // 4095
            t_8 = (t * 255 + 2047) // 4095
            
            if v_8 > 255: v_8 = 255
            if p_8 > 255: p_8 = 255
            if q_8 > 255: q_8 = 255
            if t_8 > 255: t_8 = 255
            
            if region == 0:
                r, g, b = v_8, t_8, p_8
            elif region == 1:
                r, g, b = q_8, v_8, p_8
            elif region == 2:
                r, g, b = p_8, v_8, t_8
            elif region == 3:
                r, g, b = p_8, q_8, v_8
            elif region == 4:
                r, g, b = t_8, p_8, v_8
            else:
                r, g, b = v_8, p_8, q_8
            
            rgb_buf[buf_idx] = int(g)
            rgb_buf[buf_idx + 1] = int(r)
            rgb_buf[buf_idx + 2] = int(b)
    
    @micropython.viper
    def rgb2hsv_batch_optimized(self, rgb_buf: ptr8, h_buf: ptr16, s_buf: ptr16, 
                                 v_buf: ptr16, count: int):
        """批量RGB轉HSV - 優化版"""
        for i in range(count):
            buf_idx = i * 3
            r = int(rgb_buf[buf_idx + 1])
            g = int(rgb_buf[buf_idx])
            b = int(rgb_buf[buf_idx + 2])
            
            max_val = r if r > g else g
            max_val = max_val if max_val > b else b
            min_val = r if r < g else g
            min_val = min_val if min_val < b else b
            
            delta = int(max_val - min_val)
            
            v = (int(max_val) * 4095 + 127) // 255
            if v > 4095:
                v = 4095
            
            if delta == 0 or max_val == 0:
                h_buf[i] = 0
                s_buf[i] = 0
                v_buf[i] = v
                continue
            
            s = (delta * 4095 + (max_val >> 1)) // max_val
            if s > 4095:
                s = 4095
            
            h = 0
            if max_val == r:
                h = (60 * (int(g) - int(b))) // delta
                if h < 0:
                    h += 360
            elif max_val == g:
                h = (60 * (int(b) - int(r))) // delta + 120
            else:
                h = (60 * (int(r) - int(g))) // delta + 240
            
            if h >= 360:
                h -= 360
            
            h_buf[i] = h
            s_buf[i] = s
            v_buf[i] = v
    
    # ============================================================
    # 測試數據生成
    # ============================================================
    def generate_rgb_test_data(self, count=5000):
        """生成RGB測試數據"""
        import random
        random.seed(42)
        
        rgb_data = []
        
        # 邊界值
        for val in [0, 1, 63, 127, 128, 191, 254, 255]:
            for r in [0, 63, 127, 191, 255]:
                for g in [0, 63, 127, 191, 255]:
                    for b in [0, 63, 127, 191, 255]:
                        rgb_data.append((r, g, b))
        
        # 灰階 (256組)
        for i in range(0, 256):
            rgb_data.append((i, i, i))
        
        # 純色 (500組)
        for _ in range(500):
            choice = random.randint(0, 2)
            val = random.randint(0, 255)
            if choice == 0:
                rgb_data.append((val, 0, 0))
            elif choice == 1:
                rgb_data.append((0, val, 0))
            else:
                rgb_data.append((0, 0, val))
        
        # 隨機
        while len(rgb_data) < count:
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            rgb_data.append((r, g, b))
        
        return rgb_data[:count]
    
    def generate_hsv_test_data(self, count=5000):
        """生成HSV測試數據"""
        import random
        random.seed(42)
        
        hsv_data = []
        
        # 邊界值 (完整覆蓋)
        for h in [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 359]:
            for s in [0, 511, 1023, 2047, 3071, 4095]:
                for v in [0, 511, 1023, 2047, 3071, 4095]:
                    hsv_data.append((h, s, v))
        
        # 灰階 (完整)
        for v in range(0, 4096, 16):
            hsv_data.append((0, 0, v))
            hsv_data.append((180, 0, v))  # H無關時測試不同H
        
        # 純色環
        for h in range(0, 360, 5):
            hsv_data.append((h, 4095, 4095))
            hsv_data.append((h, 4095, 2047))
            hsv_data.append((h, 2047, 4095))
        
        # 隨機
        while len(hsv_data) < count:
            h = random.randint(0, 359)
            s = random.randint(0, 4095)
            v = random.randint(0, 4095)
            hsv_data.append((h, s, v))
        
        return hsv_data[:count]
    
    # ============================================================
    # 對比測試 - RGB → HSV → RGB
    # ============================================================
    def test_rgb_roundtrip_compare(self, count=5000):
        """RGB往返測試 - 基準版 vs 優化版"""
        print("\n" + "="*70)
        print(f"RGB → HSV → RGB 往返對比測試 ({count}組)")
        print("="*70)
        
        test_data = self.generate_rgb_test_data(count)
        
        # ========== 基準版測試 ==========
        print("\n【基準版測試】")
        rgb_in = bytearray(count * 3)
        for i, (r, g, b) in enumerate(test_data):
            rgb_in[i*3] = g
            rgb_in[i*3 + 1] = r
            rgb_in[i*3 + 2] = b
        
        hsv_h = array.array('H', [0] * count)
        hsv_s = array.array('H', [0] * count)
        hsv_v = array.array('H', [0] * count)
        rgb_out = bytearray(count * 3)
        
        gc.collect()
        t1 = time.ticks_us()
        self.rgb2hsv_batch_baseline(rgb_in, hsv_h, hsv_s, hsv_v, count)
        time_r2h_base = time.ticks_diff(time.ticks_us(), t1)
        
        gc.collect()
        t2 = time.ticks_us()
        self.hsv2rgb_batch_baseline(hsv_h, hsv_s, hsv_v, rgb_out, count)
        time_h2r_base = time.ticks_diff(time.ticks_us(), t2)
        
        # 統計基準版誤差
        max_err_base = 0
        total_err_base = 0
        perfect_base = 0
        
        for i in range(count):
            idx = i * 3
            err = max(
                abs(rgb_in[idx] - rgb_out[idx]),
                abs(rgb_in[idx+1] - rgb_out[idx+1]),
                abs(rgb_in[idx+2] - rgb_out[idx+2])
            )
            max_err_base = max(max_err_base, err)
            total_err_base += abs(rgb_in[idx] - rgb_out[idx])
            total_err_base += abs(rgb_in[idx+1] - rgb_out[idx+1])
            total_err_base += abs(rgb_in[idx+2] - rgb_out[idx+2])
            if err == 0:
                perfect_base += 1
        
        avg_err_base = total_err_base / (count * 3)
        
        print(f"  完美匹配: {perfect_base}/{count} ({perfect_base/count*100:.2f}%)")
        print(f"  最大誤差: {max_err_base}/255 ({max_err_base/255*100:.2f}%)")
        print(f"  平均誤差: {avg_err_base:.3f}/255 ({avg_err_base/255*100:.3f}%)")
        print(f"  性能: RGB→HSV {time_r2h_base/count:.2f} μs, HSV→RGB {time_h2r_base/count:.2f} μs")
        
        # ========== 優化版測試 ==========
        print("\n【優化版測試】")
        hsv_h_opt = array.array('H', [0] * count)
        hsv_s_opt = array.array('H', [0] * count)
        hsv_v_opt = array.array('H', [0] * count)
        rgb_out_opt = bytearray(count * 3)
        
        gc.collect()
        t1 = time.ticks_us()
        self.rgb2hsv_batch_optimized(rgb_in, hsv_h_opt, hsv_s_opt, hsv_v_opt, count)
        time_r2h_opt = time.ticks_diff(time.ticks_us(), t1)
        
        gc.collect()
        t2 = time.ticks_us()
        self.hsv2rgb_batch_optimized(hsv_h_opt, hsv_s_opt, hsv_v_opt, rgb_out_opt, count)
        time_h2r_opt = time.ticks_diff(time.ticks_us(), t2)
        
        # 統計優化版誤差
        max_err_opt = 0
        total_err_opt = 0
        perfect_opt = 0
        error_samples = []
        
        for i in range(count):
            idx = i * 3
            err_r = abs(rgb_in[idx+1] - rgb_out_opt[idx+1])
            err_g = abs(rgb_in[idx] - rgb_out_opt[idx])
            err_b = abs(rgb_in[idx+2] - rgb_out_opt[idx+2])
            err = max(err_r, err_g, err_b)
            
            max_err_opt = max(max_err_opt, err)
            total_err_opt += err_r + err_g + err_b
            
            if err == 0:
                perfect_opt += 1
            
            if err > 2:
                error_samples.append({
                    'rgb_in': (rgb_in[idx+1], rgb_in[idx], rgb_in[idx+2]),
                    'hsv': (hsv_h_opt[i], hsv_s_opt[i], hsv_v_opt[i]),
                    'rgb_out': (rgb_out_opt[idx+1], rgb_out_opt[idx], rgb_out_opt[idx+2]),
                    'error': (err_r, err_g, err_b)
                })
        
        avg_err_opt = total_err_opt / (count * 3)
        
        print(f"  完美匹配: {perfect_opt}/{count} ({perfect_opt/count*100:.2f}%)")
        print(f"  最大誤差: {max_err_opt}/255 ({max_err_opt/255*100:.2f}%)")
        print(f"  平均誤差: {avg_err_opt:.3f}/255 ({avg_err_opt/255*100:.3f}%)")
        print(f"  性能: RGB→HSV {time_r2h_opt/count:.2f} μs, HSV→RGB {time_h2r_opt/count:.2f} μs")
        
        if error_samples:
            print(f"\n  誤差>2 樣本 (共{len(error_samples)}組,顯示前3組):")
            for sample in error_samples[:3]:
                print(f"    RGB_in:  {sample['rgb_in']}")
                print(f"    HSV:     H={sample['hsv'][0]:3d} S={sample['hsv'][1]:4d} V={sample['hsv'][2]:4d}")
                print(f"    RGB_out: {sample['rgb_out']}")
                print(f"    誤差:    {sample['error']}\n")
        
        # ========== 對比總結 ==========
        print("\n【性能對比】")
        print(f"  完美匹配: {perfect_base} → {perfect_opt} " +
              f"({(perfect_opt-perfect_base)/perfect_base*100:+.1f}%)")
        print(f"  最大誤差: {max_err_base} → {max_err_opt} " +
              f"({(max_err_opt-max_err_base):+d})")
        print(f"  平均誤差: {avg_err_base:.3f} → {avg_err_opt:.3f} " +
              f"({(avg_err_opt-avg_err_base)/avg_err_base*100:+.1f}%)")
        print(f"  RGB→HSV速度: {time_r2h_base/count:.2f} → {time_r2h_opt/count:.2f} μs " +
              f"({(time_r2h_opt-time_r2h_base)/time_r2h_base*100:+.1f}%)")
        print(f"  HSV→RGB速度: {time_h2r_base/count:.2f} → {time_h2r_opt/count:.2f} μs " +
              f"({(time_h2r_opt-time_h2r_base)/time_h2r_base*100:+.1f}%)")
        
        return {
            'baseline': {
                'perfect': perfect_base,
                'max_error': max_err_base,
                'avg_error': avg_err_base,
                'time_r2h': time_r2h_base,
                'time_h2r': time_h2r_base
            },
            'optimized': {
                'perfect': perfect_opt,
                'max_error': max_err_opt,
                'avg_error': avg_err_opt,
                'time_r2h': time_r2h_opt,
                'time_h2r': time_h2r_opt
            }
        }
    
    # ============================================================
    # 對比測試 - HSV → RGB → HSV
    # ============================================================
    def test_hsv_roundtrip_compare(self, count=5000):
        """HSV往返測試 - 基準版 vs 優化版"""
        print("\n" + "="*70)
        print(f"HSV → RGB → HSV 往返對比測試 ({count}組)")
        print("="*70)
        
        test_data = self.generate_hsv_test_data(count)
        
        hsv_h_in = array.array('H', [h for h, s, v in test_data])
        hsv_s_in = array.array('H', [s for h, s, v in test_data])
        hsv_v_in = array.array('H', [v for h, s, v in test_data])
        
        # ========== 基準版測試 ==========
        print("\n【基準版測試】")
        rgb_base = bytearray(count * 3)
        hsv_h_base = array.array('H', [0] * count)
        hsv_s_base = array.array('H', [0] * count)
        hsv_v_base = array.array('H', [0] * count)
        
        gc.collect()
        t1 = time.ticks_us()
        self.hsv2rgb_batch_baseline(hsv_h_in, hsv_s_in, hsv_v_in, rgb_base, count)
        time_h2r_base = time.ticks_diff(time.ticks_us(), t1)
        
        gc.collect()
        t2 = time.ticks_us()
        self.rgb2hsv_batch_baseline(rgb_base, hsv_h_base, hsv_s_base, hsv_v_base, count)
        time_r2h_base = time.ticks_diff(time.ticks_us(), t2)
        
        # 統計基準版
        perfect_base = 0
        max_h_err_base = 0
        max_s_err_base = 0
        max_v_err_base = 0
        
        for i in range(count):
            h_err = abs(hsv_h_in[i] - hsv_h_base[i])
            if h_err > 180:
                h_err = 360 - h_err
            s_err = abs(hsv_s_in[i] - hsv_s_base[i])
            v_err = abs(hsv_v_in[i] - hsv_v_base[i])
            
            if h_err == 0 and s_err == 0 and v_err == 0:
                perfect_base += 1
            
            max_h_err_base = max(max_h_err_base, h_err)
            max_s_err_base = max(max_s_err_base, s_err)
            max_v_err_base = max(max_v_err_base, v_err)
        
        print(f"  完美匹配: {perfect_base}/{count} ({perfect_base/count*100:.2f}%)")
        print(f"  H最大誤差: {max_h_err_base}° ({max_h_err_base/360*100:.2f}%)")
        print(f"  S最大誤差: {max_s_err_base} ({max_s_err_base/4095*100:.2f}%)")
        print(f"  V最大誤差: {max_v_err_base} ({max_v_err_base/4095*100:.2f}%)")
        print(f"  性能: HSV→RGB {time_h2r_base/count:.2f} μs, RGB→HSV {time_r2h_base/count:.2f} μs")
        
        # ========== 優化版測試 ==========
        print("\n【優化版測試】")
        rgb_opt = bytearray(count * 3)
        hsv_h_opt = array.array('H', [0] * count)
        hsv_s_opt = array.array('H', [0] * count)
        hsv_v_opt = array.array('H', [0] * count)
        
        gc.collect()
        t1 = time.ticks_us()
        self.hsv2rgb_batch_optimized(hsv_h_in, hsv_s_in, hsv_v_in, rgb_opt, count)
        time_h2r_opt = time.ticks_diff(time.ticks_us(), t1)
        
        gc.collect()
        t2 = time.ticks_us()
        self.rgb2hsv_batch_optimized(rgb_opt, hsv_h_opt, hsv_s_opt, hsv_v_opt, count)
        time_r2h_opt = time.ticks_diff(time.ticks_us(), t2)
        
        # 統計優化版
        perfect_opt = 0
        max_h_err_opt = 0
        max_s_err_opt = 0
        max_v_err_opt = 0
        error_samples = []
        
        for i in range(count):
            h_err = abs(hsv_h_in[i] - hsv_h_opt[i])
            if h_err > 180:
                h_err = 360 - h_err
            s_err = abs(hsv_s_in[i] - hsv_s_opt[i])
            v_err = abs(hsv_v_in[i] - hsv_v_opt[i])
            
            if h_err == 0 and s_err == 0 and v_err == 0:
                perfect_opt += 1
            
            max_h_err_opt = max(max_h_err_opt, h_err)
            max_s_err_opt = max(max_s_err_opt, s_err)
            max_v_err_opt = max(max_v_err_opt, v_err)
            
            if (h_err > 2 and hsv_v_in[i] > 100) or s_err > 50 or v_err > 10:
                idx = i * 3
                error_samples.append({
                    'hsv_in': (hsv_h_in[i], hsv_s_in[i], hsv_v_in[i]),
                    'rgb': (rgb_opt[idx+1], rgb_opt[idx], rgb_opt[idx+2]),
                    'hsv_out': (hsv_h_opt[i], hsv_s_opt[i], hsv_v_opt[i]),
                    'error': (h_err, s_err, v_err)
                })
        
        print(f"  完美匹配: {perfect_opt}/{count} ({perfect_opt/count*100:.2f}%)")
        print(f"  H最大誤差: {max_h_err_opt}° ({max_h_err_opt/360*100:.2f}%)")
        print(f"  S最大誤差: {max_s_err_opt} ({max_s_err_opt/4095*100:.2f}%)")
        print(f"  V最大誤差: {max_v_err_opt} ({max_v_err_opt/4095*100:.2f}%)")
        print(f"  性能: HSV→RGB {time_h2r_opt/count:.2f} μs, RGB→HSV {time_r2h_opt/count:.2f} μs")
        
        if error_samples:
            print(f"\n  顯著誤差樣本 (共{len(error_samples)}組,顯示前3組):")
            for sample in error_samples[:3]:
                print(f"    HSV_in:  H={sample['hsv_in'][0]:3d} S={sample['hsv_in'][1]:4d} V={sample['hsv_in'][2]:4d}")
                print(f"    RGB:     {sample['rgb']}")
                print(f"    HSV_out: H={sample['hsv_out'][0]:3d} S={sample['hsv_out'][1]:4d} V={sample['hsv_out'][2]:4d}")
                print(f"    誤差:    ΔH={sample['error'][0]:3d} ΔS={sample['error'][1]:4d} ΔV={sample['error'][2]:4d}\n")
        
        # ========== 對比總結 ==========
        print("\n【性能對比】")
        print(f"  完美匹配: {perfect_base} → {perfect_opt} " +
              f"({(perfect_opt-perfect_base)/max(1,perfect_base)*100:+.1f}%)")
        print(f"  H最大誤差: {max_h_err_base}° → {max_h_err_opt}°")
        print(f"  S最大誤差: {max_s_err_base} → {max_s_err_opt}")
        print(f"  V最大誤差: {max_v_err_base} → {max_v_err_opt}")
        print(f"  HSV→RGB速度: {time_h2r_base/count:.2f} → {time_h2r_opt/count:.2f} μs " +
              f"({(time_h2r_opt-time_h2r_base)/time_h2r_base*100:+.1f}%)")
        print(f"  RGB→HSV速度: {time_r2h_base/count:.2f} → {time_r2h_opt/count:.2f} μs " +
              f"({(time_r2h_opt-time_r2h_base)/time_r2h_base*100:+.1f}%)")
        
        return {
            'baseline': {
                'perfect': perfect_base,
                'max_h_err': max_h_err_base,
                'max_s_err': max_s_err_base,
                'max_v_err': max_v_err_base,
                'time_h2r': time_h2r_base,
                'time_r2h': time_r2h_base
            },
            'optimized': {
                'perfect': perfect_opt,
                'max_h_err': max_h_err_opt,
                'max_s_err': max_s_err_opt,
                'max_v_err': max_v_err_opt,
                'time_h2r': time_h2r_opt,
                'time_r2h': time_r2h_opt
            }
        }
    
    # ============================================================
    # 完整窮舉測試
    # ============================================================
    def exhaustive_test_compare(self):
        """完整窮舉測試 - 對比版"""
        print("\n" + "="*70)
        print("完整窮舉測試: RGB全空間掃描 (基準版 vs 優化版)")
        print("="*70)
        
        step = 8
        samples = []
        
        print(f"生成測試數據 (RGB每{step}步取樣)...")
        for r in range(0, 256, step):
            for g in range(0, 256, step):
                for b in range(0, 256, step):
                    samples.append((r, g, b))
        
        count = len(samples)
        print(f"總測試樣本: {count:,}\n")
        
        # 分批處理
        batch_size = 5000
        
        perfect_base_total = 0
        max_err_base_total = 0
        sum_err_base_total = 0
        
        perfect_opt_total = 0
        max_err_opt_total = 0
        sum_err_opt_total = 0
        
        for start in range(0, count, batch_size):
            end = min(start + batch_size, count)
            batch = samples[start:end]
            batch_count = len(batch)
            
            # 準備數據
            rgb_in = bytearray(batch_count * 3)
            for i, (r, g, b) in enumerate(batch):
                rgb_in[i*3] = g
                rgb_in[i*3 + 1] = r
                rgb_in[i*3 + 2] = b
            
            # 基準版
            hsv_h = array.array('H', [0] * batch_count)
            hsv_s = array.array('H', [0] * batch_count)
            hsv_v = array.array('H', [0] * batch_count)
            rgb_out_base = bytearray(batch_count * 3)
            
            self.rgb2hsv_batch_baseline(rgb_in, hsv_h, hsv_s, hsv_v, batch_count)
            self.hsv2rgb_batch_baseline(hsv_h, hsv_s, hsv_v, rgb_out_base, batch_count)
            
            # 優化版
            hsv_h_opt = array.array('H', [0] * batch_count)
            hsv_s_opt = array.array('H', [0] * batch_count)
            hsv_v_opt = array.array('H', [0] * batch_count)
            rgb_out_opt = bytearray(batch_count * 3)
            
            self.rgb2hsv_batch_optimized(rgb_in, hsv_h_opt, hsv_s_opt, hsv_v_opt, batch_count)
            self.hsv2rgb_batch_optimized(hsv_h_opt, hsv_s_opt, hsv_v_opt, rgb_out_opt, batch_count)
            
            # 統計
            for i in range(batch_count):
                idx = i * 3
                
                # 基準版
                err_base = max(
                    abs(rgb_in[idx] - rgb_out_base[idx]),
                    abs(rgb_in[idx+1] - rgb_out_base[idx+1]),
                    abs(rgb_in[idx+2] - rgb_out_base[idx+2])
                )
                max_err_base_total = max(max_err_base_total, err_base)
                sum_err_base_total += err_base
                if err_base == 0:
                    perfect_base_total += 1
                
                # 優化版
                err_opt = max(
                    abs(rgb_in[idx] - rgb_out_opt[idx]),
                    abs(rgb_in[idx+1] - rgb_out_opt[idx+1]),
                    abs(rgb_in[idx+2] - rgb_out_opt[idx+2])
                )
                max_err_opt_total = max(max_err_opt_total, err_opt)
                sum_err_opt_total += err_opt
                if err_opt == 0:
                    perfect_opt_total += 1
            
            print(f"處理進度: {end}/{count} ({end/count*100:.1f}%)")
            gc.collect()
        
        avg_err_base = sum_err_base_total / count
        avg_err_opt = sum_err_opt_total / count
        
        print("\n【窮舉測試結果對比】")
        print("-" * 70)
        print(f"總測試樣本: {count:,}\n")
        
        print("基準版:")
        print(f"  完美匹配: {perfect_base_total:,} ({perfect_base_total/count*100:.2f}%)")
        print(f"  最大誤差: {max_err_base_total}/255 ({max_err_base_total/255*100:.2f}%)")
        print(f"  平均誤差: {avg_err_base:.3f}/255 ({avg_err_base/255*100:.3f}%)\n")
        
        print("優化版:")
        print(f"  完美匹配: {perfect_opt_total:,} ({perfect_opt_total/count*100:.2f}%)")
        print(f"  最大誤差: {max_err_opt_total}/255 ({max_err_opt_total/255*100:.2f}%)")
        print(f"  平均誤差: {avg_err_opt:.3f}/255 ({avg_err_opt/255*100:.3f}%)\n")
        
        print("改進:")
        print(f"  完美匹配: {(perfect_opt_total-perfect_base_total)/perfect_base_total*100:+.1f}%")
        print(f"  最大誤差: {max_err_base_total} → {max_err_opt_total} ({max_err_opt_total-max_err_base_total:+d})")
        print(f"  平均誤差: {(avg_err_opt-avg_err_base)/avg_err_base*100:+.1f}%")
        
        return {
            'baseline': {
                'perfect': perfect_base_total,
                'max_error': max_err_base_total,
                'avg_error': avg_err_base
            },
            'optimized': {
                'perfect': perfect_opt_total,
                'max_error': max_err_opt_total,
                'avg_error': avg_err_opt
            }
        }
    
    # ============================================================
    # 主測試流程
    # ============================================================
    def run_all_tests(self):
        """執行所有對比測試"""
        print("\n" + "█"*70)
        print("█" + " "*68 + "█")
        print("█" + "  RGB ↔ HSV 轉換完整對比測試 (基準版 vs 優化版)  ".center(68) + "█")
        print("█" + " "*68 + "█")
        print("█"*70)
        
        # 第一步
        result1 = self.test_rgb_roundtrip_compare(5000)
        
        # 第二步
        result2 = self.test_hsv_roundtrip_compare(5000)
        
        # 詢問窮舉測試
        print("\n" + "="*70)
        print("快速對比測試完成!")
        print("="*70)
        cont = input("\n是否執行完整窮舉測試 (32,768組)? (y/n): ")
        
        if cont.lower() == 'y':
            result3 = self.exhaustive_test_compare()
            
            # 最終總結
            print("\n" + "█"*70)
            print("█" + " 最終測試總結 ".center(68) + "█")
            print("█"*70)
            
            print("\n【RGB → HSV → RGB 往返】")
            print(f"  快速測試 (5000組):")
            print(f"    完美匹配: {result1['baseline']['perfect']} → {result1['optimized']['perfect']} " +
                  f"({(result1['optimized']['perfect']-result1['baseline']['perfect'])/result1['baseline']['perfect']*100:+.1f}%)")
            print(f"  窮舉測試 (32,768組):")
            print(f"    完美匹配: {result3['baseline']['perfect']} → {result3['optimized']['perfect']} " +
                  f"({(result3['optimized']['perfect']-result3['baseline']['perfect'])/result3['baseline']['perfect']*100:+.1f}%)")
            print(f"    最大誤差: {result3['baseline']['max_error']} → {result3['optimized']['max_error']}")
            
            print("\n【HSV → RGB → HSV 往返】")
            print(f"  完美匹配: {result2['baseline']['perfect']} → {result2['optimized']['perfect']} " +
                  f"({(result2['optimized']['perfect']-result2['baseline']['perfect'])/max(1,result2['baseline']['perfect'])*100:+.1f}%)")
            print(f"  H誤差: {result2['baseline']['max_h_err']}° → {result2['optimized']['max_h_err']}°")
            print(f"  S誤差: {result2['baseline']['max_s_err']} → {result2['optimized']['max_s_err']}")
            print(f"  V誤差: {result2['baseline']['max_v_err']} → {result2['optimized']['max_v_err']}")
            
            print("\n【推薦方案】")
            if result3['optimized']['perfect'] > result3['baseline']['perfect'] * 1.2:
                print("  ✓ 優化版顯著優於基準版,強烈推薦使用!")
            elif result3['optimized']['max_error'] < result3['baseline']['max_error']:
                print("  ✓ 優化版精度更高,推薦使用")
            else:
                print("  → 兩版本性能接近,可根據具體需求選擇")
            
            print("\n█"*70)

# ============================================================
# 執行測試
# ============================================================
if __name__ == '__main__':
    benchmark = RGBHSVOptimizedBenchmark()
    benchmark.run_all_tests()