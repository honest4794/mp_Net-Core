"""
action_task_1.py — 綜合動作控制任務 + UART Display 協定

三階段馬達控制:
  RISE (升高) → 正轉
  WAIT (等待) → 停止
  FALL (下降) → 反轉

觸發: 從 bus.shared["_vbtn1_event"] 讀取虛擬按鈕旗標 (hw_actions 寫入)
  v[1]==1:
    空閒(IDLE)       → 啟動 RISE 階段
    升高/等待中        → 提早跳到 FALL 階段

UART Display 協定 (與 DisplayController 相容):
  幀格式: [0xB4] [mode(8-bit)] [brightness(0-31)] [time] [0xFF]
  mode byte: Bit7=特殊模式, Bit6=保留, Bit5-0=模式值(0-63)
  - 本地 mode/brightness 改變 → 發送 UART
  - 收到 UART fram → 更新狀態, 不回傳

可設定參數 (bus.shared):
  _motor_rise_ms  (預設 5000)
  _motor_wait_ms  (預設 500)
  _motor_fall_ms  (預設 5000)
"""

import time
from lib.task import Task
from lib.sys_bus import bus
from lib.hw_manager import HW, _PIN_CACHE
from lib.log_service import get_log
from lib.mp3_tf_16p import MP3TF16P

# ═══ UART 協定常數 ═══

_UART_SOF = 0xB4
_UART_EOF = 0xFF
_UART_BRIGHTNESS_MAX = 31  # APA102 5-bit

# mode byte 位元結構 (8-bit, 0-255 完整傳遞):
#   Bit 7 (0x80): 特殊模式旗標 (1=特殊模式)
#   Bit 6 (0x40): 保留, 暫不使用
#   Bit 5-0:     實際模式值 (0-63)
MODE_SPECIAL  = 0x80  # Bit 7
MODE_RESERVED = 0x40  # Bit 6
MODE_VALUE    = 0x3F  # Bits 5-0

# ═══ 腳位解析 ═══

def _resolve_pin(gpio_or_label):
    from machine import Pin
    if isinstance(gpio_or_label, str):
        cfg = bus.shared.get("PIN") or {}
        lst = cfg.get("list") or []
        for item in lst:
            if isinstance(item, dict) and item.get("label") == gpio_or_label:
                gpio_num = int(item.get("GPIO", 0))
                if gpio_num in _PIN_CACHE:
                    return _PIN_CACHE[gpio_num]
                return Pin(gpio_num, Pin.OUT)
        return None
    gpio = int(gpio_or_label)
    if gpio in _PIN_CACHE:
        return _PIN_CACHE[gpio]
    p = Pin(gpio, Pin.OUT)
    _PIN_CACHE[gpio] = p
    return p


# ═══ 常數 ═══

STATE_IDLE      = 0
STATE_RISE      = 1
STATE_WAIT      = 2
STATE_FALL      = 3
STATE_PRE_DELAY = 4   # 進入模式後, 啟動電機前的延遲

_DEFAULT_RISE_MS = 5000
_DEFAULT_WAIT_MS = 90000
_DEFAULT_FALL_MS = 10000


def _read_cfg(key, default):
    v = bus.shared.get(key)
    return int(v) if v is not None else default


# 馬達腳位預設 GPIO（label 找不到時的回落）
_MOTOR_DEFAULT_PINS = {
    "m1":   8,
    "m2":   9,
    "m_en": 10,
}


def _resolve_pin_or(label, fallback_gpio):
    """按 label 解析 pin，找不到則用 fallback GPIO"""
    p = _resolve_pin(label)
    if p is not None:
        return p
    return _resolve_pin(fallback_gpio)


# ═══ 模式設定 (硬編碼) ═══
_MAX_MODE = 9  # 總模式數 (mode 1-9), mode 0=standby 不計入

# 電機觸發列表: (mod, entry_delay_ms, wait_ms)
# 只放需要觸發電機的模式, 不在列表 = 不觸發
_MOTOR_MODE_LIST = [
    (1, 0,  20000),    # mode 1: delay 500ms → RISE → wait 500ms → FALL
]


# ═══ ActionTask1 ═══

class ActionTask1(Task):
    def __init__(self, name, ctx):
        super().__init__(name, ctx)
        self._m1 = None
        self._m2 = None
        self._m_en = None
        self._state = STATE_IDLE
        self._deadline = 0
        self._rise_ms = _DEFAULT_RISE_MS
        self._wait_ms = _DEFAULT_WAIT_MS
        self._fall_ms = _DEFAULT_FALL_MS

        # UART Display 狀態
        self._uart = None
        self._display_mode = 0
        self._display_brightness = 0
        self._display_time = 0
        self._mode_list = _MOTOR_MODE_LIST[:]  # 模式列表拷貝
        self._max_mode = 0                    # on_start 時設定
        self._last_vbtn0 = 1        # 初始假設放開（pull-up）
        self._vbtn0_press_time = 0
        self._first_click = True    # 第一次點擊用 mode=1 而非 mode+1
        self._vbtn0_long_triggered = False
        self._mp3 = None
        self._mp3_state = 0        # 0=未初始化, 1=等待中, 2=完成
        self._mp3_deadline = 0
        self._uart_rx_buf = bytearray()  # UART 接收累積 buffer

    def on_start(self):
        super().on_start()

        self._rise_ms = _read_cfg("_motor_rise_ms", _DEFAULT_RISE_MS)
        self._wait_ms = _read_cfg("_motor_wait_ms", _DEFAULT_WAIT_MS)
        self._fall_ms = _read_cfg("_motor_fall_ms", _DEFAULT_FALL_MS)

        self._max_mode = _MAX_MODE  # 總模式數 (從 _MAX_MODE 取得)

        self._m1   = _resolve_pin_or("m1",   _MOTOR_DEFAULT_PINS["m1"])
        self._m2   = _resolve_pin_or("m2",   _MOTOR_DEFAULT_PINS["m2"])
        self._m_en = _resolve_pin_or("m_en", _MOTOR_DEFAULT_PINS["m_en"])
        self._enter(STATE_IDLE)

        get_log().info(
            "[Motor] rise={} wait={} fall={}ms".format(
                self._rise_ms, self._wait_ms, self._fall_ms))

        # 初始化 UART (從 bus.shared["UART"] 讀設定)
        self._init_uart()
        # 初始化 MP3-TF-16P (UART list[1], baud 9600)
        self._init_mp3()

    # ═══ 階段切換 ═══

    def _enter(self, state, delay_ms=None):
        self._state = state
        now = time.ticks_ms()

        if state == STATE_IDLE:
            self._motor_stop()
            self._deadline = 0
            HW.set(HW.VBTN, 1, 0)
        elif state == STATE_PRE_DELAY:
            self._motor_stop()
            self._deadline = time.ticks_add(now, delay_ms or 0)
        elif state == STATE_RISE:
            self._motor_fwd()
            self._deadline = time.ticks_add(now, self._rise_ms)
        elif state == STATE_WAIT:
            self._motor_stop()
            self._deadline = time.ticks_add(now, self._wait_ms)
        elif state == STATE_FALL:
            self._motor_rev()
            self._deadline = time.ticks_add(now, self._fall_ms)

    # ═══ 馬達控制 ═══

    def _motor_stop(self):
        if self._m1: self._m1.value(0)
        if self._m2: self._m2.value(0)
        if self._m_en: self._m_en.value(0)

    def _motor_fwd(self):
        if self._m1: self._m1.value(0)
        if self._m2: self._m2.value(1)
        if self._m_en: self._m_en.value(1)

    def _motor_rev(self):
        if self._m1: self._m1.value(1)
        if self._m2: self._m2.value(0)
        if self._m_en: self._m_en.value(1)

    # ═══ UART Display 協定 ═══

    def _init_uart(self):
        """從 bus.shared["UART"].list[0] 初始化 UART"""
        uart_cfg = bus.shared.get("UART", {}) or {}
        if not int(uart_cfg.get("enable", 0) or 0):
            return
        lst = uart_cfg.get("list", []) or []
        if not lst:
            return

        cfg = lst[0]
        uid = int(cfg.get("id", 1) or 1)
        baud = int(cfg.get("baudrate", 115200) or 115200)
        gpio = cfg.get("GPIO", {}) or {}
        tx = gpio.get("tx")
        rx = gpio.get("rx")

        import machine
        try:
            self._uart = machine.UART(
                uid,
                baudrate=baud,
                bits=8,
                parity=None,
                stop=1,
                tx=machine.Pin(tx) if tx is not None else None,
                rx=machine.Pin(rx) if rx is not None else None,
                timeout=0,
                timeout_char=0,
            )
            get_log().info("[UART] init id={} baud={} tx={} rx={}".format(uid, baud, tx, rx))
        except Exception as e:
            get_log().error("[UART] init failed: {}".format(e))

    def _send_uart_state(self):
        """發送 5-byte 幀: [0xB4, mode, brightness(0-31), time, 0xFF]"""
        if self._uart is None:
            return
        brightness = max(0, min(self._display_brightness, _UART_BRIGHTNESS_MAX))
        try:
            data = bytearray([
                _UART_SOF,
                self._display_mode,
                brightness,
                self._display_time & 0xFF,
                _UART_EOF,
            ])
            self._uart.write(data)
        except Exception as e:
            get_log().error("[UART] send error: {}".format(e))

    def _handle_uart_receive(self):
        """輪詢 UART 接收，解析 5-byte 幀（累積 buffer，支援碎片）"""
        if self._uart is None:
            return
        try:
            # 不依賴 any()，每圈都讀一次，避免 FIFO 漏收
            chunk = self._uart.read()
            if chunk:
                self._uart_rx_buf.extend(chunk)

            processed = 0
            i = 0
            while i + 4 < len(self._uart_rx_buf):
                if (self._uart_rx_buf[i] == _UART_SOF
                        and self._uart_rx_buf[i + 4] == _UART_EOF):
                    mode = self._uart_rx_buf[i + 1]
                    brightness = self._uart_rx_buf[i + 2] & _UART_BRIGHTNESS_MAX
                    time_remaining = self._uart_rx_buf[i + 3]
                    self._process_uart_cmd(mode, brightness, time_remaining)
                    processed = i + 5
                    break  # 只處理第一個幀
                i += 1

            if processed > 0:
                self._uart_rx_buf = self._uart_rx_buf[processed:]
            elif len(self._uart_rx_buf) > 256:
                # 防止垃圾資料無限累積，溢出時清空
                self._uart_rx_buf = bytearray()
        except Exception as e:
            get_log().error("[UART] recv error: {}".format(e))

    def _init_mp3(self):
        """初始化 MP3-TF-16P (從 UART list[1], baud 9600)"""
        uart_cfg = bus.shared.get("UART", {}) or {}
        if not int(uart_cfg.get("enable", 0) or 0):
            return
        lst = uart_cfg.get("list", []) or []
        if len(lst) < 2:
            return
        cfg = lst[1]
        uid = int(cfg.get("id", 2) or 2)
        baud = int(cfg.get("baudrate", 9600) or 9600)
        gpio = cfg.get("GPIO", {}) or {}
        tx = gpio.get("tx")
        rx = gpio.get("rx")
        import machine
        try:
            uart = machine.UART(
                uid,
                baudrate=baud,
                bits=8,
                parity=None,
                stop=1,
                tx=machine.Pin(tx) if tx is not None else None,
                rx=machine.Pin(rx) if rx is not None else None,
                timeout=0,
                timeout_char=0,
            )
            self._mp3 = MP3TF16P(uart)
            # 上電需等模組初始化完成，用非阻塞定時器
            self._mp3_state = 1
            self._mp3_deadline = time.ticks_add(time.ticks_ms(), 1500)
            get_log().info("[MP3] init UART{} baud={} tx={} rx={}".format(uid, baud, tx, rx))
        except Exception as e:
            get_log().error("[MP3] init failed: {}".format(e))

    def _process_uart_cmd(self, mode, brightness, time_remaining):
        """處理收到的 UART 幀 — 更新內部狀態，不回傳"""
        changed = False
        mode_changed = False
        if self._display_mode != mode:
            self._display_mode = mode
            changed = True
            mode_changed = True
        if self._display_brightness != brightness:
            self._display_brightness = brightness
            changed = True
        if self._display_time != time_remaining:
            self._display_time = time_remaining
            changed = True

        if changed:
            # 同步到 bus.shared 供其他 task 讀取
            bus.shared["_display_mode"] = self._display_mode
            bus.shared["_display_brightness"] = self._display_brightness
            bus.shared["_display_time"] = self._display_time
            get_log().immediate("[UART] rx mode={} bri={} time={}".format(
                mode, brightness, time_remaining))
            # 只有 mode 本身變更才觸發電機/音頻，防止 UART 重複同 mode 時重播
            if mode_changed:
                self._check_mode_motor()
                self._check_mode_audio()

    def _check_mode_motor(self):
        """
        檢查當前 _display_mode 是否匹配電機模式列表。
        列表格式: bus.shared["_mode_motor_list"] = [[mod, entry_delay_ms, wait_ms], ...]
          mod            — 比對的模式值 (低位元)
          entry_delay_ms — 進入模式後, 啟動電機前的延遲 (ms), 0=立即啟動
          wait_ms        — RISE 結束後的 WAIT 時間 (ms)
        RISE/FALL 時間固定 (由 bus.shared["_motor_rise_ms"] / _fall_ms 決定, 預設各 5000ms)
        匹配時自動啟動電機序列, 可提前結束 (VBTN[1])
        """
        motor_list = self._mode_list  # 直接使用硬編碼列表
        for entry in motor_list:
            if not isinstance(entry, (list, tuple)) or len(entry) < 3:
                continue
            mod_match, entry_delay, wait = entry[0], int(entry[1]), int(entry[2])
            if (self._display_mode & MODE_VALUE) == mod_match:
                self._wait_ms = wait
                if self._state == STATE_IDLE:
                    if entry_delay > 0:
                        self._enter(STATE_PRE_DELAY, delay_ms=entry_delay)
                    else:
                        self._enter(STATE_RISE)
                else:
                    self._enter(STATE_FALL)  # 運轉中 → 提前降下
                get_log().info("[Motor] auto mode={} entry_delay={} wait={}".format(
                    mod_match, entry_delay, wait))
                break

    def _check_mode_audio(self):
        """
        根據當前模式播放 SD 卡音頻 (每段播一次)。
        映射: bus.shared["_mode_audio_map"] = {mode: track, ...}
        若未設定映射表, 預設 track = mode (mode 0=standby 不播音)
        """
        if self._mp3 is None or self._mp3_state != 2:
            return
        raw_mode = self._display_mode & MODE_VALUE
        audio_map = bus.shared.get("_mode_audio_map", None)
        if isinstance(audio_map, dict):
            track = audio_map.get(raw_mode)
            if track is None:
                self._mp3.stop()
                return
        else:
            if raw_mode == 0:          # mode 0 = standby, 不播音
                self._mp3.stop()
                return
            track = raw_mode           # mode 1 → track 1, mode 2 → track 2, ...
        self._mp3.stop()
        time.sleep_ms(30)
        self._mp3.play_track(track)
        get_log().info("[Audio] mode={} track={}".format(raw_mode, track))

    def set_display_state(self, mode=None, brightness=None):
        """
        設定顯示狀態（外部呼叫用）
        - mode/brightness 有變更時發送 UART
        - time 由 DisplayController 管理，不在此設定
        """
        changed = False
        if mode is not None and self._display_mode != mode:
            max_mode = self._max_mode
            val = mode & MODE_VALUE  # 只比對低位元（排除特殊旗標 bit7）
            if max_mode > 0 and val > max_mode:
                mode = 1 | (mode & MODE_SPECIAL)  # 9→1 wrap, 保留特殊旗標
            self._display_mode = mode
            changed = True
        if brightness is not None:
            b = max(0, min(brightness, _UART_BRIGHTNESS_MAX))
            if self._display_brightness != b:
                self._display_brightness = b
                changed = True

        if changed:
            bus.shared["_display_mode"] = self._display_mode
            bus.shared["_display_brightness"] = self._display_brightness
            self._send_uart_state()
            # mode 變更 → 檢查電機映射、音頻
            if mode is not None:
                special = " (SPECIAL)" if (self._display_mode & MODE_SPECIAL) else ""
                get_log().info("[Mode] switch to mode={} raw_mode={}{} bri={}".format(
                    self._display_mode,
                    self._display_mode & MODE_VALUE,
                    special,
                    self._display_brightness))
                self._check_mode_motor()
                self._check_mode_audio()

    # ═══ 主迴圈 ═══

    def loop(self):
        if not self.running:
            return
        now = time.ticks_ms()

        # ── MP3 初始化後續 (非阻塞等 1.5s) ──
        if self._mp3_state == 1 and time.ticks_diff(self._mp3_deadline, now) <= 0:
            self._mp3.switch_drive(1)
            self._mp3.stop()
            self._mp3_state = 2

        # ── UART 接收 ──
        self._handle_uart_receive()

        # ── VBTN[0] 短按/長按 ──
        v0 = HW.get(HW.VBTN, 0)
        now_btn = time.ticks_ms()
        if v0 == 0 and self._last_vbtn0 == 1:
            # 剛按下 → 記錄時間
            self._vbtn0_press_time = now_btn
            self._vbtn0_long_triggered = False
            self._last_vbtn0 = 0
        elif v0 == 0 and self._vbtn0_press_time > 0 and not self._vbtn0_long_triggered and self._last_vbtn0 == 0:
            # 持續按住 → 檢查 3s 長按
            if time.ticks_diff(now_btn, self._vbtn0_press_time) >= 3000:
                self._vbtn0_long_triggered = True
                self.set_display_state(mode=self._display_mode ^ MODE_SPECIAL)
        elif v0 == 1 and self._vbtn0_press_time > 0 and self._last_vbtn0 == 0:
            # 放開 → 短按(模式+1) 或 第一次點擊用 mode=1
            if not self._vbtn0_long_triggered:
                if self._first_click:
                    self._first_click = False
                    self.set_display_state(mode=1)
                else:
                    self.set_display_state(mode=self._display_mode + 1)
            self._last_vbtn0 = 1

        # ── 計時: 階段到期 → 下一階段 ──
        if self._state != STATE_IDLE and self._deadline > 0:
            if time.ticks_diff(now, self._deadline) >= 0:
                if self._state == STATE_PRE_DELAY:
                    self._enter(STATE_RISE)
                elif self._state == STATE_RISE:
                    self._enter(STATE_WAIT)
                elif self._state == STATE_WAIT:
                    self._enter(STATE_FALL)
                elif self._state == STATE_FALL:
                    self._enter(STATE_IDLE)
                self.success += 1

        # ── 虛擬按鈕旗標 (hw_actions 接收端寫入) ──
        v = bus.shared.pop("_vbtn1_event", None)
        if v is not None and v == 1:
            self._on_vbtn1(now)

    def _on_vbtn1(self, now):
        """VBTN[1] 按下"""
        if self._state == STATE_IDLE:
            self._enter(STATE_RISE)
        elif self._state in (STATE_RISE, STATE_WAIT):
            self._enter(STATE_FALL)   # 提早下降
        self.success += 1

    def on_stop(self):
        self._motor_stop()
        self._deadline = 0
        super().on_stop()
