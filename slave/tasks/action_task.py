import time
from lib.task import Task
from lib.sys_bus import bus
from lib.hw_manager import _PIN_CACHE


class ActionTask(Task):
    def __init__(self, name, ctx):
        super().__init__(name, ctx)
        self._pulses = []

    def on_start(self):
        super().on_start()
        self._pulses = []

    def _resolve_pin(self, gpio):
        """接受 GPIO 號碼或 label，回傳 Pin 物件"""
        from machine import Pin
        if isinstance(gpio, str):
            cfg = bus.shared.get("PIN") or {}
            lst = cfg.get("list") or []
            for item in lst:
                if isinstance(item, dict) and item.get("label") == gpio:
                    gpio_num = int(item.get("GPIO", 0))
                    if gpio_num in _PIN_CACHE:
                        return _PIN_CACHE[gpio_num]
                    return Pin(gpio_num, Pin.OUT)
            return None
        if gpio in _PIN_CACHE:
            return _PIN_CACHE[gpio]
        p = Pin(int(gpio), Pin.OUT)
        _PIN_CACHE[int(gpio)] = p
        return p

    def _start_pulse(self, gpio, value, duration_ms):
        p = self._resolve_pin(gpio)
        if p is None:
            print("[ActionTask] pin {} not found".format(gpio))
            return
        try:
            orig = p.value()
            p.value(value)
        except Exception as e:
            print("[ActionTask] pin {} err: {}".format(gpio, e))
            return

        deadline = time.ticks_ms() + duration_ms
        self._pulses.append({
            "gpio": gpio,
            "orig_value": orig,
            "target_value": value,
            "deadline": deadline,
            "done": False,
        })
        print("[ActionTask] {} {} -> {} ({}ms)".format(gpio, orig, value, duration_ms))

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
                p = self._resolve_pin(pulse["gpio"])
                if p is not None:
                    try:
                        p.value(pulse["orig_value"])
                    except Exception as e:
                        print("[ActionTask] {} revert err: {}".format(pulse["gpio"], e))
                print("[ActionTask] pin {} {} -> {} (done)".format(
                    pulse["gpio"], pulse["target_value"], pulse["orig_value"]))
                pulse["done"] = True
                self.success += 1

        self._pulses = [p for p in self._pulses if not p["done"]]

    def on_stop(self):
        super().on_stop()
        for pulse in self._pulses:
            if not pulse["done"]:
                p = self._resolve_pin(pulse["gpio"])
                if p is not None:
                    try:
                        p.value(pulse["orig_value"])
                    except Exception:
                        pass
        self._pulses = []
