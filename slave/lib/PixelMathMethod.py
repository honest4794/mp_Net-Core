"""
PixelMathMethod.py — 12-bit 整數波形數學核心（免查表多項式逼近）

三條硬約束：
  1. 核心用 @micropython.viper 加速
  2. 全程整數運算，無浮點、無 math.sin / math.pi、無查表
  3. 數值域固定 12-bit（0-4095），輸出 buffer 用 array('H')

波形逼近：拋物線基底 + 二次修正項（922*(y^2-y)>>12），把 0-65535 相位映射到
0-4095（或 -4096..4096）的正弦，取代舊的 65536 點查表。

效能技巧（對齊舊專案）：
  - 預先儲存重複計算：compile() 把 program 編譯成段描述 tuple，除法/位移/clamp
    只在編譯時算一次，value_at 熱路徑不再 dict.get / int / // / clamp。
  - 乘數變加數：Effect.frame 用 g += spacing 累加，取代 i*spacing 乘法。

決定性（無狀態）：value_at(comp, g) 給全域幀 g 直接回傳單值，
是 effect 的 restart / seek 的基石（相位不藏在 generator 狀態裡）。
"""

try:
    import micropython
    _MP = True
except ImportError:
    _MP = False
    micropython = None


if _MP:

    @micropython.viper
    def _wave01_q12(phase: int) -> int:
        # 0-4095 單週期正弦（相位 0-65535）
        p = phase & 65535
        if p < 32768:
            x = p
            sgn = 1
        else:
            x = p - 32768
            sgn = -1
        s = (x * (32768 - x)) >> 16
        s2 = (s * s) >> 12
        s = s + ((922 * (s2 - s)) >> 12)
        if sgn < 0:
            s = -s
        w = (s + 4096) >> 1
        if w > 4095:
            w = 4095
        return w

    @micropython.viper
    def _sin_q12(phase: int) -> int:
        # -4096..4096 有號正弦（相位 0-65535），供符號判斷用
        p = phase & 65535
        if p < 32768:
            x = p
            sgn = 1
        else:
            x = p - 32768
            sgn = -1
        y = (x * (32768 - x)) >> 16
        y2 = (y * y) >> 12
        y = y + ((922 * (y2 - y)) >> 12)
        return y if sgn > 0 else -y

else:
    # PC 對照版（無 micropython），語義與 viper 版一致
    def _wave01_q12(phase):
        p = phase & 65535
        if p < 32768:
            x = p
            sgn = 1
        else:
            x = p - 32768
            sgn = -1
        s = (x * (32768 - x)) >> 16
        s2 = (s * s) >> 12
        s = s + ((922 * (s2 - s)) >> 12)
        if sgn < 0:
            s = -s
        w = (s + 4096) >> 1
        return 4095 if w > 4095 else w

    def _sin_q12(phase):
        p = phase & 65535
        if p < 32768:
            x = p
            sgn = 1
        else:
            x = p - 32768
            sgn = -1
        y = (x * (32768 - x)) >> 16
        y2 = (y * y) >> 12
        y = y + ((922 * (y2 - y)) >> 12)
        return y if sgn > 0 else -y


def _clamp12(v):
    v = int(v)
    if v < 0:
        return 0
    if v > 4095:
        return 4095
    return v


# 波形段 type → 小整數（熱路徑用 int 分派，比 str 比較快）
_KIND = {"keep": 0, "math_now": 1, "square_wave_now": 2,
         "pulse_wave": 3, "pulse": 4, "starter": 5}


class PixelMathMethod:
    """12-bit 整數波形數學核心。無狀態、決定性。"""

    def compile(self, program):
        """預編譯 program → 段描述 tuple 列表（重複計算只算一次）。

        每段 tuple：
          (start, end, kind, l_range, l_lim, phi4, step_phase, pulse, gap, width)
          start/end    : 段在全域時間軸的起/止幀（end 為累加 end_Time）
          kind         : 段 type 的小整數（_KIND）
          l_range      : clamp(l_max) - clamp(l_lim)
          l_lim        : clamp(l_lim)
          phi4         : phi << 4（對齊舊 is_math_pattern_next）
          step_phase   : (65536*F)//10//fs，相位每幀增量（預算好，省除法）
          pulse        : pulse_wave 的門檻（原始值）
          gap / width  : pulse 型用（gap = fs//F，width = pulse % gap）
        """
        comp = []
        prev = 0
        for seg in program:
            end = int(seg.get("end_Time", 0))
            fs = end - prev
            if fs < 1:
                fs = 1
            l_max = _clamp12(seg.get("l_max", 4095))
            l_lim = _clamp12(seg.get("l_lim", 0))
            l_range = l_max - l_lim
            F = int(seg.get("F", 1))
            step_phase = (65536 * F) // 10 // fs
            phi4 = int(seg.get("phi", 0)) << 4
            kind = _KIND.get(seg.get("type", "keep"), 0)
            pulse = int(seg.get("pulse", 2047))
            gap = fs // F if F > 0 else 1
            if gap < 1:
                gap = 1
            width = pulse % gap
            comp.append((prev, end, kind, l_range, l_lim, phi4, step_phase, pulse, gap, width))
            prev = end
        return comp

    def value_at(self, comp, g):
        """compiled + 全域幀 g → 單值（0-4095）。決定性、無狀態、熱路徑。"""
        if not comp:
            return 0
        g %= comp[-1][1]
        for seg in comp:
            start, end, kind, l_range, l_lim, phi4, step_phase, pulse, gap, width = seg
            if g < end:
                if kind == 0:           # keep
                    return l_range + l_lim
                if kind == 5:           # starter
                    return 0
                rel = g - start
                if kind == 4:           # pulse（不經正弦）
                    return l_lim + (l_range if (rel + phi4) % gap <= width else 0)
                ph = (phi4 + step_phase * rel) & 65535
                if kind == 1:           # math_now
                    v = (_wave01_q12(ph) * l_range) >> 12
                elif kind == 2:         # square_wave_now
                    v = l_range if _wave01_q12(ph) >= 2048 else 0
                else:                   # pulse_wave (kind == 3)
                    v = l_range if _wave01_q12(ph) >= pulse else 0
                return v + l_lim
        return 0

    def pattern_value_at(self, program, t):
        """相容包裝：直接吃原始 program dict 列表（測試/除錯用，非熱路徑）。"""
        return self.value_at(self.compile(program), int(t))


# 模組級單例（所有 effect 共享一份，零重複建構）
mt = PixelMathMethod()
