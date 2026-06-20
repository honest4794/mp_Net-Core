"""
action_task_1.py — 綜合動作控制任務 + UART Display 協定

三階段馬達控制:
  RISE (升高) → 正轉
  WAIT (等待) → 停止
  FALL (下降) → 反轉

觸發: 直接輪詢虛擬按鈕 VBTN[0]/VBTN[1]
  VBTN[0] 短按:
    空閒(IDLE)       → 啟動 RISE 階段
    升高/等待中      → 提早跳到 FALL 階段
  VBTN[0] 長按:
    反轉 Bit6 保留旗標
  VBTN[1] 短按:
    mode + 1 (限制於低 6 bit: 0-63, 保留 Bit6/Bit7)
  VBTN[1] 長按:
    反轉 Bit7 特殊模式旗標

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
from lib.proto import Proto

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

CMD_HW_EX_IC = 0x1403
EX_IC_CHIP_TYPE = 0
EX_IC_CHIP_ID = 0

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

_DEFAULT_RISE_MS = 7300
_DEFAULT_WAIT_MS = 90000
_DEFAULT_FALL_MS = 8000


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
_MAX_MODE = MODE_VALUE  # mode 僅使用低 6 bit (0-63)
_LONG_PRESS_MS = 3000

# 電機觸發列表: (mod, entry_delay_ms, wait_ms)
# 只放需要觸發電機的模式, 不在列表 = 不觸發
_MOTOR_MODE_LIST = [
    (1, 0,  17700),    # mode 1: delay 500ms → RISE → wait 500ms → FALL
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
        self._temp_mode = 0
        self._display_brightness = 0
        self._display_time = 0
        self._mode_list = _MOTOR_MODE_LIST[:]  # 模式列表拷貝
        self._max_mode = 0                    # on_start 時設定
        self._last_vbtn = [1, 1]              # 初始假設放開（pull-up）
        self._vbtn_press_time = [0, 0]
        self._vbtn_long_triggered = [False, False]
        self._now_bus = None
        self._mp3 = None
        self._mp3_state = 0        # 0=未初始化, 1=等待中, 2=完成
        self._mp3_deadline = 0
        self._uart_rx_buf = bytearray()  # UART 接收累積 buffer

    def on_start(self):
        super().on_start()

        self._rise_ms = _read_cfg("_motor_rise_ms", _DEFAULT_RISE_MS)
        self._wait_ms = _read_cfg("_motor_wait_ms", _DEFAULT_WAIT_MS)
        self._fall_ms = _read_cfg("_motor_fall_ms", _DEFAULT_FALL_MS)

        self._max_mode = _MAX_MODE
        self._now_bus = bus.get_service("NowBus")
        vbtn0 = HW.get(HW.VBTN, 0)
        vbtn1 = HW.get(HW.VBTN, 1)
        self._last_vbtn[0] = 1 if vbtn0 is None else int(vbtn0)
        self._last_vbtn[1] = 1 if vbtn1 is None else int(vbtn1)
        self._vbtn_press_time = [0, 0]
        self._vbtn_long_triggered = [False, False]

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

    def _build_uart_state_frame(self, mode=None, brightness=None, time_remaining=None):
        """建立 5-byte 幀: [0xB4, mode, brightness(0-31), time, 0xFF]"""
        if mode is None:
            mode = self._display_mode
        if brightness is None:
            brightness = self._display_brightness
        if time_remaining is None:
            time_remaining = self._display_time
        brightness = max(0, min(brightness, _UART_BRIGHTNESS_MAX))
        return bytes([
            _UART_SOF,
            mode & 0xFF,
            brightness,
            time_remaining & 0xFF,
            _UART_EOF,
        ])

    def _send_uart_state(self, mode=None, brightness=None, time_remaining=None):
        """發送 5-byte 幀: [0xB4, mode, brightness(0-31), time, 0xFF]"""
        if self._uart is None:
            return
        try:
            if mode is None:
                mode = self._display_mode
            if brightness is None:
                brightness = self._display_brightness
            if time_remaining is None:
                time_remaining = self._display_time
            data = self._build_uart_state_frame(mode=mode, brightness=brightness, time_remaining=time_remaining)
            self._uart.write(data)
            get_log().info("[UART][TX] mod={} bit={} bri={} time={} frame={}".format(
                mode & MODE_VALUE,
                self._format_mode_bits(mode),
                brightness,
                time_remaining,
                self._format_frame_hex(data)))
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
        prev_mode = self._display_mode
        self._temp_mode = mode

        mode_changed = self._temp_mode != prev_mode
        brightness_changed = self._display_brightness != brightness
        time_changed = self._display_time != time_remaining
        changed = mode_changed or brightness_changed or time_changed

        if mode_changed:
            self._display_mode = self._temp_mode
        if brightness_changed:
            self._display_brightness = brightness
        if time_changed:
            self._display_time = time_remaining

        if changed:
            # 同步到 bus.shared 供其他 task 讀取
            bus.shared["_display_mode"] = self._display_mode
            bus.shared["_temp_mode"] = self._temp_mode
            bus.shared["_display_brightness"] = self._display_brightness
            bus.shared["_display_time"] = self._display_time
            get_log().immediate("[UART] rx mod={} bit={} bri={} time={}".format(
                mode & MODE_VALUE,
                self._format_mode_bits(mode),
                brightness,
                time_remaining))
            # 只有收到確認模式與當前運行模式不同，才提交新模式並通知外部
            if mode_changed:
                get_log().info("[Mode] switch mod={} bit={} bri={}".format(
                    self._display_mode & MODE_VALUE,
                    self._format_mode_bits(self._display_mode),
                    self._display_brightness))
                self._notify_control_panel_ex_ic()
                self._check_mode_motor()
                self._check_mode_audio()

    def _format_mode_bits(self, mode):
        return "{:08b}".format(mode & 0xFF)

    def _format_frame_hex(self, data):
        return " ".join("{:02X}".format(b) for b in data)

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

    def _toggle_mode_flag(self, flag):
        self.set_display_state(mode=self._display_mode ^ flag)

    def _notify_control_panel_ex_ic(self):
        now_bus = self._now_bus or bus.get_service("NowBus")
        if now_bus is None:
            return
        self._now_bus = now_bus
        try:
            frame = self._build_uart_state_frame()
            payload = bytes([EX_IC_CHIP_TYPE, EX_IC_CHIP_ID]) + frame
            now_bus.broadcast(Proto.pack(CMD_HW_EX_IC, payload))
            get_log().info("[NOW][TX][0x1403] chip={} id={} mod={} bit={} bri={} time={} frame={}".format(
                EX_IC_CHIP_TYPE,
                EX_IC_CHIP_ID,
                self._display_mode & MODE_VALUE,
                self._format_mode_bits(self._display_mode),
                self._display_brightness,
                self._display_time,
                self._format_frame_hex(frame)))
        except Exception as e:
            get_log().error("[EX_IC] notify display frame failed: {}".format(e))

    def _next_mode(self):
        max_mode = self._max_mode
        flags = self._display_mode & (MODE_SPECIAL | MODE_RESERVED)
        if max_mode < 0:
            return flags
        val = (self._display_mode & MODE_VALUE) + 1
        return flags | (val % (max_mode + 1))

    def _handle_vbtn_short(self, btn_id):
        if btn_id == 0:
            self._trigger_motor_action()
        elif btn_id == 1:
            self.set_display_state(mode=self._next_mode())

    def _handle_vbtn_long(self, btn_id):
        if btn_id == 0:
            self._toggle_mode_flag(MODE_RESERVED)
        elif btn_id == 1:
            self._toggle_mode_flag(MODE_SPECIAL)

    def _poll_vbtn(self, btn_id, now_btn):
        state = HW.get(HW.VBTN, btn_id)
        if state is None:
            state = 1

        if state == 0 and self._last_vbtn[btn_id] == 1:
            self._vbtn_press_time[btn_id] = now_btn
            self._vbtn_long_triggered[btn_id] = False
            self._last_vbtn[btn_id] = 0
        elif (state == 0
              and self._vbtn_press_time[btn_id] > 0
              and not self._vbtn_long_triggered[btn_id]
              and self._last_vbtn[btn_id] == 0):
            if time.ticks_diff(now_btn, self._vbtn_press_time[btn_id]) >= _LONG_PRESS_MS:
                self._vbtn_long_triggered[btn_id] = True
                self._handle_vbtn_long(btn_id)
        elif state == 1 and self._vbtn_press_time[btn_id] > 0 and self._last_vbtn[btn_id] == 0:
            if not self._vbtn_long_triggered[btn_id]:
                self._handle_vbtn_short(btn_id)
            self._last_vbtn[btn_id] = 1
            self._vbtn_press_time[btn_id] = 0
            self._vbtn_long_triggered[btn_id] = False

    def set_display_state(self, mode=None, brightness=None):
        """
        設定顯示狀態（外部呼叫用）
        - mode/brightness 有變更時發送 UART
        - time 由 DisplayController 管理，不在此設定
        """
        target_mode = self._display_mode
        target_brightness = self._display_brightness
        changed = False
        if mode is not None and target_mode != mode:
            max_mode = self._max_mode
            flags = mode & (MODE_SPECIAL | MODE_RESERVED)
            val = mode & MODE_VALUE
            if max_mode > 0 and val > max_mode:
                mode = flags | (val % (max_mode + 1))
            target_mode = mode
            changed = True
        if brightness is not None:
            b = max(0, min(brightness, _UART_BRIGHTNESS_MAX))
            if target_brightness != b:
                target_brightness = b
                changed = True

        if changed:
            self._send_uart_state(
                mode=target_mode,
                brightness=target_brightness,
                time_remaining=self._display_time,
            )
            # 本地只送 request，待 UART 回覆後才提交新模式
            if mode is not None:
                get_log().info("[Mode][REQ] mod={} bit={} bri={}".format(
                    target_mode & MODE_VALUE,
                    self._format_mode_bits(target_mode),
                    target_brightness))

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

        now_btn = time.ticks_ms()
        self._poll_vbtn(0, now_btn)
        self._poll_vbtn(1, now_btn)

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

    def _trigger_motor_action(self):
        """VBTN[0] 短按: 控制電機動作"""
        if self._state == STATE_IDLE:
            self._enter(STATE_RISE)
        elif self._state in (STATE_RISE, STATE_WAIT):
            self._enter(STATE_FALL)   # 提早下降
        self.success += 1

    def on_stop(self):
        self._motor_stop()
        self._deadline = 0
        super().on_stop()
