"""
Pin State Snapshot + Auto-Restore Task

透過統一硬體管理器 (hw_manager) 存取所有硬體資源。
"""

import time
from lib.task import Task
from lib.sys_bus import bus
from lib.hw_manager import HW, _get_pin

# -- 監控目標列表 --
_snap_targets = []        # [(hw_type, hw_id, label), ...]
_initial_states = {}      # (type, id) -> initial_value
_change_log = []          # [(ticks_ms, (type, id), from_val, to_val)]
_timeout_ms = 0
_restored = False


def add_pin(gpio_num, label=None):
    _snap_targets.append((HW.PIN, gpio_num, label or "pin{}".format(gpio_num)))


def add_pwm(pwm_idx, label=None):
    _snap_targets.append((HW.PWM, pwm_idx, label or "pwm{}".format(pwm_idx)))


def set_timeout_ms(ms):
    global _timeout_ms
    _timeout_ms = int(ms or 0)


def get_log():
    return list(_change_log)


# -- 硬體讀寫 (統一走 HW manager) --

def _read_state(hw_type, hw_id):
    if hw_type == HW.PWM:
        v = HW.get(HW.PWM, hw_id)
        return -1 if v is None else v
    elif hw_type == HW.PIN:
        try:
            return _get_pin(hw_id).value()
        except Exception:
            return -1
    return -1


def _write_state(hw_type, hw_id, value):
    if hw_type == HW.PWM:
        HW.set(HW.PWM, hw_id, value)
    elif hw_type == HW.PIN:
        HW.set(HW.PIN, hw_id, value)


# -- Task --

class PinSnapTask(Task):
    log_schema = ["type", "id", "from", "to", "elapsed_ms"]

    def __init__(self, name, ctx):
        super().__init__(name, ctx)
        self._start_ticks = 0

    def on_start(self):
        super().on_start()
        global _restored
        _restored = False
        self._take_snapshot()
        self._start_ticks = time.ticks_ms()
        bus.shared["_pin_snap_started"] = True

    def _take_snapshot(self):
        global _initial_states
        _initial_states.clear()
        for hw_type, hw_id, _ in _snap_targets:
            val = _read_state(hw_type, hw_id)
            _initial_states[(hw_type, hw_id)] = val

    def _restore_all(self):
        global _restored
        for key, initial_val in _initial_states.items():
            hw_type, hw_id = key
            _write_state(hw_type, hw_id, initial_val)
        _restored = True
        _change_log.clear()
        bus.shared["_pin_snap_restored"] = True

    def _check_changes(self):
        now = time.ticks_ms()
        for hw_type, hw_id, _ in _snap_targets:
            key = (hw_type, hw_id)
            initial = _initial_states.get(key)
            if initial is None:
                continue
            current = _read_state(hw_type, hw_id)
            if current == initial or current == -1:
                continue

            last = None
            for entry in reversed(_change_log):
                if entry[1] == key:
                    last = entry
                    break
            if last is not None and last[3] == current:
                continue

            _change_log.append((now, key, initial, current))

            self._lwrite(
                hw_type, hw_id, initial, current,
                time.ticks_diff(now, self._start_ticks),
            )

    def loop(self):
        if not self.running or _restored:
            return
        self._check_changes()
        self.success += 1

        if _timeout_ms > 0:
            elapsed = time.ticks_diff(time.ticks_ms(), self._start_ticks)
            if elapsed >= _timeout_ms:
                self._restore_all()
                self.running = False
