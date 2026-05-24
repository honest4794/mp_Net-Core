from lib.sys_bus import bus
from lib.hw_manager import HW, _get_pin

HW_TYPE_PIN = 0
HW_TYPE_PWM = 1


def on_hw_ctl(ctx, args):
    hw_type = int(args.get("type", 0) or 0)
    hw_id = int(args.get("id", 0) or 0)
    value = int(args.get("value", 0) or 0)

    if hw_type == HW_TYPE_PIN:
        try:
            _get_pin(hw_id).value(value)
            print("[HW] pin {} = {}".format(hw_id, value))
        except Exception as e:
            print("[HW] pin err: {}".format(e))

    elif hw_type == HW_TYPE_PWM:
        pwm_list = bus.get_service("pwm_list")
        if not pwm_list or hw_id >= len(pwm_list):
            print("[HW] pwm idx {} out of range".format(hw_id))
            return
        try:
            pwm_list[hw_id].duty_u16(value)
            print("[HW] pwm {} duty={}".format(hw_id, value))
        except Exception as e:
            print("[HW] pwm err: {}".format(e))


def on_hw_query(ctx, args):
    hw_type = int(args.get("type", 0) or 0)
    hw_id = int(args.get("id", 0) or 0)

    if hw_type == HW_TYPE_PIN:
        from machine import Pin
        try:
            p = Pin(hw_id, Pin.IN)
            val = p.value()
            print("[HW] pin {} = {}".format(hw_id, val))
        except Exception as e:
            print("[HW] pin query err: {}".format(e))

    elif hw_type == HW_TYPE_PWM:
        pwm_list = bus.get_service("pwm_list")
        if not pwm_list or hw_id >= len(pwm_list):
            print("[HW] pwm idx {} out of range".format(hw_id))
            return
        try:
            duty = pwm_list[hw_id].duty_u16()
            print("[HW] pwm {} duty={}".format(hw_id, duty))
        except Exception as e:
            print("[HW] pwm query err: {}".format(e))


def register(app):
    app.disp.on(0x1401, on_hw_ctl)
    app.disp.on(0x1402, on_hw_query)
    print("[HW] Hardware actions registered")
