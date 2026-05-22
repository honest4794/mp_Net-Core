import time
from lib.task import Task
from lib.sys_bus import bus

_PIN_CACHE = {}


def _get_pin(gpio_num, mode=None):
    from machine import Pin
    if mode is None:
        mode = Pin.OUT
    key = (gpio_num, mode)
    if key not in _PIN_CACHE:
        _PIN_CACHE[key] = Pin(gpio_num, mode)
    return _PIN_CACHE[key]


class ActionTask(Task):
    def __init__(self, name, ctx):
        super().__init__(name, ctx)
        self._pulses = []

    def on_start(self):
        super().on_start()
        self._pulses = []

    def _start_pulse(self, gpio, value, duration_ms):
        try:
            p = _get_pin(gpio)
            orig = p.value()
        except Exception as e:
            print("[ActionTask] pin {} init err: {}".format(gpio, e))
            return

        try:
            p.value(value)
        except Exception as e:
            print("[ActionTask] pin {} set err: {}".format(gpio, e))
            return

        deadline = time.ticks_ms() + duration_ms
        self._pulses.append({
            "gpio": gpio,
            "orig_value": orig,
            "target_value": value,
            "deadline": deadline,
            "duration_ms": duration_ms,
            "done": False,
        })
        print("[ActionTask] pin {} {} -> {} ({}ms)".format(gpio, orig, value, duration_ms))

    def loop(self):
        if not self.running:
            return

        cmd = bus.shared.pop("action_pulse", None)
        if cmd and isinstance(cmd, dict):
            gpio = cmd.get("gpio")
            value = cmd.get("value", 1)
            duration_ms = cmd.get("duration_ms", 500)
            if gpio is not None:
                self._start_pulse(int(gpio), int(value), int(duration_ms))

        now = time.ticks_ms()
        for pulse in self._pulses:
            if pulse["done"]:
                continue
            if time.ticks_diff(now, pulse["deadline"]) >= 0:
                try:
                    p = _get_pin(pulse["gpio"])
                    p.value(pulse["orig_value"])
                except Exception as e:
                    print("[ActionTask] pin {} revert err: {}".format(pulse["gpio"], e))
                print("[ActionTask] pin {} {} -> {} (done)".format(
                    pulse["gpio"], pulse["target_value"], pulse["orig_value"]))
                pulse["done"] = True
                self.success += 1

        self._pulses = [p for p in self._pulses if not p["done"]]

    def on_stop(self):
        super().on_stop()
        for pulse in self._pulses:
            if not pulse["done"]:
                try:
                    p = _get_pin(pulse["gpio"])
                    p.value(pulse["orig_value"])
                except Exception:
                    pass
        self._pulses = []
