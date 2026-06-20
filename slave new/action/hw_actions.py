from lib.sys_bus import bus
from lib.hw_manager import HW


def on_hw_ctl(ctx, args):
    hw_type = int(args.get("type", 0) or 0)
    hw_id   = int(args.get("id", 0) or 0)
    value   = int(args.get("value", 0) or 0)
    label   = args.get("label") or ""

    if hw_type == HW.VBTN:
        HW.set(HW.VBTN, hw_id, value)
        if hw_id == 1:
            bus.shared["_vbtn1_event"] = value
        print("[HW] vbtn {}={}".format(hw_id, value))
        return

    if hw_type == HW.PIN:
        try:
            p = HW.resolve_pin(hw_id)
            p.value(value)
            print("[HW] pin {}={}".format(hw_id, value))
        except Exception as e:
            print("[HW] pin err: {}".format(e))
        return

    if hw_type == HW.PWM:
        try:
            HW.set(HW.PWM, hw_id, value)
            print("[HW] pwm {} duty={}".format(hw_id, value))
        except Exception as e:
            print("[HW] pwm err: {}".format(e))
        return

    if label == "enc_delta":
        # HW_CTL schema 的 value 是 u16，這裡轉回 signed delta。
        if value & 0x8000:
            value -= 0x10000
        cur = int(bus.shared.get("_enc_delta", 0) or 0)
        bus.shared["_enc_delta"] = cur + value
        print("[HW] enc_delta={:+d}".format(value))
        return

    if label:
        print("[HW] {}={}".format(label, value))
        bus.shared["hw_events"] = {"label": label, "value": value}
        return

    print("[HW] unknown type=0x{:02X}".format(hw_type))


def on_hw_query(ctx, args):
    hw_type = int(args.get("type", 0) or 0)
    hw_id   = int(args.get("id", 0) or 0)

    if hw_type == HW.PIN:
        try:
            p = HW.resolve_pin(hw_id)
            print("[HW] pin {} = {}".format(hw_id, p.value()))
        except Exception as e:
            print("[HW] pin query err: {}".format(e))

    elif hw_type == HW.PWM:
        val = HW.get(HW.PWM, hw_id)
        print("[HW] pwm {} duty={}".format(hw_id, val))


def register(app):
    app.disp.on(0x1401, on_hw_ctl)
    app.disp.on(0x1402, on_hw_query)
    print("[HW] Hardware actions registered")
